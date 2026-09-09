import hashlib
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

MERCURY_MIMETYPE = "application/mercury+json"


class WidgetException(Exception):
    pass


@dataclass(frozen=True)
class InputWidgetRegistration:
    """Search metadata for a value-bearing Mercury input widget."""

    code_uid: str
    widget: object
    key: str = ""
    url_key: str = ""


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
    input_widgets = {}  # code_uid -> InputWidgetRegistration

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
    def register_input(code_uid, widget, key="", url_key=""):
        """Register explicit lookup aliases for a supported input widget."""
        WidgetsManager.input_widgets[code_uid] = InputWidgetRegistration(
            code_uid=code_uid,
            widget=widget,
            key=key,
            url_key=url_key,
        )

    @staticmethod
    def resolve_input(identifier):
        """Resolve by key first and then by url_key.

        Returns ``(source, matches)`` where source is ``"key"``, ``"url_key"``,
        or ``None``. Stale registrations are ignored.
        """
        active = [
            registration
            for code_uid, registration in WidgetsManager.input_widgets.items()
            if WidgetsManager.widgets.get(code_uid) is registration.widget
        ]
        key_matches = [item for item in active if item.key and item.key == identifier]
        if key_matches:
            return "key", key_matches
        url_matches = [
            item for item in active if item.url_key and item.url_key == identifier
        ]
        if url_matches:
            return "url_key", url_matches
        return None, []

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
