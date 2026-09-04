import { PageConfig, URLExt } from '@jupyterlab/coreutils';

export type SharedRun = {
  runId: number;
  token: string;
  fromIndex: number;
  initialize: boolean;
};

export type SharedSessionCallbacks = {
  onSnapshot: (outputs: Record<string, any[]>) => Promise<boolean> | boolean;
  onRun: (run: SharedRun, clientId: string) => Promise<void>;
  onReady: () => void;
  onOutput: (cellId: string, message: any, reset: boolean) => void;
  onConnectionLost: () => void;
};

export class SharedSessionClient {
  constructor(
    private readonly sessionId: string,
    private readonly callbacks: SharedSessionCallbacks
  ) {}

  async connect(): Promise<void> {
    const wsUrl = URLExt.join(
      PageConfig.getWsUrl(),
      'mercury/api/shared-sessions',
      this.sessionId
    );
    await new Promise<void>((resolve, reject) => {
      const socket = new WebSocket(wsUrl);
      this.socket = socket;
      let connected = false;
      socket.onmessage = event => {
        const message = JSON.parse(String(event.data));
        if (message.type === 'welcome') {
          this.clientId = String(message.client_id);
          connected = true;
          this.messageQueue = this.messageQueue
            .then(async () => {
              const snapshotReady = await this.callbacks.onSnapshot(
                message.outputs ?? {}
              );
              resolve();
              if (message.initialized && snapshotReady) {
                this.callbacks.onReady();
              }
            })
            .catch(error => {
              console.error(
                '[Mercury] Failed to restore shared session snapshot:',
                error
              );
              reject(error);
            });
          return;
        }
        this.messageQueue = this.messageQueue
          .then(() => this.handleMessage(message))
          .catch(error => {
            console.error(
              '[Mercury] Failed to process shared session message:',
              error
            );
          });
      };
      socket.onerror = () => {
        if (!connected) {
          reject(new Error('Could not connect to the shared Mercury session'));
        }
      };
      socket.onclose = () => {
        if (!connected) {
          reject(new Error('Shared Mercury session closed during startup'));
        } else if (!this.disposed) {
          this.callbacks.onConnectionLost();
        }
      };
    });
  }

  requestRun(fromIndex: number, recovery = false): void {
    this.send({ type: 'rerun_request', from_index: fromIndex, recovery });
  }

  dispose(): void {
    this.disposed = true;
    this.socket?.close();
    this.socket = null;
  }

  private async handleRun(message: any): Promise<void> {
    const run: SharedRun = {
      runId: Number(message.run_id),
      token: String(message.token),
      fromIndex: Number(message.from_index),
      initialize: message.initialize === true
    };
    try {
      await this.callbacks.onRun(run, this.clientId);
    } finally {
      this.send({
        type: 'run_complete',
        run_id: run.runId,
        token: run.token
      });
    }
  }

  private async handleMessage(message: any): Promise<void> {
    if (message.type === 'run') {
      await this.handleRun(message);
      return;
    }
    if (message.type === 'output') {
      if (message.executor_client_id !== this.clientId) {
        this.callbacks.onOutput(
          String(message.cell_id),
          message.message,
          message.reset === true
        );
      }
      return;
    }
    if (message.type === 'run_complete') {
      this.callbacks.onReady();
    }
  }

  private send(message: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  private socket: WebSocket | null = null;
  private clientId = '';
  private disposed = false;
  private messageQueue: Promise<void> = Promise.resolve();
}
