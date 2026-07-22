from __future__ import annotations

from ev4_transition.service.report_publication import publish_result_payload
import json
from pathlib import Path

from ev4_transition.service.guidance import build_operator_guidance, classify_output_state, load_guidance_registry
from ev4_transition.ui.adapters import build_gate_request
from ev4_transition.service import run_preflight
from ev4_transition.ui.components import status_summary_markdown


KNOWN_CODES = {
    "PG.SERVICE.REPO_PATH_MISSING",
    "PG.SERVICE.LOCAL_FILE_ACCESS_FAILED",
    "PG_A2C_EXTERNAL_FILE_READ_FAILED",
    "PG_A2C_EXTERNAL_HASH_MISMATCH",
    "PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED",
    "PG_A2C_CE_SCHEMA_VALIDATION_FAILED",
    "PG_A2C_SOURCE_SCHEMA_ID_MISMATCH",
    "PG_A2C_WRONG_SOURCE_STAGE",
    "PG.UI.UNHANDLED_EXCEPTION",
    "PG.UI.REPORT_WRITE_FAILED",
}


def _result(code: str, *, status: str = "invalid", choice: str = "architect_to_ce", path: str = "$.payload.data", message: str = "failure") -> dict:
    return {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": choice,
        "status": status,
        "diagnostics": [
            {
                "code": code,
                "severity": "insufficient_evidence" if status == "insufficient_evidence" else "error",
                "message": message,
                "path": path,
            }
        ],
        "engine_result": None,
        "output": None,
    }


def test_guidance_registry_loads_and_covers_known_diagnostic_codes():
    registry = load_guidance_registry()

    assert KNOWN_CODES <= set(registry)
    assert registry["PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED"].repair_prompt_template == "architect_schema_repair_v1"


def test_valid_status_without_primary_diagnostic_uses_success_guidance_not_invalid_fallback():
    result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": "architect_to_ce",
        "status": "valid",
        "diagnostics": [],
        "output": {"stage": "ce"},
    }
    guidance = build_operator_guidance(result)

    assert guidance.safe_to_continue is True
    assert "diagnostic مسدودکننده ثبت نشده" in guidance.current_problem_fa
    assert "production/readiness proof نیست" in " ".join(guidance.next_actions_fa)
    assert "نامعتبر" not in guidance.current_problem_fa
    assert all("خطادار" not in action for action in guidance.next_actions_fa)


def test_repo_path_missing_produces_persian_next_action_about_local_paths():
    guidance = build_operator_guidance(_result("PG.SERVICE.REPO_PATH_MISSING", status="insufficient_evidence", path="$.repo_paths.ce_repo_path"))
    text = " ".join([guidance.current_problem_fa, *guidance.next_actions_fa, guidance.where_stopped_fa])

    assert "مسیر" in text
    assert "local" in text or "checkout" in text
    assert guidance.safe_to_continue is False


def test_external_file_read_failed_guides_missing_pinned_files_or_stale_checkout():
    guidance = build_operator_guidance(_result("PG_A2C_EXTERNAL_FILE_READ_FAILED", status="insufficient_evidence"))
    text = " ".join([guidance.current_problem_fa, *guidance.next_actions_fa])

    assert "pin" in text or "pin‌شده" in text
    assert "checkout" in text


def test_architect_schema_failure_explains_outdated_or_invalid_architect_bundle():
    guidance = build_operator_guidance(
        _result(
            "PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED",
            path="$.payload.data.approved_structure_model.structure_nodes[0].node_kind",
            message="'legacy_section' is not one of ['section', 'container']",
        )
    )
    text = " ".join([guidance.current_problem_fa, *guidance.next_actions_fa])

    assert "Architect" in text
    assert "schema" in text
    assert "دوباره تولید" in text or "repair prompt" in text
    assert guidance.repair_prompt_fa_or_en


def test_output_null_is_classified_as_no_downstream_package_produced():
    guidance = build_operator_guidance(_result("PG_A2C_WRONG_SOURCE_STAGE"))

    assert classify_output_state(_result("PG_A2C_WRONG_SOURCE_STAGE")) == "no_output_because_invalid"
    assert "خیر" in guidance.output_state_fa
    assert "output برابر null" in guidance.output_state_fa


def test_validate_bundle_accepted_is_validation_only_not_ce_input():
    result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": "validate_bundle",
        "status": "accepted",
        "diagnostics": [],
        "output": None,
    }
    guidance = build_operator_guidance(result)

    assert classify_output_state(result) == "validation_only_no_transition"
    assert guidance.safe_to_continue is False
    assert "transition" in guidance.output_state_fa
    assert "CE" not in guidance.headline_fa


def test_repair_prompt_generation_includes_diagnostic_paths_and_messages():
    result = _result(
        "PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED",
        path="$.payload.data.architect_intent.dynamic_loop_intent.status",
        message="'old' is not one of ['confirmed', 'not_applicable']",
    )
    prompt = build_operator_guidance(result).repair_prompt_fa_or_en

    assert prompt is not None
    assert "$.payload.data.architect_intent.dynamic_loop_intent.status" in prompt
    assert "'old' is not one of" in prompt
    assert "Return only the corrected full JSON" in prompt


def test_status_summary_group_count_uses_html_code_not_literal_markdown_backticks():
    rendered = status_summary_markdown(_result("PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED"))

    assert "count: <bdi dir=\"ltr\"><code>1</code></bdi>" in rendered
    assert "count: `1`" not in rendered


def test_report_html_preserves_persian_rtl_and_raw_json_ltr(tmp_path: Path):
    result = _result("PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED", message="schema mismatch")
    paths = publish_result_payload(result, tmp_path)[2]
    html_path = next(Path(path) for path in paths if Path(path).name == "report.html")
    html = html_path.read_text(encoding="utf-8")

    assert '<html lang="fa" dir="rtl">' in html
    assert '<pre dir="ltr">' in html
    assert "راهنمای عملیاتی" in html
    assert "Raw JSON result" in html


def test_main_guidance_does_not_expose_raw_traceback():
    result = _result("PG.UI.UNHANDLED_EXCEPTION", message="Traceback (most recent call last):\nFile secret.py line 1")
    rendered = status_summary_markdown(result)

    assert "Traceback" not in rendered
    assert "secret.py" not in rendered
    assert "جزئیات runtime" in rendered


def test_ui_preflight_rejects_project_gate_result_json_as_transition_input(tmp_path: Path):
    prior_result = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": "validate_bundle",
        "status": "accepted",
        "diagnostics": [],
        "output": None,
    }
    request = build_gate_request(
        "Architect → CE",
        pasted_json=json.dumps(prior_result),
        architect_repo_path="/tmp/architect-not-used",
        ce_repo_path="/tmp/ce-not-used",
        output_dir=tmp_path,
    )
    result = run_preflight(request)
    assert result.status == "blocked"
    assert any(check.id == "json.source.project_gate_result" for check in result.checks)


def test_ui_preflight_rejects_wrong_stage_for_selected_transition(tmp_path: Path):
    architect_bundle = {
        "schema_version": "stage-evidence-bundle.v1",
        "stage": "architect",
        "payload_schema": {"id": "ev4-architect-stage-payload@1.0.0"},
        "payload": {"data": {}},
    }
    request = build_gate_request(
        "CE → Builder",
        pasted_json=json.dumps(architect_bundle),
        ce_repo_path="/tmp/ce-not-used",
        builder_repo_path="/tmp/builder-not-used",
        output_dir=tmp_path,
    )
    result = run_preflight(request)
    assert result.status == "blocked"
    assert any(check.id == "json.source.wrong_stage" for check in result.checks)
