try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings

    warnings.warn("Importing 'mercury_app' outside a proper installation.")
    __version__ = "dev"


def __getattr__(name):
    if name == "MercuryApp":
        from .app import MercuryApp

        return MercuryApp
    if name == "_load_jupyter_server_extension":
        from .serverextension import _load_jupyter_server_extension

        return _load_jupyter_server_extension
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "@mljar/mercury-extension"}]


def _jupyter_server_extension_points():
    from .app import MercuryApp

    return [{"module": "mercury_app", "app": MercuryApp}]


def _load_jupyter_server_extension(serverapp):
    from .serverextension import _load_jupyter_server_extension as _load_impl

    return _load_impl(serverapp)
