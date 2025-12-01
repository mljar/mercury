import {
  // JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { INotebookCellExecutor, runCell } from '@jupyterlab/notebook';

import { NotebookCellExecutor } from './notebookcell';

import { IMercuryCellExecutor } from '@mljar/mercury-tokens';

export const mercuryCellExecutor: JupyterFrontEndPlugin<IMercuryCellExecutor> =
  {
    id: '@mljar/mercury-extension:mercury-cell-executor',
    autoStart: true,
    provides: IMercuryCellExecutor,
    activate: () => {
      return new NotebookCellExecutor();
    }
  };

export const defaultCellExecutor: JupyterFrontEndPlugin<INotebookCellExecutor> =
  {
    id: '@mljar/mercury-extension:default-cell-executor',
    description: 'Provides the notebook cell executor.',
    autoStart: true,
    provides: INotebookCellExecutor,
    activate: (): INotebookCellExecutor => {
      return Object.freeze({ runCell });
    }
  };
