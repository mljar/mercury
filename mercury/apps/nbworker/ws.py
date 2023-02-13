import json
import logging
import sys
from queue import Queue

import websocket

from apps.nbworker.db import DBClient
from apps.nbworker.utils import Purpose, WorkerState
from apps.nbworker.utils import stop_event

log = logging.getLogger(__name__)


class WSClient(DBClient):
    def __init__(self, ws_address, notebook_id, session_id, worker_id):
        super(WSClient, self).__init__(notebook_id, session_id, worker_id)

        self.connect(ws_address)

        self.queue = Queue()

        self.msg_counter = 0

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
        self.queue.put(json.dumps({"purpose": Purpose.InitNotebook}))
        if self.worker_exists():
            self.set_worker_state(WorkerState.Running)
            self.send_state()
        self.delete_stale_workers()

    def on_close(self, ws, close_status_code, close_msg):
        global stop_event
        stop_event.set()
        log.info(f"WS close connection, status={close_status_code}, msg={close_msg}")

    def on_pong(self, wsapp, msg):
        log.info("WS on_pong")
        if self.is_worker_stale():
            self.delete_worker()
            log.info(f"Worker id={self.worker_id} is stale, quit")
            sys.exit(1)

    def on_error(self, ws, msg):
        log.debug(f"WS on_error, {msg}")

    def on_message(self, ws, msg):
        log.debug(f"WS on_message {msg}")
        self.queue.put(msg)
        self.msg_counter += 1

    def send_state(self):
        try:
            log.debug(f"Send state {self.worker_state()}")
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
