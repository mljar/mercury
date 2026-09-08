from collections.abc import Mapping
from typing import Iterable, Literal, Optional

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager

Position = Literal["sidebar", "inline", "bottom"]
Orientation = Literal["horizontal", "vertical"]
Animation = Literal["blink", "pulse"]
SUPPORTED_STATES = ("off", "ok", "warning", "error", "active")


def _normalize_statuses(statuses):
    if not isinstance(statuses, Mapping):
        raise TypeError("StatusLights statuses must be a mapping of labels to states.")

    normalized = {}
    for raw_label, raw_state in statuses.items():
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise ValueError("StatusLights labels must be non-empty strings.")
        if not isinstance(raw_state, str):
            raise ValueError(f"StatusLights state for '{raw_label}' must be a string.")
        label = raw_label.strip()
        state = raw_state.strip().lower()
        if state not in SUPPORTED_STATES:
            supported = ", ".join(SUPPORTED_STATES)
            raise ValueError(
                f"Unsupported StatusLights state '{raw_state}' for '{label}'. "
                f"Supported states: {supported}."
            )
        if label in normalized:
            raise ValueError(f"Duplicate StatusLights label after trimming: '{label}'.")
        normalized[label] = state
    return normalized


def _normalize_animation_labels(labels, field, status_labels):
    if labels is None:
        return []
    if isinstance(labels, (str, bytes)) or not isinstance(labels, Iterable):
        raise TypeError(f"StatusLights {field} must be a sequence of labels.")

    normalized = []
    for raw_label in labels:
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise ValueError(f"StatusLights {field} labels must be non-empty strings.")
        label = raw_label.strip()
        if label not in status_labels:
            raise ValueError(
                f"StatusLights {field} label '{label}' is missing from statuses."
            )
        if label not in normalized:
            normalized.append(label)
    return normalized


def _normalize_configuration(statuses, blink=None, pulse=None):
    normalized_statuses = _normalize_statuses(statuses)
    normalized_blink = _normalize_animation_labels(blink, "blink", normalized_statuses)
    normalized_pulse = _normalize_animation_labels(pulse, "pulse", normalized_statuses)
    conflicts = [label for label in normalized_blink if label in normalized_pulse]
    if conflicts:
        raise ValueError(
            "StatusLights labels cannot blink and pulse at the same time: "
            + ", ".join(conflicts)
            + "."
        )
    return normalized_statuses, normalized_blink, normalized_pulse


def StatusLights(
    statuses,
    blink=None,
    pulse=None,
    title: str = "",
    orientation: Orientation = "horizontal",
    show_title: bool = True,
    show_group_border: bool = True,
    show_item_borders: bool = True,
    position: Position = "inline",
    key: str = "",
):
    """Create and display a group of animated status lamps.

    Parameters
    ----------
    statuses : Mapping[str, str]
        Ordered mapping of lamp labels to one of ``off``, ``ok``, ``warning``,
        ``error``, or ``active``.
    blink, pulse : Iterable[str] | None, optional
        Labels whose lamps should blink or pulse. A label can use at most one
        animation and must exist in ``statuses``.
    title : str, optional
        Heading displayed above the lamps.
    orientation : {"horizontal", "vertical"}, optional
        Arrange lamps in a responsive row or a single column. Default is
        ``"horizontal"``.
    show_title : bool, optional
        Display ``title`` when it is non-empty. Default is ``True``.
    show_group_border : bool, optional
        Display the outer panel surface and border. Default is ``True``.
    show_item_borders : bool, optional
        Display a surface and border around each lamp item. Default is ``True``.
    position : {"sidebar", "inline", "bottom"}, optional
        Mercury layout placement. Default is ``"inline"``.
    key : str, optional
        Stable identifier used to reuse the widget across cell executions.

    Returns
    -------
    StatusLightsWidget
        The displayed widget. Use ``set()``, ``update()``, and
        ``set_animation()`` for live changes.
    """
    normalized_statuses, normalized_blink, normalized_pulse = _normalize_configuration(
        statuses, blink, pulse
    )
    if not isinstance(title, str):
        raise TypeError("StatusLights title must be a string.")
    display_options = {
        "show_title": show_title,
        "show_group_border": show_group_border,
        "show_item_borders": show_item_borders,
    }
    invalid_option = next(
        (
            name
            for name, value in display_options.items()
            if not isinstance(value, bool)
        ),
        None,
    )
    if invalid_option is not None:
        raise TypeError(f"StatusLights {invalid_option} must be a boolean.")

    identity_args = [] if key else [tuple(normalized_statuses)]
    identity_kwargs = (
        {}
        if key
        else {
            "title": title,
            "orientation": orientation,
            **display_options,
            "position": position,
        }
    )
    code_uid = WidgetsManager.get_code_uid(
        "StatusLights",
        key=key,
        args=identity_args,
        kwargs=identity_kwargs,
    )
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        cached.configure(
            normalized_statuses,
            blink=normalized_blink,
            pulse=normalized_pulse,
            title=title,
            orientation=orientation,
            **display_options,
            position=position,
        )
        display(cached)
        return cached

    widget = StatusLightsWidget(
        statuses=normalized_statuses,
        blink=normalized_blink,
        pulse=normalized_pulse,
        title=title,
        orientation=orientation,
        **display_options,
        position=position,
    )
    WidgetsManager.add_widget(code_uid, widget)
    display(widget)
    return widget


class StatusLightsWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const root = document.createElement("section");
      root.className = "mljar-status-lights";

      const title = document.createElement("div");
      title.className = "mljar-status-lights-title";

      const grid = document.createElement("div");
      grid.className = "mljar-status-lights-grid";
      grid.setAttribute("role", "list");

      root.append(title, grid);
      el.appendChild(root);

      function draw() {
        const statuses = model.get("statuses") || {};
        const blink = new Set(model.get("blink") || []);
        const pulse = new Set(model.get("pulse") || []);
        const heading = model.get("title") || "";
        const orientation = model.get("orientation") || "horizontal";
        const showTitle = model.get("show_title") !== false;
        const showGroupBorder = model.get("show_group_border") !== false;
        const showItemBorders = model.get("show_item_borders") !== false;

        title.textContent = heading;
        title.hidden = !showTitle || !heading;
        root.classList.toggle("is-vertical", orientation === "vertical");
        root.classList.toggle("without-group-border", !showGroupBorder);
        root.classList.toggle("without-item-borders", !showItemBorders);
        grid.replaceChildren();

        Object.entries(statuses).forEach(([label, state]) => {
          const item = document.createElement("div");
          item.className = "mljar-status-light-item";
          item.setAttribute("role", "listitem");
          item.setAttribute("aria-label", `${label}: ${state}`);

          const lamp = document.createElement("span");
          lamp.className = `mljar-status-light mljar-status-light-${state}`;
          if (blink.has(label)) lamp.classList.add("is-blinking");
          if (pulse.has(label)) lamp.classList.add("is-pulsing");
          lamp.setAttribute("aria-hidden", "true");

          const text = document.createElement("span");
          text.className = "mljar-status-light-text";

          const name = document.createElement("span");
          name.className = "mljar-status-light-label";
          name.textContent = label;

          const stateLabel = document.createElement("span");
          stateLabel.className = "mljar-status-light-state";
          stateLabel.textContent = state;

          text.append(name, stateLabel);
          item.append(lamp, text);
          grid.appendChild(item);
        });
      }

      const watched = [
        "statuses",
        "blink",
        "pulse",
        "title",
        "orientation",
        "show_title",
        "show_group_border",
        "show_item_borders"
      ];
      watched.forEach(name => model.on(`change:${name}`, draw));
      draw();

      return () => {
        watched.forEach(name => model.off(`change:${name}`, draw));
      };
    }
    export default { render };
    """

    _css = f"""
    .mljar-status-lights {{
      width: 100%;
      padding: 14px;
      border: 1px solid var(--mercury-border-color, #d0d7de);
      border-radius: var(--mercury-border-radius-lg, 10px);
      background: var(--mercury-panel-bg, #ffffff);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45),
                  var(--mercury-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.04));
      color: var(--mercury-text-color, #0f172a);
      font-family: var(--mercury-font-family, Arial, sans-serif);
      box-sizing: border-box;
    }}
    .mljar-status-lights.without-group-border {{
      padding: 0;
      border: 0;
      background: transparent;
      box-shadow: none;
    }}
    .mljar-status-lights-title {{
      margin: 0 0 11px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.045em;
      text-transform: uppercase;
    }}
    .mljar-status-lights-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
      gap: 8px;
    }}
    .mljar-status-lights.is-vertical .mljar-status-lights-grid {{
      grid-template-columns: minmax(0, 1fr);
    }}
    .mljar-status-light-item {{
      min-width: 0;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 10px;
      border: 1px solid var(--mercury-border-color, #d0d7de);
      border-radius: var(--mercury-border-radius, 6px);
      background: var(--mercury-surface-color, #ffffff);
      box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
      box-sizing: border-box;
    }}
    .mljar-status-lights.without-item-borders .mljar-status-light-item {{
      padding: 5px 4px;
      border: 0;
      background: transparent;
      box-shadow: none;
    }}
    .mljar-status-light {{
      --lamp-color: #94a3b8;
      flex: 0 0 17px;
      width: 17px;
      height: 17px;
      border: 1px solid rgba(15, 23, 42, 0.42);
      border-radius: 50%;
      background: radial-gradient(
        circle at 34% 28%,
        #ffffff 0 7%,
        var(--lamp-color) 25%,
        color-mix(in srgb, var(--lamp-color) 68%, #000000) 100%
      );
      box-shadow: inset 0 -2px 3px rgba(0, 0, 0, 0.35),
                  0 0 4px var(--lamp-color),
                  0 0 12px color-mix(in srgb, var(--lamp-color) 72%, transparent),
                  0 0 22px color-mix(in srgb, var(--lamp-color) 38%, transparent);
      filter: saturate(1.35) brightness(1.08);
      box-sizing: border-box;
    }}
    .mljar-status-light-off {{
      --lamp-color: #94a3b8;
      opacity: 0.46;
      filter: none;
      box-shadow: inset 0 -2px 3px rgba(0, 0, 0, 0.4);
    }}
    .mljar-status-light-ok {{
      --lamp-color: var(--mercury-success-color, #00e676);
    }}
    .mljar-status-light-warning {{
      --lamp-color: var(--mercury-warning-color, #ffd600);
    }}
    .mljar-status-light-error {{
      --lamp-color: var(--mercury-danger-color, #ff1744);
    }}
    .mljar-status-light-active {{
      --lamp-color: var(--mercury-primary-color, #00b8ff);
    }}
    .mljar-status-light-text {{
      min-width: 0;
      display: flex;
      flex-direction: column;
      line-height: 1.15;
    }}
    .mljar-status-light-label {{
      overflow: hidden;
      color: var(--mercury-text-color, #0f172a);
      font-size: 13px;
      font-weight: 600;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .mljar-status-light-state {{
      margin-top: 3px;
      color: var(--mercury-muted-text-color, #475569);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .mljar-status-light.is-blinking {{
      animation: mljar-status-light-blink 0.85s steps(1, end) infinite;
    }}
    .mljar-status-light.is-pulsing {{
      animation: mljar-status-light-pulse 1.55s ease-in-out infinite;
    }}
    @keyframes mljar-status-light-blink {{
      0%, 48% {{ opacity: 1; }}
      49%, 100% {{ opacity: 0.16; box-shadow: none; }}
    }}
    @keyframes mljar-status-light-pulse {{
      0%, 100% {{
        transform: scale(0.92);
        filter: saturate(1.2) brightness(0.9);
        opacity: 0.72;
      }}
      50% {{
        transform: scale(1.1);
        filter: saturate(1.55) brightness(1.3);
        opacity: 1;
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .mljar-status-light.is-blinking,
      .mljar-status-light.is-pulsing {{
        animation: none;
      }}
    }}
    """

    statuses = traitlets.Dict(
        key_trait=traitlets.Unicode(),
        value_trait=traitlets.Unicode(),
        default_value={},
    ).tag(sync=True)
    blink = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    pulse = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    title = traitlets.Unicode(default_value="").tag(sync=True)
    orientation = traitlets.Enum(
        values=["horizontal", "vertical"],
        default_value="horizontal",
    ).tag(sync=True)
    show_title = traitlets.Bool(default_value=True).tag(sync=True)
    show_group_border = traitlets.Bool(default_value=True).tag(sync=True)
    show_item_borders = traitlets.Bool(default_value=True).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
    ).tag(sync=True)

    def __init__(
        self,
        statuses=None,
        blink=None,
        pulse=None,
        title="",
        orientation="horizontal",
        show_title=True,
        show_group_border=True,
        show_item_borders=True,
        position="inline",
        **kwargs,
    ):
        normalized = _normalize_configuration(statuses or {}, blink, pulse)
        super().__init__(
            statuses=normalized[0],
            blink=normalized[1],
            pulse=normalized[2],
            title=title,
            orientation=orientation,
            show_title=show_title,
            show_group_border=show_group_border,
            show_item_borders=show_item_borders,
            position=position,
            **kwargs,
        )

    def configure(
        self,
        statuses,
        blink=None,
        pulse=None,
        title=None,
        orientation=None,
        show_title=None,
        show_group_border=None,
        show_item_borders=None,
        position=None,
    ):
        """Replace the complete lamp configuration."""
        normalized = _normalize_configuration(statuses, blink, pulse)
        self.statuses, self.blink, self.pulse = normalized
        if title is not None:
            if not isinstance(title, str):
                raise TypeError("StatusLights title must be a string.")
            self.title = title
        if orientation is not None:
            self.orientation = orientation
        if show_title is not None:
            self.show_title = show_title
        if show_group_border is not None:
            self.show_group_border = show_group_border
        if show_item_borders is not None:
            self.show_item_borders = show_item_borders
        if position is not None:
            self.position = position
        return self

    def set(self, name, state):
        """Add or update one lamp."""
        normalized = _normalize_statuses({name: state})
        statuses = dict(self.statuses)
        statuses.update(normalized)
        self.statuses = statuses

    def update(self, statuses):
        """Merge multiple lamp states."""
        normalized = _normalize_statuses(statuses)
        updated = dict(self.statuses)
        updated.update(normalized)
        self.statuses = updated

    def set_animation(self, name, animation: Optional[Animation] = None):
        """Set ``blink`` or ``pulse`` for one lamp, or clear its animation."""
        if not isinstance(name, str) or name.strip() not in self.statuses:
            raise ValueError(
                f"StatusLights animation label '{name}' is missing from statuses."
            )
        label = name.strip()
        if animation not in (None, "blink", "pulse"):
            raise ValueError(
                "StatusLights animation must be 'blink', 'pulse', or None."
            )
        blink = [item for item in self.blink if item != label]
        pulse = [item for item in self.pulse if item != label]
        if animation == "blink":
            blink.append(label)
        elif animation == "pulse":
            pulse.append(label)
        self.blink = blink
        self.pulse = pulse

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
