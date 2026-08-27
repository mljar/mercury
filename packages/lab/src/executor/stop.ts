import type { KernelMessage } from '@jupyterlab/services';

const STOP_EXECUTION_ERROR_NAME = 'StopExecution';

export function isStopExecutionReply(
  reply: KernelMessage.IExecuteReplyMsg | void
): boolean {
  return (
    reply?.content.status === 'error' &&
    reply.content.ename === STOP_EXECUTION_ERROR_NAME
  );
}

export function isStopExecutionError(
  error: { errorName?: string } | null | undefined
): boolean {
  return error?.errorName === STOP_EXECUTION_ERROR_NAME;
}
