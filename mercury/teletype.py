import math
import numbers
from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager

Position = Literal["sidebar", "inline", "bottom"]


def _normalize_text(text):
    if not isinstance(text, str):
        raise TypeError("Teletype text must be a string.")
    return text


def _normalize_speed(speed):
    if isinstance(speed, bool) or not isinstance(speed, numbers.Real):
        raise TypeError("Teletype speed must be a finite non-negative number.")
    normalized = float(speed)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError("Teletype speed must be a finite non-negative number.")
    return normalized


def Teletype(
    text,
    speed=30,
    cursor=True,
    auto_scroll=True,
    position: Position = "inline",
    key: str = "",
):
    """Create and display animated teletype text.

    Text is revealed one Unicode grapheme at a time. Extending ``text`` or calling
    ``append()`` queues only the new suffix, while unrelated replacement text starts
    a fresh reveal.

    Parameters
    ----------
    text : str
        Plain text to display. Spaces and newline characters are preserved.
    speed : int | float, optional
        Delay in milliseconds per visible character. Use ``0`` for immediate output.
        Default is ``30``.
    cursor : bool, optional
        Show a terminal-style cursor. Default is ``True``.
    auto_scroll : bool, optional
        Keep new output visible while the reader remains near the bottom. Default is
        ``True``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    key : str, optional
        Stable identifier used to reuse the widget across cell executions.

    Returns
    -------
    TeletypeWidget
        The displayed widget. Use ``append()``, ``set()``, ``clear()``, or assign to
        ``text`` to update it in place.
    """
    normalized_text = _normalize_text(text)
    normalized_speed = _normalize_speed(speed)
    if not isinstance(cursor, bool):
        raise TypeError("Teletype cursor must be a boolean.")
    if not isinstance(auto_scroll, bool):
        raise TypeError("Teletype auto_scroll must be a boolean.")

    identity_args = [] if key else [normalized_text]
    identity_kwargs = (
        {}
        if key
        else {
            "speed": normalized_speed,
            "cursor": cursor,
            "auto_scroll": auto_scroll,
            "position": position,
        }
    )
    code_uid = WidgetsManager.get_code_uid(
        "Teletype", key=key, args=identity_args, kwargs=identity_kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        cached.configure(
            normalized_text,
            speed=normalized_speed,
            cursor=cursor,
            auto_scroll=auto_scroll,
            position=position,
        )
        display(cached)
        return cached

    widget = TeletypeWidget(
        text=normalized_text,
        speed=normalized_speed,
        cursor=cursor,
        auto_scroll=auto_scroll,
        position=position,
    )
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget


class TeletypeWidget(anywidget.AnyWidget):
    _esm = r"""
    function render({ model, el }) {
      const root = document.createElement("section");
      root.className = "mljar-teletype";

      const visual = document.createElement("pre");
      visual.className = "mljar-teletype-visual";
      visual.setAttribute("aria-hidden", "true");
      const output = document.createTextNode("");
      visual.appendChild(output);

      const announcements = document.createElement("div");
      announcements.className = "mljar-teletype-accessible";
      announcements.setAttribute("role", "log");
      announcements.setAttribute("aria-live", "polite");
      announcements.setAttribute("aria-relevant", "additions text");
      announcements.setAttribute("aria-atomic", "false");

      root.append(visual, announcements);
      el.appendChild(root);

      const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      );
      const segmenter = typeof Intl !== "undefined" && Intl.Segmenter
        ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
        : null;

      let target = "";
      let parts = [];
      let revealed = 0;
      let frame = null;
      let previousTime = null;
      let elapsed = 0;
      let initialized = false;

      function segment(text) {
        if (segmenter) {
          return Array.from(segmenter.segment(text), item => item.segment);
        }
        return Array.from(text);
      }

      function scrollContainer() {
        let parent = root.parentElement;
        while (parent) {
          const style = window.getComputedStyle(parent);
          if (
            /(auto|scroll)/.test(style.overflowY) &&
            parent.scrollHeight > parent.clientHeight
          ) {
            return parent;
          }
          parent = parent.parentElement;
        }
        return document.scrollingElement || document.documentElement;
      }

      function isNearBottom(container) {
        return (
          container.scrollHeight - container.scrollTop - container.clientHeight < 40
        );
      }

      function updateVisual(update) {
        const container = scrollContainer();
        const pinned = isNearBottom(container);
        update();
        if (model.get("auto_scroll") !== false && pinned) {
          container.scrollTop = container.scrollHeight;
        }
      }

      function replaceVisual(text) {
        updateVisual(() => { output.data = text; });
      }

      function appendVisual(text) {
        updateVisual(() => { output.appendData(text); });
      }

      function announce(text, replace = false) {
        if (replace) announcements.replaceChildren();
        if (!text) return;
        const addition = document.createElement("span");
        addition.textContent = text;
        announcements.appendChild(addition);
        while (announcements.childElementCount > 100) {
          announcements.firstElementChild.remove();
        }
      }

      function stopFrame() {
        if (frame !== null) window.cancelAnimationFrame(frame);
        frame = null;
        previousTime = null;
        elapsed = 0;
        root.classList.remove("is-typing");
      }

      function finish() {
        stopFrame();
        revealed = parts.length;
        replaceVisual(target);
      }

      function tick(timestamp) {
        frame = null;
        const speed = Number(model.get("speed"));
        if (reducedMotion.matches || speed <= 0) {
          finish();
          return;
        }

        if (previousTime === null) previousTime = timestamp;
        elapsed += timestamp - previousTime;
        previousTime = timestamp;

        const count = Math.floor(elapsed / speed);
        if (count > 0) {
          const nextRevealed = Math.min(parts.length, revealed + count);
          elapsed -= count * speed;
          appendVisual(parts.slice(revealed, nextRevealed).join(""));
          revealed = nextRevealed;
        }

        if (revealed < parts.length) {
          frame = window.requestAnimationFrame(tick);
        } else {
          stopFrame();
        }
      }

      function start() {
        if (revealed >= parts.length) {
          root.classList.remove("is-typing");
          return;
        }
        if (reducedMotion.matches || Number(model.get("speed")) <= 0) {
          finish();
          return;
        }
        root.classList.add("is-typing");
        if (frame === null) frame = window.requestAnimationFrame(tick);
      }

      function drawText() {
        const next = String(model.get("text") ?? "");
        if (initialized && next === target) return;

        const previousTarget = target;
        const previousParts = parts;
        const extendsTarget = initialized && next.startsWith(previousTarget);
        target = next;
        parts = segment(target);

        if (extendsTarget) {
          let sharedParts = 0;
          while (
            sharedParts < previousParts.length &&
            sharedParts < parts.length &&
            previousParts[sharedParts] === parts[sharedParts]
          ) {
            sharedParts += 1;
          }
          if (revealed > sharedParts) {
            revealed = sharedParts;
            replaceVisual(parts.slice(0, revealed).join(""));
          }
          announce(next.slice(previousTarget.length));
        } else {
          stopFrame();
          revealed = 0;
          replaceVisual("");
          announce(next, true);
        }

        initialized = true;
        start();
      }

      function drawOptions() {
        root.dataset.cursor = model.get("cursor") === false ? "hidden" : "visible";
        previousTime = null;
        elapsed = 0;
        start();
      }

      function reduceMotionChanged() {
        if (reducedMotion.matches) finish();
      }

      model.on("change:text", drawText);
      model.on("change:speed", drawOptions);
      model.on("change:cursor", drawOptions);
      model.on("change:auto_scroll", drawOptions);
      if (reducedMotion.addEventListener) {
        reducedMotion.addEventListener("change", reduceMotionChanged);
      } else {
        reducedMotion.addListener(reduceMotionChanged);
      }

      drawOptions();
      drawText();

      return () => {
        stopFrame();
        model.off("change:text", drawText);
        model.off("change:speed", drawOptions);
        model.off("change:cursor", drawOptions);
        model.off("change:auto_scroll", drawOptions);
        if (reducedMotion.removeEventListener) {
          reducedMotion.removeEventListener("change", reduceMotionChanged);
        } else {
          reducedMotion.removeListener(reduceMotionChanged);
        }
      };
    }
    export default { render };
    """

    _css = """
    .mljar-teletype {
      width: 100%;
      padding: 14px 16px;
      border: 0.5px solid var(--mercury-border-color, #d0d7de);
      border-radius: var(--mercury-border-radius, 6px);
      background: var(--mercury-card-background-color, var(--mercury-panel-bg, #ffffff));
      color: var(--mercury-text-color, #0f172a);
      box-sizing: border-box;
    }
    .mljar-teletype-visual {
      display: block;
      min-height: 1.5em;
      margin: 0;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
      color: inherit;
      font-family: ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas,
                   "Liberation Mono", "Courier New", monospace;
      font-size: var(--mercury-font-size, 16px);
      line-height: 1.55;
      tab-size: 4;
    }
    .mljar-teletype[data-cursor="visible"] .mljar-teletype-visual::after {
      content: "";
      display: inline-block;
      width: 0.62em;
      height: 1.08em;
      margin-left: 0.12em;
      vertical-align: -0.16em;
      background: var(--mercury-accent-color, var(--mercury-primary-color, #007bff));
      animation: mljar-teletype-cursor 1s steps(1, end) infinite;
      user-select: none;
    }
    .mljar-teletype.is-typing .mljar-teletype-visual::after {
      animation: none;
      opacity: 1;
    }
    .mljar-teletype-accessible {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
    @keyframes mljar-teletype-cursor {
      0%, 48% { opacity: 1; }
      49%, 100% { opacity: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .mljar-teletype-visual::after {
        animation: none !important;
        opacity: 1;
      }
    }
    """

    text = traitlets.Unicode(default_value="", allow_none=False).tag(sync=True)
    speed = traitlets.Float(default_value=30).tag(sync=True)
    cursor = traitlets.Bool(default_value=True).tag(sync=True)
    auto_scroll = traitlets.Bool(default_value=True).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"], default_value="inline"
    ).tag(sync=True)

    def __init__(
        self,
        text="",
        speed=30,
        cursor=True,
        auto_scroll=True,
        position="inline",
        **kwargs,
    ):
        super().__init__(
            text=_normalize_text(text),
            speed=_normalize_speed(speed),
            cursor=cursor,
            auto_scroll=auto_scroll,
            position=position,
            **kwargs,
        )

    @traitlets.validate("speed")
    def _validate_speed(self, proposal):
        return _normalize_speed(proposal["value"])

    def configure(
        self,
        text,
        speed=None,
        cursor=None,
        auto_scroll=None,
        position=None,
    ):
        """Replace the complete teletype configuration."""
        with self.hold_trait_notifications():
            self.text = _normalize_text(text)
            if speed is not None:
                self.speed = _normalize_speed(speed)
            if cursor is not None:
                if not isinstance(cursor, bool):
                    raise TypeError("Teletype cursor must be a boolean.")
                self.cursor = cursor
            if auto_scroll is not None:
                if not isinstance(auto_scroll, bool):
                    raise TypeError("Teletype auto_scroll must be a boolean.")
                self.auto_scroll = auto_scroll
            if position is not None:
                self.position = position
        return self

    def append(self, text):
        """Append plain text to the current animation queue."""
        self.text += _normalize_text(text)

    def set(self, text):
        """Replace the target text."""
        self.text = _normalize_text(text)

    def clear(self):
        """Clear the output."""
        self.text = ""

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        bundle = data[0] if isinstance(data, tuple) else data
        widget_mimetype = "application/vnd.jupyter.widget-view+json"
        if isinstance(bundle, dict) and widget_mimetype in bundle:
            bundle[MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            bundle.pop("text/plain", None)
        return data
