"""Public application views of Jupyter services intended for notebook authors."""

import json

from jupyter_server.auth.decorator import authorized
from jupyter_server.services.events.handlers import SubscribeWebsocket
from jupyter_server.services.kernelspecs.handlers import (
    KernelSpecsAPIHandler,
    is_kernelspec_model,
)
from jupyter_server.utils import ensure_async, url_unescape
from tornado import web


def public_kernel_spec(name, spec):
    """Expose display fields, never launch arguments, environment, or files."""
    if is_kernelspec_model(spec):
        spec = spec["spec"]
    return {
        "name": name,
        "spec": {
            "display_name": spec.get("display_name", name),
            "language": spec.get("language", ""),
            # JupyterLab's client validator expects an argv array.
            "argv": [],
            "env": {},
        },
        "resources": {},
    }


class MercuryKernelSpecsHandler(KernelSpecsAPIHandler):
    @web.authenticated
    @authorized
    async def get(self, kernel_name=None):
        manager = self.kernel_spec_manager
        if kernel_name is not None:
            name = url_unescape(kernel_name)
            try:
                spec = await ensure_async(manager.get_kernel_spec(name))
            except KeyError as exc:
                raise web.HTTPError(404, reason="Kernel spec does not exist") from exc
            model = public_kernel_spec(
                name, spec if is_kernelspec_model(spec) else spec.to_dict()
            )
        else:
            specs = await ensure_async(manager.get_all_specs())
            model = {
                "default": self.kernel_manager.default_kernel_name,
                "kernelspecs": {
                    name: public_kernel_spec(
                        name, info if is_kernelspec_model(info) else info["spec"]
                    )
                    for name, info in specs.items()
                },
            }
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(model))


class MercuryEventsWebsocket(SubscribeWebsocket):
    """Keep the client event connection alive without sharing server-wide events.

    Mercury uses kernel channels and its own shared-session coordinator. The
    generic JupyterLab service manager also opens an events connection, but
    application viewers must not subscribe to other browsers' server activity.
    """

    def open(self):
        pass

    def on_close(self):
        pass
