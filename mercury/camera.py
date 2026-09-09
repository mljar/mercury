# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from __future__ import annotations

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME

CameraMode = Literal["photo", "video"]
FacingMode = Literal["user", "environment"]
Position = Literal["sidebar", "inline", "bottom"]


def Camera(
    mode: CameraMode = "photo",
    label: str = "Camera",
    facing_mode: FacingMode = "environment",
    max_duration: int = 30,
    audio: bool = False,
    position: Position = "inline",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """Create and display a browser camera with a live preview.

    The camera stream stays in the browser. A completed photo or video is sent to
    Python as bytes and causes the cells below this widget to execute once.

    Parameters
    ----------
    mode : {"photo", "video"}, optional
        Capture a still image or record a video. Default is ``"photo"``.
    label : str, optional
        Text displayed above the camera. Default is ``"Camera"``.
    facing_mode : {"user", "environment"}, optional
        Prefer the front or rear camera. Default is ``"environment"``.
    max_duration : int, optional
        Maximum video duration in seconds, from 1 to 300. Default is ``30``.
    audio : bool, optional
        Request microphone audio for video recordings. Default is ``False``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    disabled : bool, optional
        Disable camera access and controls. Default is ``False``.
    hidden : bool, optional
        Hide the widget and stop its media stream. Default is ``False``.
    key : str, optional
        Stable identifier used to reuse the camera across cell executions.

    Returns
    -------
    CameraWidget
        The displayed widget. ``value`` contains captured bytes or ``None``.
    """
    if mode not in ("photo", "video"):
        raise ValueError("Camera: `mode` must be 'photo' or 'video'.")
    if facing_mode not in ("user", "environment"):
        raise ValueError("Camera: `facing_mode` must be 'user' or 'environment'.")
    if not isinstance(label, str):
        raise TypeError("Camera: `label` must be a string.")
    if isinstance(max_duration, bool) or not isinstance(max_duration, int):
        raise TypeError("Camera: `max_duration` must be an integer.")
    if not 1 <= max_duration <= 300:
        raise ValueError("Camera: `max_duration` must be between 1 and 300 seconds.")
    if not isinstance(audio, bool):
        raise TypeError("Camera: `audio` must be a boolean.")
    if not isinstance(disabled, bool):
        raise TypeError("Camera: `disabled` must be a boolean.")
    if not isinstance(hidden, bool):
        raise TypeError("Camera: `hidden` must be a boolean.")

    kwargs = {
        "mode": mode,
        "label": label,
        "facing_mode": facing_mode,
        "max_duration": max_duration,
        "audio": audio,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }
    code_uid = WidgetsManager.get_code_uid(
        "Camera", key=key, args=[], kwargs=kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = CameraWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class CameraWidget(anywidget.AnyWidget):
    _esm = r"""
function render({ model, el }) {
  el.innerHTML = "";

  const container = document.createElement("div");
  container.className = "mljar-camera";

  const label = document.createElement("div");
  label.className = "mljar-camera-label";

  const viewport = document.createElement("div");
  viewport.className = "mljar-camera-viewport";

  const liveVideo = document.createElement("video");
  liveVideo.className = "mljar-camera-live";
  liveVideo.autoplay = true;
  liveVideo.muted = true;
  liveVideo.playsInline = true;

  const photo = document.createElement("img");
  photo.className = "mljar-camera-result";
  photo.alt = "Captured photo";
  photo.hidden = true;

  const recordingVideo = document.createElement("video");
  recordingVideo.className = "mljar-camera-result";
  recordingVideo.controls = true;
  recordingVideo.playsInline = true;
  recordingVideo.hidden = true;

  const liveBadge = document.createElement("div");
  liveBadge.className = "mljar-camera-live-badge";
  liveBadge.textContent = "LIVE";
  liveBadge.hidden = true;

  const recordingBadge = document.createElement("div");
  recordingBadge.className = "mljar-camera-recording-badge";
  recordingBadge.hidden = true;

  const recordingDot = document.createElement("span");
  recordingDot.className = "mljar-camera-recording-dot";
  const timerText = document.createElement("span");
  timerText.textContent = "00:00";
  recordingBadge.append(recordingDot, timerText);

  const placeholder = document.createElement("div");
  placeholder.className = "mljar-camera-placeholder";
  placeholder.textContent = "Starting camera…";

  const status = document.createElement("div");
  status.className = "mljar-camera-status";
  status.setAttribute("role", "status");

  const controls = document.createElement("div");
  controls.className = "mljar-camera-controls";

  const primary = document.createElement("button");
  primary.type = "button";
  primary.className = "mljar-camera-button mljar-camera-button-primary";

  const retake = document.createElement("button");
  retake.type = "button";
  retake.className = "mljar-camera-button mljar-camera-button-secondary";
  retake.textContent = "Retake";
  retake.hidden = true;

  viewport.append(liveVideo, photo, recordingVideo, liveBadge, recordingBadge, placeholder);
  controls.append(primary, retake);
  container.append(label, viewport, status, controls);
  el.appendChild(container);

  let stream = null;
  let recorder = null;
  let recordedChunks = [];
  let recordingStartedAt = 0;
  let recordingTimeout = null;
  let timerInterval = null;
  let resultUrl = null;
  let disposed = false;
  let starting = false;
  let localRevision = model.get("revision") || 0;

  function clearTimers() {
    if (recordingTimeout !== null) clearTimeout(recordingTimeout);
    if (timerInterval !== null) clearInterval(timerInterval);
    recordingTimeout = null;
    timerInterval = null;
  }

  function revokeResultUrl() {
    if (resultUrl) URL.revokeObjectURL(resultUrl);
    resultUrl = null;
    photo.removeAttribute("src");
    recordingVideo.removeAttribute("src");
    recordingVideo.load();
  }

  function stopStream() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    liveVideo.srcObject = null;
    liveBadge.hidden = true;
  }

  function nextRevision() {
    localRevision = Math.max(localRevision, model.get("revision") || 0) + 1;
    return localRevision;
  }

  function saveCapture(blob, mimeType, filename, duration) {
    retake.disabled = true;
    return blob.arrayBuffer().then(buffer => {
      if (disposed) return;
      const revision = nextRevision();
      model.send({
        event: "capture",
        mime_type: mimeType,
        filename,
        byte_size: blob.size,
        duration,
        revision
      }, {}, [buffer]);
      model.set("mime_type", mimeType);
      model.set("filename", filename);
      model.set("byte_size", blob.size);
      model.set("duration", duration);
      model.set("revision", revision);
      model.save_changes();
    }).catch(() => {
      if (!disposed) status.textContent = "Unable to transfer the capture to Python.";
    }).finally(() => {
      if (!disposed) retake.disabled = !!model.get("disabled");
    });
  }

  function clearCapture() {
    const revision = nextRevision();
    model.send({ event: "clear", revision });
    model.set("mime_type", "");
    model.set("filename", "");
    model.set("byte_size", 0);
    model.set("duration", 0);
    model.set("revision", revision);
    model.save_changes();
  }

  function filename(extension) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `camera-${stamp}.${extension}`;
  }

  function showLive() {
    revokeResultUrl();
    photo.hidden = true;
    recordingVideo.hidden = true;
    liveVideo.hidden = false;
    placeholder.hidden = !!stream;
    liveBadge.hidden = !stream;
    recordingBadge.hidden = true;
    retake.hidden = true;
    primary.hidden = false;
    primary.classList.remove("is-recording");
    primary.textContent = model.get("mode") === "video" ? "Start recording" : "Take photo";
    primary.disabled = !stream || !!model.get("disabled");
    status.textContent = stream ? "Camera preview is live." : "";
  }

  function showError(error) {
    stopStream();
    placeholder.hidden = false;
    placeholder.textContent = "Camera unavailable";
    liveVideo.hidden = true;
    primary.hidden = false;
    primary.textContent = "Try again";
    primary.disabled = !!model.get("disabled");
    if (!window.isSecureContext) {
      status.textContent = "Camera access requires HTTPS or localhost.";
    } else if (error && error.name === "NotAllowedError") {
      status.textContent = "Camera permission was denied. Allow access in your browser and try again.";
    } else if (error && error.name === "NotFoundError") {
      status.textContent = "No camera was found on this device.";
    } else if (error && error.name === "NotReadableError") {
      status.textContent = "The camera is already in use or unavailable.";
    } else {
      status.textContent = "Unable to start the camera.";
    }
  }

  async function startCamera() {
    if (disposed || starting || model.get("disabled") || model.get("hidden")) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError(new Error("getUserMedia is unavailable"));
      return;
    }
    starting = true;
    primary.disabled = true;
    placeholder.hidden = false;
    placeholder.textContent = "Starting camera…";
    status.textContent = "Waiting for camera permission…";
    try {
      stopStream();
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: model.get("facing_mode") || "environment" } },
        audio: model.get("mode") === "video" && !!model.get("audio")
      });
      if (disposed || model.get("disabled") || model.get("hidden")) {
        stopStream();
        return;
      }
      liveVideo.srcObject = stream;
      stream.getVideoTracks().forEach(track => {
        track.addEventListener("ended", () => {
          if (!disposed && stream && stream.getVideoTracks().every(item => item.readyState === "ended")) {
            showError(new Error("Camera stream ended"));
          }
        }, { once: true });
      });
      await liveVideo.play();
      liveVideo.classList.toggle("is-mirrored", model.get("facing_mode") === "user");
      showLive();
    } catch (error) {
      if (!disposed) showError(error);
    } finally {
      starting = false;
    }
  }

  function capturePhoto() {
    if (!stream || !liveVideo.videoWidth || !liveVideo.videoHeight) return;
    primary.disabled = true;
    const canvas = document.createElement("canvas");
    canvas.width = liveVideo.videoWidth;
    canvas.height = liveVideo.videoHeight;
    const context = canvas.getContext("2d");
    if (model.get("facing_mode") === "user") {
      context.translate(canvas.width, 0);
      context.scale(-1, 1);
    }
    context.drawImage(liveVideo, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      if (!blob || disposed) {
        status.textContent = "Unable to capture a photo.";
        primary.disabled = !!model.get("disabled");
        return;
      }
      revokeResultUrl();
      resultUrl = URL.createObjectURL(blob);
      photo.src = resultUrl;
      photo.hidden = false;
      liveVideo.hidden = true;
      liveBadge.hidden = true;
      placeholder.hidden = true;
      primary.hidden = true;
      retake.hidden = false;
      status.textContent = "Photo captured.";
      void saveCapture(blob, "image/jpeg", filename("jpg"), 0);
    }, "image/jpeg", 0.92);
  }

  function supportedVideoType() {
    const candidates = [
      "video/webm;codecs=vp9",
      "video/webm;codecs=vp8",
      "video/webm",
      "video/mp4"
    ];
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
    return candidates.find(type => MediaRecorder.isTypeSupported(type)) || "";
  }

  function extensionFor(mimeType) {
    return mimeType.includes("mp4") ? "mp4" : "webm";
  }

  function updateTimer() {
    const seconds = Math.floor((performance.now() - recordingStartedAt) / 1000);
    const minutesText = String(Math.floor(seconds / 60)).padStart(2, "0");
    const secondsText = String(seconds % 60).padStart(2, "0");
    timerText.textContent = `${minutesText}:${secondsText}`;
  }

  function stopRecording() {
    if (recorder && recorder.state !== "inactive") recorder.stop();
  }

  function cancelRecording() {
    if (!recorder || recorder.state === "inactive") return;
    recorder.ondataavailable = null;
    recorder.onstop = null;
    recorder.onerror = null;
    recorder.stop();
    recordedChunks = [];
    clearTimers();
    recordingBadge.hidden = true;
    primary.classList.remove("is-recording");
  }

  function startRecording() {
    if (!stream || !window.MediaRecorder) {
      status.textContent = "Video recording is not supported by this browser.";
      return;
    }
    recordedChunks = [];
    const preferredType = supportedVideoType();
    try {
      recorder = preferredType
        ? new MediaRecorder(stream, { mimeType: preferredType })
        : new MediaRecorder(stream);
    } catch (error) {
      status.textContent = "Unable to start video recording.";
      return;
    }
    recorder.ondataavailable = event => {
      if (event.data && event.data.size > 0) recordedChunks.push(event.data);
    };
    recorder.onerror = () => {
      clearTimers();
      recordingBadge.hidden = true;
      status.textContent = "Video recording failed.";
    };
    recorder.onstop = () => {
      clearTimers();
      recordingBadge.hidden = true;
      const duration = Math.max(0, (performance.now() - recordingStartedAt) / 1000);
      const mimeType = recorder.mimeType || recordedChunks[0]?.type || preferredType || "video/webm";
      const blob = new Blob(recordedChunks, { type: mimeType });
      if (!blob.size || disposed) {
        status.textContent = "No video data was recorded.";
        showLive();
        return;
      }
      revokeResultUrl();
      resultUrl = URL.createObjectURL(blob);
      recordingVideo.src = resultUrl;
      recordingVideo.hidden = false;
      liveVideo.hidden = true;
      liveBadge.hidden = true;
      placeholder.hidden = true;
      primary.hidden = true;
      retake.hidden = false;
      status.textContent = "Video recorded.";
      void saveCapture(blob, mimeType, filename(extensionFor(mimeType)), duration);
    };
    recordingStartedAt = performance.now();
    recorder.start(250);
    timerText.textContent = "00:00";
    recordingBadge.hidden = false;
    primary.textContent = "Stop recording";
    primary.classList.add("is-recording");
    status.textContent = "Recording video…";
    timerInterval = setInterval(updateTimer, 250);
    recordingTimeout = setTimeout(stopRecording, model.get("max_duration") * 1000);
  }

  function handlePrimary() {
    if (!stream) {
      void startCamera();
      return;
    }
    if (model.get("mode") === "photo") {
      capturePhoto();
    } else if (recorder && recorder.state !== "inactive") {
      primary.disabled = true;
      stopRecording();
    } else {
      startRecording();
    }
  }

  function handleRetake() {
    clearCapture();
    primary.classList.remove("is-recording");
    showLive();
    if (!stream) void startCamera();
  }

  function syncFromModel() {
    label.textContent = model.get("label") || "";
    label.hidden = !model.get("label");
    container.hidden = !!model.get("hidden");
    localRevision = Math.max(localRevision, model.get("revision") || 0);
    const unavailable = !!model.get("disabled") || starting;
    primary.disabled = unavailable || (!!stream && liveVideo.readyState < 2);
    retake.disabled = unavailable;
    if (model.get("disabled") || model.get("hidden")) {
      cancelRecording();
      stopStream();
      placeholder.hidden = false;
      placeholder.textContent = model.get("disabled") ? "Camera disabled" : "Camera hidden";
    } else if (!stream && !starting) {
      void startCamera();
    }
  }

  primary.addEventListener("click", handlePrimary);
  retake.addEventListener("click", handleRetake);
  model.on("change:label", syncFromModel);
  model.on("change:disabled", syncFromModel);
  model.on("change:hidden", syncFromModel);
  model.on("change:revision", syncFromModel);

  syncFromModel();

  return () => {
    disposed = true;
    clearTimers();
    cancelRecording();
    stopStream();
    revokeResultUrl();
    primary.removeEventListener("click", handlePrimary);
    retake.removeEventListener("click", handleRetake);
    model.off("change:label", syncFromModel);
    model.off("change:disabled", syncFromModel);
    model.off("change:hidden", syncFromModel);
    model.off("change:revision", syncFromModel);
  };
}

export default { render };
    """

    _css = f"""
    .mljar-camera {{
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow-x: hidden;
      box-sizing: border-box;
      font-family: {THEME.get('font_family')};
      color: {THEME.get('text_color')};
    }}

    .mljar-camera-label {{
      margin-bottom: 8px;
      font-size: {THEME.get('font_size')};
      font-weight: 600;
    }}

    .mljar-camera-viewport {{
      position: relative;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      aspect-ratio: 4 / 3;
      overflow: hidden;
      border: 1px solid {THEME.get('border_color')};
      border-radius: {THEME.get('border_radius_lg')} !important;
      background: #111827;
    }}

    .mljar-camera-live,
    .mljar-camera-result {{
      width: 100%;
      max-width: 100%;
      min-width: 0;
      height: 100%;
      display: block;
      object-fit: contain;
      background: #111827;
    }}

    .mljar-camera-live.is-mirrored {{
      transform: scaleX(-1);
    }}

    .mljar-camera-live[hidden],
    .mljar-camera-result[hidden] {{
      display: none;
    }}

    .mljar-camera-placeholder {{
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      color: #f8fafc;
      background: #111827;
      font-size: 0.95rem;
    }}

    .mljar-camera-placeholder[hidden] {{
      display: none;
    }}

    .mljar-camera-live-badge,
    .mljar-camera-recording-badge {{
      position: absolute;
      top: 12px;
      right: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      border-radius: {THEME.get('border_radius_sm')} !important;
      padding: 4px 8px;
      color: #ffffff;
      background: rgba(15, 23, 42, 0.72);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
    }}

    .mljar-camera-live-badge[hidden],
    .mljar-camera-recording-badge[hidden] {{
      display: none;
    }}

    .mljar-camera-recording-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: {THEME.get('danger_color')};
      animation: mljar-camera-pulse 1s ease-in-out infinite;
    }}

    .mljar-camera-status {{
      min-height: 20px;
      padding-top: 6px;
      overflow-wrap: anywhere;
      color: {THEME.get('muted_text_color')};
      font-size: 0.86rem;
    }}

    .mljar-camera-controls {{
      display: flex;
      min-width: 0;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;
      padding-top: 4px;
    }}

    .mljar-camera-button {{
      border: 1px solid {THEME.get('primary_color')};
      border-radius: {THEME.get('border_radius')} !important;
      padding: 7px 16px;
      font-family: inherit;
      font-size: {THEME.get('font_size')};
      font-weight: 600;
      cursor: pointer;
      box-shadow: {THEME.get('button_shadow')};
    }}

    .mljar-camera-button-primary {{
      color: {THEME.get('button_primary_text')};
      background: {THEME.get('primary_color')};
    }}

    .mljar-camera-button-primary.is-recording {{
      border-color: {THEME.get('danger_color')};
      background: {THEME.get('danger_color')};
    }}

    .mljar-camera-button-secondary {{
      color: {THEME.get('primary_color')};
      background: {THEME.get('widget_background_color')};
    }}

    .mljar-camera-button:hover:not(:disabled) {{
      box-shadow: {THEME.get('button_shadow_hover')};
      filter: brightness(0.98);
    }}

    .mljar-camera-button:focus-visible {{
      outline: 2px solid {THEME.get('focus_border_color')};
      outline-offset: 2px;
    }}

    .mljar-camera-button:disabled {{
      cursor: not-allowed;
      opacity: 0.55;
    }}

    @keyframes mljar-camera-pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.35; }}
    }}
    """

    mode = traitlets.Enum(["photo", "video"], default_value="photo").tag(sync=True)
    label = traitlets.Unicode("Camera").tag(sync=True)
    facing_mode = traitlets.Enum(
        ["user", "environment"], default_value="environment"
    ).tag(sync=True)
    max_duration = traitlets.Int(30, min=1, max=300).tag(sync=True)
    audio = traitlets.Bool(False).tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)
    position = traitlets.Enum(
        ["sidebar", "inline", "bottom"], default_value="inline"
    ).tag(sync=True)

    mime_type = traitlets.Unicode("").tag(sync=True)
    filename = traitlets.Unicode("").tag(sync=True)
    byte_size = traitlets.Int(0).tag(sync=True)
    duration = traitlets.Float(0).tag(sync=True)
    revision = traitlets.Int(0).tag(sync=True)

    cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._value: bytes | None = None
        self._last_revision = 0
        self.on_msg(self._handle_camera_message)

    def _handle_camera_message(self, _widget, content, buffers):
        revision = int(content.get("revision", 0) or 0)
        if revision <= self._last_revision:
            return

        event = content.get("event")
        if event == "capture":
            if len(buffers or []) != 1:
                raise ValueError("Camera: capture must contain exactly one buffer.")
            mime_type = str(content.get("mime_type", ""))
            expected_prefix = "image/" if self.mode == "photo" else "video/"
            if not mime_type.startswith(expected_prefix):
                expected_kind = "an image" if self.mode == "photo" else "a video"
                raise ValueError(
                    f"Camera: expected {expected_kind} MIME type, got {mime_type!r}."
                )
            value = bytes(buffers[0])
            declared_size = int(content.get("byte_size", len(value)))
            if declared_size != len(value):
                raise ValueError("Camera: captured buffer size does not match metadata.")

            self._value = value
            self.mime_type = mime_type
            self.filename = str(content.get("filename", ""))
            self.byte_size = len(value)
            self.duration = max(0.0, float(content.get("duration", 0) or 0))
            self._last_revision = revision
            return

        if event == "clear":
            self._value = None
            self.mime_type = ""
            self.filename = ""
            self.byte_size = 0
            self.duration = 0
            self._last_revision = revision

    @property
    def value(self) -> bytes | None:
        return self._value

    @property
    def size(self) -> int:
        return self.byte_size

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            data[0][MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
