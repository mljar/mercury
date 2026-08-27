import type { KernelMessage } from '@jupyterlab/services';

import { isStopExecutionError, isStopExecutionReply } from '../executor/stop';

function executeReply(content: object): KernelMessage.IExecuteReplyMsg {
  return { content } as KernelMessage.IExecuteReplyMsg;
}

describe('StopExecution detection', () => {
  it('recognizes a StopExecution kernel reply', () => {
    const reply = executeReply({
      status: 'error',
      ename: 'StopExecution',
      evalue: '',
      traceback: []
    });

    expect(isStopExecutionReply(reply)).toBe(true);
  });

  it('does not treat ordinary errors or successful replies as StopExecution', () => {
    const ordinaryError = executeReply({
      status: 'error',
      ename: 'ValueError',
      evalue: 'invalid value',
      traceback: []
    });
    const successfulReply = executeReply({
      status: 'ok',
      execution_count: 1,
      payload: [],
      user_expressions: {}
    });

    expect(isStopExecutionReply(ordinaryError)).toBe(false);
    expect(isStopExecutionReply(successfulReply)).toBe(false);
    expect(isStopExecutionReply(undefined)).toBe(false);
  });

  it('recognizes the KernelError produced for StopExecution', () => {
    expect(isStopExecutionError({ errorName: 'StopExecution' })).toBe(true);
    expect(isStopExecutionError({ errorName: 'ValueError' })).toBe(false);
    expect(isStopExecutionError(undefined)).toBe(false);
  });
});
