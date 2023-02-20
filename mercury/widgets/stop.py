import os


class StopExecution(Exception):
    def _render_traceback_(self):
        if os.environ.get("RUN_MERCURY") is not None:
            return ["StopExecution"]
        pass


def Stop():
    raise StopExecution()
