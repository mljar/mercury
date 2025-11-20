import { Token } from '@lumino/coreutils';
import { INotebookCellExecutor } from '@jupyterlab/notebook';

/**
 * Extended Mercury executor interface
 */
export interface IMercuryCellExecutor extends INotebookCellExecutor {}

/**
 * Shared token for Mercury cell executor
 */
export const IMercuryCellExecutor = new Token<IMercuryCellExecutor>(
  '@mljar/mercury-extension:MercuryCellExecutor',
  'Mercury cell executor'
);
