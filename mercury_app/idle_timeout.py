# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import logging
import time
from threading import Event, Thread

import tornado.web

logger = logging.getLogger("mercury.idle_timeout")

class TimeoutManager:
    def __init__(self, timeout, serverapp):
        self.timeout = timeout
        self.serverapp = serverapp
        self.last_activity = time.time()
        self._stop_event = Event()
        self._thread = Thread(target=self.check)
        self._thread.daemon = True
        self._thread.start()

    def touch(self):
        logger.debug(f"[Idle Timeout] touch() called at {time.strftime('%X')}")
        self.last_activity = time.time()

    def check(self):
        def shutdown_server(serverapp):
            if hasattr(serverapp, "shutdown"):
                logger.debug("[Idle Timeout] Calling serverapp.shutdown()")
                serverapp.io_loop.add_callback(serverapp.shutdown)
            elif hasattr(serverapp, "stop"):
                logger.debug("[Idle Timeout] Calling serverapp.stop()")
                serverapp.io_loop.add_callback(serverapp.stop)
            else:
                logger.debug("[Idle Timeout] Forcing os._exit(0)")
                import os
                os._exit(0)
        while not self._stop_event.is_set():
            delta = time.time() - self.last_activity
            logger.debug(f"[Idle Timeout] Seconds since last activity: {delta:.1f}")
            if delta > self.timeout:
                logger.debug("[Idle Timeout] Idle timeout reached. Shutting down.")
                shutdown_server(self.serverapp)
                break
            time.sleep(5)

    def stop(self):
        self._stop_event.set()

class TimeoutActivityTransform(tornado.web.OutputTransform):
    def __init__(self, request):
        super().__init__(request)
        handler = getattr(request, "handler", None)
        if handler is not None:
            app = handler.application
            if hasattr(app, "_timeout_manager"):
                logger.debug("[Idle Timeout] touch() via HTTP request")
                app._timeout_manager.touch()

    def transform_first_chunk(self, status_code, headers, chunk, finishing):
        return status_code, headers, chunk

    def transform_chunk(self, chunk, finishing):
        return chunk

def patch_kernel_websocket_handler():
    try:
        from jupyter_server.services.kernels.websocket import KernelWebsocketHandler
        orig_on_message = KernelWebsocketHandler.on_message
        def on_message_with_touch(self, message):
            if hasattr(self.application, "_timeout_manager"):
                logger.debug("[Idle Timeout] touch() via WebSocket message (KernelWebsocketHandler)")
                self.application._timeout_manager.touch()
            return orig_on_message(self, message)
        KernelWebsocketHandler.on_message = on_message_with_touch
        logger.debug("[Idle Timeout] Patched KernelWebsocketHandler.on_message for idle reset.")
    except Exception as e:
        logger.debug(f"[Idle Timeout] Could not patch KernelWebsocketHandler: {e}")
