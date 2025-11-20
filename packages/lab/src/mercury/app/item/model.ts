import { Widget } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

export class CellItemModel {
  constructor(options: CellItemModel.IOptions) {
    this._cellId = options.cellId;
    this._sidebar = options.sidebar;
    this._bottom = options.bottom;
  }

  get cellId(): string {
    return this._cellId;
  }
  get sidebar(): boolean {
    return this._sidebar;
  }
  get bottom(): boolean {
    return this._bottom;
  }
  dispose() {
    Signal.clearData(this);
  }
  private _cellId = '';
  // place cell in the sidebar or not
  private _sidebar = false;
  // place cell in the bottom or not
  private _bottom = false;
}

export namespace CellItemModel {
  export interface IOptions {
    cellId: string;
    cellWidget: Widget;
    /**
     * Place cell in the sidebar.
     */
    sidebar: boolean;
    /**
     * Place cell in the bottom.
     */
    bottom: boolean;
  }
}
