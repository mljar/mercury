import copy
import json
import logging
import sys
import threading
import time
import os
import hashlib

from datetime import datetime
from django_drf_filepond.models import TemporaryUpload
from execnb.nbio import nb2dict, read_nb

from apps.nb.nbrun import NbRun
from apps.nbworker.utils import Purpose, WorkerState
from apps.nbworker.ws import WSClient
from apps.storage.storage import StorageManager
from apps.tasks.export_pdf import to_pdf
from apps.tasks.models import Task
from apps.ws.utils import parse_params
from apps.nbworker.utils import stop_event
from widgets.manager import WidgetsManager

log = logging.getLogger(__name__)


class NBWorker(WSClient):
    def __init__(self, ws_address, notebook_id, session_id, worker_id):
        super(NBWorker, self).__init__(ws_address, notebook_id, session_id, worker_id)

        self.prev_nb = None
        self.prev_widgets = {}
        self.prev_body = ""
        self.prev_update_time = None
        self.prev_md5 = None
        # monitor notebook file updates if running locally
        if "127.0.0.1" in ws_address:
            threading.Thread(target=self.nb_file_watch, daemon=True).start()
        threading.Thread(target=self.process_msgs, daemon=True).start()
        self.ws.run_forever(ping_interval=5, ping_timeout=3)

    @staticmethod
    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def nb_file_watch(self):
        while not stop_event.is_set():
            current_update_time = datetime.fromtimestamp(
                os.path.getmtime(self.notebook.path)
            )
            if (
                self.prev_update_time is not None
                and self.prev_update_time != current_update_time
            ):
                checksum = NBWorker.md5(self.notebook.path)

                log.debug(f"Checksum {checksum} prev {self.prev_md5}")

                if self.prev_md5 is None or checksum != self.prev_md5:
                    log.debug("Notebook file changed!")
                    msg = json.dumps({"purpose": Purpose.InitNotebook})
                    self.queue.put(msg)

                self.prev_md5 = checksum

            self.prev_update_time = current_update_time
            time.sleep(0.25)

    def process_msgs(self):
        global stop_event
        while not stop_event.is_set():
            item = self.queue.get()
            log.debug(f"Porcess msg {item}")
            json_data = json.loads(item)

            if json_data.get("purpose", "") == Purpose.InitNotebook:
                self.init_notebook()
            elif json_data.get("purpose", "") == Purpose.RunNotebook:
                self.run_notebook(json_data)
            elif json_data.get("purpose", "") == Purpose.SaveNotebook:
                self.save_notebook()
            elif json_data.get("purpose", "") == Purpose.DisplayNotebook:
                self.display_notebook(json_data)
            elif json_data.get("purpose", "") == Purpose.ClearSession:
                self.init_notebook()
            elif json_data.get("purpose", "") == Purpose.WorkerPing:
                self.worker_pong()
            elif json_data.get("purpose", "") == Purpose.CloseWorker:
                stop_event.set()
                self.delete_worker()
                sys.exit(1)
            elif json_data.get("purpose", "") == Purpose.DownloadHTML:
                self.download_html()
            elif json_data.get("purpose", "") == Purpose.DownloadPDF:
                self.download_pdf()

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
        self.prev_body = copy.deepcopy(body)

    def update_nb(self, widgets):
        log.debug(f"Update nb {widgets}")

        index_execute_from = 1
        # fill notebook with widgets values
        self.prev_widgets = copy.deepcopy(widgets)
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
            elif widget_type == "OutputDir":
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

            """
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
            """
            self.send_widgets(self.nb, expected_widgets_keys=widgets.keys())
            self.prev_nb = copy.deepcopy(self.nb)
        else:
            log.debug("Skip nb execution, no changes in widgets")

    def send_widgets(self, nb, expected_widgets_keys, init_widgets=False):
        nb_widgets_keys = []
        widgets_params = []
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
                            msg["widgetKey"] = w.get("code_uid")
                            log.debug(f"Update widget {msg}")
                            if init_widgets:
                                widgets_params += [msg]
                            else:
                                msg["purpose"] = Purpose.UpdateWidgets
                                self.ws.send(json.dumps(msg))

                        code_uid = w.get("code_uid")
                        if code_uid is not None:
                            nb_widgets_keys += [code_uid]

                        if w.get("widget", "") == "App":
                            if w.get("title", "") != "":
                                self.ws.send(
                                    json.dumps(
                                        {
                                            "purpose": Purpose.UpdateTitle,
                                            "title": w.get("title"),
                                        }
                                    )
                                )
                            if w.get("show_code") is not None:
                                self.nbrun.set_show_code(w.get("show_code"))
                                self.ws.send(
                                    json.dumps(
                                        {
                                            "purpose": Purpose.UpdateShowCode,
                                            "showCode": w.get("show_code"),
                                        }
                                    )
                                )

        if init_widgets:
            msg = {"purpose": Purpose.InitWidgets, "widgets": widgets_params}
            log.debug("------------Init widgets")
            log.debug(msg)
            self.ws.send(json.dumps(msg))
        else:
            # check if hide some widgets
            # needed only when updating widgets
            hide_widgets = []
            for widget_key in expected_widgets_keys:
                if widget_key not in nb_widgets_keys:
                    hide_widgets += [widget_key]

            log.debug(f"Hide widgets {hide_widgets}")
            if hide_widgets:
                msg = {"purpose": Purpose.HideWidgets, "keys": hide_widgets}
                self.ws.send(json.dumps(msg))

    def initialize_outputdir(self):
        sm = StorageManager(self.session_id, self.worker_id)
        output_dir = sm.worker_output_dir()
        self.nbrun.run_code(
            f"""import os\nos.environ["MERCURY_OUTPUTDIR"]="{output_dir}" """
        )

    def init_notebook(self):
        log.debug(f"Init notebook, show_code={self.show_code()}")

        self.prev_nb = None
        self.prev_widgets = {}
        self.prev_body = ""

        self.update_worker_state(WorkerState.Busy)

        self.nbrun = NbRun(
            show_code=self.show_code(),
            show_prompt=self.show_prompt(),
            is_presentation=self.is_presentation(),
            reveal_theme=self.reveal_theme(),
        )
        # we need to initialize the output dir always
        # even if there is no OutputDir in the notebook
        self.initialize_outputdir()

        self.nb_original = read_nb(self.notebook.path)

        self.nbrun.run_notebook(self.nb_original)

        # TODO: update params in db if needed"
        params = {}
        parse_params(nb2dict(self.nb_original), params)

        # update database ...
        log.debug(f"Executed params {json.dumps(params, indent=4)}")

        update_database = False
        if params.get("title", "") != "" and self.notebook.title != params.get(
            "title", ""
        ):
            self.notebook.title = params.get("title", "")
            update_database = True

        nb_params = json.loads(self.notebook.params)
        for property in [
            "show-code",
            "show-prompt",
            "continuous_update",
            "static_notebook",
            "description",
        ]:
            if params.get(property) is not None and nb_params.get(
                property
            ) != params.get(property):
                nb_params[property] = params.get(property)
                update_database = True
        # save widgets params
        if json.dumps(nb_params.get("params", {})) != json.dumps(
            params.get("params", {})
        ):
            nb_params["params"] = params["params"]
            update_database = True

        if update_database:
            self.notebook.params = json.dumps(nb_params)
            self.notebook.save()

        self.nbrun.set_show_code_and_prompt(
            nb_params.get("show-code", False), nb_params.get("show-prompt", True)
        )
        self.nbrun.set_is_presentation(nb_params.get("output", "app") == "slides")

        log.debug(params)
        log.debug(f"Exporter show_code {self.nbrun.exporter.show_code}")

        self.nb = copy.deepcopy(self.nb_original)

        if self.is_presentation():
            body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            body = self.nbrun.export_html(self.nb, full_header=False)

        msg = {"purpose": Purpose.ExecutedNotebook, "body": body}
        if update_database:
            msg["reloadNotebook"] = True
        self.ws.send(json.dumps(msg))
        self.prev_body = copy.deepcopy(body)

        self.send_widgets(self.nb, expected_widgets_keys=[], init_widgets=True)
        self.update_worker_state(WorkerState.Running)

    def save_notebook(self):
        log.debug(f"Save notebook")
        # save nb in HTML
        if self.is_presentation():
            nb_body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            nb_body = self.nbrun.export_html(self.nb, full_header=True)

        sm = StorageManager(self.session_id, self.worker_id)
        nb_path = sm.save_nb_html(nb_body)

        # create task with path to HTML file
        task = Task.objects.create(
            task_id=f"worker-{self.worker_id}",
            session_id=self.session_id,
            notebook_id=self.notebook_id,
            state="DONE",
            params=json.dumps(self.prev_widgets),
            result=nb_path,
        )
        log.debug(f"Task ({task.id}) created")

        # send notice that nb saved
        self.ws.send(json.dumps({"purpose": Purpose.SavedNotebook}))

    def display_notebook(self, json_params):
        log.debug(f"Display notebook ({json_params})")

    def download_html(self):
        log.debug(f"Download HTML")
        # save nb in HTML with full header
        if self.is_presentation():
            nb_body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            nb_body = self.nbrun.export_html(self.nb, full_header=True)

        sm = StorageManager(self.session_id, self.worker_id)
        _, nb_url = sm.save_nb_html(nb_body)

        # send HTML url address
        self.ws.send(
            json.dumps(
                {
                    "purpose": Purpose.DownloadHTML,
                    "url": nb_url,
                    "filename": f"{self.notebook.slug}.html",
                }
            )
        )

    def download_pdf(self):
        log.debug(f"Download PDF")
        # save nb in HTML with full header
        if self.is_presentation():
            nb_body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            nb_body = self.nbrun.export_html(self.nb, full_header=True)

        # export to PDF
        sm = StorageManager(self.session_id, self.worker_id)
        _, pdf_url = sm.save_nb_pdf(nb_body, self.is_presentation())

        # send PDF url
        self.ws.send(
            json.dumps(
                {
                    "purpose": Purpose.DownloadPDF,
                    "url": pdf_url,
                    "filename": f"{self.notebook.slug}.pdf",
                }
            )
        )
