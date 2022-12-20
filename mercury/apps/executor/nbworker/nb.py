import sys
import json
import copy
import threading
import logging

from execnb.nbio import read_nb, nb2dict

from apps.executor.executor import Executor
from apps.executor.nbworker.ws import WSClient
from apps.executor.nbworker.utils import WorkerState, Purpose
from apps.executor.utils import parse_params

log = logging.getLogger(__name__)


class NBWorker(WSClient):
    def __init__(self, ws_address, notebook_id, session_id, worker_id):

        super(NBWorker, self).__init__(ws_address, notebook_id, session_id, worker_id)

        threading.Thread(target=self.process_msgs, daemon=True).start()

        self.ws.run_forever(ping_interval=5, ping_timeout=3)

    def process_msgs(self):
        while True:
            item = self.queue.get()
            log.debug(f"Porcess msg {item}")
            self.update_worker_state(WorkerState.Running)
            json_data = json.loads(item)

            if json_data.get("purpose", "") == Purpose.InitNotebook:
                self.init_notebook()
            elif json_data.get("purpose", "") == Purpose.RunNotebook:
                self.run_notebook(json_data)
            elif json_data.get("purpose", "") == Purpose.ClearSession:
                self.init_notebook()
            elif json_data.get("purpose", "") == Purpose.WorkerPing:
                self.worker_pong()
            elif json_data.get("purpose", "") == Purpose.CloseWorker:
                self.delete_worker()
                sys.exit(1)

            self.update_worker_state(WorkerState.Running)
            self.queue.task_done()

    def worker_pong(self):
        if self.worker_exists():
            self.send_state()

    def run_notebook(self, json_params):
        log.debug(f"Run notebook with {json_params}")
        self.update_worker_state(WorkerState.Busy)

        widgets = json.loads(json_params.get("widgets", "{}"))

        self.update_nb(widgets)

        body = self.executor.export_html(
            self.nb, full_header=False, show_code=self.show_code
        )

        # with open(f"test_{counter}.html", "w") as fout:
        #    fout.write(body)

        self.ws.send(json.dumps({"purpose": Purpose.ExecutedNotebook, "body": body}))

    def update_nb(self, widgets):
        log.debug(f"Update nb {widgets}")

        index_execute_from = 0
        # fill notebook with widgets values
        for w in widgets.keys():
            value = widgets[w]
            model_id = self.widgets_mapping[w]
            log.debug(f"Update widget id={w} model_id={model_id} value={value}")

            if isinstance(value, str):
                code = f'from widgets.manager import set_update\nset_update("{model_id}", field="value", new_value="{value}")'
            else:
                code = f'from widgets.manager import set_update\nset_update("{model_id}", field="value", new_value={value})'
            r = self.executor.run(code)
            
            updated = "True" in str(r)
            log.debug(f"Update reponse {r}, updated={updated}")

            if updated:
                cell_index = self.widget_index_to_cell_index[w]
                log.debug(f"Widget updated, update nb from {cell_index}")
                
                if index_execute_from == 0:
                    index_execute_from = cell_index
                else:
                    index_execute_from = min(index_execute_from, cell_index)


        # cell index to smallest widget index
        ci2wi = {} # keeps the smallest widget index
        for wi in self.widget_index_to_cell_index.keys():
            ci = self.widget_index_to_cell_index[wi]
            if ci in ci2wi:
                ci2wi[ci] = min(ci2wi[ci], int(wi[1:]))
            else:
                ci2wi[ci] = int(wi[1:])
        
        log.debug(f"Execute nb from {index_execute_from}")
        log.debug(f"Cell index to smallest widget index {ci2wi}")    
        
        if index_execute_from != 0:
            self.nb = copy.deepcopy(self.nb_original)
            for i in range(index_execute_from, len(self.nb.cells)):

                log.debug(f"Execute cell index={i}")

                if i in ci2wi:
                    reset_widgets_counter = ci2wi[i]
                    log.debug(f"Reset widgets counter {reset_widgets_counter}")
                    code = f'from widgets.manager import set_widgets_counter\nset_widgets_counter({reset_widgets_counter})'
                    log.debug(code)
                    r = self.executor.run(code)
                    log.debug(r)
                else:
                    log.debug("Cell index={i} not found")
                


                self.executor.run_cell(self.nb.cells[i], counter=i)

                for output in self.nb.cells[i].get("outputs", []):
                    if "data" in output:
                        if "application/mercury+json" in output["data"]:
                            w = output["data"]["application/mercury+json"]
                            log.debug(w)
                            w = json.loads(w)

                            wi = ""
                            for k in self.widgets_mapping.keys():
                                if self.widgets_mapping[k] == w.get("model_id", ""):
                                    wi = k 
                            log.debug(f"Widget index {wi}")
                            if wi == "":
                                continue
                            # prepare msg to send by ws
                            msg = w
                            msg["purpose"] = Purpose.UpdateWidgets
                            msg["widgetKey"] = wi
                            self.ws.send(json.dumps(msg))
                

        else:
            log.debug("Skip nb execution, no changes in widgets")
            
            


    def init_notebook(self):
        log.debug("Init notebook")
        self.update_worker_state(WorkerState.Busy)

        self.executor = Executor()
        self.nb_original = read_nb(self.notebook.path)
        self.executor.run_notebook(self.nb_original, export_html=False)

        # TODO: update params in db if needed"
        params = {}
        self.widgets_mapping, self.widget_index_to_cell_index = parse_params(
            nb2dict(self.nb_original), params
        )
        log.debug(params)
        log.debug(self.widgets_mapping)
        log.debug(self.widget_index_to_cell_index)

        self.show_code = params.get("show-code", False)
        
        self.nb = copy.deepcopy(self.nb_original)

