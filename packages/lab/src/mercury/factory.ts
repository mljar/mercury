import { DocumentRegistry, ABCWidgetFactory } from '@jupyterlab/docregistry';

import {
  INotebookModel,
  NotebookPanel,
  StaticNotebook
} from '@jupyterlab/notebook';

import {
  IEditorFactoryService,
  IEditorMimeTypeService
} from '@jupyterlab/codeeditor';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { MercuryWidget } from './widget';

import { MercuryPanel } from './panel';
// import { LabIcon } from '@jupyterlab/ui-components';

export class MercuryWidgetFactory extends ABCWidgetFactory<
  MercuryWidget,
  INotebookModel
> {
  constructor(options: MercuryWidgetFactory.IOptions<MercuryWidget>) {
    super(options);
    this.rendermime = options.rendermime;
    this.contentFactory =
      options.contentFactory ||
      new NotebookPanel.ContentFactory({
        editorFactory: options.editorFactoryService.newInlineEditor
      });
    this.mimeTypeService = options.mimeTypeService;
    this._editorConfig =
      options.editorConfig || StaticNotebook.defaultEditorConfig;
    this._notebookConfig =
      options.notebookConfig || StaticNotebook.defaultNotebookConfig;
  }

  /*
   * The rendermime instance.
   */
  readonly rendermime: IRenderMimeRegistry;

  /**
   * The content factory used by the widget factory.
   */
  readonly contentFactory: NotebookPanel.IContentFactory;

  /**
   * The service used to look up mime types.
   */
  readonly mimeTypeService: IEditorMimeTypeService;

  /**
   * A configuration object for cell editor settings.
   */
  get editorConfig(): StaticNotebook.IEditorConfig {
    return this._editorConfig;
  }
  set editorConfig(value: StaticNotebook.IEditorConfig) {
    this._editorConfig = value;
  }

  /**
   * A configuration object for notebook settings.
   */
  get notebookConfig(): StaticNotebook.INotebookConfig {
    return this._notebookConfig;
  }
  set notebookConfig(value: StaticNotebook.INotebookConfig) {
    this._notebookConfig = value;
  }

  protected createNewWidget(
    context: DocumentRegistry.IContext<INotebookModel>,
    source?: MercuryWidget
  ): MercuryWidget {
    const options = {
      context: context,
      rendermime: source
        ? source.content.rendermime
        : this.rendermime.clone({ resolver: context.urlResolver }),
      contentFactory: this.contentFactory,
      mimeTypeService: this.mimeTypeService,
      editorConfig: source ? source.content.editorConfig : this._editorConfig,
      notebookConfig: source
        ? source.content.notebookConfig
        : this._notebookConfig
    };
    return new MercuryWidget(context, new MercuryPanel(options));
  }

  private _editorConfig: StaticNotebook.IEditorConfig;
  private _notebookConfig: StaticNotebook.INotebookConfig;
}

export namespace MercuryWidgetFactory {
  export interface IOptions<T extends MercuryWidget>
    extends DocumentRegistry.IWidgetFactoryOptions<T> {
    /*
     * A rendermime instance.
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
     * The service used to create default panel.
     */
    editorFactoryService: IEditorFactoryService;

    /**
     * The notebook cell editor configuration.
     */
    editorConfig?: StaticNotebook.IEditorConfig;

    /**
     * The notebook configuration.
     */
    notebookConfig?: StaticNotebook.INotebookConfig;
    notebookPanel: NotebookPanel | null;

    iconClass?: string;
    iconLabel?: string;
  }
}
