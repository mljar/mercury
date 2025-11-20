import { CodeCell } from '@jupyterlab/cells';
import { IOutputAreaModel } from '@jupyterlab/outputarea';
import { Widget } from '@lumino/widgets';

export class OutputStamper {
  //private readonly LOG_PREFIX = '[CellIDStampPlugin]';
  private readonly ID_ATTR = 'data-cell-id';

  // Dedupe console logs for elements we’ve already stamped
  private loggedSetAttr = new WeakSet<HTMLElement>();

  // Track per-cell listeners + observers for cleanup
  private cellTeardown = new WeakMap<CodeCell, () => void>();

  private setAttr(el: HTMLElement | null | undefined, id: string, label: string) {
    if (!el) return;
    const current = el.getAttribute(this.ID_ATTR);
    if (current !== id) {
      el.setAttribute(this.ID_ATTR, id);
      if (!this.loggedSetAttr.has(el)) {
        // Keep logs sparse and readable
        // eslint-disable-next-line no-console
        //console.log(`${this.LOG_PREFIX} set ${this.ID_ATTR} on ${label}`, { id, el });
        this.loggedSetAttr.add(el);
      }
    }
  }

  private deepStamp(root: HTMLElement, id: string) {
    this.setAttr(root, id, 'node');
    // Most common renderer wrappers in JupyterLab (add more as needed)
    const items = root.querySelectorAll<HTMLElement>(
      [
        '.jp-OutputArea-output',
        '.jp-RenderedText',
        '.jp-RenderedHTMLCommon',
        '.jp-RenderedImage',
        '.jp-RenderedJSON',
        '.jp-RenderedMarkdown',
        '.jp-RenderedSVG'
      ].join(', ')
    );
    items.forEach((el, idx) => this.setAttr(el, id, `output descendant #${idx}`));
  }

  /**
   * One-shot stamp of what currently exists in the output area.
   */
  private stampOnce(cell: CodeCell): void {
    const id = cell.model?.id;
    if (!id) return;

    const area = cell.outputArea as any;
    const node = (area?.node as HTMLElement) ?? null;

    if (node) this.setAttr(node, id, 'output area');

    // SAFE widgets fast-path
    let widgets: readonly Widget[] | null = null;
    try {
      // Accessing the getter can throw if output area internals aren't ready
      widgets = (area?.widgets as readonly Widget[]) ?? null;
    } catch {
      widgets = null;
    }
    if (widgets && widgets.length) {
      widgets.forEach((w, idx) => {
        const el = (w?.node as HTMLElement) ?? null;
        if (el) {
          this.setAttr(el, id, `output item (widget) #${idx}`);
          this.deepStamp(el, id);
        }
      });
    }

    if (node) {
      node.querySelectorAll<HTMLElement>('.jp-OutputArea-output').forEach((el, idx) => {
        this.setAttr(el, id, `output item (query) #${idx}`);
        this.deepStamp(el, id);
      });
    }
  }

  /**
   * Attach live stamping to a CodeCell:
   *  - Re-stamps on output model changes and on output area re-layouts.
   *  - Observes DOM mutations inside the output area to stamp late wrappers.
   */
  attach(cell: CodeCell): void {
    if (this.cellTeardown.has(cell)) return;
    const id = cell.model?.id;
    if (!id) return;

    const area = cell.outputArea as any;
    const areaNode = (area?.node as HTMLElement) ?? null;
    const model: IOutputAreaModel | undefined = area?.model as IOutputAreaModel | undefined;

    // Delay initial stamp until the cell has rendered
    void cell.ready.then(() => this.stampOnce(cell));
    // (optional) also try immediately just in case it's already ready
    this.stampOnce(cell);

    const rafStamp = () => requestAnimationFrame(() => this.stampOnce(cell));

    // model.changed -> restamp
    let modelDisposer: (() => void) | undefined;
    if (model && 'changed' in model) {
      const onModelChanged = () => rafStamp();
      model.changed.connect(onModelChanged);
      modelDisposer = () => model.changed.disconnect(onModelChanged);
    }

    // observe DOM changes
    let observerDisposer: (() => void) | undefined;
    if (areaNode) {
      const mo = new MutationObserver(() => rafStamp());
      mo.observe(areaNode, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
      observerDisposer = () => mo.disconnect();
    }

    const teardown = () => { try { modelDisposer?.(); } catch { } try { observerDisposer?.(); } catch { }; this.cellTeardown.delete(cell); };
    this.cellTeardown.set(cell, teardown);

    const onDisposed = () => teardown();
    cell.disposed.connect(onDisposed);
    const prev = teardown;
    this.cellTeardown.set(cell, () => { try { cell.disposed.disconnect(onDisposed); } catch { } prev(); });
  }

  /**
   * Detach live stamping from a CodeCell (cleanup listeners/observers).
   */
  detach(cell: CodeCell): void {
    const teardown = this.cellTeardown.get(cell);
    if (teardown) {
      teardown();
    }
  }
}
