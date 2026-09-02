const SHARED_SESSION_ICON = `
  <svg viewBox="0 0 20 20" width="17" height="17" fill="none" aria-hidden="true">
    <path d="M7.25 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2.5 16.5v-1.25A3.75 3.75 0 0 1 6.25 11.5h2A3.75 3.75 0 0 1 12 15.25v1.25M13 9a2.5 2.5 0 1 0 0-5M13.5 11.5h.25a3.75 3.75 0 0 1 3.75 3.75v1.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
`;

export class SharedSessionIndicator {
  mount(): void {
    if (this.root) {
      return;
    }

    this.injectStyles();

    const root = document.createElement('aside');
    root.className = 'mrc-shared-session';
    root.setAttribute('aria-label', 'Shared session information');

    const card = document.createElement('div');
    card.className = 'mrc-shared-session-card';
    card.id = 'mrcSharedSessionDetails';

    const heading = document.createElement('div');
    heading.className = 'mrc-shared-session-heading';
    heading.innerHTML = `${SHARED_SESSION_ICON}<strong>Shared session</strong>`;

    const description = document.createElement('p');
    description.textContent =
      'Everyone viewing this app shares the same Python session. Widget changes and results are synchronized across browsers.';

    const minimize = document.createElement('button');
    minimize.type = 'button';
    minimize.className = 'mrc-shared-session-minimize';
    minimize.textContent = 'Minimize';
    minimize.setAttribute('aria-controls', card.id);
    minimize.addEventListener('click', this.minimize);

    card.appendChild(heading);
    card.appendChild(description);
    card.appendChild(minimize);

    const compact = document.createElement('button');
    compact.type = 'button';
    compact.className = 'mrc-shared-session-compact';
    compact.setAttribute('aria-controls', card.id);
    compact.setAttribute('aria-expanded', 'false');
    compact.setAttribute('aria-label', 'Show shared session information');
    compact.innerHTML = `${SHARED_SESSION_ICON}<span>Shared session</span>`;
    compact.addEventListener('click', this.expand);

    root.appendChild(card);
    root.appendChild(compact);
    document.body.appendChild(root);

    this.root = root;
    this.compact = compact;
    this.minimizeButton = minimize;
  }

  destroy(): void {
    this.compact?.removeEventListener('click', this.expand);
    this.minimizeButton?.removeEventListener('click', this.minimize);
    this.root?.remove();
    this.styleEl?.remove();
    this.root = null;
    this.compact = null;
    this.minimizeButton = null;
    this.styleEl = null;
  }

  private injectStyles(): void {
    const style = document.createElement('style');
    style.id = 'mrc-shared-session-style';
    style.textContent = `
      .mrc-shared-session {
        position: fixed;
        right: 16px;
        bottom: calc(16px + env(safe-area-inset-bottom, 0px));
        z-index: 10001;
        font-family: var(--mercury-font-family, system-ui, sans-serif);
      }
      .mrc-shared-session-card {
        width: min(300px, calc(100vw - 32px));
        box-sizing: border-box;
        padding: 14px;
        border: 1px solid var(--mercury-border-color, #d1d5db);
        border-radius: 12px;
        background: var(--mercury-card-background-color, #fff);
        color: var(--mercury-text-color, #111827);
        box-shadow: var(--mercury-shadow-lg, 0 10px 28px rgb(0 0 0 / 16%));
        font-size: 13px;
        line-height: 1.45;
      }
      .mrc-shared-session-heading {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
      }
      .mrc-shared-session-card p {
        margin: 8px 0 10px;
      }
      .mrc-shared-session-minimize {
        display: block;
        margin-left: auto;
        padding: 3px 0;
        border: 0;
        background: transparent;
        color: var(--mercury-muted-text-color, #4b5563);
        font: inherit;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }
      .mrc-shared-session-minimize:hover {
        color: var(--mercury-text-color, #111827);
        text-decoration: underline;
      }
      .mrc-shared-session-compact {
        display: none;
        align-items: center;
        gap: 7px;
        padding: 8px 12px;
        border: 1px solid var(--mercury-border-color, #d1d5db);
        border-radius: 999px;
        background: var(--mercury-card-background-color, #fff);
        color: var(--mercury-text-color, #111827);
        box-shadow: var(--mercury-shadow-md, 0 4px 14px rgb(0 0 0 / 12%));
        font: inherit;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.2;
        cursor: pointer;
      }
      .mrc-shared-session-compact:hover {
        background: var(--mercury-hover-background-color, #f3f4f6);
      }
      .mrc-shared-session-minimize:focus-visible,
      .mrc-shared-session-compact:focus-visible {
        outline: 2px solid var(--mercury-focus-border-color, #2563eb);
        outline-offset: 2px;
      }
      .mrc-shared-session.is-minimized .mrc-shared-session-card {
        display: none;
      }
      .mrc-shared-session.is-minimized .mrc-shared-session-compact {
        display: inline-flex;
      }
      @media (max-width: 480px) {
        .mrc-shared-session {
          right: 12px;
          bottom: calc(12px + env(safe-area-inset-bottom, 0px));
        }
        .mrc-shared-session-card {
          width: min(300px, calc(100vw - 24px));
        }
      }
    `;
    document.head.appendChild(style);
    this.styleEl = style;
  }

  private minimize = (): void => {
    this.root?.classList.add('is-minimized');
    this.compact?.setAttribute('aria-expanded', 'false');
    this.compact?.focus();
  };

  private expand = (): void => {
    this.root?.classList.remove('is-minimized');
    this.compact?.setAttribute('aria-expanded', 'true');
    this.minimizeButton?.focus();
  };

  private root: HTMLElement | null = null;
  private compact: HTMLButtonElement | null = null;
  private minimizeButton: HTMLButtonElement | null = null;
  private styleEl: HTMLStyleElement | null = null;
}
