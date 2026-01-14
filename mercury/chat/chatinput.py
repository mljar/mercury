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
    - a single-line text input
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

      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = model.get("placeholder") || "Type a message...";
      input.value = model.get("value") || "";
      input.classList.add("mljar-chatinput-input");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.classList.add("mljar-chatinput-button");
      btn.textContent = model.get("button_icon") || " ➤ ";
      btn.setAttribute("aria-label", "Send message");

      container.appendChild(input);
      container.appendChild(btn);
      el.appendChild(container);

      let lastModelValue = model.get("value") ?? "";

      model.on("change:value", () => {
        const newVal = model.get("value") ?? "";

        // Only update the visible input if the user hasn't typed since
        // the last time we applied a model value.
        const userHasTyped = input.value !== lastModelValue;
        if (!userHasTyped) {
            input.value = newVal;
        }

        lastModelValue = newVal;
      });
      
      const sendMessage = () => {
        const msg = (input.value || "").trim();
        if (!msg) return;

        model.set("submitted", msg);
        model.set("value", msg);
        // After submission we clear the input, but the model value becomes msg.
        // Track it so subsequent model changes don't clobber a new draft.
        lastModelValue = msg;
        input.value = "";
        model.save_changes();
      };

      btn.addEventListener("click", sendMessage);

      input.addEventListener("keydown", (ev) => {
        const sendOnEnter = !!model.get("send_on_enter");
        if (!sendOnEnter) return;
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          sendMessage();
        }
      });
    }
    export default { render };
    """

    _css = f"""
    .mljar-chatinput-container {{
        display: flex;
        flex-direction: row;
        align-items: center;
        width: 100%;
        min-width: 160px;
        box-sizing: border-box;
        gap: 8px;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        color: {THEME.get('text_color', '#222')};
        padding-top: 8px;
        padding-bottom: 8px;
    }}

    .mljar-chatinput-input {{
        flex: 1 1 auto;
        width: 100%;
        border: { '1px solid ' + THEME.get('border_color', '#ccc') if THEME.get('border_visible', True) else 'none'};
        border-radius: {THEME.get('border_radius', '6px')};
        padding: 6px 10px;
        min-height: 1.6em;
        background: {THEME.get('widget_background_color', '#fff')};
        color: {THEME.get('text_color', '#222')};
        box-sizing: border-box;
        padding: 10px;
        font-size: 0.9rem;
    }}

    .mljar-chatinput-input:focus {{
        outline: none;
        border-color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-chatinput-button {{
        flex: 0 0 auto;
        border: none;
        border-radius: {THEME.get('border_radius', '6px')} !important;
        min-height: 1.6em;
        cursor: pointer;
        background: {THEME.get('primary_color', '#007bff')};
        color: {THEME.get('button_text_color', '#fff')};
        font-weight: bold;
        padding: 11px;
        padding-left: 18px;
        padding-right: 18px;
    }}

    .mljar-chatinput-button:hover {{
        filter: brightness(0.95);
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
