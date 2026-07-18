from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ev4_transition.architect_to_ce import ARCHITECT_REPO, CE_REPO, TransitionValidatorHooks, transition_from_local_paths
from ev4_transition.canonical_json import bytes_sha256, canonical_dumps, load_json_file
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.diagnostics import diagnostic
from ev4_transition.external_lock import ARCHITECT_COMMIT, verify_external_contract_lock
from ev4_transition.validator_runner import run_architect_validator, run_ce_validator

ROOT = Path(__file__).resolve().parents[1]
ARCH = Path(os.environ.get("EV4_ARCHITECT_REPO", ROOT / "../EV4-Architect-Repo")).resolve()
CE = Path(os.environ.get("EV4_CE_REPO", ROOT / "../EV4-Constructability-Engineer-Repo")).resolve()
LOCK = ROOT / "contracts/locks/architect-to-ce-transition.v1.lock.json"


def external_available() -> bool:
    return (ARCH / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").exists() and (CE / "schemas/ce_architect_stage_intake.v1_1.schema.json").exists()


pytestmark = pytest.mark.skipif(not external_available(), reason="pinned specialist checkouts are not available")


def architect_payload(name: str = "minimal-complete.v1.json") -> dict:
    subdir = "insufficient-evidence" if "missing" in name else "valid"
    return json.loads((ARCH / "fixtures/architect-stage-payload" / subdir / name).read_text(encoding="utf-8"))


def source_bundle(payload: dict, *, bundle_id: str = "synthetic-architect-a2c-001", include_commit: bool = True, stage: str = "architect", schema_id: str = "ev4-architect-stage-payload@1.0.0") -> dict:
    evidence_status = "insufficient_evidence" if payload["payload_status"] == "insufficient_evidence" else "complete"
    produced_by = {"repository": "rezahh107/EV4-Architect-Repo", "ref": "synthetic-fixture"}
    if include_commit:
        produced_by["commit_sha"] = ARCHITECT_COMMIT
    bundle = {
        "schema_version": "stage-evidence-bundle.v1",
        "bundle_id": bundle_id,
        "stage": stage,
        "payload_schema": {"id": schema_id, "version": "1.0.0", "owner_repository": "rezahh107/EV4-Architect-Repo"},
        "produced_by": produced_by,
        "evidence_status": evidence_status,
        "payload": {"schema_id": schema_id, "data": payload},
        "evidence": [{"id": "architect-payload", "kind": "fixture", "state": "validated", "description": "Synthetic Architect payload fixture.", "artifact_hash": {"algorithm": "sha256", "value": bytes_sha256(canonical_dumps(payload).encode("utf-8")), "scope": "canonical_json"}, "source": {"type": "synthetic_fixture", "reference": "Architect fixture"}}],
        "provenance": {"source": "synthetic-fixture", "created_by": "project-gate-tests"},
        "synthetic": True,
    }
    if evidence_status == "insufficient_evidence":
        bundle["missing_evidence"] = [{"id": item["unresolved_id"], "owner": item["owner"], "reason": item["reason"]} for item in payload.get("unresolved_evidence", [])]
    return bundle


def official_hooks(events: list[str] | None = None) -> TransitionValidatorHooks:
    return TransitionValidatorHooks(
        architect=lambda payload: run_architect_validator(ARCH, payload),
        ce=lambda payload, bundle: run_ce_validator(CE, payload, bundle),
        events=events,
    )


def run_transition(bundle: dict, hooks: TransitionValidatorHooks | None = None) -> dict:
    return transition_from_local_paths(bundle, ROOT / "schemas", LOCK, ARCH, CE, validator_hooks=hooks)


def lock_source() -> LocalCheckoutContractSource:
    return LocalCheckoutContractSource({ARCHITECT_REPO: ARCH, CE_REPO: CE})


def test_valid_transition_outputs_complete_ce_v1_1_bundle():
    result = run_transition(source_bundle(architect_payload()), official_hooks())
    assert result["status"] == "valid"
    assert result["output"]["stage"] == "ce"
    target = result["output"]["payload"]["data"]
    assert target["schema_id"] == "ev4-ce-architect-stage-intake@1.1.0"
    assert target["schema_version"] == "1.1.0"
    assert target["mapping_contract"]["mapping_id"] == "ev4-architect-stage-to-ce-intake-mapping@1.1.0"
    assert target["project_gate_transition"]["executed"] is True
    assert target["project_gate_transition"]["transition_id"] == "ev4-architect-to-ce-transition@1.0.0"
    assert target["project_gate_transition"]["source_bundle_id"] == "synthetic-architect-a2c-001"
    assert target["project_gate_transition"]["source_bundle_hash"]["value"] == result["hashes"]["source_bundle"]["value"]
    assert target["validation_contract"]["rules"] == [f"CE-I{i:02d}" for i in range(1, 22)]
    assert "project_gate_transition_implemented" not in target["ce_processing_prerequisites"]
    assert "ce_review_units" not in canonical_dumps(target)


def test_complete_mapping_trace_and_derivation_rules():
    result = run_transition(source_bundle(architect_payload()), official_hooks())
    trace = result["output"]["payload"]["data"]["mapping_trace"]
    targets = {row["target_path"]: row for row in trace}
    required = {
        "$.project_gate_transition.executed": "CE-MAP-A2C-01",
        "$.project_gate_transition.transition_id": "CE-MAP-A2C-01",
        "$.project_gate_transition.transition_version": "CE-MAP-A2C-01",
        "$.project_gate_transition.producer_repository": "CE-MAP-A2C-01",
        "$.project_gate_transition.source_bundle_hash": "CE-MAP-A2C-02",
    }
    assert len(trace) == 21
    for target, rule in required.items():
        assert targets[target]["classification"] == "deterministic_derived_metadata"
        assert targets[target]["derivation_rule"] == {"id": rule, "version": "1.0.0"}
    assert targets["$.project_gate_transition.source_bundle_id"]["classification"] == "direct_evidence_copy"
    assert "derivation_rule" not in targets["$.project_gate_transition.source_bundle_id"]
    for row in trace:
        if row["classification"] != "deterministic_derived_metadata":
            assert "derivation_rule" not in row


def test_canonical_source_hash_changes_with_source_bundle_identity():
    first = run_transition(source_bundle(architect_payload(), bundle_id="synthetic-architect-a2c-001"), official_hooks())
    second = run_transition(source_bundle(architect_payload(), bundle_id="synthetic-architect-a2c-002"), official_hooks())
    assert first["status"] == "valid"
    assert second["status"] == "valid"
    assert first["output"]["payload"]["data"]["project_gate_transition"]["source_bundle_hash"]["value"] != second["output"]["payload"]["data"]["project_gate_transition"]["source_bundle_hash"]["value"]


def test_validation_order_and_final_result_validation_last():
    events: list[str] = []
    result = run_transition(source_bundle(architect_payload()), official_hooks(events))
    assert result["status"] == "valid"
    assert events.index("architect_schema") < events.index("architect_semantic") < events.index("mapper")
    assert events.index("mapper") < events.index("ce_schema") < events.index("ce_semantic") < events.index("source_binding") < events.index("target_bundle") < events.index("final_result_schema")
    assert events[-1] == "final_result_schema"


def test_mapper_skipped_when_architect_validator_fails():
    events: list[str] = []
    hooks = TransitionValidatorHooks(
        architect=lambda payload: [diagnostic("TEST_ARCHITECT_FAIL", "error", "architect failed", "$")],
        ce=lambda payload, bundle: [],
        events=events,
    )
    result = run_transition(source_bundle(architect_payload()), hooks)
    assert result["status"] == "invalid"
    assert result["output"] is None
    assert "architect_semantic" in events
    assert "mapper" not in events


def test_target_bundle_absent_when_ce_validator_fails():
    events: list[str] = []
    hooks = TransitionValidatorHooks(
        architect=lambda payload: [],
        ce=lambda payload, bundle: [diagnostic("TEST_CE_FAIL", "error", "ce failed", "$")],
        events=events,
    )
    result = run_transition(source_bundle(architect_payload()), hooks)
    assert result["status"] == "invalid"
    assert result["output"] is None
    assert "ce_schema" in events
    assert "ce_semantic" in events
    assert "source_binding" in events
    assert "target_bundle" not in events
    assert events[-1] == "final_result_schema"


def test_explicit_source_commit_preserved_and_missing_commit_omitted():
    explicit = run_transition(source_bundle(architect_payload(), include_commit=True), official_hooks())
    absent = run_transition(source_bundle(architect_payload(), include_commit=False), official_hooks())
    assert explicit["output"]["payload"]["data"]["source_repository_ref"]["commit_sha"] == ARCHITECT_COMMIT
    assert "commit_sha" not in absent["output"]["payload"]["data"]["source_repository_ref"]


def test_insufficient_evidence_transition_keeps_output_and_status():
    payload = architect_payload("missing-real-stage-output.v1.json")
    result = run_transition(source_bundle(payload), official_hooks())
    assert result["status"] == "insufficient_evidence"
    assert result["output"] is not None
    assert result["output"]["evidence_status"] == "insufficient_evidence"
    assert result["output"]["payload"]["data"]["intake_status"] == "insufficient_evidence"
    assert result["output"]["payload"]["data"]["missing_evidence"]


@pytest.mark.parametrize(("mutator", "code"), [
    (lambda b: b.__setitem__("stage", "builder"), "PG_A2C_WRONG_SOURCE_STAGE"),
    (lambda b: b["payload_schema"].__setitem__("id", "ev4-architect-output-contract@1.0.0"), "PG_A2C_SOURCE_SCHEMA_ID_MISMATCH"),
    (lambda b: b["payload_schema"].__setitem__("owner_repository", "rezahh107/EV4-Builder-Assistant-Repo"), "PG_A2C_SOURCE_OWNER_MISMATCH"),
])
def test_invalid_identity_inputs_fail_closed(mutator, code: str):
    bundle = source_bundle(architect_payload())
    mutator(bundle)
    result = run_transition(bundle, official_hooks())
    assert result["status"] == "invalid"
    assert result["output"] is None
    assert any(d["code"] == code for d in result["diagnostics"])


@pytest.mark.parametrize(("mutator", "code"), [
    (lambda lock: lock["files"].pop(0), "PG_A2C_LOCK_ROLE_MISSING"),
    (lambda lock: lock["files"].append(copy.deepcopy(lock["files"][0])), "PG_A2C_LOCK_ROLE_DUPLICATE"),
    (lambda lock: lock["files"].append({**copy.deepcopy(lock["files"][0]), "role": "unexpected_role"}), "PG_A2C_LOCK_ROLE_UNEXPECTED"),
    (lambda lock: lock["files"][0].__setitem__("repository", "rezahh107/EV4-Builder-Assistant-Repo"), "PG_A2C_LOCK_REPOSITORY_MISMATCH"),
    (lambda lock: lock["files"][0].__setitem__("accepted_commit", "0" * 40), "PG_A2C_LOCK_COMMIT_MISMATCH"),
    (lambda lock: lock["files"][0].__setitem__("path", "schemas/wrong.json"), "PG_A2C_LOCK_PATH_MISMATCH"),
    (lambda lock: lock["files"][0].__setitem__("contract_or_schema_id", "wrong@1.0.0"), "PG_A2C_LOCK_IDENTITY_MISMATCH"),
    (lambda lock: lock["files"][0].__setitem__("sha256_file_bytes", "0" * 64), "PG_A2C_EXTERNAL_HASH_MISMATCH"),
])
def test_lock_enforcement_rejects_tampering(mutator, code: str):
    lock = load_json_file(LOCK)
    mutator(lock)
    diagnostics = verify_external_contract_lock(lock, lock_source())
    assert any(d.code == code for d in diagnostics)


def test_repeat_run_byte_identical():
    bundle = source_bundle(architect_payload())
    first = canonical_dumps(run_transition(bundle, official_hooks()))
    second = canonical_dumps(run_transition(bundle, official_hooks()))
    assert first == second


def test_no_live_timestamp_and_nonfinite_invalid():
    result = run_transition(source_bundle(architect_payload()), official_hooks())
    assert "created_at" not in canonical_dumps(result)
    bundle = source_bundle(architect_payload())
    bundle["payload"]["data"]["extension_records"] = [float("nan")]
    proc = subprocess.run(
        [sys.executable, "-m", "ev4_transition.cli", "transition", "architect-to-ce", "-", "--architect-repo", str(ARCH), "--ce-repo", str(CE)],
        input=json.dumps(bundle),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode != 0
