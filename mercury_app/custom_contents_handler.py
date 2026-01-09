# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import datetime

from jupyter_server.services.contents.handlers import ContentsHandler
from jupyter_server.utils import ensure_async
from tornado.web import HTTPError


def convert_datetimes(obj):
    if isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(i) for i in obj]
    elif isinstance(obj, datetime.datetime):
        dt = obj
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        try:
            dt = dt.astimezone(datetime.timezone.utc)
        except Exception:
            pass
        iso = dt.isoformat()
        if iso.endswith("+00:00"):
            iso = iso[:-6] + "Z"
        return iso
    else:
        return obj

class MercuryContentsHandler(ContentsHandler):
    async def get(self, path=""):
        if path.endswith("/checkpoints"):
            return await super().get(path)
        model = await ensure_async(self.contents_manager.get(path, content=True, type=None, format=None))
        model = convert_datetimes(model)
        self.set_header("Content-Type", "application/json")
        self.finish(model)

    async def put(self, path=""):
        model = await ensure_async(self.contents_manager.get(path, content=True, type=None, format=None))
        model = convert_datetimes(model)
        self.set_header("Content-Type", "application/json")
        self.finish(model)

    async def patch(self, path=""):
        # Block patching!
        raise HTTPError(403, reason="Patching notebooks is disabled in this application.")

    async def post(self, path=""):
        # Block creating!
        raise HTTPError(403, reason="Creating notebooks is disabled in this application.")

    async def delete(self, path=""):
        # Optional: Block deleting notebooks
        raise HTTPError(403, reason="Deleting notebooks is disabled in this application.")
