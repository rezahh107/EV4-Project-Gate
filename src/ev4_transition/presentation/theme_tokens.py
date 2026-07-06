from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

ThemeName = Literal["light", "dark"]

THEME_TOKENS: dict[ThemeName, dict[str, Any]] = {
    "light": {
        "surface.base": "#f8fafc",
        "surface.raised": "#ffffff",
        "surface.overlay": "#f1f5f9",
        "text.primary": "#0f172a",
        "text.secondary": "#475569",
        "border.subtle": "#e2e8f0",
        "border.default": "#cbd5e1",
        "border.strong": "#94a3b8",
        "accent.primary": "#2563eb",
        "accent.hover": "#1d4ed8",
        "focus.ring": "#2563eb",
        "code.bg": "#eef2ff",
        "status.accepted": {"tone": "success", "foreground": "#065f46", "background": "#d1fae5", "icon": "✅", "label": "پذیرفته شد"},
        "status.repair_needed": {"tone": "warning", "foreground": "#92400e", "background": "#fef3c7", "icon": "🛠️", "label": "نیازمند اصلاح"},
        "status.insufficient_evidence": {"tone": "warning", "foreground": "#92400e", "background": "#ffedd5", "icon": "⚠️", "label": "شواهد کافی نیست"},
        "status.invalid": {"tone": "danger", "foreground": "#991b1b", "background": "#fee2e2", "icon": "❌", "label": "نامعتبر"},
        "font.fa_ui": "Vazirmatn, Vazir, IRANSansX, IranSansXV, Tahoma, system-ui, sans-serif",
        "font.code": "Cascadia Code, JetBrains Mono, Fira Code, Consolas, monospace",
    },
    "dark": {
        "surface.base": "#0b1120",
        "surface.raised": "#111827",
        "surface.overlay": "#1e293b",
        "text.primary": "#e5e7eb",
        "text.secondary": "#cbd5e1",
        "border.subtle": "#334155",
        "border.default": "#475569",
        "border.strong": "#64748b",
        "accent.primary": "#93c5fd",
        "accent.hover": "#bfdbfe",
        "focus.ring": "#8bc4ff",
        "code.bg": "#020617",
        "status.accepted": {"tone": "success", "foreground": "#bbf7d0", "background": "#064e3b", "icon": "✅", "label": "پذیرفته شد"},
        "status.repair_needed": {"tone": "warning", "foreground": "#fde68a", "background": "#78350f", "icon": "🛠️", "label": "نیازمند اصلاح"},
        "status.insufficient_evidence": {"tone": "warning", "foreground": "#fed7aa", "background": "#7c2d12", "icon": "⚠️", "label": "شواهد کافی نیست"},
        "status.invalid": {"tone": "danger", "foreground": "#fecaca", "background": "#7f1d1d", "icon": "❌", "label": "نامعتبر"},
        "font.fa_ui": "Vazirmatn, Vazir, IRANSansX, IranSansXV, Tahoma, system-ui, sans-serif",
        "font.code": "Cascadia Code, JetBrains Mono, Fira Code, Consolas, monospace",
    },
}

REQUIRED_TOKEN_KEYS = (
    "status.accepted",
    "status.repair_needed",
    "status.insufficient_evidence",
    "status.invalid",
    "surface.base",
    "surface.raised",
    "surface.overlay",
    "text.primary",
    "text.secondary",
    "border.subtle",
    "border.default",
    "border.strong",
    "accent.primary",
    "accent.hover",
    "focus.ring",
    "code.bg",
)


def theme_tokens(theme: ThemeName) -> dict[str, Any]:
    return deepcopy(THEME_TOKENS[theme])


def assert_theme_contract() -> None:
    for theme, tokens in THEME_TOKENS.items():
        missing = [key for key in REQUIRED_TOKEN_KEYS if key not in tokens]
        if missing:
            raise AssertionError(f"{theme} theme missing required tokens: {missing}")
        for status in ("accepted", "repair_needed", "insufficient_evidence", "invalid"):
            token = tokens[f"status.{status}"]
            if not all(token.get(key) for key in ("tone", "foreground", "background", "icon", "label")):
                raise AssertionError(f"status.{status} in {theme} must include tone, colors, icon, and label")
    if THEME_TOKENS["light"]["surface.base"] == THEME_TOKENS["dark"]["text.primary"]:
        raise AssertionError("dark theme appears to be a simple inversion")


def css_custom_properties() -> str:
    """Return scoped CSS custom properties backed by semantic DMDS tokens."""

    light = THEME_TOKENS["light"]
    dark = THEME_TOKENS["dark"]
    return f"""
    .gradio-container,
    .ev4-app,
    .ev4-shell {{
      --ev4-surface-base: {light["surface.base"]};
      --ev4-surface-raised: {light["surface.raised"]};
      --ev4-surface-overlay: {light["surface.overlay"]};
      --ev4-text-primary: {light["text.primary"]};
      --ev4-text-secondary: {light["text.secondary"]};
      --ev4-border-subtle: {light["border.subtle"]};
      --ev4-border-default: {light["border.default"]};
      --ev4-border-strong: {light["border.strong"]};
      --ev4-accent-primary: {light["accent.primary"]};
      --ev4-accent-hover: {light["accent.hover"]};
      --ev4-focus-ring: {light["focus.ring"]};
      --ev4-code-bg: {light["code.bg"]};
      --ev4-font-fa-ui: {light["font.fa_ui"]};
      --ev4-font-code: {light["font.code"]};
      --ev4-status-accepted-fg: {light["status.accepted"]["foreground"]};
      --ev4-status-accepted-bg: {light["status.accepted"]["background"]};
      --ev4-status-warning-fg: {light["status.insufficient_evidence"]["foreground"]};
      --ev4-status-warning-bg: {light["status.insufficient_evidence"]["background"]};
      --ev4-status-danger-fg: {light["status.invalid"]["foreground"]};
      --ev4-status-danger-bg: {light["status.invalid"]["background"]};
    }}
    @media (prefers-color-scheme: dark) {{
      .gradio-container,
      .ev4-app,
      .ev4-shell {{
        --ev4-surface-base: {dark["surface.base"]};
        --ev4-surface-raised: {dark["surface.raised"]};
        --ev4-surface-overlay: {dark["surface.overlay"]};
        --ev4-text-primary: {dark["text.primary"]};
        --ev4-text-secondary: {dark["text.secondary"]};
        --ev4-border-subtle: {dark["border.subtle"]};
        --ev4-border-default: {dark["border.default"]};
        --ev4-border-strong: {dark["border.strong"]};
        --ev4-accent-primary: {dark["accent.primary"]};
        --ev4-accent-hover: {dark["accent.hover"]};
        --ev4-focus-ring: {dark["focus.ring"]};
        --ev4-code-bg: {dark["code.bg"]};
        --ev4-status-accepted-fg: {dark["status.accepted"]["foreground"]};
        --ev4-status-accepted-bg: {dark["status.accepted"]["background"]};
        --ev4-status-warning-fg: {dark["status.insufficient_evidence"]["foreground"]};
        --ev4-status-warning-bg: {dark["status.insufficient_evidence"]["background"]};
        --ev4-status-danger-fg: {dark["status.invalid"]["foreground"]};
        --ev4-status-danger-bg: {dark["status.invalid"]["background"]};
      }}
    }}
    """
