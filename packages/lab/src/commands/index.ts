import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISessionContext, ISessionContextDialogs } from '@jupyterlab/apputils';

import {
  INotebookTracker,
  Notebook,
  NotebookActions
} from '@jupyterlab/notebook';

import { ITranslator } from '@jupyterlab/translation';

function runAllBelow(
  notebook: Notebook,
  sessionContext?: ISessionContext,
  sessionDialogs?: ISessionContextDialogs,
  translator?: ITranslator
) {
  if (!notebook.model || !notebook.activeCell) {
    return Promise.resolve(false);
  }
  const cellIndex = notebook.activeCellIndex;
  notebook.activeCellIndex = notebook.activeCellIndex + 1;
  const promise = NotebookActions.runAllBelow(
    notebook,
    sessionContext,
    sessionDialogs,
    translator
  );
  promise.finally(() => {
    notebook.activeCellIndex = cellIndex;
  });
}
export const commands: JupyterFrontEndPlugin<void> = {
  id: '@mljar/mercury-extension:commands',
  description: 'Commands used in Mercury',
  autoStart: true,
  requires: [INotebookTracker],
  activate: (app: JupyterFrontEnd, notebookTracker: INotebookTracker) => {
    const commandID = '@mljar/mercury-execute-below';
    app.commands.addCommand(commandID, {
      label: 'Execute cells below',
      execute: () => {
        const nb = notebookTracker.currentWidget;
        if (nb) {
          runAllBelow(nb.content, nb.context.sessionContext);
        }
      }
    });
  }
};
