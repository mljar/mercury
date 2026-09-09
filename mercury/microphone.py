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

Position = Literal["sidebar", "inline", "bottom"]


def Microphone(
    label: str = "Record audio",
    max_duration: int = 60,
    position: Position = "inline",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """Create and display a browser audio recorder.

    Microphone access begins only after the user selects Start recording. A completed
    recording is sent to Python as bytes and causes cells below this widget to execute
    once.

    Parameters
    ----------
    label : str, optional
        Text displayed above the recorder. Default is ``"Record audio"``.
    max_duration : int, optional
        Maximum recording duration in seconds, from 1 to 300. Default is ``60``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    disabled : bool, optional
        Disable microphone access and controls. Default is ``False``.
    hidden : bool, optional
        Hide the widget and stop its media stream. Default is ``False``.
    key : str, optional
        Stable identifier used to reuse the recorder across cell executions.

    Returns
    -------
    MicrophoneWidget
        The displayed widget. ``value`` contains recorded bytes or ``None``.
    """
    if not isinstance(label, str):
        raise TypeError("Microphone: `label` must be a string.")
    if isinstance(max_duration, bool) or not isinstance(max_duration, int):
        raise TypeError("Microphone: `max_duration` must be an integer.")
    if not 1 <= max_duration <= 300:
        raise ValueError(
            "Microphone: `max_duration` must be between 1 and 300 seconds."
        )
    if not isinstance(disabled, bool):
        raise TypeError("Microphone: `disabled` must be a boolean.")
    if not isinstance(hidden, bool):
        raise TypeError("Microphone: `hidden` must be a boolean.")

    kwargs = {
        "label": label,
        "max_duration": max_duration,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }
    code_uid = WidgetsManager.get_code_uid(
        "Microphone", key=key, args=[], kwargs=kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = MicrophoneWidget(**with_widget_render_metadata(kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class MicrophoneWidget(anywidget.AnyWidget):
    _esm = r"""
function render({ model, el }) {
  el.innerHTML = "";

  const container = document.createElement("div");
  container.className = "mljar-microphone";

  const label = document.createElement("div");
  label.className = "mljar-microphone-label";

  const panel = document.createElement("div");
  panel.className = "mljar-microphone-panel";

  const stateRow = document.createElement("div");
  stateRow.className = "mljar-microphone-state";

  const recordingDot = document.createElement("span");
  recordingDot.className = "mljar-microphone-dot";
  recordingDot.hidden = true;

  const stateText = document.createElement("span");
  stateText.textContent = "Ready to record";

  const timer = document.createElement("span");
  timer.className = "mljar-microphone-timer";
  timer.textContent = "00:00 / 01:00";
  timer.hidden = true;

  stateRow.append(recordingDot, stateText, timer);

  const player = document.createElement("audio");
  player.className = "mljar-microphone-player";
  player.controls = true;
  player.preload = "metadata";
  player.hidden = true;

  const status = document.createElement("div");
  status.className = "mljar-microphone-status";
  status.setAttribute("role", "status");

  const controls = document.createElement("div");
  controls.className = "mljar-microphone-controls";

  const primary = document.createElement("button");
  primary.type = "button";
  primary.className = "mljar-microphone-button mljar-microphone-button-primary";
  primary.textContent = "Start recording";

  const again = document.createElement("button");
  again.type = "button";
  again.className = "mljar-microphone-button mljar-microphone-button-secondary";
  again.textContent = "Record again";
  again.hidden = true;

  controls.append(primary, again);
  panel.append(stateRow, player, status, controls);
  container.append(label, panel);
  el.appendChild(container);

  let stream = null;
  let recorder = null;
  let chunks = [];
  let startedAt = 0;
  let stopTimeout = null;
  let timerInterval = null;
  let resultUrl = null;
  let disposed = false;
  let starting = false;
  let localRevision = model.get("revision") || 0;

  function formatTime(seconds) {
    const whole = Math.max(0, Math.floor(seconds));
    const minutesText = String(Math.floor(whole / 60)).padStart(2, "0");
    const secondsText = String(whole % 60).padStart(2, "0");
    return `${minutesText}:${secondsText}`;
  }

  function clearTimers() {
    if (stopTimeout !== null) clearTimeout(stopTimeout);
    if (timerInterval !== null) clearInterval(timerInterval);
    stopTimeout = null;
    timerInterval = null;
  }

  function stopStream() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
  }

  function revokeResultUrl() {
    if (resultUrl) URL.revokeObjectURL(resultUrl);
    resultUrl = null;
    player.removeAttribute("src");
    player.load();
  }

  function nextRevision() {
    localRevision = Math.max(localRevision, model.get("revision") || 0) + 1;
    return localRevision;
  }

  function extensionFor(mimeType) {
    if (mimeType.includes("mp4")) return "mp4";
    if (mimeType.includes("ogg")) return "ogg";
    return "webm";
  }

  function filename(extension) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `microphone-${stamp}.${extension}`;
  }

  function supportedAudioType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/ogg;codecs=opus",
      "audio/mp4",
      "audio/webm"
    ];
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
    return candidates.find(type => MediaRecorder.isTypeSupported(type)) || "";
  }

  function updateTimer() {
    const elapsed = (performance.now() - startedAt) / 1000;
    timer.textContent = `${formatTime(elapsed)} / ${formatTime(model.get("max_duration"))}`;
  }

  function showReady() {
    recordingDot.hidden = true;
    timer.hidden = true;
    player.hidden = true;
    stateText.textContent = "Ready to record";
    primary.textContent = "Start recording";
    primary.classList.remove("is-recording");
    primary.hidden = false;
    primary.disabled = !!model.get("disabled");
    again.hidden = true;
    status.textContent = "Microphone access starts only when you select Start recording.";
  }

  function showError(error) {
    clearTimers();
    stopStream();
    recordingDot.hidden = true;
    timer.hidden = true;
    stateText.textContent = "Microphone unavailable";
    primary.textContent = "Try again";
    primary.classList.remove("is-recording");
    primary.hidden = false;
    primary.disabled = !!model.get("disabled");
    if (!window.isSecureContext) {
      status.textContent = "Microphone access requires HTTPS or localhost.";
    } else if (error && error.name === "NotAllowedError") {
      status.textContent = "Microphone permission was denied. Allow access in your browser and try again.";
    } else if (error && error.name === "NotFoundError") {
      status.textContent = "No microphone was found on this device.";
    } else if (error && error.name === "NotReadableError") {
      status.textContent = "The microphone is already in use or unavailable.";
    } else if (!window.MediaRecorder) {
      status.textContent = "Audio recording is not supported by this browser.";
    } else {
      status.textContent = "Unable to start audio recording.";
    }
  }

  function saveRecording(blob, mimeType, recordedFilename, duration) {
    again.disabled = true;
    return blob.arrayBuffer().then(buffer => {
      if (disposed) return;
      const revision = nextRevision();
      model.send({
        event: "recording",
        mime_type: mimeType,
        filename: recordedFilename,
        byte_size: blob.size,
        duration,
        revision
      }, {}, [buffer]);
      model.set("mime_type", mimeType);
      model.set("filename", recordedFilename);
      model.set("byte_size", blob.size);
      model.set("duration", duration);
      model.set("revision", revision);
      model.save_changes();
    }).catch(() => {
      if (!disposed) status.textContent = "Unable to transfer the recording to Python.";
    }).finally(() => {
      if (!disposed) again.disabled = !!model.get("disabled");
    });
  }

  function clearRecording() {
    const revision = nextRevision();
    model.send({ event: "clear", revision });
    model.set("mime_type", "");
    model.set("filename", "");
    model.set("byte_size", 0);
    model.set("duration", 0);
    model.set("revision", revision);
    model.save_changes();
  }

  function finishRecording() {
    clearTimers();
    recordingDot.hidden = true;
    timer.hidden = true;
    primary.classList.remove("is-recording");
    const duration = Math.max(0, (performance.now() - startedAt) / 1000);
    const preferredType = supportedAudioType();
    const mimeType = recorder?.mimeType || chunks[0]?.type || preferredType || "audio/webm";
    const blob = new Blob(chunks, { type: mimeType });
    stopStream();
    if (!blob.size || disposed) {
      if (!disposed) {
        status.textContent = "No audio data was recorded.";
        showReady();
      }
      return;
    }
    revokeResultUrl();
    resultUrl = URL.createObjectURL(blob);
    player.src = resultUrl;
    player.hidden = false;
    stateText.textContent = "Recording complete";
    primary.hidden = true;
    again.hidden = false;
    status.textContent = `${formatTime(duration)} recorded.`;
    void saveRecording(
      blob,
      mimeType,
      filename(extensionFor(mimeType)),
      duration
    );
  }

  function cancelRecording() {
    if (recorder && recorder.state !== "inactive") {
      recorder.ondataavailable = null;
      recorder.onstop = null;
      recorder.onerror = null;
      recorder.stop();
    }
    recorder = null;
    chunks = [];
    clearTimers();
    recordingDot.hidden = true;
    timer.hidden = true;
    primary.classList.remove("is-recording");
    stopStream();
  }

  function stopRecording() {
    if (!recorder || recorder.state === "inactive") return;
    primary.disabled = true;
    stateText.textContent = "Finishing recording…";
    recorder.stop();
  }

  async function startRecording() {
    if (disposed || starting || model.get("disabled") || model.get("hidden")) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      showError(new Error("Audio recording is unavailable"));
      return;
    }
    starting = true;
    primary.disabled = true;
    stateText.textContent = "Waiting for permission…";
    status.textContent = "Your browser may ask to use the microphone.";
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (disposed || model.get("disabled") || model.get("hidden")) {
        stopStream();
        return;
      }
      const preferredType = supportedAudioType();
      recorder = preferredType
        ? new MediaRecorder(stream, { mimeType: preferredType })
        : new MediaRecorder(stream);
      chunks = [];
      recorder.ondataavailable = event => {
        if (event.data && event.data.size > 0) chunks.push(event.data);
      };
      recorder.onerror = event => {
        recorder.ondataavailable = null;
        recorder.onstop = null;
        chunks = [];
        showError(event.error || new Error("Recording failed"));
      };
      recorder.onstop = finishRecording;
      stream.getAudioTracks().forEach(track => {
        track.addEventListener("ended", () => {
          if (!disposed && recorder && recorder.state !== "inactive") stopRecording();
        }, { once: true });
      });
      startedAt = performance.now();
      recorder.start(250);
      recordingDot.hidden = false;
      timer.hidden = false;
      timer.textContent = `00:00 / ${formatTime(model.get("max_duration"))}`;
      stateText.textContent = "Recording";
      primary.textContent = "Stop recording";
      primary.classList.add("is-recording");
      primary.disabled = false;
      status.textContent = "Recording audio…";
      timerInterval = setInterval(updateTimer, 250);
      stopTimeout = setTimeout(stopRecording, model.get("max_duration") * 1000);
    } catch (error) {
      if (!disposed) showError(error);
    } finally {
      starting = false;
    }
  }

  function handlePrimary() {
    if (recorder && recorder.state !== "inactive") {
      stopRecording();
    } else {
      void startRecording();
    }
  }

  function handleAgain() {
    clearRecording();
    revokeResultUrl();
    showReady();
  }

  function syncFromModel() {
    label.textContent = model.get("label") || "";
    label.hidden = !model.get("label");
    container.hidden = !!model.get("hidden");
    localRevision = Math.max(localRevision, model.get("revision") || 0);
    const unavailable = !!model.get("disabled") || starting;
    primary.disabled = unavailable;
    again.disabled = unavailable;
    if (model.get("disabled") || model.get("hidden")) {
      cancelRecording();
      stateText.textContent = model.get("disabled") ? "Microphone disabled" : "Microphone hidden";
      status.textContent = "";
    } else if (!recorder && !resultUrl && !starting) {
      showReady();
    }
  }

  primary.addEventListener("click", handlePrimary);
  again.addEventListener("click", handleAgain);
  model.on("change:label", syncFromModel);
  model.on("change:disabled", syncFromModel);
  model.on("change:hidden", syncFromModel);
  model.on("change:revision", syncFromModel);

  syncFromModel();

  return () => {
    disposed = true;
    cancelRecording();
    revokeResultUrl();
    primary.removeEventListener("click", handlePrimary);
    again.removeEventListener("click", handleAgain);
    model.off("change:label", syncFromModel);
    model.off("change:disabled", syncFromModel);
    model.off("change:hidden", syncFromModel);
    model.off("change:revision", syncFromModel);
  };
}

export default { render };
    """

    _css = f"""
    .mljar-microphone {{
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow-x: hidden;
      box-sizing: border-box;
      font-family: {THEME.get('font_family')};
      color: {THEME.get('text_color')};
    }}

    .mljar-microphone-label {{
      margin-bottom: 8px;
      font-size: {THEME.get('font_size')};
      font-weight: 600;
    }}

    .mljar-microphone-panel {{
      min-width: 0;
      padding: 14px;
      border: 1px solid {THEME.get('border_color')};
      border-radius: {THEME.get('border_radius_lg')} !important;
      background: {THEME.get('widget_background_color')};
      box-sizing: border-box;
    }}

    .mljar-microphone-state {{
      display: flex;
      min-width: 0;
      align-items: center;
      gap: 8px;
      color: {THEME.get('text_color')};
      font-size: 0.95rem;
      font-weight: 600;
    }}

    .mljar-microphone-dot {{
      width: 9px;
      height: 9px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: {THEME.get('danger_color')};
      animation: mljar-microphone-pulse 1s ease-in-out infinite;
    }}

    .mljar-microphone-dot[hidden] {{
      display: none;
    }}

    .mljar-microphone-timer {{
      margin-left: auto;
      color: {THEME.get('muted_text_color')};
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}

    .mljar-microphone-timer[hidden] {{
      display: none;
    }}

    .mljar-microphone-player {{
      display: block;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      margin-top: 12px;
    }}

    .mljar-microphone-player[hidden] {{
      display: none;
    }}

    .mljar-microphone-status {{
      min-height: 20px;
      padding-top: 7px;
      overflow-wrap: anywhere;
      color: {THEME.get('muted_text_color')};
      font-size: 0.86rem;
    }}

    .mljar-microphone-controls {{
      display: flex;
      min-width: 0;
      flex-wrap: wrap;
      gap: 8px;
      padding-top: 4px;
    }}

    .mljar-microphone-button {{
      border: 1px solid {THEME.get('primary_color')};
      border-radius: {THEME.get('border_radius')} !important;
      padding: 7px 16px;
      font-family: inherit;
      font-size: {THEME.get('font_size')};
      font-weight: 600;
      cursor: pointer;
      box-shadow: {THEME.get('button_shadow')};
    }}

    .mljar-microphone-button-primary {{
      color: {THEME.get('button_primary_text')};
      background: {THEME.get('primary_color')};
    }}

    .mljar-microphone-button-primary.is-recording {{
      border-color: {THEME.get('danger_color')};
      background: {THEME.get('danger_color')};
    }}

    .mljar-microphone-button-secondary {{
      color: {THEME.get('primary_color')};
      background: {THEME.get('widget_background_color')};
    }}

    .mljar-microphone-button:hover:not(:disabled) {{
      box-shadow: {THEME.get('button_shadow_hover')};
      filter: brightness(0.98);
    }}

    .mljar-microphone-button:focus-visible {{
      outline: 2px solid {THEME.get('focus_border_color')};
      outline-offset: 2px;
    }}

    .mljar-microphone-button:disabled {{
      cursor: not-allowed;
      opacity: 0.55;
    }}

    @keyframes mljar-microphone-pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.35; }}
    }}
    """

    label = traitlets.Unicode("Record audio").tag(sync=True)
    max_duration = traitlets.Int(60, min=1, max=300).tag(sync=True)
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
        self.on_msg(self._handle_microphone_message)

    def _handle_microphone_message(self, _widget, content, buffers):
        revision = int(content.get("revision", 0) or 0)
        if revision <= self._last_revision:
            return

        event = content.get("event")
        if event == "recording":
            if len(buffers or []) != 1:
                raise ValueError(
                    "Microphone: recording must contain exactly one buffer."
                )
            mime_type = str(content.get("mime_type", ""))
            if not mime_type.startswith("audio/"):
                raise ValueError(
                    f"Microphone: expected an audio MIME type, got {mime_type!r}."
                )
            value = bytes(buffers[0])
            declared_size = int(content.get("byte_size", len(value)))
            if declared_size != len(value):
                raise ValueError(
                    "Microphone: recorded buffer size does not match metadata."
                )

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
