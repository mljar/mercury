import {
  CodeCell,
  MarkdownCell,
  RawCell,
  type Cell,
  type CodeCellModel,
  type ICellModel,
  type MarkdownCellModel,
  type RawCellModel
} from '@jupyterlab/cells';
import { Message } from '@lumino/messaging';
import { Signal } from '@lumino/signaling';
import { Panel, SplitPanel, Widget } from '@lumino/widgets';
import { CellItemWidget } from './item/widget';
import {
  AppModel,
  MERCURY_MIMETYPE,
  type IWidgetUpdate,
  type IExecutionError
} from './model';
import {
  codeCellExecute,
  executeWidgetsManagerClearValues
} from '../../executor/codecell';
// import {
//   getWidgetManager,
//   resolveIpyModel,
//   getWidgetModelIdsFromCell
// } from './ipyWidgetsHelpers';

import {
  hideErrorOutputsOnChange,
  removeElements,
  removePromptsOnChange
} from './domHelpers';
import { OutputStamper } from './outputStamper';

// --- metadata helpers for showCode (JL4 sharedModel first, legacy fallback)
import type { INotebookModel } from '@jupyterlab/notebook';
import type { DocumentRegistry } from '@jupyterlab/docregistry';
import type { IObservableJSON } from '@jupyterlab/observables';
import { BusyIndicator } from './busyIndicator';

function readShowCodeFromContext(
  context: DocumentRegistry.IContext<INotebookModel>
): boolean | undefined {
  const shared = (context.model as any)?.sharedModel;
  if (shared?.getMetadata) {
    const all = shared.getMetadata() ?? {};
    const v = (all as any)?.mercury?.showCode;
    return typeof v === 'boolean' ? v : undefined;
  }
  const md = context.model?.metadata as unknown as IObservableJSON | undefined;
  const mercury = (md?.get?.('mercury') as any) ?? {};
  const v = mercury?.showCode;
  return typeof v === 'boolean' ? v : undefined;
}

function readTitleFromContext(
  context: DocumentRegistry.IContext<INotebookModel>
): string | undefined {
  const shared = (context.model as any)?.sharedModel;
  if (shared?.getMetadata) {
    const all = shared.getMetadata() ?? {};
    const v = (all as any)?.mercury?.title;
    return typeof v === 'string' && v.trim() ? v.trim() : undefined;
  }
  const md = context.model?.metadata as unknown as IObservableJSON | undefined;
  const mercury = (md?.get?.('mercury') as any) ?? {};
  const v = mercury?.title;
  return typeof v === 'string' && v.trim() ? v.trim() : undefined;
}

function readFullWidthFromContext(
  context: DocumentRegistry.IContext<INotebookModel>
): boolean {
  const shared = (context.model as any)?.sharedModel;
  if (shared?.getMetadata) {
    const all = shared.getMetadata() ?? {};
    const v = (all as any)?.mercury?.fullWidth;
    // default: false
    return typeof v === 'boolean' ? v : false;
  }
  const md = context.model?.metadata as unknown as IObservableJSON | undefined;
  const mercury = (md?.get?.('mercury') as any) ?? {};
  const v = mercury?.fullWidth;
  return typeof v === 'boolean' ? v : false; // default false
}

function readAutoRerunFromContext(
  context: DocumentRegistry.IContext<INotebookModel>
): boolean {
  const shared = (context.model as any)?.sharedModel;
  if (shared?.getMetadata) {
    const all = shared.getMetadata() ?? {};
    const v = (all as any)?.mercury?.autoRerun;
    return v === undefined ? true : !!v; // default true
  }
  const md = context.model?.metadata as unknown as IObservableJSON | undefined;
  const mercury = (md?.get?.('mercury') as any) ?? {};
  const v = mercury?.autoRerun;
  return v === undefined ? true : !!v; // default true
}

function bindShowCodeListener(
  context: DocumentRegistry.IContext<INotebookModel>,
  onChange: () => void
): void {
  const shared = (context.model as any)?.sharedModel;
  if (shared?.changed?.connect) {
    shared.changed.connect(() => onChange());
    return;
  }
  const md = context.model?.metadata as unknown as IObservableJSON | undefined;
  // @ts-ignore Signal exists at runtime
  md?.changed?.connect?.(() => onChange());
}

// simple debounce; good enough for UI toggles
function debounce<T extends (...args: any[]) => void>(fn: T, ms = 80) {
  let t: number | undefined;
  return (...args: Parameters<T>) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), ms);
  };
}

/**
 * Default layout ratios and colors.
 */
const SIDEBAR_RATIO = 0.2; // 20% width
const MAIN_RATIO = 0.8; // 80% width
const TOP_RATIO = 0.85; // 85% height
const BOTTOM_RATIO = 0.15; // 15% height
const DEFAULT_SIDEBAR_BG = '#f8f9fa';

/**
 * Minimal page-config structure we actually consume.
 */
interface IPageConfigLike {
  baseUrl?: string;
  showCode?: boolean;
  theme?: {
    sidebar_background_color?: string;
  };
}

/**
 * Read the inline Jupyter page config JSON.
 * Throws if the element does not exist or contains invalid JSON.
 */
function getPageConfig(): IPageConfigLike {
  const el = document.getElementById('jupyter-config-data');
  if (!el) {
    throw new Error('Page config script not found');
  }

  try {
    return JSON.parse(el.textContent || '{}') as IPageConfigLike;
  } catch (err) {
    console.warn('Invalid page config JSON:', err);
    return {};
  }
}

/**
 * Fetch theme overrides.
 * The `url` parameter is accepted for future flexibility.
 */
// async function fetchTheme(_url: string) {
//   try {
//     const response = await fetch('http://localhost:8888/mercury/api/theme');
//     if (!response.ok) {
//       throw new Error(`Theme API error: ${response.status}`);
//     }
//     return await response.json();
//   } catch (err) {
//     console.warn('Failed to fetch theme overrides', err);
//     return {};
//   }
// }

/**
 * Main application widget that lays out notebook cells into
 * a sidebar (left), a main area (top-right), and a bottom panel (right).
 *
 * Layout sketch:
 *
 * +-------------------------------------------------------+
 * | mercury-main-panel                                    |
 * |                                                       |
 * |  +--------+---------------------------------------+   |
 * |  |        |      mercury-right-split-panel        |   |
 * |  |  Left  |   +-------------------------------+   |   |
 * |  | Panel  |   |      Right Top (Main)         |   |   |
 * |  | (20%)  |   |        (85% height)           |   |   |
 * |  |        |   +-------------------------------+   |   |
 * |  |        |   |    Right Bottom (Chat Input)  |   |   |
 * |  |        |   |         (15% height)          |   |   |
 * |  +--------+---+-------------------------------+---+   |
 * +-------------------------------------------------------+
 */
export class AppWidget extends Panel {
  // Layout containers
  private _split: SplitPanel; // left-right
  private _left: Panel; // sidebar
  private _rightSplit: SplitPanel; // top-bottom
  private _rightTop: Panel; // main
  private _rightBottom: Panel; // chat/bottom

  // State
  private _showCode = false;
  private _model: AppModel;
  private _cellItems: CellItemWidget[] = [];

  // Mapping: cellId -> notebook index to keep stable ordering for inline widgets.
  private _cellOrder = new Map<string, number>();

  // Visibility bookkeeping to avoid redundant size resets.
  private _lastLeftVisible = false;
  private _lastBottomVisible = false;
  private _initialized = false;   // true after the first initializeCells finishes
  private _rebuilding = false;    // guards against concurrent rebuilds

  // Stable signal handler refs
  private _cellsChangedHandler = (_: any, args: any) => this.onCellsChanged(args);
  private _mercuryWidgetAddedHandler = (_: any, payload: { cellId: string; position?: string }) => {
    const item = this._cellItems.find(w => w.cellId === payload.cellId);
    if (item && item.child instanceof CodeCell) {
      this.placeCell(item.child, payload.position);
      // If showCode is on and the input is in rightTop, also re-order the input
      if (this._showCode && item.child.parent === this._rightTop) {
        const order = this._cellOrder.get(item.child.model.id);
        const idx = this.insertionIndexFor(this._rightTop, order, 'input');
        if ((this._rightTop.layout as any)?.removeWidget) {
          (this._rightTop.layout as any).removeWidget(item.child);
        }
        this._rightTop.insertWidget(idx, item.child);
      }
    }
  };
  private _cellsChangedConnected = false;
  private _widgetUpdatedConnected = false;
  private _mercuryWidgetAddedConnected = false;
  private _leftHeader!: Panel;   // NEW: fixed header area
  private _leftContent!: Panel;  // NEW: scrollable area for sidebar widgets
  private _sidebarTitle?: string;
  // autorerun state + UI
  private _autoRerun = true;
  private _leftFooter!: Panel;
  private _runAllBtn!: HTMLButtonElement;
  private _busy?: BusyIndicator;
  private _fullWidth = false;
  private _toastContainer?: HTMLDivElement;

  constructor(model: AppModel) {
    super();

    const pageConfig = getPageConfig();
    // void fetchTheme(pageConfig.baseUrl || '');

    this._model = model;

    this.id = 'mercury-main-panel';
    this.addClass('mercury-main-panel');

    // Build static layout containers
    this._left = this.createSidebar(pageConfig);
    const { rightSplit, rightTop, rightBottom } = this.createRightPanels();
    this._rightSplit = rightSplit;
    this._rightTop = rightTop;
    this._rightBottom = rightBottom;
    this._split = this.createMainSplit(this._left, this._rightSplit);

    this._split.spacing = 0;

    this._busy = new BusyIndicator({
      container: this._rightTop.node,
      position: 'top-right'
    });

    // Add root container to this widget
    this.addWidget(this._split);

    this.createToastContainer();

    const scheduleRebuild = debounce(() => this.rebuildForShowCodeChange(), 80);
    bindShowCodeListener(this._model.context, () => {
      const v = readShowCodeFromContext(this._model.context);
      if (typeof v === 'boolean' && v !== this._showCode) {
        this._showCode = v;
        scheduleRebuild();
      }
      // always refresh the sidebar title (cheap)
      const newTitle = readTitleFromContext(this._model.context);
      if (newTitle !== this._sidebarTitle) {
        this.setSidebarTitle(newTitle);
      }
      // update fullWidth
      const newFull = readFullWidthFromContext(this._model.context);
      if (newFull !== this._fullWidth) {
        this._fullWidth = newFull;
        this.applyFullWidthLayout();
      }
      // refresh autoRerun state + UI
      const newAuto = readAutoRerunFromContext(this._model.context);
      if (newAuto !== this._autoRerun) {
        this._autoRerun = newAuto;
        this.syncAutoRerunUI();
      }
    });

    // Sidebar toggle buttons
    this.installSidebarToggles();

    // Sidebar set title
    this._sidebarTitle = readTitleFromContext(this._model.context);
    this.setSidebarTitle(this._sidebarTitle);

    // fill width
    this._fullWidth = readFullWidthFromContext(this._model.context);
    this.applyFullWidthLayout();

    // Auto Rerun
    this._autoRerun = readAutoRerunFromContext(this._model.context);
    this.syncAutoRerunUI();

    // When the model is ready, populate all cell widgets
    this._model.ready.connect(() => this.initializeCells());

    // When a mercury widget is added (from outputs), try to place it — single connection
    if (!this._mercuryWidgetAddedConnected) {
      this._model.mercuryWidgetAdded.connect(this._mercuryWidgetAddedHandler);
      this._mercuryWidgetAddedConnected = true;
    }

    this._model.executionError.connect(this.onExecutionError, this);

    // style for bottom panel
    //this._rightBottom.node.style.backgroundColor =
    //  pageConfig?.theme?.sidebar_background_color ?? DEFAULT_SIDEBAR_BG;
    this._model.context.sessionContext.statusChanged.connect((_, status) => {
      // if (status === 'busy') {
      //   this._busy?.begin();
      // } else if (status === 'idle') {
      //   this._busy?.finish();
      // }
    });
    // Wire the button to interrupt the kernel
    this._busy.element.addEventListener('mbi:interrupt', () => {
      try {
        void this._model.context.sessionContext.session?.kernel?.interrupt();
      } catch {
        /* empty */
      }
    });
  }

  private createToastContainer(): void {
    if (this._toastContainer) {
      return;
    }
    const el = document.createElement('div');
    el.className = 'mercury-toast-container';
    this.node.appendChild(el);
    this._toastContainer = el;
  }

  private onExecutionError(_model: AppModel, err: IExecutionError): void {
    if (!this._toastContainer) {
      this.createToastContainer();
      if (!this._toastContainer) {
        return;
      }
    }

    const toast = document.createElement('div');
    toast.className = 'mercury-toast mercury-toast-error';

    const title = document.createElement('div');
    title.className = 'mercury-toast-title';
    title.textContent = err.ename || 'Error';

    const msg = document.createElement('div');
    msg.className = 'mercury-toast-body';
    msg.textContent = err.evalue || 'Execution error';

    const close = document.createElement('button');
    close.className = 'mercury-toast-close';
    close.type = 'button';
    close.textContent = '×';

    // zamknięcie po kliknięciu
    close.onclick = () => {
      toast.remove();
    };

    toast.appendChild(close);
    toast.appendChild(title);
    toast.appendChild(msg);

    this._toastContainer.appendChild(toast);

    // auto-hide po kilku sekundach (np. 8s)
    const timeout = window.setTimeout(() => {
      try {
        toast.remove();
      } catch { /* ignore */ }
    }, 8000);

    // jeśli user zamknie ręcznie – wyczyść timeout
    toast.addEventListener('remove', () => {
      window.clearTimeout(timeout);
    });
  }

  private setSidebarTitle(title?: string) {
    const t = (title ?? '').trim();
    this._sidebarTitle = t || undefined;

    if (!this._leftHeader) return;
    const titleEl = (this._leftHeader.node as any)._titleEl as HTMLDivElement | undefined;
    if (titleEl) titleEl.textContent = t || '';

    // Hide the title row if empty (optional)
    this._leftHeader.node.style.display = t ? '' : 'none';

    this.updatePanelVisibility(); // re-evaluate left visibility
  }


  // ────────────────────────────────────────────────────────────────────────────
  // Lifecycle hooks
  // ────────────────────────────────────────────────────────────────────────────

  protected onAfterAttach(msg: Message): void {
    super.onAfterAttach(msg);

    // Keep browser context menu; block JupyterLab/Lumino menu only.
    this.node.addEventListener(
      'contextmenu',
      (event: MouseEvent) => event.stopImmediatePropagation(),
      true
    );
    this._left.node.addEventListener('contextmenu', e => e.preventDefault());

    // Set split sizes after first paint
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this._split.setRelativeSizes([SIDEBAR_RATIO, MAIN_RATIO]);
        this._rightSplit.setRelativeSizes([TOP_RATIO, BOTTOM_RATIO]);
      });
    });
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    try {
      if (this._toastContainer) {
        this._toastContainer.remove();
        this._toastContainer = undefined;
      }
    } catch { }
    try {
      if (this._widgetUpdatedConnected) {
        this._model?.widgetUpdated?.disconnect(this.onWidgetUpdate, this);
        this._widgetUpdatedConnected = false;
      }
    } catch { }
    try {
      if (this._cellsChangedConnected) {
        this._model?.cells?.changed?.disconnect(this._cellsChangedHandler);
        this._cellsChangedConnected = false;
      }
    } catch { }
    try {
      if (this._mercuryWidgetAddedConnected) {
        this._model?.mercuryWidgetAdded?.disconnect(this._mercuryWidgetAddedHandler);
        this._mercuryWidgetAddedConnected = false;
      }
    } catch { }

    try {
      this._model?.ready?.disconnect(this.initializeCells, this);
    } catch { }

    for (const item of this._cellItems) {
      try {
        item.child?.model?.stateChanged?.disconnect(undefined as any, this);
      } catch { }
    }
    this._cellItems = [];
    this._left = null as any;
    this._rightTop = null as any;
    this._rightBottom = null as any;
    this._rightSplit = null as any;
    this._split = null as any;

    Signal.clearData(this);
    try { this._busy?.dispose(); } catch { }
    super.dispose();
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Public API
  // ────────────────────────────────────────────────────────────────────────────

  get cellWidgets(): CellItemWidget[] {
    return this._cellItems;
  }

  /**
   * Place a code cell's output area into the appropriate panel
   * based on its MERCURY_MIMETYPE metadata or an explicit override.
   * Keeps widgets ordered by notebook order in ALL targets.
   */
  placeCell(
    cell: CodeCell,
    posOverride?: 'sidebar' | 'bottom' | 'inline' | string
  ): void {
    if (this.isDisposed) {
      return;
    }

    const oa = cell.outputArea;

    // Determine target position
    let position = posOverride;
    if (!position) {
      for (let i = 0; i < oa.model.length; i++) {
        const output = oa.model.get(i);
        const data = output.data as Record<string, unknown> | undefined;

        if (data && MERCURY_MIMETYPE in data) {
          const raw = data[MERCURY_MIMETYPE];
          let meta: any = null;

          try {
            if (typeof raw === 'string') {
              // Old behavior: MIME payload as JSON string
              meta = JSON.parse(raw);
            } else if (typeof raw === 'object' && raw !== null) {
              // New behavior: MIME payload as object
              meta = raw;
            }

            if (meta && typeof meta.position === 'string') {
              position = meta.position;
            } else {
              position = 'sidebar';
            }
          } catch {
            position = 'sidebar';
          }

          break;
        }
      }
    }

    // Map to target panel (default to inline/rightTop)
    const target: Panel =
      position === 'sidebar'
        ? this._leftContent
        : position === 'bottom'
          ? this._rightBottom
          : this._rightTop;

    // Compute stable insertion index from notebook order
    const order = this._cellOrder.get(cell.model.id);
    const kind = target === this._rightTop ? 'output' : 'other';
    const idx = this.insertionIndexFor(target, order, kind);

    // Insert in order if possible; otherwise append
    if (typeof (target as any).insertWidget === 'function') {
      target.insertWidget(idx, oa);
    } else {
      target.addWidget(oa);
    }

    // Update visibility/sizing of panels after placement
    this.updatePanelVisibility();

    if (target === this._rightBottom) {
      requestAnimationFrame(() => this.adjustBottomHeight());
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Initialization
  // ────────────────────────────────────────────────────────────────────────────

  private hideInlineOutputWrapper(cell: CodeCell) {
    const el = cell.node.querySelector<HTMLElement>('.jp-Cell-outputWrapper');
    if (el) el.style.display = 'none';
  }

  // private showInlineOutputWrapper(cell: CodeCell) {
  //   const el = cell.node.querySelector<HTMLElement>('.jp-Cell-outputWrapper');
  //   if (el) el.style.display = '';
  // }

  private initializeCells(): void {
    const cells = this._model.cells;

    this.rebuildCellOrder();

    for (let i = 0; i < cells.length; i++) {
      const model = cells.get(i);
      const item = this.createCell(model);
      this._cellItems.push(item);

      if (item.child instanceof CodeCell) {
        const code = item.child;
        const oa = code.outputArea;

        if (this._showCode) {
          // ORDERED insert of code INPUT into rightTop
          const order = this._cellOrder.get(code.model.id);
          const idx = this.insertionIndexFor(this._rightTop, order, 'input');
          this._rightTop.insertWidget(idx, code);
          this.hideInlineOutputWrapper(code);
        }

        if (item.sidebar) {
          this._leftContent.addWidget(oa);
        } else if (item.bottom) {
          this._rightBottom.addWidget(oa);
        } else {
          // inline outputs go to rightTop in order — make sure outputs come after input
          const order = this._cellOrder.get(code.model.id);
          const idx = this.insertionIndexFor(this._rightTop, order, 'output');
          this._rightTop.insertWidget(idx, oa);
        }
      } else {
        // Non-code cells go inline in the main area in order
        const order = this._cellOrder.get(item.child.model.id);
        const idx = this.insertionIndexFor(this._rightTop, order, 'other');
        this._rightTop.insertWidget(idx, item.child);
      }
    }

    // React to per-widget updates (may trigger downstream re-execution)
    try {
      if (this._widgetUpdatedConnected) {
        this._model.widgetUpdated.disconnect(this.onWidgetUpdate, this);
      }
    } catch { }
    this._model.widgetUpdated.connect(this.onWidgetUpdate, this);
    this._widgetUpdatedConnected = true;

    // React to structural changes in the cell list (single connection)
    try {
      if (this._cellsChangedConnected) {
        this._model.cells.changed.disconnect(this._cellsChangedHandler);
      }
    } catch { }
    this._model.cells.changed.connect(this._cellsChangedHandler);
    this._cellsChangedConnected = true;

    this.updatePanelVisibility();
    void this.checkWidgetModels();

    // ✅ cells are now ready; future toggles can safely rebuild
    this._initialized = true;

    // If metadata already has showCode, prefer it over pageConfig
    const metaShow = readShowCodeFromContext(this._model.context);
    if (typeof metaShow === 'boolean') {
      this._showCode = metaShow;
    }
  }

  /** Remove any existing sidebar toggle DOM buttons to avoid duplicates. */
  private removeSidebarToggles(): void {
    try {
      this.node.querySelectorAll('.mercury-sidebar-toggle').forEach(n => n.remove());
      this._left?.node?.querySelectorAll?.('.mercury-sidebar-toggle')?.forEach(n => n.remove());
    } catch { /* ignore */ }
  }

  /** Full teardown + rebuild when showCode changes. */
  private rebuildForShowCodeChange(): void {
    if (this._rebuilding || this.isDisposed) return;
    if (!this._initialized) return; // wait until first init

    this._rebuilding = true;

    // 1) Snapshot scroll position (optional nicety)
    const scrollTop = this._rightTop?.node?.scrollTop ?? 0;

    // 2) Disconnect signals we registered in initializeCells
    try {
      if (this._widgetUpdatedConnected) {
        this._model.widgetUpdated.disconnect(this.onWidgetUpdate, this);
        this._widgetUpdatedConnected = false;
      }
    } catch { }
    try {
      if (this._cellsChangedConnected) {
        this._model.cells.changed.disconnect(this._cellsChangedHandler);
        this._cellsChangedConnected = false;
      }
    } catch { }

    // 3) Dispose all cell widgets we created
    try {
      for (const item of this._cellItems) {
        this.disposeItem(item);
      }
    } catch { }
    this._cellItems = [];
    this._cellOrder.clear();

    // 4) Remove toggle buttons to avoid duplicates
    this.removeSidebarToggles();

    // 5) Dispose existing panels/split and remove from this container
    try {
      if (this._split) {
        if (this._split.parent && (this.layout as any)?.removeWidget) {
          (this.layout as any).removeWidget(this._split);
        }
        this._split.dispose();
      }
    } catch { }

    // 6) Recreate panels/splits fresh (same as constructor)
    try {
      const pageConfig = getPageConfig(); // ok to call again
      this._left = this.createSidebar(pageConfig);
      const { rightSplit, rightTop, rightBottom } = this.createRightPanels();
      this._rightSplit = rightSplit;
      this._rightTop = rightTop;
      this._rightBottom = rightBottom;
      this._split = this.createMainSplit(this._left, this._rightSplit);
      this.addWidget(this._split);
      this.installSidebarToggles();
      this.setSidebarTitle(readTitleFromContext(this._model.context));
      this._autoRerun = readAutoRerunFromContext(this._model.context);
      this.syncAutoRerunUI();
      this.applyFullWidthLayout();
    } catch (err) {
      console.error('[Mercury][rebuild] failed to recreate panels:', err);
    }

    // 7) Reset bookkeeping
    this._lastLeftVisible = false;
    this._lastBottomVisible = false;
    this._initialized = false; // will flip to true at end of initializeCells

    // 8) Re-initialize from the model (this uses current this._showCode)
    try {
      this.initializeCells();
    } catch (err) {
      console.error('[Mercury][rebuild] initializeCells error:', err);
    }

    // 9) Restore scroll position (best-effort, after a tick)
    requestAnimationFrame(() => {
      try { if (this._rightTop?.node) this._rightTop.node.scrollTop = scrollTop; } catch { }
      this._rebuilding = false;
    });
  }

  /**
   * Create a CellItemWidget for a given ICellModel.
   */
  private outputStamper = new OutputStamper();
  private createCell(cellModel: ICellModel): CellItemWidget {
    let widget: Cell;
    let sidebar = false;
    let bottom = false;

    switch (cellModel.type) {
      case 'code': {
        const cell = new CodeCell({
          model: cellModel as CodeCellModel,
          rendermime: this._model.rendermime,
          contentFactory: this._model.contentFactory,
          editorConfig: this._model.editorConfig.code
        });
        cell.readOnly = true;

        this.outputStamper.attach(cell);

        // hide error outputs
        hideErrorOutputsOnChange(cell.outputArea.node);

        // adjust height
        const oa = cell.outputArea;
        const syncOutputVisibility = () => {
          const hasOutputs = oa.model.length > 0;
          oa.node.style.display = hasOutputs ? '' : 'none';
          this.updatePanelVisibility();
          if (oa.parent === this._rightBottom) {
            requestAnimationFrame(() => this.adjustBottomHeight());
          }
        };
        syncOutputVisibility();
        oa.model.changed.connect(() => {
          syncOutputVisibility();
        });

        // Look for MERCURY metadata to decide placement
        for (let i = 0; i < cell.outputArea.model.length; i++) {
          const output = cell.outputArea.model.get(i);
          const data = output.data as Record<string, unknown> | undefined;
          if (data && MERCURY_MIMETYPE in data) {
            try {
              const raw = data[MERCURY_MIMETYPE];
              let meta: any;

              if (typeof raw === 'string') {
                // Old behavior: JSON as string
                meta = JSON.parse(raw);
              } else if (typeof raw === 'object' && raw !== null) {
                // New behavior: JSON as object
                meta = raw;
              } else {
                meta = {};
              }

              const pos =
                typeof meta.position === 'string' ? meta.position : 'sidebar';
              sidebar = pos === 'sidebar';
              bottom = pos === 'bottom';
            } catch {
              sidebar = true;
              bottom = false;
            }

            break;
          }
        }
        widget = cell;
        break;
      }

      case 'markdown': {
        const cell = new MarkdownCell({
          model: cellModel as MarkdownCellModel,
          rendermime: this._model.rendermime,
          contentFactory: this._model.contentFactory,
          editorConfig: this._model.editorConfig.markdown
        });
        cell.inputHidden = false;
        cell.rendered = true;
        removeElements(cell.node, 'jp-Collapser');
        removeElements(cell.node, 'jp-InputPrompt');
        widget = cell;
        break;
      }

      default: {
        const cell = new RawCell({
          model: cellModel as RawCellModel,
          contentFactory: this._model.contentFactory,
          editorConfig: this._model.editorConfig.raw
        });
        cell.inputHidden = false;
        removeElements(cell.node, 'jp-Collapser');
        removeElements(cell.node, 'jp-InputPrompt');
        widget = cell;
        break;
      }
    }

    // executionCount updates when an execution finishes (reply received)
    widget.model.stateChanged.connect((_, args) => {
      if (args.name === 'executionCount') {
        this.updatePanelVisibility();
      }
    });

    return new CellItemWidget(widget, {
      cellId: cellModel.id,
      cellWidget: widget,
      sidebar,
      bottom
    });
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Cell list / ordering utilities
  // ────────────────────────────────────────────────────────────────────────────

  private rebuildCellOrder(): void {
    const cells = this._model.cells;
    this._cellOrder.clear();
    for (let i = 0; i < cells.length; i++) {
      this._cellOrder.set(cells.get(i).id, i);
    }
  }

  private panelWidgets(panel: Panel | null | undefined): ReadonlyArray<Widget> {
    // after dispose panel.layout === null → return empty list
    return ((panel as any)?.layout?.widgets ?? []) as ReadonlyArray<Widget>;
  }

  /**
   * Find insertion index inside `container` so that widgets maintain notebook order.
   * Ensures that code inputs appear before their outputs for the same cell in rightTop.
   */
  private insertionIndexFor(
    container: Panel,
    targetOrder?: number,
    targetKind: 'input' | 'output' | 'other' = 'other'
  ): number {
    if (targetOrder === undefined) {
      return this.panelWidgets(container).length;
    }

    let idx = 0;
    for (const w of this.panelWidgets(container)) {
      const ci = this._cellItems.find(
        c =>
          c.child === w || // code input or markdown/raw
          (c.child instanceof CodeCell && (c.child as CodeCell).outputArea === w) // output area
      );
      if (!ci) continue;

      const otherOrder = this._cellOrder.get(ci.child.model.id);
      if (otherOrder === undefined) continue;

      if (otherOrder < targetOrder) {
        idx++;
        continue;
      }

      if (otherOrder === targetOrder) {
        const wIsOutput =
          ci.child instanceof CodeCell && (ci.child as CodeCell).outputArea === w;
        const wIsInput = ci.child === w;

        // If inserting an OUTPUT, it must come AFTER its INPUT
        if (targetKind === 'output' && wIsInput) {
          idx++;
          continue;
        }

        // If inserting an INPUT, it must come BEFORE its OUTPUT
        if (targetKind === 'input' && wIsOutput) {
          // do NOT increment; keep idx where it is so input goes before output
          continue;
        }
      }
    }
    return idx;
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Model reactions
  // ────────────────────────────────────────────────────────────────────────────

  private onCellsChanged(args: any): void {
    if (this.isDisposed) {
      return;
    }
    switch (args.type) {
      case 'add': {
        this.rebuildCellOrder();
        let insertAt = args.newIndex;
        for (const m of args.newValues as ICellModel[]) {
          const item = this.createCell(m);
          this._cellItems.splice(insertAt, 0, item);
          this.insertItem(item, insertAt);
          insertAt++;
        }
        this.rebuildCellOrder();
        this.updatePanelVisibility();
        void this.checkWidgetModels();
        break;
      }

      case 'remove': {
        for (let i = 0; i < (args.oldValues as ICellModel[]).length; i++) {
          const removed = this._cellItems.splice(args.oldIndex, 1)[0];
          if (removed) {
            this.disposeItem(removed);
          }
        }
        this.rebuildCellOrder();
        this.updatePanelVisibility();
        break;
      }

      case 'move': {
        const [moved] = this._cellItems.splice(args.oldIndex, 1);
        this._cellItems.splice(args.newIndex, 0, moved);
        this.rebuildCellOrder();

        if (moved.child instanceof CodeCell) {
          const cell = moved.child as CodeCell;
          const oa = cell.outputArea;

          // Reposition OUTPUT area in its target panel
          if (oa.parent) {
            if ((oa.parent.layout as any)?.removeWidget) {
              (oa.parent.layout as any).removeWidget(oa);
            } else {
              Widget.detach(oa);
            }
          }
          const target = moved.sidebar
            ? this._leftContent
            : moved.bottom
              ? this._rightBottom
              : this._rightTop;

          const order = this._cellOrder.get(cell.model.id);
          const outIdx = this.insertionIndexFor(
            target,
            order,
            target === this._rightTop ? 'output' : 'other'
          );
          target.insertWidget(outIdx, oa);

          // If showing code inputs, also reposition the *code input* in rightTop
          if (this._showCode && cell.parent === this._rightTop) {
            const inOrder = this._cellOrder.get(cell.model.id);
            const inIdx = this.insertionIndexFor(this._rightTop, inOrder, 'input');
            if ((this._rightTop.layout as any)?.removeWidget) {
              (this._rightTop.layout as any).removeWidget(cell);
            } else if (cell.parent) {
              Widget.detach(cell);
            }
            this._rightTop.insertWidget(inIdx, cell);
            this.hideInlineOutputWrapper(cell);
          }
        } else {
          const w = moved.child;
          if (w.parent) {
            if ((w.parent.layout as any)?.removeWidget) {
              (w.parent.layout as any).removeWidget(w);
            } else {
              Widget.detach(w);
            }
          }
          const order = this._cellOrder.get(w.model.id);
          const idx = this.insertionIndexFor(this._rightTop, order, 'other');
          this._rightTop.insertWidget(idx, w);
        }

        this.updatePanelVisibility();
        break;
      }

      case 'set': {
        const item = this._cellItems[args.newIndex];
        if (item?.child instanceof CodeCell) {
          this.placeCell(item.child as CodeCell);
        }
        this.updatePanelVisibility();
        break;
      }

      default: {
        this.rebuildCellOrder();
        this.updatePanelVisibility();
      }
    }
  }

  // --- autorerun gate + coalesce ---
  private _acceptWidgetInput = true;
  private _rerunInProgress = false;
  private _pendingRerunFromIndex: number | null = null;
  private _rerunTimer: number | null = null;

  private onWidgetUpdate = (_model: AppModel, update: IWidgetUpdate) => {
    if (!this._autoRerun || this.isDisposed) {
      return;
    }
    if (!update.cellModelId) {
      return;
    }
    // find index of the updated cell
    const cells = this._model.cells;
    let updatedIndex = -1;
    for (let i = 0; i < cells.length; i++) {
      if (cells.get(i).id === update.cellModelId) {
        updatedIndex = i;
        break;
      }
    }
    if (updatedIndex === -1) {
      return;
    }

    const fromIndex = updatedIndex + 1;

    // If we are busy, just remember earliest affected index
    if (!this._acceptWidgetInput || this._rerunInProgress) {
      this._pendingRerunFromIndex =
        this._pendingRerunFromIndex === null
          ? fromIndex
          : Math.min(this._pendingRerunFromIndex, fromIndex);
      return;
    }

    // Debounce bursts of updates (checkbox rapid clicks, slider drags, etc.)
    this._pendingRerunFromIndex =
      this._pendingRerunFromIndex === null
        ? fromIndex
        : Math.min(this._pendingRerunFromIndex, fromIndex);

    if (this._rerunTimer !== null) {
      window.clearTimeout(this._rerunTimer);
    }
    this._rerunTimer = window.setTimeout(() => {
      this._rerunTimer = null;
      const start = this._pendingRerunFromIndex;
      this._pendingRerunFromIndex = null;
      if (start !== null) {
        void this._runCellsFromIndex(start);
      }
    }, 10);
  };

  private async _runCellsFromIndex(fromIndex: number): Promise<void> {
    // If a run is already happening, coalesce and exit
    if (this._rerunInProgress) {
      this._pendingRerunFromIndex =
        this._pendingRerunFromIndex === null
          ? fromIndex
          : Math.min(this._pendingRerunFromIndex, fromIndex);
      return;
    }

    this._rerunInProgress = true;
    this._acceptWidgetInput = false;

    this._busy?.begin();
    try {
      const cells = this._model.cells;

      const itemByCellId = new Map<string, { child: unknown }>();
      for (const w of this._cellItems) {
        itemByCellId.set(w.cellId, w);
      }
      for (let i = fromIndex; i < cells.length; i++) {
        // stop early if a newer update arrived
        //if (this._pendingRerunFromIndex !== null) {
        //  break;
        //}

        const cellModel = cells.get(i);
        if (cellModel.type !== 'code') {
          continue;
        }

        const item = itemByCellId.get(cellModel.id);
        const child = item?.child;
        if (!(child instanceof CodeCell)) {
          continue;
        }

        await codeCellExecute(child, this._model.context.sessionContext);
        // await every 5th cell
        // if ((i - fromIndex) % 2 === 0) {
        //   await codeCellExecute(child, this._model.context.sessionContext);
        // } else {
        //   codeCellExecute(child, this._model.context.sessionContext);
        // }
      }

      // Do this once per chain, not per cell
      await executeWidgetsManagerClearValues(
        this._model.context.sessionContext
      );
    } catch (e) {
      console.error('[Mercury][autoRerun] chain failed:', e);
    } finally {
      this._busy?.finish();
      this._acceptWidgetInput = true;
      this._rerunInProgress = false;
      // If something changed while we were running, run again once (coalesced)
      if (this._pendingRerunFromIndex !== null) {
        const nextFrom = this._pendingRerunFromIndex;
        this._pendingRerunFromIndex = null;
        void this._runCellsFromIndex(nextFrom);
      }
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Insert / dispose helpers
  // ────────────────────────────────────────────────────────────────────────────

  private insertItem(item: CellItemWidget, _modelIndex: number): void {
    if (this.isDisposed) {
      return;
    }
    const order = this._cellOrder.get(item.child.model.id);

    if (item.child instanceof CodeCell) {
      const cell = item.child as CodeCell;
      const oa = cell.outputArea;

      if (this._showCode) {
        // ORDERED insert of the code input
        const inIdx = this.insertionIndexFor(this._rightTop, order, 'input');
        this._rightTop.insertWidget(inIdx, cell);
        this.hideInlineOutputWrapper(cell);
      }

      const target = item.sidebar
        ? this._leftContent
        : item.bottom
          ? this._rightBottom
          : this._rightTop;

      const outIdx = this.insertionIndexFor(
        target,
        order,
        target === this._rightTop ? 'output' : 'other'
      );
      target.insertWidget(outIdx, oa);
    } else {
      // markdown / raw -> rightTop, in notebook order
      const idx = this.insertionIndexFor(this._rightTop, order, 'other');
      this._rightTop.insertWidget(idx, item.child);
    }
  }

  private disposeItem(item: CellItemWidget): void {
    if (item.child instanceof CodeCell) {
      item.child.outputArea.dispose();
      item.child.dispose();
    } else {
      item.child.dispose();
    }
  }

  // ────────────────────────────────────────────────────────────────────────────
  // ipywidgets utilities
  // ────────────────────────────────────────────────────────────────────────────

  private async reexecuteAllCodeCells(): Promise<void> {
    const cells = this._model.cells;
    for (let i = 0; i < cells.length; i++) {
      const m = cells.get(i);
      if (m.type !== 'code') {
        continue;
      }

      const item = this._cellItems.find(w => w.cellId === m.id);
      if (item && item.child instanceof CodeCell) {
        await codeCellExecute(
          item.child as CodeCell,
          this._model.context.sessionContext,
          {
            deletedCells: this._model.context.model?.deletedCells ?? []
          }
        );
      }
    }
    await executeWidgetsManagerClearValues(this._model.context.sessionContext);
  }

  private async checkWidgetModels(): Promise<void> {
    /*
    if (this.isDisposed) {
      return;
    }
    const manager = await getWidgetManager(this._model.rendermime);
    if (!manager) {
      console.warn('No widget manager - cannot check widget models');
      return;
    }

    let totalWithId = 0;
    let foundCount = 0;
    let hasCodeCells = false;
    let allOutputsEmpty = true;

    for (const item of this._cellItems) {
      if (!(item.child instanceof CodeCell)) {
        continue;
      }

      hasCodeCells = true;

      // check if outputs exist
      if (item.child.model.outputs.length > 0) {
        allOutputsEmpty = false;
      }

      const ids = getWidgetModelIdsFromCell(item.child);
      if (ids.length === 0) {
        continue;
      }

      totalWithId += ids.length;
      for (const id of ids) {
        const model = await resolveIpyModel(manager, id);
        if (model && !!(model as any).comm_live) {
          foundCount++;
        }
      }
    }

    // condition 1: we had widget ids but none were alive
    const noLiveModels = totalWithId > 0 && foundCount === 0;

    // condition 2: there are code cells but all outputs are empty
    const emptyOutputs = hasCodeCells && allOutputsEmpty;

    if (noLiveModels || emptyOutputs) {
      this.reexecuteAllCodeCells();
    }
      */
  }

  // ────────────────────────────────────────────────────────────────────────────
  // Layout helpers
  // ────────────────────────────────────────────────────────────────────────────

  private applyFullWidthLayout(): void {
    if (!this._rightTop || !this._rightBottom) {
      return;
    }

    const nodes = [this._rightTop.node, this._rightBottom.node];

    if (!this._fullWidth) {
      // max 1024px + auto margin
      for (const node of nodes) {
        node.classList.add('mercury-right-limited');
      }
    } else {
      // full width no margins
      for (const node of nodes) {
        node.classList.remove('mercury-right-limited');
      }
    }
  }

  private syncAutoRerunUI(): void {
    // button visible only when autoRerun is false
    if (this._runAllBtn) {
      this._runAllBtn.style.display = this._autoRerun ? 'none' : '';
    }
    this.updatePanelVisibility();
  }

  private createSidebar(pageConfig: IPageConfigLike): Panel {
    const left = new Panel();
    left.addClass('mercury-left-panel');
    left.node.style.backgroundColor =
      pageConfig?.theme?.sidebar_background_color ?? DEFAULT_SIDEBAR_BG;

    // Header panel (fixed at top)
    this._leftHeader = new Panel();
    this._leftHeader.addClass('mercury-left-header');

    // Title element inside header
    const titleEl = document.createElement('div');
    titleEl.className = 'mercury-sidebar-title';
    (this._leftHeader.node as any)._titleEl = titleEl;
    this._leftHeader.node.appendChild(titleEl);

    // Content panel (all sidebar widgets go here)
    this._leftContent = new Panel();
    this._leftContent.addClass('mercury-left-content');

    // NEW: Footer panel (bottom) with "Run all" button
    this._leftFooter = new Panel();
    this._leftFooter.addClass('mercury-left-footer');
    // create the button once and keep a ref
    this._runAllBtn = document.createElement('button');
    this._runAllBtn.className = 'mercury-runall-btn';
    this._runAllBtn.textContent = '▶ Run';
    this._runAllBtn.onclick = () => {
      // Runs all code cells top → bottom
      this.reexecuteAllCodeCells();
    };
    // start hidden; shown only when _autoRerun === false
    this._runAllBtn.style.display = 'none';
    this._leftFooter.node.appendChild(this._runAllBtn);

    // Compose: header → content → footer
    left.addWidget(this._leftHeader);
    left.addWidget(this._leftContent);
    left.addWidget(this._leftFooter);

    return left;
  }

  private createRightPanels() {
    const rightTop = new Panel();
    rightTop.addClass('mercury-right-top-panel');

    const rightBottom = new Panel();
    rightBottom.addClass('mercury-right-bottom-panel');

    removePromptsOnChange(rightBottom.node, () => {
      // po zmianie DOM-u w bottom panelu – popraw wysokość
      requestAnimationFrame(() => this.adjustBottomHeight());
    });

    const rightSplit = new SplitPanel();
    rightSplit.orientation = 'vertical';
    rightSplit.addClass('mercury-right-split-panel');
    rightSplit.addWidget(rightTop);
    rightSplit.addWidget(rightBottom);

    return { rightSplit, rightTop, rightBottom } as const;
  }

  private createMainSplit(left: Panel, right: SplitPanel): SplitPanel {
    const split = new SplitPanel();
    split.orientation = 'horizontal';
    split.addClass('mercury-split-panel');
    split.addWidget(left);
    split.addWidget(right);
    split.node.style.height = '100%';
    split.node.style.width = '100%';
    return split;
  }

  private installSidebarToggles(): void {
    const collapseBtn = document.createElement('button');
    collapseBtn.innerHTML = '«';
    collapseBtn.className = 'mercury-sidebar-toggle mercury-sidebar-collapse';
    collapseBtn.title = 'Hide sidebar';
    this._left.node.appendChild(collapseBtn);

    const expandBtn = document.createElement('button');
    expandBtn.innerHTML = '»';
    expandBtn.className = 'mercury-sidebar-toggle mercury-sidebar-expand';
    expandBtn.title = 'Show sidebar';
    expandBtn.style.display = 'none';
    this.node.appendChild(expandBtn);

    collapseBtn.onclick = () => {
      this._left.hide();
      this._split.setRelativeSizes([0, 1]);
      collapseBtn.style.display = 'none';
      expandBtn.style.display = '';
    };

    expandBtn.onclick = () => {
      this._left.show();
      this._split.setRelativeSizes([SIDEBAR_RATIO, MAIN_RATIO]);
      collapseBtn.style.display = '';
      expandBtn.style.display = 'none';
    };
  }

  private updatePanelVisibility(): void {
    if (this.isDisposed) return;

    const leftContentHasOutputs =
      this.panelWidgets(this._leftContent).some(
        w => (w as any).model?.length > 0
      ) || !this._autoRerun;

    const bottomHasContent = this.panelWidgets(this._rightBottom).some(
      w => (w as any).model?.length > 0
    );

    if (!leftContentHasOutputs) {
      this._left?.hide();
      if (this._lastLeftVisible !== false) this._split?.setRelativeSizes([0, 1]);
    } else {
      this._left?.show();
      if (this._lastLeftVisible !== true) this._split?.setRelativeSizes([SIDEBAR_RATIO, MAIN_RATIO]);
    }
    this._lastLeftVisible = leftContentHasOutputs;

    // refresh bottom height
    void this._rightBottom.node.offsetHeight;
    if (!bottomHasContent) {
      this._rightBottom?.hide();
      if (this._lastBottomVisible !== false) {
        this._rightSplit?.setRelativeSizes([1, 0]);
      }
    } else {
      this._rightBottom?.show();
      // this.adjustBottomHeight();
      // Measure after layout settles
      requestAnimationFrame(() => this.adjustBottomHeight());
    }
    this._lastBottomVisible = bottomHasContent;
  }

  private static readonly MAX_BOTTOM_PX = 320;

  private adjustBottomHeight(maxPx = AppWidget.MAX_BOTTOM_PX): void {
    if (!this._rightSplit || !this._rightBottom) {
      return;
    }

    // If the split (or bottom) isn’t laid out yet, try again next frame
    this._rightSplit.node.clientHeight;
    const totalH = this._rightSplit.node.clientHeight || 0;

    if (totalH === 0) {
      requestAnimationFrame(() => this.adjustBottomHeight(maxPx));
      return;
    }

    // Needed pixels for the bottom content
    const neededPx = Math.min(
      maxPx,
      Math.max(0, this._rightBottom.node.scrollHeight)
    );
    // Convert to ratios for SplitPanel
    const bottomRatio = Math.max(0, Math.min(neededPx / totalH, 1) * 1.0);
    //const topRatio = 1 - bottomRatio;

    // If the content is tiny, keep a thin but visible rail (e.g., 32px)
    const minBottomPx = 32;
    const minBottomRatio = Math.min(minBottomPx / totalH, 0.05); // up to 5%
    const finalBottom =
      bottomRatio > 0 ? Math.max(bottomRatio, minBottomRatio) : 0;

    this._rightSplit.setRelativeSizes([1 - finalBottom, finalBottom]);

    // Ask Lumino to re-flow just in case (guards against rare race conditions)
    (this._rightSplit as any).update?.();
  }
}
