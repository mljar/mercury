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
          if (app.serviceManager?.ready) {
            await app.serviceManager.ready;
          }
          const docManagerReady = (documentManager as any)?.ready;
          if (docManagerReady?.then) {
            await docManagerReady;
          }
          const notebookPath = PageConfig.getOption('notebookPath');
          const mercuryPanel = documentManager.open(
            notebookPath,
            'Mercury'
          ) as MercuryWidget;

          // Hide default toolbar and mount panel early
          mercuryPanel.toolbar.hide();
          app.shell.add(mercuryPanel, 'mercury');

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
              const waitForKernelReady = async (kc: typeof kernelConnection) => {
                if (!kc) {
                  return;
                }
                if (
                  kc.connectionStatus === 'connected' &&
                  kc.status === 'idle'
                ) {
                  return;
                }
                await new Promise<void>(resolve => {
                  const maybeResolve = () => {
                    if (
                      kc.connectionStatus === 'connected' &&
                      kc.status === 'idle'
                    ) {
                      kc.connectionStatusChanged.disconnect(maybeResolve);
                      kc.statusChanged.disconnect(maybeResolve);
                      resolve();
                    }
                  };
                  kc.connectionStatusChanged.connect(maybeResolve);
                  kc.statusChanged.connect(maybeResolve);
                  maybeResolve();
                });
              };
              const waitForCellWidgets = async (
                appWidget: AppWidget,
                totalCells: number,
                timeoutMs = 10000,
                intervalMs = 200
              ) => {
                if (totalCells <= 0) {
                  return;
                }
                const startedAt = Date.now();
                while (
                  appWidget.cellWidgets.length === 0 &&
                  Date.now() - startedAt < timeoutMs
                ) {
                  await new Promise(resolve => setTimeout(resolve, intervalMs));
                }
              };
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
              await waitForKernelReady(kernelConnection);

              const executeAll = async () => {
                try {
                  console.info('[Mercury] Executing cells');

                  const scheduledForExecution = new Set<string>();
                  const notebook = mercuryPanel.context.model;
                  const appWidget = mercuryPanel.content.widgets[0] as AppWidget;
                  const totalCells = notebook.cells.length;
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

                  if (appWidget.cellWidgets.length === 0 && totalCells > 0) {
                    await waitForCellWidgets(appWidget, totalCells);
                  }

                  for (const cellItem of appWidget.cellWidgets) {
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
                  console.info('[Mercury] All cells executed');
                } catch (err) {
                  console.error('[Mercury] Failed while executing cells:', err);
                } finally {
                  const hideLoader = (window as any).hideMercuryLoader;
                  if (typeof hideLoader === 'function') {
                    hideLoader();
                  }
                }
              };

              await executeAll();
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
