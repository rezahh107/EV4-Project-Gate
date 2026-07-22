from __future__ import annotations

from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import load_json_file

REQUIRED_EVIDENCE_STATE = {
    "producer_prs_merged": "verified",
    "expected_shas_match": "verified",
    "exact_head_ci": "verified",
    "git_show_blob_sha256": "verified",
    "ce_standard_handoff": "verified_post_merge_normalized_handoff",
    "ce_stage_bundle_schema": "verified_by_prompt_0_reference",
}
CODE = "PG-P05-JOIN-EVIDENCE-NOT-READY"


def validate_join_evidence_packet(path: str | Path) -> dict[str, Any]:
    """Fail closed when an explicit legacy compatibility packet is not ready.

    Normal producer execution never calls this function. A caller must opt in by
    supplying an explicit path; the result has no authority outside that legacy
    compatibility check.
    """

    selected = Path(path)
    try:
        packet = load_json_file(selected)
    except Exception as exc:
        return _blocked(
            selected,
            [
                {
                    "field": "$",
                    "expected": "readable JSON",
                    "actual": type(exc).__name__,
                }
            ],
        )

    failures: list[dict[str, Any]] = []
    if packet.get("prompt_5_ready") is not True:
        failures.append(
            {
                "field": "$.prompt_5_ready",
                "expected": True,
                "actual": packet.get("prompt_5_ready"),
            }
        )
    if packet.get("blocking_insufficient_evidence") != []:
        failures.append(
            {
                "field": "$.blocking_insufficient_evidence",
                "expected": [],
                "actual": packet.get("blocking_insufficient_evidence"),
            }
        )
    if packet.get("ready_decision") != "ready":
        failures.append(
            {
                "field": "$.ready_decision",
                "expected": "ready",
                "actual": packet.get("ready_decision"),
            }
        )

    state = packet.get("evidence_state") if isinstance(packet.get("evidence_state"), dict) else {}
    for key, expected in REQUIRED_EVIDENCE_STATE.items():
        if state.get(key) != expected:
            failures.append(
                {
                    "field": f"$.evidence_state.{key}",
                    "expected": expected,
                    "actual": state.get(key),
                }
            )

    substitution = (
        packet.get("prompt_5_substitution")
        if isinstance(packet.get("prompt_5_substitution"), dict)
        else {}
    )
    for marker in (
        "FROM_PROMPT_1_FINAL_REPORT",
        "FROM_PROMPT_2_FINAL_REPORT",
        "FROM_PROMPT_3_FINAL_REPORT",
        "FROM_PROMPT_4_FINAL_REPORT",
    ):
        value = substitution.get(marker)
        status = value.get("replacement_status") if isinstance(value, dict) else value
        if status != "verified":
            failures.append(
                {
                    "field": f"$.prompt_5_substitution.{marker}",
                    "expected": "verified",
                    "actual": value,
                }
            )

    if failures:
        return _blocked(selected, failures)
    return {
        "status": "passed",
        "path": str(selected),
        "prompt_5_execution_allowed": True,
        "authorization_effect": "legacy_explicit_caller_only",
        "diagnostics": [],
    }


def _blocked(path: str | Path, failures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked",
        "path": str(path),
        "prompt_5_execution_allowed": False,
        "authorization_effect": "legacy_explicit_caller_only",
        "diagnostics": [
            {
                "code": CODE,
                "severity": "error",
                "path": item["field"],
                "message": "An explicitly supplied legacy join packet is not ready.",
                "details": item,
                "repair_owner": "Project Gate",
            }
            for item in failures
        ],
    }
