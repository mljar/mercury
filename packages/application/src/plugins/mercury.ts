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
//import { INotebookCellExecutor } from '@mljar/mercury-tokens';

import { MercuryNavbar } from './navbar';
import { IMercuryCellExecutor } from '@mljar/mercury-tokens';
//import { INotebookCellExecutor } from '@jupyterlab/notebook';

/**
 * Open the notebook with Mercury.
 */
export const plugin: JupyterFrontEndPlugin<void> = {
  id: 'mercury-application:opener',
  autoStart: true,
  // requires: [IDocumentManager, INotebookCellExecutor],
  requires: [IDocumentManager, IMercuryCellExecutor],
  optional: [IEditorServices, ISessionContextDialogs, ITranslator],
  activate: (
    app: JupyterFrontEnd,
    documentManager: IDocumentManager,
    executor: IMercuryCellExecutor,
    //executor: INotebookCellExecutor,
    editorServices: IEditorServices | null,
    sessionContextDialogs: ISessionContextDialogs | null,
    translator: ITranslator | null
  ) => {
    console.info('[Mercury] Activating standalone app opener');
    const { mimeTypeService } = editorServices ?? {};
    Promise.all([app.started, app.restored])
      .then(async () => {
        try {
          console.info('[Mercury] App started/restored');
          if (app.serviceManager?.ready) {
            await app.serviceManager.ready;
          }
          const docManagerReady = (documentManager as any)?.ready;
          if (docManagerReady?.then) {
            await docManagerReady;
          }
          const notebookPath = PageConfig.getOption('notebookPath');
          console.info('[Mercury] Opening notebook', { notebookPath });
          const mercuryPanel = documentManager.open(
            notebookPath,
            'Mercury'
          ) as MercuryWidget;

          // Hide default toolbar and mount panel early
          mercuryPanel.toolbar.hide();
          app.shell.add(mercuryPanel, 'mercury');
          console.info('[Mercury] Panel mounted');

          // ------- Navbar: create and mount (separate file) -------
          const baseUrl = PageConfig.getBaseUrl() || '/';

          const urlParams = new URLSearchParams(window.location.search);
          const skipNavbar = urlParams.has('no-navbar');

          if (!skipNavbar) {
            try {
              const navbar = new MercuryNavbar({
                baseUrl,
                title: PageConfig.getOption('title') || 'Mercury',
                apiUrl: `${baseUrl}mercury/api/notebooks`,
                onHeightChange: px => {
                  // add top padding below fixed header
                  const mercuryMainPanel = mercuryPanel.node.querySelector(
                    '.mercury-main-panel'
                  ) as HTMLElement | null;
                  if (mercuryMainPanel) {
                    mercuryMainPanel.style.paddingTop = `${px}px`;
                  } else {
                    const notebookPanel = mercuryPanel.node.querySelector(
                      '.jp-Notebook'
                    ) as HTMLElement | null;
                    if (notebookPanel) {
                      notebookPanel.style.paddingTop = `${px}px`;
                    }
                  }
                }
              });
              await navbar.mount();

              // Clean up if panel is disposed
              mercuryPanel.disposed.connect(() => navbar.destroy());
            } catch (err) {
              console.error('[Mercury] Failed to mount navbar:', err);
            }
          }

          // ---------- Execute notebook cells once kernel is ready ----------
          mercuryPanel.context.ready.then(async () => {
            try {
              console.info('[Mercury] Context ready, preparing execution');
              let session = mercuryPanel.context.sessionContext.session;
              if (!session) {
                const [, changes] = await signalToPromise(
                  mercuryPanel.context.sessionContext.sessionChanged
                );
                session = changes.newValue!;
              }
              let kernelConnection = session?.kernel;
              if (!kernelConnection) {
                const [, changes] = await signalToPromise(session.kernelChanged);
                kernelConnection = changes.newValue!;
              }
              console.info('[Mercury] Kernel resolved', {
                status: kernelConnection?.status,
                connectionStatus: kernelConnection?.connectionStatus
              });

              const executeAll = async () => {
                try {
                  console.info('[Mercury] executeAll invoked', {
                    status: kernelConnection?.status,
                    connectionStatus: kernelConnection?.connectionStatus
                  });
                  if (
                    kernelConnection?.connectionStatus === 'connected' &&
                    kernelConnection?.status === 'idle'
                  ) {
                    kernelConnection.connectionStatusChanged.disconnect(executeAll);
                    kernelConnection.statusChanged.disconnect(executeAll);
                    console.info('[Mercury] Kernel idle/connected, executing cells');

                    const scheduledForExecution = new Set<string>();
                    const notebook = mercuryPanel.context.model;
                    const info = notebook.getMetadata('language_info');
                    const mimetype = info
                      ? mimeTypeService?.getMimeTypeByLanguage(info)
                      : undefined;
                    console.info('[Mercury] Notebook metadata', {
                      languageInfo: info,
                      mimeType: mimetype
                    });

                    const onCellExecutionScheduled = (args: { cell: Cell }) => {
                      scheduledForExecution.add(args.cell.model.id);
                      console.info('[Mercury] Cell scheduled', {
                        id: args.cell.model.id
                      });
                    };

                    const onCellExecuted = (args: { cell: Cell }) => {
                      scheduledForExecution.delete(args.cell.model.id);
                      console.info('[Mercury] Cell executed', {
                        id: args.cell.model.id
                      });
                    };

                    for (const cellItem of (
                      mercuryPanel.content.widgets[0] as AppWidget
                    ).cellWidgets) {
                      if (mimetype) {
                        cellItem.child.model.mimeType = mimetype;
                      }
                      console.info('[Mercury] Running cell', {
                        id: cellItem.child.model.id,
                        type: cellItem.child.model.type
                      });
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
                    console.info('[Mercury] All cells executed');
                  }
                } catch (err) {
                  console.error('[Mercury] Failed while executing cells:', err);
                }
              };

              kernelConnection?.connectionStatusChanged.connect(executeAll);
              kernelConnection?.statusChanged.connect(executeAll);
              executeAll();
            } catch (err) {
              console.error('[Mercury] Failed to prepare kernel execution:', err);
            }
          });
        } catch (err) {
          console.error('[Mercury] Failed during Mercury plugin setup:', err);
        }
      })
      .catch(err => {
        console.error('[Mercury] Failed to activate Mercury plugin:', err);
      });
  }
};
