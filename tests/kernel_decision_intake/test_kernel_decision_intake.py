from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.kernel_decision_dependencies import EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES, KERNEL_ACCEPTED_COMMIT, KERNEL_INTAKE_SCHEMA_ID, KERNEL_LOCK_SCHEMA_VERSION, KERNEL_REPOSITORY
from ev4_transition.kernel_decision_intake import KernelAuditExecution, KernelDecisionIntakeConfig, run_kernel_decision_intake

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "fixtures/kernel-decision-intake/complete-layout-structure.synthetic.json"
MANIFEST = ROOT / "fixtures/kernel-decision-intake/cases.synthetic.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _kernel(tmp_path: Path):
    root = tmp_path / "kernel"
    texts = {
        "decision_record_schema": json.dumps({"$id":"https://ev4.local/schemas/decision-record.v2.schema.json"}),
        "p0_decision_matrices": json.dumps({"matrix_registry_id":"p0-decision-matrices.v0","matrices":[{"decision_family_id":"layout_structure"},{"decision_family_id":"media_choice"}]}),
        "resolver_rule_registry": json.dumps({"registry_id":"resolver-rule-registry.v0","active_rules":[{"decision_family_id":"layout_structure"}]}),
        "layout_structure_rule": json.dumps({"contract_id":"resolver.contract.layout_structure.mvp.v0","rule_id":"resolver.rule.layout_structure.mvp.v0","rule_version":"0.1.0"}),
        "resolver_implementation": "export function resolveDecision() {}\n",
        "l2_decision_correctness_audit": "export function auditDecisionRecord() {}\n",
    }
    files = []
    for role, dep in EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES.items():
        _write(root / dep.path, texts[role])
        files.append({"role":role,"repository":dep.repository,"accepted_commit":dep.accepted_commit,"path":dep.path,"contract_or_schema_id":dep.contract_or_schema_id,"sha256_file_bytes":bytes_sha256((root/dep.path).read_bytes())})
    lock = {"schema_version":KERNEL_LOCK_SCHEMA_VERSION,"intake_schema_id":KERNEL_INTAKE_SCHEMA_ID,"kernel_pin":{"repository":KERNEL_REPOSITORY,"accepted_commit":KERNEL_ACCEPTED_COMMIT},"files":sorted(files,key=lambda item:item["role"])}
    return root, lock


def _pass(packet: dict) -> KernelAuditExecution:
    return KernelAuditExecution("completed", {"audit_status":"pass","human_override_observed":False,"resolver_output":{"resolver_status":"auto_resolved","rule_id":"resolver.rule.layout_structure.mvp.v0","rule_version":"0.1.0"},"diagnostics":[]}, {"exit_code":0})


def _apply(bundle: dict, mutation: str):
    packet = bundle["payload"]["data"]["decision_packets"][0]
    executor = _pass
    lock_mutator = None
    if mutation == "none":
        pass
    elif mutation == "human_override":
        executor = lambda _: KernelAuditExecution("completed", {"audit_status":"pass","human_override_observed":True,"resolver_output":{"resolver_status":"human_overridden"},"diagnostics":[{"code":"L2_HUMAN_OVERRIDE_OBSERVED","severity":"warning","source":"semantic","path":"decision_record.decision_type","message":"synthetic"}]})
    elif mutation == "requires_reaudit":
        packet["decision_record"]["requires_reaudit"] = True
        executor = lambda _: KernelAuditExecution("completed", {"audit_status":"pass","human_override_observed":False,"resolver_output":{"resolver_status":"conditional"},"diagnostics":[{"code":"L2_DECISION_REQUIRES_REAUDIT","severity":"warning","source":"semantic","path":"decision_record.requires_reaudit","message":"synthetic"}]})
    elif mutation == "known_unsupported_family":
        for value in (packet, packet["decision_record"], packet["resolver_input"], packet["audit_context"]):
            value["decision_family_id"] = "media_choice"
        packet["decision_record"]["rule_id"] = "resolver.rule.media_choice.future"
        packet["decision_record"]["rule_version"] = "0.0.0"
        executor = lambda _: KernelAuditExecution("completed", {"audit_status":"unsupported","human_override_observed":False,"resolver_output":None,"diagnostics":[{"code":"L2_DECISION_FAMILY_NOT_RESOLVER_COVERED","severity":"warning","source":"semantic","path":"decision_record.decision_family_id","message":"synthetic"}]})
    elif mutation.startswith("missing_") and mutation in {"missing_decision_record","missing_resolver_input","missing_audit_context"}:
        packet.pop(mutation.removeprefix("missing_"))
    elif mutation == "missing_conditional_justification":
        packet["decision_record"]["resolver_status"] = "conditional"
        executor = lambda _: KernelAuditExecution("completed", {"audit_status":"fail","human_override_observed":False,"resolver_output":{"resolver_status":"conditional"},"diagnostics":[{"code":"L2_CONDITIONAL_JUSTIFICATION_REQUIRED","severity":"error","source":"semantic","path":"audit_context.conditional_justification.summary","message":"synthetic"}]})
    elif mutation == "decision_family_mismatch":
        packet["resolver_input"]["decision_family_id"] = "media_choice"
    elif mutation == "decision_id_mismatch":
        packet["resolver_input"]["decision_id"] = "D2"
    elif mutation == "evidence_ref_mismatch":
        packet["resolver_input"]["evidence_refs"][0]["evidence_id"] = "EV2"
    elif mutation in {"duplicate_packet_id","duplicate_decision_id","cross_packet_substitution"}:
        second = copy.deepcopy(packet)
        second["packet_id"] = "P2"
        second["decision_id"] = "D2"
        for value in (second["decision_record"],second["resolver_input"],second["audit_context"]):
            value["decision_id"] = "D2"
        if mutation == "duplicate_packet_id":
            second["packet_id"] = packet["packet_id"]
        if mutation == "duplicate_decision_id":
            second["decision_id"] = packet["decision_id"]
            for value in (second["decision_record"],second["resolver_input"],second["audit_context"]):
                value["decision_id"] = packet["decision_id"]
        if mutation == "cross_packet_substitution":
            second["decision_record"]["evidence_refs"][0]["evidence_id"] = "EV2"
            second["resolver_input"]["evidence_refs"][0]["evidence_id"] = "EV2"
            second["resolver_input"]["context"]["required_evidence_refs"] = ["EV2"]
            second["audit_context"]["source_evidence_refs"] = ["EV2"]
        bundle["payload"]["data"]["decision_packets"].append(second)
        if mutation == "cross_packet_substitution":
            packet["resolver_input"]["context"]["required_evidence_refs"].append("EV2")
    elif mutation == "authored_fake_l2_pass":
        packet["l2_audit_status"] = "pass"
    elif mutation == "authored_derived_counts":
        bundle["payload"]["data"]["accepted_decision_count"] = 1
    elif mutation == "kernel_lock_mismatch":
        lock_mutator = lambda lock: lock["files"][0].__setitem__("accepted_commit", "2"*40)
    elif mutation == "kernel_artifact_hash_mismatch":
        lock_mutator = lambda lock: lock["files"][0].__setitem__("sha256_file_bytes", "0"*64)
    elif mutation == "short_kernel_ref":
        bundle["payload"]["data"]["kernel_pin"]["accepted_commit"] = "76a82e2"
    elif mutation == "unknown_intake_schema":
        bundle["payload"]["schema_id"] = "unknown-intake@9"
    elif mutation == "unknown_rule_version":
        packet["decision_record"]["rule_version"] = "9.9.9"
    elif mutation == "malformed_kernel_output":
        executor = lambda _: KernelAuditExecution("malformed", None)
    elif mutation == "kernel_execution_unavailable":
        executor = lambda _: KernelAuditExecution("unavailable", None)
    elif mutation == "unsupported_asserted_claim":
        packet["asserted_claims"][0]["claim"] = "production_ready"
    elif mutation == "forbidden_claim_outside_asserted_claims":
        packet["production_ready"] = True
    else:
        raise AssertionError(mutation)
    return executor, lock_mutator


def _all_diagnostics(result: dict) -> list[dict]:
    return [*result["diagnostics"], *[item for packet in result["packet_results"] for item in packet["project_gate_diagnostics"]]]


CASES = [case for case in json.loads(MANIFEST.read_text())["cases"] if case["mutation"] not in {"receipt_without_intake","final_gate_without_intake"}]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_synthetic_fixture_case(case: dict, tmp_path: Path):
    bundle = json.loads(BASE.read_text())
    executor, lock_mutator = _apply(bundle, case["mutation"])
    kernel, lock = _kernel(tmp_path)
    if lock_mutator:
        lock_mutator(lock)
    executions = 0

    def counted_executor(packet: dict) -> KernelAuditExecution:
        nonlocal executions
        executions += 1
        return executor(packet)

    result = run_kernel_decision_intake(bundle, LocalCheckoutContractSource({KERNEL_REPOSITORY:kernel}), KernelDecisionIntakeConfig(ROOT/"schemas", lock), audit_executor=counted_executor)
    assert result["status"] == case["expected_status"], result
    if case["expected_pg_code"]:
        matching = [item for item in _all_diagnostics(result) if item["code"] == case["expected_pg_code"]]
        assert any(item["path"] == case["expected_path"] for item in matching), matching
    upstream_codes = sorted({item["code"] for packet in result["packet_results"] for item in packet["upstream_diagnostics"]})
    assert upstream_codes == sorted(case["expected_upstream_codes"])
    if case["mutation"] in {"authored_fake_l2_pass", "authored_derived_counts", "unsupported_asserted_claim", "forbidden_claim_outside_asserted_claims", "cross_packet_substitution"}:
        assert executions == 0
    Draft202012Validator(json.loads((ROOT/"schemas/kernel-decision-intake-result/kernel-decision-intake-result.v1.schema.json").read_text())).validate(result)


def test_manifest_labels_every_case_synthetic():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["synthetic"] is True
    assert "not real handoff" in manifest["evidence_limit"]
