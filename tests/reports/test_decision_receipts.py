from __future__ import annotations

from copy import deepcopy

from ev4_transition.kernel_decision_dependencies import KERNEL_ACCEPTED_COMMIT, KERNEL_INTAKE_RESULT_SCHEMA_ID, KERNEL_REPOSITORY
from ev4_transition.reports import BLOCKED_RECEIPT_FA, SUCCESS_RECEIPT_FA, WARNING_RECEIPT_FA, build_kernel_decision_receipt, render_markdown_report, render_plain_summary

LOCK_HASH = "0" * 64


def _trace() -> dict:
    return {"decision_family":"layout_structure","decision_card_ref":"projection:synthetic","selected_option":"flexbox","rejected_options":["grid"],"evidence_refs":["EV1"],"evidence_state":"validated","consumer_stage":"project_gate_receipt"}


def _intake(status: str = "accepted") -> dict:
    return {
        "schema_version":KERNEL_INTAKE_RESULT_SCHEMA_ID,
        "result_type":"kernel_decision_intake",
        "status":status,
        "kernel_pin":{"repository":KERNEL_REPOSITORY,"accepted_commit":KERNEL_ACCEPTED_COMMIT,"semantic_lock_sha256":LOCK_HASH},
        "accepted_requires":{"kernel_pin_verified":True,"semantic_lock_verified":True,"intake_schema_valid":True,"packet_binding_valid":True,"l2_executed_all":True,"no_unsupported_claims":True,"result_schema_valid":True},
        "packet_results":[{"packet_id":"P1","decision_id":"D1","decision_family_id":"layout_structure","status":"accepted","l2_executed":True}],
        "derived_counts":{"provisional_count":0,"human_override_count":0,"unresolved_decision_count":0,"accepted_decision_count":1,"rejected_decision_count":0},
        "hashes":{"semantic_lock_hash":{"algorithm":"sha256","scope":"semantic_lock","value":LOCK_HASH}},
        "provenance":{"result_producer":"rezahh107/EV4-Project-Gate"}
    }


def _result(status: str = "accepted", *, trace: bool = True, intake: bool = True) -> dict:
    result = {"schema_version":"project-gate-test-result.v1","status":status,"diagnostics":[],"output":{"decision_lineage":_trace()} if trace else {"package_id":"untraced"}}
    if intake:
        result["kernel_decision_intake_result"] = _intake()
    return result


def test_success_requires_trace_and_authoritative_accepted_intake():
    receipt = build_kernel_decision_receipt(_result())
    assert receipt.status == "success"
    assert receipt.trace_complete is True
    assert receipt.authoritative_intake_accepted is True
    assert receipt.message_fa == SUCCESS_RECEIPT_FA


def test_complete_seven_field_trace_alone_no_longer_succeeds():
    receipt = build_kernel_decision_receipt(_result(intake=False))
    assert receipt.status == "warning"
    assert receipt.trace_complete is True
    assert receipt.authoritative_intake_accepted is False
    assert receipt.message_fa == WARNING_RECEIPT_FA


def test_nonaccepted_intake_cannot_produce_success_receipt():
    result = _result()
    result["kernel_decision_intake_result"] = _intake("insufficient_evidence")
    receipt = build_kernel_decision_receipt(result)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False


def test_tampered_semantic_lock_hash_cannot_produce_success_receipt():
    result = _result()
    result["kernel_decision_intake_result"]["hashes"]["semantic_lock_hash"]["value"] = "f" * 64
    receipt = build_kernel_decision_receipt(result)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False


def test_wrong_result_producer_cannot_produce_success_receipt():
    result = _result()
    result["kernel_decision_intake_result"]["provenance"]["result_producer"] = "rezahh107/other"
    receipt = build_kernel_decision_receipt(result)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False


def test_missing_trace_with_accepted_intake_is_warning():
    receipt = build_kernel_decision_receipt(_result(trace=False))
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is True
    assert receipt.trace_complete is False


def test_nonaccepted_gate_is_blocked_even_with_authoritative_intake():
    receipt = build_kernel_decision_receipt(_result("repair_needed"))
    assert receipt.status == "blocked"
    assert receipt.message_fa == BLOCKED_RECEIPT_FA


def test_receipt_is_presentation_only_and_does_not_mutate_machine_result():
    result = _result()
    original = deepcopy(result)
    receipt = build_kernel_decision_receipt(result)
    assert result == original
    assert receipt.presentation_layer_only is True
    assert receipt.source_of_truth == "accepted_kernel_decision_intake_result"


def test_renderers_do_not_upgrade_lineage_only_result():
    result = _result(intake=False)
    assert SUCCESS_RECEIPT_FA not in render_plain_summary(result)
    assert WARNING_RECEIPT_FA in render_plain_summary(result)
    assert SUCCESS_RECEIPT_FA not in render_markdown_report(result)


def test_receipt_does_not_claim_release_or_production_readiness():
    receipt = build_kernel_decision_receipt(_result())
    summary = render_plain_summary(_result())
    markdown = render_markdown_report(_result())
    for forbidden in ("release_ready", "production_ready"):
        assert forbidden not in receipt.message_fa
        assert forbidden not in summary
        assert forbidden not in markdown
