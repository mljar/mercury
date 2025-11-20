import anywidget
import traitlets

from .manager import WidgetsManager, MERCURY_MIMETYPE

def _filter_identity_kwargs(d, exclude=("value", "data")):
    # keep only config; drop state-like keys
    return {k: v for k, v in d.items() if k not in exclude}

def Download(data, filename="file.txt", label="Download", mime="text/plain", key="", is_base64=False, **kwargs):
    id_kwargs = _filter_identity_kwargs(
        dict(filename=filename, label=label, mime=mime, is_base64=is_base64, **kwargs),
        exclude=("value", "data")
    )
    code_uid = WidgetsManager.get_code_uid("Download", key=key, kwargs=id_kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = DownloadWidget(
        data=data,
        filename=filename,
        label=label,
        mime=mime,
        is_base64=is_base64,
        **kwargs
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

            // If data is base64-encoded
            if (model.get("is_base64")) {
                const blob = base64ToBlob(data, mime);
                const url = URL.createObjectURL(blob);
                triggerDownload(url, filename);
            } else {
                // Plain text
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

        // Optional: simple styles
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
    is_base64 = traitlets.Bool(False).tag(sync=True)  # True if data is base64

    # Optionally, custom CSS or placement as in your Slider
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS to append to default styles").tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="sidebar",
        help="Widget placement: sidebar, inline, or bottom"
    ).tag(sync=True)

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_()
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position
            }
            import json
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data


