const THEME_CSS_VARIABLE_MAP = {
  font_family: '--mercury-font-family',
  heading_font_family: '--mercury-heading-font-family',
  font_size: '--mercury-font-size',
  font_weight: '--mercury-font-weight',
  heading_font_weight: '--mercury-heading-font-weight',
  text_color: '--mercury-text-color',
  muted_text_color: '--mercury-muted-text-color',
  background_color: '--mercury-background-color',
  surface_color: '--mercury-surface-color',
  content_background_color: '--mercury-content-background-color',
  panel_bg: '--mercury-panel-bg',
  card_background_color: '--mercury-card-background-color',
  border_color: '--mercury-border-color',
  border_radius: '--mercury-border-radius',
  primary_color: '--mercury-primary-color',
  accent_color: '--mercury-accent-color',
  focus_border_color: '--mercury-focus-border-color',
  hover_background_color: '--mercury-hover-background-color',
  selected_background_color: '--mercury-selected-background-color',
  sidebar_background_color: '--mercury-sidebar-background-color',
  sidebar_text_color: '--mercury-sidebar-text-color',
  sidebar_title_color: '--mercury-sidebar-title-color',
  sidebar_shadow: '--mercury-sidebar-shadow',
  sidebar_backdrop_color: '--mercury-sidebar-backdrop-color',
  topbar_background_color: '--mercury-topbar-background-color',
  topbar_text_color: '--mercury-topbar-text-color',
  topbar_border_color: '--mercury-topbar-border-color',
  footer_background_color: '--mercury-footer-background-color',
  footer_text_color: '--mercury-footer-text-color',
  footer_border_color: '--mercury-footer-border-color',
  loader_background_color: '--mercury-loader-background-color',
  loader_card_background_color: '--mercury-loader-card-background-color',
  loader_text_color: '--mercury-loader-text-color',
  loader_border_color: '--mercury-loader-border-color',
  loader_icon_color: '--mercury-loader-icon-color',
  loader_steam_color: '--mercury-loader-steam-color',
  toast_background_color: '--mercury-toast-background-color',
  toast_text_color: '--mercury-toast-text-color',
  toast_error_border_color: '--mercury-toast-error-border-color',
  run_button_background: '--mercury-run-button-background',
  run_button_background_hover: '--mercury-run-button-background-hover',
  run_button_text_color: '--mercury-run-button-text-color',
  run_button_focus_color: '--mercury-run-button-focus-color',
  shadow_sm: '--mercury-shadow-sm',
  shadow_md: '--mercury-shadow-md',
  shadow_lg: '--mercury-shadow-lg'
} as const;

export type ThemeCssKey = keyof typeof THEME_CSS_VARIABLE_MAP;

export interface IPageConfigLike {
  baseUrl?: string;
  showCode?: boolean;
  theme?: Partial<Record<ThemeCssKey, string>>;
}

export function getPageConfig(): IPageConfigLike {
  const el = document.getElementById('jupyter-config-data');
  if (!el) {
    throw new Error('Page config script not found');
  }

  try {
    return JSON.parse(el.textContent || '{}') as IPageConfigLike;
  } catch (err) {
    console.warn('Invalid page config JSON:', err);
    return {};
  }
}

export async function fetchTheme(
  baseUrl = ''
): Promise<IPageConfigLike['theme']> {
  const prefix = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  const url = `${prefix}mercury/api/theme`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Theme API error: ${response.status}`);
    }
    return (await response.json()) as IPageConfigLike['theme'];
  } catch (err) {
    console.warn('Failed to fetch theme overrides', err);
    return {};
  }
}

export function applyThemeCssVars(theme?: IPageConfigLike['theme']): void {
  if (!theme) {
    return;
  }

  const rootStyle = document.documentElement.style;

  for (const [key, cssVar] of Object.entries(THEME_CSS_VARIABLE_MAP) as Array<
    [ThemeCssKey, (typeof THEME_CSS_VARIABLE_MAP)[ThemeCssKey]]
  >) {
    const value = theme[key]?.trim();
    if (!value) {
      continue;
    }
    rootStyle.setProperty(cssVar, value);
  }
}

export async function loadThemeCssVars(baseUrl = ''): Promise<void> {
  const theme = await fetchTheme(baseUrl);
  applyThemeCssVars(theme);
}
