from __future__ import annotations

from ev4_transition.presentation.theme_tokens import THEME_TOKENS, assert_theme_contract, css_custom_properties


def test_operator_panel_semantic_tokens_exist_across_light_and_dark():
    required = {
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
        "shadow.raised",
    }

    assert_theme_contract()
    for theme in ("light", "dark"):
        assert required <= set(THEME_TOKENS[theme])


def test_operator_panel_css_exports_extended_custom_properties():
    css = css_custom_properties()

    assert "--ev4-surface-overlay" in css
    assert "--ev4-border-subtle" in css
    assert "--ev4-border-strong" in css
    assert "--ev4-accent-primary" in css
    assert "--ev4-accent-hover" in css
    assert "--ev4-code-bg" in css
    assert "--ev4-shadow-raised" in css
