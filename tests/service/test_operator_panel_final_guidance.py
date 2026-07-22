from __future__ import annotations

from ev4_transition.service.report_publication import publish_result_payload
from pathlib import Path

from ev4_transition.service.guidance import build_operator_guidance, classify_output_state, load_guidance_registry
from ev4_transition.ui.components import status_summary_markdown


REQUIRED_GUIDANCE_CODES = {
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


def _result(code: str, *, status: str = "invalid", choice: str = "architect_to_ce", output=None) -> dict:
    return {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": choice,
        "status": status,
        "diagnostics": [
            {
                "code": code,
                "severity": "insufficient_evidence" if status == "insufficient_evidence" else "error",
                "message": "schema mismatch",
                "path": "$.payload.data.node",
            }
        ],
        "engine_result": None,
        "output": output,
    }


def test_final_guidance_registry_covers_required_operator_codes():
    registry = load_guidance_registry()

    assert REQUIRED_GUIDANCE_CODES <= set(registry)


def test_final_output_state_language_distinguishes_validation_only_and_transition_output():
    validation_only = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": "validate_bundle",
        "status": "accepted",
        "diagnostics": [],
        "output": None,
    }
    produced = {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": "architect_to_ce",
        "status": "accepted",
        "diagnostics": [],
        "output": {"schema_version": "stage-evidence-bundle.v1", "stage": "ce"},
    }

    validation_guidance = build_operator_guidance(validation_only)
    produced_guidance = build_operator_guidance(produced)

    assert classify_output_state(validation_only) == "validation_only_no_transition"
    assert "فقط" in validation_guidance.output_state_fa
    assert "CE input bundle" in produced_guidance.output_state_fa
    assert produced_guidance.safe_to_continue is True


def test_final_invalid_and_accepted_summaries_keep_gate_scope_not_readiness_claims():
    invalid_guidance = build_operator_guidance(_result("PG_A2C_WRONG_SOURCE_STAGE", status="invalid"))
    accepted_summary = status_summary_markdown(
        {
            "schema_version": "ev4-project-gate-ui-result.v1",
            "result_type": "service_response",
            "transition_choice": "architect_to_ce",
            "status": "accepted",
            "diagnostics": [],
            "output": {"stage": "ce"},
        }
    )

    assert "متوقف شد" in invalid_guidance.headline_fa
    assert "production failure" not in invalid_guidance.current_problem_fa
    assert "هشدار محدوده" in accepted_summary
    assert "اثبات نهایی تولید" in accepted_summary


def test_final_report_html_has_rtl_shell_ltr_code_blocks_and_ltr_diagnostic_identifiers(tmp_path: Path):
    result = _result("PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED")
    paths = publish_result_payload(result, tmp_path)[2]
    html = next(Path(path) for path in paths if Path(path).name == "report.html").read_text(encoding="utf-8")

    assert '<html lang="fa" dir="rtl">' in html
    assert '<pre dir="ltr"><code>' in html
    assert "Raw diagnostics" in html
    assert '<bdi dir="ltr"><code>PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED</code></bdi>' in html
    assert '<bdi dir="ltr"><code>$.payload.data.node</code></bdi>' in html


def test_final_report_markdown_includes_preflight_raw_diagnostics_and_raw_json(tmp_path: Path):
    result = _result("PG_A2C_EXTERNAL_HASH_MISMATCH", status="insufficient_evidence")
    paths = publish_result_payload(result, tmp_path)[2]
    markdown = next(Path(path) for path in paths if Path(path).name == "report.md").read_text(encoding="utf-8")

    assert "## Preflight summary" in markdown
    assert "## Raw diagnostics" in markdown
    assert "## Raw JSON result" in markdown
    assert "PG_A2C_EXTERNAL_HASH_MISMATCH" in markdown
