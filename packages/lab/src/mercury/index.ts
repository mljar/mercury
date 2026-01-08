import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';

import { NotebookPanel, StaticNotebook } from '@jupyterlab/notebook';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { IEditorServices } from '@jupyterlab/codeeditor';

import { WidgetTracker } from '@jupyterlab/apputils';

import { MercuryWidgetFactory } from './factory';

import { IMercuryTracker, MercuryWidget } from './widget';

import { OpenMercuryButton } from './toolbar/button';

export * from './factory';
export * from './widget';

export const mercury: JupyterFrontEndPlugin<IMercuryTracker> = {
  id: '@mljar/mercury-extension:factory',
  autoStart: true,
  provides: IMercuryTracker,
  requires: [
    NotebookPanel.IContentFactory,
    IEditorServices,
    IRenderMimeRegistry
  ],
  optional: [ILayoutRestorer],
  activate: (
    app: JupyterFrontEnd,
    contentFactory: NotebookPanel.IContentFactory,
    editorServices: IEditorServices,
    rendermime: IRenderMimeRegistry
  ) => {
    console.log('Mercury extension is active.');
    const tracker = new WidgetTracker<MercuryWidget>({
      namespace: '@mljar/mercury-extension:widget-tracker'
    });

    const factory = new MercuryWidgetFactory({
      name: 'Mercury',
      fileTypes: ['notebook'],
      modelName: 'notebook',
      preferKernel: true,
      canStartKernel: true,
      rendermime: rendermime,
      contentFactory,
      editorConfig: StaticNotebook.defaultEditorConfig,
      notebookConfig: StaticNotebook.defaultNotebookConfig,
      mimeTypeService: editorServices.mimeTypeService,
      editorFactoryService: editorServices.factoryService,
      notebookPanel: null,
      iconClass: 'mrc-Icon'
    });

    factory.widgetCreated.connect((sender, widget) => {
      widget.title.iconClass = 'mrc-Icon';

      widget.context.pathChanged.connect(() => {
        void tracker.save(widget);
      });

      void tracker.add(widget);
      widget.update();
      app.commands.notifyCommandChanged();
    });

    app.docRegistry.addWidgetFactory(factory);
    app.docRegistry.addWidgetExtension(
      'Notebook',
      new OpenMercuryButton(app.commands)
    );

    return tracker;
  }
};
