# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal, Union

import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE

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
        return 

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
        el.innerHTML = ""; // Clear old content

        let container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "flex-start";

        let btn = document.createElement("button");
        btn.innerHTML = model.get("label") || "Download";
        btn.classList.add("mljar-download-btn");

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

        let styleTag = document.createElement("style");
        styleTag.textContent = `
        .mljar-download-btn {
            padding: 6px 20px;
            background: #0081fa;
            color: #fff;
            border-radius: 7px;
            border: none;
            font-size: 1em;
            cursor: pointer;
            margin: 4px 0;
        }
        .mljar-download-btn:hover {
            background: #0059a8;
        }
        `;
        el.appendChild(styleTag);
    }
    export default { render };
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
