import anywidget
import traitlets
from IPython.display import display

from .manager import WidgetsManager, MERCURY_MIMETYPE
from .theme import THEME

class UploadedFile:
    def __init__(self, name, value):
        self.name = name
        self.value = bytes(value)
    def __repr__(self):
        return f"UploadedFile(name={self.name!r}, value=<{len(self.value)} bytes>)"


class FileWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      el.innerHTML = "";

      const container = document.createElement("div");
      container.classList.add("mljar-file-container");
      container.style.containerType = "inline-size"; // enable @container

      const label = document.createElement("div");
      label.classList.add("mljar-file-label");
      label.innerHTML = model.get("label") || "File upload";

      const input = document.createElement("input");
      input.type = "file";
      input.disabled = model.get("disabled");
      input.multiple = model.get("multiple");
      const inputId = `mljar-file-${Math.random().toString(36).slice(2)}`;
      input.id = inputId;
      input.classList.add("mljar-file-input-hidden");

      if (model.get("hidden")) container.style.display = "none";

      const dropzone = document.createElement("label");
      dropzone.classList.add("mljar-file-dropzone");
      dropzone.setAttribute("for", inputId);
      dropzone.innerHTML = `
        <div>Drag and drop files here</div>
        <div class="mljar-file-drop-hint">Limit ${model.get("max_file_size")} per file</div>
      `;

      const browseBtn = document.createElement("button");
      browseBtn.classList.add("mljar-file-browse-btn");
      browseBtn.type = "button";
      browseBtn.textContent = "Browse files";

      const fileList = document.createElement("ul");
      fileList.classList.add("mljar-file-list");

      const openPicker = () => input.click();
      browseBtn.onclick = openPicker;

      function handleFiles(files) {
        const filesArr = Array.from(files);
        filesArr.forEach(file => {
          const maxSize = model.get("max_file_size");
          let allowed = true;
          if (maxSize.endsWith("MB")) {
            allowed = file.size <= parseInt(maxSize) * 1024 * 1024;
          } else if (maxSize.endsWith("GB")) {
            allowed = file.size <= parseInt(maxSize) * 1024 * 1024 * 1024;
          } else if (maxSize.endsWith("KB")) {
            allowed = file.size <= parseInt(maxSize) * 1024;
          }
          if (!allowed) {
            alert("File " + file.name + " is too large!");
            return;
          }
          const reader = new FileReader();
          reader.onload = (evt) => {
            const newVals = [...model.get("values")];
            const newNames = [...model.get("filenames")];
            newVals.push(Array.from(new Uint8Array(evt.target.result)));
            newNames.push(file.name);
            model.set("values", newVals);
            model.set("filenames", newNames);
            model.save_changes();
          };
          reader.readAsArrayBuffer(file);
        });
      }

      input.addEventListener("change", () => handleFiles(input.files));

      dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
      dropzone.addEventListener("dragleave", (e) => { e.preventDefault(); dropzone.classList.remove("dragover"); });
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        handleFiles(e.dataTransfer.files);
      });

      function updateList() {
        fileList.innerHTML = "";
        const files = model.get("filenames") || [];
        for (let i=0; i<files.length; ++i) {
          const li = document.createElement("li");
          li.classList.add("mljar-file-list-item");
          li.innerHTML = `<span class="mljar-file-icon">📄</span> <span class="mljar-file-name" title="${files[i]}">${files[i]}</span>`;
          const remove = document.createElement("button");
          remove.classList.add("mljar-file-remove-btn");
          remove.type = "button";
          remove.textContent = "×";
          remove.onclick = () => {
            const newVals = [...model.get("values")];
            const newNames = [...model.get("filenames")];
            newVals.splice(i,1);
            newNames.splice(i,1);
            model.set("values", newVals);
            model.set("filenames", newNames);
            model.save_changes();
          };
          li.appendChild(remove);
          fileList.appendChild(li);
        }
      }
      model.on("change:values", updateList);
      model.on("change:filenames", updateList);

      dropzone.appendChild(browseBtn);
      container.appendChild(label);
      container.appendChild(dropzone);
      container.appendChild(input);
      container.appendChild(fileList);
      el.appendChild(container);

      // ---- cell id
      const ID_ATTR = 'data-cell-id';
      const hostWithId = el.closest(`[${ID_ATTR}]`);
      const cellId = hostWithId ? hostWithId.getAttribute(ID_ATTR) : null;
      if (cellId) {
        model.set('cell_id', cellId);
        model.save_changes();
        model.send({ type: 'cell_id_detected', value: cellId });
      } else {
        const mo = new MutationObserver(() => {
          const host = el.closest(`[${ID_ATTR}]`);
          const newId = host?.getAttribute(ID_ATTR);
          if (newId) {
            model.set('cell_id', newId);
            model.save_changes();
            model.send({ type: 'cell_id_detected', value: newId });
            mo.disconnect();
          }
        });
        mo.observe(document.body, { attributes: true, subtree: true, attributeFilter: [ID_ATTR] });
      }

      // ---- styles: TWO states only (>=320px wide / <320px)
      const css = `
        .mljar-file-container {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          width: 100%;
          margin-bottom: 1em;
          container-type: inline-size;
        }

        .mljar-file-label { font-weight: 600; margin-bottom: 8px; }

        .mljar-file-input-hidden {
          position: absolute !important;
          left: -9999px !important;
          width: 1px !important; height: 1px !important;
          opacity: 0 !important; overflow: hidden !important;
          z-index: -1 !important;
        }

        .mljar-file-dropzone {
          border: 2px dashed #bbb;
          border-radius: 12px;
          padding: 18px;
          width: 100%;
          max-width: 100%;
          background: #fafbfc;
          position: relative;
          margin-bottom: 12px;
          transition: border-color 0.2s, background 0.2s;
          box-sizing: border-box;
          display: block;
          cursor: pointer;
        }
        .mljar-file-dropzone.dragover { border-color: #00b1e4; background: #e9f6fa; }
        .mljar-file-drop-hint { font-size: 0.93em; color: #666; margin-top: 3px; }

        .mljar-file-browse-btn {
          background: #fff; 
          """ + f"color: {THEME.get('primary_color', '#007bff')};" + """

          border: 2px solid """ + f"{THEME.get('primary_color', '#007bff')}" + """;
          border-radius: """ + f"{THEME.get('border_radius', '8px')}" + """ !important;
          padding: 6px 18px;
          font-size: 1.08em; font-weight: 600;
          cursor: pointer;
          margin-top: 12px;
          transition: background 0.2s, color 0.2s, border-color 0.2s;
          position: absolute; right: 18px; bottom: 18px;
        }
        .mljar-file-browse-btn:hover { background: """ + f"{THEME.get('primary_color', '#007bff')}" + """; color: #fff; }

        .mljar-file-list {
          list-style: none; margin: 0; padding: 0;
          width: 100%; max-width: 100%;
        }
        .mljar-file-list-item { display: flex; align-items: center; margin-bottom: 2px; font-size: 1.06em; }
        .mljar-file-icon { margin-right: 7px; }
        .mljar-file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: calc(100% - 42px); }
        .mljar-file-remove-btn { margin-left: 8px; background: none; border: none; color: #f44; font-size: 1.1em; cursor: pointer; font-weight: 700; }

        /* ======= Container queries: ONE breakpoint ======= */
        /* Narrow < 320px: stack button full width under text */
        @container (max-width: 320px) {
          .mljar-file-browse-btn {
            position: static !important;
            display: block;
            width: 100%;
            margin-top: 12px;
          }
        }
      `;
      const styleTag = document.createElement("style");
      styleTag.textContent = css;
      el.appendChild(styleTag);

      // Custom CSS hook
      const extraCSS = model.get("custom_css");
      if (extraCSS && extraCSS.trim().length > 0) {
        const extra = document.createElement("style");
        extra.textContent = extraCSS;
        el.appendChild(extra);
      }

      // ---- Fallback when container queries unsupported: mirror single breakpoint
      try {
        const supportsContainer = CSS && CSS.supports && CSS.supports("(container-type: inline-size)");
        if (!supportsContainer && typeof ResizeObserver !== "undefined") {
          const apply = () => {
            const w = container.clientWidth || 0;
            container.classList.toggle("cq-narrow", w <= 320);
          };
          const ro = new ResizeObserver(apply);
          ro.observe(container);
          apply();

          const fbCss = `
            .mljar-file-container.cq-narrow .mljar-file-browse-btn {
              position: static !important;
              display: block;
              width: 100%;
              margin-top: 12px;
            }
          `;
          const fb = document.createElement("style");
          fb.textContent = fbCss;
          el.appendChild(fb);
        }
      } catch {}

      updateList();
    }
    export default { render };
    """

    label = traitlets.Unicode("Choose a file").tag(sync=True)
    max_file_size = traitlets.Unicode("100MB").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)
    multiple = traitlets.Bool(False).tag(sync=True)
    key = traitlets.Unicode("").tag(sync=True)
    values = traitlets.List(traitlets.List(traitlets.Int())).tag(sync=True)
    filenames = traitlets.List(traitlets.Unicode()).tag(sync=True)
    custom_css = traitlets.Unicode(default_value="", help="Extra CSS to append to default styles").tag(sync=True)
    position = traitlets.Enum(["sidebar", "inline", "bottom"], default_value="sidebar").tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    @property
    def value(self):
        if self.values and self.values[0]:
            return bytes(self.values[0])
        return None

    @property
    def name(self):
        if self.filenames:
            return self.filenames[0]
        return None

    def __iter__(self):
        return (UploadedFile(name, value) for name, value in zip(self.filenames, self.values))

    @property
    def files(self):
        return [UploadedFile(name, value) for name, value in zip(self.filenames, self.values)]

    @property
    def values_bytes(self):
        return [bytes(val) for val in self.values]

    @property
    def names(self):
        return self.filenames.copy()

    @property
    def key_value(self):
        return self.key

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            mercury_mime = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position
            }
            data[0][MERCURY_MIMETYPE] = mercury_mime
        return data


def File(label="Choose a file", max_file_size="100MB", key="", disabled=False, hidden=False, multiple=False):
    code_uid = WidgetsManager.get_code_uid("File", key=key, kwargs=dict(label=label, max_file_size=max_file_size, multiple=multiple))
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached
    instance = FileWidget(
        label=label,
        max_file_size=max_file_size,
        disabled=disabled,
        hidden=hidden,
        multiple=multiple,
        key=key,
    )
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance
