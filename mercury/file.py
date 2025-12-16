# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


class UploadedFile:
    def __init__(self, name, value):
        self.name = name
        self.value = bytes(value)

    def __repr__(self):
        return f"UploadedFile(name={self.name!r}, value=<{len(self.value)} bytes>)"


def UploadFile(
    label: str = "Upload file",
    max_file_size: str = "100MB",
    multiple: bool = False,
    position: Position = "sidebar",
    disabled: bool = False,
    hidden: bool = False,
    key: str = "",
):
    """
    Create and display an UploadFile widget.

    This function instantiates an `UploadFileWidget` that lets the user upload
    one or more files (drag-and-drop or file picker). If a widget with the same
    configuration (identified by a unique code UID generated from widget type,
    arguments, and keyword arguments) already exists in the `WidgetsManager`,
    the existing instance is returned and displayed.

    Parameters
    ----------
    label : str
        Text displayed above the upload area.
        The default is `"Upload file"`.
    max_file_size : str
        Maximum allowed size per file. Supported suffixes: `"KB"`, `"MB"`, `"GB"`.
        Examples: `"500KB"`, `"10MB"`, `"1GB"`.
        The default is `"100MB"`.
    multiple : bool
        If `True`, the user can upload multiple files.
        The default is `False`.
    position : {"sidebar", "inline", "bottom"}, optional
        Controls where the widget is displayed:

        - `"sidebar"` — place the widget in the left sidebar panel (default).
        - `"inline"` — render the widget directly in the notebook flow.
        - `"bottom"` — render the widget after all notebook cells.
    disabled : bool, optional
        If `True`, the widget is visible but cannot be interacted with.
        The default is `False`.
    hidden : bool, optional
        If `True`, the widget exists in the UI state but is not rendered.
        The default is `False`.
    key : str, optional
        Unique identifier used to differentiate widgets with the same parameters.

    Returns
    -------
    UploadFileWidget
        The created or retrieved UploadFile widget instance.

    Examples
    --------
    Upload a single file:

    >>> import mercury as mr
    >>> up = mr.UploadFile(label="Upload CSV", max_file_size="10MB")
    >>> up.name
    'data.csv'
    >>> up.value  # bytes (first file)
    b'...'

    Upload multiple files:

    >>> up = mr.UploadFile(label="Upload images", multiple=True)
    >>> [f.name for f in up.files]
    ['a.png', 'b.png']

    Iterate over uploaded files:

    >>> for f in up:
    ...     print(f.name, len(f.value))
    """

    args = [label, max_file_size, multiple, position]
    kwargs = {
        "label": label,
        "max_file_size": max_file_size,
        "multiple": multiple,
        "position": position
    }

    code_uid = WidgetsManager.get_code_uid("UploadFile", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        display(cached)
        return cached

    instance = UploadFileWidget(**kwargs)
    WidgetsManager.add_widget(code_uid, instance)
    display(instance)
    return instance


class UploadFileWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      el.innerHTML = "";

      const container = document.createElement("div");
      container.classList.add("mljar-file-container");

      const labelEl = document.createElement("div");
      labelEl.classList.add("mljar-file-label");

      const input = document.createElement("input");
      input.type = "file";
      input.classList.add("mljar-file-input-hidden");
      const inputId = `mljar-file-${Math.random().toString(36).slice(2)}`;
      input.id = inputId;

      const dropzone = document.createElement("label");
      dropzone.classList.add("mljar-file-dropzone");
      dropzone.setAttribute("for", inputId);

      const dzText = document.createElement("div");
      dzText.textContent = "Drag and drop files here";

      const dzHint = document.createElement("div");
      dzHint.classList.add("mljar-file-drop-hint");

      const browseBtn = document.createElement("button");
      browseBtn.classList.add("mljar-file-browse-btn");
      browseBtn.type = "button";
      browseBtn.textContent = "Browse files";
      browseBtn.onclick = () => input.click();

      const fileList = document.createElement("ul");
      fileList.classList.add("mljar-file-list");

      dropzone.appendChild(dzText);
      dropzone.appendChild(dzHint);
      dropzone.appendChild(browseBtn);

      container.appendChild(labelEl);
      container.appendChild(dropzone);
      container.appendChild(input);
      container.appendChild(fileList);
      el.appendChild(container);

      function parseMaxSize(str) {
        if (!str || typeof str !== "string") return null;
        const s = str.trim();
        const num = parseInt(s, 10);
        if (!Number.isFinite(num) || num <= 0) return null;

        if (s.endsWith("KB")) return num * 1024;
        if (s.endsWith("MB")) return num * 1024 * 1024;
        if (s.endsWith("GB")) return num * 1024 * 1024 * 1024;
        return null;
      }

      function handleFiles(files) {
        const maxStr = model.get("max_file_size") || "100MB";
        const maxBytes = parseMaxSize(maxStr);

        Array.from(files || []).forEach(file => {
          if (maxBytes !== null && file.size > maxBytes) {
            alert(`File ${file.name} is too large! Limit ${maxStr} per file.`);
            return;
          }

          const reader = new FileReader();
          reader.onload = (evt) => {
            const newVals = [...(model.get("values") || [])];
            const newNames = [...(model.get("filenames") || [])];

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

      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });

      dropzone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });

      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        handleFiles(e.dataTransfer.files);
      });

      function updateList() {
        fileList.innerHTML = "";
        const files = model.get("filenames") || [];

        for (let i = 0; i < files.length; i++) {
          const li = document.createElement("li");
          li.classList.add("mljar-file-list-item");

          const icon = document.createElement("span");
          icon.classList.add("mljar-file-icon");
          icon.textContent = "📄";

          const name = document.createElement("span");
          name.classList.add("mljar-file-name");
          name.title = files[i];
          name.textContent = files[i];

          const remove = document.createElement("button");
          remove.classList.add("mljar-file-remove-btn");
          remove.type = "button";
          remove.textContent = "×";
          remove.onclick = () => {
            const newVals = [...(model.get("values") || [])];
            const newNames = [...(model.get("filenames") || [])];
            newVals.splice(i, 1);
            newNames.splice(i, 1);
            model.set("values", newVals);
            model.set("filenames", newNames);
            model.save_changes();
          };

          li.appendChild(icon);
          li.appendChild(name);
          li.appendChild(remove);
          fileList.appendChild(li);
        }
      }

      function syncFromModel() {
        labelEl.innerHTML = model.get("label") || "Upload file";
        dzHint.textContent = `Limit ${model.get("max_file_size") || "100MB"} per file`;

        const disabled = !!model.get("disabled");
        input.disabled = disabled;
        browseBtn.disabled = disabled;
        dropzone.classList.toggle("is-disabled", disabled);

        const multiple = !!model.get("multiple");
        input.multiple = multiple;

        const hidden = !!model.get("hidden");
        container.style.display = hidden ? "none" : "flex";
      }

      model.on("change:values", updateList);
      model.on("change:filenames", updateList);

      model.on("change:label", syncFromModel);
      model.on("change:max_file_size", syncFromModel);
      model.on("change:disabled", syncFromModel);
      model.on("change:hidden", syncFromModel);
      model.on("change:multiple", syncFromModel);

      syncFromModel();
      updateList();

      // ---- read cell id (no DOM modifications) ----
      /*
      const ID_ATTR = "data-cell-id";
      const hostWithId = el.closest(`[${ID_ATTR}]`);
      const cellId = hostWithId ? hostWithId.getAttribute(ID_ATTR) : null;

      if (cellId) {
        model.set("cell_id", cellId);
        model.save_changes();
        model.send({ type: "cell_id_detected", value: cellId });
      } else {
        const mo = new MutationObserver(() => {
          const host = el.closest(`[${ID_ATTR}]`);
          const newId = host?.getAttribute(ID_ATTR);
          if (newId) {
            model.set("cell_id", newId);
            model.save_changes();
            model.send({ type: "cell_id_detected", value: newId });
            mo.disconnect();
          }
        });
        mo.observe(document.body, { attributes: true, subtree: true, attributeFilter: [ID_ATTR] });
      }*/
    }
    export default { render };
    """

    _css = f"""
    .mljar-file-container {{
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      width: 100%;
      margin-bottom: 1em;
      padding-left: 4px;
      padding-right: 4px;
      box-sizing: border-box;
      container-type: inline-size;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      color: {THEME.get('text_color', '#222')};
    }}

    .mljar-file-label {{
      font-weight: 600;
      margin-bottom: 8px;
      font-size: {THEME.get('font_size', '14px')};
    }}

    .mljar-file-input-hidden {{
      position: absolute !important;
      left: -9999px !important;
      width: 1px !important;
      height: 1px !important;
      opacity: 0 !important;
      overflow: hidden !important;
      z-index: -1 !important;
    }}

    .mljar-file-dropzone {{
      border: 2px dashed {THEME.get('border_color', '#bbb')};
      border-radius: {THEME.get('border_radius', '12px')};
      padding: 18px;
      width: 100%;
      max-width: 100%;
      background: {THEME.get('panel_bg', '#fafbfc')};
      position: relative;
      margin-bottom: 12px;
      transition: border-color 0.2s, background 0.2s;
      box-sizing: border-box;
      display: block;
      cursor: pointer;
    }}

    .mljar-file-dropzone.dragover {{
      border-color: {THEME.get('primary_color', '#00b1e4')};
      background: {THEME.get('panel_bg_hover', '#e9f6fa')};
    }}

    .mljar-file-dropzone.is-disabled {{
      opacity: 0.65;
      cursor: not-allowed;
    }}

    .mljar-file-drop-hint {{
      font-size: 0.93em;
      color: #666;
      margin-top: 3px;
    }}

    .mljar-file-browse-btn {{
      background: #fff;
      color: {THEME.get('primary_color', '#007bff')};
      border: 2px solid {THEME.get('primary_color', '#007bff')};
      border-radius: {THEME.get('border_radius', '8px')};
      padding: 6px 18px;
      font-size: 1.08em;
      font-weight: 600;
      cursor: pointer;
      margin-top: 12px;
      transition: background 0.2s, color 0.2s, border-color 0.2s;
      position: absolute;
      right: 18px;
      bottom: 18px;
    }}

    .mljar-file-browse-btn:hover:not(:disabled) {{
      background: {THEME.get('primary_color', '#007bff')};
      color: #fff;
    }}

    .mljar-file-browse-btn:disabled {{
      cursor: not-allowed;
      opacity: 0.8;
    }}

    .mljar-file-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      width: 100%;
      max-width: 100%;
    }}

    .mljar-file-list-item {{
      display: flex;
      align-items: center;
      margin-bottom: 2px;
      font-size: 1.06em;
    }}

    .mljar-file-icon {{
      margin-right: 7px;
    }}

    .mljar-file-name {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: calc(100% - 42px);
    }}

    .mljar-file-remove-btn {{
      margin-left: 8px;
      background: none;
      border: none;
      color: #f44;
      font-size: 1.1em;
      cursor: pointer;
      font-weight: 700;
    }}

    @container (max-width: 320px) {{
      .mljar-file-browse-btn {{
        position: static !important;
        display: block;
        width: 100%;
        margin-top: 12px;
      }}
    }}
    """

    label = traitlets.Unicode("Upload file").tag(sync=True)
    max_file_size = traitlets.Unicode("100MB").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)
    multiple = traitlets.Bool(False).tag(sync=True)
    key = traitlets.Unicode("").tag(sync=True)

    values = traitlets.List(traitlets.List(traitlets.Int()), default_value=[]).tag(sync=True)
    filenames = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)

    position = traitlets.Enum(["sidebar", "inline", "bottom"], default_value="sidebar").tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)

    @property
    def value(self):
        if self.values:
            return bytes(self.values[0])
        return None

    @property
    def name(self):
        if self.filenames:
            return self.filenames[0]
        return None

    def __iter__(self):
        return iter(self.files)

    @property
    def files(self):
        return [UploadedFile(name, value) for name, value in zip(self.filenames, self.values)]

    @property
    def values_bytes(self):
        return [bytes(val) for val in self.values]

    @property
    def names(self):
        return self.filenames.copy()

    def _repr_mimebundle_(self, **kwargs):
        data = super()._repr_mimebundle_(**kwargs)
        if len(data) > 1:
            data[0][MERCURY_MIMETYPE] = {
                "widget": type(self).__qualname__,
                "model_id": self.model_id,
                "position": self.position,
            }
            if "text/plain" in data[0]:
                del data[0]["text/plain"]
        return data
