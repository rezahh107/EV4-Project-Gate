from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

ThemeName = Literal["light", "dark"]

THEME_TOKENS: dict[ThemeName, dict[str, Any]] = {
    "light": {
        "surface.base": "#f8fafc",
        "surface.raised": "#ffffff",
        "surface.overlay": "#f1f5f9",
        "surface.dialog": "#ffffff",
        "text.primary": "#0f172a",
        "text.secondary": "#475569",
        "text.muted": "#64748b",
        "text.disabled": "#475569",
        "border.subtle": "#e2e8f0",
        "border.default": "#cbd5e1",
        "border.strong": "#64748b",
        "accent.primary": "#2563eb",
        "accent.hover": "#1d4ed8",
        "accent.active": "#1e40af",
        "focus.ring": "#2563eb",
        "selection.bg": "#dbeafe",
        "success": "#166534",
        "success.bg": "#dcfce7",
        "warning": "#92400e",
        "warning.bg": "#fef3c7",
        "danger": "#991b1b",
        "danger.bg": "#fee2e2",
        "info": "#1d4ed8",
        "info.bg": "#dbeafe",
        "input.bg": "#ffffff",
        "input.border": "#64748b",
        "input.text": "#0f172a",
        "button.primary.bg": "#2563eb",
        "button.primary.text": "#f8fafc",
        "button.secondary.bg": "#ffffff",
        "button.secondary.text": "#0f172a",
        "disabled.bg": "#e2e8f0",
        "disabled.text": "#475569",
        "code.bg": "#eef2ff",
        "shadow.raised": "rgba(15, 23, 42, 0.08)",
        "status.accepted": {"tone": "success", "foreground": "#166534", "background": "#dcfce7", "icon": "✅", "label": "پذیرفته شد"},
        "status.repair_needed": {"tone": "warning", "foreground": "#92400e", "background": "#fef3c7", "icon": "🛠️", "label": "نیازمند اصلاح"},
        "status.insufficient_evidence": {"tone": "warning", "foreground": "#92400e", "background": "#fef3c7", "icon": "⚠️", "label": "شواهد کافی نیست"},
        "status.invalid": {"tone": "danger", "foreground": "#991b1b", "background": "#fee2e2", "icon": "❌", "label": "نامعتبر"},
        "font.fa_ui": "Vazirmatn, Vazir, IRANSansX, IranSansXV, Tahoma, system-ui, sans-serif",
        "font.code": "Cascadia Code, JetBrains Mono, Fira Code, Consolas, monospace",
    },
    "dark": {
        "surface.base": "#0f172a",
        "surface.raised": "#172033",
        "surface.overlay": "#202d40",
        "surface.dialog": "#2b3a50",
        "text.primary": "#f3f6fb",
        "text.secondary": "#b8c4d6",
        "text.muted": "#93a4ba",
        "text.disabled": "#94a3b8",
        "border.subtle": "#2a3648",
        "border.default": "#5f718d",
        "border.strong": "#8aa0bf",
        "accent.primary": "#8bc4ff",
        "accent.hover": "#a5d6ff",
        "accent.active": "#60a5fa",
        "focus.ring": "#8bc4ff",
        "selection.bg": "rgba(139, 196, 255, 0.28)",
        "success": "#63d49b",
        "success.bg": "#173b2c",
        "warning": "#f3c86a",
        "warning.bg": "#493918",
        "danger": "#ff9c92",
        "danger.bg": "#4a211f",
        "info": "#8bc4ff",
        "info.bg": "#19334d",
        "input.bg": "#0f172a",
        "input.border": "#5f718d",
        "input.text": "#f3f6fb",
        "button.primary.bg": "#2563eb",
        "button.primary.text": "#f8fafc",
        "button.secondary.bg": "#202d40",
        "button.secondary.text": "#f3f6fb",
        "disabled.bg": "#1e293b",
        "disabled.text": "#94a3b8",
        "code.bg": "#020617",
        "shadow.raised": "rgba(0, 0, 0, 0.32)",
        "status.accepted": {"tone": "success", "foreground": "#63d49b", "background": "#173b2c", "icon": "✅", "label": "پذیرفته شد"},
        "status.repair_needed": {"tone": "warning", "foreground": "#f3c86a", "background": "#493918", "icon": "🛠️", "label": "نیازمند اصلاح"},
        "status.insufficient_evidence": {"tone": "warning", "foreground": "#f3c86a", "background": "#493918", "icon": "⚠️", "label": "شواهد کافی نیست"},
        "status.invalid": {"tone": "danger", "foreground": "#ff9c92", "background": "#4a211f", "icon": "❌", "label": "نامعتبر"},
        "font.fa_ui": "Vazirmatn, Vazir, IRANSansX, IranSansXV, Tahoma, system-ui, sans-serif",
        "font.code": "Cascadia Code, JetBrains Mono, Fira Code, Consolas, monospace",
    },
}

STATUS_NAMES = ("accepted", "repair_needed", "insufficient_evidence", "invalid")
REQUIRED_STATUS_FIELDS = ("tone", "foreground", "background", "icon", "label")
REQUIRED_TOKEN_KEYS = (
    "surface.base",
    "surface.raised",
    "surface.overlay",
    "surface.dialog",
    "text.primary",
    "text.secondary",
    "text.muted",
    "text.disabled",
    "border.subtle",
    "border.default",
    "border.strong",
    "accent.primary",
    "accent.hover",
    "accent.active",
    "focus.ring",
    "selection.bg",
    "success",
    "success.bg",
    "warning",
    "warning.bg",
    "danger",
    "danger.bg",
    "info",
    "info.bg",
    "input.bg",
    "input.border",
    "input.text",
    "button.primary.bg",
    "button.primary.text",
    "button.secondary.bg",
    "button.secondary.text",
    "disabled.bg",
    "disabled.text",
    "code.bg",
    "shadow.raised",
    "status.accepted",
    "status.repair_needed",
    "status.insufficient_evidence",
    "status.invalid",
    "font.fa_ui",
    "font.code",
)


def theme_tokens(theme: ThemeName) -> dict[str, Any]:
    return deepcopy(THEME_TOKENS[theme])


def assert_theme_contract() -> None:
    for theme, tokens in THEME_TOKENS.items():
        missing = [key for key in REQUIRED_TOKEN_KEYS if key not in tokens]
        if missing:
            raise AssertionError(f"{theme} theme missing required tokens: {missing}")
        for status in STATUS_NAMES:
            token = tokens[f"status.{status}"]
            if not isinstance(token, dict):
                raise AssertionError(f"status.{status} in {theme} must be an object token")
            if not all(token.get(key) for key in REQUIRED_STATUS_FIELDS):
                raise AssertionError(f"status.{status} in {theme} must include tone, colors, icon, and label")
    if THEME_TOKENS["dark"]["surface.base"] in {"#000", "#000000"}:
        raise AssertionError("dark theme must not use pure black as its base surface")
    if THEME_TOKENS["dark"]["text.primary"].lower() in {"#fff", "#ffffff"}:
        raise AssertionError("dark theme must not use persistent pure white body text")
    if THEME_TOKENS["light"]["surface.base"] == THEME_TOKENS["dark"]["text.primary"]:
        raise AssertionError("dark theme appears to be a simple inversion")


def _theme_custom_properties(theme: ThemeName) -> str:
    tokens = THEME_TOKENS[theme]
    return f"""
      color-scheme: {theme};
      --ev4-surface-base: {tokens["surface.base"]};
      --ev4-surface-raised: {tokens["surface.raised"]};
      --ev4-surface-overlay: {tokens["surface.overlay"]};
      --ev4-surface-dialog: {tokens["surface.dialog"]};
      --ev4-text-primary: {tokens["text.primary"]};
      --ev4-text-secondary: {tokens["text.secondary"]};
      --ev4-text-muted: {tokens["text.muted"]};
      --ev4-text-disabled: {tokens["text.disabled"]};
      --ev4-border-subtle: {tokens["border.subtle"]};
      --ev4-border-default: {tokens["border.default"]};
      --ev4-border-strong: {tokens["border.strong"]};
      --ev4-accent-primary: {tokens["accent.primary"]};
      --ev4-accent-hover: {tokens["accent.hover"]};
      --ev4-accent-active: {tokens["accent.active"]};
      --ev4-focus-ring: {tokens["focus.ring"]};
      --ev4-selection-bg: {tokens["selection.bg"]};
      --ev4-success: {tokens["success"]};
      --ev4-success-bg: {tokens["success.bg"]};
      --ev4-warning: {tokens["warning"]};
      --ev4-warning-bg: {tokens["warning.bg"]};
      --ev4-danger: {tokens["danger"]};
      --ev4-danger-bg: {tokens["danger.bg"]};
      --ev4-info: {tokens["info"]};
      --ev4-info-bg: {tokens["info.bg"]};
      --ev4-input-bg: {tokens["input.bg"]};
      --ev4-input-border: {tokens["input.border"]};
      --ev4-input-text: {tokens["input.text"]};
      --ev4-button-primary-bg: {tokens["button.primary.bg"]};
      --ev4-button-primary-text: {tokens["button.primary.text"]};
      --ev4-button-secondary-bg: {tokens["button.secondary.bg"]};
      --ev4-button-secondary-text: {tokens["button.secondary.text"]};
      --ev4-disabled-bg: {tokens["disabled.bg"]};
      --ev4-disabled-text: {tokens["disabled.text"]};
      --ev4-code-bg: {tokens["code.bg"]};
      --ev4-shadow-raised: {tokens["shadow.raised"]};
      --ev4-font-fa-ui: {tokens["font.fa_ui"]};
      --ev4-font-code: {tokens["font.code"]};
      --ev4-status-accepted-fg: {tokens["status.accepted"]["foreground"]};
      --ev4-status-accepted-bg: {tokens["status.accepted"]["background"]};
      --ev4-status-success-fg: {tokens["status.accepted"]["foreground"]};
      --ev4-status-success-bg: {tokens["status.accepted"]["background"]};
      --ev4-status-repair-fg: {tokens["status.repair_needed"]["foreground"]};
      --ev4-status-repair-bg: {tokens["status.repair_needed"]["background"]};
      --ev4-status-warning-fg: {tokens["status.insufficient_evidence"]["foreground"]};
      --ev4-status-warning-bg: {tokens["status.insufficient_evidence"]["background"]};
      --ev4-status-danger-fg: {tokens["status.invalid"]["foreground"]};
      --ev4-status-danger-bg: {tokens["status.invalid"]["background"]};
    """


def css_custom_properties() -> str:
    """Return scoped CSS custom properties backed by semantic DMDS tokens.

    Resolution model:
    - Light tokens are the safe default.
    - Explicit Gradio/browser light or dark classes win when present.
    - System dark preference is only a fallback when no explicit class/data-theme is available.
    """

    light = _theme_custom_properties("light")
    dark = _theme_custom_properties("dark")
    return f"""
    .gradio-container,
    .ev4-app,
    .ev4-shell {{
{light}
    }}
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) .gradio-container,
      :root:not([data-theme="light"]) .ev4-app,
      :root:not([data-theme="light"]) .ev4-shell {{
{dark}
      }}
    }}
    :root[data-theme="light"] .gradio-container,
    :root[data-theme="light"] .ev4-app,
    :root[data-theme="light"] .ev4-shell,
    body.light .gradio-container,
    body.light .ev4-app,
    body.light .ev4-shell,
    .light .gradio-container,
    .light .ev4-app,
    .light .ev4-shell {{
{light}
    }}
    :root[data-theme="dark"] .gradio-container,
    :root[data-theme="dark"] .ev4-app,
    :root[data-theme="dark"] .ev4-shell,
    body.dark .gradio-container,
    body.dark .ev4-app,
    body.dark .ev4-shell,
    .dark .gradio-container,
    .dark .ev4-app,
    .dark .ev4-shell {{
{dark}
    }}
    """
