import anywidget
import traitlets
import base64
import json
from IPython.display import display
from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME


def PDF(*args, key="", **kwargs):
    code_uid = WidgetsManager.get_code_uid("PDF", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = PDFWidget(*args, **kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class PDFWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let container = document.createElement("div");
      container.classList.add("mljar-pdf-container");

      const label = model.get("label");
      if (label) {
        const topLabel = document.createElement("div");
        topLabel.classList.add("mljar-pdf-label");
        topLabel.innerHTML = label;
        container.appendChild(topLabel);
      }

      const iframe = document.createElement("iframe");
      iframe.width = model.get("width") || "100%";
      iframe.height = model.get("height") || "800";
      iframe.style.border = "none";
      iframe.src = model.get("data_url");

      container.appendChild(iframe);
      el.appendChild(container);

      const css = model.get("custom_css");
      if (css && css.trim().length > 0) {
        let styleTag = document.createElement("style");
        styleTag.textContent = css;
        el.appendChild(styleTag);
      }
    }
    export default { render };
    """

    _css = f"""
    .mljar-pdf-container {{
      display: flex;
      flex-direction: column;
      width: 95%;
      margin: auto;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      font-size: {THEME.get('font_size', '14px')};
      color: {THEME.get('text_color', '#222')};
      margin-bottom: 8px;
    }}
    .mljar-pdf-label {{
      margin-bottom: 6px;
      font-weight: bold;
    }}
    """

    # --- traits ---
    file_path = traitlets.Unicode(default_value="").tag(sync=True)
    data_url = traitlets.Unicode(default_value="").tag(sync=True)
    width = traitlets.Unicode(default_value="100%").tag(sync=True)
    height = traitlets.Unicode(default_value="800").tag(sync=True)
    label = traitlets.Unicode(default_value="").tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement"
    ).tag(sync=True)

    def __init__(self, file_path=None, **kwargs):
        super().__init__(**kwargs)
        if file_path:
            try:
                with open(file_path, "rb") as fin:
                    content = fin.read()
                base64_pdf = base64.b64encode(content).decode("utf-8")
                self.data_url = f"data:application/pdf;base64,{base64_pdf}"
            except Exception as e:
                print("Problem with displaying PDF:", e)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
