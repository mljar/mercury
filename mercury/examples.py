import math
import numbers
import warnings
from collections.abc import Mapping
from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .url_params import is_valid_date, is_valid_datetime_local, is_valid_time

Position = Literal["sidebar", "inline", "bottom"]


def _normalize_examples(examples):
    if not isinstance(examples, Mapping) or not examples:
        raise ValueError("Examples examples must be a non-empty mapping.")

    normalized = {}
    for name, values in examples.items():
        if not isinstance(name, str) or not name.strip():
            raise TypeError("Examples names must be non-empty strings.")
        if not isinstance(values, Mapping):
            raise TypeError(f"Examples entry {name!r} must be a mapping.")
        normalized_values = {}
        for identifier, value in values.items():
            if not isinstance(identifier, str) or not identifier.strip():
                raise TypeError("Examples widget identifiers must be non-empty strings.")
            normalized_values[identifier] = value
        normalized[name] = normalized_values
    return normalized


def Examples(
    examples,
    position: Position = "sidebar",
    key: str = "",
):
    """Display named examples that populate existing Mercury input widgets.

    Example field names resolve against input widget ``key`` values first and then
    ``url_key`` values. Define this component after its target inputs and before the
    cells that consume their values.

    Parameters
    ----------
    examples : mapping[str, mapping[str, object]]
        Ordered example names and explicit input values.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"sidebar"``.
    key : str, optional
        Stable identifier used to reuse the component across cell executions.

    Returns
    -------
    ExamplesWidget
        The displayed examples component.
    """
    normalized = _normalize_examples(examples)
    identity_args = [] if key else [normalized]
    identity_kwargs = {} if key else {"position": position}
    code_uid = WidgetsManager.get_code_uid(
        "Examples", key=key, args=identity_args, kwargs=identity_kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        cached.configure(normalized, position=position)
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    widget = ExamplesWidget(
        examples=normalized,
        position=position,
        **with_widget_render_metadata({}),
    )
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget


def _normalize_widget_value(widget, value):
    trait = widget.traits().get("value")
    if trait is None:
        raise ValueError("does not expose a supported value")

    widget_type = type(widget).__name__
    if widget_type in {"NumberInputWidget", "SliderWidget"} and isinstance(
        value, bool
    ):
        raise ValueError("must be a finite number")

    try:
        normalized = trait._validate(widget, value)
    except Exception as exc:
        raise ValueError("has an invalid value type") from exc

    if widget_type in {"NumberInputWidget", "SliderWidget"}:
        if (
            isinstance(normalized, bool)
            or not isinstance(normalized, numbers.Real)
            or not math.isfinite(float(normalized))
        ):
            raise ValueError("must be a finite number")
        if normalized < widget.min or normalized > widget.max:
            raise ValueError(f"must be between {widget.min} and {widget.max}")

    if widget_type == "SelectWidget" and normalized not in widget.choices:
        raise ValueError("must be one of the widget choices")

    if widget_type == "MultiSelectWidget":
        invalid = [item for item in normalized if item not in widget.choices]
        if invalid:
            raise ValueError(f"contains unknown choices: {', '.join(invalid)}")

    if widget_type in {"DateInputWidget", "TimeInputWidget", "DateTimeInputWidget"}:
        validator = {
            "DateInputWidget": is_valid_date,
            "TimeInputWidget": is_valid_time,
            "DateTimeInputWidget": is_valid_datetime_local,
        }[widget_type]
        if normalized and not validator(normalized):
            raise ValueError("has an invalid date or time format")
        if widget_type == "DateTimeInputWidget":
            normalized = normalized.replace("T", " ", 1)
        if widget.min and normalized < widget.min:
            raise ValueError(f"must not be earlier than {widget.min}")
        if widget.max and normalized > widget.max:
            raise ValueError(f"must not be later than {widget.max}")

    if widget_type == "DateRangeWidget":
        if len(normalized) != 2:
            raise ValueError("must contain a start and end date")
        start, end = normalized
        if (start and not is_valid_date(start)) or (end and not is_valid_date(end)):
            raise ValueError("must contain valid YYYY-MM-DD dates")
        if start > end:
            raise ValueError("must have a start date before its end date")
        if widget.min and start < widget.min:
            raise ValueError(f"must not start before {widget.min}")
        if widget.max and end > widget.max:
            raise ValueError(f"must not end after {widget.max}")

    return normalized


class ExamplesWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const root = document.createElement("section");
      root.className = "mljar-examples";

      const heading = document.createElement("h3");
      heading.className = "mljar-examples-heading";
      heading.textContent = "Examples";

      const buttons = document.createElement("div");
      buttons.className = "mljar-examples-buttons";

      const warning = document.createElement("div");
      warning.className = "mljar-examples-warning";
      warning.setAttribute("role", "status");
      warning.setAttribute("aria-live", "polite");

      root.append(heading, buttons, warning);
      el.appendChild(root);

      let busy = false;
      let requestId = "";
      let requestSequence = 0;

      function drawState() {
        const selected = model.get("selected") || "";
        const messages = model.get("warning_messages") || [];
        Array.from(buttons.children).forEach(button => {
          const active = button.dataset.name === selected;
          button.classList.toggle("is-selected", active);
          button.setAttribute("aria-pressed", String(active));
          button.disabled = busy;
        });
        warning.textContent = messages.length
          ? `⚠ ${messages.join(" ")}`
          : "";
        warning.hidden = messages.length === 0;
        root.classList.toggle("is-busy", busy);
        root.setAttribute("aria-busy", String(busy));
      }

      function choose(name) {
        if (busy) return;
        busy = true;
        requestSequence += 1;
        requestId = `${model.model_id}-${Date.now()}-${requestSequence}`;
        drawState();
        model.send({
          event: "apply_example",
          name,
          request_id: requestId,
        });
      }

      function drawButtons() {
        buttons.replaceChildren();
        (model.get("labels") || []).forEach(name => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "mljar-examples-button";
          button.dataset.name = name;
          button.textContent = name;
          button.addEventListener("click", () => choose(name));
          buttons.appendChild(button);
        });
        drawState();
      }

      function handleMessage(content) {
        if (content?.event !== "example_applied") return;
        if (content.request_id !== requestId) return;
        busy = false;
        drawState();
        if (content.changed) {
          model.set("apply_tick", (model.get("apply_tick") || 0) + 1);
          model.save_changes();
        }
      }

      model.on("change:labels", drawButtons);
      model.on("change:selected", drawState);
      model.on("change:warning_messages", drawState);
      model.on("msg:custom", handleMessage);
      drawButtons();

      return () => {
        model.off("change:labels", drawButtons);
        model.off("change:selected", drawState);
        model.off("change:warning_messages", drawState);
        model.off("msg:custom", handleMessage);
      };
    }
    export default { render };
    """

    _css = """
    .mljar-examples {
      width: 100%;
      padding: 4px;
      color: var(--mercury-text-color, #0f172a);
      font-family: var(--mercury-font-family, Arial, sans-serif);
      box-sizing: border-box;
    }
    .mljar-examples-heading {
      margin: 0 0 8px;
      color: inherit;
      font-family: var(--mercury-heading-font-family, inherit);
      font-size: var(--mercury-font-size, 14px);
      font-weight: var(--mercury-heading-font-weight, 700);
    }
    .mljar-examples-buttons {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }
    .mljar-examples-button {
      width: 100%;
      min-height: 38px;
      padding: 8px 12px;
      border: 1px solid var(--mercury-border-color, #d0d7de);
      border-radius: var(--mercury-border-radius, 8px) !important;
      background: var(--mercury-widget-background-color, var(--mercury-card-background-color, #ffffff));
      color: var(--mercury-text-color, #0f172a);
      font: inherit;
      font-weight: 600;
      text-align: left;
      cursor: pointer;
      transition: border-color 120ms ease, background-color 120ms ease,
                  color 120ms ease;
    }
    .mljar-examples-button:hover:not(:disabled) {
      border-color: var(--mercury-primary-color, #007bff);
      background: var(--mercury-hover-background-color, #f8fafc);
    }
    .mljar-examples-button:focus-visible {
      outline: 2px solid var(--mercury-focus-border-color, var(--mercury-accent-color, #4c7cf0));
      outline-offset: 2px;
    }
    .mljar-examples-button.is-selected {
      border-color: var(--mercury-primary-color, #007bff);
      background: var(--mercury-selected-background-color, #eef3ff);
      color: var(--mercury-primary-color, #007bff);
    }
    .mljar-examples-button:disabled {
      cursor: wait;
      opacity: 0.72;
    }
    .mljar-examples-warning {
      margin-top: 8px;
      color: var(--mercury-warning-color, #b45309);
      font-size: 0.9em;
      line-height: 1.4;
    }
    .mljar-examples-warning[hidden] {
      display: none;
    }
    @media (prefers-reduced-motion: reduce) {
      .mljar-examples-button { transition: none; }
    }
    """

    labels = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    selected = traitlets.Unicode(default_value="").tag(sync=True)
    warning_messages = traitlets.List(
        traitlets.Unicode(), default_value=[]
    ).tag(sync=True)
    apply_tick = traitlets.Int(default_value=0).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"], default_value="sidebar"
    ).tag(sync=True)
    cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, examples, position="sidebar", **kwargs):
        normalized = _normalize_examples(examples)
        self._examples = normalized
        super().__init__(labels=list(normalized), position=position, **kwargs)
        self.on_msg(self._handle_example_message)

    def configure(self, examples, position=None):
        """Replace the available examples without applying one."""
        normalized = _normalize_examples(examples)
        self._examples = normalized
        with self.hold_trait_notifications():
            self.labels = list(normalized)
            if self.selected not in normalized:
                self.selected = ""
            self.warning_messages = []
            if position is not None:
                self.position = position
        return self

    def _apply_example(self, name):
        messages = []
        updates = []
        values = self._examples.get(name)
        if values is None:
            return False, [f"Unknown example: {name}."]

        for identifier, value in values.items():
            source, matches = WidgetsManager.resolve_input(identifier)
            if not matches:
                messages.append(f"Widget not found: {identifier}.")
                continue
            if len(matches) > 1:
                messages.append(
                    f"Ambiguous {source} {identifier!r}: {len(matches)} widgets found."
                )
                continue

            widget = matches[0].widget
            try:
                normalized = _normalize_widget_value(widget, value)
            except ValueError as exc:
                messages.append(f"Invalid value for {identifier!r}: {exc}.")
                continue
            if widget.value != normalized:
                updates.append((widget, normalized))

        changed = False
        for widget, value in updates:
            try:
                widget.value = value
                changed = True
            except Exception as exc:
                messages.append(
                    f"Could not update {type(widget).__name__}: {exc}."
                )

        return changed, messages

    def _handle_example_message(self, _widget, content, _buffers):
        if content.get("event") != "apply_example":
            return
        request_id = content.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            return

        name = content.get("name")
        changed, messages = self._apply_example(name)
        self.selected = name if isinstance(name, str) and name in self._examples else ""
        self.warning_messages = messages
        self.send(
            {
                "event": "example_applied",
                "request_id": request_id,
                "changed": changed,
            }
        )
        if messages:
            warnings.warn("Examples: " + " ".join(messages), UserWarning, stacklevel=2)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        bundle = data[0] if isinstance(data, tuple) else data
        widget_mimetype = "application/vnd.jupyter.widget-view+json"
        if isinstance(bundle, dict) and widget_mimetype in bundle:
            bundle[MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            bundle.pop("text/plain", None)
        return data
