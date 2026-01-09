import anywidget
import traitlets
import ipywidgets as widgets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


# ---------- Global CSS (injected once) ----------
def _ensure_global_tabs_styles():
    css = f"""
    <style>
      .mljar-tabs {{
        width: 100%;
        border: 1px solid {THEME.get('border_color', '#ddd')};
        border-radius: {THEME.get('border_radius', '8px')};
        background: {THEME.get('panel_bg', '#fff')};
        overflow: hidden;
      }}

      /* Tablist (header) */
      .mljar-tablist {{
        display: flex;
        gap: 4px;
        align-items: stretch;
        border-bottom: 1px solid {THEME.get('border_color', '#ddd')};
        background: {THEME.get('panel_bg_hover', '#f7f7f9')};
        flex-wrap: wrap; /* allow wrapping if many tabs */
      }}
      .mljar-tablist button {{
        appearance: none;
        border: 0;
        background: transparent;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', '600')};
        color: {THEME.get('text_color', '#222')};
        padding: 10px 14px;
        cursor: pointer;
        position: relative;
        transition: background 0.15s ease;
        border-radius: 0;
      }}
      .mljar-tablist button:hover {{
        background: {THEME.get('panel_bg_hover_2', '#efefef')};
      }}
      .mljar-tablist button[aria-selected="true"] {{
        color: {THEME.get('primary_color', '#007bff')};
      }}
      .mljar-tablist button[aria-selected="true"]::after {{
        content: "";
        position: absolute;
        left: 8px; right: 8px; bottom: 0;
        height: 3px;
        background: {THEME.get('primary_color', '#007bff')};
        border-radius: 2px;
      }}

      /* Panels */
      .mljar-tabpanels {{
        width: 100%;
        box-sizing: border-box;
        padding: 8px;
      }}
      .mljar-tab-panel {{
        display: none;
        width: 100%;
        box-sizing: border-box;
      }}
      .mljar-tab-panel.is-active {{
        display: block;
      }}

      /* --- IMPORTANT: neutralize ipywidgets' default margins that cause overflow --- */
      .mljar-tab-panel :is(.jupyter-widgets, .widget-box, .widget-hbox, .widget-vbox) {{
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: 100%;          /* prevent width+margin from exceeding container */
        box-sizing: border-box;   /* be safe if padding gets applied */
      }}

      /* Wrap long lines to avoid horizontal scrollbars */
      .mljar-tab-panel .jp-RenderedText pre,
      .mljar-tab-panel pre,
      .mljar-tab-panel code {{
        white-space: pre-wrap !important;
        word-break: break-word !important;
      }}

      /* Scale media to container width */
      .mljar-tab-panel img,
      .mljar-tab-panel canvas,
      .mljar-tab-panel svg,
      .mljar-tab-panel video {{
        max-width: 100%;
        height: auto;
      }}

      /* Wide tables scroll inside themselves, not the whole panel */
      .mljar-tab-panel table {{
        display: block;
        max-width: 100%;
        overflow-x: auto;
      }}

      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {{
        .mljar-tablist button {{
          transition: none;
        }}
      }}
    </style>
    """
    display(widgets.HTML(css))


class TabOutput(widgets.Output):
    """Tab widget with a convenient .clear() alias."""
    def clear(self, wait: bool = True):
        self.clear_output(wait=wait)

# ---------- Public API ----------
def Tabs(labels=("Tab 1", "Tab 2"), active=0, key=""):
    """
    Create a tabbed container with one output area per tab.

    This helper renders a tab header and a content panel area.
    Each tab is associated with an `ipywidgets.Output` object,
    which can be written to using a `with` block.

    Parameters
    ----------
    labels : tuple[str] or list[str], optional
        Labels displayed in the tab header.
        Each label creates one tab and one output panel.
        Default is ("Tab 1", "Tab 2").

    active : int, optional
        Index (0-based) of the tab that is active initially.
        If out of range, it is clamped to a valid index.
        Default is 0.

    key : str, optional
        Unique identifier used to distinguish Tabs instances
        with identical arguments. Required when Tabs are
        created inside loops.

    Returns
    -------
    tuple[ipywidgets.Output, ...]
        A tuple of output widgets, one per tab.
        Write content into a tab using:

        >>> tabs = mr.Tabs(["A", "B"])
        >>> with tabs[0]:
        ...     print("Content for tab A")

    Notes
    -----
    - Only one tab panel is visible at a time.
    - Switching tabs does not clear their contents.
    - Tabs are cached and reused between cell re-runs
      unless a different `key` is provided.
    """
    _ensure_global_tabs_styles()

    code_uid = WidgetsManager.get_code_uid("Tabs", key=key or "|".join(map(str, labels)), 
                kwargs=dict(labels=labels))
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        box, outs, _header, _panels = cached
        display(box)
        return outs

    header = _TabsHeaderWidget(labels=list(labels), active=int(active))

    # Create an Output per tab, wrapped in a panel Box
    outs = tuple(TabOutput() for _ in labels)
    panels = []
    for i, out in enumerate(outs):
        out.layout.width = "100%"
        # Hide horizontal overflow; our CSS handles wrapping and internal table scroll.
        out.layout.overflow_x = "hidden"
        out.layout.overflow_y = "auto"

        panel = widgets.Box([out], layout=widgets.Layout(width="100%"))
        panel.add_class("mljar-tab-panel")
        if i == int(active):
            panel.add_class("is-active")
        panels.append(panel)

    panel_box = widgets.VBox(panels, layout=widgets.Layout(width="100%"))
    panel_box.add_class("mljar-tabpanels")

    def _on_active_change(change):
        idx = int(change["new"])
        for j, p in enumerate(panels):
            if j == idx:
                p.add_class("is-active")
            else:
                p.remove_class("is-active")

    header.observe(_on_active_change, names="active")

    container = widgets.VBox([header, panel_box], layout=widgets.Layout(width="100%"))
    container.add_class("mljar-tabs")

    display(container)
    WidgetsManager.add_widget(code_uid, (container, outs, header, panels))
    return outs


# ---------- Header AnyWidget ----------
class _TabsHeaderWidget(anywidget.AnyWidget):
    labels = traitlets.List(trait=traitlets.Unicode(), default_value=["Tab 1", "Tab 2"]).tag(sync=True)
    active = traitlets.Int(0).tag(sync=True)
    custom_css = traitlets.Unicode(default_value="").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement hint.",
    ).tag(sync=True)

    _esm = """

    function render({ model, el }) {

      const tablist = document.createElement("div");
      tablist.classList.add("mljar-tablist");
      tablist.setAttribute("role", "tablist");

      const buttons = [];

      function makeButton(label, index) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.classList.add("mljar-tab");
        btn.setAttribute("role", "tab");
        btn.setAttribute("aria-selected", "false");
        btn.setAttribute("tabindex", "-1");
        btn.textContent = label || `Tab ${index + 1}`;

        btn.addEventListener("click", () => {
          model.set("active", index);
          model.save_changes();
        });

        btn.addEventListener("keydown", (e) => {
          const len = buttons.length;
          let i = model.get("active") || 0;
          if (e.key === "ArrowRight") {
            i = (i + 1) % len;
            model.set("active", i);
            model.save_changes();
            buttons[i].focus();
          } else if (e.key === "ArrowLeft") {
            i = (i - 1 + len) % len;
            model.set("active", i);
            model.save_changes();
            buttons[i].focus();
          } else if (e.key === "Home") {
            i = 0;
            model.set("active", i);
            model.save_changes();
            buttons[i].focus();
          } else if (e.key === "End") {
            i = len - 1;
            model.set("active", i);
            model.save_changes();
            buttons[i].focus();
          }
        });

        return btn;
      }

      function syncButtons() {
        const labels = model.get("labels") || [];
        const active = model.get("active") || 0;

        // Rebuild if labels length changed
        if (buttons.length !== labels.length) {
          tablist.replaceChildren();
          buttons.length = 0;
          labels.forEach((lab, i) => {
            const b = makeButton(lab, i);
            buttons.push(b);
            tablist.appendChild(b);
          });
        }

        // Update states
        buttons.forEach((b, i) => {
          const selected = (i === active);
          b.setAttribute("aria-selected", String(selected));
          b.setAttribute("tabindex", selected ? "0" : "-1");
        });
      }

      // Initial build
      syncButtons();
      el.appendChild(tablist);

      // React to model changes
      model.on("change:labels", syncButtons);
      model.on("change:active", syncButtons);

      // Custom CSS injection if provided
      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        const styleTag = document.createElement("style");
        styleTag.textContent = css;
        el.appendChild(styleTag);
      }
    }
    export default { render };
    """

    _css = f"""
    .mljar-tab {{
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      font-weight: {THEME.get('font_weight', '600')};
      color: {THEME.get('text_color', '#222')};
    }}
    """

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_()
        if len(data) > 1:
            import json
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data