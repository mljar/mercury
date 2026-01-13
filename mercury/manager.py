import logging
import hashlib

log = logging.getLogger(__name__)

MERCURY_MIMETYPE = "application/mercury+json"

class WidgetException(Exception):
    pass


def _safe_str(obj):
    """Return a simple, stable string for hashing."""
    if obj is None:
        return "None"
    try:
        return str(obj)
    except Exception:
        try:
            return repr(obj)
        except Exception:
            return "<?>"


def _config_hash(args, kwargs):
    """Create a short, robust hash for widget configuration (excluding 'value')."""
    try:
        # filter out position, because we can have the same widget but displayed in different places
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ("value", "position", "data")
        }

        safe_args = tuple(_safe_str(a) for a in args)
        safe_items = sorted((k, _safe_str(v)) for k, v in filtered_kwargs.items())

        src = repr((safe_args, safe_items))
        result = hashlib.sha1(src.encode("utf-8")).hexdigest()[:8]
        return result
    except Exception:
        return "cfg_hash"


class WidgetsManager:
    widgets = {}  # model_id -> widget

    @staticmethod
    def get_code_uid(widget_type="widget", key="", index=None, args=[], kwargs={}):
        cfg_hash = _config_hash(args, kwargs)
        
        uid = f"{widget_type}.{cfg_hash}"
        
        if index is not None:
            uid += f".{index}"
        if key:
            uid += f".{key}"

        return uid

    @staticmethod
    def add_widget(code_uid, widget):
        WidgetsManager.widgets[code_uid] = widget

    @staticmethod
    def get_widget(code_uid):
        return WidgetsManager.widgets.get(code_uid)

    @staticmethod
    def clear():
        for uid, widget in list(WidgetsManager.widgets.items()):
            try:
                if type(widget).__name__ == "ButtonWidget":
                    if getattr(widget, "value", None) is True:
                        widget.value = False
                elif type(widget).__name__ == "ChatInputWidget":
                    if getattr(widget, "value", "") != "":
                        widget.value = ""
            except Exception as e:
                log.warning(f"Failed to reset widget {uid}: {e}")
