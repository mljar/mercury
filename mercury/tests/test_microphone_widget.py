import pytest

import mercury as mr
import mercury.microphone as microphone_module
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.microphone import Microphone, MicrophoneWidget
from mercury.render_context import source_cell_context


def setup_function():
    WidgetsManager.widgets.clear()


def teardown_function():
    WidgetsManager.widgets.clear()


def test_microphone_defaults(monkeypatch):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)

    microphone = Microphone()

    assert microphone.label == "Record audio"
    assert microphone.max_duration == 60
    assert microphone.position == "inline"
    assert microphone.disabled is False
    assert microphone.hidden is False
    assert microphone.value is None
    assert microphone.mime_type == ""
    assert microphone.filename == ""
    assert microphone.size == 0
    assert microphone.duration == 0
    assert microphone.revision == 0


def test_microphone_is_exported_from_public_api():
    assert mr.Microphone is Microphone


def test_microphone_passes_configuration(monkeypatch):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)

    microphone = Microphone(
        label="Voice note",
        max_duration=12,
        position="sidebar",
        disabled=True,
        hidden=True,
    )

    assert microphone.label == "Voice note"
    assert microphone.max_duration == 12
    assert microphone.position == "sidebar"
    assert microphone.disabled is True
    assert microphone.hidden is True


@pytest.mark.parametrize("duration", [0, 301, -1])
def test_microphone_rejects_out_of_range_duration(monkeypatch, duration):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)
    with pytest.raises(ValueError, match="max_duration"):
        Microphone(max_duration=duration)


@pytest.mark.parametrize("duration", [1.5, "10", True])
def test_microphone_rejects_non_integer_duration(monkeypatch, duration):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)
    with pytest.raises(TypeError, match="max_duration"):
        Microphone(max_duration=duration)


@pytest.mark.parametrize("argument", [1, None, []])
def test_microphone_rejects_non_string_label(monkeypatch, argument):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)
    with pytest.raises(TypeError, match="label"):
        Microphone(label=argument)


def test_recording_stores_bytes_and_metadata():
    microphone = MicrophoneWidget()

    microphone._handle_microphone_message(
        microphone,
        {
            "event": "recording",
            "mime_type": "audio/webm;codecs=opus",
            "filename": "voice.webm",
            "byte_size": 4,
            "duration": 2.5,
            "revision": 1,
        },
        [b"RIFF"],
    )

    assert microphone.value == b"RIFF"
    assert microphone.mime_type == "audio/webm;codecs=opus"
    assert microphone.filename == "voice.webm"
    assert microphone.size == 4
    assert microphone.duration == pytest.approx(2.5)


def test_recording_requires_one_buffer():
    microphone = MicrophoneWidget()

    with pytest.raises(ValueError, match="exactly one buffer"):
        microphone._handle_microphone_message(
            microphone,
            {
                "event": "recording",
                "mime_type": "audio/webm",
                "byte_size": 1,
                "revision": 1,
            },
            [],
        )


def test_recording_rejects_non_audio_mime_type():
    microphone = MicrophoneWidget()

    with pytest.raises(ValueError, match="audio MIME"):
        microphone._handle_microphone_message(
            microphone,
            {
                "event": "recording",
                "mime_type": "video/webm",
                "byte_size": 1,
                "revision": 1,
            },
            [b"x"],
        )


def test_recording_rejects_incorrect_declared_size():
    microphone = MicrophoneWidget()

    with pytest.raises(ValueError, match="size does not match"):
        microphone._handle_microphone_message(
            microphone,
            {
                "event": "recording",
                "mime_type": "audio/webm",
                "byte_size": 99,
                "revision": 1,
            },
            [b"x"],
        )


def test_record_again_clears_recording():
    microphone = MicrophoneWidget()
    microphone._value = b"old"
    microphone.mime_type = "audio/webm"
    microphone.filename = "old.webm"
    microphone.byte_size = 3
    microphone.duration = 1.25

    microphone._handle_microphone_message(
        microphone, {"event": "clear", "revision": 2}, []
    )

    assert microphone.value is None
    assert microphone.mime_type == ""
    assert microphone.filename == ""
    assert microphone.size == 0
    assert microphone.duration == 0


def test_stale_revision_is_ignored():
    microphone = MicrophoneWidget()
    microphone._last_revision = 3
    microphone._value = b"current"

    microphone._handle_microphone_message(
        microphone, {"event": "clear", "revision": 2}, []
    )

    assert microphone.value == b"current"


def test_microphone_is_cached_by_key(monkeypatch):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)

    first = Microphone(key="voice-note")
    second = Microphone(key="voice-note")

    assert second is first


def test_microphone_refreshes_render_metadata_when_cached(monkeypatch):
    monkeypatch.setattr(microphone_module, "display", lambda *_: None)

    with source_cell_context("microphone-cell"):
        microphone = Microphone(key="voice-note")
    with source_cell_context("rerun-cell"):
        cached = Microphone(key="voice-note")

    assert cached is microphone
    assert cached.source_cell_id == "rerun-cell"


def test_microphone_mimebundle_contains_mercury_metadata():
    microphone = MicrophoneWidget(position="inline")

    data = microphone._repr_mimebundle_()

    assert data[0][MERCURY_MIMETYPE] == {
        "widget": "MicrophoneWidget",
        "model_id": microphone.model_id,
        "position": "inline",
    }
    assert "text/plain" not in data[0]


def test_frontend_waits_for_click_and_records_audio():
    source = MicrophoneWidget._esm

    assert "navigator.mediaDevices.getUserMedia({ audio: true })" in source
    assert "new MediaRecorder" in source
    assert "MediaRecorder.isTypeSupported" in source
    assert 'primary.addEventListener("click", handlePrimary)' in source
    assert "syncFromModel();" in source
    assert "void startRecording();" not in source.split("syncFromModel();")[-1]


def test_frontend_transfers_completed_audio_and_cleans_up():
    source = MicrophoneWidget._esm

    assert 'event: "recording"' in source
    assert 'recorder.onstop = finishRecording' in source
    assert "blob.arrayBuffer()" in source
    assert "model.save_changes()" in source
    assert "stream.getTracks().forEach(track => track.stop())" in source
    assert "URL.revokeObjectURL" in source
    assert "return () =>" in source


def test_frontend_saves_only_completed_recording_or_clear():
    source = MicrophoneWidget._esm

    assert source.count("model.save_changes()") == 2
    assert 'event: "clear"' in source
    assert "setTimeout(stopRecording" in source
