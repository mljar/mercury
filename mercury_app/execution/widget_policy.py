"""Separate browser input from kernel-owned widget code and presentation.

Jupyter trusts its browser as a notebook author. A Mercury viewer is instead an
untrusted application user, including when several viewers share one kernel.
Only identities observed in kernel messages can select a browser-write policy.
Unknown widgets remain renderable and readable, but cannot accept arbitrary
state updates or custom commands in standalone mode.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from .policy import ExecutionDenied

INPUT_FIELDS = {
    "mercury.text.TextInputWidget": {"value", "cell_id"},
    "mercury.number.NumberInputWidget": {"value", "cell_id"},
    "mercury.slider.SliderWidget": {"value", "cell_id"},
    "mercury.checkbox.CheckboxWidget": {
        "value",
        "cell_id",
        "n_toggles",
        "last_changed_at",
    },
    "mercury.button.ButtonWidget": {"value", "n_clicks", "last_clicked_at"},
    "mercury.select.SelectWidget": {"value"},
    "mercury.multiselect.MultiSelectWidget": {"value"},
    "mercury.date.DateInputWidget": {"value"},
    "mercury.time.TimeInputWidget": {"value"},
    "mercury.datetime_input.DateTimeInputWidget": {"value"},
    "mercury.daterange.DateRangeWidget": {"value"},
    "mercury.chat.chatinput.ChatInputWidget": {"value", "submitted"},
    "mercury.tabs._TabsHeaderWidget": {"active"},
    "mercury.expander._ExpanderHeaderWidget": {"expanded"},
    "mercury.examples.ExamplesWidget": {"apply_tick"},
    "mercury.file.UploadFileWidget": {"filenames", "file_sizes", "revision", "cell_id"},
    "mercury.camera.CameraWidget": {
        "mime_type",
        "filename",
        "byte_size",
        "duration",
        "revision",
    },
    "mercury.microphone.MicrophoneWidget": {
        "mime_type",
        "filename",
        "byte_size",
        "duration",
        "revision",
    },
    "mercury.table.TableWidget": {
        "_id_selected_rows",
        "selected_rows",
        "table_sort_column",
        "table_sort_direction",
        "table_page",
        "table_search_query",
    },
}

CUSTOM_EVENTS = {
    "mercury.file.UploadFileWidget": {"upload_files", "remove_file"},
    "mercury.camera.CameraWidget": {"capture", "clear"},
    "mercury.microphone.MicrophoneWidget": {"recording", "clear"},
    "mercury.examples.ExamplesWidget": {"apply_example"},
    "mercury.scenarios.ScenariosWidget": {"scenario_save", "scenario_load"},
}

# Standard ipywidgets controls are also common in Mercury notebooks. Output
# widgets (notably HTML and Output) deliberately have no writable value/outputs.
CONTROL_FIELDS = {
    **{
        name: {"value"}
        for name in (
            "TextModel",
            "TextareaModel",
            "PasswordModel",
            "ComboboxModel",
            "CheckboxModel",
            "ToggleButtonModel",
            "IntTextModel",
            "FloatTextModel",
            "BoundedIntTextModel",
            "BoundedFloatTextModel",
            "IntSliderModel",
            "FloatSliderModel",
            "FloatLogSliderModel",
            "IntRangeSliderModel",
            "FloatRangeSliderModel",
            "DatePickerModel",
            "TimePickerModel",
            "DatetimeModel",
            "NaiveDatetimeModel",
            "ColorPickerModel",
            "PlayModel",
        )
    },
    **{
        name: {"index"}
        for name in (
            "DropdownModel",
            "RadioButtonsModel",
            "SelectModel",
            "SelectMultipleModel",
            "SelectionSliderModel",
            "SelectionRangeSliderModel",
            "ToggleButtonsModel",
        )
    },
    "TabModel": {"selected_index"},
    "AccordionModel": {"selected_index"},
}


@dataclass(frozen=True)
class WidgetPolicy:
    fields: frozenset[str] = frozenset()
    events: frozenset[str] = frozenset()
    cell_tracking: bool = False
    button: bool = False
    control: bool = False

    @classmethod
    def from_state(cls, state):
        if not isinstance(state, Mapping):
            return cls()
        identity = state.get("_anywidget_id")
        if not isinstance(identity, str):
            identity = ""
        fields = set()
        events = set()
        button = False
        if state.get("_model_module") == "anywidget":
            fields = INPUT_FIELDS.get(identity, set())
            events = CUSTOM_EVENTS.get(identity, set())
        elif state.get("_model_module") == "@jupyter-widgets/controls":
            name = state.get("_model_name")
            fields = CONTROL_FIELDS.get(name, set()) if isinstance(name, str) else set()
            button = name == "ButtonModel"
        return cls(
            frozenset(fields) | {"_view_count"},
            frozenset(events),
            "cell_id" in fields,
            button,
        )

    def authorize(self, data, buffers):
        if not isinstance(data, Mapping):
            raise ExecutionDenied("Malformed widget message")
        method = data.get("method")
        if self.control:
            if method != "request_states" or buffers:
                raise ExecutionDenied("Unsupported widget control request")
            return
        if method == "request_state" and not buffers:
            return
        if method == "update":
            state = data.get("state")
            paths = data.get("buffer_paths", [])
            if not isinstance(state, Mapping) or not isinstance(paths, list):
                raise ExecutionDenied("Malformed widget state update")
            if set(state) - self.fields:
                raise ExecutionDenied("Widget field is owned by the notebook")
            # Mercury's permitted state fields are JSON values, not binary
            # buffers. Media uploads use validated custom messages instead.
            if paths or buffers:
                raise ExecutionDenied("Binary widget state updates are disabled")
            return
        if method == "custom":
            content = data.get("content")
            if not isinstance(content, Mapping):
                raise ExecutionDenied("Malformed custom widget message")
            event = content.get("event")
            if isinstance(event, str) and event in self.events:
                return
            if self.button and event == "click" and not buffers:
                return
            if (
                self.cell_tracking
                and content.get("type") == "cell_id_detected"
                and not buffers
            ):
                return
        raise ExecutionDenied("Widget request is not allowed")
