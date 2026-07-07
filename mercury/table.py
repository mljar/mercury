import anywidget
import traitlets
from IPython.display import display
import hashlib
import json
import math
from numbers import Real, Integral
from typing import Any, List, Dict
import datetime
from .manager import WidgetsManager, MERCURY_MIMETYPE
from .render_context import apply_widget_render_metadata, with_widget_render_metadata
from .theme import THEME


_CSS_SIZE_UNITS = ("px", "%", "vh", "vw", "rem", "em")


def _validate_css_size(value, name: str, *, allow_none: bool = False):
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.endswith(_CSS_SIZE_UNITS):
        allowed = "', '".join(_CSS_SIZE_UNITS)
        raise ValueError(
            f"Table: `{name}` must be a string ending with '{allowed}', "
            f"e.g. '400px', '80%', or '50vh'"
        )
    return value


def _json_safe_table_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()

    if isinstance(value, bool):
        return bool(value)

    if isinstance(value, Integral):
        return int(value)

    if isinstance(value, Real):
        try:
            if math.isnan(value) or math.isinf(value):
                return None
        except TypeError:
            pass
        return float(value) if isinstance(value, float) else value

    try:
        if value != value:
            return None
    except Exception:
        pass

    if isinstance(value, dict):
        return {str(k): _json_safe_table_value(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe_table_value(v) for v in value]

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _table_data_payload(data: Any) -> Any:
    if data is None:
        return None

    to_dicts = getattr(data, "to_dicts", None)
    if callable(to_dicts):
        columns = getattr(data, "columns", None)
        return {
            "type": "polars",
            "columns": _json_safe_table_value(list(columns) if columns is not None else []),
            "records": _json_safe_table_value(to_dicts()),
        }

    to_dict = getattr(data, "to_dict", None)
    if callable(to_dict):
        try:
            records = to_dict(orient="records")
        except TypeError:
            records = to_dict()
        columns = getattr(data, "columns", None)
        index = getattr(data, "index", None)
        index_values = list(index) if index is not None else []
        return {
            "type": "pandas",
            "columns": _json_safe_table_value(list(columns) if columns is not None else []),
            "index": _json_safe_table_value(index_values),
            "records": _json_safe_table_value(records),
        }

    return {
        "type": type(data).__name__,
        "records": _json_safe_table_value(data),
    }


def _table_data_hash(data: Any) -> str:
    payload = _table_data_payload(data)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:12]


def Table(
    data,
    page_size: int = 50,
    search: bool = False,
    select_rows: bool = False,
    width: str = "100%",
    height: str | None = None,
    position: str = "inline",
    show_index_col: bool = False,
    display_now: bool = True,
    key: str = "",
):
    # validation
    try:
        page_size_int = int(page_size)
    except Exception:
        raise Exception("Table: `page_size` must be integer")

    width = _validate_css_size(width, "width")
    height = _validate_css_size(height, "height", allow_none=True)

    widget_kwargs = {
        "data": data,
        "page_size": page_size_int,
        "search": search,
        "select_rows": select_rows,
        "width": width,
        "height": height,
        "show_index_col": show_index_col,
        "position": position,
    }
    uid_kwargs = {
        "data_hash": _table_data_hash(data),
        "page_size": page_size_int,
        "search": search,
        "select_rows": select_rows,
        "width": width,
        "height": height,
        "show_index_col": show_index_col,
        "position": position,
    }
    code_uid = WidgetsManager.get_code_uid("Table", key=key, kwargs=uid_kwargs)
    cached = WidgetsManager.get_widget(code_uid)
    if cached:
        apply_widget_render_metadata(cached)
        if display_now:
            display(cached)
        return cached

    instance = TableWidget(**with_widget_render_metadata(widget_kwargs))
    WidgetsManager.add_widget(code_uid, instance)
    if display_now:
        display(instance)
    return instance


# new data trait declaration
class DataFrameTrait(traitlets.TraitType):
    """Trait that accepts tabular data and converts it into a JSON-safe list of dicts.
    Accepted input types:
      - pandas.DataFrame
      - polars.DataFrame
      - list[dict]
      - dict of lists
      - dict of dicts
    """

    default_value: list = []
    info_text = "pandas.DataFrame, polars.DataFrame, list[dict], or dict"

    def to_json_safe(self, val: Any) -> Any:
        """Convert a single value to something JSON-serializable."""
        if val is None:
            return None

        # dates / datetimes -> ISO string
        try:
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
        except Exception:
            pass

        # Simple scalars
        if isinstance(val, bool):
            return bool(val)

        if isinstance(val, Integral):
            return int(val)

        if isinstance(val, Real):
            # NaN / Inf -> None
            try:
                if math.isnan(val) or math.isinf(val):
                    return None
            except TypeError:
                pass
            return float(val) if isinstance(val, float) else val

        # Generic NaN-like
        try:
            if val != val:  # NaN != NaN
                return None
        except Exception:
            pass

        # Dict -> sanitize values
        if isinstance(val, dict):
            return {str(k): self.to_json_safe(v) for k, v in val.items()}

        # List / tuple -> sanitize each element
        if isinstance(val, (list, tuple)):
            return [self.to_json_safe(v) for v in val]

        # Fallback: return as-is (JSON will handle strings etc.)
        return val

    def _from_list_of_dicts(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize list[dict] input."""
        if not records:
            return []
        if not all(isinstance(rec, dict) for rec in records):
            raise traitlets.TraitError("List input must contain only dict rows.")
        return [{k: self.to_json_safe(v) for k, v in rec.items()} for rec in records]

    def _from_dict(self, value: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize dict input into list[dict].

        Supported shapes:
          - column-wise: {col: [v1, v2, ...]}
          - row-wise:    {row_key: {col: val, ...}}
          - single row:  {col: val, ...}
        """
        if not value:
            return []

        vals = list(value.values())

        # Case 1: column-wise dict: {col: [..], col2: [..]}
        if all(isinstance(v, (list, tuple)) for v in vals):
            lengths = {len(v) for v in vals}
            if len(lengths) != 1:
                raise traitlets.TraitError(
                    "All column lists in dict must have the same length."
                )
            n = next(iter(lengths))
            keys = list(value.keys())
            out: List[Dict[str, Any]] = []
            for i in range(n):
                row = {k: self.to_json_safe(value[k][i]) for k in keys}
                out.append(row)
            return out

        # Case 2: row-wise dict: {id1: {col: val}, id2: {...}}
        if all(isinstance(v, dict) for v in vals):
            return [{k: self.to_json_safe(v) for k, v in row.items()} for row in vals]

        # Case 3: treat as a single row
        return [{k: self.to_json_safe(v) for k, v in value.items()}]

    def _from_pandas_like(self, value: Any) -> List[Dict[str, Any]]:
        """Handle pandas-like objects via .to_dict()."""
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            # Try orient="records" first
            try:
                records = to_dict(orient="records")
                if isinstance(records, list):
                    return self._from_list_of_dicts(records)
            except TypeError:
                # Fallback: assume column-wise dict
                d = to_dict()
                if isinstance(d, dict):
                    return self._from_dict(d)
        raise traitlets.TraitError(
            "Object with .to_dict is not a supported DataFrame-like value."
        )

    def _from_polars_like(self, value: Any) -> List[Dict[str, Any]]:
        """Handle polars-like objects via .to_dicts()."""
        to_dicts = getattr(value, "to_dicts", None)
        if callable(to_dicts):
            records = to_dicts()
            if isinstance(records, list):
                return self._from_list_of_dicts(records)
        raise traitlets.TraitError(
            "Object with .to_dicts is not a supported Polars-like DataFrame."
        )

    def validate(self, obj, value):
        """Main entry point: normalize many possible input types to list[dict]."""
        # No data / default
        if value is None or value is traitlets.Undefined:
            return []

        # list[dict]
        if isinstance(value, list):
            return self._from_list_of_dicts(value)

        # dict
        if isinstance(value, dict):
            return self._from_dict(value)

        # polars DataFrame
        if hasattr(value, "to_dicts"):
            return self._from_polars_like(value)

        # pandas DataFrame
        if hasattr(value, "to_dict"):
            return self._from_pandas_like(value)

        self.error(obj, value)

    def error(self, obj, value):
        raise traitlets.TraitError(
            f"The '{self.name}' trait expected DataFrame-like, list[dict], or dict, not {value!r}"
        )


class TableWidget(anywidget.AnyWidget):
    _esm = """
function render({ model, el }) {
  const c = (tag, props = {}) =>
    Object.assign(document.createElement(tag), props);
  const syncEllipsisTitle = cell => {
    const text = cell.textContent || '';
    if (!text) {
      cell.removeAttribute('title');
      return;
    }
    if (cell.scrollWidth > cell.clientWidth) {
      cell.title = text;
    } else {
      cell.removeAttribute('title');
    }
  };

  let data = model.get('data') || [];
  let page = model.get('table_page');
  const pageSize = model.get('page_size');
  const showIndexCol = model.get('show_index_col');
  const indexLabel = showIndexCol
    ? model.get('_oryginal_index_column_name') || 'Index'
    : '';

  let isLoading = false;
  let searchTimeout = null;
  let fixedTableHeight = null;
  let lastKnownColumns = null;
  const MERCURY_INDEX_NAME = 'mercury_table_row_index';

  const container = c('div', { className: 'mljar-mercury-table-widget-table-container' });
  el.appendChild(container);

  const wrap = c('div', { className: 'mljar-mercury-table-widget-table-wrapper' });
  const table = c('table', { className: 'mljar-mercury-table-widget-tbl' });
  container.appendChild(wrap);
  wrap.appendChild(table);

  const controls = c('div', { className: 'mljar-mercury-table-widget-table-controls' });
  const controlsLeft = c('div', { className: 'mljar-mercury-table-widget-controls-left' });
  const controlsRight = c('div', { className: 'mljar-mercury-table-widget-controls-right' });
  controls.appendChild(controlsLeft);
  controls.appendChild(controlsRight);
  el.appendChild(controls);

  let searchBox = null;

  function applyLoadingState() {
    if (isLoading) {
      container.classList.add('loading');
    } else {
      container.classList.remove('loading');
    }
  }

  const rowsSelectionEnabled = () => model.get('select_rows');

  const rowsEqual = (a, b) => {
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) return false;
    for (const k of aKeys) {
      if (a[k] !== b[k]) return false;
    }
    return true;
  };

  const isRowSelected = row => {
    const selected = model.get('_id_selected_rows') || [];
    return selected.some(r => rowsEqual(r, row));
  };

  function removeIndex(data) {
    if (!Array.isArray(data)) return [];

    return data.map(row =>
      row && typeof row === 'object'
        ? (({ [MERCURY_INDEX_NAME]: _, ...rest }) => rest)(row)
        : row
    );
  }

  function renameIndex(data) {
    if (!Array.isArray(data)) return [];

    return data.map(row =>
      row && typeof row === 'object'
        ? (({ [MERCURY_INDEX_NAME]: idx, ...rest }) => ({
            [indexLabel]: idx,
            ...rest
          }))(row)
        : row
    );
  }

  function toggleRowSelection(row, checked, tr) {
    const current = model.get('_id_selected_rows') || [];
    const id = row[MERCURY_INDEX_NAME];
    let next;

    if (checked) {
      next = current.concat([row]);
      tr.classList.add('mljar-mercury-table-widget-row-selected');
    } else {
      next = current.filter(r => r[MERCURY_INDEX_NAME] !== id);
      tr.classList.remove('mljar-mercury-table-widget-row-selected');
    }

    model.set('_id_selected_rows', next);
    model.set(
      'selected_rows',
      showIndexCol ? renameIndex(next) : removeIndex(next)
    );
    model.save_changes();
  }

  function renderTable() {
    const hasData = data.length > 0;
    const hiddenCols = showIndexCol ? new Set() : new Set([MERCURY_INDEX_NAME]);
    const selectionEnabled = rowsSelectionEnabled();

    let cols = [];

    if (hasData) {
      cols = Object.keys(data[0]).filter(c => !hiddenCols.has(c));
      lastKnownColumns = [...cols];
    } else if (lastKnownColumns) {
      cols = lastKnownColumns;
    }
    
    const existingOverlay = container.querySelector(
      '.mljar-mercury-table-widget-no-data-overlay'
    );
    if (existingOverlay) {
      existingOverlay.remove();
    }

    table.innerHTML = '';
    table.classList.toggle('has-row-selection', selectionEnabled);

    const w = model.get('width');
    const h = model.get('height');
    if (w) {
      wrap.style.width = w;
      controls.style.width = w;
    }
    if (h) {
      wrap.style.height = h;
      wrap.style.maxHeight = h;
    }

        
    if (cols.length > 0) {
      const thead = table.appendChild(c('thead'));
      const trh = thead.appendChild(c('tr'));

      if (selectionEnabled) {
        trh.appendChild(c('th', { textContent: '' }));
      }

      const sCol = model.get('table_sort_column');
      const sDir = model.get('table_sort_direction');

      cols.forEach(col => {
        const isIndexCol = col === MERCURY_INDEX_NAME;
        const label = isIndexCol ? indexLabel : col;
        const th = c('th', { textContent: label });

        if (sCol === col && sDir === 1) th.textContent += ' ▲';
        if (sCol === col && sDir === 2) th.textContent += ' ▼';

        th.onclick = () => {
          let dir = 1;
          if (sCol === col) dir = (sDir + 1) % 3;

          model.set('table_sort_column', col);
          model.set('table_sort_direction', dir);
          model.set('table_page', 1);
          model.save_changes();
        };

        trh.appendChild(th);
        requestAnimationFrame(() => syncEllipsisTitle(th));
      });
    }

    const tbody = table.appendChild(c('tbody'));

    if (hasData) {
      data.forEach(row => {
        const tr = tbody.appendChild(c('tr'));

        const selected = selectionEnabled && isRowSelected(row);
        if (selected) tr.classList.add('mljar-mercury-table-widget-row-selected');

        if (selectionEnabled) {
          const tdSelect = c('td');
          const checkbox = c('input', { type: 'checkbox' });
          checkbox.checked = selected;
          checkbox.onchange = () =>
            toggleRowSelection(row, checkbox.checked, tr);
          tdSelect.appendChild(checkbox);
          tr.appendChild(tdSelect);
        }

        cols.forEach(col => {
          const td = c('td', { textContent: row[col] });
          tr.appendChild(td);
          requestAnimationFrame(() => syncEllipsisTitle(td));
        });
      });
    }

    if (!hasData) {
      const overlay = c('div', {
        className: 'mljar-mercury-table-widget-no-data-overlay',
        textContent: 'No data found'
      });
      const thead = table.querySelector('thead');
      if (thead) {
        const h = thead.getBoundingClientRect().height;
        overlay.style.top = `${h}px`;
      }
      wrap.appendChild(overlay);
    }

    if (h) {
      fixedTableHeight = null;
    } else if (fixedTableHeight === null) {
      requestAnimationFrame(() => {
        const h = wrap.getBoundingClientRect().height;
        if (h > 0) {
          fixedTableHeight = h;
          wrap.style.height = `${fixedTableHeight}px`;
        }
      });
    } else {
      wrap.style.height = `${fixedTableHeight}px`;
    }
  }

  function renderPager() {
    controlsLeft.innerHTML = '';

    let filteredLength = model.get('_filtered_length');
    if (!filteredLength && data) {
      filteredLength = data.length;
    }
    filteredLength = filteredLength || 0;

    const searchActive = model.get('search');

    if (!searchActive && (filteredLength === 0 || filteredLength <= pageSize)) {
      return;
    }

    const total = Math.max(1, Math.ceil(filteredLength / pageSize));

    // pagination on the left
    if (filteredLength > pageSize) {
      const prev = c('button', {
        textContent: 'Previous',
        disabled: page <= 1,
        className: 'mljar-mercury-table-widget-mljar-mercury-table-widget-pager-btn'
      });
      prev.onclick = () => {
        model.set('table_page', page - 1);
        model.save_changes();
      };

      const pageInput = c('input', {
        type: 'number',
        min: 1,
        max: total,
        value: String(page),
        className: 'mljar-mercury-table-widget-page-input'
      });

      const goToPageFromInput = () => {
        let val = parseInt(pageInput.value, 10);

        if (isNaN(val)) {
          pageInput.value = String(page);
          return;
        }

        if (val < 1) val = 1;
        if (val > total) val = total;

        model.set('table_page', val);
        model.save_changes();
      };

      pageInput.onchange = goToPageFromInput;
      pageInput.onkeydown = e => {
        if (e.key === 'Enter') {
          e.preventDefault();
          goToPageFromInput();
        }
      };

      const ofLabel = c('span', {
        textContent: ` / ${total}`,
        className: 'mljar-mercury-table-widget-page-of'
      });

      const next = c('button', {
        textContent: 'Next',
        disabled: page >= total,
        className: 'mljar-mercury-table-widget-mljar-mercury-table-widget-pager-btn'
      });
      next.onclick = () => {
        model.set('table_page', page + 1);
        model.save_changes();
      };

      controlsLeft.appendChild(prev);
      controlsLeft.appendChild(pageInput);
      controlsLeft.appendChild(ofLabel);
      controlsLeft.appendChild(next);
    }

    // search input on the right
    if (searchActive) {
      if (!searchBox) {
        searchBox = c('input', {
          type: 'text',
          placeholder: 'Search...',
          className: 'mljar-mercury-table-widget-search-box'
        });

        searchBox.oninput = () => {
          const value = searchBox.value;

          isLoading = true;
          applyLoadingState();

          clearTimeout(searchTimeout);
          searchTimeout = setTimeout(() => {
            model.set('table_search_query', value);
            model.set('table_page', 1);
            model.save_changes();
          }, 250);
        };

        controlsRight.appendChild(searchBox);
      }

      // keep input element, only update its value (focus is preserved)
      const currentQuery = model.get('table_search_query') || '';
      if (searchBox.value !== currentQuery) {
        searchBox.value = currentQuery;
      }
      searchBox.style.display = '';
    } else {
      // hide search input when search is disabled
      if (searchBox) {
        searchBox.style.display = 'none';
      }
    }
  }

  const rerender = () => {
    data = model.get('data') || [];
    page = model.get('table_page');
    renderTable();
    renderPager();

    isLoading = false;
    applyLoadingState();
  };

  model.on('change:data', rerender);
  model.on('change:table_sort_column', rerender);
  model.on('change:table_sort_direction', rerender);
  model.on('change:table_page', rerender);
  model.on('change:_filtered_length', rerender);
  model.on('change:search_version', rerender);
  model.on('change:height', rerender);
  rerender();

}
export default { render };
"""

    _css = """
.mljar-mercury-table-widget-table-controls {
  display: flex;
  justify-content: space-between;
  padding: 10px 0px 0px 0px;
  align-items: center;
  gap: 16px;
  font-family: %(font_family)s;
  font-size: %(font_size)s;
  color: %(text_color)s;
}

.mljar-mercury-table-widget-controls-left,
.mljar-mercury-table-widget-controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mljar-mercury-table-widget-mljar-mercury-table-widget-pager-btn {
  padding: 4px 10px;
  border-radius: %(border_radius_sm)s;
  border: 1px solid %(border_color)s;
  background: %(widget_background_color)s;
  color: %(text_color)s;
  cursor: pointer;
  transition:
    background-color 0.16s ease,
    border-color 0.16s ease,
    color 0.16s ease;
}

.mljar-mercury-table-widget-mljar-mercury-table-widget-pager-btn:hover:not(:disabled) {
  background: %(hover_background_color)s;
  border-color: %(focus_border_color)s;
}

.mljar-mercury-table-widget-mljar-mercury-table-widget-pager-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.mljar-mercury-table-widget-page-of {
  margin: 0 4px;
}

.mljar-mercury-table-widget-table-wrapper {
  max-height: 480px;
  overflow-y: auto;
  overflow-x: auto;
  display: block;
  box-sizing: border-box;
  background: %(widget_background_color)s;
  scrollbar-width: thin;
  scrollbar-color: %(muted_text_color)s %(panel_bg_hover)s;
}

.mljar-mercury-table-widget-table-wrapper::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.mljar-mercury-table-widget-table-wrapper::-webkit-scrollbar-track {
  background: %(panel_bg_hover)s;
  border-radius: 8px;
}

.mljar-mercury-table-widget-table-wrapper::-webkit-scrollbar-thumb {
  background: %(muted_text_color)s;
  border-radius: 8px;
  border: 2px solid %(panel_bg_hover)s;
}

.mljar-mercury-table-widget-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: %(accent_color)s;
}

.mljar-mercury-table-widget-tbl {
  border-collapse: collapse;
  table-layout: auto;
  font-family: %(font_family)s;
  font-size: %(font_size)s;
  color: %(text_color)s;
  background: %(widget_background_color)s;
  width: max-content;
  min-width: 100%%;
}

.mljar-mercury-table-widget-tbl th,
.mljar-mercury-table-widget-tbl td {
  border: 1px solid %(border_color)s;
  padding: 8px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 160px;
  max-width: 200px;
}

.mljar-mercury-table-widget-tbl th {
  background: %(panel_bg_hover)s;
  color: %(text_color)s;
  cursor: pointer;
  text-align: center;
  font-family: %(heading_font_family)s;
  font-weight: 700;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.mljar-mercury-table-widget-tbl th:hover {
  background: %(hover_background_color)s;
}

.mljar-mercury-table-widget-tbl th:active {
  background: %(selected_background_color)s;
  color: %(accent_color)s;
}

.mljar-mercury-table-widget-tbl tbody tr:nth-child(even) td {
  background: %(panel_bg)s;
}

.mljar-mercury-table-widget-tbl tbody tr:nth-child(odd) td {
  background: %(widget_background_color)s;
}

.mljar-mercury-table-widget-tbl tbody tr:hover td {
  background: %(hover_background_color)s;
}

.mljar-mercury-table-widget-pager {
  margin-top: 8px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.mljar-mercury-table-widget-page-input {
  width: 56px;
  text-align: center;
  padding: 4px 6px;
  font-family: %(font_family)s;
  font-size: %(font_size)s;
  color: %(text_color)s;
  background: %(widget_background_color)s;
  border: 1px solid %(border_color)s;
  border-radius: %(border_radius_sm)s;
  -moz-appearance: textfield;
}
.mljar-mercury-table-widget-page-input::-webkit-outer-spin-button,
.mljar-mercury-table-widget-page-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.mljar-mercury-table-widget-search-box {
  padding: 6px 8px;
  width: 200px;
  font-family: %(font_family)s;
  font-size: %(font_size)s;
  color: %(text_color)s;
  background: %(widget_background_color)s;
  border: 1px solid %(border_color)s;
  border-radius: %(border_radius)s;
}

.mljar-mercury-table-widget-search-box::placeholder {
  color: %(muted_text_color)s;
}

.mljar-mercury-table-widget-page-input:focus,
.mljar-mercury-table-widget-search-box:focus {
  outline: none;
  border-color: %(focus_border_color)s;
  box-shadow: none;
}

.mljar-mercury-table-widget-table-container {
  position: relative;
  min-height: 40px;
}

.mljar-mercury-table-widget-table-container.loading .mljar-mercury-table-widget-table-wrapper {
  filter: blur(2px);
  pointer-events: none;
}

.mljar-mercury-table-widget-table-container.loading::after {
  content: '';
  position: absolute;
  top: 50%%;
  left: 50%%;
  width: 40px;
  height: 40px;
  border-radius: 50%%;
  border: 4px solid %(border_color)s;
  border-top-color: %(accent_color)s;
  transform: translate(-50%%, -50%%);
  animation: spin 0.8s linear infinite;
  z-index: 10;
}

@keyframes spin {
  from {
    transform: translate(-50%%, -50%%) rotate(0deg);
  }
  to {
    transform: translate(-50%%, -50%%) rotate(360deg);
  }
}

.mljar-mercury-table-widget-row-selected {
  background-color: %(selected_background_color)s;
}

.mljar-mercury-table-widget-tbl.has-row-selection td:first-child,
.mljar-mercury-table-widget-tbl.has-row-selection th:first-child {
  width: 32px;
  min-width: 32px;
  max-width: 32px;
  text-align: center;
}

.mljar-mercury-table-widget-table-wrapper.no-data-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.mljar-mercury-table-widget-no-data-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: %(font_family)s;
  font-size: 20px;
  font-weight: bold;
  color: %(muted_text_color)s;
  background: %(widget_background_color)s;
  pointer-events: none;
}
""" % {
        "font_family": THEME.get("font_family"),
        "heading_font_family": THEME.get("heading_font_family", THEME.get("font_family")),
        "font_size": THEME.get("font_size"),
        "text_color": THEME.get("text_color"),
        "muted_text_color": THEME.get("muted_text_color"),
        "border_color": THEME.get("border_color"),
        "border_radius": THEME.get("border_radius", "6px"),
        "border_radius_sm": THEME.get("border_radius_sm", "4px"),
        "widget_background_color": THEME.get("widget_background_color"),
        "panel_bg": THEME.get("panel_bg"),
        "panel_bg_hover": THEME.get("panel_bg_hover", THEME.get("panel_bg")),
        "hover_background_color": THEME.get("hover_background_color"),
        "selected_background_color": THEME.get("selected_background_color"),
        "focus_border_color": THEME.get("focus_border_color", THEME.get("accent_color")),
        "accent_color": THEME.get("accent_color", THEME.get("primary_color")),
    }

    # --- backend flags / storage ---

    # whether we use DataFrame backend or list[dict]
    _use_frame_backend: bool = False
    _frame_lib: str | None = None  # "pandas" or "polars"

    # backend: DataFrame
    _full_df = None
    _filtered_df = None
    _sorted_df = None

    # backend: list[dict]
    _full_data: list[dict] | None = None
    _filtered_data: list[dict] | None = None
    _sorted_data: list[dict] | None = None
    _mercury_index_column_name = "mercury_table_row_index"

    # traits synced to JS
    data = DataFrameTrait().tag(sync=True)
    page_size = traitlets.Int(50).tag(sync=True)
    search = traitlets.Bool(False).tag(sync=True)
    select_rows = traitlets.Bool(False).tag(sync=True)
    width = traitlets.Unicode("100%").tag(sync=True)
    height = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    show_index_col = traitlets.Bool(False).tag(sync=True)
    position = traitlets.Enum(
        values=["sidebar", "inline", "bottom"],
        default_value="inline",
        help="Widget placement: sidebar, inline, or bottom",
    ).tag(sync=True)

    table_search_query = traitlets.Unicode("").tag(sync=True)
    table_page = traitlets.Int(1).tag(sync=True)
    table_sort_column = traitlets.Unicode("").tag(sync=True)
    table_sort_direction = traitlets.Int(0).tag(sync=True)  # 0 none, 1 asc, 2 desc
    _filtered_length = traitlets.Int(0).tag(sync=True)
    search_version = traitlets.Int(0).tag(sync=True)
    _id_selected_rows = DataFrameTrait().tag(sync=True)
    selected_rows = DataFrameTrait().tag(sync=True)
    _oryginal_index_column_name = traitlets.Unicode("").tag(sync=True)
    cell_id = traitlets.Unicode(allow_none=True).tag(sync=True)
    source_cell_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    render_slot_id = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    layout_path = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

    # -------- event router --------

    def _react(self, change):
        if self._full_df is None and not self._full_data:
            self.data = []
            self._filtered_length = 0
            return

        name = change["name"]

        if name == "table_search_query":
            self.table_page = 1
            self._handle_refresh(("filter", "sort", "paginate"))
            self.search_version += 1

        elif name in ("table_sort_column", "table_sort_direction"):
            self.table_page = 1
            self._handle_refresh(("sort", "paginate"))

        elif name in ("table_page", "table_page_size"):
            self._handle_refresh(("paginate"))

        else:
            self._handle_refresh(("filter", "sort", "paginate"))

    # -------- dispatcher: frame vs list --------

    def _handle_refresh(self, steps=("filter", "sort", "paginate")):
        if "filter" in steps:
            self._apply_filter()
        if "sort" in steps:
            self._apply_sort()
        if "paginate" in steps:
            self._paginate()

    def _apply_filter(self):
        if self._use_frame_backend:
            self._apply_filter_frame()
        else:
            self._apply_filter_list()

    def _apply_sort(self):
        if self._use_frame_backend:
            self._apply_sort_frame()
        else:
            self._apply_sort_list()

    def _paginate(self):
        if self._use_frame_backend:
            self._paginate_frame()
        else:
            self._paginate_list()

    # -------- filtering: list backend --------

    def _apply_filter_list(self):
        records = self._full_data or []
        q = (self.table_search_query or "").strip().lower()

        if not q:
            self._filtered_data = records
        else:
            out = []
            for row in records:
                for k, v in row.items():
                    if not self.show_index_col and k == self._mercury_index_column_name:
                        continue
                    if q in str(v).lower():
                        out.append(row)
                        break
            self._filtered_data = out

        self._filtered_length = len(self._filtered_data or [])

    # -------- sorting: list backend --------

    def _apply_sort_list(self):
        records = self._filtered_data or []
        col = self.table_sort_column
        direction = self.table_sort_direction

        if not col or direction == 0:
            self._sorted_data = records
            return

        reverse = direction == 2

        def sort_key(row: dict):
            v = row.get(col)
            return (v is None, v)

        try:
            self._sorted_data = sorted(records, key=sort_key, reverse=reverse)
        except TypeError:
            self._sorted_data = sorted(
                records,
                key=lambda r: (r.get(col) is None, str(r.get(col))),
                reverse=reverse,
            )

    # -------- pagination: list backend --------

    def _paginate_list(self):
        records = self._sorted_data or []

        if not records:
            self.data = []
            return

        size = max(int(self.page_size), 1)
        total = len(records)
        max_page = max((total - 1) // size + 1, 1)

        page = max(int(self.table_page), 1)
        if page > max_page:
            page = max_page
            self.table_page = page

        start = (page - 1) * size
        end = start + size

        page_records = records[start:end]
        self.data = page_records

    # -------- filtering: DataFrame backend --------

    def _apply_filter_frame(self):
        df = self._full_df
        if df is None:
            self._filtered_df = None
            self._filtered_length = 0
            return

        q = (self.table_search_query or "").strip()
        if not q:
            self._filtered_df = df
            self._filtered_length = (
                getattr(df, "shape", (0,))[0]
                if self._frame_lib == "pandas"
                else df.height
            )
            return

        if self._frame_lib == "pandas":
            import pandas as pd

            # search_df = df.drop(columns=[self._mercury_index_column_name], errors="ignore")
            search_df = (
                df
                if self.show_index_col
                else df.drop(columns=[self._mercury_index_column_name], errors="ignore")
            )
            bool_df = search_df.astype(str).apply(
                lambda col: col.str.contains(q, case=False, na=False)
            )
            mask = bool_df.any(axis=1)
            self._filtered_df = df[mask]
            self._filtered_length = int(mask.sum())
        elif self._frame_lib == "polars":
            import polars as pl

            q_lower = q.lower()
            # search_df = df.drop(self._mercury_index_column_name, strict=False)
            search_df = (
                df
                if self.show_index_col
                else df.drop(self._mercury_index_column_name, strict=False)
            )
            tmp = search_df.select(pl.all().cast(pl.Utf8).str.to_lowercase())
            mask = tmp.select(
                pl.any_horizontal(pl.all().str.contains(q_lower, literal=True))
            ).to_series()
            self._filtered_df = df.filter(mask)
            self._filtered_length = self._filtered_df.height
        else:
            # fallback: convert to list backend
            trait = DataFrameTrait()
            rows = trait.validate(self, df)
            for i, row in enumerate(rows):
                rows[i] = {self._mercury_index_column_name: i, **row}
            self._full_data = rows
            self._use_frame_backend = False
            self._apply_filter_list()

    # -------- sorting: DataFrame backend --------

    def _apply_sort_frame(self):
        df = self._filtered_df
        if df is None:
            self._sorted_df = None
            return

        col = self.table_sort_column
        direction = self.table_sort_direction

        if not col or direction == 0 or col not in df.columns:
            self._sorted_df = df
            return

        ascending = direction == 1

        if self._frame_lib == "pandas":
            self._sorted_df = df.sort_values(col, ascending=ascending)
        elif self._frame_lib == "polars":
            self._sorted_df = df.sort(by=col, descending=not ascending)
        else:
            self._sorted_df = df

    # -------- pagination: DataFrame backend --------

    def _paginate_frame(self):
        df = self._sorted_df
        if df is None:
            self.data = []
            return

        size = max(int(self.page_size), 1)

        if self._frame_lib == "pandas":
            total = len(df)
        else:  # polars
            total = df.height

        max_page = max((total - 1) // size + 1, 1)

        page = max(int(self.table_page), 1)
        if page > max_page:
            page = max_page
            self.table_page = page

        start = (page - 1) * size

        if self._frame_lib == "pandas":
            page_df = df.iloc[start : start + size]
        else:  # polars
            page_df = df.slice(start, size)

        trait = DataFrameTrait()
        self.data = trait.validate(self, page_df)

    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)

        self._use_frame_backend = False
        self._frame_lib = None

        if data is not None:
            # try pandas DataFrame
            frame_used = False
            try:
                import pandas as pd

                if isinstance(data, pd.DataFrame):
                    if isinstance(data.index, pd.MultiIndex):
                        raise traitlets.TraitError(
                            "Table widget does not support pandas MultiIndex rows. "
                        )

                    if isinstance(data.columns, pd.MultiIndex):
                        raise traitlets.TraitError(
                            "Table widget does not support pandas MultiIndex columns."
                        )

                    self._use_frame_backend = True
                    self._frame_lib = "pandas"
                    df = data.copy()
                    self._oryginal_index_column_name = df.index.name or ""
                    df = df.reset_index(
                        names=self._mercury_index_column_name
                    )  # add index col
                    self._full_df = df
                    frame_used = True
            except ImportError:
                pass

            # try polars DataFrame
            if not frame_used:
                try:
                    import polars as pl

                    if isinstance(data, pl.DataFrame):
                        self._use_frame_backend = True
                        self._frame_lib = "polars"
                        df = data.clone()
                        df = df.with_row_index(name=self._mercury_index_column_name)
                        self._full_df = df
                        frame_used = True
                except ImportError:
                    pass

            if frame_used:
                # fast path: DataFrame backend
                self._handle_refresh(("filter", "sort", "paginate"))
            else:
                # generic path: list[dict] backend
                trait = DataFrameTrait()
                rows = trait.validate(self, data)
                for i, row in enumerate(rows):
                    rows[i] = {self._mercury_index_column_name: i, **row}

                self._full_data = rows
                self._handle_refresh(("filter", "sort", "paginate"))
        else:
            self._full_data = []
            self._filtered_data = []
            self._sorted_data = []
            self.data = []

        self.observe(
            self._react,
            names=[
                "table_page",
                "page_size",
                "table_search_query",
                "table_sort_column",
                "table_sort_direction",
            ],
        )

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
