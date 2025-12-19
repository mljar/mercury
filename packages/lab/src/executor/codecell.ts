import { ISessionContext } from '@jupyterlab/apputils';

import { CodeCell } from '@jupyterlab/cells';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { JSONObject } from '@lumino/coreutils';

import { outputAreaExecute } from './outputArea';

export async function codeCellExecute(
  cell: CodeCell,
  sessionContext: ISessionContext,
  metadata?: JSONObject,
  p0?: { deletedCells: string[] }
): Promise<KernelMessage.IExecuteReplyMsg | void> {
  const model = cell.model;
  const code = model.sharedModel.getSource();

  if (!code.trim() || !sessionContext.session?.kernel) {
    model.sharedModel.transact(() => {
      model.clearExecution();
      cell.outputArea.model.clear();
    }, false);
    return;
  }
  const cellId = { cellId: model.sharedModel.getId() };
  metadata = {
    ...model.metadata,
    ...metadata,
    ...cellId
  };

  if (code !== '') {
    cell.setPrompt('*');
  }

  model.trusted = true;
  let future:
    | Kernel.IFuture<
        KernelMessage.IExecuteRequestMsg,
        KernelMessage.IExecuteReplyMsg
      >
    | undefined;
  try {
    const msgPromise = outputAreaExecute(
      code,
      cell.outputArea,
      sessionContext,
      metadata
    );
    model.deleteMetadata('execution');

    // Save this execution's future so we can compare in the catch below.
    future = cell.outputArea.future;
    let msg: KernelMessage.IExecuteReplyMsg | undefined;

    try {
      msg = await msgPromise;
    } catch (e: any) {
      if (String(e?.message || e).includes('Canceled future')) {
        // normalne anulowanie (re-run, dispose, widget update)
        return;
      }
      throw e;
    }

    if (!msg) {
      return;
    }

    model.executionCount = msg.content.execution_count;
    return msg;
  } catch (e) {
    // If we started executing, and the cell is still indicating this
    // execution, clear the prompt.
    if (future && !cell.isDisposed && cell.outputArea.future === future) {
      cell.setPrompt('');
    }
    throw e;
  }
}

export async function executeSilently(
  sessionContext: ISessionContext,
  code: string
): Promise<void> {
  const kernel = sessionContext.session?.kernel;
  if (!kernel) {
    return;
  }
  const future = kernel.requestExecute({
    code,
    silent: true, // <- no iopub execute_input, etc.
    store_history: false, // <- not added to history
    stop_on_error: false,
    allow_stdin: false
  });
  try {
    await future.done;
  } catch {
    // swallow — we don't want housekeeping to break UX
  }
}

export async function executeWidgetsManagerClearValues(
  sessionContext: ISessionContext
): Promise<void> {
  const clearCode = `
try:
    from mercury.manager import WidgetsManager
except Exception:
    WidgetsManager = None
if WidgetsManager is not None:
    WidgetsManager.clear()
`;

  return executeSilently(sessionContext, clearCode);
}
