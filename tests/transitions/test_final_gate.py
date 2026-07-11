from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256, canonical_sha256
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.kernel_decision_dependencies import KERNEL_ACCEPTED_COMMIT, KERNEL_INTAKE_RESULT_SCHEMA_ID, KERNEL_REPOSITORY
from ev4_transition.transitions.final_gate import EXPECTED_FINAL_GATE_DEPENDENCIES, GATE_ID, PG_REPO, RESPONSIVE_OUTPUT_SCHEMA, RESPONSIVE_REPO, FinalGateConfig, run_final_gate, verify_final_gate_lock

ROOT = Path(__file__).resolve().parents[2]
ZERO_HASH = "0" * 64


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _lineage() -> dict:
    return {"decision_family":"layout_structure","decision_card_ref":"projection:synthetic","selected_option":"flexbox","rejected_options":["grid"],"evidence_refs":["EV1"],"evidence_state":"validated","consumer_stage":"final_evidence_gate"}


def _hash_record(scope: str, value: str = ZERO_HASH) -> dict:
    return {"algorithm":"sha256","scope":scope,"value":value}


def _intake(kernel_lock: dict, status: str = "accepted") -> dict:
    lock_hash = canonical_sha256(kernel_lock)
    packet_status = "accepted" if status == "accepted" else "insufficient_evidence"
    accepted_count = 1 if packet_status == "accepted" else 0
    unresolved_count = 0 if packet_status == "accepted" else 1
    return {
        "schema_version":KERNEL_INTAKE_RESULT_SCHEMA_ID,
        "result_type":"kernel_decision_intake",
        "status":status,
        "kernel_pin":{"repository":KERNEL_REPOSITORY,"accepted_commit":KERNEL_ACCEPTED_COMMIT,"semantic_lock_sha256":lock_hash},
        "accepted_requires":{"kernel_pin_verified":True,"semantic_lock_verified":True,"intake_schema_valid":True,"packet_binding_valid":True,"l2_executed_all":True,"no_unsupported_claims":True,"result_schema_valid":True},
        "diagnostics":[],
        "upstream_diagnostics":[{"packet_id":"P1","diagnostics":[]}],
        "packet_results":[{
            "packet_id":"P1","decision_id":"D1","decision_family_id":"layout_structure","status":packet_status,"l2_executed":True,"human_override_observed":False,
            "project_gate_diagnostics":[],"upstream_diagnostics":[],"resolver_output":{"resolver_status":"auto_resolved"},
            "decision_record_ref":{"packet_id":"P1","decision_id":"D1","sha256":ZERO_HASH},
            "source_evidence_refs":["EV1"],"runtime_evidence_refs":[],
            "hashes":{"packet_hash":_hash_record("packet"),"decision_record_hash":_hash_record("decision_record"),"resolver_input_hash":_hash_record("resolver_input"),"audit_context_hash":_hash_record("audit_context")},
            "provenance":{"provenance_id":"PROV1"},"execution_record":{"exit_code":0}
        }],
        "derived_counts":{"provisional_count":0,"human_override_count":0,"unresolved_decision_count":unresolved_count,"accepted_decision_count":accepted_count,"rejected_decision_count":0},
        "decision_record_refs":[{"packet_id":"P1","decision_id":"D1","sha256":ZERO_HASH}],
        "source_evidence_refs":[{"packet_id":"P1","reference":"EV1"}],
        "runtime_evidence_refs":[],
        "hashes":{"source_input_hash":_hash_record("source_input"),"semantic_lock_hash":_hash_record("semantic_lock",lock_hash)},
        "provenance":{"source_bundle_id":"synthetic-kroad-011","source_bundle_provenance":{"source":"synthetic-fixture"},"result_producer":PG_REPO}
    }


def _input(*, include_intake: bool = True, include_lineage: bool = True, intake_status: str = "accepted") -> dict:
    output = {"schema":RESPONSIVE_OUTPUT_SCHEMA,"responsive_tree_output":{"mode":"blocked"},"real_evidence":True,"evidence_status":"real"}
    if include_lineage:
        output["decision_lineage"] = _lineage()
    value = {"responsive_output":output}
    if include_intake:
        value["_test_intake_status"] = intake_status
    return value


def _repos(tmp_path: Path):
    pg, responsive = tmp_path / "pg", tmp_path / "responsive"
    for dep in EXPECTED_FINAL_GATE_DEPENDENCIES.values():
        root = pg if dep.repository == PG_REPO else responsive
        if dep.path.endswith(".py"):
            text = "import sys\nprint('responsive ok')\nsys.exit(0)\n"
        elif dep.path.endswith(".json") and "responsive-output" in dep.path:
            text = json.dumps({"id":dep.contract_or_schema_id,"marker":dep.identity_marker,"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["schema"],"properties":{"schema":{"const":RESPONSIVE_OUTPUT_SCHEMA}},"additionalProperties":True})
        elif dep.path.endswith(".json"):
            text = json.dumps({"id":dep.contract_or_schema_id,"marker":dep.identity_marker})
        else:
            text = f"{dep.identity_marker}\n"
        _write(root / dep.path, text)
    source = LocalCheckoutContractSource({PG_REPO:pg, RESPONSIVE_REPO:responsive})
    lock = {"schema_version":"final-gate-lock.v1","gate_id":GATE_ID,"files":[]}
    for dep in EXPECTED_FINAL_GATE_DEPENDENCIES.values():
        root = pg if dep.repository == PG_REPO else responsive
        lock["files"].append({"role":dep.role,"repository":dep.repository,"accepted_commit":dep.accepted_commit,"path":dep.path,"contract_or_schema_id":dep.contract_or_schema_id,"sha256_file_bytes":bytes_sha256((root/dep.path).read_bytes())})
    kernel_lock = {"schema_version":"kernel-decision-intake-lock.v1","intake_schema_id":"ev4-project-gate-kernel-decision-intake@1.0.0","kernel_pin":{"repository":KERNEL_REPOSITORY,"accepted_commit":KERNEL_ACCEPTED_COMMIT},"files":[]}
    schema_dir = tmp_path / "schemas/final-gate-result"
    schema_dir.mkdir(parents=True)
    schema_dir.joinpath("final-gate-result.v1.schema.json").write_text(json.dumps({"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["schema_version","gate_id","status","kernel_decision_intake_result"],"additionalProperties":True}), encoding="utf-8")
    kroad_schema_dir = tmp_path / "schemas/kernel-decision-intake-result"
    kroad_schema_dir.mkdir(parents=True)
    kroad_schema_dir.joinpath("kernel-decision-intake-result.v1.schema.json").write_text((ROOT/"schemas/kernel-decision-intake-result/kernel-decision-intake-result.v1.schema.json").read_text(), encoding="utf-8")
    return pg, responsive, source, lock, kernel_lock


def _run(tmp_path: Path, value: dict) -> dict:
    pg, responsive, source, lock, kernel_lock = _repos(tmp_path)
    candidate = dict(value)
    intake_status = candidate.pop("_test_intake_status", None)
    if intake_status is not None:
        candidate["kernel_decision_intake_result"] = _intake(kernel_lock, intake_status)
    return run_final_gate(candidate, source, FinalGateConfig(tmp_path/"schemas", lock, pg, responsive, 30, True, kernel_lock))


def _codes(result: dict) -> list[str]:
    return [item["code"] for item in result["diagnostics"]]


def test_final_gate_requires_authoritative_kernel_intake(tmp_path: Path):
    result = _run(tmp_path, _input(include_intake=False))
    assert result["status"] == "invalid"
    assert result["accepted_requires"]["kernel_decision_intake_accepted"] is False
    item = next(x for x in result["diagnostics"] if x["code"] == "PG.FINAL.KERNEL_INTAKE_REQUIRED")
    assert item["path"] == "$.kernel_decision_intake_result"


def test_complete_lineage_alone_cannot_authenticate_acceptance(tmp_path: Path):
    result = _run(tmp_path, _input(include_intake=False, include_lineage=True))
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_REQUIRED" in _codes(result)


def test_final_gate_rejects_nonaccepted_intake(tmp_path: Path):
    result = _run(tmp_path, _input(intake_status="insufficient_evidence"))
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_NOT_ACCEPTED" in _codes(result)


def test_final_gate_accepts_verified_intake_and_preserves_projection(tmp_path: Path):
    result = _run(tmp_path, _input())
    assert result["status"] == "accepted", result
    assert result["accepted_requires"]["kernel_decision_intake_accepted"] is True
    assert result["output"]["decision_lineage"] == _lineage()
    assert result["kernel_decision_intake_result"]["status"] == "accepted"


def test_lineage_is_optional_projection_when_intake_is_authoritative(tmp_path: Path):
    result = _run(tmp_path, _input(include_lineage=False))
    assert result["status"] == "accepted", result
    assert result["accepted_requires"]["decision_lineage_projection_valid"] is True


def test_final_gate_rejects_lineage_projection_drift(tmp_path: Path):
    value = _input()
    value["decision_lineage"] = {**_lineage(), "selected_option":"grid"}
    result = _run(tmp_path, value)
    assert result["status"] == "invalid"
    assert "PG.FINAL.DECISION_LINEAGE_DRIFT" in _codes(result)


def test_final_gate_rejects_forbidden_claim(tmp_path: Path):
    value = _input()
    value["claim"] = "production_ready"
    result = _run(tmp_path, value)
    assert result["status"] == "invalid"
    assert "PG.FINAL.FORBIDDEN_CLAIM" in _codes(result)


def test_final_gate_rejects_tampered_intake_lock_hash(tmp_path: Path):
    pg, responsive, source, lock, kernel_lock = _repos(tmp_path)
    value = _input()
    value.pop("_test_intake_status")
    intake = _intake(kernel_lock)
    intake["kernel_pin"]["semantic_lock_sha256"] = "f" * 64
    value["kernel_decision_intake_result"] = intake
    result = run_final_gate(value, source, FinalGateConfig(tmp_path/"schemas", lock, pg, responsive, 30, True, kernel_lock))
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_LOCK_HASH_INVALID" in _codes(result)


def test_final_gate_rejects_schema_invalid_intake(tmp_path: Path):
    pg, responsive, source, lock, kernel_lock = _repos(tmp_path)
    value = _input()
    value.pop("_test_intake_status")
    intake = _intake(kernel_lock)
    intake.pop("hashes")
    value["kernel_decision_intake_result"] = intake
    result = run_final_gate(value, source, FinalGateConfig(tmp_path/"schemas", lock, pg, responsive, 30, True, kernel_lock))
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_SCHEMA_INVALID" in _codes(result)


def test_final_gate_does_not_count_synthetic_as_real_evidence(tmp_path: Path):
    value = _input()
    value["responsive_output"]["synthetic_only"] = True
    value["responsive_output"]["evidence_status"] = "synthetic_fixture"
    result = _run(tmp_path, value)
    assert result["status"] == "insufficient_evidence"
    assert "PG.FINAL.SYNTHETIC_ONLY_EVIDENCE" in _codes(result)


def test_final_gate_lock_detects_hash_mismatch(tmp_path: Path):
    pg, responsive, source, lock, _ = _repos(tmp_path)
    lock["files"][0]["sha256_file_bytes"] = "0"*64
    assert any(item.code == "PG.FINAL.EXTERNAL_HASH_MISMATCH" for item in verify_final_gate_lock(lock, source))


def test_final_gate_completed_result_is_schema_valid(tmp_path: Path):
    result = _run(tmp_path, _input())
    schema = json.loads((tmp_path/"schemas/final-gate-result/final-gate-result.v1.schema.json").read_text())
    Draft202012Validator(schema).validate(result)
