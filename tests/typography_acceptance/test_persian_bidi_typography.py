from ev4_transition.presentation.bidi import LTR_ISOLATE_START, ISOLATE_END, isolate_ltr_text, markdown_code_ltr
from ev4_transition.reports import render_markdown_report


def test_persian_report_container_is_rtl():
    rendered = render_markdown_report({"status": "accepted", "diagnostics": []})
    assert '<section lang="fa" dir="rtl"' in rendered


def test_technical_fragments_are_ltr_isolated():
    fragment = markdown_code_ltr("schemas/stage-bundle/stage-bundle.v1.schema.json")
    assert '<bdi dir="ltr"><code>' in fragment
    assert "</code></bdi>" in fragment


def test_code_paths_hashes_are_copyable():
    path = "contracts/locks/final-gate.v1.lock.json"
    digest = "a" * 64
    rendered = render_markdown_report({"status": "accepted", "diagnostics": [], "artifact_path": path, "sha256": digest})
    assert f"<code>{path}</code>" in rendered
    assert f"<code>{digest}</code>" in rendered


def test_diagnostic_codes_are_ltr():
    rendered = render_markdown_report({"status": "invalid", "diagnostics": [{"code": "PG_OUTPUT_001", "severity": "error", "message": "x", "path": "$"}]})
    assert '<bdi dir="ltr"><code>PG_OUTPUT_001</code></bdi>' in rendered


def test_plain_text_ltr_isolation_uses_unicode_isolates():
    isolated = isolate_ltr_text("PG-UNICODE-001")
    assert isolated.startswith(LTR_ISOLATE_START)
    assert isolated.endswith(ISOLATE_END)
