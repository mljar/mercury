import json
import logging
import os
import sys
from types import SimpleNamespace

import requests

from apps.workers.constants import WorkerState
from apps.ws.utils import machine_uuid

log = logging.getLogger(__name__)


class RESTClient:
    def __init__(self, notebook_id, session_id, worker_id):
        self.server_url = os.environ.get("MERCURY_SERVER_URL", "http://127.0.0.1:8000")
        self.notebook_id = notebook_id
        self.session_id = session_id
        self.worker_id = worker_id
        self.worker = None  # SimpleNamespace object
        self.state = WorkerState.Unknown
        self.notebook = None  # SimpleNamespace object
        self.owner = None  # SimpleNamespace object
        self.user = None  # SimpleNamespace object
        self.load_notebook()
        self.load_owner_and_user()

    def load_notebook(self):
        try:
            log.info(f"Load notebook id={self.notebook_id}")
            response = requests.get(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/nb",
                timeout=5
            )
            if response.status_code != 200:
                raise Exception("Cant load notebook")
            self.notebook = SimpleNamespace(**response.json())
        except Exception:
            log.exception("Exception when notebook load, quit")
            sys.exit(0)

    def load_owner_and_user(self):
        try:
            log.info("Load owner and user")
            response = requests.get(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/owner-and-user",
                timeout=5
            )
            if response.status_code != 200:
                raise Exception("Cant load onwer and user information")
            owner = response.json().get("owner", {})
            user = response.json().get("user", {})
            if owner:
                self.owner = SimpleNamespace(**owner)
            if user:
                self.user = SimpleNamespace(**user)
        except Exception:
            log.exception("Exception when loading owner and user")

    def get_user_info(self):
        print(self.user)
        if self.user is None:
            return None
        return json.dumps(self.user.__dict__)

    def update_notebook(self, new_params):
        log.info(f"Executed params {json.dumps(new_params, indent=4)}")

        update_database = False
        if new_params.get("title", "") != "" and self.notebook.title != new_params.get(
            "title", ""
        ):
            self.notebook.title = new_params.get("title", "")
            update_database = True

        nb_params = json.loads(self.notebook.params)
        for property in [
            "show-code",
            "show-prompt",
            "continuous_update",
            "static_notebook",
            "description",
            "show_sidebar",
            "full_screen",
            "allow_download",
            "stop_on_error",
        ]:
            if new_params.get(property) is not None and nb_params.get(
                property
            ) != new_params.get(property):
                nb_params[property] = new_params.get(property)
                update_database = True
        # save widgets params
        if json.dumps(nb_params.get("params", {})) != json.dumps(
            new_params.get("params", {})
        ):
            nb_params["params"] = new_params["params"]
            update_database = True

        if update_database:
            try:
                log.info(f"Update notebook id={self.notebook_id}")
                response = requests.post(
                    f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/update-nb",
                    {"title": self.notebook.title, "params": json.dumps(nb_params)},
                    timeout=5
                )
                if response.status_code != 200:
                    raise Exception(f"Cant update notebook {response}")
                self.notebook = SimpleNamespace(**response.json())
            except Exception:
                log.exception("Exception when updating notebook")

        return update_database

    def is_presentation(self):
        try:
            isIt = self.notebook.output == "slides"
            log.info(f"Check if notebook is presentation ({isIt})")
            return isIt
        except Exception:
            log.exception("Exception when check if notebook is presentation")
        return False

    def show_code(self):
        try:
            show_it = str(
                json.loads(self.notebook.params).get("show-code", "false")
            ).lower()
            log.info(f"Check if show code from notebook ({show_it})")
            return show_it == "true"
        except Exception:
            log.exception("Exception when check if show code from notebook")
        return False

    def show_prompt(self):
        try:
            show_it = str(
                json.loads(self.notebook.params).get("show-prompt", "false")
            ).lower()
            log.info(f"Check if show prompt from notebook ({show_it})")
            return show_it == "true"
        except Exception:
            log.exception("Exception when check if show promtp from notebook")
        return False

    def reveal_theme(self):
        # TODO: get reveal theme
        return "white"

    def stop_on_error(self):
        try:
            stop_on_error = str(
                json.loads(self.notebook.params).get("stop_on_error", "false")
            ).lower()
            log.info(f"Check if stop_on_error ({stop_on_error})")
            return stop_on_error == "true"
        except Exception:
            log.exception("Exception when check if stop_on_error")
        return False

    def worker_state(self):
        return self.state

    def set_worker_state(self, new_state):
        try:
            log.info(
                f"Worker id={self.worker_id} set state {new_state} uuid {machine_uuid()}"
            )
            self.state = new_state
            # set worker machine id
            # to control number of workers
            # in the single machine
            response = requests.post(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/set-worker-state",
                {"state": new_state, "machine_id": machine_uuid()},
                timeout=5
            )
            if response.status_code != 200:
                raise Exception(f"Problem when set worker state {response}")
            self.worker = SimpleNamespace(**response.json())
        except Exception:
            log.exception("Exception when set worker state")

    @staticmethod
    def delete_worker_in_db(session_id, worker_id, notebook_id):
        try:
            log.info(f"Delete worker id={worker_id}")
            server_url = os.environ.get("MERCURY_SERVER_URL", "http://127.0.0.1:8000")

            response = requests.post(
                f"{server_url}/api/v1/worker/{session_id}/{worker_id}/{notebook_id}/delete-worker",
                timeout=5
            )
            if response.status_code != 204:
                raise Exception(f"Problem when delete worker {response}")

        except Exception:
            pass
            # log.exception(f"Exception when delete worker")

    def delete_worker(self):
        RESTClient.delete_worker_in_db(
            self.session_id, self.worker_id, self.notebook_id
        )

    def worker_exists(self):
        try:
            log.info(f"Worker id={self.worker_id} exists")

            response = requests.get(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/worker",
                timeout=5
            )
            self.worker = SimpleNamespace(**response.json())

        except Exception as e:
            # log.exception(f"Worker id={self.worker_id} does not exists, quit")
            sys.exit(1)
        return True

    def is_worker_stale(self):
        try:
            response = requests.get(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/is-worker-stale",
                timeout=5
            )
            if response.status_code == 200:
                is_stale = response.json().get("is_stale", True)
                log.info(f"Check worker id={self.worker_id} is stale {is_stale}")
                return is_stale
            return True

        except Exception:
            log.exception(
                f"Exception when check if worker id={self.worker_id} is stale"
            )
        return True

    def list_secrets(self):
        try:
            response = requests.get(
                f"{self.server_url}/api/v1/worker/{self.session_id}/{self.worker_id}/{self.notebook_id}/worker-secrets",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            log.exception(f"Exception when list worker id={self.worker_id} secrets")
        return []
