type HealthState = 'ok' | 'down';

export class ServerHealthMonitor {
  private _baseUrl: string;
  private _state: HealthState = 'ok';
  private _timer: number | null = null;
  private _ws: WebSocket | null = null;
  private _onDown: () => void;

  constructor(baseUrl: string, onDown: () => void, onUp: () => void) {
    this._baseUrl = baseUrl;
    this._onDown = onDown;

    // Listen to browser offline/online too
    window.addEventListener('offline', () => this._flipDown('offline'));

    // Also watch the event bus websocket (closing indicates backend is gone)
    this._openEventsWS();
  }

  dispose() {
    if (this._timer !== null) {
      window.clearTimeout(this._timer);
      this._timer = null;
    }
    this._ws?.close();
    this._ws = null;
    window.removeEventListener('offline', this._flipDown as any);
  }

  private _openEventsWS() {
    try {
      const wsUrl = new URL('api/events/subscribe', this._baseUrl);
      // Convert http(s) → ws(s)
      wsUrl.protocol = wsUrl.protocol.replace('http', 'ws');

      this._ws = new WebSocket(wsUrl.toString());
      this._ws.onopen = () => {};
      this._ws.onmessage = () => {};
      this._ws.onclose = () => this._flipDown('ws-close');
      this._ws.onerror = () => this._flipDown('ws-error');
    } catch {
      // If constructing WS throws, treat as down and rely on pings
      this._flipDown('ws-build');
    }
  }

  private _flipDown(_reason: string) {
    if (this._state === 'down') {
      return;
    }
    this._state = 'down';
    this._onDown();
  }
}
