from ev4_transition.presentation.theme_tokens import THEME_TOKENS, assert_theme_contract


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
        "text.primary",
        "text.secondary",
        "border.default",
    }
    for theme in ("light", "dark"):
        assert required <= set(THEME_TOKENS[theme])


def test_focus_token_exists_for_light_and_dark_if_themed_report_exists():
    assert THEME_TOKENS["light"]["focus.ring"]
    assert THEME_TOKENS["dark"]["focus.ring"]
    assert THEME_TOKENS["light"]["focus.ring"] != THEME_TOKENS["dark"]["focus.ring"]
