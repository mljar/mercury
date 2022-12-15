import sys
import json
import websocket

import logging

from apps.executor.nbworker.utils import WorkerState, Purpose

log = logging.getLogger(__name__)


class WSClient:
    def __init__(self, ws_address, notebook_id, session_id, worker_id):

        super(WSClient, self).__init__(notebook_id, session_id, worker_id)

        self.connect(ws_address)

        self.state = WorkerState.Running

    def connect(self, ws_address):
        try:
            log.debug(f"WS connect to {ws_address}")
            self.ws = websocket.WebSocketApp(
                ws_address,
                on_open=lambda ws: self.on_open(ws),
                on_close=lambda ws, close_status_code, close_msg: self.on_close(
                    ws, close_status_code, close_msg
                ),
                on_error=lambda ws, msg: self.on_error(ws, msg),
                on_pong=lambda ws, msg: self.on_pong(ws, msg),
                on_message=lambda ws, msg: self.on_message(ws, msg),
            )
        except Exception:
            log.exception("Exception when WS connect")

    def on_open(self, ws):
        log.info("Open ws connection")
        if self.worker_exists():
            self.send_status()
        self.delete_stale_workers()

    def on_close(self, ws, close_status_code, close_msg):
        log.info("WS close connection, status={close_status_code}, msg={close_msg}")

    def on_pong(self, wsapp, msg):
        if self.is_worker_stale():
            self.delete_worker()
            log.info(f"Worker id={self.worker_id} is stale, quit")
            sys.exit(1)

    def on_error(self, ws, msg):
        log.debug(f"WS on_error, {msg}")

    def on_message(self, ws, msg):

        global counter

        data = json.loads(msg)

        if "purpose" in data:
            purpose = data["purpose"]
            logging.info(purpose)
            if purpose == "worker-ping":
                worker_exists_and_running(worker_id, ws)
            if purpose == "run-notebook":
                q.put(
                    json.dumps(
                        {
                            "purpose": "run-notebook",
                            "widgets": data.get("widgets", "{}"),
                        }
                    )
                )
            if purpose == "clear-session":
                q.put(json.dumps({"purpose": "clear-session"}))
            if purpose == "close-worker":
                delete_current_worker()
                print("no worker-ping from client, quit")
                sys.exit(1)

        counter += 1

    def send_state(self):
        try:
            log.debug(f"Send state {self.state}")
            self.ws.send(
                json.dumps({"purpose": Purpose.WorkerState, "state": self.state})
            )
        except Exception as e:
            log.exception("Exception when send state")
