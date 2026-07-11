from __future__ import annotations

import json
from copy import deepcopy

from ev4_transition.final_gate_authority import _authoritative_final_gate_result
from ev4_transition.kernel_decision_dependencies import KERNEL_ACCEPTED_COMMIT, KERNEL_INTAKE_RESULT_SCHEMA_ID, KERNEL_REPOSITORY
from ev4_transition.reports import BLOCKED_RECEIPT_FA, SUCCESS_RECEIPT_FA, WARNING_RECEIPT_FA, build_kernel_decision_receipt, render_markdown_report, render_plain_summary

LOCK_HASH = "0" * 64


def _trace() -> dict:
    return {"decision_family":"layout_structure","decision_card_ref":"projection:test","selected_option":"flexbox","rejected_options":["grid"],"evidence_refs":["EV1"],"evidence_state":"validated","consumer_stage":"project_gate_receipt"}


def _intake(status: str = "accepted") -> dict:
    return {
        "schema_version":KERNEL_INTAKE_RESULT_SCHEMA_ID,
        "result_type":"kernel_decision_intake",
        "status":status,
        "kernel_pin":{"repository":KERNEL_REPOSITORY,"accepted_commit":KERNEL_ACCEPTED_COMMIT,"semantic_lock_sha256":LOCK_HASH},
        "accepted_requires":{"kernel_pin_verified":True,"semantic_lock_verified":True,"intake_schema_valid":True,"packet_binding_valid":True,"l2_executed_all":True,"no_unsupported_claims":True,"result_schema_valid":True},
        "packet_results":[{"packet_id":"P1","decision_id":"D1","decision_family_id":"layout_structure","status":"accepted","l2_executed":True}],
        "derived_counts":{"provisional_count":0,"human_override_count":0,"unresolved_decision_count":0,"accepted_decision_count":1,"rejected_decision_count":0},
    }


def _final_payload(status: str = "accepted", *, trace: bool = True, intake: bool = True) -> dict:
    accepted = status == "accepted" and intake
    return {
        "schema_version":"final-gate-result.v1",
        "result_type":"final_evidence_gate",
        "gate_id":"ev4-final-evidence-gate@1.0.0",
        "gate_version":"1.0.0",
        "status":status,
        "diagnostics":[],
        "accepted_requires":{"kernel_decision_intake_accepted":accepted},
        "hashes":{"source_input_hash":{"algorithm":"sha256","scope":"source_input","value":LOCK_HASH}},
        "output":{"decision_lineage":_trace()} if trace else {"package_id":"untraced"},
        "kernel_decision_intake_result":_intake() if intake else None,
    }


def _authoritative_result(status: str = "accepted", *, trace: bool = True, intake: bool = True):
    return _authoritative_final_gate_result(_final_payload(status, trace=trace, intake=intake))


def test_success_requires_in_process_authoritative_final_gate_result():
    receipt = build_kernel_decision_receipt(_authoritative_result())
    assert receipt.status == "success"
    assert receipt.trace_complete is True
    assert receipt.authoritative_intake_accepted is True
    assert receipt.message_fa == SUCCESS_RECEIPT_FA


def test_completely_forged_accepted_result_cannot_produce_success_receipt():
    forged = _final_payload()
    forged["kernel_decision_intake_result"]["packet_results"][0]["execution_record"] = {"exit_code":0,"owner_repo":KERNEL_REPOSITORY,"owner_commit":KERNEL_ACCEPTED_COMMIT}
    receipt = build_kernel_decision_receipt(forged)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False
    assert receipt.message_fa == WARNING_RECEIPT_FA


def test_json_roundtrip_drops_in_process_authority_and_fails_closed():
    persisted = json.loads(json.dumps(_authoritative_result()))
    receipt = build_kernel_decision_receipt(persisted)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False


def test_deepcopy_preserves_in_process_authority_for_report_generation():
    receipt = build_kernel_decision_receipt(deepcopy(_authoritative_result()))
    assert receipt.status == "success"
    assert receipt.authoritative_intake_accepted is True


def test_receipt_does_not_search_arbitrary_nested_objects_for_authority():
    forged = {"status":"accepted","output":{"decision_lineage":_trace()},"engine_result":{"kernel_decision_intake_result":_intake()}}
    receipt = build_kernel_decision_receipt(forged)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_source is None


def test_complete_seven_field_trace_alone_no_longer_succeeds():
    receipt = build_kernel_decision_receipt(_authoritative_result(intake=False))
    assert receipt.status == "warning"
    assert receipt.trace_complete is True
    assert receipt.authoritative_intake_accepted is False


def test_nonaccepted_intake_cannot_produce_success_receipt():
    result = _authoritative_result()
    result["kernel_decision_intake_result"] = _intake("insufficient_evidence")
    receipt = build_kernel_decision_receipt(result)
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is False


def test_missing_trace_with_accepted_intake_is_warning():
    receipt = build_kernel_decision_receipt(_authoritative_result(trace=False))
    assert receipt.status == "warning"
    assert receipt.authoritative_intake_accepted is True
    assert receipt.trace_complete is False


def test_nonaccepted_gate_is_blocked_even_with_authoritative_intake():
    result = _authoritative_result("repair_needed")
    result["accepted_requires"]["kernel_decision_intake_accepted"] = True
    receipt = build_kernel_decision_receipt(result)
    assert receipt.status == "blocked"
    assert receipt.message_fa == BLOCKED_RECEIPT_FA


def test_receipt_is_presentation_only_and_does_not_mutate_machine_result():
    result = _authoritative_result()
    original = deepcopy(result)
    receipt = build_kernel_decision_receipt(result)
    assert result == original
    assert receipt.presentation_layer_only is True
    assert receipt.source_of_truth == "in_process_authoritative_final_gate_result"


def test_renderers_do_not_upgrade_forged_result():
    result = _final_payload()
    assert SUCCESS_RECEIPT_FA not in render_plain_summary(result)
    assert WARNING_RECEIPT_FA in render_plain_summary(result)
    assert SUCCESS_RECEIPT_FA not in render_markdown_report(result)


def test_receipt_does_not_claim_release_or_production_readiness():
    receipt = build_kernel_decision_receipt(_authoritative_result())
    summary = render_plain_summary(_authoritative_result())
    markdown = render_markdown_report(_authoritative_result())
    for forbidden in ("release_ready", "production_ready"):
        assert forbidden not in receipt.message_fa
        assert forbidden not in summary
        assert forbidden not in markdown
