from __future__ import annotations

from ev4_transition.ui.app import operator_panel_css


def test_operator_panel_css_styles_radio_indicators_explicitly():
    css = operator_panel_css()

    required_fragments = [
        'input[type="radio"]',
        'input[type="radio"]:checked',
        'input[type="radio"]:focus-visible',
        "appearance: none",
        "--ev4-control-indicator-bg",
        "--ev4-control-indicator-border",
        "--ev4-control-indicator-checked-bg",
        "--ev4-control-indicator-checked-dot",
        "--ev4-control-indicator-focus-ring",
        "radial-gradient(circle, var(--ev4-control-indicator-checked-dot)",
    ]
    for fragment in required_fragments:
        assert fragment in css


def test_operator_panel_css_has_dark_header_anti_white_island_selectors():
    css = operator_panel_css()

    required_fragments = [
        "body.dark .ev4-header",
        ".dark .ev4-header",
        ':root[data-theme="dark"] .ev4-header',
        "linear-gradient(145deg, var(--ev4-surface-raised), var(--ev4-surface-overlay))",
        "@media (prefers-color-scheme: dark)",
        "body:not(.light) .ev4-header",
    ]
    for fragment in required_fragments:
        assert fragment in css

    assert ".ev4-header { padding: 1.15rem 1.25rem; }" in css
    assert "background: var(--ev4-surface-raised);" in css
