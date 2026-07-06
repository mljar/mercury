# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import ipywidgets as widgets
from IPython.display import display, clear_output
from threading import Timer

import anywidget
import traitlets

from .message import Message, MSG_CSS_CLASS
from ..theme import THEME


class ScrollHelper(anywidget.AnyWidget):
    """
    Tiny anywidget that runs front-end JS to scroll to the last chat message.

    It looks for elements with the message CSS class (MSG_CSS_CLASS) and tries
    to scroll the preferred scroll container so the last one is visible.
    """

    _esm = """
function render({ model, el }) {
  const LOG_PREFIX = "[ScrollHelper]";
  const MSG_CLASS = model.get("msg_css_class") || "mljar-chat-msg";

  // Just in case, hide the helper element itself
  el.classList.add("mljar-chat-scroll-helper");

  function isScrollable(elem) {
    if (!elem) return false;
    const cs = getComputedStyle(elem);
    const oy = cs.overflowY;
    const o = cs.overflow;
    const canScroll = elem.scrollHeight > (elem.clientHeight + 2);
    return (
      canScroll &&
      (oy === "auto" || oy === "scroll" || o === "auto" || o === "scroll")
    );
  }

  function findScrollableWithin(rootEl) {
    if (!rootEl) return null;
    if (isScrollable(rootEl)) return rootEl;

    const walker = document.createTreeWalker(
      rootEl,
      NodeFilter.SHOW_ELEMENT,
      null
    );
    let n = walker.currentNode;
    while ((n = walker.nextNode())) {
      if (isScrollable(n)) return n;
    }
    return null;
  }

  function getScrollableAncestor(node) {
    let cur = node && node.parentElement;
    while (cur) {
      if (isScrollable(cur)) return cur;
      cur = cur.parentElement;
    }
    return null;
  }

  function scrollIntoContainer(elem, container) {
    if (!elem || !container) return;
    let y = 0;
    let n = elem;
    while (n && n !== container) {
      y += n.offsetTop || 0;
      n = n.offsetParent;
    }
    const target = Math.max(
      0,
      y - (container.clientHeight - elem.clientHeight) + 16
    );
    container.scrollTop = target;
  }

  function scrollPageFallback(elem) {
    try {
      elem.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch (e) {
      // ignore
    }
  }

  function autoScroll() {
    const msgs = document.getElementsByClassName(MSG_CLASS);
    if (!msgs || !msgs.length) return;
    const last = msgs[msgs.length - 1];

    const selector =
      model.get("scroll_container_selector") ||
      "#mercury-main-panel, .mercury-main-panel";

    let pref = null;
    try {
      pref = document.querySelector(selector);
    } catch (e) {
      console.warn(LOG_PREFIX, "bad selector", selector, e);
    }

    const scroller =
      findScrollableWithin(pref) ||
      getScrollableAncestor(last) ||
      document.scrollingElement ||
      document.documentElement;

    if (scroller) {
      scrollIntoContainer(last, scroller);
    } else {
      scrollPageFallback(last);
    }
  }

  function scheduleScroll() {
    // Give big outputs (plots, images) a moment to layout
    requestAnimationFrame(() => {
      setTimeout(autoScroll, 100);
    });
  }

  // initial scroll attempt (in case messages already present)
  scheduleScroll();

  // each time Python bumps `tick`, schedule scroll
  model.on("change:tick", scheduleScroll);
}
export default { render };
    """

    _css = f"""
    .mljar-chat-scroll-helper {{
        display: none;
    }}

    .mljar-chat-container {{
        background: transparent;
        box-sizing: border-box;
    }}

    .mljar-chat-container > .widget-box,
    .mljar-chat-container > .jupyter-widgets,
    .mljar-chat-container .widget-box,
    .mljar-chat-container .jupyter-widgets {{
        box-sizing: border-box;
    }}

    .mljar-chat-placeholder {{
        color: {THEME.get('muted_text_color', '#777')};
        text-align: center;
        padding: 32px 0;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', 'normal')};
        line-height: 1.6;
        background: transparent;
        border: {('1px dashed ' + THEME.get('border_color', '#ccc')) if THEME.get('border_visible', True) else 'none'};
        border-radius: {THEME.get('border_radius', '6px')};
    }}
    """

    tick = traitlets.Int(0).tag(sync=True)
    scroll_container_selector = traitlets.Unicode(
        "#mercury-main-panel, .mercury-main-panel"
    ).tag(sync=True)
    msg_css_class = traitlets.Unicode("mljar-chat-msg").tag(sync=True)


class Chat:
    """
    Chat container that displays Message widgets and auto-scrolls
    to the most recent message.

    The Chat widget manages a vertical list of Message instances and ensures
    that newly added messages are brought into view automatically.

    Scrolling behavior is implemented via an internal `ScrollHelper`
    anywidget that runs frontend JavaScript. The Chat itself does not
    create its own scrollbar — scrolling happens in the surrounding
    application or page container.

    Usage
    -----
    >>> chat = mr.Chat()
    >>> chat.add(mr.Message("Hello"))
    >>> chat.add(mr.Message("How can I help you?"))

    API
    ---
    - add(message): append a Message and scroll to it
    - clear(): remove all messages and show the placeholder

    Parameters
    ----------
    placeholder : str, optional
        Text displayed when the chat contains no messages.
    scroll_container_selector : str, optional
        CSS selector used to locate the preferred scrollable container
        (defaults to the Mercury main panel).
    height : str, optional
        CSS height for the chat message container. If empty, Chat keeps its
        natural height and the surrounding app/page container scrolls.
    scroll_debounce : float, optional
        Debounce delay in seconds for scrolling after message content updates.

    Notes
    -----
    - The Chat widget does not manage message layout details;
      each message is responsible for its own rendering.
    - Auto-scrolling is resilient to large outputs (plots, images)
      and waits briefly for layout stabilization before scrolling.
    """
    def __init__(
        self,
        placeholder: str = "💬 No messages yet. Start the conversation!",
        scroll_container_selector: str = "#mercury-main-panel, .mercury-main-panel",
        height: str = "",
        scroll_debounce: float = 0.1,
    ):
        """
        Chat widget that holds Message widgets and auto-scrolls using anywidget.

        API is intentionally kept the same as your original Chat:

            chat = Chat()
            chat.add(Message(...))
            chat.clear()

        Only the scrolling implementation changed (via ScrollHelper).
        """
        self.messages = []
        self.scroll_container_selector = scroll_container_selector
        self.height = str(height or "").strip()
        self.scroll_debounce = max(float(scroll_debounce), 0.0)
        self._scroll_timer = None

        # Placeholder label (same as before)
        self.placeholder_label = widgets.HTML(
            f"""
            <div class="mljar-chat-placeholder">{placeholder}</div>
            """
        )

        # Container for all messages
        self.vbox = widgets.VBox(
            [self.placeholder_label],
            layout=widgets.Layout(
                width="100%",
                height=self.height or None,
                padding="4px 4px 0 4px",
                overflow="auto" if self.height else "visible",
            ),
        )
        self.vbox.add_class("mljar-chat-container")

        # Hidden helper widget that runs JS (via anywidget) for scrolling
        self._scroller = ScrollHelper(
            scroll_container_selector=self.scroll_container_selector,
            msg_css_class=MSG_CSS_CLASS,
        )

        clear_output(wait=True)
        # Display both the visible chat and the hidden scroller
        display(self.vbox, self._scroller)

    # ---- internal render ----

    def _render(self):
        # Update visible children
        self.vbox.children = self.messages or [self.placeholder_label]

        self._scroll_now()

    def _scroll_now(self):
        if self._scroll_timer is not None:
            self._scroll_timer.cancel()
            self._scroll_timer = None
        self._scroller.tick += 1

    def _schedule_scroll(self):
        if self.scroll_debounce == 0:
            self._scroll_now()
            return
        if self._scroll_timer is not None:
            self._scroll_timer.cancel()
        self._scroll_timer = Timer(self.scroll_debounce, self._scroll_now)
        self._scroll_timer.daemon = True
        self._scroll_timer.start()

    def _attach_message(self, message: Message):
        message._on_update = self._schedule_scroll

    def _detach_message(self, message: Message):
        if getattr(message, "_on_update", None) == self._schedule_scroll:
            message._on_update = None

    # ---- public API (unchanged) ----

    def add(self, message: Message):
        """
        Add a Message widget to the chat and scroll to it.
        """
        self._attach_message(message)
        self.messages.append(message)
        self._render()

    def clear(self):
        """
        Clear all messages from the chat.
        """
        for message in self.messages:
            self._detach_message(message)
        self.messages.clear()
        self._render()

    def remove_last(self):
        """
        Remove the last Message widget from the chat.
        """
        if not self.messages:
            return

        message = self.messages.pop()
        self._detach_message(message)
        self._render()
