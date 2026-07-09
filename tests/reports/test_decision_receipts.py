from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ev4_transition.reports import (
    BLOCKED_RECEIPT_FA,
    SUCCESS_RECEIPT_FA,
    WARNING_RECEIPT_FA,
    build_kernel_decision_receipt,
    render_markdown_report,
    render_plain_summary,
)
from ev4_transition.service import build_report_bundle

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _trace() -> dict:
    return {
        "decision_family": "project_gate_wave_5_fixture",
        "decision_card_ref": "kernel-card:project-gate-wave-5-fixture",
        "selected_option": "preserve_machine_trace",
        "rejected_options": ["receipt_text_as_source_of_truth"],
        "evidence_refs": ["tests/reports/test_decision_receipts.py::_trace"],
        "evidence_state": "validated",
        "consumer_stage": "project_gate_receipt",
    }


def _accepted_result() -> dict:
    return {"schema_version": "project-gate-test-result.v1", "status": "accepted", "diagnostics": [], "output": {"decision_lineage": _trace()}}


def _fixture(path: str) -> dict:
    return json.loads((_REPO_ROOT / path).read_text(encoding="utf-8"))


def test_complete_machine_trace_allows_success_receipt():
    receipt = build_kernel_decision_receipt(_accepted_result())

    assert receipt.status == "success"
    assert receipt.trace_complete is True
    assert receipt.message_fa == SUCCESS_RECEIPT_FA
    assert receipt.machine_trace_source == "$.output.decision_lineage"


def test_positive_fixture_complete_trace_allows_success_receipt():
    receipt = build_kernel_decision_receipt(_fixture("fixtures/valid/project-gate-kernel-decision-receipt-complete-trace.v1.json"))

    assert receipt.status == "success"
    assert receipt.missing_trace_fields == []


def test_missing_decision_card_ref_blocks_success_receipt():
    result = _accepted_result()
    result["output"]["decision_lineage"].pop("decision_card_ref")

    receipt = build_kernel_decision_receipt(result)

    assert receipt.status == "warning"
    assert receipt.message_fa == WARNING_RECEIPT_FA
    assert "decision_card_ref" in receipt.missing_trace_fields


def test_missing_evidence_refs_blocks_success_receipt():
    result = _accepted_result()
    result["output"]["decision_lineage"].pop("evidence_refs")

    receipt = build_kernel_decision_receipt(result)

    assert receipt.status == "warning"
    assert receipt.message_fa == WARNING_RECEIPT_FA
    assert "evidence_refs" in receipt.missing_trace_fields


def test_warning_or_blocked_receipt_is_used_when_trace_is_incomplete():
    result = _fixture("fixtures/insufficient-evidence/project-gate-kernel-decision-receipt-missing-trace.v1.json")

    receipt = build_kernel_decision_receipt(result)

    assert receipt.status in {"warning", "blocked"}
    assert receipt.status != "success"
    assert receipt.message_fa in {WARNING_RECEIPT_FA, BLOCKED_RECEIPT_FA}


def test_project_gate_receipt_does_not_replace_machine_trace():
    result = {"schema_version": "project-gate-test-result.v1", "status": "accepted", "diagnostics": [], "output": {"ok": True}}
    original = deepcopy(result)

    receipt = build_kernel_decision_receipt(result)
    summary = render_plain_summary(result)

    assert result == original
    assert receipt.trace_complete is False
    assert receipt.status == "warning"
    assert SUCCESS_RECEIPT_FA not in summary
    assert WARNING_RECEIPT_FA in summary


def test_project_gate_cannot_emit_gate_pass_receipt_for_untraced_package():
    result = _fixture("fixtures/invalid/project-gate-kernel-decision-receipt-gate-pass-without-trace.v1.json")

    bundle = build_report_bundle(result)

    assert bundle.decision_receipt["status"] == "warning"
    assert bundle.decision_receipt["trace_complete"] is False
    assert bundle.decision_receipt["message_fa"] == WARNING_RECEIPT_FA
    assert SUCCESS_RECEIPT_FA not in bundle.persian_plain_summary


def test_project_gate_receipt_does_not_claim_release_ready():
    receipt = build_kernel_decision_receipt(_accepted_result())
    summary = render_plain_summary(_accepted_result())
    markdown = render_markdown_report(_accepted_result())

    assert "release_ready" not in receipt.message_fa
    assert "release_ready" not in summary
    assert "release_ready" not in markdown


def test_project_gate_receipt_does_not_claim_production_ready():
    receipt = build_kernel_decision_receipt(_accepted_result())
    summary = render_plain_summary(_accepted_result())
    markdown = render_markdown_report(_accepted_result())

    assert "production_ready" not in receipt.message_fa
    assert "production_ready" not in summary
    assert "production_ready" not in markdown
