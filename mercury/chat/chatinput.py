# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import anywidget
import traitlets
from IPython.display import display

from ..manager import WidgetsManager, MERCURY_MIMETYPE
from ..theme import THEME


def ChatInput(*args, key="", **kwargs):
    """
    Create and display a ChatInput widget.

    This function instantiates a `ChatInputWidget`, which provides a text input
    field and a send button suitable for chat-style interfaces.

    If a widget with the same configuration already exists (identified by
    a unique code UID generated from widget type, arguments, keyword arguments,
    and `key`), the existing instance is reused and displayed instead of
    creating a new one.

    Parameters
    ----------
    *args
        Positional arguments forwarded to `ChatInputWidget`.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.
        This is required when creating widgets inside loops.
    **kwargs
        Keyword arguments forwarded to `ChatInputWidget`.

    Returns
    -------
    ChatInputWidget
        The created or retrieved ChatInput widget instance.

    Examples
    --------
    Basic usage:

    >>> import mercury as mr
    >>> chat_input = mr.ChatInput()

    Access the last submitted message:

    >>> chat_input.value

    Reacting to user input:

    >>> if chat_input.submitted:
    ...     print("User said:", chat_input.submitted)
    """
    code_uid = WidgetsManager.get_code_uid(
        "ChatInput", key=key, args=args, kwargs=kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = ChatInputWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class ChatInputWidget(anywidget.AnyWidget):
    """
    Text input widget for chat-style applications.

    The `ChatInputWidget` provides:
    - a multiline text input
    - a send button
    - optional submission on Enter key

    It is typically used together with `Chat` and `Message` widgets
    to build conversational user interfaces.

    Public Traits
    -------------
    value : str
        The last submitted message.
        This value updates **only when the user submits** the input.
    placeholder : str
        Placeholder text shown in the input field.
    button_icon : str
        Text or emoji displayed on the send button.
    send_on_enter : bool
        If `True`, pressing Enter submits the message.
    position : {"sidebar", "inline", "bottom"}
        Controls where the widget is rendered in the Mercury App.
    cell_id : str or None
        Identifier of the notebook cell hosting the widget.

    Internal Trigger
    ----------------
    submitted : str
        Internal synchronized trait that is updated when the user
        submits a message. This is useful as an event-like signal.

        Although synced to Python, it is considered **non-public API**
        and may change in the future.

    Notes
    -----
    - The visible input field is cleared after submission.
    - The public `value` trait always contains the **last submitted message**.
    - Programmatically changing `value` does not trigger submission.
    """

    _esm = """
    function render({ model, el }) {
      el.style.flex = "0 0 auto";
      const container = document.createElement("div");
      container.classList.add("mljar-chatinput-container");

      const input = document.createElement("textarea");
      input.rows = 1;
      input.placeholder = model.get("placeholder") || "Type a message...";
      input.value = model.get("value") || "";
      input.classList.add("mljar-chatinput-input");

      const measureInput = document.createElement("textarea");
      measureInput.rows = 1;
      measureInput.classList.add("mljar-chatinput-input", "mljar-chatinput-measure");
      measureInput.setAttribute("aria-hidden", "true");
      measureInput.tabIndex = -1;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.classList.add("mljar-chatinput-button");
      btn.innerHTML = `<span class="mljar-chatinput-send-icon" aria-hidden="true">${model.get("button_icon") || "➤"}</span>`;
      btn.setAttribute("aria-label", "Send message");

      container.appendChild(input);
      container.appendChild(btn);
      container.appendChild(measureInput);
      el.appendChild(container);

      let lastModelValue = model.get("value") ?? "";
      let isGenerating = !!window.__mercuryExecutionRunning;
      let lastHeight = 0;
      let resizeNotifyFrame = null;
      let resizeNotifyTimeout = null;
      let resizeSeq = 0;
      const resizeSource = `chatinput-${Math.random().toString(36).slice(2)}`;
      let suppressNextValueSync = false;

      const notifyResize = () => {
        if (resizeNotifyTimeout !== null) {
          window.clearTimeout(resizeNotifyTimeout);
        }
        resizeNotifyTimeout = window.setTimeout(() => {
          resizeNotifyTimeout = null;
          if (resizeNotifyFrame !== null) return;
          const seq = ++resizeSeq;
          resizeNotifyFrame = requestAnimationFrame(() => {
            resizeNotifyFrame = null;
            const detail = {
              height: container.getBoundingClientRect().height,
              source: resizeSource,
              seq
            };
            window.dispatchEvent(new CustomEvent("mercury:bottom-resize-requested", { detail }));
          });
        }, 90);
      };

      const resizeInput = (notify = true) => {
        const styles = window.getComputedStyle(input);
        const maxHeight = Math.min(160, Math.max(80, window.innerHeight * 0.3));
        const borderY =
          parseFloat(styles.borderTopWidth || "0") +
          parseFloat(styles.borderBottomWidth || "0");
        const minHeight = parseFloat(styles.minHeight || "0") || 0;
        measureInput.style.width = `${input.getBoundingClientRect().width}px`;
        measureInput.value = input.value || input.placeholder || "";
        const nextHeight = Math.max(
          minHeight,
          Math.min(measureInput.scrollHeight + borderY, maxHeight)
        );
        input.style.height = `${nextHeight}px`;
        input.style.overflowY =
          measureInput.scrollHeight + borderY > maxHeight + 1 ? "auto" : "hidden";
        if (nextHeight !== lastHeight) {
          lastHeight = nextHeight;
          if (notify) {
            notifyResize();
          }
        }
      };

      const renderButtonState = () => {
        if (isGenerating) {
          btn.innerHTML = '<span class="mljar-chatinput-stop-icon" aria-hidden="true"></span>';
          btn.classList.remove("mljar-chatinput-button-stop");
          btn.setAttribute("aria-label", "Stop response generation");
          btn.title = "Stop response generation";
        } else {
          btn.innerHTML = `<span class="mljar-chatinput-send-icon" aria-hidden="true">${model.get("button_icon") || "➤"}</span>`;
          btn.classList.remove("mljar-chatinput-button-stop");
          btn.setAttribute("aria-label", "Send message");
          btn.title = "";
        }
      };

      const setGenerating = (next) => {
        isGenerating = !!next;
        renderButtonState();
      };

      const requestStop = () => {
        window.dispatchEvent(new CustomEvent("mercury:interrupt-requested"));
      };

      const onExecutionStarted = () => setGenerating(true);
      const onExecutionFinished = () => setGenerating(false);

      window.addEventListener("mercury:execution-started", onExecutionStarted);
      window.addEventListener("mercury:execution-finished", onExecutionFinished);
      renderButtonState();

      model.on("change:value", () => {
        const newVal = model.get("value") ?? "";

        if (suppressNextValueSync && newVal === lastModelValue) {
            suppressNextValueSync = false;
            return;
        }

        // Only update the visible input if the user hasn't typed since
        // the last time we applied a model value.
        const userHasTyped = input.value !== lastModelValue;
        if (!userHasTyped) {
            input.value = newVal;
            resizeInput();
        }

        lastModelValue = newVal;
      });

      const sendMessage = () => {
        if (isGenerating) {
          requestStop();
          return;
        }
        const msg = (input.value || "").trim();
        if (!msg) return;

        model.set("submitted", msg);
        model.set("value", msg);
        // After submission we clear the input, but the model value becomes msg.
        // Track it so subsequent model changes don't clobber a new draft.
        lastModelValue = msg;
        suppressNextValueSync = true;
        input.value = "";
        resizeInput(true);
        model.save_changes();
      };

      const insertNewlineAtCursor = () => {
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? input.value.length;
        const before = input.value.slice(0, start);
        const after = input.value.slice(end);
        input.value = `${before}\n${after}`;
        const cursor = start + 1;
        input.selectionStart = cursor;
        input.selectionEnd = cursor;
        resizeInput(false);
      };

      btn.addEventListener("click", sendMessage);

      model.on("change:button_icon", renderButtonState);

      input.addEventListener("input", () => resizeInput(false));
      input.addEventListener("blur", () => resizeInput(true));

      input.addEventListener("keydown", (ev) => {
        if (isGenerating) return;
        const sendOnEnter = !!model.get("send_on_enter");
        if (!sendOnEnter) return;
        if (ev.key === "Enter" && ev.shiftKey) {
          ev.preventDefault();
          insertNewlineAtCursor();
          return;
        }
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          sendMessage();
        }
      });

      resizeInput(true);

      return () => {
        if (resizeNotifyTimeout !== null) {
          window.clearTimeout(resizeNotifyTimeout);
        }
        if (resizeNotifyFrame !== null) {
          cancelAnimationFrame(resizeNotifyFrame);
        }
        window.removeEventListener("mercury:execution-started", onExecutionStarted);
        window.removeEventListener("mercury:execution-finished", onExecutionFinished);
      };
    }
    export default { render };
    """

    _css = f"""
    .mljar-chatinput-container {{
        position: relative;
        display: block;
        width: 100%;
        min-width: 160px;
        box-sizing: border-box;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', 'normal')};
        color: {THEME.get('text_color', '#222')};
        padding: 8px 4px;
    }}

    .mljar-chatinput-input {{
        display: block;
        width: 100%;
        resize: none;
        border: { '1px solid ' + THEME.get('border_color', '#ccc') if THEME.get('border_visible', True) else 'none'};
        border-radius: {THEME.get('border_radius', '6px')};
        min-height: calc(1.4em + 24px);
        max-height: min(160px, 30vh);
        overflow-y: hidden;
        background: {THEME.get('widget_background_color', '#fff')};
        color: {THEME.get('text_color', '#222')};
        box-sizing: border-box;
        padding: 9px 56px 9px 10px;
        font: inherit;
        line-height: 1.4;
        appearance: none !important;
        background-color: {THEME.get('widget_background_color', '#fff')} !important;
    }}

    .mljar-chatinput-input::placeholder {{
        color: {THEME.get('muted_text_color', '#777')};
        opacity: 1;
    }}

    .mljar-chatinput-input:focus {{
        outline: none;
        border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
        border-width: 2px;
        box-shadow: none;
    }}

    .mljar-chatinput-measure {{
        position: absolute;
        left: -9999px;
        top: 0;
        visibility: hidden;
        pointer-events: none;
        height: auto;
        min-height: 0;
        max-height: none;
        overflow-y: hidden;
        z-index: -1;
    }}

    .mljar-chatinput-button {{
        position: absolute;
        right: 0;
        top: 8px;
        bottom: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid {THEME.get('primary_color', '#007bff')};
        border-radius: 0 {THEME.get('border_radius', '6px')} {THEME.get('border_radius', '6px')} 0 !important;
        width: 60px;
        cursor: pointer;
        background: {THEME.get('primary_color', '#007bff')};
        color: {THEME.get('button_text_color', THEME.get('widget_background_color', '#fff'))};
        font: inherit;
        font-weight: 600;
        padding: 0;
        line-height: 1;
        transition: background 0.2s, color 0.2s, border-color 0.2s, transform 120ms ease;
    }}

    .mljar-chatinput-button:hover:not(:disabled) {{
        background: {THEME.get('hover_background_color', '#f8fafc')};
        color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-chatinput-button:active:not(:disabled) {{
        background: {THEME.get('selected_background_color', '#eef3ff')};
        color: {THEME.get('accent_color', THEME.get('primary_color', '#007bff'))};
        transform: translateY(1px);
    }}

    .mljar-chatinput-button:focus-visible {{
        outline: none;
        border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
    }}

    .mljar-chatinput-send-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transform: translateX(1px);
        font-size: 16px;
        line-height: 1;
    }}

    .mljar-chatinput-stop-icon {{
        display: inline-block;
        width: 10px;
        height: 10px;
        background: currentColor;
        border-radius: 2px;
    }}
    """

    # Public traits
    value = traitlets.Unicode("").tag(sync=True)
    placeholder = traitlets.Unicode("Type a message...").tag(sync=True)
    button_icon = traitlets.Unicode("➤").tag(sync=True)
    send_on_enter = traitlets.Bool(True).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="bottom",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    # Internal-ish trigger
    submitted = traitlets.Unicode("").tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
