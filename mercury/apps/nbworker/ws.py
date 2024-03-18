import json
import logging
import sys
from queue import Queue

import websocket

from apps.nbworker.rest import RESTClient
from apps.nbworker.utils import Purpose, stop_event
from apps.storage.storage import StorageManager

log = logging.getLogger(__name__)


class WSClient(RESTClient):
    def __init__(self, ws_address, notebook_id, session_id, worker_id):
        super(WSClient, self).__init__(notebook_id, session_id, worker_id)

        self.sm = StorageManager(self.session_id, self.worker_id, self.notebook_id)

        self.ws_address = ws_address

        self.connect(ws_address)

        self.queue = Queue()

        self.msg_counter = 0

    def connect(self, ws_address):
        try:
            log.info(f"WS connect to {ws_address}")
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
        self.queue.put(json.dumps({"purpose": Purpose.InitNotebook}))
        # just check if exists
        self.worker_exists()

    def on_close(self, ws, close_status_code, close_msg):
        global stop_event
        stop_event.set()
        self.sm.delete_worker_output_dir()
        log.info(f"WS close connection, status={close_status_code}, msg={close_msg}")

    def on_pong(self, wsapp, msg):
        log.info("WS on_pong")
        if self.is_worker_stale():
            self.delete_worker()
            log.info(f"Worker id={self.worker_id} is stale, quit")
            sys.exit(1)

    def on_error(self, ws, msg):
        log.info(f"WS on_error, {msg}")

    def on_message(self, ws, msg):
        log.info(f"WS on_message {msg}")

        json_data = json.loads(msg)
        if json_data.get("purpose", "") == Purpose.WorkerPing:
            self.worker_pong()
        else:
            self.queue.put(msg)

        self.msg_counter += 1

    def send_state(self):
        try:
            log.info(f"Send state {self.worker_state()}")
            msg = {
                "purpose": Purpose.WorkerState,
                "state": self.worker_state(),
                "workerId": self.worker_id,
            }
            self.ws.send(json.dumps(msg))
        except Exception as e:
            log.exception("Exception when send state")

    def update_worker_state(self, new_state):
        self.set_worker_state(new_state)
        self.send_state()
