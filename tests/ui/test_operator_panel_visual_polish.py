from __future__ import annotations

from ev4_transition.ui.app import HEADER_WARNING_FA, operator_header_html, operator_panel_css
from ev4_transition.ui.components import status_summary_markdown


def test_operator_header_is_compact_rtl_and_scope_safe():
    html = operator_header_html()

    assert '<section lang="fa" dir="rtl"' in html
    assert 'class="ev4-app ev4-shell ev4-rtl"' in html
    assert '<bdi dir="ltr">EV4 Project Gate</bdi>' in html
    assert "پنل محلی بررسی گذارها" in html
    assert HEADER_WARNING_FA in html
    assert "Elementor" in html
    assert "Responsive" in html
    assert "gate runner" in html


def test_operator_panel_css_uses_rtl_ltr_and_token_classes():
    css = operator_panel_css()

    assert ".ev4-header" in css
    assert ".ev4-section" in css
    assert ".ev4-status-card" in css
    assert ".ev4-ltr" in css
    assert "unicode-bidi: isolate" in css
    assert "letter-spacing: normal" in css
    assert "var(--ev4-surface-raised)" in css
    assert "var(--ev4-border-subtle)" in css
    assert "var(--ev4-code-bg)" in css
    assert "var(--ev4-shadow-raised)" in css
    assert "prefers-color-scheme: dark" in css


def test_status_summary_keeps_persian_status_rtl_and_technical_meta_ltr():
    rendered = status_summary_markdown({"status": "insufficient_evidence", "diagnostics": []})

    assert '<section lang="fa" dir="rtl" role="status"' in rendered
    assert 'class="ev4-status-content"' in rendered
    assert "⚠️" in rendered
    assert "شواهد کافی نیست" in rendered
    assert '<span dir="ltr">status</span>' in rendered
    assert '<bdi dir="ltr"><code>insufficient_evidence</code></bdi>' in rendered
    assert '<span dir="ltr">semantic tone</span>' in rendered
