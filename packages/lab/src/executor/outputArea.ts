import { ISessionContext } from '@jupyterlab/apputils';
import { OutputArea } from '@jupyterlab/outputarea';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { JSONObject } from '@lumino/coreutils';

const FUTURE_DESCRIPTOR = Object.getOwnPropertyDescriptor(
  OutputArea.prototype,
  'future'
);
const NO_FLICKER_PATCHED = Symbol('no-flicker-patched');
const NO_FLICKER_RUN_TOKEN = Symbol('no-flicker-run-token');

type NoFlickerOptions = {
  /** Log debug messages to console */
  debug?: boolean;
  /**
   * If true: when execution finishes with no visible outputs, clear anyway at idle.
   * Default false (keep old output; usually best UX + no flicker).
   */
  clearOnSilentIdle?: boolean;
  /**
   * Treat these as "visible" triggers for the first-clear (advanced).
   * Default false.
   */
  treatClearOutputAsVisible?: boolean;
  treatUpdateDisplayDataAsVisible?: boolean;
};

function assertOutputAreaInternals(output: any, debug: boolean) {
  const missing: string[] = [];
  if (typeof output._onIOPub !== 'function') missing.push('_onIOPub');
  if (typeof output._onExecuteReply !== 'function') missing.push('_onExecuteReply');
  if (typeof output.onInputRequest !== 'function') missing.push('onInputRequest');
  if (!('model' in output)) missing.push('model');
  if (!('widgets' in output)) missing.push('widgets');
  if (typeof output._clear !== 'function') missing.push('_clear');
  if (!('outputLengthChanged' in output)) missing.push('outputLengthChanged');
  if (!('_maxNumberOutputs' in output)) missing.push('_maxNumberOutputs');

  if (missing.length) {
    const msg =
      `[no-flicker] OutputArea internals changed/missing: ${missing.join(', ')}. ` +
      `Your JupyterLab version likely changed OutputArea private API.`;
    if (debug) console.error(msg, output);
    throw new Error(msg);
  }
}

function isStatusMsgContent(content: any): content is { execution_state: string } {
  return (
    typeof content === 'object' &&
    content !== null &&
    'execution_state' in content
  );
}

function isVisibleMsgType(
  msgType: string,
  opts: NoFlickerOptions
): boolean {
  if (
    msgType === 'execute_result' ||
    msgType === 'display_data' ||
    msgType === 'stream' ||
    msgType === 'error'
  ) {
    return true;
  }
  if (opts.treatClearOutputAsVisible && msgType === 'clear_output') return true;
  if (opts.treatUpdateDisplayDataAsVisible && msgType === 'update_display_data') return true;
  return false;
}

export async function outputAreaExecute(
  code: string,
  output: OutputArea,
  sessionContext: ISessionContext,
  metadata?: JSONObject,
  options: NoFlickerOptions = {}
): Promise<KernelMessage.IExecuteReplyMsg | undefined> {
  const opts: Required<NoFlickerOptions> = {
    debug: options.debug ?? false,
    clearOnSilentIdle: options.clearOnSilentIdle ?? false,
    treatClearOutputAsVisible: options.treatClearOutputAsVisible ?? false,
    treatUpdateDisplayDataAsVisible: options.treatUpdateDisplayDataAsVisible ?? false
  };

  const log = (...args: any[]) => {
    if (opts.debug) console.log('[no-flicker]', ...args);
  };

  log('outputAreaExecute code:', code);

  // stop_on_error override
  let stopOnError = true;
  const tags = (metadata as any)?.tags;
  if (Array.isArray(tags) && tags.includes('raises-exception')) {
    stopOnError = false;
  }

  const content: KernelMessage.IExecuteRequestMsg['content'] = {
    code,
    stop_on_error: stopOnError
  };

  const kernel = sessionContext.session?.kernel;
  if (!kernel) throw new Error('Session has no kernel.');

  // Per-execution token (protect against interleaving old/new futures)
  const runToken = Symbol('run');
  (output as any)[NO_FLICKER_RUN_TOKEN] = runToken;

  const future = kernel.requestExecute(content, false, metadata);

  // Patch OutputArea.future setter only once per OutputArea instance
  if (!(output as any)[NO_FLICKER_PATCHED]) {
    log('Patching OutputArea.future setter (once per OutputArea instance)');

    Object.defineProperty(output, 'future', {
      configurable: true, // ✅ improvement #1
      enumerable: true,
      get() {
        if (FUTURE_DESCRIPTOR?.get) {
          return FUTURE_DESCRIPTOR.get.call(this);
        }
        return (this as any)._future;
      },
      set(
        value: Kernel.IShellFuture<
          KernelMessage.IExecuteRequestMsg,
          KernelMessage.IExecuteReplyMsg
        >
      ) {
        const debug = (options as any)?.debug ?? false; // may be undefined here; safe
        // ✅ improvement #2: assert internals early with a useful error
        assertOutputAreaInternals(this, !!debug);

        if (this.model.isDisposed) throw Error('Model is disposed');
        if (this._future === value) return;

        const oldFuture = this._future;
        if (oldFuture) void oldFuture.done.finally(() => oldFuture.dispose());
        this._future = value;

        value.done
          .finally(() => {
            this._pendingInput = false;
          })
          .catch(() => {
            /* no-op */
          });

        // INTENTIONALLY no clear here -> no flicker

        const myToken = (this as any)[NO_FLICKER_RUN_TOKEN];

        // ✅ improvement #3: simpler state than counters (first visible only)
        let seenVisible = false;
        let cleared = false;

        const originalOnIOPub = (msg: KernelMessage.IIOPubMessage) => {
          this._onIOPub(msg);
        };

        value.onIOPub = (msg: KernelMessage.IIOPubMessage) => {
          // Ignore messages from an old run
          if ((this as any)[NO_FLICKER_RUN_TOKEN] !== myToken) return;

          const msgType = msg.header.msg_type;

          try {
            const visible = isVisibleMsgType(msgType, opts);

            if (!seenVisible && visible) {
              seenVisible = true;
              if (!cleared) {
                log(`CLEAR model (reason=first-visible, msgType=${msgType})`);
                this.model.clear();

                if (this.widgets.length) {
                  this._clear();
                  this.outputLengthChanged.emit(
                    Math.min(this.model.length, this._maxNumberOutputs)
                  );
                }

                cleared = true;
              }
            }

            // ✅ improvement #4: configurable silent-idle behavior
            if (
              opts.clearOnSilentIdle &&
              !cleared &&
              msgType === 'status' &&
              isStatusMsgContent(msg.content) &&
              msg.content.execution_state === 'idle' &&
              !seenVisible
            ) {
              log('CLEAR model (reason=silent-idle)');
              this.model.clear();

              if (this.widgets.length) {
                this._clear();
                this.outputLengthChanged.emit(
                  Math.min(this.model.length, this._maxNumberOutputs)
                );
              }

              cleared = true;
            }
          } catch (e) {
            console.log('[no-flicker] handler error:', e);
          }

          originalOnIOPub(msg);
        };

        value.onReply = (msg: KernelMessage.IExecuteReplyMsg) => {
          if ((this as any)[NO_FLICKER_RUN_TOKEN] !== myToken) return;
          this._onExecuteReply(msg);
        };

        value.onStdin = (msg: KernelMessage.IStdinMessage) => {
          if ((this as any)[NO_FLICKER_RUN_TOKEN] !== myToken) return;
          if (KernelMessage.isInputRequestMsg(msg)) {
            this.onInputRequest(msg, value);
          }
        };
      }
    });

    (output as any)[NO_FLICKER_PATCHED] = true;
  }

  // Attach: no immediate clear because patched setter omits "clear here"
  (output as any).future = future;

  return future.done;
}
