# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

"""
Message widget for chat-style interfaces built with ipywidgets.

This module defines the `Message` class, a lightweight UI component
representing a single chat message with an avatar and rich content
rendering support (Markdown, HTML, or plain text).

The widget is designed to work inside higher-level containers such as
`Chat`, where messages are stacked vertically and automatically scrolled
into view.
"""

import ipywidgets as widgets
from IPython.display import display, HTML as DHTML, Javascript, Markdown

MSG_CSS_CLASS = "mljar-chat-msg"


class Message(widgets.HBox):
    """
    A single chat message widget with avatar and rich content rendering.

    The `Message` widget renders:
    - an avatar (emoji inside a styled container)
    - message content rendered as Markdown, raw HTML, or plain text

    Only **one rendering mode** is active at a time. Switching modes
    resets the previous buffer to avoid mixing formats.

    Messages are typically managed by a parent `Chat` container, but
    can also be displayed standalone.

    Parameters
    ----------
    markdown : str, optional
        Initial message content rendered as Markdown.
    role : {"user", "assistant"}, optional
        Role used to determine avatar styling (background color).
    emoji : str, optional
        Emoji displayed inside the avatar.

    Examples
    --------
    Basic usage:

    >>> msg = Message(markdown="**Hello world!**", role="user")
    >>> display(msg)

    Streaming-style updates:

    >>> msg = Message()
    >>> chat.add(msg)
    >>> msg.append_markdown("Hello ")
    >>> msg.append_markdown("world!")
    """

    def __init__(self, markdown="", role="user", emoji="👤"):
        """
        Initialize a Message widget.

        Parameters
        ----------
        markdown : str, optional
            Initial Markdown content.
        role : str, optional
            Message role used for avatar styling.
        emoji : str, optional
            Emoji shown in the avatar.
        """
        super().__init__()

        avatar_bg = "#84c4ff" if role == "user" else "#eeeeee"
        avatar_html = (
            f'<div style="width:36px;height:36px;background:{avatar_bg};'
            f'border-radius:12px;display:flex;align-items:center;justify-content:center;'
            f'box-shadow:0 1px 4px rgba(60,60,60,0.10);">'
            f'<span style="font-size:18px;line-height:1;">{emoji}</span>'
            f'</div>'
        )

        avatar = widgets.HTML(
            value=avatar_html,
            layout=widgets.Layout(margin="0 8px 8px 0", align_self="flex-start"),
        )

        self.output = widgets.Output(
            layout=widgets.Layout(
                align_self="flex-start",
                margin="8px 0 0 0",
                overflow_y="visible",
                overflow_x="visible",
            )
        )
        self.output.add_class(MSG_CSS_CLASS)

        self.children = [avatar, self.output]
        self.layout.align_items = "flex-start"

        # Buffers and rendering mode
        self._mode = None  # one of {"markdown", "html", "text", None}
        self._md_buffer = ""
        self._html_buffer = ""
        self._text_buffer = ""

        if markdown != "":
            self.set_content(markdown=markdown)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render(self):
        """
        Re-render the message content based on the active mode.

        Clears the output widget and displays the current buffer using
        the appropriate renderer.
        """
        self.output.clear_output(wait=True)
        with self.output:
            if self._mode == "markdown":
                display(Markdown(self._md_buffer))
            elif self._mode == "html":
                display(DHTML(self._html_buffer))
            elif self._mode == "text":
                print(self._text_buffer)

    def _set_mode(self, mode):
        """
        Switch rendering mode and reset unrelated buffers.

        Parameters
        ----------
        mode : {"markdown", "html", "text"}
            Rendering mode to activate.

        Raises
        ------
        ValueError
            If an unsupported mode is provided.
        """
        if mode not in {"markdown", "html", "text"}:
            raise ValueError("mode must be 'markdown', 'html', or 'text'")

        if self._mode != mode:
            if mode == "markdown":
                self._md_buffer = ""
            elif mode == "html":
                self._html_buffer = ""
            elif mode == "text":
                self._text_buffer = ""
            self._mode = mode

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_content(self, markdown=None, text=None, html=None):
        """
        Replace message content entirely.

        Exactly one content type must be provided.

        Parameters
        ----------
        markdown : str, optional
            Markdown content.
        text : str, optional
            Plain text content (no formatting).
        html : str, optional
            Raw HTML content.

        Raises
        ------
        ValueError
            If zero or more than one content type is provided.
        """
        if sum(v is not None for v in (text, html, markdown)) != 1:
            raise ValueError("Provide exactly one of text=, html=, markdown=")

        if markdown is not None:
            self._set_mode("markdown")
            self._md_buffer = markdown
        elif text is not None:
            self._set_mode("text")
            self._text_buffer = text
        elif html is not None:
            self._set_mode("html")
            self._html_buffer = html

        self._render()

    def append_markdown(self, chunk: str):
        """
        Append Markdown content and re-render.

        Useful for streaming or incremental message updates.
        """
        self._set_mode("markdown")
        self._md_buffer += chunk
        self._render()

    def append_text(self, chunk: str):
        """
        Append plain text and re-render.
        """
        self._set_mode("text")
        self._text_buffer += chunk
        self._render()

    def append_html(self, chunk: str):
        """
        Append raw HTML and re-render.
        """
        self._set_mode("html")
        self._html_buffer += chunk
        self._render()

    def set_bouncing_text(self, text: str, color="#444"):
        """
        Render animated bouncing text.

        Each character is wrapped in a span with a staggered
        bounce animation.

        Parameters
        ----------
        text : str
            Text to render.
        color : str, optional
            CSS color used for the text.
        """
        spans = []
        for i, ch in enumerate(text):
            safe_ch = ch if ch != " " else "&nbsp;"
            spans.append(
                f'<span style="animation-delay:{i*0.1:.1f}s">{safe_ch}</span>'
            )

        html = f"""
        <style>
        .bounce-text span {{
            display: inline-block;
            animation: bounce 1.4s infinite;
            font-weight: bold;
            font-size: 1em;
            color: {color};
        }}
        @keyframes bounce {{
            0%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-6px); }}
        }}
        </style>
        <div class="bounce-text">{''.join(spans)}</div>
        """
        self.set_content(html=html)

    def set_gradient_text(self, text: str, colors=None, speed=0.85):
        """
        Render animated gradient text.

        Characters cycle through provided colors with a staggered delay.

        Parameters
        ----------
        text : str
            Text to render.
        colors : list[str], optional
            List of CSS colors used for animation.
        speed : float, optional
            Duration of one full color cycle in seconds.
        """
        if colors is None:
            colors = ["#666", "#999", "#bbb", "#999"]

        stops = " ".join(
            f"{i*100//(len(colors)-1)}% {{ color: {c}; }}"
            for i, c in enumerate(colors)
        )

        style = f"""
        <style>
        @keyframes colorwave {{
          {stops}
        }}
        .gradient-text span {{
          display:inline-block;
          animation: colorwave {speed}s infinite;
        }}
        </style>
        """

        spans = []
        for i, ch in enumerate(text):
            safe_ch = ch if ch != " " else "&nbsp;"
            spans.append(
                f'<span style="animation-delay:{i*0.1:.1f}s">{safe_ch}</span>'
            )

        html = style + f'<div class="gradient-text">{"".join(spans)}</div>'
        self.set_content(html=html)

    def clear(self):
        """
        Clear the message content.
        """
        self.output.clear_output(wait=True)

    def __enter__(self):
        """
        Enter output context manager.
        """
        return self.output.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit output context manager.
        """
        return self.output.__exit__(exc_type, exc_val, exc_tb)
