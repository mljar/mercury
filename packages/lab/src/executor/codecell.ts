import { ISessionContext } from '@jupyterlab/apputils';

import { CodeCell } from '@jupyterlab/cells';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { JSONObject } from '@lumino/coreutils';

import { outputAreaExecute } from './outputArea';

export async function codeCellExecute(
  cell: CodeCell,
  sessionContext: ISessionContext,
  metadata?: JSONObject
): Promise<KernelMessage.IExecuteReplyMsg | void> {
  const model = cell.model;
  const code = model.sharedModel.getSource();
  // if (!code.trim() || !sessionContext.session?.kernel) {
  //   model.sharedModel.transact(() => {
  //     model.clearExecution();
  //   }, false);
  //   return;
  // }
  const cellId = { cellId: model.sharedModel.getId() };
  metadata = {
    ...model.metadata,
    ...metadata,
    ...cellId
  };
  const { recordTiming } = metadata;
  // model.sharedModel.transact(() => {
  //   model.clearExecution();
  //   cell.outputHidden = false;
  // }, false);
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
    // cell.outputArea.future assigned synchronously in `execute`
    if (recordTiming) {
      const recordTimingHook = (msg: KernelMessage.IIOPubMessage) => {
        let label: string;
        switch (msg.header.msg_type) {
          case 'status':
            label = `status.${(msg as KernelMessage.IStatusMsg).content.execution_state}`;
            break;
          case 'execute_input':
            label = 'execute_input';
            break;
          default:
            return true;
        }
        // If the data is missing, estimate it to now
        // Date was added in 5.1: https://jupyter-client.readthedocs.io/en/stable/messaging.html#message-header
        const value = msg.header.date || new Date().toISOString();
        const timingInfo: any = Object.assign(
          {},
          model.getMetadata('execution')
        );
        timingInfo[`iopub.${label}`] = value;
        model.setMetadata('execution', timingInfo);
        return true;
      };
      cell.outputArea.future.registerMessageHook(recordTimingHook);
    } else {
      model.deleteMetadata('execution');
    }
    // Save this execution's future so we can compare in the catch below.
    future = cell.outputArea.future;
    const msg = (await msgPromise)!;
    model.executionCount = msg.content.execution_count;
    if (recordTiming) {
      const timingInfo = Object.assign(
        {},
        model.getMetadata('execution') as any
      );
      const started = msg.metadata.started as string;
      // Started is not in the API, but metadata IPyKernel sends
      if (started) {
        timingInfo['shell.execute_reply.started'] = started;
      }
      // Per above, the 5.0 spec does not assume date, so we estimate is required
      const finished = msg.header.date as string;
      timingInfo['shell.execute_reply'] = finished || new Date().toISOString();
      model.setMetadata('execution', timingInfo);
    }

    return msg;
  } catch (e) {
    // If we started executing, and the cell is still indicating this
    // execution, clear the prompt.
    if (future && !cell.isDisposed && cell.outputArea.future === future) {
      cell.setPrompt('');
      // if (recordTiming && future.isDisposed) {
      //   // Record the time when the cell execution was aborted
      //   const timingInfo: any = Object.assign(
      //     {},
      //     model.getMetadata('execution')
      //   );
      //   timingInfo['execution_failed'] = new Date().toISOString();
      //   model.setMetadata('execution', timingInfo);
      // }
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
