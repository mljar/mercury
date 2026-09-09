from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager

Position = Literal["sidebar", "inline", "bottom"]
Size = Literal["small", "medium", "large"]


def _normalize_value(value):
    if not isinstance(value, (str, int, float)):
        raise TypeError("SplitFlap value must be a string or number.")
    return str(value)


def SplitFlap(
    value,
    size: Size = "medium",
    animate: bool = True,
    position: Position = "inline",
    key: str = "",
):
    """Create and display an animated retro split-flap board.

    Parameters
    ----------
    value : str | int | float
        Short text or number displayed on the board.
    size : {"small", "medium", "large"}, optional
        Character tile size. Default is ``"medium"``.
    animate : bool, optional
        Animate changed characters. Default is ``True``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    key : str, optional
        Stable identifier used to reuse the widget across cell executions.

    Returns
    -------
    SplitFlapWidget
        The displayed widget. Call ``set(value)`` to update it in place.
    """
    normalized_value = _normalize_value(value)
    if not isinstance(animate, bool):
        raise TypeError("SplitFlap animate must be a boolean.")

    args = [] if key else [normalized_value]
    kwargs = (
        {}
        if key
        else {
            "size": size,
            "animate": animate,
            "position": position,
        }
    )
    code_uid = WidgetsManager.get_code_uid(
        "SplitFlap", key=key, args=args, kwargs=kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        cached.configure(
            normalized_value,
            size=size,
            animate=animate,
            position=position,
        )
        display(cached)
        return cached

    widget = SplitFlapWidget(
        value=normalized_value,
        size=size,
        animate=animate,
        position=position,
    )
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget


class SplitFlapWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const root = document.createElement("section");
      root.className = "mljar-split-flap";

      const viewport = document.createElement("div");
      viewport.className = "mljar-split-flap-viewport";

      const board = document.createElement("div");
      board.className = "mljar-split-flap-board";
      board.setAttribute("role", "status");
      board.setAttribute("aria-live", "polite");
      board.setAttribute("aria-atomic", "true");

      viewport.appendChild(board);
      root.appendChild(viewport);
      el.appendChild(root);

      let currentValue = "";
      let hasDrawn = false;
      let animationToken = 0;
      let cleanupTimer = null;
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

      function half(className, character) {
        const node = document.createElement("span");
        node.className = className;
        const glyph = document.createElement("span");
        glyph.textContent = character || "\u00a0";
        node.appendChild(glyph);
        return node;
      }

      function staticTile(character) {
        const tile = document.createElement("span");
        tile.className = "mljar-split-flap-tile";
        tile.dataset.character = character;
        tile.setAttribute("aria-hidden", "true");
        tile.append(
          half("mljar-split-flap-half is-top", character),
          half("mljar-split-flap-half is-bottom", character)
        );
        return tile;
      }

      function animatedTile(previousCharacter, nextCharacter, changeIndex) {
        const tile = document.createElement("span");
        tile.className = "mljar-split-flap-tile is-changing";
        tile.dataset.character = nextCharacter;
        tile.setAttribute("aria-hidden", "true");
        tile.style.setProperty(
          "--flap-delay",
          `${Math.min(changeIndex * 18, 108)}ms`
        );

        tile.append(
          half("mljar-split-flap-half is-top", nextCharacter),
          half(
            "mljar-split-flap-half is-bottom is-previous-bottom",
            previousCharacter
          ),
          half(
            "mljar-split-flap-half is-top is-falling-top",
            previousCharacter
          ),
          half(
            "mljar-split-flap-half is-bottom is-arriving-bottom",
            nextCharacter
          )
        );
        return tile;
      }

      function paintRow(row, value, previousValue, shouldAnimate) {
        const nextCharacters = Array.from(value);
        const previousCharacters = Array.from(previousValue);
        const length = shouldAnimate
          ? Math.max(nextCharacters.length, previousCharacters.length)
          : nextCharacters.length;
        const existingTiles = Array.from(row.children);
        let changeIndex = 0;

        for (let index = 0; index < length; index += 1) {
          const nextCharacter = nextCharacters[index] || "";
          const previousCharacter = previousCharacters[index] || "";
          const changed = shouldAnimate && nextCharacter !== previousCharacter;
          const existingTile = existingTiles[index];

          if (
            !changed &&
            existingTile?.dataset.character === nextCharacter &&
            !existingTile.classList.contains("is-changing")
          ) {
            continue;
          }

          const tile = changed
            ? animatedTile(previousCharacter, nextCharacter, changeIndex++)
            : staticTile(nextCharacter);
          if (existingTile) existingTile.replaceWith(tile);
          else row.appendChild(tile);
        }

        for (let index = existingTiles.length - 1; index >= length; index -= 1) {
          existingTiles[index].remove();
        }
      }

      function paint(value, previousValue, shouldAnimate) {
        const nextRows = String(value).split("\\n");
        const previousRows = String(previousValue).split("\\n");
        const length = shouldAnimate
          ? Math.max(nextRows.length, previousRows.length)
          : nextRows.length;
        const existingRows = Array.from(board.children);

        for (let index = 0; index < length; index += 1) {
          let row = existingRows[index];
          if (!row) {
            row = document.createElement("div");
            row.className = "mljar-split-flap-row";
            board.appendChild(row);
          }
          paintRow(
            row,
            nextRows[index] || "",
            previousRows[index] || "",
            shouldAnimate
          );
        }

        for (let index = existingRows.length - 1; index >= length; index -= 1) {
          existingRows[index].remove();
        }
      }

      function draw() {
        const nextValue = String(model.get("value") ?? "");
        const size = model.get("size") || "medium";
        const animate = model.get("animate") !== false;
        const previousValue = currentValue;
        const changed = nextValue !== previousValue;
        const shouldAnimate =
          animate && hasDrawn && changed && !reducedMotion.matches;

        root.dataset.size = size;
        board.setAttribute("aria-label", nextValue);

        if (hasDrawn && !changed) return;

        const token = ++animationToken;
        if (cleanupTimer !== null) window.clearTimeout(cleanupTimer);
        paint(nextValue, previousValue, shouldAnimate);
        currentValue = nextValue;
        hasDrawn = true;

        if (shouldAnimate) {
          cleanupTimer = window.setTimeout(() => {
            if (token === animationToken) paint(currentValue, currentValue, false);
          }, 520);
        }
      }

      const watched = ["value", "size", "animate"];
      watched.forEach(name => model.on(`change:${name}`, draw));
      draw();

      return () => {
        if (cleanupTimer !== null) window.clearTimeout(cleanupTimer);
        watched.forEach(name => model.off(`change:${name}`, draw));
      };
    }
    export default { render };
    """

    _css = """
    .mljar-split-flap {
      width: 100%;
      box-sizing: border-box;
    }
    .mljar-split-flap-viewport {
      max-width: 100%;
      overflow-x: auto;
      overflow-y: hidden;
      scrollbar-width: thin;
    }
    .mljar-split-flap-board {
      --flap-width: 42px;
      --flap-height: 56px;
      --flap-font-size: 30px;
      --flap-gap: 4px;
      display: inline-grid;
      min-width: min-content;
      gap: var(--flap-gap);
      padding: 6px;
      border-radius: var(--mercury-border-radius, 6px);
      background: #090b0d;
      box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.8);
      contain: layout paint;
      box-sizing: border-box;
    }
    .mljar-split-flap[data-size="small"] .mljar-split-flap-board {
      --flap-width: 30px;
      --flap-height: 40px;
      --flap-font-size: 21px;
      --flap-gap: 3px;
      padding: 5px;
    }
    .mljar-split-flap[data-size="large"] .mljar-split-flap-board {
      --flap-width: 58px;
      --flap-height: 78px;
      --flap-font-size: 42px;
      --flap-gap: 5px;
      padding: 8px;
    }
    .mljar-split-flap-row {
      display: flex;
      gap: var(--flap-gap);
      min-width: min-content;
    }
    .mljar-split-flap-tile {
      position: relative;
      flex: 0 0 var(--flap-width);
      width: var(--flap-width);
      height: var(--flap-height);
      border-radius: 4px;
      background: #15191d;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.055),
                  0 2px 5px rgba(0, 0, 0, 0.75);
      color: #f4f0dc;
      font-family: "Roboto Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: var(--flap-font-size);
      font-weight: 700;
      line-height: var(--flap-height);
      text-align: center;
      perspective: 420px;
      contain: paint;
      box-sizing: border-box;
    }
    .mljar-split-flap-tile::after {
      content: "";
      position: absolute;
      z-index: 8;
      top: calc(50% - 1px);
      right: -1px;
      left: -1px;
      height: 2px;
      background: linear-gradient(
        to bottom,
        #050607 0 50%,
        rgba(255, 255, 255, 0.07) 50% 100%
      );
      pointer-events: none;
    }
    .mljar-split-flap-half {
      position: absolute;
      right: 0;
      left: 0;
      height: 50%;
      overflow: hidden;
      backface-visibility: hidden;
      background: linear-gradient(180deg, #292e34 0%, #171b1f 100%);
    }
    .mljar-split-flap-half > span {
      position: absolute;
      right: 0;
      left: 0;
      height: var(--flap-height);
      text-shadow: 0 0 6px color-mix(in srgb, var(--mercury-primary-color, #00a8dc) 18%, transparent);
    }
    .mljar-split-flap-half.is-top {
      top: 0;
      border-radius: 3px 3px 0 0;
    }
    .mljar-split-flap-half.is-top > span {
      top: 0;
    }
    .mljar-split-flap-half.is-bottom {
      bottom: 0;
      border-radius: 0 0 3px 3px;
      background: linear-gradient(180deg, #111418 0%, #20252a 100%);
    }
    .mljar-split-flap-half.is-bottom > span {
      bottom: 0;
    }
    .mljar-split-flap-half.is-previous-bottom {
      z-index: 2;
    }
    .mljar-split-flap-half.is-falling-top {
      z-index: 5;
      transform-origin: center bottom;
      will-change: transform;
      animation: mljar-split-flap-top 190ms cubic-bezier(.55, .06, .68, .19)
                 var(--flap-delay) both;
    }
    .mljar-split-flap-half.is-arriving-bottom {
      z-index: 6;
      transform: rotateX(90deg);
      transform-origin: center top;
      will-change: transform;
      animation: mljar-split-flap-bottom 210ms cubic-bezier(.22, .61, .36, 1)
                 calc(var(--flap-delay) + 180ms) both;
    }
    @keyframes mljar-split-flap-top {
      from { transform: rotateX(0deg); }
      to { transform: rotateX(-90deg); }
    }
    @keyframes mljar-split-flap-bottom {
      from { transform: rotateX(90deg); }
      to { transform: rotateX(0deg); }
    }
    @media (prefers-reduced-motion: reduce) {
      .mljar-split-flap-half.is-falling-top,
      .mljar-split-flap-half.is-arriving-bottom {
        animation: none;
      }
    }
    """

    value = traitlets.Any(default_value="").tag(sync=True)
    size = traitlets.Enum(
        values=["small", "medium", "large"], default_value="medium"
    ).tag(sync=True)
    animate = traitlets.Bool(default_value=True).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"], default_value="inline"
    ).tag(sync=True)

    def __init__(
        self,
        value="",
        size="medium",
        animate=True,
        position="inline",
        **kwargs,
    ):
        super().__init__(
            value=_normalize_value(value),
            size=size,
            animate=animate,
            position=position,
            **kwargs,
        )

    def configure(
        self,
        value,
        size=None,
        animate=None,
        position=None,
    ):
        """Replace the complete display configuration."""
        with self.hold_trait_notifications():
            self.value = _normalize_value(value)
            if size is not None:
                self.size = size
            if animate is not None:
                if not isinstance(animate, bool):
                    raise TypeError("SplitFlap animate must be a boolean.")
                self.animate = animate
            if position is not None:
                self.position = position
        return self

    def set(self, value):
        """Update the displayed value in place."""
        self.value = _normalize_value(value)

    @traitlets.validate("value")
    def _validate_value(self, proposal):
        return _normalize_value(proposal["value"])

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
