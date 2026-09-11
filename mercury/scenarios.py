"""Named, browser-local snapshots of an analysis."""

import base64
import copy
import io
import json
import math
import numbers
from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path

import anywidget
import traitlets
from IPython import get_ipython
from IPython.display import display

from .examples import _normalize_widget_value
from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import (
    apply_widget_render_metadata,
    get_effective_source_cell_id,
    with_widget_render_metadata,
)

MAX_ROWS = 5000
MAX_COLUMNS = 100
MAX_SNAPSHOT_BYTES = 5 * 1024 * 1024


def _scalar(value):
    """JSON-safe values, preserving dates and integers outside JS's safe range."""
    if value is None or type(value).__name__ in {"NAType", "NaTType"}:
        return None
    if isinstance(value, (date, datetime)):
        return {"type": "date", "value": value.isoformat()}
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, numbers.Integral):
        value = int(value)
        return (
            value
            if abs(value) <= 2**53 - 1
            else {"type": "integer", "value": str(value)}
        )
    if isinstance(value, numbers.Real):
        value = float(value)
        return value if math.isfinite(value) else None
    # NumPy booleans and scalar strings are not always Python scalar subclasses.
    if type(value).__module__.startswith("numpy") and hasattr(value, "item"):
        return _scalar(value.item())
    raise ValueError(f"Unsupported value type: {type(value).__name__}.")


def _output(value):
    module = type(value).__module__
    if (
        module.startswith(("pandas.", "polars."))
        and type(value).__name__ == "DataFrame"
    ):
        rows, columns = value.shape
        if rows > MAX_ROWS or columns > MAX_COLUMNS:
            raise ValueError(
                f"Tables are limited to {MAX_ROWS:,} rows and {MAX_COLUMNS} columns."
            )
        is_pandas = module.startswith("pandas.")
        data = (
            value.itertuples(index=False, name=None) if is_pandas else value.iter_rows()
        )
        result = {
            "kind": "table",
            "columns": [str(column) for column in value.columns],
            "dtypes": [str(dtype) for dtype in value.dtypes],
            "rows": [[_scalar(item) for item in row] for row in data],
        }
        if is_pandas:
            # Keep named/non-default indexes as a visible row-label column.
            index = value.index
            if (
                type(index).__name__ != "RangeIndex"
                or index.start != 0
                or index.step != 1
                or index.name
            ):
                result["index_name"] = str(index.name or "Index")
                result["index"] = [str(item) for item in index]
        return result
    if module.startswith("matplotlib."):
        figure = value if hasattr(value, "savefig") else getattr(value, "figure", None)
        if figure is None:
            raise ValueError("Pass a Matplotlib Figure or Axes for a plot snapshot.")
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
        return {
            "kind": "plot",
            "mime": "image/png",
            "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
        }
    return {"kind": "scalar", "value": _scalar(value)}


def _mapping(value, name):
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"Scenarios {name} must be a non-empty mapping.")
    if any(not isinstance(label, str) or not label.strip() for label in value):
        raise ValueError(f"Scenarios {name} labels must be non-empty strings.")
    return dict(value)


def Scenarios(inputs, outputs, position="sidebar", key=""):
    """Save and compare inputs, scalars, DataFrames and Matplotlib figures.

    Put this in its own cell below all calculations. Inputs are Mercury widget
    objects; outputs are calculated values. Saved snapshots live in this browser,
    scoped to the app and key, and survive notebook reruns and kernel restarts.
    """
    identity = key or get_effective_source_cell_id() or "default"
    uid = WidgetsManager.get_code_uid("Scenarios", key=identity)
    widget = WidgetsManager.get_widget(uid)
    if widget is None:
        widget = ScenariosWidget(
            storage_key=identity, **with_widget_render_metadata({})
        )
        WidgetsManager.add_widget(uid, widget)
    apply_widget_render_metadata(widget)
    widget.configure(inputs, outputs, position=position)
    display(widget)
    return widget


class ScenariosWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name("_scenarios.js")
    _css = Path(__file__).with_name("_scenarios.css")

    storage_key = traitlets.Unicode("default").tag(sync=True)
    ready = traitlets.Bool(False).tag(sync=True)
    running = traitlets.Bool(False).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)
    position = traitlets.Enum(
        ["sidebar", "inline", "bottom"], default_value="sidebar"
    ).tag(sync=True)
    cell_id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        self._inputs = {}
        self._candidate = None
        self._configured_in_cell = False
        self._shell = get_ipython()
        super().__init__(**kwargs)
        self.on_msg(self._handle_message)
        if self._shell is not None:
            self._shell.events.register("pre_run_cell", self._before_cell)
            self._shell.events.register("post_run_cell", self._after_cell)

    def _before_cell(self, *_):
        self.running = True
        self._configured_in_cell = False

    def _after_cell(self, result):
        self.running = False
        if result.error_before_exec or result.error_in_exec:
            self.ready = False
            self.error = "Execution failed. Re-run the analysis before saving."
        elif self._configured_in_cell and self._candidate is not None:
            self.ready = True

    def _input_changed(self, *_):
        self.ready = False
        self.error = "Inputs changed. Run the analysis before saving."

    def configure(self, inputs, outputs, position="sidebar"):
        self.ready = False
        self._candidate = None
        inputs = _mapping(inputs, "inputs")
        outputs = _mapping(outputs, "outputs")
        for widget in inputs.values():
            # Direct references work without key/url_key, including DateRange.
            if (
                not isinstance(widget, traitlets.HasTraits)
                or "value" not in widget.traits()
            ):
                raise ValueError(
                    "Scenarios inputs must be Mercury input widgets, not their values."
                )
            if type(widget).__name__ not in {
                "NumberInputWidget",
                "SliderWidget",
                "SelectWidget",
                "MultiSelectWidget",
                "TextInputWidget",
                "CheckboxWidget",
                "DateInputWidget",
                "TimeInputWidget",
                "DateTimeInputWidget",
                "DateRangeWidget",
            }:
                raise ValueError(
                    f"Unsupported scenario input: {type(widget).__name__}."
                )
        if len({id(widget) for widget in inputs.values()}) != len(inputs):
            raise ValueError("Each scenario input widget must be provided only once.")
        for widget in self._inputs.values():
            widget.unobserve(self._input_changed, names="value")
        self._inputs = inputs
        for widget in inputs.values():
            widget.observe(self._input_changed, names="value")
        self.position = position
        self.error = ""
        try:
            snapshot = {
                "version": 1,
                "inputs": {
                    label: copy.deepcopy(widget.value)
                    for label, widget in inputs.items()
                },
                "input_types": {
                    label: type(widget).__name__ for label, widget in inputs.items()
                },
                "outputs": {label: _output(value) for label, value in outputs.items()},
            }
            if (
                len(json.dumps(snapshot, allow_nan=False).encode("utf-8"))
                > MAX_SNAPSHOT_BYTES
            ):
                raise ValueError(
                    "Scenario exceeds the 5 MiB snapshot limit. Reduce table or plot sizes."
                )
            self._candidate = snapshot
            self._configured_in_cell = True
            # In a kernel, the post-run hook confirms that this cell succeeded.
            self.ready = self._shell is None
        except (TypeError, ValueError) as exc:
            self.error = str(exc)
        return self

    def snapshot(self, name):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise ValueError("Enter a scenario name of 1–80 characters.")
        if not self.ready or self.running or self._candidate is None:
            raise ValueError(
                self.error or "Wait for the analysis to finish before saving."
            )
        if any(
            widget.value != self._candidate["inputs"][label]
            for label, widget in self._inputs.items()
        ):
            self._input_changed()
            raise ValueError(self.error)
        snapshot = copy.deepcopy(self._candidate)
        snapshot.update(
            name=name.strip(), saved_at=datetime.now(timezone.utc).isoformat()
        )
        return snapshot

    def load(self, snapshot):
        if self.running:
            raise ValueError("Wait for the analysis to finish before loading.")
        if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
            raise ValueError("Unsupported scenario format.")
        values, types = snapshot.get("inputs"), snapshot.get("input_types")
        if (
            not isinstance(values, dict)
            or set(values) != set(self._inputs)
            or not isinstance(types, dict)
        ):
            raise ValueError("Saved inputs do not match this analysis.")
        updates = []
        for label, widget in self._inputs.items():
            if types.get(label) != type(widget).__name__:
                raise ValueError(f"Input type changed: {label}.")
            if getattr(widget, "disabled", False):
                raise ValueError(f"Input is disabled: {label}.")
            try:
                value = _normalize_widget_value(widget, values[label])
            except ValueError as exc:
                raise ValueError(f"{label}: {exc}.") from exc
            if value != widget.value:
                updates.append((widget, value, copy.deepcopy(widget.value)))
        # All values are validated before writing; roll back unexpected setter failures.
        try:
            for widget, value, _ in updates:
                widget.value = value
        except Exception as exc:
            for widget, _, previous in updates:
                widget.value = previous
            raise ValueError(
                "Could not load inputs; previous values were restored."
            ) from exc
        return list(
            dict.fromkeys(
                widget.source_cell_id or widget.cell_id
                for widget, _, _ in updates
                if widget.source_cell_id or widget.cell_id
            )
        ), bool(updates)

    def _handle_message(self, _, content, buffers):
        if not isinstance(content, dict) or not isinstance(
            content.get("request_id"), str
        ):
            return
        request_id = content["request_id"]
        try:
            if content.get("event") == "scenario_save":
                self.send(
                    {
                        "event": "scenario_saved",
                        "request_id": request_id,
                        "snapshot": self.snapshot(content.get("name")),
                    }
                )
            elif content.get("event") == "scenario_load":
                cells, changed = self.load(content.get("snapshot"))
                self.send(
                    {
                        "event": "scenario_loaded",
                        "request_id": request_id,
                        "source_cell_ids": cells,
                        "changed": changed,
                    }
                )
        except (ValueError, TypeError) as exc:
            self.send(
                {
                    "event": "scenario_error",
                    "request_id": request_id,
                    "message": str(exc),
                }
            )

    def close(self):
        for widget in self._inputs.values():
            widget.unobserve(self._input_changed, names="value")
        if self._shell is not None:
            self._shell.events.unregister("pre_run_cell", self._before_cell)
            self._shell.events.unregister("post_run_cell", self._after_cell)
            self._shell = None
        super().close()

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        bundle = data[0] if isinstance(data, tuple) else data
        if isinstance(bundle, dict):
            bundle.pop("text/plain", None)
            bundle[MERCURY_MIMETYPE] = {
                "widget": "ScenariosWidget",
                "model_id": self.model_id,
                "position": self.position,
            }
        return data
