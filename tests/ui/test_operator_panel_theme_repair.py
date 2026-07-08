from __future__ import annotations

from types import SimpleNamespace

from ev4_transition.ui.app import operator_panel_css, operator_run_outputs


def test_operator_run_outputs_returns_canonical_json_preview_string():
    output = SimpleNamespace(
        status_markdown="status",
        diagnostics_rows=[],
        capability_rows=[],
        json_preview='{"status":"invalid"}',
        result={"status": "invalid"},
        download_paths=[],
    )

    rendered = operator_run_outputs(output)

    assert isinstance(rendered[3], str)
    assert rendered[3] == output.json_preview
    assert rendered[3] != output.result


def test_operator_panel_css_defines_button_hover_states():
    css = operator_panel_css()

    assert "--ev4-button-primary-hover-bg" in css
    assert "--ev4-button-primary-hover-text" in css
    assert "--ev4-button-secondary-hover-bg" in css
    assert "--ev4-button-secondary-hover-text" in css
    assert 'button:not(.primary):not([variant="primary"]):hover' in css
