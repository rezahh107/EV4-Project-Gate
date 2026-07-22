from __future__ import annotations

from ev4_transition.service.report_publication import publish_result_payload
from copy import deepcopy
import json
from pathlib import Path
import tomllib

from ev4_transition.ui.adapters import (
    CAPABILITY_STATUS_PATH,
    build_capability_rows,
    load_capability_payload,
    run_operator_check,
    build_gate_request,
)
from ev4_transition.ui.components import diagnostics_to_rows, ltr_token, status_summary_markdown
from ev4_transition.ui.app import run_authoritative_preflight
from ev4_transition.service import run_preflight


ROOT = Path(__file__).resolve().parents[2]


def test_malformed_json_returns_safe_ui_error(tmp_path: Path):
    result, token = run_authoritative_preflight(
        "Validate Stage Evidence Bundle", "pinned_owner_file_computation",
        '{"schema_version": ', None, str(ROOT), None, None, None, None, None, str(tmp_path),
    )
    assert result.status == "blocked"
    assert token is None
    assert any("PG.SERVICE.MALFORMED_JSON" in str(check.technical_detail) for check in result.checks)


def test_non_object_json_returns_invalid_guard_without_engine_execution(tmp_path: Path):
    result, token = run_authoritative_preflight(
        "Validate Stage Evidence Bundle", "pinned_owner_file_computation",
        "[]", None, str(ROOT), None, None, None, None, None, str(tmp_path),
    )
    assert result.status == "blocked"
    assert token is None
    assert any(check.id == "json.source.not_object" for check in result.checks)


def test_missing_project_gate_schemas_directory_fails_closed(tmp_path: Path):
    project_gate_without_schemas = tmp_path / "EV4-Project-Gate"
    project_gate_without_schemas.mkdir()
    request = build_gate_request(
        "Architect → CE",
        pasted_json='{"schema_version":"stage-evidence-bundle.v1","stage":"architect"}',
        project_gate_repo_path=str(project_gate_without_schemas),
        architect_repo_path=str(tmp_path / "missing-a"),
        ce_repo_path=str(tmp_path / "missing-ce"),
        output_dir=tmp_path / "out",
    )
    result = run_preflight(request)
    assert result.status == "blocked"
    assert any(check.id.endswith("does_not_exist") for check in result.checks)


def test_status_rendering_uses_icon_and_text():
    cases = {
        "accepted": ("✅", "پذیرفته شد"),
        "valid": ("✅", "پذیرفته شد"),
        "invalid": ("❌", "نامعتبر"),
        "insufficient_evidence": ("⚠️", "شواهد کافی نیست"),
        "repair_needed": ("🛠️", "نیازمند اصلاح"),
    }

    for status, (icon, label) in cases.items():
        rendered = status_summary_markdown({"status": status, "diagnostics": []})
        assert icon in rendered
        assert label in rendered
        assert "status:" in rendered
        assert "semantic tone:" in rendered


def test_diagnostics_rendering_preserves_code_severity_and_path():
    rows = diagnostics_to_rows(
        [
            {
                "code": "PG_UI_TEST",
                "severity": "insufficient_evidence",
                "path": "$.evidence[0].artifact_hash.value",
                "message": "Missing evidence.",
                "details": {"repository": "rezahh107/EV4-Project-Gate", "next_action": "Add evidence."},
            }
        ]
    )

    assert len(rows) == 1
    row_text = " ".join(rows[0])
    assert "PG_UI_TEST" in row_text
    assert "insufficient_evidence" in row_text
    assert "$.evidence[0].artifact_hash.value" in row_text
    assert "rezahh107/EV4-Project-Gate" in row_text


def test_ltr_isolation_helper_wraps_technical_tokens_and_handles_none():
    token = ltr_token("schemas/stage-bundle/stage-bundle.v1.schema.json")
    numeric_token = ltr_token(28)

    assert token.startswith("\u2066")
    assert token.endswith("\u2069")
    assert "schemas/stage-bundle/stage-bundle.v1.schema.json" in token
    assert numeric_token.startswith("\u2066")
    assert "28" in numeric_token
    assert ltr_token(None) == ""


def test_capability_inspector_reads_without_mutating_source_file():
    before = CAPABILITY_STATUS_PATH.read_text(encoding="utf-8")
    payload = load_capability_payload()
    rows = build_capability_rows()
    after = CAPABILITY_STATUS_PATH.read_text(encoding="utf-8")

    assert payload["schema_version"] == "ev4-project-gate-capability-status.v1"
    assert rows
    assert before == after


def test_packaged_capability_truth_exposes_ui_service_routing():
    payload = load_capability_payload()
    ui = payload["capabilities"]["user_interface"]
    rows = build_capability_rows()
    ui_row = next(row for row in rows if row[0] == "UI")

    assert ui["status"] == "implemented_initial_operator_panel"
    assert ui["service_routing"] == "implemented_prompt_06_fail_closed"
    assert ui["browser_accessibility_evidence"] == "insufficient_evidence"
    assert "implemented_prompt_06_fail_closed" in " ".join(ui_row)
    assert "insufficient_evidence" in " ".join(ui_row)


def test_unavailable_transition_is_marked_and_does_not_fake_execution(tmp_path: Path):
    for transition in ["CE → Builder", "Builder → Responsive", "Final Evidence Gate"]:
        request = build_gate_request(transition, pasted_json='{"schema_version":"x"}', output_dir=tmp_path / transition.replace(" ", "_"))
        result = run_preflight(request)
        assert result.status == "blocked"
        assert any(check.status == "error" for check in result.checks)


def test_report_and_result_rendering_does_not_mutate_original_result(tmp_path: Path):
    result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "ui_guard",
        "status": "repair_needed",
        "diagnostics": [
            {
                "code": "PG_UI_REPAIR",
                "severity": "warning",
                "message": "Repair is needed.",
                "path": "$.payload",
            }
        ],
        "output": {"path": "fixtures/example.json"},
    }
    before = deepcopy(result)

    paths = publish_result_payload(result, tmp_path)[2]

    assert result == before
    assert {Path(path).name for path in paths} == {"result.json", "report.md", "report.html"}
    result_path = next(Path(path) for path in paths if Path(path).name == "result.json")
    loaded = json.loads(result_path.read_text(encoding="utf-8"))
    assert loaded == before


def test_html_report_escapes_untrusted_json_payload(tmp_path: Path):
    payload = '</pre><script>alert(1)</script>'
    result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "status": "invalid",
        "diagnostics": [
            {
                "code": "PG.UI.XSS_REGRESSION",
                "severity": "error",
                "message": payload,
                "path": "$.payload",
            }
        ],
        "output": {"untrusted": payload},
    }

    paths = publish_result_payload(result, tmp_path)[2]
    html_path = next(Path(path) for path in paths if Path(path).name == "report.html")
    html = html_path.read_text(encoding="utf-8")

    assert "&lt;/pre&gt;&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "</pre><script>" not in html
    assert "<script>alert(1)</script>" not in html


def test_partial_download_artifact_failure_removes_written_files(monkeypatch, tmp_path: Path):
    import ev4_transition.io.safe_publication as publication
    real_link = publication.os.link
    calls = {"count": 0}
    def fail_second(source, destination, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("second publication failed")
        return real_link(source, destination, **kwargs)
    monkeypatch.setattr(publication.os, "link", fail_second)
    paths = publish_result_payload({"status": "invalid", "diagnostics": []}, tmp_path)[2]
    assert paths == []
    attempts = list(tmp_path.glob("run-*"))
    assert len(attempts) == 1
    assert list(attempts[0].iterdir()) == []


def test_markdown_report_neutralizes_triple_backtick_without_mutating_result_json(tmp_path: Path):
    payload = "```breakout"
    result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "status": "invalid",
        "diagnostics": [{"code": "PG.UI.MD_FENCE", "severity": "error", "message": payload, "path": "$.payload"}],
        "output": {"untrusted": payload},
    }

    paths = publish_result_payload(result, tmp_path)[2]
    md = next(Path(path) for path in paths if Path(path).name == "report.md").read_text(encoding="utf-8")
    result_path = next(Path(path) for path in paths if Path(path).name == "result.json")
    loaded_json = json.loads(result_path.read_text(encoding="utf-8"))

    assert loaded_json == result
    assert "```breakout" not in md
    assert "``​`breakout" in md
    assert "## Raw diagnostics" in md
    assert "## Raw JSON result" in md
    assert md.count("```") == 4
    assert {Path(path).name for path in paths} == {"result.json", "report.md", "report.html"}


def test_gradio_is_optional_ui_dependency_only():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]
    ui_dependencies = pyproject["project"]["optional-dependencies"]["ui"]

    assert not any(dependency.startswith("gradio") for dependency in dependencies)
    assert any(dependency.startswith("gradio") for dependency in ui_dependencies)
    assert pyproject["project"]["scripts"]["ev4-project-gate-ui"] == "ev4_transition.ui.app:main"


def test_unhandled_ui_exception_is_logged_without_primary_traceback(monkeypatch, caplog, tmp_path: Path):
    import logging
    import ev4_transition.ui.adapters as adapters

    def explode(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(adapters, "build_gate_request", explode)
    with caplog.at_level(logging.ERROR, logger=adapters.__name__):
        output = run_operator_check("Validate Stage Evidence Bundle", pasted_json='{"schema_version":"x"}', output_dir=tmp_path)

    assert output.result["status"] == "invalid"
    assert output.result["diagnostics"][0]["code"] == "PG.UI.UNHANDLED_EXCEPTION"
    assert "Traceback" not in output.status_markdown
    assert any("Unhandled exception in UI operator check" in record.message for record in caplog.records)
    assert any(record.exc_info for record in caplog.records)


def test_download_artifact_failure_returns_no_paths(monkeypatch, tmp_path: Path):
    import ev4_transition.service.report_publication as reports
    def fail_attempt(*args, **kwargs):
        raise OSError("disk unavailable")
    monkeypatch.setattr(reports, "prepare_attempt_paths", fail_attempt)
    paths = publish_result_payload({"status": "invalid", "diagnostics": []}, tmp_path)[2]
    assert paths == []


def test_finalize_failure_returns_safe_invalid_output(monkeypatch, caplog, tmp_path: Path):
    import logging
    import ev4_transition.ui.adapters as adapters

    def fail_finalize(*args, **kwargs):
        raise RuntimeError("capability file vanished")

    monkeypatch.setattr(adapters, "_finalize", fail_finalize)
    with caplog.at_level(logging.ERROR, logger=adapters.__name__):
        output = run_operator_check("Inspect Capabilities", output_dir=tmp_path)

    assert output.result["status"] == "invalid"
    assert output.result["diagnostics"][0]["code"] == "PG.UI.CRITICAL_FINALIZATION_FAILURE"
    assert "Traceback" not in output.status_markdown
    assert output.download_paths == []
    assert any("Critical failure while finalizing UI operator output" in record.message for record in caplog.records)
    assert any(record.exc_info for record in caplog.records)


def test_ui_adapter_builds_gate_request_for_all_service_choices(tmp_path: Path):
    paths = {
        "project_gate_repo_path": str(tmp_path / "pg"),
        "architect_repo_path": str(tmp_path / "architect"),
        "ce_repo_path": str(tmp_path / "ce"),
        "builder_repo_path": str(tmp_path / "builder"),
        "responsive_repo_path": str(tmp_path / "responsive"),
    }
    cases = {
        "Validate Stage Evidence Bundle": "validate_bundle",
        "Inspect Capabilities": "inspect_capabilities",
        "Architect → CE": "architect_to_ce",
        "CE → Builder": "ce_to_builder",
        "Builder → Responsive": "builder_to_responsive",
        "Final Evidence Gate": "final_gate",
    }
    for label, choice in cases.items():
        request = build_gate_request(label, pasted_json='{"schema_version":"x"}', **paths)
        assert request.transition_choice == choice
        assert request.repo_paths.ce_repo_path == paths["ce_repo_path"]
        assert request.repo_paths.builder_repo_path == paths["builder_repo_path"]


def test_ui_calls_internal_service_layer(monkeypatch, tmp_path: Path):
    calls = {}

    class FakeResponse:
        def to_dict(self):
            return {
                "status": "insufficient_evidence",
                "transition_choice": "ce_to_builder",
                "service_diagnostics": [{"code": "PG.TEST", "severity": "insufficient_evidence", "message": "missing", "path": "$"}],
                "engine_result": None,
                "capabilities_snapshot": load_capability_payload(),
                "download_filenames": {},
                "report_bundle": {},
                "user_message_fa": "⚠️ شواهد کافی نیست.",
                "next_action_fa": "مسیرها را کامل کن.",
            }

    import ev4_transition.ui.adapters as adapters

    def fake_run_gate_request(request):
        calls["choice"] = request.transition_choice
        calls["ce"] = request.repo_paths.ce_repo_path
        calls["builder"] = request.repo_paths.builder_repo_path
        return FakeResponse()

    monkeypatch.setattr(adapters, "run_gate_request", fake_run_gate_request)
    output = run_operator_check("CE → Builder", pasted_json='{"schema_version":"x"}', ce_repo_path="/tmp/ce", builder_repo_path="/tmp/builder", output_dir=tmp_path)

    assert output.result["status"] == "insufficient_evidence"
    assert calls == {"choice": "ce_to_builder", "ce": "/tmp/ce", "builder": "/tmp/builder"}
