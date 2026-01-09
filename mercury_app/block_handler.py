# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from tornado.web import HTTPError, RequestHandler

BLOCKED_PATTERNS = [
    # JupyterLab UI + API
    r"/lab(?!/(?:extensions/|api/settings(?:/|$)|api/translations(?:/|$)))(?:/.*)?"
    r"/api/terminals(?:/.*)?",
    r"/api/shutdown(?:/.*)?",
    r"/files(?:/.*)?",
]

class BlockedHandler(RequestHandler):
    def prepare(self):
        raise HTTPError(403, reason="This endpoint is disabled")
