import { UUID } from '@lumino/coreutils';
import * as Y from 'yjs';
import { YCodeCell, YMarkdownCell, YNotebook, YRawCell } from '@jupyter/ydoc';

const PATCH_MARKER = '__mercuryYdocAttachPatch';

function createYCell(cell, notebook) {
  const ymodel = new Y.Map();
  const ysource = new Y.Text();
  const ymetadata = new Y.Map();

  ymodel.set('source', ysource);
  ymodel.set('metadata', ymetadata);
  ymodel.set('cell_type', cell.cell_type);
  ymodel.set('id', cell.id ?? UUID.uuid4());

  if (cell.cell_type === 'markdown') {
    return new YMarkdownCell(ymodel, ysource, { notebook }, ymetadata);
  }

  if (cell.cell_type === 'code') {
    const youtputs = new Y.Array();
    ymodel.set('outputs', youtputs);
    return new YCodeCell(ymodel, ysource, youtputs, { notebook }, ymetadata);
  }

  return new YRawCell(ymodel, ysource, { notebook }, ymetadata);
}

function applyCellData(ycell, cell) {
  if (typeof ycell.setAttachments === 'function') {
    if (cell.cell_type === 'markdown' && cell.attachments != null) {
      ycell.setAttachments(cell.attachments);
    }
    if (cell.cell_type === 'raw' && cell.attachments) {
      ycell.setAttachments(cell.attachments);
    }
  }

  if (cell.cell_type === 'code') {
    const cCell = cell;
    ycell.execution_count = cCell.execution_count ?? null;
    if (cCell.outputs) {
      ycell.setOutputs(cCell.outputs);
    }
  }

  if (cell.metadata != null) {
    ycell.setMetadata(cell.metadata);
  }
  if (cell.source != null) {
    const source =
      typeof cell.source === 'string' ? cell.source : cell.source.join('');
    ycell.setSource(source);
  }
}

function patchNotebookInsertCells() {
  if (YNotebook.prototype[PATCH_MARKER]) {
    return;
  }

  const originalInsertCells = YNotebook.prototype.insertCells;
  YNotebook.prototype.insertCells = function patchedInsertCells(index, cells) {
    if (!Array.isArray(cells)) {
      return originalInsertCells.call(this, index, cells);
    }

    const yCells = cells.map(cell => {
      const ycell = createYCell(cell, this);
      this._ycellMapping.set(ycell.ymodel, ycell);
      return ycell;
    });

    this.transact(() => {
      this._ycells.insert(index, yCells.map(cell => cell.ymodel));
    });

    yCells.forEach((cell, cellIndex) => {
      applyCellData(cell, cells[cellIndex]);
    });

    return yCells;
  };

  YNotebook.prototype[PATCH_MARKER] = true;
}

function patchTextLengthAccess() {
  const desc = Object.getOwnPropertyDescriptor(Y.Text.prototype, 'length');
  if (!desc || !desc.get) {
    return;
  }
  if (desc.get.__mercuryPatched) {
    return;
  }
  const originalGet = desc.get;
  Object.defineProperty(Y.Text.prototype, 'length', {
    get() {
      if (!this.doc) {
        return 0;
      }
      return originalGet.call(this);
    }
  });
  Object.defineProperty(Y.Text.prototype, '__mercuryPatched', {
    value: true
  });
}

function patchUndoManagerScope() {
  if (Y.UndoManager.prototype.__mercuryPatched) {
    return;
  }
  const originalAddToScope = Y.UndoManager.prototype.addToScope;
  Y.UndoManager.prototype.addToScope = function patchedAddToScope(types) {
    const list = Array.isArray(types) ? types : [types];
    const filtered = list.filter(
      type => type && type.doc && (!this.doc || type.doc === this.doc)
    );
    if (filtered.length === 0) {
      return;
    }
    return originalAddToScope.call(this, filtered);
  };
  Y.UndoManager.prototype.__mercuryPatched = true;
}

patchNotebookInsertCells();
patchTextLengthAccess();
patchUndoManagerScope();
