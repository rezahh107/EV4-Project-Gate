from __future__ import annotations

import json
from pathlib import Path

from ev4_transition.canonical_json import bytes_sha256
from ev4_transition.evidence_truth import (
    RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
    derive_evidence_classification,
    resolve_evidence,
    synthetic_indicators,
)

BUILDER_REPO = "rezahh107/EV4-Builder-Assistant-Repo"
BUILDER_COMMIT = "69a2c61edf6d06b4418ad770fcefbfdffcf275d6"


def _derive(value):
    return derive_evidence_classification(
        value,
        source_resolved=True,
        hash_verified=True,
        schema_valid=True,
        claim_binding_valid=True,
        subject_binding_valid=True,
        positive_proof_verified=True,
    )


def _write_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return bytes_sha256(path.read_bytes())


def _viewport_artifact(tmp_path: Path, *, viewport: str = "desktop") -> tuple[Path, str]:
    path = tmp_path / "viewport.json"
    digest = _write_json(
        path,
        {
            "evidence_ref": f"{viewport}-proof",
            "viewport": viewport,
            "run_id": "RUN-1",
            "status": "confirmed",
        },
    )
    return path, digest


def _write_receipt(
    artifact_path: Path,
    digest: str,
    *,
    viewport: str = "desktop",
    receipt_hash: str | None = None,
) -> None:
    _write_json(
        artifact_path.with_name(artifact_path.name + ".receipt.json"),
        {
            "schema": RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
            "evidence_type": "viewport_artifact",
            "viewport": viewport,
            "run_id": "RUN-1",
            "subject_ref": "desktop-proof",
            "artifact_ref": artifact_path.name,
            "artifact_sha256": receipt_hash or digest,
            "producer_commit": BUILDER_COMMIT,
            "capture_status": "completed",
            "validation_status": "accepted",
        },
    )


def _resolve_viewport(tmp_path: Path, digest: str):
    return resolve_evidence(
        artifact_ref="viewport.json",
        declared_sha256=digest,
        repository_root=tmp_path,
        owner_repository=BUILDER_REPO,
        owner_commit=BUILDER_COMMIT,
        claim_id="desktop_evidence_verified",
        evidence_type="viewport_evidence",
        subject_ref="desktop-proof",
        expected_subject_ref="desktop-proof",
        viewport="desktop",
    )


def test_top_level_synthetic_derives_synthetic():
    value = {"synthetic": True}
    assert synthetic_indicators(value)
    assert _derive(value) == "synthetic"


def test_nested_fixture_source_derives_synthetic():
    value = {"evidence": {"source": {"type": "synthetic_fixture"}}}
    assert _derive(value) == "synthetic"


def test_fixture_path_derives_synthetic():
    assert synthetic_indicators({"source": {"reference": "fixtures/evidence.json"}})


def test_absent_source_bytes_derives_insufficient_evidence(tmp_path: Path):
    result = resolve_evidence(
        artifact_ref="missing.json",
        declared_sha256="0" * 64,
        repository_root=tmp_path,
        evidence_type="action_batch",
        claim_id="builder_completion_verified",
        owner_repository=BUILDER_REPO,
    )
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.FILE_MISSING" for item in result.diagnostics)


def test_renamed_fixture_without_positive_proof_is_rejected(tmp_path: Path):
    path = tmp_path / "delivery.json"
    digest = _write_json(path, {"schema": "ev4-action-batch@1.0.0", "actions": []})
    result = resolve_evidence(
        artifact_ref=path.name,
        declared_sha256=digest,
        repository_root=tmp_path,
        owner_repository=BUILDER_REPO,
        owner_commit=BUILDER_COMMIT,
        claim_id="builder_completion_verified",
        evidence_type="action_batch",
        subject_ref="delivery.json",
        expected_subject_ref="delivery.json",
    )
    assert result.synthetic_indicators == ()
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.OWNER_VALIDATOR_REQUIRED" for item in result.diagnostics)


def test_owner_validator_acceptance_is_positive_proof(tmp_path: Path):
    path = tmp_path / "action-batch.json"
    digest = _write_json(path, {"schema": "ev4-action-batch@1.0.0", "actions": []})
    result = resolve_evidence(
        artifact_ref=path.name,
        declared_sha256=digest,
        repository_root=tmp_path,
        owner_repository=BUILDER_REPO,
        owner_commit=BUILDER_COMMIT,
        owner_validator="scripts/validate-action-batch.mjs",
        owner_validator_callback=lambda _path, _value: ("accepted", []),
        claim_id="builder_completion_verified",
        evidence_type="action_batch",
        subject_ref=path.name,
        expected_subject_ref=path.name,
    )
    assert result.classification == "real_verified"
    assert result.positive_proof_verified is True
    assert result.schema_valid is True


def test_valid_hash_without_runtime_receipt_is_rejected(tmp_path: Path):
    _, digest = _viewport_artifact(tmp_path)
    result = _resolve_viewport(tmp_path, digest)
    assert result.hash_verified is True
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.RUNTIME_RECEIPT_REQUIRED" for item in result.diagnostics)


def test_runtime_receipt_with_wrong_hash_is_rejected(tmp_path: Path):
    path, digest = _viewport_artifact(tmp_path)
    _write_receipt(path, digest, receipt_hash="a" * 64)
    result = _resolve_viewport(tmp_path, digest)
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.RUNTIME_RECEIPT_BINDING_MISMATCH" for item in result.diagnostics)


def test_runtime_receipt_with_wrong_viewport_is_rejected(tmp_path: Path):
    path, digest = _viewport_artifact(tmp_path)
    _write_receipt(path, digest, viewport="tablet")
    result = _resolve_viewport(tmp_path, digest)
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.RUNTIME_RECEIPT_BINDING_MISMATCH" for item in result.diagnostics)


def test_correct_runtime_receipt_and_artifact_are_real_verified(tmp_path: Path):
    path, digest = _viewport_artifact(tmp_path)
    _write_receipt(path, digest)
    result = _resolve_viewport(tmp_path, digest)
    assert result.classification == "real_verified"
    assert result.positive_proof_type == "runtime_receipt"
    assert result.positive_proof_verified is True
    assert result.schema_valid is True
    assert result.claim_binding_valid is True
    assert result.subject_binding_valid is True


def test_caller_classification_fields_do_not_authorize(tmp_path: Path):
    path = tmp_path / "viewport.json"
    digest = _write_json(
        path,
        {
            "evidence_ref": "desktop-proof",
            "viewport": "desktop",
            "run_id": "RUN-1",
            "status": "confirmed",
            "synthetic": False,
            "real_evidence": True,
            "evidence_status": "real_verified",
            "verification_status": "accepted",
            "classification": "real_verified",
        },
    )
    result = _resolve_viewport(tmp_path, digest)
    assert result.classification == "insufficient_evidence"
    assert result.positive_proof_verified is False


def test_wrong_file_hash_is_rejected(tmp_path: Path):
    path, digest = _viewport_artifact(tmp_path)
    _write_receipt(path, digest)
    result = _resolve_viewport(tmp_path, "a" * 64)
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.HASH_MISMATCH" for item in result.diagnostics)


def test_desktop_evidence_cannot_satisfy_tablet_claim(tmp_path: Path):
    path, digest = _viewport_artifact(tmp_path)
    _write_receipt(path, digest)
    result = resolve_evidence(
        artifact_ref="viewport.json",
        declared_sha256=digest,
        repository_root=tmp_path,
        owner_repository=BUILDER_REPO,
        owner_commit=BUILDER_COMMIT,
        claim_id="tablet_evidence_verified",
        evidence_type="viewport_evidence",
        subject_ref="desktop-proof",
        expected_subject_ref="desktop-proof",
        viewport="desktop",
    )
    assert result.classification == "insufficient_evidence"
    assert any(item["code"] == "PG.EVIDENCE.CLAIM_VIEWPORT_MISMATCH" for item in result.diagnostics)
