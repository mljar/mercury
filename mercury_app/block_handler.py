# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import re

from tornado.routing import PathMatches, Rule
from tornado.web import HTTPError, RequestHandler

BLOCKED_PATTERNS = [
    # JupyterLab UI + API
    r"/lab(?!/(?:extensions/|api/settings(?:/|$)|api/translations(?:/|$)))(?:/.*)?",
    r"/api/terminals(?:/.*)?",
    r"/terminals(?:/.*)?",
    r"/api/config(?:/.*)?",
    r"/api/nbconvert(?:/.*)?",
    r"/nbconvert(?:/.*)?",
    r"/api/shutdown(?:/.*)?",
    r"/api/contents(?:/.*)?",
    r"/files(?:/.*)?",
]


class ReadOnlyPathMatches(PathMatches):
    """Match forbidden methods, leaving reads to the original Jupyter handler."""

    def match(self, request):
        if request.method in {"GET", "HEAD"}:
            return None
        return super().match(request)


def build_block_rules(base_url="", settings_url="/lab/api/settings"):
    prefix = re.escape(base_url.rstrip("/"))
    rules = [
        Rule(PathMatches(prefix + pattern), BlockedHandler)
        for pattern in BLOCKED_PATTERNS
    ]
    # Cover the stock Lab endpoint as well as a configured Mercury settings URL.
    for path in sorted({"/lab/api/settings", settings_url.rstrip("/")}):
        if path.startswith("/"):
            pattern = prefix + re.escape(path) + r"(?:/.*)?"
            rules.append(Rule(ReadOnlyPathMatches(pattern), BlockedHandler))
    return rules


class BlockedHandler(RequestHandler):
    def prepare(self):
        raise HTTPError(403, reason="This endpoint is disabled")
