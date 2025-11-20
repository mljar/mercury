import json

import tornado
from jupyter_server.base.handlers import APIHandler

from .handlers import THEME


class ThemeHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps(THEME))
