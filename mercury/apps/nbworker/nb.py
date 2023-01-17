import copy
import json
import logging
import sys
import threading

from django_drf_filepond.models import TemporaryUpload
from execnb.nbio import nb2dict, read_nb

from apps.nb.nbrun import NbRun
from apps.nbworker.utils import Purpose, WorkerState
from apps.nbworker.ws import WSClient
from apps.storage.storage import StorageManager
from apps.ws.utils import parse_params
from widgets.manager import WidgetsManager

log = logging.getLogger(__name__)


class NBWorker(WSClient):
    def __init__(self, ws_address, notebook_id, session_id, worker_id):

        super(NBWorker, self).__init__(ws_address, notebook_id, session_id, worker_id)

        self.prev_nb = None

        threading.Thread(target=self.process_msgs, daemon=True).start()

        self.ws.run_forever(ping_interval=5, ping_timeout=3)

    def process_msgs(self):
        while True:
            item = self.queue.get()
            log.debug(f"Porcess msg {item}")
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

            self.queue.task_done()

    def worker_pong(self):
        self.update_worker_state(WorkerState.Running)
        if self.worker_exists():
            self.send_state()

    def run_notebook(self, json_params):
        log.debug(f"Run notebook with {json_params}")
        self.update_worker_state(WorkerState.Busy)

        widgets = json.loads(json_params.get("widgets", "{}"))

        self.update_nb(widgets)

        if self.is_presentation():
            body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            body = self.nbrun.export_html(self.nb, full_header=False)

        # with open(f"test_{counter}.html", "w") as fout:
        #    fout.write(body)

        self.ws.send(json.dumps({"purpose": Purpose.ExecutedNotebook, "body": body}))
        self.update_worker_state(WorkerState.Running)

    def update_nb(self, widgets):
        log.debug(f"Update nb {widgets}")

        index_execute_from = 1
        # fill notebook with widgets values
        for widget_key in widgets.keys():
            value = widgets[widget_key]

            widget_type = WidgetsManager.parse_widget_type(widget_key)
            log.debug(
                f"Update widget code_uid={widget_key} value={value} widget type {widget_type}"
            )

            if widget_type == "File" and len(value) == 2:
                log.debug(f"Get file {value[0]} from id={value[1]}")
                tu = TemporaryUpload.objects.get(upload_id=value[1])
                value[1] = tu.get_file_path()
                log.debug(f"File path is {value[1]}")

                code = (
                    f'WidgetsManager.update("{widget_key}", field="filename", new_value="{value[0]}")\n'
                    f'WidgetsManager.update("{widget_key}", field="filepath", new_value="{value[1]}")\n'
                )
            if widget_type == "OutputDir":

                sm = StorageManager(self.session_id, self.worker_id)
                output_dir = sm.worker_output_dir()
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value="{output_dir}")'

            elif isinstance(value, str):
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value="{value}")'
            else:
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value={value})'

            log.debug(f"Execute code {code}")

            r = self.nbrun.run_code(code)

            updated = "True" in str(r)
            log.debug(f"Update reponse {r}, updated={updated}")

            if updated:
                cell_index = WidgetsManager.parse_cell_index(widget_key)
                log.debug(f"Widget updated, update nb from {cell_index}")

                if index_execute_from == 1:
                    index_execute_from = cell_index
                else:
                    index_execute_from = min(index_execute_from, cell_index)

        if index_execute_from != 1:
            if self.prev_nb is not None:
                self.nb = copy.deepcopy(self.prev_nb)
            else:
                self.nb = copy.deepcopy(self.nb_original)

            for i in range(index_execute_from, len(self.nb.cells) + 1):

                log.debug(f"Execute cell index={i-1}")

                self.nbrun.run_cell(self.nb.cells[i - 1], counter=i)

                print(self.nb.cells[i - 1])

                for output in self.nb.cells[i - 1].get("outputs", []):
                    if "data" in output:
                        if "application/mercury+json" in output["data"]:
                            w = output["data"]["application/mercury+json"]
                            log.debug(w)
                            w = json.loads(w)

                            # prepare msg to send by ws
                            msg = WidgetsManager.frontend_format(w)
                            if msg:
                                msg["purpose"] = Purpose.UpdateWidgets
                                msg["widgetKey"] = w.get("code_uid")
                                log.debug(f"Update widget {msg}")
                                self.ws.send(json.dumps(msg))

            # check if hide some widgets
            nb_widgets_keys = []
            for cell in self.nb.cells:
                for output in cell.get("outputs", []):
                    w = output.get("data", {}).get("application/mercury+json")
                    if w is not None:
                        w = json.loads(w)
                        code_uid = w.get("code_uid")
                        if code_uid is not None:
                            nb_widgets_keys += [code_uid]

            hide_widgets = []
            for widget_key in widgets.keys():
                if widget_key not in nb_widgets_keys:
                    hide_widgets += [widget_key]

            log.debug(f"Hide widgets {hide_widgets}")
            if hide_widgets:
                msg = {"purpose": Purpose.HideWidgets, "keys": hide_widgets}
                self.ws.send(json.dumps(msg))

            self.prev_nb = copy.deepcopy(self.nb)
        else:
            log.debug("Skip nb execution, no changes in widgets")

    def send_widgets(self, nb, expected_widgets_keys):
        nb_widgets_keys = []
        for cell in nb.cells:
            for output in cell.get("outputs", []):
                if "data" in output:
                    if "application/mercury+json" in output["data"]:
                        w = output["data"]["application/mercury+json"]
                        log.debug(w)
                        w = json.loads(w)

                        # prepare msg to send by ws
                        msg = WidgetsManager.frontend_format(w)
                        if msg:
                            msg["purpose"] = Purpose.UpdateWidgets
                            msg["widgetKey"] = w.get("code_uid")
                            log.debug(f"Update widget {msg}")
                            self.ws.send(json.dumps(msg))

                        code_uid = w.get("code_uid")
                        if code_uid is not None:
                            nb_widgets_keys += [code_uid]

        # check if hide some widgets
        hide_widgets = []
        for widget_key in expected_widgets_keys:
            if widget_key not in nb_widgets_keys:
                hide_widgets += [widget_key]

        log.debug(f"Hide widgets {hide_widgets}")
        if hide_widgets:
            msg = {"purpose": Purpose.HideWidgets, "keys": hide_widgets}
            self.ws.send(json.dumps(msg))

    def init_notebook(self):
        log.debug(f"Init notebook, show_code={self.show_code()}")
        self.update_worker_state(WorkerState.Busy)

        self.nbrun = NbRun(
            show_code=self.show_code(),
            show_prompt=self.show_prompt(),
            is_presentation=self.is_presentation(),
            reveal_theme=self.reveal_theme(),
        )
        self.nb_original = read_nb(self.notebook.path)

        self.nbrun.run_notebook(self.nb_original)

        # TODO: update params in db if needed"
        params = {}
        parse_params(nb2dict(self.nb_original), params)
        log.debug(params)
        self.nb = copy.deepcopy(self.nb_original)

        self.send_widgets(self.nb, expected_widgets_keys=[])
        self.update_worker_state(WorkerState.Running)