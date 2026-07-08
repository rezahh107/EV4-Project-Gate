from __future__ import annotations

from ev4_transition.presentation.theme_tokens import STATUS_NAMES, THEME_TOKENS, assert_theme_contract, css_custom_properties


def test_final_theme_contract_requires_status_icon_label_and_tone():
    assert_theme_contract()

    for theme in ("light", "dark"):
        for status in STATUS_NAMES:
            token = THEME_TOKENS[theme][f"status.{status}"]
            assert token["icon"]
            assert token["label"]
            assert token["tone"] in {"success", "warning", "danger"}
            assert token["foreground"].startswith("#")
            assert token["background"].startswith("#")


def test_final_dark_theme_is_not_pure_black_or_simple_white_inversion():
    dark = THEME_TOKENS["dark"]
    light = THEME_TOKENS["light"]

    assert dark["surface.base"] not in {"#000", "#000000"}
    assert dark["surface.raised"] != dark["surface.base"]
    assert dark["text.primary"] not in {"#fff", "#ffffff"}
    assert light["surface.base"] != dark["text.primary"]


def test_final_css_exports_focus_code_status_and_component_custom_properties():
    css = css_custom_properties()

    assert "--ev4-focus-ring" in css
    assert "--ev4-code-bg" in css
    assert "--ev4-input-border" in css
    assert "--ev4-button-primary-text" in css
    assert "--ev4-button-primary-hover-text" in css
    assert "--ev4-button-secondary-hover-text" in css
    assert "--ev4-disabled-text" in css
    assert "--ev4-surface-dialog" in css
    assert "--ev4-status-accepted-fg" in css
    assert "--ev4-status-repair-fg" in css
    assert "--ev4-status-warning-fg" in css
    assert "--ev4-status-danger-fg" in css
