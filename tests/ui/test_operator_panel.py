from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tomllib

from ev4_transition.ui.adapters import (
    CAPABILITY_STATUS_PATH,
    build_capability_rows,
    load_capability_payload,
    render_download_artifacts,
    run_operator_check,
    build_gate_request,
)
from ev4_transition.ui.components import diagnostics_to_rows, ltr_token, status_summary_markdown


ROOT = Path(__file__).resolve().parents[2]


def test_malformed_json_returns_safe_ui_error(tmp_path: Path):
    output = run_operator_check(
        "Validate Stage Evidence Bundle",
        pasted_json='{"schema_version": ',
        output_dir=tmp_path,
    )

    assert output.result["status"] == "invalid"
    assert output.result["diagnostics"][0]["code"] == "PG.SERVICE.MALFORMED_JSON"
    assert "JSON" in output.result["diagnostics"][0]["message"]
    assert output.download_paths


def test_non_object_json_returns_invalid_guard_without_engine_execution(tmp_path: Path):
    output = run_operator_check(
        "Validate Stage Evidence Bundle",
        pasted_json="[]",
        output_dir=tmp_path,
    )

    assert output.result["status"] == "invalid"
    assert output.result["result_type"] == "service_response"
    assert output.result["diagnostics"][0]["code"] == "INPUT_NOT_OBJECT"
    assert output.result["diagnostics"][0]["path"] == "$"


def test_missing_project_gate_schemas_directory_fails_closed(tmp_path: Path):
    project_gate_without_schemas = tmp_path / "EV4-Project-Gate"
    project_gate_without_schemas.mkdir()

    output = run_operator_check(
        "Validate Stage Evidence Bundle",
        pasted_json='{"schema_version": "stage-evidence-bundle.v1"}',
        project_gate_repo_path=str(project_gate_without_schemas),
        output_dir=tmp_path / "out",
    )

    assert output.result["status"] == "insufficient_evidence"
    assert output.result["diagnostics"][0]["code"] == "PG.SERVICE.LOCAL_FILE_ACCESS_FAILED"
    assert output.result["diagnostics"][0]["severity"] == "insufficient_evidence"


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
        output = run_operator_check(transition, pasted_json='{"schema_version": "x"}', output_dir=tmp_path / transition.replace(" ", "_"))

        assert output.result["status"] == "insufficient_evidence"
        assert output.result["status"] != "accepted"
        assert output.result["diagnostics"][0]["code"] == "PG.SERVICE.REPO_PATH_MISSING"
        assert output.result["output"] is None
        assert "checkout path is required" in output.result["diagnostics"][0]["message"]


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

    paths = render_download_artifacts(result, tmp_path)

    assert result == before
    assert {Path(path).name for path in paths} == {"result.json", "report.md", "report.html"}
    loaded = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
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

    paths = render_download_artifacts(result, tmp_path)
    html_path = next(Path(path) for path in paths if Path(path).name == "report.html")
    html = html_path.read_text(encoding="utf-8")

    assert "&lt;/pre&gt;&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "</pre><script>" not in html
    assert "<script>alert(1)</script>" not in html


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


def test_download_artifact_failure_logs_and_cleans_temporary_directory(monkeypatch, caplog, tmp_path: Path):
    import logging
    import ev4_transition.ui.adapters as adapters

    temp_dir = tmp_path / "orphan_candidate"
    monkeypatch.setattr(adapters.tempfile, "mkdtemp", lambda prefix: str(temp_dir))

    def raise_os_error(self, *args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(adapters.Path, "write_text", raise_os_error)
    with caplog.at_level(logging.ERROR, logger=adapters.__name__):
        paths = render_download_artifacts({"status": "invalid", "diagnostics": []})

    assert paths == []
    assert not temp_dir.exists()
    assert any("Failed to render download artifacts" in record.message for record in caplog.records)


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
