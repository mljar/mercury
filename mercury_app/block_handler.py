from tornado.web import RequestHandler, HTTPError

BLOCKED_PATTERNS = [
    # JupyterLab UI + API
    #r"/lab(?:/.*)?",
    #r"/lab(?!/(?:extensions/|api/settings(?:/|$)))(?:/.*)?",
    r"/lab(?!/(?:extensions/|api/settings(?:/|$)|api/translations(?:/|$)))(?:/.*)?"
    r"/api/terminals(?:/.*)?",
    r"/api/shutdown(?:/.*)?",
    r"/files(?:/.*)?",
]

class BlockedHandler(RequestHandler):
    def prepare(self):
        raise HTTPError(403, reason="This endpoint is disabled")
