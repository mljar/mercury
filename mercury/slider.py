import anywidget
import traitlets

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME

def Slider(*args, key="", **kwargs):
    code_uid = WidgetsManager.get_code_uid("Slider", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = SliderWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance

class SliderWidget(anywidget.AnyWidget):
    _esm = """
function render({ model, el }) {
  // Your existing UI creation code (unchanged) ...
  const container = document.createElement("div");
  container.classList.add("mljar-slider-container");

  const topLabel = document.createElement("div");
  topLabel.classList.add("mljar-slider-top-label");
  topLabel.innerHTML = model.get("label") || "Select number";

  const sliderRow = document.createElement("div");
  sliderRow.classList.add("mljar-slider-row");

  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = model.get("min");
  slider.max = model.get("max");
  slider.value = model.get("value");
  slider.classList.add("mljar-slider-input");

  const valueLabel = document.createElement("span");
  valueLabel.classList.add("mljar-slider-value-label");
  valueLabel.innerHTML = model.get("value");

  let debounceTimer = null;
  slider.addEventListener("input", () => {
    model.set("value", Number(slider.value));
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => model.save_changes(), 100);
  });

  model.on("change:value", () => {
    slider.value = model.get("value");
    valueLabel.innerHTML = model.get("value");
  });

  sliderRow.appendChild(slider);
  sliderRow.appendChild(valueLabel);
  container.appendChild(topLabel);
  container.appendChild(sliderRow);
  el.appendChild(container);

  // ---- read cell id (no DOM modifications) ----
const LOG_PREFIX = '[SliderWidget]';
const ID_ATTR = 'data-cell-id';
const hostWithId = el.closest(`[${ID_ATTR}]`);
const cellId = hostWithId ? hostWithId.getAttribute(ID_ATTR) : null;

if (cellId) {
  // console.log(`${LOG_PREFIX} found cell_id`, cellId);
  model.set('cell_id', cellId);
  model.save_changes();
  // also send an explicit event
  model.send({ type: 'cell_id_detected', value: cellId });
        
}

  // Optional: handle case where stamp might appear slightly later
  if (!cellId) {
    const mo = new MutationObserver(() => {
      const host = el.closest(`[${ID_ATTR}]`);
      const newId = host?.getAttribute(ID_ATTR);
      if (newId) {
        // console.log('set cell id', newId);
        model.set('cell_id', newId);
        model.save_changes();
        
        // also send an explicit event
        model.send({ type: 'cell_id_detected', value: newId });
        
        mo.disconnect();
      }
    });
    mo.observe(document.body, { attributes: true, subtree: true, attributeFilter: [ID_ATTR] });
  }
}
export default { render };
    """
    _css = f"""
    .mljar-slider-container {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        width: 100%;
        min-width: 120px;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', 'normal')};
        color: {THEME.get('text_color', '#222')};
    }}

    .mljar-slider-top-label {{
        margin-bottom: 6px;
        font-weight: bold;
    }}

    .mljar-slider-row {{
        display: flex;
        flex-direction: row;
        align-items: center;
        width: 100%;
        overflow: hidden;
    }}

    .mljar-slider-input {{
        flex: 1 1 auto;
        min-width: 60px;
        max-width: 100%;
        margin-right: 16px;
        background: transparent;
        -webkit-appearance: none;
        appearance: none;
        border: none;
        height: 24px; /* big enough for thumb */
        padding: 0;
    }}

    .mljar-slider-input:focus {{
        outline: none;
    }}

    /* Track */
    .mljar-slider-input::-webkit-slider-runnable-track {{
        height: 6px;
        background: {THEME.get('slider_track_color', '#e0e0e0')};
        border-radius: {THEME.get('border_radius', '6px')};
        margin: auto; /* center track in the input box */
    }}
    .mljar-slider-input::-moz-range-track {{
        height: 6px;
        background: {THEME.get('slider_track_color', '#e0e0e0')};
        border-radius: {THEME.get('border_radius', '6px')};
    }}

    /* Thumb */
    .mljar-slider-input::-webkit-slider-thumb {{
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: {THEME.get('primary_color', '#007bff')};
        cursor: pointer;
        margin-top: -5px; /* centers thumb on track */
    }}
    .mljar-slider-input::-moz-range-thumb {{
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: {THEME.get('primary_color', '#007bff')};
        cursor: pointer;
    }}

    .mljar-slider-value-label {{
        font-weight: bold;
        font-size: 1.1em;
        color: {THEME.get('text_color', '#000')};
        margin-left: 8px;
    }}
    """



    
    value = traitlets.Int(0).tag(sync=True)
    min = traitlets.Int(0).tag(sync=True)
    max = traitlets.Int(100).tag(sync=True)
    label = traitlets.Unicode("Select number").tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS to append to default styles").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom"
    ).tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_()
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime

        return data

