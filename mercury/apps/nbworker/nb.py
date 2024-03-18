import copy
import hashlib
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime

from execnb.nbio import nb2dict, read_nb

from apps.nb.nbrun import NbRun
from apps.nbworker.utils import Purpose, stop_event
from apps.nbworker.ws import WSClient
from apps.workers.constants import WorkerState
from apps.ws.utils import parse_params
from apps.accounts.views.utils import get_idle_time, get_max_run_time
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
        self.start_time = time.time()
        self.max_idle_time = get_idle_time(self.owner)
        self.max_run_time = get_max_run_time(self.owner)
        self.last_execution_time = time.time()
        self.start_time = time.time()

        # monitor notebook file updates if running locally
        if (
            "127.0.0.1" in ws_address
            and os.environ.get("MERCURY_DISABLE_AUTO_RELOAD", "NO") != "YES"
        ):
            threading.Thread(target=self.nb_file_watch, daemon=True).start()
        threading.Thread(target=self.process_msgs, daemon=True).start()
        self.ws.run_forever(ping_interval=10, ping_timeout=5)

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

                log.info(f"Checksum {checksum} prev {self.prev_md5}")

                if self.prev_md5 is None or checksum != self.prev_md5:
                    log.info("Notebook file changed!")
                    msg = json.dumps({"purpose": Purpose.InitNotebook})
                    self.queue.put(msg)

                self.prev_md5 = checksum

            self.prev_update_time = current_update_time
            time.sleep(0.25)

    def process_msgs(self):
        global stop_event
        while not stop_event.is_set():
            item = self.queue.get()
            log.info(f"Porcess msg {item}")
            json_data = json.loads(item)

            self.last_execution_time = time.time()

            if json_data.get("purpose", "") == Purpose.InitNotebook:
                self.init_notebook()
            elif json_data.get("purpose", "") == Purpose.RunNotebook:
                self.run_notebook(json_data)
            elif json_data.get("purpose", "") == Purpose.DisplayNotebook:
                self.display_notebook(json_data)
            elif json_data.get("purpose", "") == Purpose.ClearSession:
                self.init_notebook()
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
        total_run_time = time.time() - self.start_time
        elapsed_from_last_execution = time.time() - self.last_execution_time
        log.info(f"Total run time {total_run_time}")
        log.info(f"Elapsed from last execution {elapsed_from_last_execution}")

        close_worker = True
        if total_run_time > self.max_run_time:
            self.update_worker_state(WorkerState.MaxRunTimeReached)
        elif elapsed_from_last_execution > self.max_idle_time:
            self.update_worker_state(WorkerState.MaxIdleTimeReached)
        else:
            self.update_worker_state(self.worker_state())
            close_worker = False

        if self.worker_exists():
            self.send_state()

        if close_worker:
            self.queue.put(json.dumps({"purpose": Purpose.CloseWorker}))

    def run_notebook(self, json_params):
        log.info(f"Run notebook with {json_params}")
        self.update_worker_state(WorkerState.Busy)

        widgets = json.loads(json_params.get("widgets", "{}"))

        self.update_nb(widgets)

        self.sm.sync_output_dir()

        body = self.nbrun.export_html(self.nb, full_header=self.is_presentation())

        # with open(f"test_{counter}.html", "w") as fout:
        #    fout.write(body)

        self.ws.send(json.dumps({"purpose": Purpose.ExecutedNotebook, "body": body}))
        self.update_worker_state(WorkerState.Running)
        self.prev_body = copy.deepcopy(body)

    def update_nb(self, widgets):
        log.info(f"Update nb {widgets}")

        index_execute_from = None
        # fill notebook with widgets values
        self.prev_widgets = copy.deepcopy(widgets)
        for widget_key in widgets.keys():
            value = widgets[widget_key]

            widget_type = WidgetsManager.parse_widget_type(widget_key)
            log.info(
                f"Update widget code_uid={widget_key} value={value} widget type {widget_type}"
            )

            if widget_type == "File" and len(value) == 2:
                log.info(f"Get file {value[0]} from id={value[1]}")
                # tu = TemporaryUpload.objects.get(upload_id=value[1])
                # value[1] = tu.get_file_path()
                # value[1] = value[1].replace("\\", "\\\\")
                value = self.sm.get_user_uploaded_file(value)
                log.info(f"File path is {value[1]}")

                code = (
                    f'WidgetsManager.update("{widget_key}", field="filename", new_value="{value[0]}")\n'
                    f'WidgetsManager.update("{widget_key}", field="filepath", new_value="{value[1]}")\n'
                )
            elif widget_type == "OutputDir":
                output_dir = self.sm.worker_output_dir()
                output_dir = output_dir.replace("\\", "\\\\")
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value="{output_dir}")'

            elif isinstance(value, str):
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value="""{value}""")'
            else:
                code = f'WidgetsManager.update("{widget_key}", field="value", new_value={value})'

            log.info(f"Execute code {code}")

            r = self.nbrun.run_code(code)

            updated = "True" in str(r)
            log.info(f"Update reponse {r}, updated={updated}")

            if updated:
                cell_index = WidgetsManager.parse_cell_index(widget_key)
                log.info(f"Widget updated, update nb from {cell_index}")

                if index_execute_from is None:
                    index_execute_from = cell_index
                else:
                    index_execute_from = min(index_execute_from, cell_index)

        if index_execute_from is not None:
            if self.prev_nb is not None:
                self.nb = copy.deepcopy(self.prev_nb)
            else:
                self.nb = copy.deepcopy(self.nb_original)

            self.nbrun.run_notebook(self.nb, start=index_execute_from - 1)

            self.send_widgets(self.nb, expected_widgets_keys=widgets.keys())
            self.prev_nb = copy.deepcopy(self.nb)
        else:
            log.info("Skip nb execution, no changes in widgets")

    def send_widgets(self, nb, expected_widgets_keys, init_widgets=False):
        nb_widgets_keys = []
        widgets_params = []
        for cell in nb.cells:
            for output in cell.get("outputs", []):
                if "data" in output:
                    if "application/mercury+json" in output["data"]:
                        w = output["data"]["application/mercury+json"]
                        log.info(w)
                        w = json.loads(w)

                        # prepare msg to send by ws
                        msg = WidgetsManager.frontend_format(w)
                        if msg:
                            msg["widgetKey"] = w.get("code_uid")
                            log.info(f"Update widget {msg}")
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
            log.info("Init widgets")
            log.info(msg)
            self.ws.send(json.dumps(msg))
        else:
            # check if hide some widgets
            # needed only when updating widgets
            hide_widgets = []
            for widget_key in expected_widgets_keys:
                if widget_key not in nb_widgets_keys:
                    hide_widgets += [widget_key]

            log.info(f"Hide widgets {hide_widgets}")
            if hide_widgets:
                msg = {"purpose": Purpose.HideWidgets, "keys": hide_widgets}
                self.ws.send(json.dumps(msg))

    def initialize_outputdir(self):
        output_dir = self.sm.worker_output_dir()
        output_dir = output_dir.replace("\\", "\\\\")
        self.nbrun.run_code(
            f"""import os\nos.environ["MERCURY_OUTPUTDIR"]="{output_dir}" """
        )

    def install_new_packages(self):
        if "127.0.0.1" not in self.ws_address and "localhost" not in self.ws_address:
            fname = "requirements.txt"
            if os.path.exists(fname):
                log.info(f"Install new packages from requirements.txt")
                cmd = f"pip install --no-input -r {fname}"
                self.nbrun.run_code(cmd)

    def provision_secrets(self):
        secrets = self.list_secrets()
        if secrets:
            cmd = "import os\n"
            for s in secrets:
                name = s.get("name", "")
                secret = s.get("secret", "")
                cmd += f'os.environ["{name}"] = "{secret}"'
                cmd += "\n" # add new line between secrets
            log.info("Set secrets")
            self.nbrun.run_code(cmd)

    def init_notebook(self):
        log.info(f"Init notebook, show_code={self.show_code()}")

        self.sm.provision_uploaded_files()

        self.prev_nb = None
        self.prev_widgets = {}
        self.prev_body = ""

        self.update_worker_state(WorkerState.Busy)

        self.nbrun = NbRun(
            show_code=self.show_code(),
            show_prompt=self.show_prompt(),
            is_presentation=self.is_presentation(),
            reveal_theme=self.reveal_theme(),
            stop_on_error=self.stop_on_error(),
            user_info=self.get_user_info(),
        )
        
        self.provision_secrets()
        self.install_new_packages()

        # we need to initialize the output dir always
        # even if there is no OutputDir in the notebook
        self.initialize_outputdir()

        self.nb_original = read_nb(self.notebook.path)

        self.nbrun.run_notebook(self.nb_original)

        self.sm.sync_output_dir()

        # TODO: update params in db if needed"
        params = {}
        parse_params(nb2dict(self.nb_original), params)

        # update database ...

        log.info(f"Executed params {json.dumps(params, indent=4)}")
        update_database = self.update_notebook(params)

        # update_database = False
        # if params.get("title", "") != "" and self.notebook.title != params.get(
        #     "title", ""
        # ):
        #     self.notebook.title = params.get("title", "")
        #     update_database = True

        # nb_params = json.loads(self.notebook.params)
        # for property in [
        #     "show-code",
        #     "show-prompt",
        #     "continuous_update",
        #     "static_notebook",
        #     "description",
        #     "show_sidebar",
        #     "full_screen",
        #     "allow_download",
        # ]:
        #     if params.get(property) is not None and nb_params.get(
        #         property
        #     ) != params.get(property):
        #         nb_params[property] = params.get(property)
        #         update_database = True
        # # save widgets params
        # if json.dumps(nb_params.get("params", {})) != json.dumps(
        #     params.get("params", {})
        # ):
        #     nb_params["params"] = params["params"]
        #     update_database = True

        # if update_database:
        #     self.notebook.params = json.dumps(nb_params)
        #     self.notebook.save()

        nb_params = json.loads(self.notebook.params)

        self.nbrun.set_show_code_and_prompt(
            nb_params.get("show-code", False), nb_params.get("show-prompt", True)
        )
        self.nbrun.set_is_presentation(nb_params.get("output", "app") == "slides")
        self.nbrun.set_stop_on_error(nb_params.get("stop_on_error", False))

        log.info(params)
        log.info(f"Exporter show_code {self.nbrun.exporter.show_code}")

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

    # def save_notebook(self):
    #     log.info(f"Save notebook")
    #     # save nb in HTML
    #     if self.is_presentation():
    #         nb_body = self.nbrun.export_html(self.nb, full_header=True)
    #     else:
    #         nb_body = self.nbrun.export_html(self.nb, full_header=True)

    #     sm = StorageManager(self.session_id, self.worker_id)
    #     nb_path = sm.save_nb_html(nb_body)

    #     # create task with path to HTML file
    #     task = Task.objects.create(
    #         task_id=f"worker-{self.worker_id}",
    #         session_id=self.session_id,
    #         notebook_id=self.notebook_id,
    #         state="DONE",
    #         params=json.dumps(self.prev_widgets),
    #         result=nb_path,
    #     )
    #     log.info(f"Task ({task.id}) created")

    #     # send notice that nb saved
    #     self.ws.send(json.dumps({"purpose": Purpose.SavedNotebook}))

    def display_notebook(self, json_params):
        log.info(f"Display notebook ({json_params})")

    def download_html(self):
        log.info(f"Download HTML")
        # save nb in HTML with full header
        if self.is_presentation():
            nb_body = self.nbrun.export_html(self.nb, full_header=True)
        else:
            nb_body = self.nbrun.export_html(self.nb, full_header=True)

        _, nb_url = self.sm.save_nb_html(nb_body)

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
        log.info(f"Download PDF")
        # save nb in HTML with full header
        nb_body = self.nbrun.export_html(self.nb, full_header=True)

        # export to PDF
        _, pdf_url = self.sm.save_nb_pdf(nb_body, self.is_presentation())

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
