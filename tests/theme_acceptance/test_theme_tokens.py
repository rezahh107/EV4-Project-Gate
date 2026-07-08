from ev4_transition.presentation.theme_tokens import THEME_TOKENS, REQUIRED_TOKEN_KEYS, assert_theme_contract


def test_dark_theme_is_not_simple_inversion():
    assert_theme_contract()
    light = THEME_TOKENS["light"]
    dark = THEME_TOKENS["dark"]
    assert light["surface.base"] != dark["text.primary"]
    assert dark["surface.raised"] != light["surface.raised"]


def test_light_and_dark_tokens_exist_if_themed_report_exists():
    required = {
        "status.accepted",
        "status.repair_needed",
        "status.insufficient_evidence",
        "status.invalid",
        "surface.base",
        "surface.raised",
        "surface.dialog",
        "text.primary",
        "text.secondary",
        "text.disabled",
        "border.default",
        "accent.active",
        "button.primary.text",
        "input.border",
        "disabled.text",
    }
    for theme in ("light", "dark"):
        assert required <= set(THEME_TOKENS[theme])
        assert set(REQUIRED_TOKEN_KEYS) <= set(THEME_TOKENS[theme])


def test_focus_token_exists_for_light_and_dark_if_themed_report_exists():
    assert THEME_TOKENS["light"]["focus.ring"]
    assert THEME_TOKENS["dark"]["focus.ring"]
    assert THEME_TOKENS["light"]["focus.ring"] != THEME_TOKENS["dark"]["focus.ring"]


def test_dark_theme_avoids_pure_black_and_pure_white_body_text():
    dark = THEME_TOKENS["dark"]
    assert dark["surface.base"].lower() != "#000000"
    assert dark["text.primary"].lower() != "#ffffff"


def test_status_tokens_include_meaning_fields_across_themes():
    tones = {}
    for theme in ("light", "dark"):
        tones[theme] = {}
        for status in ("accepted", "repair_needed", "insufficient_evidence", "invalid"):
            token = THEME_TOKENS[theme][f"status.{status}"]
            assert {"tone", "foreground", "background", "icon", "label"} <= set(token)
            tones[theme][status] = token["tone"]
    assert tones["light"] == tones["dark"]


def test_gradio_css_uses_semantic_custom_properties():
    from ev4_transition.presentation.theme_tokens import css_custom_properties

    css = css_custom_properties()
    assert "--ev4-surface-base" in css
    assert "--ev4-focus-ring" in css
    assert "--ev4-button-primary-text" in css
    assert "prefers-color-scheme: dark" in css
