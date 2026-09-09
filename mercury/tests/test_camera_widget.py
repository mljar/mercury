import pytest

import mercury as mr
import mercury.camera as camera_module
from mercury.camera import Camera, CameraWidget
from mercury.manager import MERCURY_MIMETYPE, WidgetsManager
from mercury.render_context import source_cell_context


def setup_function():
    WidgetsManager.widgets.clear()


def teardown_function():
    WidgetsManager.widgets.clear()


def test_camera_defaults(monkeypatch):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)

    camera = Camera()

    assert camera.mode == "photo"
    assert camera.label == "Camera"
    assert camera.facing_mode == "environment"
    assert camera.max_duration == 30
    assert camera.audio is False
    assert camera.position == "inline"
    assert camera.disabled is False
    assert camera.hidden is False
    assert camera.value is None
    assert camera.mime_type == ""
    assert camera.filename == ""
    assert camera.size == 0
    assert camera.duration == 0
    assert camera.revision == 0


def test_camera_is_exported_from_public_api():
    assert mr.Camera is Camera


def test_camera_passes_configuration(monkeypatch):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)

    camera = Camera(
        mode="video",
        label="Record",
        facing_mode="user",
        max_duration=12,
        audio=True,
        position="sidebar",
        disabled=True,
        hidden=True,
    )

    assert camera.mode == "video"
    assert camera.label == "Record"
    assert camera.facing_mode == "user"
    assert camera.max_duration == 12
    assert camera.audio is True
    assert camera.position == "sidebar"
    assert camera.disabled is True
    assert camera.hidden is True


@pytest.mark.parametrize("mode", ["still", "", None])
def test_camera_rejects_invalid_mode(monkeypatch, mode):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)
    with pytest.raises(ValueError, match="mode"):
        Camera(mode=mode)


@pytest.mark.parametrize("facing", ["front", "rear", "", None])
def test_camera_rejects_invalid_facing_mode(monkeypatch, facing):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)
    with pytest.raises(ValueError, match="facing_mode"):
        Camera(facing_mode=facing)


@pytest.mark.parametrize("duration", [0, 301, -1])
def test_camera_rejects_out_of_range_duration(monkeypatch, duration):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)
    with pytest.raises(ValueError, match="max_duration"):
        Camera(max_duration=duration)


@pytest.mark.parametrize("duration", [1.5, "10", True])
def test_camera_rejects_non_integer_duration(monkeypatch, duration):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)
    with pytest.raises(TypeError, match="max_duration"):
        Camera(max_duration=duration)


def test_photo_capture_stores_bytes_and_metadata():
    camera = CameraWidget(mode="photo")

    camera._handle_camera_message(
        camera,
        {
            "event": "capture",
            "mime_type": "image/jpeg",
            "filename": "camera.jpg",
            "byte_size": 4,
            "duration": 0,
            "revision": 1,
        },
        [b"JPEG"],
    )

    assert camera.value == b"JPEG"
    assert camera.mime_type == "image/jpeg"
    assert camera.filename == "camera.jpg"
    assert camera.size == 4
    assert camera.duration == 0


def test_video_capture_stores_duration():
    camera = CameraWidget(mode="video")

    camera._handle_camera_message(
        camera,
        {
            "event": "capture",
            "mime_type": "video/webm;codecs=vp8",
            "filename": "camera.webm",
            "byte_size": 3,
            "duration": 2.75,
            "revision": 1,
        },
        [b"VID"],
    )

    assert camera.value == b"VID"
    assert camera.mime_type == "video/webm;codecs=vp8"
    assert camera.filename == "camera.webm"
    assert camera.duration == pytest.approx(2.75)


def test_capture_requires_one_matching_buffer():
    camera = CameraWidget(mode="photo")
    content = {
        "event": "capture",
        "mime_type": "image/jpeg",
        "byte_size": 1,
        "revision": 1,
    }

    with pytest.raises(ValueError, match="exactly one buffer"):
        camera._handle_camera_message(camera, content, [])


def test_capture_rejects_wrong_mime_family():
    camera = CameraWidget(mode="photo")

    with pytest.raises(ValueError, match="expected an image MIME"):
        camera._handle_camera_message(
            camera,
            {
                "event": "capture",
                "mime_type": "video/webm",
                "byte_size": 1,
                "revision": 1,
            },
            [b"x"],
        )


def test_capture_rejects_incorrect_declared_size():
    camera = CameraWidget(mode="video")

    with pytest.raises(ValueError, match="size does not match"):
        camera._handle_camera_message(
            camera,
            {
                "event": "capture",
                "mime_type": "video/webm",
                "byte_size": 99,
                "revision": 1,
            },
            [b"x"],
        )


def test_retake_clears_capture():
    camera = CameraWidget(mode="photo")
    camera._value = b"old"
    camera.mime_type = "image/jpeg"
    camera.filename = "old.jpg"
    camera.byte_size = 3

    camera._handle_camera_message(
        camera, {"event": "clear", "revision": 2}, []
    )

    assert camera.value is None
    assert camera.mime_type == ""
    assert camera.filename == ""
    assert camera.size == 0


def test_stale_revision_is_ignored():
    camera = CameraWidget(mode="photo")
    camera._last_revision = 3
    camera._value = b"current"

    camera._handle_camera_message(
        camera, {"event": "clear", "revision": 2}, []
    )

    assert camera.value == b"current"


def test_camera_is_cached_by_key(monkeypatch):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)

    first = Camera(key="document-camera")
    second = Camera(key="document-camera")

    assert second is first


def test_camera_refreshes_render_metadata_when_cached(monkeypatch):
    monkeypatch.setattr(camera_module, "display", lambda *_: None)

    with source_cell_context("camera-cell"):
        camera = Camera(key="document-camera")
    with source_cell_context("rerun-cell"):
        cached = Camera(key="document-camera")

    assert cached is camera
    assert cached.source_cell_id == "rerun-cell"


def test_camera_mimebundle_contains_mercury_metadata():
    camera = CameraWidget(position="inline")

    data = camera._repr_mimebundle_()

    assert data[0][MERCURY_MIMETYPE] == {
        "widget": "CameraWidget",
        "model_id": camera.model_id,
        "position": "inline",
    }
    assert "text/plain" not in data[0]


def test_frontend_has_live_preview_capture_recording_and_cleanup():
    source = CameraWidget._esm

    assert "navigator.mediaDevices.getUserMedia" in source
    assert "liveVideo.srcObject = stream" in source
    assert "context.drawImage(liveVideo" in source
    assert "canvas.toBlob" in source
    assert "new MediaRecorder" in source
    assert "MediaRecorder.isTypeSupported" in source
    assert 'model.send({' in source
    assert 'event: "capture"' in source
    assert "model.save_changes()" in source
    assert "stream.getTracks().forEach(track => track.stop())" in source
    assert "URL.revokeObjectURL" in source
    assert "return () =>" in source


def test_frontend_only_saves_on_completed_capture_or_clear():
    source = CameraWidget._esm

    assert source.count("model.save_changes()") == 2
    assert 'event: "clear"' in source
    assert 'recorder.onstop = () =>' in source


def test_camera_layout_prevents_horizontal_overflow():
    css = CameraWidget._css

    assert "overflow-x: hidden" in css
    assert css.count("max-width: 100%") >= 3
    assert "flex-wrap: wrap" in css
    assert "overflow-wrap: anywhere" in css
