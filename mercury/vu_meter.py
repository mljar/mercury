import builtins
import math
import numbers
import warnings
from collections.abc import Sequence
from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager

Position = Literal["sidebar", "inline", "bottom"]
Size = Literal["small", "medium", "large"]


def _normalize_number(value, name):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(f"VUMeter {name} must be a finite number.")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"VUMeter {name} must be a finite number.")
    return normalized


def _normalize_zones(zones, minimum, maximum):
    if zones is None:
        return []
    if isinstance(zones, (str, bytes)) or not isinstance(zones, Sequence):
        raise TypeError("VUMeter zones must be a sequence of two numbers.")
    if len(zones) == 0:
        return []
    if len(zones) != 2:
        raise ValueError("VUMeter zones must contain exactly two thresholds.")

    low = _normalize_number(zones[0], "zone threshold")
    high = _normalize_number(zones[1], "zone threshold")
    if not minimum < low < high < maximum:
        raise ValueError(
            "VUMeter zones must be ascending and strictly inside the meter range."
        )
    return [low, high]


def _normalize_configuration(value, minimum, maximum, zones):
    normalized_min = _normalize_number(minimum, "min")
    normalized_max = _normalize_number(maximum, "max")
    if normalized_min >= normalized_max:
        raise ValueError("VUMeter min must be smaller than max.")

    normalized_value = _normalize_number(value, "value")
    clamped_value = builtins.min(
        normalized_max, builtins.max(normalized_min, normalized_value)
    )
    if clamped_value != normalized_value:
        warnings.warn(
            "VUMeter value is outside the configured range and was clamped.",
            UserWarning,
            stacklevel=3,
        )

    normalized_zones = _normalize_zones(zones, normalized_min, normalized_max)
    return (
        clamped_value,
        normalized_min,
        normalized_max,
        normalized_zones,
    )


def VUMeter(
    value,
    min=0,
    max=100,
    label: str = "",
    zones=None,
    higher_is_better: bool = True,
    size: Size = "medium",
    animate: bool = True,
    position: Position = "inline",
    key: str = "",
):
    """Create and display a retro analog VU meter.

    The needle responds to live value changes. With two zone thresholds, the scale
    uses Mercury's success, warning, and danger theme colors.

    Parameters
    ----------
    value : int | float
        Current finite meter value. Values outside the range are clamped.
    min, max : int | float, optional
        Finite scale bounds where ``min < max``. Defaults are ``0`` and ``100``.
    label : str, optional
        Text printed inside the instrument face.
    zones : sequence of two numbers | None, optional
        Ascending thresholds strictly inside the scale.
    higher_is_better : bool, optional
        Use danger-to-success zones when ``True`` and the reverse when ``False``.
    size : {"small", "medium", "large"}, optional
        Responsive instrument size. Default is ``"medium"``.
    animate : bool, optional
        Animate later needle changes. Default is ``True``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    key : str, optional
        Stable identifier used to reuse the meter across cell executions.

    Returns
    -------
    VUMeterWidget
        The displayed live widget. Assign to ``value`` or call ``set(value)``.
    """
    normalized = _normalize_configuration(value, min, max, zones)
    if not isinstance(label, str):
        raise TypeError("VUMeter label must be a string.")
    if not isinstance(higher_is_better, bool):
        raise TypeError("VUMeter higher_is_better must be a boolean.")
    if not isinstance(animate, bool):
        raise TypeError("VUMeter animate must be a boolean.")

    identity_args = [] if key else [normalized[0], normalized[1], normalized[2]]
    identity_kwargs = (
        {}
        if key
        else {
            "label": label,
            "zones": normalized[3],
            "higher_is_better": higher_is_better,
            "size": size,
            "animate": animate,
            "position": position,
        }
    )
    code_uid = WidgetsManager.get_code_uid(
        "VUMeter", key=key, args=identity_args, kwargs=identity_kwargs
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        cached.configure(
            normalized[0],
            min=normalized[1],
            max=normalized[2],
            label=label,
            zones=normalized[3],
            higher_is_better=higher_is_better,
            size=size,
            animate=animate,
            position=position,
        )
        display(cached)
        return cached

    widget = VUMeterWidget(
        value=normalized[0],
        min=normalized[1],
        max=normalized[2],
        label=label,
        zones=normalized[3],
        higher_is_better=higher_is_better,
        size=size,
        animate=animate,
        position=position,
    )
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget


class VUMeterWidget(anywidget.AnyWidget):
    _esm = """
    const SVG_NS = "http://www.w3.org/2000/svg";
    const CENTER_X = 180;
    const CENTER_Y = 172;
    const START_ANGLE = -70;
    const SWEEP_ANGLE = 140;

    function svgNode(name, attributes = {}) {
      const node = document.createElementNS(SVG_NS, name);
      Object.entries(attributes).forEach(([key, value]) => {
        node.setAttribute(key, String(value));
      });
      return node;
    }

    function point(ratio, radius) {
      const angle = (START_ANGLE + ratio * SWEEP_ANGLE) * Math.PI / 180;
      return {
        x: CENTER_X + Math.sin(angle) * radius,
        y: CENTER_Y - Math.cos(angle) * radius,
      };
    }

    function arcPath(startRatio, endRatio, radius) {
      const start = point(startRatio, radius);
      const end = point(endRatio, radius);
      return `M ${start.x} ${start.y} A ${radius} ${radius} 0 0 1 ${end.x} ${end.y}`;
    }

    function displayNumber(value, span) {
      const decimals = span <= 2 ? 2 : span <= 20 ? 1 : 0;
      return Number(value.toFixed(decimals)).toString();
    }

    function render({ model, el }) {
      const root = document.createElement("section");
      root.className = "mljar-vu-meter";

      const instrument = document.createElement("div");
      instrument.className = "mljar-vu-meter-instrument";
      instrument.setAttribute("role", "meter");

      const svg = svgNode("svg", {
        class: "mljar-vu-meter-dial",
        viewBox: "0 0 360 220",
        "aria-hidden": "true",
      });

      const defs = svgNode("defs");
      const faceGradient = svgNode("linearGradient", {
        id: `mljar-vu-face-${model.model_id}`,
        x1: "0",
        y1: "0",
        x2: "0",
        y2: "1",
      });
      faceGradient.append(
        svgNode("stop", { class: "mljar-vu-face-light", offset: "0%" }),
        svgNode("stop", { class: "mljar-vu-face-dark", offset: "100%" })
      );
      const glassGradient = svgNode("linearGradient", {
        id: `mljar-vu-glass-${model.model_id}`,
        x1: "0",
        y1: "0",
        x2: "0",
        y2: "1",
      });
      glassGradient.append(
        svgNode("stop", { class: "mljar-vu-glass-light", offset: "0%" }),
        svgNode("stop", { class: "mljar-vu-glass-clear", offset: "72%" })
      );
      defs.append(faceGradient, glassGradient);

      const face = svgNode("rect", {
        class: "mljar-vu-meter-face",
        x: 0,
        y: 0,
        width: 360,
        height: 220,
        rx: 10,
        fill: `url(#mljar-vu-face-${model.model_id})`,
      });
      const scale = svgNode("g", { class: "mljar-vu-meter-scale" });
      const label = svgNode("text", {
        class: "mljar-vu-meter-label",
        x: CENTER_X,
        y: 204,
        "text-anchor": "middle",
      });
      const needle = svgNode("g", { class: "mljar-vu-meter-needle" });
      needle.append(
        svgNode("line", {
          class: "mljar-vu-meter-needle-line",
          x1: CENTER_X,
          y1: CENTER_Y + 12,
          x2: CENTER_X,
          y2: 43,
        }),
        svgNode("circle", {
          class: "mljar-vu-meter-hub-outer",
          cx: CENTER_X,
          cy: CENTER_Y,
          r: 14,
        }),
        svgNode("circle", {
          class: "mljar-vu-meter-hub-inner",
          cx: CENTER_X,
          cy: CENTER_Y,
          r: 7,
        })
      );

      const glass = svgNode("path", {
        class: "mljar-vu-meter-glass",
        d: "M 18 18 H 342 V 92 Q 180 58 18 104 Z",
        fill: `url(#mljar-vu-glass-${model.model_id})`,
      });

      svg.append(defs, face, scale, label, needle, glass);
      instrument.appendChild(svg);
      root.appendChild(instrument);
      el.appendChild(root);

      function addArc(start, end, className) {
        scale.appendChild(
          svgNode("path", {
            class: `mljar-vu-meter-arc ${className}`,
            d: arcPath(start, end, 127),
          })
        );
      }

      function drawScale() {
        const minimum = Number(model.get("min"));
        const maximum = Number(model.get("max"));
        const span = maximum - minimum;
        const zones = model.get("zones") || [];
        const higherIsBetter = model.get("higher_is_better") !== false;

        scale.replaceChildren();
        if (zones.length === 2) {
          const low = (Number(zones[0]) - minimum) / span;
          const high = (Number(zones[1]) - minimum) / span;
          const zoneNames = higherIsBetter
            ? ["is-danger", "is-warning", "is-success"]
            : ["is-success", "is-warning", "is-danger"];
          addArc(0, low, zoneNames[0]);
          addArc(low, high, zoneNames[1]);
          addArc(high, 1, zoneNames[2]);
        } else {
          addArc(0, 1, "is-primary");
        }

        for (let index = 0; index <= 20; index += 1) {
          const ratio = index / 20;
          const major = index % 5 === 0;
          const inside = point(ratio, major ? 107 : 113);
          const outside = point(ratio, 121);
          scale.appendChild(
            svgNode("line", {
              class: major
                ? "mljar-vu-meter-tick is-major"
                : "mljar-vu-meter-tick",
              x1: inside.x,
              y1: inside.y,
              x2: outside.x,
              y2: outside.y,
            })
          );

          if (major) {
            const textPoint = point(ratio, 92);
            const tickLabel = svgNode("text", {
              class: "mljar-vu-meter-tick-label",
              x: textPoint.x,
              y: textPoint.y + 4,
              "text-anchor": "middle",
            });
            tickLabel.textContent = displayNumber(minimum + ratio * span, span);
            scale.appendChild(tickLabel);
          }
        }

      }

      function drawAppearance() {
        label.textContent = model.get("label") || "VU";
        root.dataset.size = model.get("size") || "medium";
        root.classList.toggle("without-animation", model.get("animate") === false);
        drawValue();
      }

      function drawValue() {
        const minimum = Number(model.get("min"));
        const maximum = Number(model.get("max"));
        const value = Number(model.get("value"));
        const ratio = Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)));
        const angle = START_ANGLE + ratio * SWEEP_ANGLE;
        const heading = model.get("label") || "VU meter";

        needle.style.transform = `rotate(${angle}deg)`;
        instrument.setAttribute("aria-label", heading);
        instrument.setAttribute("aria-valuemin", String(minimum));
        instrument.setAttribute("aria-valuemax", String(maximum));
        instrument.setAttribute("aria-valuenow", String(value));
        instrument.setAttribute("aria-valuetext", `${heading}: ${value}`);
      }

      const scaleTraits = ["min", "max", "zones", "higher_is_better"];
      const appearanceTraits = ["label", "size", "animate"];
      const drawScaleAndValue = () => {
        drawScale();
        drawValue();
      };
      model.on("change:value", drawValue);
      scaleTraits.forEach(name => model.on(`change:${name}`, drawScaleAndValue));
      appearanceTraits.forEach(name => model.on(`change:${name}`, drawAppearance));
      drawScale();
      drawAppearance();
      window.requestAnimationFrame(() => root.classList.add("is-ready"));

      return () => {
        model.off("change:value", drawValue);
        scaleTraits.forEach(name => model.off(`change:${name}`, drawScaleAndValue));
        appearanceTraits.forEach(name => model.off(`change:${name}`, drawAppearance));
      };
    }
    export default { render };
    """

    _css = """
    .mljar-vu-meter {
      width: 100%;
      max-width: 360px;
      color: var(--mercury-text-color, #0f172a);
      font-family: var(--mercury-font-family, Arial, sans-serif);
      box-sizing: border-box;
    }
    .mljar-vu-meter[data-size="small"] { max-width: 280px; }
    .mljar-vu-meter[data-size="large"] { max-width: 480px; }
    .mljar-vu-meter-instrument {
      width: 100%;
      padding: 0;
      overflow: hidden;
      border: 0.5px solid var(--mercury-border-color, #d0d7de);
      border-radius: var(--mercury-border-radius-lg, 10px);
      background: var(
        --mercury-card-background-color,
        var(--mercury-panel-bg, #ffffff)
      );
      box-shadow: none;
      box-sizing: border-box;
      transition: border-color 0.15s, background-color 0.15s;
    }
    .mljar-vu-meter-dial {
      display: block;
      width: 100%;
      height: auto;
      overflow: visible;
    }
    .mljar-vu-face-light {
      stop-color: color-mix(in srgb, var(--mercury-card-background-color, var(--mercury-panel-bg, #ffffff)) 94%, var(--mercury-warning-color, #f59e0b));
    }
    .mljar-vu-face-dark {
      stop-color: color-mix(in srgb, var(--mercury-card-background-color, var(--mercury-panel-bg, #ffffff)) 97%, #000000);
    }
    .mljar-vu-meter-face {
      stroke: none;
    }
    .mljar-vu-meter-arc {
      fill: none;
      stroke-width: 6;
      stroke-linecap: butt;
      opacity: 0.88;
    }
    .mljar-vu-meter-arc.is-primary { stroke: var(--mercury-primary-color, #007bff); }
    .mljar-vu-meter-arc.is-success { stroke: var(--mercury-success-color, #19b96c); }
    .mljar-vu-meter-arc.is-warning { stroke: var(--mercury-warning-color, #f59e0b); }
    .mljar-vu-meter-arc.is-danger { stroke: var(--mercury-danger-color, #dc3545); }
    .mljar-vu-meter-tick {
      stroke: var(--mercury-muted-text-color, #475569);
      stroke-width: 1.3;
      opacity: 0.72;
    }
    .mljar-vu-meter-tick.is-major {
      stroke: var(--mercury-text-color, #0f172a);
      stroke-width: 2.1;
      opacity: 0.92;
    }
    .mljar-vu-meter-tick-label {
      fill: var(--mercury-text-color, #0f172a);
      font-family: var(--mercury-font-family, Arial, sans-serif);
      font-size: 12px;
      font-weight: 650;
    }
    .mljar-vu-meter-label {
      fill: var(--mercury-text-color, #0f172a);
      font-family: var(--mercury-heading-font-family, inherit);
      font-size: 13px;
      font-weight: var(--mercury-heading-font-weight, 800);
      letter-spacing: 1.4px;
    }
    .mljar-vu-meter-needle {
      transform-origin: 180px 172px;
      transform-box: view-box;
    }
    .mljar-vu-meter.is-ready:not(.without-animation) .mljar-vu-meter-needle {
      transition: transform 520ms cubic-bezier(0.22, 1.18, 0.36, 1);
    }
    .mljar-vu-meter-needle-line {
      stroke: var(--mercury-accent-color, var(--mercury-primary-color, #007bff));
      stroke-width: 3;
      stroke-linecap: round;
      filter: drop-shadow(1px 1px 1px color-mix(in srgb, #000000 35%, transparent));
    }
    .mljar-vu-meter-hub-outer {
      fill: color-mix(in srgb, var(--mercury-text-color, #0f172a) 72%, #ffffff);
      stroke: color-mix(in srgb, var(--mercury-text-color, #0f172a) 76%, #000000);
      stroke-width: 2;
    }
    .mljar-vu-meter-hub-inner {
      fill: var(--mercury-accent-color, var(--mercury-primary-color, #007bff));
      stroke: color-mix(in srgb, var(--mercury-accent-color, #007bff) 72%, #000000);
      stroke-width: 1;
    }
    .mljar-vu-glass-light { stop-color: rgba(255, 255, 255, 0.34); }
    .mljar-vu-glass-clear { stop-color: rgba(255, 255, 255, 0); }
    .mljar-vu-meter-glass { pointer-events: none; }
    @media (prefers-reduced-motion: reduce) {
      .mljar-vu-meter-needle { transition: none !important; }
    }
    """

    min = traitlets.Float(default_value=0).tag(sync=True)
    max = traitlets.Float(default_value=100).tag(sync=True)
    value = traitlets.Any(default_value=0).tag(sync=True)
    label = traitlets.Unicode(default_value="").tag(sync=True)
    zones = traitlets.List(traitlets.Float(), default_value=[]).tag(sync=True)
    higher_is_better = traitlets.Bool(default_value=True).tag(sync=True)
    size = traitlets.Enum(
        values=["small", "medium", "large"], default_value="medium"
    ).tag(sync=True)
    animate = traitlets.Bool(default_value=True).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"], default_value="inline"
    ).tag(sync=True)

    def __init__(
        self,
        value=0,
        min=0,
        max=100,
        label="",
        zones=None,
        higher_is_better=True,
        size="medium",
        animate=True,
        position="inline",
        **kwargs,
    ):
        normalized = _normalize_configuration(value, min, max, zones)
        super().__init__(
            min=normalized[1],
            max=normalized[2],
            zones=normalized[3],
            label=label,
            higher_is_better=higher_is_better,
            size=size,
            animate=animate,
            position=position,
            value=normalized[0],
            **kwargs,
        )

    @traitlets.validate("value")
    def _validate_value(self, proposal):
        value = _normalize_number(proposal["value"], "value")
        clamped = builtins.min(self.max, builtins.max(self.min, value))
        if clamped != value:
            warnings.warn(
                "VUMeter value is outside the configured range and was clamped.",
                UserWarning,
                stacklevel=3,
            )
        return clamped

    def configure(
        self,
        value,
        min=0,
        max=100,
        label="",
        zones=None,
        higher_is_better=True,
        size="medium",
        animate=True,
        position="inline",
    ):
        """Replace the complete meter configuration."""
        normalized = _normalize_configuration(value, min, max, zones)
        with self.hold_trait_notifications():
            self.min = normalized[1]
            self.max = normalized[2]
            self.zones = normalized[3]
            self.label = label
            self.higher_is_better = higher_is_better
            self.size = size
            self.animate = animate
            self.position = position
            self.value = normalized[0]
        return self

    def set(self, value):
        """Update the meter value in place."""
        self.value = value

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
