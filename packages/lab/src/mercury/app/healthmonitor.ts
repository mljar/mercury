import { ServerConnection } from '@jupyterlab/services';

type HealthState = 'ok' | 'down';

function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  return p.finally(() => clearTimeout(t));
}

function pingServer(baseUrl: string, timeoutMs = 3000): Promise<boolean> {
  // Try a very cheap endpoint first; fall back to /api/sessions.
  const url = new URL('api/sessions', baseUrl).toString();
  return withTimeout(fetch(url, { cache: 'no-store' }), timeoutMs)
    .then(r => r.ok)
    .catch(() => false);
}

export class ServerHealthMonitor {
  private _baseUrl: string;
  private _state: HealthState = 'ok';
  private _failStreak = 0;
  private _timer: number | null = null;
  private _ws: WebSocket | null = null;
  private _onDown: () => void;
  private _onUp: () => void;

  constructor(baseUrl: string, onDown: () => void, onUp: () => void) {
    this._baseUrl = baseUrl;
    this._onDown = onDown;
    this._onUp = onUp;

    // Listen to browser offline/online too
    window.addEventListener('offline', () => this._flipDown('offline'));
    window.addEventListener('online', () => this._retrySoon());

    // Optional: observe unhandled JLab network errors
    window.addEventListener('unhandledrejection', (ev: PromiseRejectionEvent) => {
      const reason: any = ev.reason;
      // JLab services throws ServerConnection.NetworkError or TypeError on network fail
      if (
        reason instanceof (ServerConnection as any).NetworkError ||
        reason?.name === 'TypeError'
      ) {
        this._flipDown('unhandledrejection');
      }
    });

    // Also watch the event bus websocket (closing indicates backend is gone)
    this._openEventsWS();

    this._schedule(); // start ping loop
  }

  dispose() {
    if (this._timer !== null) {
      window.clearTimeout(this._timer);
      this._timer = null;
    }
    this._ws?.close();
    this._ws = null;
    window.removeEventListener('offline', this._flipDown as any);
    window.removeEventListener('online', this._retrySoon as any);
  }

  private _openEventsWS() {
    try {
      const wsUrl = new URL('api/events/subscribe', this._baseUrl);
      // Convert http(s) → ws(s)
      wsUrl.protocol = wsUrl.protocol.replace('http', 'ws');

      this._ws = new WebSocket(wsUrl.toString());
      this._ws.onopen = () => {/* noop */ };
      this._ws.onmessage = () => {/* noop */ };
      this._ws.onclose = () => this._flipDown('ws-close');
      this._ws.onerror = () => this._flipDown('ws-error');
    } catch {
      // If constructing WS throws, treat as down and rely on pings
      this._flipDown('ws-build');
    }
  }

  private _schedule() {
    const backoffMs = Math.min(30000, 1000 * Math.pow(2, this._failStreak)); // 1s → 2s → 4s ... max 30s
    this._timer = window.setTimeout(() => this._tick(), backoffMs);
  }

  private async _tick() {
    const ok = await pingServer(this._baseUrl);
    if (ok) {
      this._failStreak = 0;
      this._flipUp();
    } else {
      this._failStreak++;
      this._flipDown('ping-fail');
    }
    this._schedule();
  }

  private _retrySoon() {
    this._failStreak = 0;
    if (this._timer !== null) {
      window.clearTimeout(this._timer);
      this._timer = null;
    }
    this._schedule();
  }

  private _flipDown(_reason: string) {
    if (this._state === 'down') return;
    this._state = 'down';
    this._onDown();
  }

  private _flipUp() {
    if (this._state === 'ok') return;
    this._state = 'ok';
    this._onUp();
  }
}
