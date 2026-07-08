from __future__ import annotations

import re

from ev4_transition.presentation.theme_tokens import THEME_TOKENS


def _rgb(hex_color: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", hex_color)
    if not match:
        raise AssertionError(f"Expected an opaque 6-digit hex color, got {hex_color!r}")
    raw = match.group(1)
    return tuple(int(raw[index : index + 2], 16) / 255 for index in (0, 2, 4))  # type: ignore[return-value]


def _linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    red, green, blue = (_linear(channel) for channel in _rgb(hex_color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


TEXT_PAIRS = {
    "light.primary_on_base": ("light", "text.primary", "surface.base"),
    "light.primary_on_raised": ("light", "text.primary", "surface.raised"),
    "light.secondary_on_raised": ("light", "text.secondary", "surface.raised"),
    "light.muted_on_raised": ("light", "text.muted", "surface.raised"),
    "light.primary_button_text": ("light", "button.primary.text", "button.primary.bg"),
    "light.primary_button_hover_text": ("light", "button.primary.hover.text", "button.primary.hover.bg"),
    "light.secondary_button_text": ("light", "button.secondary.text", "button.secondary.bg"),
    "light.secondary_button_hover_text": ("light", "button.secondary.hover.text", "button.secondary.hover.bg"),
    "light.disabled_text": ("light", "disabled.text", "disabled.bg"),
    "dark.primary_on_base": ("dark", "text.primary", "surface.base"),
    "dark.primary_on_raised": ("dark", "text.primary", "surface.raised"),
    "dark.secondary_on_raised": ("dark", "text.secondary", "surface.raised"),
    "dark.muted_on_raised": ("dark", "text.muted", "surface.raised"),
    "dark.primary_button_text": ("dark", "button.primary.text", "button.primary.bg"),
    "dark.primary_button_hover_text": ("dark", "button.primary.hover.text", "button.primary.hover.bg"),
    "dark.secondary_button_text": ("dark", "button.secondary.text", "button.secondary.bg"),
    "dark.secondary_button_hover_text": ("dark", "button.secondary.hover.text", "button.secondary.hover.bg"),
    "dark.disabled_text": ("dark", "disabled.text", "disabled.bg"),
}

UI_PAIRS = {
    "light.input_border_on_input": ("light", "input.border", "input.bg"),
    "light.focus_ring_on_raised": ("light", "focus.ring", "surface.raised"),
    "light.strong_border_on_raised": ("light", "border.strong", "surface.raised"),
    "dark.input_border_on_input": ("dark", "input.border", "input.bg"),
    "dark.focus_ring_on_raised": ("dark", "focus.ring", "surface.raised"),
    "dark.strong_border_on_raised": ("dark", "border.strong", "surface.raised"),
}

STATUS_PAIRS = {
    "light.success": ("light", "success", "success.bg"),
    "light.warning": ("light", "warning", "warning.bg"),
    "light.danger": ("light", "danger", "danger.bg"),
    "light.info": ("light", "info", "info.bg"),
    "dark.success": ("dark", "success", "success.bg"),
    "dark.warning": ("dark", "warning", "warning.bg"),
    "dark.danger": ("dark", "danger", "danger.bg"),
    "dark.info": ("dark", "info", "info.bg"),
}


def _token_ratio(theme: str, foreground_key: str, background_key: str) -> float:
    tokens = THEME_TOKENS[theme]
    return contrast_ratio(tokens[foreground_key], tokens[background_key])


def test_theme_text_pairs_meet_wcag_aa_normal_text_contrast():
    failures = []
    for label, (theme, foreground, background) in TEXT_PAIRS.items():
        ratio = _token_ratio(theme, foreground, background)
        if ratio < 4.5:
            failures.append(f"{label}: {ratio:.2f}:1")

    assert failures == []


def test_theme_ui_pairs_meet_non_text_contrast():
    failures = []
    for label, (theme, foreground, background) in UI_PAIRS.items():
        ratio = _token_ratio(theme, foreground, background)
        if ratio < 3.0:
            failures.append(f"{label}: {ratio:.2f}:1")

    assert failures == []


def test_status_foreground_background_pairs_are_readable():
    failures = []
    for label, (theme, foreground, background) in STATUS_PAIRS.items():
        ratio = _token_ratio(theme, foreground, background)
        if ratio < 4.5:
            failures.append(f"{label}: {ratio:.2f}:1")

    assert failures == []
