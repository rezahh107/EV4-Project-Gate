from ev4_transition.presentation.status_mapping import presentation_for_status
from ev4_transition.reports import render_markdown_report, render_plain_summary


def _result(status="insufficient_evidence"):
    return {
        "status": status,
        "diagnostics": [
            {"code": "PG_TEST_001", "severity": "insufficient_evidence", "message": "Missing evidence.", "path": "$.evidence[0]"}
        ],
        "schema_id": "transition-result.v1",
    }


def test_status_uses_icon_text_and_token():
    rendered = render_markdown_report(_result("accepted"))
    assert "✅" in rendered
    assert "پذیرفته شد" in rendered
    assert "data-token=\"status.accepted\"" in rendered
    assert "semantic tone" in rendered


def test_insufficient_evidence_uses_warning():
    presentation = presentation_for_status("insufficient_evidence")
    assert presentation.icon == "⚠️"
    assert presentation.tone == "warning"
    assert presentation.persian_label == "شواهد کافی نیست"


def test_status_color_is_not_only_signal():
    rendered = render_markdown_report(_result("repair_needed"))
    assert "🛠️" in rendered
    assert "نیازمند اصلاح" in rendered
    assert "data-tone=\"warning\"" in rendered
    assert "status.repair_needed" in rendered


def test_error_text_has_next_action():
    rendered = render_plain_summary(_result("invalid"))
    assert "اقدام بعدی" in rendered
    assert "دوباره اجرا" in rendered


def test_advanced_diagnostics_section_exists():
    rendered = render_markdown_report(_result())
    assert "جزئیات پیشرفته / Evidence / Diagnostics" in rendered
    assert "Diagnostics" in rendered
    assert "PG_TEST_001" in rendered
