// src/navbar.ts
type NotebookItem = {
  name: string;
  description?: string;
  href: string;
  slug: string;
  thumbnail_bg?: string;
  thumbnail_text?: string;
  thumbnail_text_color?: string;
};

export type MercuryNavbarOptions = {
  /** Base URL from PageConfig.getBaseUrl() */
  baseUrl: string;
  /** Title from PageConfig.getOption('title') */
  title: string;
   /** Label for the notebooks dropdown button */
  notebooksButtonLabel?: string;
  /** URL that returns the notebooks JSON array */
  apiUrl: string;
  /** Callback fired when the header height is known/changes (e.g., mount) */
  onHeightChange?: (px: number) => void;
  /** Where to insert the header; defaults to document.body */
  attachTo?: HTMLElement;
};

export class MercuryNavbar {
  private opts: MercuryNavbarOptions;
  private header?: HTMLElement;
  private styleEl?: HTMLStyleElement;
  private btn?: HTMLButtonElement;
  private menu?: HTMLDivElement;
  private menuList?: HTMLDivElement;
  private caret?: SVGSVGElement;
  private notebooks: NotebookItem[] = [];
  private menuOpen = false;
  private clickAway?: (e: MouseEvent) => void;
  private keyHandler?: (e: KeyboardEvent) => void;

  constructor(opts: MercuryNavbarOptions) {
    this.opts = { ...opts, attachTo: opts.attachTo ?? document.body };
  }

  async mount(): Promise<void> {
    this.injectStyles();
    this.buildHeader();
    this.opts.attachTo!.insertBefore(this.header!, this.opts.attachTo!.firstChild);
    document.body.classList.add('mercury-has-header');

    // Notify consumer about height so they can add padding to content below
    const height = this.header!.getBoundingClientRect().height || 52;
    this.opts.onHeightChange?.(height);

    await this.loadNotebooks();
    this.bindGlobalHandlers();
  }

  destroy(): void {
    this.unbindGlobalHandlers();
    document.body.classList.remove('mercury-has-header');
    this.header?.remove();
    this.styleEl?.remove();
  }

  /** ------- private helpers below ------- */

  private injectStyles() {
    const style = document.createElement('style');
    style.id = 'mrc-header-style';
    style.textContent = `
        :root { color-scheme: light; }
        .mrc-hidden { display: none; }
  
        /* Header */
        .mrc-hdr {
          position: fixed; top: 0; left: 0; right: 0; z-index: 10000;
          background: var(--mercury-topbar-background-color);
          border-bottom: 1px solid var(--mercury-topbar-border-color);
          box-shadow: none;
        }
        .mrc-hdr-inner {
          width: 100%;
          margin: 0;
          display: flex; align-items: center; justify-content: space-between;
          box-sizing: border-box;
          padding: .7rem 1rem;
        }
        .mrc-brand-wrap {
          display: flex; align-items: center; gap: .6rem;
          min-width: 0;
        }
        .mrc-brand {
          font-weight: 750; letter-spacing: -.01em;
          color: var(--mercury-topbar-text-color);
          font-size: clamp(16px, 2vw, 20px);
          text-decoration: none;
          font-family: var(--mercury-heading-font-family);
        }
        .mrc-brand:hover { text-decoration: underline; }
  
        /* Button */
        .mrc-btn {
          display: inline-flex; align-items: center; gap: .5rem;
          border: 1px solid var(--mercury-topbar-border-color);
          background: transparent;
          color: var(--mercury-topbar-text-color);
          padding: .45rem .75rem; font-size: 13px; border-radius: .5rem;
          transition: background-color .15s ease, border-color .15s ease, transform .15s ease;
          cursor: pointer;
          box-shadow: none;
          text-shadow: none;
        }
        .mrc-btn[disabled] { opacity: .7; cursor: progress; }
        .mrc-btn:hover {
          text-decoration: none;
          background: color-mix(in srgb, var(--mercury-topbar-text-color) 10%, transparent);
          border-color: color-mix(in srgb, var(--mercury-topbar-text-color) 18%, var(--mercury-topbar-border-color));
        }
        .mrc-btn:focus,
        .mrc-btn:focus-visible {
          outline: none;
          border-color: var(--mercury-focus-border-color);
          box-shadow: none;
        }
        .mrc-caret { transition: transform .15s ease; }
  
        /* Menu (dropdown) */
        .mrc-menu{
          position:absolute; right:0; margin-top:.5rem; width:22rem; max-height:28rem; overflow:auto;
          border:1px solid var(--mercury-border-color); border-radius:1rem;
          background: var(--mercury-card-background-color);
          box-shadow: var(--mercury-shadow-lg);
        }
        .mrc-menu-list{ padding:.4rem; }
        .mrc-menu-item{
          display:flex; align-items:center; gap:.7rem;
          padding:.6rem .65rem; border-radius:.75rem;
          color:var(--mercury-text-color); font-size:14px;
          text-decoration:none;
          transition: background-color .12s ease, transform .12s ease;
          font-family: var(--mercury-font-family);
        }
        .mrc-menu-item:hover{ background:var(--mercury-hover-background-color); text-decoration:none; }
        .mrc-menu-item:active{ transform: translateY(0.5px); }
        .mrc-menu-thumb{
          width:36px; height:28px; border-radius:.6rem;
          display:grid; place-items:center; font-weight:700; line-height:1;
          box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--mercury-border-color) 60%, transparent);
        }
      `;
    document.head.appendChild(style);
    this.styleEl = style;
  }

  private buildHeader() {
    const header = document.createElement('header');
    header.className = 'mrc-hdr';
    header.setAttribute('role', 'banner');

    const inner = document.createElement('div');
    inner.className = 'mrc-hdr-inner';

    const brandWrap = document.createElement('div');
    brandWrap.className = 'mrc-brand-wrap';

    // Brand
    const brand = document.createElement('a');
    brand.className = 'mrc-brand';
    brand.href = this.opts.baseUrl || '/';
    brand.textContent = this.opts.title || 'Mercury';
    brandWrap.appendChild(brand);

    // Right side
    const rightWrap = document.createElement('div');
    rightWrap.style.position = 'relative';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mrc-btn';
    btn.id = 'mrcNbBtn';
    btn.setAttribute('aria-haspopup', 'menu');
    btn.setAttribute('aria-expanded', 'false');
    btn.textContent = this.opts.notebooksButtonLabel || 'Notebooks';

    const caret = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    caret.setAttribute('class', 'mrc-caret');
    caret.setAttribute('width', '16');
    caret.setAttribute('height', '16');
    caret.setAttribute('viewBox', '0 0 20 20');
    caret.setAttribute('fill', 'currentColor');
    caret.setAttribute('aria-hidden', 'true');
    caret.innerHTML = `<path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 0 1 1.08 1.04l-4.25 4.25a.75.75 0 0 1-1.06 0L5.21 8.27a.75.75 0 0 1 .02-1.06z" clip-rule="evenodd"/>`;
    btn.appendChild(caret);

    const menu = document.createElement('div');
    menu.id = 'mrcNbMenu';
    menu.className = 'mrc-menu mrc-hidden';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', 'Notebook list');

    const menuList = document.createElement('div');
    menuList.id = 'mrcNbMenuList';
    menuList.className = 'mrc-menu-list';
    menuList.setAttribute('role', 'none');

    menu.appendChild(menuList);
    rightWrap.appendChild(btn);
    rightWrap.appendChild(menu);

    inner.appendChild(brandWrap);
    inner.appendChild(rightWrap);
    header.appendChild(inner);

    // Events
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (!this.notebooks.length) return;
      this.setMenu(!this.menuOpen);
    });

    this.header = header;
    this.btn = btn;
    this.menu = menu;
    this.menuList = menuList;
    this.caret = caret;
  }

  private bindGlobalHandlers() {
    this.clickAway = (e: MouseEvent) => {
      if (!this.menuOpen || !this.menu || !this.btn) return;
      const t = e.target as Node;
      if (!this.menu.contains(t) && !this.btn.contains(t)) this.setMenu(false);
    };
    this.keyHandler = (e: KeyboardEvent) => {
      if (String(e.key).toLowerCase() === 'escape') this.setMenu(false);
    };
    document.addEventListener('click', this.clickAway!);
    document.addEventListener('keydown', this.keyHandler!);
  }

  private unbindGlobalHandlers() {
    if (this.clickAway) document.removeEventListener('click', this.clickAway);
    if (this.keyHandler) document.removeEventListener('keydown', this.keyHandler);
  }

  private setMenu(open: boolean) {
    if (!this.menu || !this.btn || !this.caret) return;
    this.menu.classList.toggle('mrc-hidden', !open);
    this.btn.setAttribute('aria-expanded', String(open));
    this.caret.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
    this.menuOpen = open;
  }

  private sizeThumb(el: HTMLElement) {
    const txt = (el.textContent || '').trim();
    let fs = '1.0rem';
    if (txt.length > 6) fs = '0.4rem';
    else if (txt.length > 4) fs = '0.6rem';
    else if (txt.length > 2) fs = '0.8rem';
    el.style.fontSize = fs;
  }

  private renderMenu(items: NotebookItem[]) {
    if (!this.menuList) return;
    const frag = document.createDocumentFragment();
    for (const nb of items) {
      const a = document.createElement('a');
      a.className = 'mrc-menu-item';
      a.href = nb.slug || '#';
      a.setAttribute('role', 'menuitem');

      const t = document.createElement('div');
      t.className = 'mrc-menu-thumb';
      t.style.background = nb.thumbnail_bg || '#f1f5f9';
      t.style.color = nb.thumbnail_text_color || '#0f172a';
      t.textContent = nb.thumbnail_text || '📒';
      this.sizeThumb(t);

      const span = document.createElement('span');
      span.textContent = nb.name || 'Notebook';

      a.appendChild(t);
      a.appendChild(span);
      frag.appendChild(a);
    }
    this.menuList.innerHTML = '';
    this.menuList.appendChild(frag);
  }

  private async loadNotebooks() {
    if (!this.btn || !this.menu) return;
    try {
      this.btn.disabled = true;
      const resp = await fetch(this.opts.apiUrl, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' }
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = (await resp.json()) as NotebookItem[] | undefined;
      this.notebooks = Array.isArray(data) ? data : [];
      if (this.notebooks.length === 0) {
        this.btn.style.display = 'none';
        this.menu.remove();
        return;
      }
      this.renderMenu(this.notebooks);
    } catch (err) {
      console.warn('[Mercury] Failed to load notebooks menu:', err);
      this.btn.style.display = 'none';
      this.menu?.remove();
    } finally {
      this.btn.disabled = false;
    }
  }
}
