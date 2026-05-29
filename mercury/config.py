import os
from pathlib import Path
from urllib.parse import urlparse

import toml


CONFIG_ENV_VAR = "MERCURY_CONFIG_DIR"


DEFAULT_THEME = {
    "font_family": "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "font_url": "",
    "heading_font_family": "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "font_size": "14px",
    "font_weight": "normal",
    "heading_font_weight": "800",
    "text_color": "#0f172a",
    "muted_text_color": "#475569",
    "background_color": "#f9fafb",
    "surface_color": "#ffffff",
    "content_background_color": "#ffffff",
    "panel_bg": "#ffffff",
    "panel_bg_hover": "#f8fafc",
    "panel_bg_hover_2": "#eef2f7",
    "widget_background_color": "#ffffff",
    "card_background_color": "#ffffff",
    "border_color": "#d0d7de",
    "border_radius": "6px",
    "border_radius_sm": "4px",
    "border_radius_lg": "10px",
    "primary_color": "#007bff",
    "accent_color": "#4c7cf0",
    "focus_border_color": "#4c7cf0",
    "hover_background_color": "#f8fafc",
    "selected_background_color": "#eef3ff",
    "button_primary_text": "#ffffff",
    "button_shadow": "0 1px 2px rgba(0,0,0,0.06)",
    "button_shadow_hover": "0 2px 6px rgba(0,0,0,0.08)",
    "danger_color": "#dc3545",
    "success_color": "#19b96c",
    "warning_color": "#f59e0b",
    "slider_track_color": "#e0e0e0",
    "sidebar_background_color": "#f8f9fa",
    "sidebar_text_color": "#0f172a",
    "sidebar_title_color": "#0f172a",
    "sidebar_shadow": "2px 0 12px rgba(0,0,0,0.18)",
    "sidebar_backdrop_color": "rgba(15,23,42,0.22)",
    "topbar_background_color": "#0b0b0c",
    "topbar_text_color": "#f3f4f6",
    "topbar_border_color": "rgba(255,255,255,0.08)",
    "footer_background_color": "#ffffff",
    "footer_text_color": "#6b7280",
    "footer_border_color": "#e5e7eb",
    "loader_background_color": "rgba(249,250,251,0.85)",
    "loader_card_background_color": "#ffffff",
    "loader_text_color": "#475569",
    "loader_border_color": "#e2e8f0",
    "loader_icon_color": "#0f172a",
    "loader_steam_color": "#94a3b8",
    "toast_background_color": "#222222",
    "toast_text_color": "#ffffff",
    "toast_error_border_color": "#e55353",
    "run_button_background": "linear-gradient(180deg, #38d36e 0%, #19b96c 100%)",
    "run_button_background_hover": "linear-gradient(180deg, #3fe076 0%, #19b96c 100%)",
    "run_button_text_color": "#ffffff",
    "run_button_focus_color": "rgba(60, 207, 119, 0.3)",
    "shadow_sm": "0 1px 2px rgba(0,0,0,0.04)",
    "shadow_md": "0 4px 12px rgba(0,0,0,0.12)",
    "shadow_lg": "0 10px 30px rgba(0,0,0,0.08)",
}


THEME_ALIASES = {
    "backgroundColor": "background_color",
    "background_color": "background_color",
    "secondaryBackgroundColor": "panel_bg",
    "secondary_background_color": "panel_bg",
    "textColor": "text_color",
    "text_color": "text_color",
    "surfaceColor": "surface_color",
    "surface_color": "surface_color",
    "primaryColor": "primary_color",
    "primary_color": "primary_color",
    "borderColor": "border_color",
    "border_color": "border_color",
    "widgetBackgroundColor": "widget_background_color",
    "widget_background_color": "widget_background_color",
    "cardBackgroundColor": "card_background_color",
    "card_background_color": "card_background_color",
    "mutedTextColor": "muted_text_color",
    "muted_text_color": "muted_text_color",
    "contentBackgroundColor": "content_background_color",
    "content_background_color": "content_background_color",
    "panelBackgroundColor": "panel_bg",
    "panel_bg": "panel_bg",
    "panelBackgroundHoverColor": "panel_bg_hover",
    "panel_bg_hover": "panel_bg_hover",
    "panelBackgroundHover2Color": "panel_bg_hover_2",
    "panel_bg_hover_2": "panel_bg_hover_2",
    "accentColor": "accent_color",
    "accent_color": "accent_color",
    "focusBorderColor": "focus_border_color",
    "focus_border_color": "focus_border_color",
    "hoverBackgroundColor": "hover_background_color",
    "hover_background_color": "hover_background_color",
    "selectedBackgroundColor": "selected_background_color",
    "selected_background_color": "selected_background_color",
    "sidebarBackgroundColor": "sidebar_background_color",
    "sidebar_background_color": "sidebar_background_color",
    "sidebarTextColor": "sidebar_text_color",
    "sidebar_text_color": "sidebar_text_color",
    "sidebarTitleColor": "sidebar_title_color",
    "sidebar_title_color": "sidebar_title_color",
    "sidebarShadow": "sidebar_shadow",
    "sidebar_shadow": "sidebar_shadow",
    "sidebarBackdropColor": "sidebar_backdrop_color",
    "sidebar_backdrop_color": "sidebar_backdrop_color",
    "topbarBackgroundColor": "topbar_background_color",
    "topbar_background_color": "topbar_background_color",
    "topbarTextColor": "topbar_text_color",
    "topbar_text_color": "topbar_text_color",
    "topbarBorderColor": "topbar_border_color",
    "topbar_border_color": "topbar_border_color",
    "footerBackgroundColor": "footer_background_color",
    "footer_background_color": "footer_background_color",
    "footerTextColor": "footer_text_color",
    "footer_text_color": "footer_text_color",
    "footerBorderColor": "footer_border_color",
    "footer_border_color": "footer_border_color",
    "loaderBackgroundColor": "loader_background_color",
    "loader_background_color": "loader_background_color",
    "loaderCardBackgroundColor": "loader_card_background_color",
    "loader_card_background_color": "loader_card_background_color",
    "loaderTextColor": "loader_text_color",
    "loader_text_color": "loader_text_color",
    "loaderBorderColor": "loader_border_color",
    "loader_border_color": "loader_border_color",
    "loaderIconColor": "loader_icon_color",
    "loader_icon_color": "loader_icon_color",
    "loaderSteamColor": "loader_steam_color",
    "loader_steam_color": "loader_steam_color",
    "toastBackgroundColor": "toast_background_color",
    "toast_background_color": "toast_background_color",
    "toastTextColor": "toast_text_color",
    "toast_text_color": "toast_text_color",
    "toastErrorBorderColor": "toast_error_border_color",
    "toast_error_border_color": "toast_error_border_color",
    "runButtonBackground": "run_button_background",
    "run_button_background": "run_button_background",
    "runButtonBackgroundHover": "run_button_background_hover",
    "run_button_background_hover": "run_button_background_hover",
    "runButtonTextColor": "run_button_text_color",
    "run_button_text_color": "run_button_text_color",
    "runButtonFocusColor": "run_button_focus_color",
    "run_button_focus_color": "run_button_focus_color",
    "headingFontFamily": "heading_font_family",
    "heading_font_family": "heading_font_family",
    "headingFontWeight": "heading_font_weight",
    "heading_font_weight": "heading_font_weight",
    "font": "font_family",
    "fontUrl": "font_url",
    "font_url": "font_url",
    "fontFamily": "font_family",
    "font_family": "font_family",
    "fontSize": "font_size",
    "font_size": "font_size",
    "fontWeight": "font_weight",
    "font_weight": "font_weight",
    "borderRadius": "border_radius",
    "border_radius": "border_radius",
    "borderRadiusSm": "border_radius_sm",
    "border_radius_sm": "border_radius_sm",
    "borderRadiusLg": "border_radius_lg",
    "border_radius_lg": "border_radius_lg",
    "buttonPrimaryText": "button_primary_text",
    "button_primary_text": "button_primary_text",
    "buttonShadow": "button_shadow",
    "button_shadow": "button_shadow",
    "buttonShadowHover": "button_shadow_hover",
    "button_shadow_hover": "button_shadow_hover",
    "dangerColor": "danger_color",
    "danger_color": "danger_color",
    "successColor": "success_color",
    "success_color": "success_color",
    "warningColor": "warning_color",
    "warning_color": "warning_color",
    "sliderTrackColor": "slider_track_color",
    "slider_track_color": "slider_track_color",
}


CSS_VARIABLE_MAP = {
    "font_family": "--mercury-font-family",
    "heading_font_family": "--mercury-heading-font-family",
    "font_size": "--mercury-font-size",
    "text_color": "--mercury-text-color",
    "muted_text_color": "--mercury-muted-text-color",
    "background_color": "--mercury-background-color",
    "surface_color": "--mercury-surface-color",
    "content_background_color": "--mercury-content-background-color",
    "panel_bg": "--mercury-panel-bg",
    "card_background_color": "--mercury-card-background-color",
    "border_color": "--mercury-border-color",
    "border_radius": "--mercury-border-radius",
    "primary_color": "--mercury-primary-color",
    "accent_color": "--mercury-accent-color",
    "focus_border_color": "--mercury-focus-border-color",
    "hover_background_color": "--mercury-hover-background-color",
    "selected_background_color": "--mercury-selected-background-color",
    "sidebar_background_color": "--mercury-sidebar-background-color",
    "sidebar_text_color": "--mercury-sidebar-text-color",
    "sidebar_title_color": "--mercury-sidebar-title-color",
    "sidebar_shadow": "--mercury-sidebar-shadow",
    "sidebar_backdrop_color": "--mercury-sidebar-backdrop-color",
    "topbar_background_color": "--mercury-topbar-background-color",
    "topbar_text_color": "--mercury-topbar-text-color",
    "topbar_border_color": "--mercury-topbar-border-color",
    "footer_background_color": "--mercury-footer-background-color",
    "footer_text_color": "--mercury-footer-text-color",
    "footer_border_color": "--mercury-footer-border-color",
    "loader_background_color": "--mercury-loader-background-color",
    "loader_card_background_color": "--mercury-loader-card-background-color",
    "loader_text_color": "--mercury-loader-text-color",
    "loader_border_color": "--mercury-loader-border-color",
    "loader_icon_color": "--mercury-loader-icon-color",
    "loader_steam_color": "--mercury-loader-steam-color",
    "toast_background_color": "--mercury-toast-background-color",
    "toast_text_color": "--mercury-toast-text-color",
    "toast_error_border_color": "--mercury-toast-error-border-color",
    "run_button_background": "--mercury-run-button-background",
    "run_button_background_hover": "--mercury-run-button-background-hover",
    "run_button_text_color": "--mercury-run-button-text-color",
    "run_button_focus_color": "--mercury-run-button-focus-color",
    "shadow_sm": "--mercury-shadow-sm",
    "shadow_md": "--mercury-shadow-md",
    "shadow_lg": "--mercury-shadow-lg",
}


def resolve_config_path(config_path: str = "config.toml") -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path

    config_dir = os.getenv(CONFIG_ENV_VAR)
    if config_dir:
        return Path(config_dir).expanduser() / path

    return Path.cwd() / path


def load_config_file(config_path: str = "config.toml") -> dict:
    resolved = resolve_config_path(config_path)
    if not resolved.exists():
        return {}
    return toml.load(resolved)


def _normalize_font_family(value: str) -> str:
    key = str(value).strip().lower()
    if key == "sans serif":
        return DEFAULT_THEME["font_family"]
    if key == "serif":
        return "Iowan Old Style, Palatino Linotype, Book Antiqua, Georgia, serif"
    if key == "monospace":
        return "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    return value


def _parse_hex_color(value: str):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("#"):
        return None
    hex_value = value[1:]
    if len(hex_value) == 3:
        hex_value = "".join(ch * 2 for ch in hex_value)
    if len(hex_value) != 6:
        return None
    try:
        return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _mix_colors(color_a: str, color_b: str, ratio: float) -> str:
    rgb_a = _parse_hex_color(color_a)
    rgb_b = _parse_hex_color(color_b)
    if rgb_a is None or rgb_b is None:
        return color_a
    ratio = max(0.0, min(1.0, ratio))
    mixed = tuple(round(a * ratio + b * (1 - ratio)) for a, b in zip(rgb_a, rgb_b))
    return _to_hex(mixed)


def _relative_luminance(color: str) -> float | None:
    rgb = _parse_hex_color(color)
    if rgb is None:
        return None

    def _channel(c: int) -> float:
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _derive_surface_color(background_color: str) -> str:
    luminance = _relative_luminance(background_color)
    if luminance is None:
        return DEFAULT_THEME["surface_color"]
    if luminance < 0.35:
        return _mix_colors("#ffffff", background_color, 0.12)
    return DEFAULT_THEME["surface_color"]


def _derive_muted_text_color(text_color: str, background_color: str) -> str:
    return _mix_colors(text_color, background_color, 0.65)


def _derive_border_color(text_color: str, background_color: str) -> str:
    return _mix_colors(text_color, background_color, 0.18)


def _derive_topbar_background(background_color: str) -> str:
    luminance = _relative_luminance(background_color)
    if luminance is None:
        return DEFAULT_THEME["topbar_background_color"]
    if luminance < 0.35:
        return _mix_colors("#000000", background_color, 0.85)
    return _mix_colors("#000000", background_color, 0.12)


def _to_rgba(color: str, alpha: float, fallback: str) -> str:
    rgb = _parse_hex_color(color)
    if rgb is None:
        return fallback
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def _derive_topbar_text(background_color: str, text_color: str) -> str:
    luminance = _relative_luminance(background_color)
    if luminance is not None and luminance < 0.45:
        return "#f8fafc"
    return text_color


def _derive_run_button_hover(primary_color: str) -> str:
    return f"linear-gradient(180deg, {_mix_colors('#ffffff', primary_color, 0.18)} 0%, {primary_color} 100%)"


def _derive_run_button_background(primary_color: str) -> str:
    return f"linear-gradient(180deg, {_mix_colors('#ffffff', primary_color, 0.1)} 0%, {_mix_colors('#000000', primary_color, 0.88)} 100%)"


def _derive_run_button_focus(primary_color: str) -> str:
    rgb = _parse_hex_color(primary_color)
    if rgb is None:
        return DEFAULT_THEME["run_button_focus_color"]
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)"


def _derive_sidebar_shadow(sidebar_background_color: str, text_color: str) -> str:
    luminance = _relative_luminance(sidebar_background_color)
    if luminance is not None and luminance < 0.35:
        glow = _to_rgba(text_color, 0.08, "rgba(255,255,255,0.08)")
        depth = "rgba(0,0,0,0.28)"
        return f"2px 0 10px {glow}, 10px 0 24px {depth}"
    return f"2px 0 12px {_to_rgba(text_color, 0.18, 'rgba(0,0,0,0.18)')}"


def _derive_sidebar_backdrop_color(text_color: str, sidebar_background_color: str) -> str:
    luminance = _relative_luminance(sidebar_background_color)
    alpha = 0.14 if luminance is not None and luminance < 0.35 else 0.18
    return _to_rgba(text_color, alpha, "rgba(15,23,42,0.22)")


def normalize_theme(theme: dict | None) -> dict:
    normalized = dict(DEFAULT_THEME)
    theme = theme or {}
    provided = set()

    overrides = theme.get("overrides")
    if isinstance(overrides, dict):
        merged_theme = {k: v for k, v in theme.items() if k != "overrides"}
        merged_theme.update(overrides)
        theme = merged_theme

    for key, value in theme.items():
        canonical = THEME_ALIASES.get(key, key)
        normalized[canonical] = value
        provided.add(canonical)

    if "font_family" in normalized:
        normalized["font_family"] = _normalize_font_family(normalized["font_family"])
    if "heading_font_family" in normalized:
        normalized["heading_font_family"] = _normalize_font_family(
            normalized["heading_font_family"]
        )

    if "heading_font_family" not in provided or not normalized.get("heading_font_family"):
        normalized["heading_font_family"] = normalized["font_family"]
    if "accent_color" not in provided or not normalized.get("accent_color"):
        normalized["accent_color"] = normalized["primary_color"]
    if "focus_border_color" not in provided or not normalized.get("focus_border_color"):
        normalized["focus_border_color"] = normalized["accent_color"]
    if "surface_color" not in provided or not normalized.get("surface_color"):
        normalized["surface_color"] = _derive_surface_color(normalized["background_color"])
    if "muted_text_color" not in provided or not normalized.get("muted_text_color"):
        normalized["muted_text_color"] = _derive_muted_text_color(
            normalized["text_color"], normalized["background_color"]
        )
    if "border_color" not in provided or not normalized.get("border_color"):
        normalized["border_color"] = _derive_border_color(
            normalized["text_color"], normalized["background_color"]
        )
    if "content_background_color" not in provided or not normalized.get("content_background_color"):
        normalized["content_background_color"] = normalized["surface_color"]
    if "panel_bg" not in provided or not normalized.get("panel_bg"):
        normalized["panel_bg"] = normalized["surface_color"]
    if "panel_bg_hover" not in provided or not normalized.get("panel_bg_hover"):
        normalized["panel_bg_hover"] = _mix_colors(
            normalized["text_color"], normalized["surface_color"], 0.06
        )
    if "panel_bg_hover_2" not in provided or not normalized.get("panel_bg_hover_2"):
        normalized["panel_bg_hover_2"] = _mix_colors(
            normalized["text_color"], normalized["surface_color"], 0.10
        )
    if "widget_background_color" not in provided or not normalized.get("widget_background_color"):
        normalized["widget_background_color"] = normalized["surface_color"]
    if "card_background_color" not in provided or not normalized.get("card_background_color"):
        normalized["card_background_color"] = normalized["surface_color"]
    if "sidebar_text_color" not in provided or not normalized.get("sidebar_text_color"):
        normalized["sidebar_text_color"] = normalized["text_color"]
    if "sidebar_title_color" not in provided or not normalized.get("sidebar_title_color"):
        normalized["sidebar_title_color"] = normalized["sidebar_text_color"]
    if "sidebar_background_color" not in provided or not normalized.get("sidebar_background_color"):
        normalized["sidebar_background_color"] = normalized["surface_color"]
    if "sidebar_shadow" not in provided or not normalized.get("sidebar_shadow"):
        normalized["sidebar_shadow"] = _derive_sidebar_shadow(
            normalized["sidebar_background_color"], normalized["text_color"]
        )
    if "sidebar_backdrop_color" not in provided or not normalized.get("sidebar_backdrop_color"):
        normalized["sidebar_backdrop_color"] = _derive_sidebar_backdrop_color(
            normalized["text_color"], normalized["sidebar_background_color"]
        )
    if "topbar_background_color" not in provided or not normalized.get("topbar_background_color"):
        normalized["topbar_background_color"] = _derive_topbar_background(
            normalized["background_color"]
        )
    if "topbar_text_color" not in provided or not normalized.get("topbar_text_color"):
        normalized["topbar_text_color"] = _derive_topbar_text(
            normalized["topbar_background_color"], normalized["text_color"]
        )
    if "topbar_border_color" not in provided or not normalized.get("topbar_border_color"):
        normalized["topbar_border_color"] = _derive_border_color(
            normalized["topbar_text_color"], normalized["topbar_background_color"]
        )
    if "footer_text_color" not in provided or not normalized.get("footer_text_color"):
        normalized["footer_text_color"] = normalized["muted_text_color"]
    if "footer_background_color" not in provided or not normalized.get("footer_background_color"):
        normalized["footer_background_color"] = normalized["surface_color"]
    if "footer_border_color" not in provided or not normalized.get("footer_border_color"):
        normalized["footer_border_color"] = normalized["border_color"]
    if "loader_card_background_color" not in provided or not normalized.get("loader_card_background_color"):
        normalized["loader_card_background_color"] = normalized["surface_color"]
    if "loader_text_color" not in provided or not normalized.get("loader_text_color"):
        normalized["loader_text_color"] = normalized["muted_text_color"]
    if "loader_border_color" not in provided or not normalized.get("loader_border_color"):
        normalized["loader_border_color"] = normalized["border_color"]
    if "loader_icon_color" not in provided or not normalized.get("loader_icon_color"):
        normalized["loader_icon_color"] = normalized["text_color"]
    if "loader_steam_color" not in provided or not normalized.get("loader_steam_color"):
        normalized["loader_steam_color"] = normalized["muted_text_color"]
    if "loader_background_color" not in provided or not normalized.get("loader_background_color"):
        rgb = _parse_hex_color(normalized["background_color"])
        if rgb is not None:
            normalized["loader_background_color"] = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.85)"
    if "toast_background_color" not in provided or not normalized.get("toast_background_color"):
        normalized["toast_background_color"] = normalized["topbar_background_color"]
    if "toast_text_color" not in provided or not normalized.get("toast_text_color"):
        normalized["toast_text_color"] = normalized["topbar_text_color"]
    if "toast_error_border_color" not in provided or not normalized.get("toast_error_border_color"):
        normalized["toast_error_border_color"] = normalized["danger_color"]
    if "run_button_background" not in provided or not normalized.get("run_button_background"):
        normalized["run_button_background"] = _derive_run_button_background(
            normalized["primary_color"]
        )
    if "run_button_background_hover" not in provided or not normalized.get("run_button_background_hover"):
        normalized["run_button_background_hover"] = _derive_run_button_hover(
            normalized["primary_color"]
        )
    if "run_button_focus_color" not in provided or not normalized.get("run_button_focus_color"):
        normalized["run_button_focus_color"] = _derive_run_button_focus(
            normalized["primary_color"]
        )
    if "button_primary_text" not in provided or not normalized.get("button_primary_text"):
        normalized["button_primary_text"] = _derive_topbar_text(
            normalized["primary_color"], normalized["text_color"]
        )

    return normalized


def load_theme_config(config_path: str = "config.toml") -> dict:
    config = load_config_file(config_path)
    return normalize_theme(config.get("theme", {}))


def build_theme_font_links(theme: dict | None) -> str:
    theme = normalize_theme(theme)
    font_url = str(theme.get("font_url") or "").strip()
    if not font_url:
        return ""

    parsed = urlparse(font_url)
    host = parsed.netloc.lower()
    lines = []
    if host == "fonts.googleapis.com":
        lines.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
        lines.append('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    lines.append(f'<link rel="stylesheet" href="{font_url}">')
    return "\n  ".join(lines)


def build_theme_css_vars(theme: dict | None) -> str:
    theme = normalize_theme(theme)
    lines = []
    for key, css_var in CSS_VARIABLE_MAP.items():
        value = theme.get(key)
        if value is None:
            continue
        lines.append(f"{css_var}: {value};")
    return "\n      ".join(lines)
