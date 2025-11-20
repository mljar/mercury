import {
  INotebookModel,
  NotebookPanel,
  StaticNotebook
} from '@jupyterlab/notebook';
import { IEditorMimeTypeService } from '@jupyterlab/codeeditor';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { Panel } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';
import { AppModel } from './app/model';
import { AppWidget } from './app/widget';
import { CellItemWidget } from './app/item/widget';

export class MercuryPanel extends Panel {
  constructor(options: MercuryPanel.IOptions) {
    super();
    this.addClass('jp-Notebook');
    this.addClass('jp-NotebookPanel-notebook');
    this.addClass('mercury-panel');

    this._context = options.context;
    this.rendermime = options.rendermime;
    this.contentFactory = options.contentFactory;
    this.mimeTypeService = options.mimeTypeService;
    this._editorConfig = options.editorConfig;
    this._notebookConfig = options.notebookConfig;

    const appModel = new AppModel({
      context: this._context,
      rendermime: this.rendermime,
      contentFactory: this.contentFactory,
      mimeTypeService: this.mimeTypeService,
      editorConfig: this._editorConfig,
      notebookConfig: this._notebookConfig
    });

    this._appWidget = new AppWidget(appModel);
    this.addWidget(this._appWidget);
  }

  /**
   * Dispose of the resources held by the widget.
   */
  dispose(): void {
    Signal.clearData(this);
    super.dispose();
  }

  /**
   * The rendermime instance for this context.
   */
  readonly rendermime: IRenderMimeRegistry;
  /**
   * A notebook panel content factory.
   */
  readonly contentFactory: NotebookPanel.IContentFactory;
  /**
   * The service used to look up mime types.
   */
  readonly mimeTypeService: IEditorMimeTypeService;
  /**
   * Getter for the notebook cell editor configuration.
   */
  get editorConfig(): StaticNotebook.IEditorConfig {
    return this._editorConfig;
  }
  /**
   * Setter for the notebook cell editor configuration.
   *
   * @param value - The `EditorConfig` of the notebook.
   */
  set editorConfig(value: StaticNotebook.IEditorConfig) {
    this._editorConfig = value;
  }

  get notebookConfig(): StaticNotebook.INotebookConfig {
    return this._notebookConfig;
  }
  set notebookConfig(value: StaticNotebook.INotebookConfig) {
    this._notebookConfig = value;
  }

  get cellWidgets(): Array<CellItemWidget> {
    return this._appWidget.cellWidgets;
  }

  private _appWidget: AppWidget;
  private _context: DocumentRegistry.IContext<INotebookModel>;
  private _editorConfig: StaticNotebook.IEditorConfig;
  private _notebookConfig: StaticNotebook.INotebookConfig;
}

export namespace MercuryPanel {
  export interface IOptions {
    /**
     * The Notebook context.
     */
    context: DocumentRegistry.IContext<INotebookModel>;
    /**
     * The rendermime instance for this context.
     */
    rendermime: IRenderMimeRegistry;
    /**
     * A notebook panel content factory.
     */
    contentFactory: NotebookPanel.IContentFactory;
    /**
     * The service used to look up mime types.
     */
    mimeTypeService: IEditorMimeTypeService;
    /**
     * A config object for cell editors
     */
    editorConfig: StaticNotebook.IEditorConfig;
    /**
     * A config object for notebook widget
     */
    notebookConfig: StaticNotebook.INotebookConfig;
  }
}
