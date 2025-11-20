import { ISessionContext } from '@jupyterlab/apputils';

import { OutputArea } from '@jupyterlab/outputarea';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { JSONObject } from '@lumino/coreutils';

export async function outputAreaExecute(
  code: string,
  output: OutputArea,
  sessionContext: ISessionContext,
  metadata?: JSONObject
): Promise<KernelMessage.IExecuteReplyMsg | undefined> {
  // Override the default for `stop_on_error`.
  let stopOnError = true;
  if (
    metadata &&
    Array.isArray(metadata.tags) &&
    metadata.tags.indexOf('raises-exception') !== -1
  ) {
    stopOnError = false;
  }
  const content: KernelMessage.IExecuteRequestMsg['content'] = {
    code,
    stop_on_error: stopOnError
  };

  const kernel = sessionContext.session?.kernel;
  if (!kernel) {
    throw new Error('Session has no kernel.');
  }
  const future = kernel.requestExecute(content, false, metadata);

  Object.defineProperty(output, 'executeCounter', {
    value: 0,
    writable: true
  });

  if (!Object.prototype.hasOwnProperty.call(output, 'monkey')) {
    Object.defineProperty(output, 'future', {
      set(
        value: Kernel.IShellFuture<
          KernelMessage.IExecuteRequestMsg,
          KernelMessage.IExecuteReplyMsg
        >
      ) {
        // Bail if the model is disposed.
        if (this.model.isDisposed) {
          throw Error('Model is disposed');
        }
        if (this._future === value) {
          return;
        }
        if (this._future) {
          this._future.dispose();
        }
        this._future = value;

        value.done
          .finally(() => {
            this._pendingInput = false;
          })
          .catch(() => {
            // No-op, required because `finally` re-raises any rejections,
            // even if caught on the `done` promise level before.
          });

        //
        // clear here
        //
        // this.model.clear();
        // // Make sure there were no input widgets.
        // if (this.widgets.length) {
        //   this._clear();
        //   this.outputLengthChanged.emit(
        //     Math.min(this.model.length, this._maxNumberOutputs)
        //   );
        // }
        function isStatusMsgContent(
          content: any
        ): content is { execution_state: string } {
          return (
            typeof content === 'object' &&
            content !== null &&
            'execution_state' in content
          );
        }

        const f = (msg: KernelMessage.IIOPubMessage) => {
          const msgType = msg.header.msg_type;
          try {
            switch (msgType) {
              case 'execute_result':
              case 'display_data':
              case 'stream':
              case 'error':
                this.executeCounter += 1;
              // eslint-disable-next-line no-fallthrough
              default:
                break;
            }
            if (
              this.executeCounter === 1 ||
              (msgType === 'status' &&
                isStatusMsgContent(msg.content) &&
                msg.content.execution_state === 'idle' &&
                this.executeCounter === 0)
            ) {
              this.model.clear();
              // Make sure there were no input widgets.
              if (this.widgets.length) {
                this._clear();
                this.outputLengthChanged.emit(
                  Math.min(this.model.length, this._maxNumberOutputs)
                );
              }
              this.executeCounter += 1;
            }
          } catch (e) {
            console.log(e);
          }
          this._onIOPub(msg);
        };
        // Handle published messages.
        //value.onIOPub = this._onIOPub;
        value.onIOPub = f;

        // Handle the execute reply.
        value.onReply = this._onExecuteReply;

        // Handle stdin.
        value.onStdin = msg => {
          if (KernelMessage.isInputRequestMsg(msg)) {
            this.onInputRequest(msg, value);
          }
        };
      }
    });

    Object.defineProperty(output, 'monkey', {
      value: 42,
      writable: false
    });
  }

  output.future = future;

  return future.done;
}
