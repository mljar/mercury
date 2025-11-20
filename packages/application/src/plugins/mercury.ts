/* eslint-disable no-inner-declarations */
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISessionContextDialogs } from '@jupyterlab/apputils';
import type { Cell } from '@jupyterlab/cells';
import { IEditorServices } from '@jupyterlab/codeeditor';
import { PageConfig, signalToPromise } from '@jupyterlab/coreutils';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { ITranslator } from '@jupyterlab/translation';
import { PromiseDelegate } from '@lumino/coreutils';
import { type AppWidget, type MercuryWidget } from '@mljar/mercury-extension';
import { IMercuryCellExecutor } from '@mljar/mercury-tokens';

import { MercuryNavbar } from './navbar'; // <-- NEW

/**
 * Open the notebook with Mercury.
 */
export const plugin: JupyterFrontEndPlugin<void> = {
  id: 'mercury-application:opener',
  autoStart: true,
  requires: [IDocumentManager, IMercuryCellExecutor],
  optional: [IEditorServices, ISessionContextDialogs, ITranslator],
  activate: (
    app: JupyterFrontEnd,
    documentManager: IDocumentManager,
    executor: IMercuryCellExecutor,
    editorServices: IEditorServices | null,
    sessionContextDialogs: ISessionContextDialogs | null,
    translator: ITranslator | null
  ) => {
    console.log('My opener 123');

    const { mimeTypeService } = editorServices ?? {};
    Promise.all([app.started, app.restored]).then(async () => {
      const notebookPath = PageConfig.getOption('notebookPath');
      console.log('notebookPath', notebookPath);
      const mercuryPanel = documentManager.open(
        notebookPath,
        'Mercury'
      ) as MercuryWidget;

      // Hide default toolbar and mount panel early
      mercuryPanel.toolbar.hide();
      app.shell.add(mercuryPanel, 'mercury');

      // ------- Navbar: create and mount (separate file) -------
      const baseUrl = PageConfig.getBaseUrl() || '/';
      const navbar = new MercuryNavbar({
        baseUrl,
        title: PageConfig.getOption('title') || 'Mercury',
        apiUrl: `${baseUrl}mercury/api/notebooks`,
        onHeightChange: (px) => {
          // add top padding below fixed header
          const mercuryMainPanel = mercuryPanel.node.querySelector('.mercury-main-panel') as HTMLElement | null;
          if (mercuryMainPanel) {
            mercuryMainPanel.style.paddingTop = `${px}px`;
          } else {
            const notebookPanel = mercuryPanel.node.querySelector('.jp-Notebook') as HTMLElement | null;
            if (notebookPanel) notebookPanel.style.paddingTop = `${px}px`;
          }
        }
      });
      await navbar.mount();

      // Clean up if panel is disposed
      mercuryPanel.disposed.connect(() => navbar.destroy());

      // ---------- Execute notebook cells once kernel is ready ----------
      mercuryPanel.context.ready.then(async () => {
        let session = mercuryPanel.context.sessionContext.session;
        console.log('session', session);
        if (!session) {
          const [, changes] = await signalToPromise(
            mercuryPanel.context.sessionContext.sessionChanged
          );
          session = changes.newValue!;
        }
        console.log('session2', session);
        let kernelConnection = session?.kernel;
        if (!kernelConnection) {
          const [, changes] = await signalToPromise(session.kernelChanged);
          kernelConnection = changes.newValue!;
        }

        console.log(kernelConnection);
        const executeAll = async () => {
          if (
            kernelConnection?.connectionStatus === 'connected' &&
            kernelConnection?.status === 'idle'
          ) {
            kernelConnection.connectionStatusChanged.disconnect(executeAll);
            kernelConnection.statusChanged.disconnect(executeAll);

            const scheduledForExecution = new Set<string>();
            const notebook = mercuryPanel.context.model;
            const info = notebook.getMetadata('language_info');
            const mimetype = info
              ? mimeTypeService?.getMimeTypeByLanguage(info)
              : undefined;

            const onCellExecutionScheduled = (args: { cell: Cell }) => {
              scheduledForExecution.add(args.cell.model.id);
            };

            const onCellExecuted = (args: { cell: Cell }) => {
              scheduledForExecution.delete(args.cell.model.id);
            };

            for (const cellItem of (
              mercuryPanel.content.widgets[0] as AppWidget
            ).cellWidgets) {
              if (mimetype) {
                cellItem.child.model.mimeType = mimetype;
              }
              await executor.runCell({
                cell: cellItem.child,
                notebook,
                notebookConfig: mercuryPanel.content.notebookConfig,
                onCellExecuted: onCellExecuted,
                onCellExecutionScheduled: onCellExecutionScheduled,
                sessionContext: mercuryPanel.context.sessionContext,
                sessionDialogs: sessionContextDialogs ?? undefined,
                translator: translator ?? undefined
              });
            }

            const waitForExecution = new PromiseDelegate<void>();
            const pollExecution = setInterval(() => {
              if (scheduledForExecution.size === 0) {
                clearInterval(pollExecution);
                waitForExecution.resolve();
              }
            }, 500);

            await waitForExecution.promise;
          }
        };

        kernelConnection?.connectionStatusChanged.connect(executeAll);
        kernelConnection?.statusChanged.connect(executeAll);
        executeAll();
      });
    });
  }
};
