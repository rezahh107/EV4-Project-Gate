from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ev4_transition.architect_to_ce import ARCHITECT_REPO, CE_REPO, transition_from_local_paths
from ev4_transition.canonical_json import bytes_sha256, canonical_dumps, load_json_file

ROOT = Path(__file__).resolve().parents[1]
ARCH = Path(os.environ.get("EV4_ARCHITECT_REPO", ROOT / "../EV4-Architect-Repo")).resolve()
CE = Path(os.environ.get("EV4_CE_REPO", ROOT / "../EV4-Constructability-Engineer-Repo")).resolve()
LOCK = ROOT / "contracts/locks/architect-to-ce-transition.v1.lock.json"


def external_available() -> bool:
    return (ARCH / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").exists() and (CE / "schemas/ce_architect_stage_intake.v1.schema.json").exists()


def lock_with_real_hashes(tmp_path: Path) -> Path:
    lock = load_json_file(LOCK)
    roots = {ARCHITECT_REPO: ARCH, CE_REPO: CE}
    for item in lock["files"]:
        item["sha256_file_bytes"] = bytes_sha256((roots[item["repository"]] / item["path"]).read_bytes())
    path = tmp_path / "lock.json"
    path.write_text(canonical_dumps(lock) + "\n", encoding="utf-8")
    return path


def corrupted_lock(tmp_path: Path) -> Path:
    good = load_json_file(lock_with_real_hashes(tmp_path))
    good["files"][0]["sha256_file_bytes"] = "0" * 64
    path = tmp_path / "bad-lock.json"
    path.write_text(canonical_dumps(good) + "\n", encoding="utf-8")
    return path


def architect_payload(name: str = "minimal-complete.v1.json") -> dict:
    subdir = "insufficient-evidence" if "missing" in name else "valid"
    return json.loads((ARCH / "fixtures/architect-stage-payload" / subdir / name).read_text(encoding="utf-8"))


def source_bundle(payload: dict, stage: str = "architect", schema_id: str = "ev4-architect-stage-payload@1.0.0") -> dict:
    evidence_status = "insufficient_evidence" if payload["payload_status"] == "insufficient_evidence" else "complete"
    bundle = {
        "schema_version": "stage-evidence-bundle.v1",
        "bundle_id": "synthetic-architect-a2c-001",
        "stage": stage,
        "payload_schema": {"id": schema_id, "version": "1.0.0", "owner_repository": "rezahh107/EV4-Architect-Repo"},
        "produced_by": {"repository": "rezahh107/EV4-Architect-Repo", "ref": "synthetic-fixture", "commit_sha": "b0651668b97f682bb17f66840c8e8c503fd3935d"},
        "evidence_status": evidence_status,
        "payload": {"schema_id": schema_id, "data": payload},
        "evidence": [{"id": "architect-payload", "kind": "fixture", "state": "validated", "description": "Synthetic Architect payload fixture.", "artifact_hash": {"algorithm": "sha256", "value": bytes_sha256(canonical_dumps(payload).encode("utf-8")), "scope": "canonical_json"}, "source": {"type": "synthetic_fixture", "reference": "Architect fixture"}}],
        "provenance": {"source": "synthetic-fixture", "created_by": "project-gate-tests"},
        "synthetic": True,
    }
    if evidence_status == "insufficient_evidence":
        bundle["missing_evidence"] = [{"id": item["unresolved_id"], "owner": item["owner"], "reason": item["reason"]} for item in payload.get("unresolved_evidence", [])]
    return bundle


pytestmark = pytest.mark.skipif(not external_available(), reason="pinned specialist checkouts are not available")


def run_transition(bundle: dict, lock_path: Path) -> dict:
    return transition_from_local_paths(bundle, ROOT / "schemas", lock_path, ARCH, CE)


def test_valid_transition_outputs_ce_bundle(tmp_path: Path):
    result = run_transition(source_bundle(architect_payload()), lock_with_real_hashes(tmp_path))
    assert result["status"] == "valid"
    assert result["output"]["stage"] == "ce"
    target = result["output"]["payload"]["data"]
    assert target["schema_id"] == "ev4-ce-architect-stage-intake@1.0.0"
    assert target["selected_architecture"]["selected_candidate_id"] == "ARCH-FAM-C"
    assert target["negative_boundary_assertions"]["builder_ready"] is False
    assert "ce_review_units" not in canonical_dumps(target)


def test_repeat_run_byte_identical(tmp_path: Path):
    bundle = source_bundle(architect_payload())
    lock = lock_with_real_hashes(tmp_path)
    first = canonical_dumps(run_transition(bundle, lock))
    second = canonical_dumps(run_transition(bundle, lock))
    assert first == second


def test_insufficient_evidence_transition_keeps_output_and_status(tmp_path: Path):
    payload = architect_payload("missing-real-stage-output.v1.json")
    result = run_transition(source_bundle(payload), lock_with_real_hashes(tmp_path))
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
def test_invalid_identity_inputs_fail_closed(tmp_path: Path, mutator, code: str):
    bundle = source_bundle(architect_payload())
    mutator(bundle)
    result = run_transition(bundle, lock_with_real_hashes(tmp_path))
    assert result["status"] == "invalid"
    assert result["output"] is None
    assert any(d["code"] == code for d in result["diagnostics"])


def test_external_hash_mismatch_fails_closed(tmp_path: Path):
    result = run_transition(source_bundle(architect_payload()), corrupted_lock(tmp_path))
    assert result["status"] == "invalid"
    assert result["output"] is None
    assert any(d["code"] == "PG_A2C_EXTERNAL_HASH_MISMATCH" for d in result["diagnostics"])


def test_no_live_timestamp_in_output(tmp_path: Path):
    result = run_transition(source_bundle(architect_payload()), lock_with_real_hashes(tmp_path))
    assert "created_at" not in canonical_dumps(result)


def test_cli_json_and_persian_outputs(tmp_path: Path):
    lock = lock_with_real_hashes(tmp_path)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(canonical_dumps(source_bundle(architect_payload())) + "\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "ev4_transition.cli", "--schema-root", str(ROOT / "schemas"), "transition", "architect-to-ce", str(bundle_path), "--architect-repo", str(ARCH), "--ce-repo", str(CE), "--lock", str(lock), "--format", "json"]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "valid"
    persian = subprocess.run(cmd[:-1] + ["persian"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert persian.returncode == 0
    assert "بسته معتبر" in persian.stdout


def test_cli_insufficient_exit_code_2(tmp_path: Path):
    lock = lock_with_real_hashes(tmp_path)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(canonical_dumps(source_bundle(architect_payload("missing-real-stage-output.v1.json"))) + "\n", encoding="utf-8")
    completed = subprocess.run([sys.executable, "-m", "ev4_transition.cli", "--schema-root", str(ROOT / "schemas"), "transition", "architect-to-ce", str(bundle_path), "--architect-repo", str(ARCH), "--ce-repo", str(CE), "--lock", str(lock)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "insufficient_evidence"
