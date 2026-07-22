from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_GATE_REPOSITORY = "rezahh107/EV4-Project-Gate"
PROJECT_GATE_SCHEMA_REGISTRY = {
    "stage-bundle.v1": "schemas/stage-bundle/stage-bundle.v1.schema.json",
    "transition-result.v1": "schemas/transition-result/transition-result.v1.schema.json",
    "architect-to-ce-transition-result.v1": "schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json",
    "diagnostic.v1": "schemas/diagnostic/diagnostic.v1.schema.json",
    "lock-manifest.v1": "schemas/lock-manifest/lock-manifest.v1.schema.json",
    "validator-evidence.v1": "schemas/validator-evidence/validator-evidence.v1.schema.json",
}


@dataclass(frozen=True)
class CoverageDiagnostic:
    code: str
    severity: str
    message: str
    path: str = "$"
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }
        if self.details:
            payload["details"] = self.details
        return payload


def validate_transition_result_semantics(payload: dict[str, Any]) -> list[CoverageDiagnostic]:
    diagnostics: list[CoverageDiagnostic] = []
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    source_provenance = provenance.get("source_provenance") if isinstance(provenance.get("source_provenance"), dict) else {}
    produced_by = provenance.get("produced_by") if isinstance(provenance.get("produced_by"), dict) else {}
    if payload.get("status") == "accepted":
        official_validators = produced_by.get("official_validators")
        if not isinstance(official_validators, list) or not official_validators:
            diagnostics.append(CoverageDiagnostic(
                "PG_EVIDENCE_ACCEPTED_MISSING_VALIDATOR_EVIDENCE",
                "error",
                "accepted result requires explicit official validator evidence.",
                "$.provenance.produced_by.official_validators",
            ))
        else:
            for index, validator_record in enumerate(official_validators):
                diagnostics.extend(_validate_validator_evidence_record(payload, validator_record, index))
        if (
            source_provenance.get("synthetic") is True
            or source_provenance.get("verification_state") == "synthetic_fixture_only"
            or source_provenance.get("kind") == "synthetic_fixture"
        ):
            diagnostics.append(CoverageDiagnostic(
                "PG_SYNTH_SYNTHETIC_ONLY_MARKED_ACCEPTED",
                "error",
                "synthetic-only evidence must not be marked accepted as real EV4 evidence.",
                "$.provenance.source_provenance",
            ))
    output_write = produced_by.get("output_write")
    if (
        payload.get("status") in {"accepted", "valid"}
        and isinstance(output_write, dict)
        and output_write.get("attempted") is True
        and output_write.get("succeeded") is False
    ):
        diagnostics.append(CoverageDiagnostic(
            "PG_OUTPUT_WRITE_FAILED_BUT_SUCCESS_STATUS",
            "error",
            "A successful status must not be emitted when output writing failed.",
            "$.provenance.produced_by.output_write.succeeded",
        ))
    return diagnostics


def validate_stage_bundle_semantics(
    payload: dict[str, Any], repo_root: str | Path | None = None
) -> list[CoverageDiagnostic]:
    payload_schema = payload.get("payload_schema") if isinstance(payload.get("payload_schema"), dict) else {}
    schema_id = payload_schema.get("id")
    owner_repository = payload_schema.get("owner_repository")
    if owner_repository != PROJECT_GATE_REPOSITORY:
        return []
    repository_path = PROJECT_GATE_SCHEMA_REGISTRY.get(schema_id)
    if repository_path is None:
        return [CoverageDiagnostic(
            "PG_BOUNDARY_COPIED_SPECIALIST_SCHEMA_CLAIMED_AS_PROJECT_GATE_OWNED",
            "error",
            "Project Gate-owned schema claims must match the exact Project Gate schema registry.",
            "$.payload_schema",
            {"schema_id": schema_id, "owner_repository": owner_repository},
        )]
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    schema_file = _resolve_reference_path(root, repository_path)
    if schema_file is None or not schema_file.is_file():
        return [CoverageDiagnostic(
            "PG_SCHEMA_REGISTRY_PATH_MISSING",
            "error",
            "Registered Project Gate schema path does not exist.",
            "$.payload_schema",
            {"schema_id": schema_id, "repository_path": repository_path},
        )]
    return []


def _validate_validator_evidence_record(
    payload: dict[str, Any], record: Any, index: int
) -> list[CoverageDiagnostic]:
    path = f"$.provenance.produced_by.official_validators[{index}]"
    diagnostics: list[CoverageDiagnostic] = []
    if not isinstance(record, dict):
        return [CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED",
            "error",
            "official validator evidence entry must be an object.",
            path,
        )]
    required = (
        "schema_version", "validator_id", "owner_repository", "validator_path",
        "execution_id", "status", "validated_stage", "validated_scope",
        "validated_hash", "result_digest",
    )
    missing = [field for field in required if field not in record]
    if missing:
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED", "error",
            "official validator evidence entry is missing required fields.", path,
            {"missing": missing},
        ))
    if record.get("schema_version") != "validator-evidence.v1":
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED", "error",
            "validator evidence schema_version must be validator-evidence.v1.",
            f"{path}.schema_version",
        ))
    if record.get("status") != "passed":
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_STATUS_NOT_PASSED", "error",
            "accepted result requires validator evidence status=passed.",
            f"{path}.status", {"status": record.get("status")},
        ))
    if not record.get("accepted_commit") and not record.get("validator_file_hash"):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_UNPINNED", "error",
            "validator evidence requires accepted_commit or validator_file_hash.", path,
        ))
    if record.get("accepted_commit") is not None and not _is_sha1(record.get("accepted_commit")):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_UNPINNED", "error",
            "accepted_commit must be a 40-character lowercase SHA-1.",
            f"{path}.accepted_commit",
        ))
    if record.get("validator_file_hash") is not None and not _is_sha256(record.get("validator_file_hash")):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_UNPINNED", "error",
            "validator_file_hash must be a 64-character lowercase SHA-256.",
            f"{path}.validator_file_hash",
        ))
    if record.get("validated_stage") != payload.get("source_stage"):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_STAGE_MISMATCH", "error",
            "validator evidence stage must match source_stage.",
            f"{path}.validated_stage",
            {"expected": payload.get("source_stage"), "actual": record.get("validated_stage")},
        ))
    scope = record.get("validated_scope")
    expected_hash = None
    if scope == "payload":
        expected_hash = ((payload.get("hashes") or {}).get("canonical_payload_hash") or {}).get("value")
    elif scope == "source_bundle":
        expected_hash = ((payload.get("hashes") or {}).get("source_bundle_hash") or {}).get("value")
    else:
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_SCOPE_MISMATCH", "error",
            "validated_scope must be payload or source_bundle.",
            f"{path}.validated_scope", {"actual": scope},
        ))
    if expected_hash is not None and record.get("validated_hash") != expected_hash:
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_HASH_MISMATCH", "error",
            "validator evidence validated_hash must match the declared result hash for its scope.",
            f"{path}.validated_hash",
            {"expected": expected_hash, "actual": record.get("validated_hash")},
        ))
    if not _is_sha256(record.get("result_digest")):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_RESULT_DIGEST_INVALID", "error",
            "validator evidence result_digest must be a lowercase SHA-256.",
            f"{path}.result_digest",
        ))
    if not isinstance(record.get("validator_path"), str) or not record.get("validator_path"):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED", "error",
            "validator_path must be a non-empty string.", f"{path}.validator_path",
        ))
    if not isinstance(record.get("owner_repository"), str) or not re.match(
        r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", record.get("owner_repository", "")
    ):
        diagnostics.append(CoverageDiagnostic(
            "PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED", "error",
            "owner_repository must be owner/repo.", f"{path}.owner_repository",
        ))
    return diagnostics


def _resolve_reference_path(repo_root: Path, reference: str) -> Path | None:
    if reference.startswith(("http://", "https://", "git://")):
        return None
    candidate = Path(reference)
    if candidate.is_absolute():
        return None
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _is_sha1(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None
