# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

import base64
from typing import Literal, Optional

import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def PDF(
    file_path: Optional[str] = None,
    label: str = "",
    width: str = "100%",
    height: str = "800",
    position: Position = "inline",
    key: str = "",
):
    """
    Display a PDF viewer widget.

    This function instantiates a `PDFWidget` which embeds a PDF document inside
    an iframe. The PDF can be provided via a local file path.

    Parameters
    ----------
    file_path : str | None, optional
        Path to a local PDF file to display. If `None`, the widget is created
        without a document (you may set `data_url` later).
    label : str, optional
        Optional label shown above the PDF viewer.
        Default is `""`.
    width : str, optional
        CSS width of the iframe (e.g. `"100%"`, `"800px"`).
        Default is `"100%"`.
    height : str, optional
        Height of the iframe (e.g. `"800"`, `"600px"`). The iframe `height`
        attribute accepts a number (pixels) or a CSS string depending on browser.
        Default is `"800"`.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed.
        Default is `"inline"`.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Examples
    --------
    Display a local PDF:

    >>> import mercury as mr
    >>> mr.PDF(file_path="report.pdf", label="Report", height="900")

    Place the viewer in the bottom area:

    >>> mr.PDF(file_path="slides.pdf", position="bottom")
    """
    args = [file_path, label, width, height, position]
    kwargs = {
        "file_path": file_path,
        "label": label,
        "width": width,
        "height": height,
        "position": position,
    }

    code_uid = WidgetsManager.get_code_uid("PDF", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return

    instance = PDFWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)


class PDFWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      el.innerHTML = "";

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
      iframe.src = model.get("data_url") || "";

      container.appendChild(iframe);
      el.appendChild(container);
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

    file_path = traitlets.Unicode(default_value="").tag(sync=True)
    data_url = traitlets.Unicode(default_value="").tag(sync=True)
    width = traitlets.Unicode(default_value="100%").tag(sync=True)
    height = traitlets.Unicode(default_value="800").tag(sync=True)
    label = traitlets.Unicode(default_value="").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement",
    ).tag(sync=True)

    def __init__(self, file_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if file_path:
            self.file_path = file_path
            try:
                with open(file_path, "rb") as fin:
                    content = fin.read()
                base64_pdf = base64.b64encode(content).decode("utf-8")
                self.data_url = f"data:application/pdf;base64,{base64_pdf}"
            except Exception as e:
                # Keep widget alive; show empty iframe
                print("Problem with displaying PDF:", e)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
