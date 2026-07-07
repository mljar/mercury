# Copyright MLJAR Sp. z o.o.
# Licensed under the Apache License, Version 2.0 (Apache-2.0)

from typing import Literal

import anywidget
import traitlets
from IPython.display import display

from .manager import MERCURY_MIMETYPE, WidgetsManager
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME

Position = Literal["sidebar", "inline", "bottom"]


_FILE_SIZE_UNITS = {
    "KB": 1024,
    "MB": 1024 * 1024,
    "GB": 1024 * 1024 * 1024,
}


def _normalize_max_file_size(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("UploadFile: `max_file_size` must be a string like '10MB'.")

    text = value.strip()
    if not text:
        raise ValueError("UploadFile: `max_file_size` must not be empty.")

    digits = ""
    unit = ""
    for char in text:
        if char.isdigit() and not unit:
            digits += char
        else:
            unit += char

    if not digits or not unit:
        raise ValueError(
            "UploadFile: `max_file_size` must include a positive number and unit."
        )

    size = int(digits)
    unit = unit.strip().upper()
    if size <= 0 or unit not in _FILE_SIZE_UNITS:
        raise ValueError(
            "UploadFile: `max_file_size` must use a positive size with KB, MB, or GB."
        )

    return f"{size}{unit}"


def _normalize_accept(value: str | list[str] | tuple[str, ...]) -> str:
    if value in ("", None):
        return ""

    if isinstance(value, str):
        candidates = value.split(",")
    elif isinstance(value, (list, tuple)):
        candidates = list(value)
    else:
        raise ValueError(
            "UploadFile: `accept` must be a string like '.csv' or a list of strings."
        )

    normalized: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, str):
            raise ValueError(
                "UploadFile: `accept` must contain only strings."
            )
        token = candidate.strip()
        if not token:
            raise ValueError(
                "UploadFile: `accept` must not contain empty entries."
            )
        normalized.append(token.lower())

    return ",".join(normalized)


def _accept_tokens(accept: str) -> list[str]:
    if not accept:
        return []
    return [token.strip().lower() for token in accept.split(",") if token.strip()]


def _matches_accept_token(filename: str, file_type: str, token: str) -> bool:
    lower_name = filename.lower()
    lower_type = file_type.lower()

    if token.startswith("."):
        return lower_name.endswith(token)
    if token.endswith("/*"):
        prefix = token[:-1]
        return lower_type.startswith(prefix)
    return lower_type == token


def _is_allowed_file(filename: str, accept: str, file_type: str = "") -> bool:
    tokens = _accept_tokens(accept)
    if not tokens:
        return True
    return any(_matches_accept_token(filename, file_type, token) for token in tokens)


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
    accept: str | list[str] = "",
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
    accept : str | list[str]
        Optional list of accepted file extensions or MIME types.
        Examples: ``".csv"``, ``[".csv", ".tsv"]``, ``"image/*"``.
        The default is empty, which allows all files.
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

    max_file_size = _normalize_max_file_size(max_file_size)
    accept = _normalize_accept(accept)

    args = [label, max_file_size, multiple, accept, position, disabled, hidden]
    kwargs = {
        "label": label,
        "max_file_size": max_file_size,
        "multiple": multiple,
        "accept": accept,
        "position": position,
        "disabled": disabled,
        "hidden": hidden,
    }

    code_uid = WidgetsManager.get_code_uid("UploadFile", key=key, args=args, kwargs=kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        display(cached)
        return cached

    instance = UploadFileWidget(**with_widget_render_metadata(kwargs))
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

      const dzAcceptHint = document.createElement("div");
      dzAcceptHint.classList.add("mljar-file-drop-hint");

      const browseBtn = document.createElement("button");
      browseBtn.classList.add("mljar-file-browse-btn");
      browseBtn.type = "button";
      browseBtn.textContent = "Browse files";
      browseBtn.onclick = () => input.click();

      const fileList = document.createElement("ul");
      fileList.classList.add("mljar-file-list");

      dropzone.appendChild(dzText);
      dropzone.appendChild(dzHint);
      dropzone.appendChild(dzAcceptHint);
      dropzone.appendChild(browseBtn);

      container.appendChild(labelEl);
      container.appendChild(dropzone);
      container.appendChild(input);
      container.appendChild(fileList);
      el.appendChild(container);

      let operationQueue = Promise.resolve();
      let localOperationRevision = model.get("revision") || 0;
      let operationInProgress = false;

      function parseMaxSize(str) {
        if (!str || typeof str !== "string") return null;
        const s = str.trim().toUpperCase();
        const num = parseInt(s, 10);
        if (!Number.isFinite(num) || num <= 0) return null;

        if (s.endsWith("KB")) return num * 1024;
        if (s.endsWith("MB")) return num * 1024 * 1024;
        if (s.endsWith("GB")) return num * 1024 * 1024 * 1024;
        return null;
      }

      function parseAccept(value) {
        if (!value || typeof value !== "string") return [];
        return value
          .split(",")
          .map(token => token.trim().toLowerCase())
          .filter(Boolean);
      }

      function isAllowedFile(file, accept) {
        const tokens = parseAccept(accept);
        if (!tokens.length) return true;
        const fileName = String(file?.name || "").toLowerCase();
        const fileType = String(file?.type || "").toLowerCase();

        return tokens.some(token => {
          if (token.startsWith(".")) {
            return fileName.endsWith(token);
          }
          if (token.endsWith("/*")) {
            const prefix = token.slice(0, -1);
            return fileType.startsWith(prefix);
          }
          return fileType === token;
        });
      }

      function setOperationState(isRunning) {
        operationInProgress = !!isRunning;
        const disabled = !!model.get("disabled") || operationInProgress;
        input.disabled = disabled;
        browseBtn.disabled = disabled;
        dropzone.classList.toggle("is-disabled", disabled);
      }

      function enqueueOperation(operation) {
        operationQueue = operationQueue
          .catch(() => {})
          .then(async () => {
            setOperationState(true);
            try {
              await operation();
            } finally {
              setOperationState(false);
            }
          });
        return operationQueue;
      }

      function readAcceptedFiles(files) {
        const maxStr = model.get("max_file_size") || "100MB";
        const accept = model.get("accept") || "";
        const maxBytes = parseMaxSize(maxStr);
        const multiple = !!model.get("multiple");
        const selectedFiles = Array.from(files || []);
        const acceptedFiles = multiple ? selectedFiles : selectedFiles.slice(0, 1);
        const readers = acceptedFiles.map(file => {
          if (!isAllowedFile(file, accept)) {
            alert(`File ${file.name} is not allowed. Accepted: ${accept}`);
            return null;
          }
          if (maxBytes !== null && file.size > maxBytes) {
            alert(`File ${file.name} is too large! Limit ${maxStr} per file.`);
            return null;
          }
          return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (evt) => {
              resolve({
                name: file.name,
                size: file.size,
                buffer: evt.target.result
              });
            };
            reader.onerror = () => reject(new Error(`Failed to read file ${file.name}`));
            reader.readAsArrayBuffer(file);
          });
        }).filter(Boolean);

        input.value = "";
        if (readers.length === 0) {
          return Promise.resolve([]);
        }
        return Promise.all(readers);
      }

      function handleFiles(files) {
        void readAcceptedFiles(files).then(readFiles => {
          if (!readFiles.length) {
            return;
          }
          return enqueueOperation(async () => {
            const multiple = !!model.get("multiple");
            const nextNames = multiple ? [...(model.get("filenames") || [])] : [];
            const nextSizes = multiple ? [...(model.get("file_sizes") || [])] : [];
            const uploadedNames = [];
            const uploadedSizes = [];
            const buffers = [];

            readFiles.forEach(file => {
              uploadedNames.push(file.name);
              uploadedSizes.push(file.size);
              buffers.push(file.buffer);
              nextNames.push(file.name);
              nextSizes.push(file.size);
            });

            // `revision` guarantees a widget state update even if a user
            // replaces a file with the same name/size as before.
            const nextRevision = Math.max(
              localOperationRevision,
              model.get("revision") || 0
            ) + 1;

            model.send(
              {
                event: "upload_files",
                uploaded_filenames: uploadedNames,
                uploaded_file_sizes: uploadedSizes,
                uploaded_file_types: readFiles.map(file => file.type || ""),
                replace: !multiple,
                revision: nextRevision
              },
              {},
              buffers
            );
            model.set("filenames", nextNames);
            model.set("file_sizes", nextSizes);
            model.set("revision", nextRevision);
            model.save_changes();
            localOperationRevision = nextRevision;
          });
        }).catch(error => {
          console.error(error);
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
            void enqueueOperation(async () => {
              const newNames = [...(model.get("filenames") || [])];
              const newSizes = [...(model.get("file_sizes") || [])];
              newNames.splice(i, 1);
              newSizes.splice(i, 1);
              // Removal also bumps `revision`, so Mercury auto-rerun
              // triggers even when the remaining filenames stay unchanged.
              const nextRevision = Math.max(
                localOperationRevision,
                model.get("revision") || 0
              ) + 1;
              model.send({
                event: "remove_file",
                index: i,
                filenames: newNames,
                file_sizes: newSizes,
                revision: nextRevision
              });
              model.set("filenames", newNames);
              model.set("file_sizes", newSizes);
              model.set("revision", nextRevision);
              model.save_changes();
              localOperationRevision = nextRevision;
            });
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
        const accept = model.get("accept") || "";
        dzAcceptHint.textContent = accept ? `Accepted types: ${accept}` : "";
        dzAcceptHint.style.display = accept ? "block" : "none";

        const multiple = !!model.get("multiple");
        input.multiple = multiple;
        input.accept = accept;
        localOperationRevision = Math.max(
          localOperationRevision,
          model.get("revision") || 0
        );
        setOperationState(operationInProgress);

        const hidden = !!model.get("hidden");
        container.style.display = hidden ? "none" : "flex";
      }

      model.on("change:filenames", updateList);
      model.on("change:file_sizes", updateList);

      model.on("change:label", syncFromModel);
      model.on("change:max_file_size", syncFromModel);
      model.on("change:accept", syncFromModel);
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
      padding-left: 4px;
      padding-right: 4px;
      box-sizing: border-box;
      container-type: inline-size;
      font-family: {THEME.get('font_family', 'Arial, sans-serif')};
      color: {THEME.get('text_color', '#222')};
    }}

    .mljar-file-label {{
      padding-top: 6px;
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
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
      background: {THEME.get('hover_background_color', '#e9f6fa')};
    }}

    .mljar-file-dropzone:focus-within {{
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
      background: {THEME.get('hover_background_color', THEME.get('panel_bg_hover', '#fafbfc'))};
    }}

    .mljar-file-dropzone.is-disabled {{
      opacity: 0.65;
      cursor: not-allowed;
    }}

    .mljar-file-drop-hint {{
      font-size: 0.93em;
      color: {THEME.get('muted_text_color', '#666')};
      margin-top: 3px;
    }}

    .mljar-file-browse-btn {{
      background: {THEME.get('widget_background_color', '#fff')};
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
      background: {THEME.get('hover_background_color', '#f8fafc')};
      color: {THEME.get('primary_color', '#007bff')};
    }}

    .mljar-file-browse-btn:active:not(:disabled) {{
      background: {THEME.get('selected_background_color', '#eef3ff')};
      color: {THEME.get('accent_color', THEME.get('primary_color', '#007bff'))};
    }}

    .mljar-file-browse-btn:focus-visible {{
      outline: none;
      border-color: {THEME.get('focus_border_color', THEME.get('accent_color', '#4c7cf0'))};
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
      color: {THEME.get('danger_color', '#f44')};
      font-size: 1.1em;
      cursor: pointer;
      font-weight: 700;
    }}

    .mljar-file-remove-btn:hover {{
      color: {THEME.get('danger_color', '#f44')};
      opacity: 0.9;
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
    accept = traitlets.Unicode("").tag(sync=True)
    disabled = traitlets.Bool(False).tag(sync=True)
    hidden = traitlets.Bool(False).tag(sync=True)
    multiple = traitlets.Bool(False).tag(sync=True)
    key = traitlets.Unicode("").tag(sync=True)

    filenames = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    file_sizes = traitlets.List(traitlets.Int(), default_value=[]).tag(sync=True)
    revision = traitlets.Int(0).tag(sync=True)

    position = traitlets.Enum(["sidebar", "inline", "bottom"], default_value="sidebar").tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_contents: list[bytes] = []
        self._last_operation_revision = 0
        self.on_msg(self._handle_file_message)

    def _handle_file_message(self, _widget, content, buffers):
        event = content.get("event")
        revision = int(content.get("revision", 0) or 0)

        if revision <= self._last_operation_revision:
            return

        self._last_operation_revision = revision

        if event == "upload_files":
            uploaded = [bytes(buffer) for buffer in (buffers or [])]
            uploaded_filenames = [
                str(name) for name in content.get("uploaded_filenames", [])
            ]
            uploaded_file_types = [
                str(file_type) for file_type in content.get("uploaded_file_types", [])
            ]
            replace = bool(content.get("replace", False))

            if len(uploaded_filenames) != len(uploaded):
                raise ValueError(
                    "UploadFile: uploaded filenames and buffers length mismatch."
                )
            if len(uploaded_file_types) != len(uploaded):
                raise ValueError(
                    "UploadFile: uploaded file types and buffers length mismatch."
                )
            for filename, file_type in zip(uploaded_filenames, uploaded_file_types):
                if not _is_allowed_file(filename, self.accept, file_type):
                    raise ValueError(
                        f"UploadFile: file {filename!r} is not allowed by accept={self.accept!r}."
                    )

            if replace:
                self._file_contents = uploaded
            else:
                self._file_contents.extend(uploaded)
            return

        if event == "remove_file":
            index = int(content.get("index", -1))
            if 0 <= index < len(self._file_contents):
                self._file_contents.pop(index)
            return

    @property
    def values(self):
        return [list(value) for value in self._file_contents]

    @values.setter
    def values(self, new_values):
        self._file_contents = [bytes(value) for value in (new_values or [])]
        self.file_sizes = [len(value) for value in self._file_contents]

    @property
    def value(self):
        if self._file_contents:
            return self._file_contents[0]
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
        return [
            UploadedFile(name, value)
            for name, value in zip(self.filenames, self._file_contents)
        ]

    @property
    def values_bytes(self):
        return list(self._file_contents)

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
