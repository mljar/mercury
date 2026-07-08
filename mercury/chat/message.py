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

from ..theme import THEME

MSG_CSS_CLASS = "mljar-chat-msg"
DEFAULT_EMOJI_BACKGROUND = "#e5e7eb"


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
        Role used to determine avatar kind.
    emoji : str, optional
        Emoji displayed inside the avatar.
    emoji_background : str, optional
        Avatar background color as a hex string. Defaults to a hardcoded gray.

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

    def __init__(self, markdown="", role="user", emoji="👤", emoji_background=None):
        """
        Initialize a Message widget.

        Parameters
        ----------
        markdown : str, optional
            Initial Markdown content.
        role : str, optional
            Message role used for avatar kind.
        emoji : str, optional
            Emoji shown in the avatar.
        emoji_background : str, optional
            Avatar background color as a hex string.
        """
        super().__init__()

        avatar_bg = str(emoji_background or DEFAULT_EMOJI_BACKGROUND)
        avatar_fg = self._get_avatar_foreground(avatar_bg)
        role_kind = self._get_role_kind(role)
        avatar_html = (
            f"<style>{self._message_css()}</style>"
            f'<div class="mljar-chat-msg-avatar mljar-chat-msg-avatar-{role_kind}" '
            f'style="background:{avatar_bg};color:{avatar_fg};">'
            f'<span style="font-size:18px;line-height:1;">{emoji}</span>'
            f'</div>'
        )

        avatar = widgets.HTML(
            value=avatar_html,
            layout=widgets.Layout(margin="0 0 8px 0", align_self="flex-start"),
        )

        self.output = widgets.Output(
            layout=widgets.Layout(
                align_self="flex-start",
                margin="0 0 0 0",
                overflow_y="visible",
                overflow_x="visible",
                padding="8px 12px 4px 12px",
                width="auto",
                flex="0 1 auto",
                border="none",
            )
        )
        self.output.add_class(MSG_CSS_CLASS)
        self.output.add_class("mljar-chat-msg-bubble")
        self.output.add_class(f"mljar-chat-msg-bubble-{role_kind}")

        self.children = [avatar, self.output]
        self.layout.align_items = "flex-start"
        self.layout.width = "100%"
        self.add_class("mljar-chat-msg-row")

        # Buffers and rendering mode
        self._mode = None  # one of {"markdown", "html", "text", None}
        self._md_buffer = ""
        self._html_buffer = ""
        self._text_buffer = ""
        self._on_update = None

        if markdown != "":
            self.set_content(markdown=markdown)

    @staticmethod
    def _get_role_kind(role):
        role_key = str(role or "").lower()
        if role_key in {"user", "human"}:
            return "user"
        if role_key == "tool":
            return "tool"
        return "assistant"

    @staticmethod
    def _get_avatar_foreground(background):
        color = str(background or "").strip().lstrip("#")
        if len(color) == 3:
            color = "".join(ch * 2 for ch in color)
        if len(color) != 6:
            return THEME.get("text_color", "#222")
        try:
            red = int(color[0:2], 16)
            green = int(color[2:4], 16)
            blue = int(color[4:6], 16)
        except ValueError:
            return THEME.get("text_color", "#222")

        luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
        if luminance < 160:
            return THEME.get(
                "button_text_color",
                THEME.get("widget_background_color", "#fff"),
            )
        return THEME.get("text_color", "#222")

    @staticmethod
    def _message_css():
        return f"""
        .mljar-chat-msg-row {{
            width: 100%;
            box-sizing: border-box;
            align-items: flex-start;
        }}

        .mljar-chat-msg-avatar {{
            width: 36px;
            height: 36px;
            min-width: 36px;
            border-radius: {THEME.get('border_radius', '6px')};
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            margin: 0 0 8px 0;
            box-shadow: 0 1px 4px rgb(60 60 60 / 10%);
            border: none !important;
        }}

        .mljar-chat-msg-bubble {{
            display: inline-block;
            width: fit-content;
            max-width: 100%;
            vertical-align: top;
            box-sizing: border-box;
            border-radius: {THEME.get('border_radius', '6px')};
            color: {THEME.get('text_color', '#222')};
            font-family: {THEME.get('font_family', 'Arial, sans-serif')};
            font-size: {THEME.get('font_size', '14px')};
            font-weight: {THEME.get('font_weight', 'normal')};
            line-height: 1.5;
            border: none !important;
        }}

        .mljar-chat-msg-bubble > .jp-OutputArea,
        .mljar-chat-msg-bubble .jp-OutputArea-child,
        .mljar-chat-msg-bubble .jp-OutputArea-output,
        .mljar-chat-msg-bubble .jp-RenderedHTMLCommon,
        .mljar-chat-msg-bubble .lm-Widget {{
            background: transparent !important;
            width: auto !important;
            max-width: 100%;
            min-width: 0;
            box-sizing: border-box;
            margin: 0 !important;
            padding: 0 !important;
        }}

        .mljar-chat-msg-bubble .jp-OutputArea-child,
        .mljar-chat-msg-bubble .jp-OutputArea-output {{
            display: inline-block;
            vertical-align: top;
        }}

        .mljar-chat-msg-bubble .jp-MarkdownOutput,
        .mljar-chat-msg-bubble .jp-MarkdownOutput p,
        .mljar-chat-msg-bubble .jp-RenderedHTMLCommon,
        .mljar-chat-msg-bubble .jp-RenderedHTMLCommon p {{
            color: {THEME.get('text_color', '#222')} !important;
        }}

        .mljar-chat-msg-bubble p {{
            margin: 0;
        }}

        .mljar-chat-msg-bubble-user {{
            background: transparent;
            color: {THEME.get('text_color', '#222')};
            border-color: {THEME.get('border_color', '#ccc')};
        }}

        .mljar-chat-msg-bubble-assistant {{
            background: transparent;
            color: {THEME.get('text_color', '#222')};
        }}

        .mljar-chat-msg-bubble-tool {{
            background: transparent;
            color: {THEME.get('text_color', '#222')};
        }}

        .mljar-chat-msg-bubble a {{
            color: inherit;
            text-decoration: underline;
            text-underline-offset: 0.14em;
        }}

        .mljar-chat-msg-bubble code {{
            color: inherit;
            background: {THEME.get('panel_bg_hover', THEME.get('panel_bg', '#f7f7f9'))};
            border: 1px solid {THEME.get('border_color', '#ccc')};
            border-radius: {THEME.get('border_radius_sm', '4px')};
            padding: 0.12em 0.38em;
        }}

        .mljar-chat-msg-bubble pre {{
            margin: 0;
            background: {THEME.get('panel_bg', THEME.get('widget_background_color', '#fff'))};
            border: 1px solid {THEME.get('border_color', '#ccc')};
            border-radius: {THEME.get('border_radius', '6px')};
            padding: 0.85em 1em;
            overflow-x: auto;
        }}
        """


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
        self._notify_update()

    def _notify_update(self):
        if self._on_update is None:
            return
        try:
            self._on_update()
        except Exception:
            pass

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
