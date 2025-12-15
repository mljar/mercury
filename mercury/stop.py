# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)


class StopExecution(Exception):
    """
    Internal exception used to stop notebook execution without
    displaying a traceback or error message.
    """

    def _render_traceback_(self):
        # Prevent Jupyter from rendering a traceback
        pass


def Stop():
    """
    Stop execution of the current notebook cell silently.

    This function raises an internal exception that is intercepted
    by Jupyter, preventing further execution without showing
    an error or traceback.

    Examples
    --------
    >>> if condition_not_met:
    ...     mr.Stop()
    """
    raise StopExecution()
