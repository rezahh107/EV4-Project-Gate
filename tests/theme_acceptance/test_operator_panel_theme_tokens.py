from __future__ import annotations

from ev4_transition.presentation.theme_tokens import THEME_TOKENS, assert_theme_contract, css_custom_properties


REQUIRED_OPERATOR_PANEL_TOKENS = {
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
}


def test_operator_panel_semantic_tokens_exist_across_light_and_dark():
    assert_theme_contract()
    for theme in ("light", "dark"):
        assert REQUIRED_OPERATOR_PANEL_TOKENS <= set(THEME_TOKENS[theme])


def test_operator_panel_css_exports_extended_custom_properties():
    css = css_custom_properties()

    required_css_vars = {
        "--ev4-surface-overlay",
        "--ev4-surface-dialog",
        "--ev4-text-muted",
        "--ev4-text-disabled",
        "--ev4-border-subtle",
        "--ev4-border-strong",
        "--ev4-accent-primary",
        "--ev4-accent-hover",
        "--ev4-accent-active",
        "--ev4-focus-ring",
        "--ev4-selection-bg",
        "--ev4-input-bg",
        "--ev4-input-border",
        "--ev4-input-text",
        "--ev4-button-primary-bg",
        "--ev4-button-primary-text",
        "--ev4-button-secondary-bg",
        "--ev4-button-secondary-text",
        "--ev4-disabled-bg",
        "--ev4-disabled-text",
        "--ev4-code-bg",
        "--ev4-shadow-raised",
    }
    for variable in required_css_vars:
        assert variable in css


def test_operator_panel_css_has_explicit_theme_resolution_selectors():
    css = css_custom_properties()

    assert "prefers-color-scheme: dark" in css
    assert ':root[data-theme="light"]' in css
    assert ':root[data-theme="dark"]' in css
    assert "body.light .gradio-container" in css
    assert "body.dark .gradio-container" in css
