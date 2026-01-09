interface BusyIndicatorOptions {
  container: HTMLElement;
  position?: 'top-right' | 'top-left';
  showDelayMs?: number;   // default 1000
  hideDelayMs?: number;   // default 500
}

export class BusyIndicator {
  private static stylesInserted = false;

  private root: HTMLDivElement;
  private dot: HTMLSpanElement;
  private btn: HTMLButtonElement;

  private busyCount = 0;
  private visible = false;

  private showTimer: number | null = null;
  private hideTimer: number | null = null;

  private showDelayMs: number;
  private hideDelayMs: number;

  constructor(opts: BusyIndicatorOptions) {
    if (!opts?.container) throw new Error('BusyIndicator: container required');
    BusyIndicator.ensureStyles();

    this.showDelayMs = opts.showDelayMs ?? 1000;
    this.hideDelayMs = opts.hideDelayMs ?? 500;

    this.root = document.createElement('div');
    this.root.className = 'mbi-root';
    this.root.style.position = 'absolute';
    this.root.style.top = '8px';
    this.root.style.right = '8px';

    this.root.setAttribute('role', 'status');
    this.root.setAttribute('aria-live', 'polite');

    this.dot = document.createElement('span');
    this.dot.className = 'mbi-dot';
    this.dot.title = 'Computing…';
    this.root.appendChild(this.dot);

    this.btn = document.createElement('button');
    this.btn.className = 'mbi-stop-btn';
    this.btn.type = 'button';
    this.btn.textContent = 'Stop';
    this.btn.title = 'Interrupt kernel';
    this.btn.addEventListener('click', () => {
      this.root.dispatchEvent(new CustomEvent('mbi:interrupt'));
    });
    this.root.appendChild(this.btn);

    this.root.style.display = 'none';
    opts.container.appendChild(this.root);
  }

  /** One unit of work started */
  begin() {
    this.busyCount++;

    // If we were about to hide, cancel that (work resumed).
    if (this.hideTimer !== null) {
      window.clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }

    // If already visible, no need to (re)show.
    if (this.visible) return;

    // If show already armed, keep it armed.
    if (this.showTimer !== null) return;

    // Arm delayed show.
    this.showTimer = window.setTimeout(() => {
      this.showTimer = null;

      // Only show if still busy.
      if (this.busyCount > 0 && !this.visible) {
        this.visible = true;
        this.root.style.display = 'inline-flex';
      }
    }, this.showDelayMs) as unknown as number;
  }

  /** One unit of work finished */
  finish() {
    // Decrement but never go below 0 (defensive).
    this.busyCount = Math.max(0, this.busyCount - 1);

    // Still busy? Then do nothing.
    if (this.busyCount > 0) return;

    // No longer busy => cancel pending show (if it hasn't shown yet).
    if (this.showTimer !== null) {
      window.clearTimeout(this.showTimer);
      this.showTimer = null;
    }

    // If not visible, nothing to hide.
    if (!this.visible) return;

    // Debounced hide: hide only if we remain at 0 long enough.
    if (this.hideTimer !== null) return;
    this.hideTimer = window.setTimeout(() => {
      this.hideTimer = null;

      // Only hide if still not busy.
      if (this.busyCount === 0 && this.visible) {
        this.visible = false;
        this.root.style.display = 'none';
      }
    }, this.hideDelayMs) as unknown as number;
  }

  error() {
    // Treat error as "finished one unit"
    this.finish();
  }

  /** Optional helper if you want a hard reset */
  reset() {
    this.busyCount = 0;
    if (this.showTimer !== null) window.clearTimeout(this.showTimer);
    if (this.hideTimer !== null) window.clearTimeout(this.hideTimer);
    this.showTimer = null;
    this.hideTimer = null;
    this.visible = false;
    this.root.style.display = 'none';
  }

  dispose() {
    if (this.showTimer !== null) window.clearTimeout(this.showTimer);
    if (this.hideTimer !== null) window.clearTimeout(this.hideTimer);
    this.showTimer = null;
    this.hideTimer = null;
    this.root.remove();
  }

  get element(): HTMLElement {
    return this.root;
  }

  private static ensureStyles() {
    if (BusyIndicator.stylesInserted) return;
    BusyIndicator.stylesInserted = true;

    const style = document.createElement('style');
    style.textContent = `
:root {
  --mbi-green1: #38d36e;
  --mbi-green2: #19b96c;
  --mbi-green-soft: rgba(56, 211, 110, 0.18);
  --mbi-pill-bg: #f2f3f5;
  --mbi-pill-border: color-mix(in srgb, var(--jp-border-color2, #e6e8eb) 80%, transparent);
  --mbi-text: var(--jp-ui-font-color1, #24292f);
}
.mbi-root {
  z-index: 1500;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--mbi-pill-bg);
  border: 1px solid var(--mbi-pill-border);
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  color: var(--mbi-text);
  display: inline-flex;
}
.mbi-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(180deg, var(--mbi-green1) 0%, var(--mbi-green2) 100%);
  box-shadow: 0 0 0 6px var(--mbi-green-soft);
  animation: mbi-pulse 2.2s ease-in-out infinite;
}
@media (prefers-reduced-motion: reduce) {
  .mbi-dot { animation: none; }
}
@keyframes mbi-pulse {
  0%, 100% { transform: scale(1); opacity: .7; }
  50% { transform: scale(1.15); opacity: 1; }
}
.mbi-stop-btn {
  background: transparent;
  color: var(--mbi-text);
  padding: 4px 10px;
  font-weight: 600;
  font-size: 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 120ms ease, background 120ms ease, transform 100ms ease, opacity 120ms ease;
}
.mbi-stop-btn:hover {
  border-color: color-mix(in srgb, var(--mbi-text) 20%, transparent);
  background: rgba(0, 0, 0, 0.04);
}
.mbi-stop-btn:active {
  transform: translateY(1px) scale(0.98);
  opacity: 0.9;
}
`;
    document.head.appendChild(style);
  }
}
