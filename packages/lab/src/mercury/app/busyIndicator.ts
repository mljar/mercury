// busyIndicator.ts
// Minimal, friendly top-right busy indicator for App View.
//
// - Hidden when idle
// - After > showDelayMs (default 1000ms): shows a light-gray pill
//   with a single pulsing green dot + "Stop" button
// - Button emits 'mbi:interrupt' event (host should interrupt the kernel)
// - Soft, calm animation and subtle gray background

interface BusyIndicatorOptions {
  container: HTMLElement;                 // e.g. this._rightTop.node
  position?: 'top-right' | 'top-left';    // default: 'top-right'
  showDelayMs?: number;                   // default: 1000
}

export class BusyIndicator {
  private static stylesInserted = false;
  private root: HTMLDivElement;
  private dot: HTMLSpanElement;
  private btn: HTMLButtonElement;
  private visible = false;
  private armedTimer: number | null = null;
  private showDelayMs: number;

  constructor(opts: BusyIndicatorOptions) {
    if (!opts?.container) throw new Error('BusyIndicator: container required');
    BusyIndicator.ensureStyles();

    this.showDelayMs = opts.showDelayMs ?? 1000;

    // Ensure container can anchor absolute child
    const cs = window.getComputedStyle(opts.container);
    if (cs.position === 'static') opts.container.style.position = 'relative';

    // Root pill
    this.root = document.createElement('div');
    this.root.className = 'mbi-root';
    this.root.style.position = 'absolute';
    this.root.style.top = '8px';
    if ((opts.position ?? 'top-right') === 'top-right') {
      this.root.style.right = '8px';
    } else {
      this.root.style.left = '8px';
    }

    this.root.setAttribute('role', 'status');
    this.root.setAttribute('aria-live', 'polite');

    // Green pulsing dot
    this.dot = document.createElement('span');
    this.dot.className = 'mbi-dot';
    this.dot.title = 'Computing…';
    this.root.appendChild(this.dot);

    // Stop button (borderless by default; subtle outline on hover)
    this.btn = document.createElement('button');
    this.btn.className = 'mbi-stop-btn';
    this.btn.type = 'button';
    this.btn.textContent = 'Stop';
    this.btn.title = 'Interrupt kernel';
    this.btn.addEventListener('click', () => {
      this.root.dispatchEvent(new CustomEvent('mbi:interrupt'));
    });
    this.root.appendChild(this.btn);

    // Start hidden
    this.root.style.display = 'none';
    opts.container.appendChild(this.root);
  }

  /** Arm a delayed show */
  begin() {
    if (this.visible || this.armedTimer !== null) return;
    this.armedTimer = window.setTimeout(() => {
      this.armedTimer = null;
      this.visible = true;
      this.root.style.display = 'inline-flex';
    }, this.showDelayMs) as unknown as number;
  }

  /** Hide immediately / cancel delayed show */
  finish() {
    if (this.armedTimer !== null) {
      window.clearTimeout(this.armedTimer);
      this.armedTimer = null;
    }
    if (this.visible) {
      this.visible = false;
      this.root.style.display = 'none';
    }
  }

  error() {
    this.finish();
  }

  dispose() {
    if (this.armedTimer !== null) {
      window.clearTimeout(this.armedTimer);
      this.armedTimer = null;
    }
    this.root.remove();
  }

  get element(): HTMLElement {
    return this.root;
  }

  // Inject CSS once
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

/* Light gray pill */
.mbi-root {
  z-index: 5;
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

/* Calm pulsing dot (run-all green gradient) */
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

/* Friendly Stop button */
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
