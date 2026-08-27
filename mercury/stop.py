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
    Stop the current Mercury notebook execution flow silently.

    This function raises an internal exception that is intercepted
    by Mercury, preventing the rest of the current cell and following
    cells from executing without showing an error or traceback.

    Examples
    --------
    >>> if condition_not_met:
    ...     mr.Stop()
    """
    raise StopExecution()
