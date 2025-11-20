import uuid
import json
import pandas as pd
from IPython.display import HTML


def Table(df: pd.DataFrame, page_size: int = 50):
    grid_id = f"aggrid_{uuid.uuid4().hex}"

    data = df.to_dict(orient="records")
    columns = [{"field": str(c)} for c in df.columns]

    html = f"""
    <style>
      /* hide default AG Grid sort icons */
      #{grid_id} .ag-header-icon,
      #{grid_id} .ag-icon-asc,
      #{grid_id} .ag-icon-desc,
      #{grid_id} .ag-icon-sort-ascending,
      #{grid_id} .ag-icon-sort-descending,
      #{grid_id} .ag-paging-button .ag-icon,
      #{grid_id} .ag-paging-panel .ag-icon,
      #{grid_id} .ag-paging-button[ref="btFirst"],
      #{grid_id} .ag-paging-button[ref="btLast"] {{
        display: none !important;
      }}
      
      #{grid_id} .ag-paging-button::after {{
        font-size: 14px;
        padding: 0 6px;
        cursor: pointer;
        opacity: 0.8;
        color: #bbb;
        transition: color 0.2s ease;
      }}

      #{grid_id} .ag-paging-button[ref="btPrevious"]::after {{
          content: "◄";
      }}

      #{grid_id} .ag-paging-button[ref="btNext"]::after {{
          content: "►";
      }}

      #{grid_id} .ag-paging-button:hover::after {{
          color: black;
      }}

      /* custom sort arrows */
      #{grid_id} .ag-header-cell-label::after {{
        content: "";
        margin-left: 4px;
        font-size: 0.7em;
      }}
      #{grid_id} .ag-header-cell-sorted-asc .ag-header-cell-label::after {{
        content: "▲";
      }}
      #{grid_id} .ag-header-cell-sorted-desc .ag-header-cell-label::after {{
        content: "▼";
      }}
    </style>

    <!-- table container -->
    <div id="{grid_id}" class="ag-theme-balham" style="width:100%;"></div>

    <script>
    (function() {{
      const SCRIPT_URL = "/files/mercury/external/ag-grid-community.min.js";

      document.querySelectorAll('script[src*="ag-grid-community"]').forEach(el => el.remove());

      function ensureScript(src) {{
        return new Promise((resolve, reject) => {{
          const existing = document.querySelector(`script[src="${{src}}"]`);
          if (existing && window.agGrid && window.agGrid.Grid) {{
            resolve();
            return;
          }}
          const s = existing || document.createElement("script");
          s.src = src;
          s.async = true;
          s.onload = resolve;
          s.onerror = reject;
          if (!existing) document.head.appendChild(s);
        }});
      }}

      (async () => {{
        await ensureScript(SCRIPT_URL);

        const gridOptions = {{
          columnDefs: {json.dumps(columns)},
          rowData: {json.dumps(data)},
          animateRows: true,
          rowSelection: "multiple",
          domLayout: "autoHeight",
          suppressSizeToFit: false,
          pagination: true,
          paginationPageSize: {page_size},

          defaultColDef: {{
            sortable: true,
            resizable: true
          }}
        }};

        const gridDiv = document.getElementById("{grid_id}");
        const grid = new window.agGrid.Grid(gridDiv, gridOptions);

        requestAnimationFrame(() => {{
          gridOptions.api.sizeColumnsToFit();
        }});

      }})();
    }})();
    </script>
    """

    return HTML(html)
