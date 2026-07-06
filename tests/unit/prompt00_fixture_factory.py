from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PRODUCER_REPOSITORY = "rezahh107/EV4-Architect-Repo"
PRODUCER_SHA = "a" * 40
HASH = "1" * 64


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def stage_bundle() -> dict[str, Any]:
    return {
        "schema_version": "stage-evidence-bundle.v1",
        "bundle_id": "architect-final-bundle-001",
        "stage": "architect",
        "payload_schema": {
            "id": "ev4-architect-stage-payload",
            "version": "1.0.0",
            "owner_repository": PRODUCER_REPOSITORY,
        },
        "produced_by": {
            "repository": PRODUCER_REPOSITORY,
            "ref": "refs/heads/main",
            "commit_sha": PRODUCER_SHA,
        },
        "evidence_status": "complete",
        "payload": {"schema_id": "ev4-architect-stage-payload@1.0.0", "data": {"status": "complete"}},
        "evidence": [
            {
                "id": "EVIDENCE-001",
                "kind": "report",
                "state": "validated",
                "description": "Synthetic Prompt 0 fixture.",
                "artifact_hash": {"algorithm": "sha256", "value": "0" * 64, "scope": "canonical_json"},
                "source": {"type": "synthetic_fixture", "reference": "tests/fixtures/producer_gate_export"},
            }
        ],
        "provenance": {"source": "synthetic Prompt 0 fixture", "created_by": "Prompt 0 fixture factory"},
        "synthetic": True,
    }


def producer_export() -> dict[str, Any]:
    return {
        "schema_version": "producer-gate-export.v1",
        "export_id": "export-architect-001",
        "producer": {
            "stage": "architect",
            "repository": PRODUCER_REPOSITORY,
            "ref": "refs/heads/main",
            "commit_sha": PRODUCER_SHA,
        },
        "pipeline_id": "architect-pipeline.v1",
        "run_id": "run-001",
        "stage_manifest": [
            {
                "stage_id": "collect",
                "stage_version": "1.0.0",
                "ordinal": 1,
                "mandatory": True,
                "status": "complete",
                "output": {
                    "present": True,
                    "artifact_ref": "artifacts/collect.json",
                    "artifact_hash": {"algorithm": "sha256", "value": HASH, "scope": "file_bytes"},
                },
                "blockers": [],
                "unknowns": [],
            },
            {
                "stage_id": "finalize",
                "stage_version": "1.0.0",
                "ordinal": 2,
                "mandatory": True,
                "status": "complete",
                "output": {
                    "present": True,
                    "artifact_ref": "artifacts/finalize.json",
                    "artifact_hash": {"algorithm": "sha256", "value": "2" * 64, "scope": "file_bytes"},
                },
                "blockers": [],
                "unknowns": [],
            },
        ],
        "final_stage_bundle": stage_bundle(),
        "handoff": {
            "target": "ce",
            "status": "successful",
            "allowed": True,
            "failure_reasons": [],
            "blocking_diagnostics": [],
            "unresolved_evidence": [],
        },
        "validation": {
            "schema_valid": True,
            "semantic_valid": True,
            "validator_id": "ev4-producer-gate-export-validator",
            "validator_version": "1.0.0",
            "diagnostics": [],
        },
        "acquisition_mode": {"mode": "producer_emitted_gate_artifact", "silent_fallback_allowed": False},
    }


def valid_export_case(name: str) -> dict[str, Any]:
    artifact = producer_export()
    if name == "complete":
        return artifact
    artifact["stage_manifest"][1]["output"] = {"present": False}
    artifact["handoff"]["allowed"] = False
    if name == "blocked":
        artifact["stage_manifest"][1]["status"] = "blocked"
        artifact["stage_manifest"][1]["blockers"] = [{"id": "FINALIZE_BLOCKED", "message": "Synthetic blocker."}]
        artifact["handoff"]["status"] = "blocked"
        artifact["handoff"]["failure_reasons"] = [{"id": "FR-001", "code": "FINALIZE_BLOCKED", "message": "Finalize blocked.", "stage_id": "finalize"}]
        artifact["handoff"]["blocking_diagnostics"] = [{"code": "FINALIZE_BLOCKED", "message": "Synthetic blocker.", "path": "$.stage_manifest[1]"}]
    elif name == "insufficient_evidence":
        artifact["stage_manifest"][1]["status"] = "insufficient_evidence"
        artifact["stage_manifest"][1]["unknowns"] = [{"id": "FINALIZE_UNKNOWN", "reason": "Evidence missing.", "required_source": "real Producer fixture"}]
        artifact["handoff"]["status"] = "insufficient_evidence"
        artifact["handoff"]["failure_reasons"] = [{"id": "FR-001", "code": "FINALIZE_EVIDENCE_MISSING", "message": "Evidence missing.", "stage_id": "finalize"}]
        artifact["handoff"]["unresolved_evidence"] = [{"id": "ME-001", "reason": "Real evidence unavailable.", "stage_id": "finalize", "required_source": "Producer fixture"}]
    else:
        raise AssertionError(name)
    return artifact


def invalid_export_case(name: str) -> dict[str, Any]:
    artifact = producer_export()
    manifest = artifact["stage_manifest"]
    if name == "competing_single_stage_envelope_identity": artifact["schema_version"] = "stage-evidence-bundle.v2"
    elif name == "missing_pipeline_id": artifact.pop("pipeline_id")
    elif name == "missing_run_id": artifact.pop("run_id")
    elif name == "duplicate_stage_id": manifest[1]["stage_id"] = manifest[0]["stage_id"]
    elif name == "duplicate_stage_ordinal": manifest[1]["ordinal"] = manifest[0]["ordinal"]
    elif name == "missing_mandatory_stage": manifest[1]["status"], manifest[1]["output"] = "not_run", {"present": False}
    elif name == "out_of_order_stage_manifest": manifest[0]["ordinal"], manifest[1]["ordinal"] = 2, 1
    elif name == "non_contiguous_stage_manifest": manifest[1]["ordinal"] = 3
    elif name == "complete_stage_without_output": manifest[0]["output"] = {"present": False}
    elif name == "output_without_sha256": manifest[0]["output"].pop("artifact_hash")
    elif name == "output_without_artifact_ref": manifest[0]["output"].pop("artifact_ref")
    elif name == "handoff_allowed_with_blocker": manifest[0]["status"], manifest[0]["blockers"] = "blocked", [{"id": "BLOCKED"}]
    elif name == "handoff_allowed_with_blocking_diagnostics": artifact["handoff"]["blocking_diagnostics"] = [{"code": "BLOCKED", "message": "blocked", "path": "$.stage_manifest[0]"}]
    elif name == "handoff_disallowed_without_failure_reason": artifact["handoff"].update({"allowed": False, "status": "blocked"})
    elif name == "final_stage_bundle_producer_mismatch": artifact["final_stage_bundle"]["produced_by"]["repository"] = "rezahh107/EV4-Builder-Assistant-Repo"
    elif name == "final_stage_bundle_commit_mismatch": artifact["final_stage_bundle"]["produced_by"]["commit_sha"] = "b" * 40
    elif name == "final_stage_bundle_stage_mismatch": artifact["final_stage_bundle"]["stage"] = "builder"
    elif name == "final_stage_bundle_payload_owner_mismatch": artifact["final_stage_bundle"]["payload_schema"]["owner_repository"] = "rezahh107/EV4-Builder-Assistant-Repo"
    elif name == "silent_fallback_allowed": artifact["acquisition_mode"]["silent_fallback_allowed"] = True
    elif name == "unknown_acquisition_mode": artifact["acquisition_mode"]["mode"] = "legacy"
    elif name == "self_validation_overclaim": artifact.pop("pipeline_id")
    else: raise AssertionError(name)
    return artifact


def lock_for(canonical_root: Path, vendored_root: Path) -> dict[str, Any]:
    canonical = canonical_root / "contracts/common/producer-gate-export.v1.schema.json"
    vendored = vendored_root / "contracts/project-gate/producer-gate-export.v1.schema.json"
    vendored.parent.mkdir(parents=True, exist_ok=True)
    vendored.write_bytes(canonical.read_bytes())
    digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
    return {
        "lock_schema": "project-gate-common-contract-lock.v1",
        "contract_owner": "rezahh107/EV4-Project-Gate",
        "contract_id": "producer-gate-export.v1",
        "contract_version": "1.0.0",
        "canonical": {"repository": "rezahh107/EV4-Project-Gate", "path": "contracts/common/producer-gate-export.v1.schema.json", "commit_sha": "0123456789abcdef0123456789abcdef01234567", "file_sha256": digest},
        "vendored": {"repository": PRODUCER_REPOSITORY, "path": "contracts/project-gate/producer-gate-export.v1.schema.json", "file_sha256": digest, "local_copy_authoritative": False},
        "verification": {"byte_equality_required": True, "compare_against_moving_default_branch": False},
    }
