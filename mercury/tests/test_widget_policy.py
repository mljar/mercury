"""An app viewer may change inputs, never another viewer's widget code."""

import pytest

from mercury_app.execution.policy import ExecutionDenied
from mercury_app.execution.widget_policy import WidgetPolicy


def policy(identity="mercury.text.TextInputWidget"):
    return WidgetPolicy.from_state(
        {"_model_module": "anywidget", "_anywidget_id": identity}
    )


@pytest.mark.parametrize(
    "field",
    [
        "_esm",
        "_css",
        "_model_module",
        "_model_name",
        "_view_module",
        "_anywidget_id",
        "label",
        "layout",
        "disabled",
        "source_cell_id",
    ],
)
def test_browser_cannot_change_notebook_owned_fields(field):
    with pytest.raises(ExecutionDenied, match="owned by the notebook"):
        policy().authorize({"method": "update", "state": {field: "untrusted"}}, [])


@pytest.mark.parametrize(
    "identity,state",
    [
        ("mercury.text.TextInputWidget", {"value": "hello", "cell_id": "cell"}),
        ("mercury.number.NumberInputWidget", {"value": 7}),
        ("mercury.button.ButtonWidget", {"value": True, "n_clicks": 1}),
        ("mercury.checkbox.CheckboxWidget", {"value": True, "n_toggles": 1}),
        (
            "mercury.file.UploadFileWidget",
            {"filenames": ["sample.txt"], "file_sizes": [3], "revision": 1},
        ),
        (
            "mercury.camera.CameraWidget",
            {"mime_type": "image/png", "byte_size": 12, "revision": 1},
        ),
        (
            "mercury.table.TableWidget",
            {"selected_rows": [{"name": "sample"}], "table_page": 2},
        ),
    ],
)
def test_browser_input_updates_are_allowed(identity, state):
    policy(identity).authorize({"method": "update", "state": state}, [])


@pytest.mark.parametrize(
    "identity,event",
    [
        ("mercury.file.UploadFileWidget", "upload_files"),
        ("mercury.file.UploadFileWidget", "remove_file"),
        ("mercury.camera.CameraWidget", "capture"),
        ("mercury.microphone.MicrophoneWidget", "recording"),
        ("mercury.examples.ExamplesWidget", "apply_example"),
        ("mercury.scenarios.ScenariosWidget", "scenario_save"),
        ("mercury.scenarios.ScenariosWidget", "scenario_load"),
    ],
)
def test_known_mercury_custom_actions_are_allowed(identity, event):
    policy(identity).authorize({"method": "custom", "content": {"event": event}}, [])
    with pytest.raises(ExecutionDenied):
        policy(identity).authorize(
            {"method": "custom", "content": {"event": "eval"}}, []
        )


@pytest.mark.parametrize(
    "model,module",
    [
        ("HTMLModel", "@jupyter-widgets/controls"),
        ("OutputModel", "@jupyter-widgets/output"),
        ("ThirdPartyModel", "unknown"),
    ],
)
def test_output_and_unknown_widgets_are_not_writable(model, module):
    rule = WidgetPolicy.from_state({"_model_name": model, "_model_module": module})
    rule.authorize({"method": "request_state"}, [])
    for field in ("value", "outputs", "_esm"):
        with pytest.raises(ExecutionDenied):
            rule.authorize({"method": "update", "state": {field: "payload"}}, [])


def test_standard_ipywidgets_input_still_accepts_values():
    rule = WidgetPolicy.from_state(
        {"_model_name": "TextModel", "_model_module": "@jupyter-widgets/controls"}
    )
    rule.authorize({"method": "update", "state": {"value": "hello"}}, [])
    with pytest.raises(ExecutionDenied):
        rule.authorize(
            {"method": "update", "state": {"description": "<img onerror=attack()>"}}, []
        )


@pytest.mark.parametrize("path", [["_esm"], ["label"], ["value", "__proto__"]])
def test_binary_paths_cannot_bypass_state_field_policy(path):
    with pytest.raises(ExecutionDenied, match="Binary"):
        policy().authorize(
            {"method": "update", "state": {}, "buffer_paths": [path]}, [b"payload"]
        )


def test_widget_control_only_accepts_state_requests():
    rule = WidgetPolicy(control=True)
    rule.authorize({"method": "request_states"}, [])
    with pytest.raises(ExecutionDenied):
        rule.authorize({"method": "update", "state": {"_esm": "payload"}}, [])
