# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal, Union

import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


def Download(
    data: Union[str, bytes],
    filename: str = "file.txt",
    label: str = "Download",
    mime: str = "text/plain",
    position: Position = "sidebar",
    is_base64: bool = False,
    key: str = "",
):
    """
    Create and display a Download widget.

    The Download widget renders a button that triggers a browser download when
    clicked. The downloaded file content is taken from `data`.

    The widget supports two data modes:

    - Plain text mode (default): `data` is treated as text and stored in a Blob.
    - Base64 mode (`is_base64=True`): `data` is treated as base64-encoded content
      and decoded in the browser before download.

    If a widget with the same configuration already exists (identified by a
    unique code UID generated from widget type, arguments, keyword arguments, and
    `key`), the existing instance is returned and displayed instead of creating
    a new one.

    Parameters
    ----------
    data : str | bytes
        File content. If `is_base64=False`, it is treated as plain text (or bytes
        decoded as UTF-8). If `is_base64=True`, it must be a base64 string.
    filename : str, optional
        Name of the downloaded file.
        Default is `"file.txt"`.
    label : str, optional
        Button label.
        Default is `"Download"`.
    mime : str, optional
        MIME type of the downloaded content.
        Default is `"text/plain"`.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed. Default is `"sidebar"`.
    is_base64 : bool, optional
        If `True`, `data` is interpreted as base64.
        Default is `False`.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.


    Examples
    --------
    Download a text file:

    >>> import mercury as mr
    >>> mr.Download("hello world\\n", filename="hello.txt", label="Download TXT")

    Download a CSV:

    >>> csv = "a,b\\n1,2\\n"
    >>> mr.Download(csv, filename="data.csv", mime="text/csv", label="Download CSV")

    Download binary data (encode to base64 first):

    >>> import base64
    >>> raw = b"\\x00\\x01\\x02"
    >>> b64 = base64.b64encode(raw).decode("ascii")
    >>> mr.Download(b64, filename="data.bin", mime="application/octet-stream", is_base64=True)
    """
    # Normalize bytes -> string (for traitlets.Unicode)
    if isinstance(data, (bytes, bytearray)) and not is_base64:
        data = data.decode("utf-8", errors="replace")
    elif isinstance(data, (bytes, bytearray)) and is_base64:
        # If user passed bytes base64, decode to str
        data = data.decode("ascii", errors="strict")

    id_kwargs = dict(
        filename=filename,
        label=label,
        mime=mime,
        position=position,
        is_base64=is_base64,
    )
    code_uid = WidgetsManager.get_code_uid("Download", key=key, kwargs=id_kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = DownloadWidget(
        data=str(data),
        filename=filename,
        label=label,
        mime=mime,
        position=position,
        is_base64=is_base64,
    )
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class DownloadWidget(anywidget.AnyWidget):
    _esm = """
    function base64ToBlob(base64, mime) {
        const binary = atob(base64);
        const array = [];
        for (let i = 0; i < binary.length; i++) {
            array.push(binary.charCodeAt(i));
        }
        return new Blob([new Uint8Array(array)], {type: mime});
    }

    function render({ model, el }) {
        el.innerHTML = "";

        const container = document.createElement("div");
        container.classList.add("mljar-download-container");

        const btn = document.createElement("button");
        btn.type = "button";
        btn.classList.add("mljar-download-btn");

        function syncFromModel() {
            btn.textContent = model.get("label") || "Download";
        }

        btn.onclick = () => {
            const data = model.get("data") || "";
            const filename = model.get("filename") || "file.txt";
            const mime = model.get("mime") || "application/octet-stream";

            if (model.get("is_base64")) {
                const blob = base64ToBlob(data, mime);
                const url = URL.createObjectURL(blob);
                triggerDownload(url, filename);
            } else {
                const blob = new Blob([data], {type: mime});
                const url = URL.createObjectURL(blob);
                triggerDownload(url, filename);
            }
        };

        function triggerDownload(url, filename) {
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        }

        container.appendChild(btn);
        el.appendChild(container);

        model.on("change:label", syncFromModel);
        syncFromModel();
    }
    export default { render };
    """

    _css = f"""
    .mljar-download-container {{
        display: inline-flex;
        width: auto;
        font-family: {THEME.get('font_family', 'Arial, sans-serif')};
        margin-bottom: 8px;
        padding-left: 4px;
        padding-right: 4px;
    }}

    .mljar-download-btn {{
        border: 1px solid {THEME.get('primary_color', '#007bff')};
        background: {THEME.get('primary_color', '#007bff')};
        color: {THEME.get('button_primary_text', '#fff')};
        border-radius: {THEME.get('border_radius', '8px')};
        padding: 4px 12px 4px 12px;
        margin-top: 5px;
        margin-bottom: 5px;
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease, border-color 120ms ease;
        user-select: none;
        outline: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: {THEME.get('font_size', '14px')};
        font-weight: {THEME.get('font_weight', '600')};
        box-shadow: {THEME.get('button_shadow', '0 1px 2px rgba(0,0,0,0.06)')};
    }}

    .mljar-download-btn:hover {{
        transform: translateY(-1px);
        box-shadow: {THEME.get('button_shadow_hover', '0 2px 6px rgba(0,0,0,0.08)')};
        border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
        background: {THEME.get('run_button_background_hover', THEME.get('primary_color', '#007bff'))};
        color: {THEME.get('button_primary_text', '#fff')};
    }}

    .mljar-download-btn:active {{
        transform: translateY(0);
        box-shadow: {THEME.get('button_shadow', '0 1px 2px rgba(0,0,0,0.06)')};
        background: {THEME.get('selected_background_color', '#eef3ff')};
        color: {THEME.get('button_primary_text', '#fff')};
    }}

    .mljar-download-btn:focus-visible {{
        outline: none;
        border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
        box-shadow: none;
    }}
    """

    data = traitlets.Unicode("").tag(sync=True)  # base64 or text
    filename = traitlets.Unicode("file.txt").tag(sync=True)
    mime = traitlets.Unicode("text/plain").tag(sync=True)
    label = traitlets.Unicode("Download").tag(sync=True)
    is_base64 = traitlets.Bool(False).tag(sync=True)

    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data
