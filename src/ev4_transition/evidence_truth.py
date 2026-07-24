from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from .canonical_json import canonical_sha256
from .viewport_runtime import (
    OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
    RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
    ViewportEvidenceRun,
    inspect_adjacent_runtime_receipt,
    verify_viewport_evidence_run,
)

EvidenceClassification = Literal["real_verified", "synthetic", "insufficient_evidence"]
OwnerValidationStatus = Literal["accepted", "rejected", "not_available", "not_run"]
EvidenceProofType = Literal["owner_validator", "runtime_execution"]
_BLOCKING_SEVERITIES = {"error", "insufficient_evidence"}


@dataclass(frozen=True)
class EvidencePolicy:
    proof_type: EvidenceProofType


EVIDENCE_POLICY_REGISTRY: dict[str, EvidencePolicy] = {
    "architect_stage_bundle": EvidencePolicy("owner_validator"),
    "producer_gate_export": EvidencePolicy("owner_validator"),
    "builder_output": EvidencePolicy("owner_validator"),
    "action_batch": EvidencePolicy("owner_validator"),
    "layout_check": EvidencePolicy("owner_validator"),
    "completion_gate": EvidencePolicy("owner_validator"),
    "execution_evidence": EvidencePolicy("owner_validator"),
    "responsive_output": EvidencePolicy("owner_validator"),
    "kernel_intake_result": EvidencePolicy("owner_validator"),
    "viewport_evidence": EvidencePolicy("runtime_execution"),
}


@dataclass(frozen=True)
class EvidenceResolution:
    classification: EvidenceClassification
    source_kind: str
    source_path: str | None
    embedded_object_present: bool
    source_resolved: bool
    actual_sha256: str | None
    declared_sha256: str | None
    hash_verified: bool
    schema_valid: bool
    claim_binding_valid: bool
    subject_binding_valid: bool
    positive_proof_type: EvidenceProofType | None
    positive_proof_verified: bool
    synthetic_conflict: bool
    runtime_receipt_path: str | None = None
    reason: str | None = None
    derived_receipt: dict[str, Any] | None = None
    owner_repository: str | None = None
    owner_commit: str | None = None
    owner_validator: str | None = None
    owner_validation_status: OwnerValidationStatus = "not_run"
    claim_classes: tuple[str, ...] = ()
    subject_refs: tuple[str, ...] = ()
    synthetic_indicators: tuple[str, ...] = ()
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "embedded_object_present": self.embedded_object_present,
            "source_resolved": self.source_resolved,
            "actual_sha256": self.actual_sha256,
            "declared_sha256": self.declared_sha256,
            "hash_verified": self.hash_verified,
            "schema_valid": self.schema_valid,
            "claim_binding_valid": self.claim_binding_valid,
            "subject_binding_valid": self.subject_binding_valid,
            "positive_proof_type": self.positive_proof_type,
            "positive_proof_verified": self.positive_proof_verified,
            "synthetic_conflict": self.synthetic_conflict,
            "runtime_receipt_path": self.runtime_receipt_path,
            "reason": self.reason,
            "derived_receipt": self.derived_receipt,
            "owner_repository": self.owner_repository,
            "owner_commit": self.owner_commit,
            "owner_validator": self.owner_validator,
            "owner_validation_status": self.owner_validation_status,
            "claim_classes": list(self.claim_classes),
            "subject_refs": list(self.subject_refs),
            "synthetic_indicators": list(self.synthetic_indicators),
            "diagnostics": [dict(item) for item in self.diagnostics],
        }


CLAIM_COMPATIBILITY: dict[str, dict[str, Any]] = {
    "architect_payload_valid": {
        "allowed_evidence_types": {"architect_stage_bundle"},
        "required_owner": "rezahh107/EV4-Architect-Repo",
        "required_viewport": None,
    },
    "architect_handoff_eligible": {
        "allowed_evidence_types": {"architect_stage_bundle", "producer_gate_export"},
        "required_owner": "rezahh107/EV4-Architect-Repo",
        "required_viewport": None,
    },
    "builder_completion_verified": {
        "allowed_evidence_types": {"action_batch", "layout_check", "completion_gate"},
        "required_owner": "rezahh107/EV4-Builder-Assistant-Repo",
        "required_viewport": None,
    },
    "execution_evidence_verified": {
        "allowed_evidence_types": {"execution_evidence"},
        "required_owner": "rezahh107/EV4-Builder-Assistant-Repo",
        "required_viewport": None,
    },
    "desktop_evidence_verified": {
        "allowed_evidence_types": {"execution_evidence", "viewport_evidence"},
        "required_owner": "rezahh107/EV4-Builder-Assistant-Repo",
        "required_viewport": "desktop",
    },
    "tablet_evidence_verified": {
        "allowed_evidence_types": {"execution_evidence", "viewport_evidence"},
        "required_owner": "rezahh107/EV4-Builder-Assistant-Repo",
        "required_viewport": "tablet",
    },
    "mobile_evidence_verified": {
        "allowed_evidence_types": {"execution_evidence", "viewport_evidence"},
        "required_owner": "rezahh107/EV4-Builder-Assistant-Repo",
        "required_viewport": "mobile",
    },
    "responsive_validation_verified": {
        "allowed_evidence_types": {"responsive_output"},
        "required_owner": "rezahh107/EV4-Responsive-Architect",
        "required_viewport": None,
    },
    "kernel_decision_valid": {
        "allowed_evidence_types": {"kernel_intake_result"},
        "required_owner": "rezahh107/EV4-Decision-Kernel",
        "required_viewport": None,
    },
    "blocking_unknowns_absent": {
        "allowed_evidence_types": {"responsive_output", "kernel_intake_result"},
        "required_owner": None,
        "required_viewport": None,
    },
    "real_evidence_present": {
        "allowed_evidence_types": {"responsive_output", "execution_evidence", "viewport_evidence"},
        "required_owner": None,
        "required_viewport": None,
    },
}

_BOOLEAN_SYNTHETIC_KEYS = {"synthetic", "synthetic_only", "synthetic_fixture"}
_SYNTHETIC_VALUES = {
    "synthetic",
    "synthetic_fixture",
    "synthetic-fixture",
    "synthetic_validation_only",
    "fixture",
    "fixture_validation",
    "test_fixture",
}
_MARKER_FIELDS = {
    "created_by",
    "source",
    "ref",
    "reference",
    "run_id",
    "export_id",
    "bundle_id",
    "kind",
    "type",
}


def synthetic_indicators(value: Any) -> list[str]:
    indicators: set[str] = set()

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                child_path = f"{path}.{key}"
                key_lower = str(key).lower()
                if key_lower in _BOOLEAN_SYNTHETIC_KEYS and child not in (
                    False,
                    None,
                    "",
                    0,
                ):
                    indicators.add(child_path)
                if isinstance(child, str):
                    token = child.strip().lower().replace(" ", "_")
                    normalized_path = child.replace("\\", "/").lower()
                    if token in _SYNTHETIC_VALUES:
                        indicators.add(child_path)
                    if key_lower == "fixture_classification" and (
                        "synthetic" in token or "fixture" in token
                    ):
                        indicators.add(child_path)
                    if key_lower in _MARKER_FIELDS and (
                        "synthetic" in token
                        or "synthetic" in normalized_path
                        or "/fixtures/" in f"/{normalized_path.strip('/')}/"
                        or normalized_path.startswith("fixtures/")
                        or ".synthetic." in normalized_path
                    ):
                        indicators.add(child_path)
                walk(child, child_path)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, "$")
    return sorted(indicators)


def derive_evidence_classification(
    value: Any,
    *,
    source_resolved: bool,
    hash_verified: bool,
    schema_valid: bool | None = None,
    claim_binding_valid: bool | None = None,
    subject_binding_valid: bool | None = None,
    positive_proof_verified: bool | None = None,
    synthetic_conflict: bool | None = None,
    owner_validation_status: OwnerValidationStatus | None = None,
) -> EvidenceClassification:
    """Derive authority from explicit predicates only.

    ``owner_validation_status`` remains accepted for compatibility with callers
    that use this helper only as a rejection classifier. It cannot grant
    positive authority.
    """

    conflict = (
        bool(synthetic_indicators(value))
        if synthetic_conflict is None
        else synthetic_conflict
    )
    if conflict:
        return "synthetic"
    if all(
        (
            source_resolved,
            hash_verified,
            schema_valid is True,
            claim_binding_valid is True,
            subject_binding_valid is True,
            positive_proof_verified is True,
        )
    ):
        return "real_verified"
    return "insufficient_evidence"


def verify_evidence_claim(
    *,
    claim_id: str,
    evidence_type: str,
    owner_repository: str | None,
    subject_ref: str | None,
    expected_subject_ref: str | None = None,
    viewport: str | None = None,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    rule = CLAIM_COMPATIBILITY.get(claim_id)
    if rule is None:
        return [
            _diag(
                "PG.EVIDENCE.CLAIM_UNKNOWN",
                "error",
                "$.claim_class",
                "Unknown consequential evidence claim.",
                claim_id=claim_id,
            )
        ]
    if evidence_type not in rule["allowed_evidence_types"]:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.CLAIM_TYPE_INCOMPATIBLE",
                "error",
                "$.evidence_type",
                "Evidence type cannot satisfy the requested claim.",
                claim_id=claim_id,
                evidence_type=evidence_type,
            )
        )
    expected_owner = rule.get("required_owner")
    if expected_owner and owner_repository != expected_owner:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.CLAIM_OWNER_MISMATCH",
                "error",
                "$.owner_repository",
                "Evidence owner does not match the claim owner.",
                claim_id=claim_id,
                expected=expected_owner,
                actual=owner_repository,
            )
        )
    required_viewport = rule.get("required_viewport")
    if required_viewport and viewport != required_viewport:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.CLAIM_VIEWPORT_MISMATCH",
                "error",
                "$.viewport",
                "Evidence viewport cannot satisfy this claim.",
                claim_id=claim_id,
                expected=required_viewport,
                actual=viewport,
            )
        )
    if expected_subject_ref is not None and subject_ref != expected_subject_ref:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.CLAIM_SUBJECT_MISMATCH",
                "error",
                "$.subject_ref",
                "Evidence subject does not match the consequential claim subject.",
                claim_id=claim_id,
                expected=expected_subject_ref,
                actual=subject_ref,
            )
        )
    return diagnostics


def resolve_evidence(
    *,
    embedded_object: Any | None = None,
    artifact_ref: str | None = None,
    declared_sha256: str | None,
    repository_root: str | Path | None = None,
    hash_scope: Literal["canonical_json", "file_bytes"] = "file_bytes",
    owner_repository: str | None = None,
    owner_commit: str | None = None,
    owner_validator: str | None = None,
    owner_validator_callback: Callable[
        [Path, Any], tuple[OwnerValidationStatus, list[dict[str, Any]]]
    ]
    | None = None,
    claim_id: str | None = None,
    evidence_type: str | None = None,
    subject_ref: str | None = None,
    expected_subject_ref: str | None = None,
    viewport: str | None = None,
    runtime_receipt_ref: str | None = None,
    runtime_run: ViewportEvidenceRun | None = None,
    producer_checkout: str | Path | None = None,
    expected_runtime_tool: str | None = None,
) -> EvidenceResolution:
    diagnostics: list[dict[str, Any]] = []
    value: Any = None
    source_path: Path | None = None
    actual_sha256: str | None = None
    source_kind = "missing"
    source_resolved = False

    if embedded_object is not None:
        value, source_kind, source_resolved = embedded_object, "embedded", True
        try:
            actual_sha256 = canonical_sha256(embedded_object)
        except Exception as exc:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.EMBEDDED_CANONICALIZATION_FAILED",
                    "error",
                    "$",
                    "Embedded evidence could not be canonicalized.",
                    error_type=type(exc).__name__,
                )
            )
    elif artifact_ref:
        source_kind = "referenced"
        if repository_root is None:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.REPOSITORY_ROOT_REQUIRED",
                    "insufficient_evidence",
                    "$.artifact_ref",
                    "Referenced evidence requires an owner repository root.",
                )
            )
        else:
            source_path, path_diagnostics = _safe_resolve(
                Path(repository_root), artifact_ref
            )
            diagnostics.extend(path_diagnostics)
            if source_path is not None:
                try:
                    raw = source_path.read_bytes()
                    actual_sha256 = hashlib.sha256(raw).hexdigest()
                    value = json.loads(raw.decode("utf-8"))
                    source_resolved = True
                except json.JSONDecodeError:
                    diagnostics.append(
                        _diag(
                            "PG.EVIDENCE.JSON_INVALID",
                            "error",
                            "$.artifact_ref",
                            "Referenced evidence is not valid JSON.",
                            artifact_ref=artifact_ref,
                        )
                    )
                except (OSError, UnicodeDecodeError) as exc:
                    diagnostics.append(
                        _diag(
                            "PG.EVIDENCE.READ_FAILED",
                            "insufficient_evidence",
                            "$.artifact_ref",
                            "Referenced evidence bytes could not be read.",
                            artifact_ref=artifact_ref,
                            error_type=type(exc).__name__,
                        )
                    )
    else:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.SOURCE_MISSING",
                "insufficient_evidence",
                "$",
                "Evidence source is missing.",
            )
        )

    if embedded_object is not None and hash_scope == "file_bytes":
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.HASH_SCOPE_UNSUPPORTED",
                "error",
                "$.hash_scope",
                "Embedded evidence requires canonical_json hashing.",
            )
        )
    if artifact_ref and hash_scope == "canonical_json" and value is not None:
        try:
            actual_sha256 = canonical_sha256(value)
        except Exception as exc:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.CANONICALIZATION_FAILED",
                    "error",
                    "$.artifact_ref",
                    "Referenced JSON could not be canonicalized.",
                    error_type=type(exc).__name__,
                )
            )

    hash_verified = bool(
        actual_sha256 and declared_sha256 and actual_sha256 == declared_sha256
    )
    if not declared_sha256:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.HASH_REQUIRED",
                "insufficient_evidence",
                "$.artifact_sha256",
                "A declared SHA-256 is required.",
            )
        )
    elif not _is_sha256(declared_sha256):
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.HASH_FORMAT_INVALID",
                "error",
                "$.artifact_sha256",
                "Declared SHA-256 must contain 64 hexadecimal characters.",
            )
        )
    elif actual_sha256 and not hash_verified:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.HASH_MISMATCH",
                "error",
                "$.artifact_sha256",
                "Declared SHA-256 does not match the resolved evidence bytes.",
                declared=declared_sha256,
                actual=actual_sha256,
            )
        )

    owner_status: OwnerValidationStatus = (
        "not_available" if owner_validator_callback is None else "not_run"
    )
    owner_diagnostics: list[dict[str, Any]] = []
    if (
        source_resolved
        and value is not None
        and owner_validator_callback is not None
        and source_path is not None
    ):
        try:
            owner_status, owner_diagnostics = owner_validator_callback(
                source_path, value
            )
            diagnostics.extend(owner_diagnostics)
        except Exception as exc:
            owner_status = "rejected"
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.OWNER_VALIDATOR_FAILED",
                    "error",
                    "$.owner_validator",
                    "Official owner validator execution failed.",
                    error_type=type(exc).__name__,
                )
            )

    claim_diagnostics: list[dict[str, Any]] = []
    if claim_id and evidence_type:
        claim_diagnostics = verify_evidence_claim(
            claim_id=claim_id,
            evidence_type=evidence_type,
            owner_repository=owner_repository,
            subject_ref=subject_ref,
            expected_subject_ref=expected_subject_ref,
            viewport=viewport,
        )
        diagnostics.extend(claim_diagnostics)
    elif claim_id or evidence_type:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.CLAIM_BINDING_INCOMPLETE",
                "error",
                "$.claim_class",
                "Evidence type and claim class must be supplied together.",
            )
        )

    policy = EVIDENCE_POLICY_REGISTRY.get(evidence_type or "")
    if policy is None:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.POLICY_REQUIRED",
                "insufficient_evidence",
                "$.evidence_type",
                "Operational evidence requires an explicit positive-proof policy.",
                evidence_type=evidence_type,
            )
        )

    schema_diagnostics: list[dict[str, Any]] = []
    subject_diagnostics: list[dict[str, Any]] = []
    runtime_receipt_path: Path | None = None
    reason: str | None = None
    derived_receipt: dict[str, Any] | None = None
    schema_valid = False
    positive_proof_verified = False

    if policy and policy.proof_type == "owner_validator":
        positive_proof_verified = owner_status == "accepted" and not _has_blocking(
            owner_diagnostics
        )
        schema_valid = positive_proof_verified
        if not positive_proof_verified:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.OWNER_VALIDATOR_REQUIRED",
                    "insufficient_evidence",
                    "$.owner_validator",
                    "The evidence policy requires an accepted official owner validator.",
                    evidence_type=evidence_type,
                    owner_validation_status=owner_status,
                )
            )
    elif policy and policy.proof_type == "runtime_execution":
        schema_diagnostics, subject_diagnostics = _validate_runtime_artifact(
            value,
            subject_ref=subject_ref,
            viewport=viewport,
        )
        diagnostics.extend(schema_diagnostics)
        diagnostics.extend(subject_diagnostics)
        schema_valid = not _has_blocking(schema_diagnostics)

        receipt_path, _, receipt_diagnostics = inspect_adjacent_runtime_receipt(
            repository_root=repository_root,
            artifact_ref=artifact_ref,
            receipt_ref=runtime_receipt_ref,
        )
        runtime_receipt_path = receipt_path
        diagnostics.extend(receipt_diagnostics)

        if runtime_run is None:
            reason = OFFICIAL_RUNTIME_NOT_OBSERVED_REASON
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.OFFICIAL_RUNTIME_EXECUTION_NOT_OBSERVED",
                    "insufficient_evidence",
                    "$.runtime_execution",
                    "File-only viewport evidence cannot authorize an operational transition.",
                    reason=reason,
                )
            )
        elif not owner_repository or not owner_commit or not expected_runtime_tool:
            reason = "official_runtime_contract_incomplete"
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_CONTRACT_INCOMPLETE",
                    "insufficient_evidence",
                    "$.runtime_execution",
                    "Runtime execution verification requires a pinned owner repository, commit, and official tool.",
                    reason=reason,
                )
            )
        else:
            verification = verify_viewport_evidence_run(
                run=runtime_run,
                producer_checkout=producer_checkout or repository_root,
                expected_repository=owner_repository,
                expected_commit=owner_commit,
                expected_tool=expected_runtime_tool,
                expected_subject_ref=expected_subject_ref or subject_ref or "",
                expected_viewport=viewport or "",
            )
            diagnostics.extend(verification.diagnostics)
            positive_proof_verified = verification.positive_proof_verified
            derived_receipt = verification.derived_receipt
            reason = (
                None
                if positive_proof_verified
                else "official_runtime_execution_not_verified"
            )
            if verification.artifact_ref != artifact_ref:
                positive_proof_verified = False
                reason = "runtime_artifact_binding_mismatch"
                diagnostics.append(
                    _diag(
                        "PG.EVIDENCE.RUNTIME_ARTIFACT_REF_MISMATCH",
                        "error",
                        "$.artifact_ref",
                        "Observed runtime artifact does not match the evidence binding artifact reference.",
                        expected=artifact_ref,
                        actual=verification.artifact_ref,
                    )
                )
            if verification.actual_sha256 != declared_sha256:
                positive_proof_verified = False
                reason = "runtime_artifact_hash_binding_mismatch"
                diagnostics.append(
                    _diag(
                        "PG.EVIDENCE.RUNTIME_DECLARED_HASH_MISMATCH",
                        "error",
                        "$.artifact_sha256",
                        "Observed runtime artifact hash does not match the evidence binding hash.",
                        expected=declared_sha256,
                        actual=verification.actual_sha256,
                    )
                )

    claim_binding_valid = bool(claim_id and evidence_type) and not _has_blocking(
        claim_diagnostics
    )
    subject_binding_valid = claim_binding_valid and not _has_blocking(
        subject_diagnostics
    )

    indicators = synthetic_indicators(value)
    synthetic_conflict = bool(indicators)
    classification = derive_evidence_classification(
        value,
        source_resolved=source_resolved,
        hash_verified=hash_verified,
        schema_valid=schema_valid,
        claim_binding_valid=claim_binding_valid,
        subject_binding_valid=subject_binding_valid,
        positive_proof_verified=positive_proof_verified,
        synthetic_conflict=synthetic_conflict,
    )
    if classification == "synthetic":
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.SYNTHETIC_DERIVED",
                "insufficient_evidence",
                "$",
                "Runtime-derived evidence classification is synthetic.",
                indicators=indicators,
            )
        )
    elif classification == "insufficient_evidence" and not diagnostics:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.INSUFFICIENT",
                "insufficient_evidence",
                "$",
                "Evidence could not be verified sufficiently for operational authority.",
            )
        )

    return EvidenceResolution(
        classification=classification,
        source_kind=source_kind,
        source_path=str(source_path) if source_path else None,
        embedded_object_present=embedded_object is not None,
        source_resolved=source_resolved,
        actual_sha256=actual_sha256,
        declared_sha256=declared_sha256,
        hash_verified=hash_verified,
        schema_valid=schema_valid,
        claim_binding_valid=claim_binding_valid,
        subject_binding_valid=subject_binding_valid,
        positive_proof_type=policy.proof_type if policy else None,
        positive_proof_verified=positive_proof_verified,
        synthetic_conflict=synthetic_conflict,
        runtime_receipt_path=str(runtime_receipt_path) if runtime_receipt_path else None,
        reason=reason,
        derived_receipt=derived_receipt,
        owner_repository=owner_repository,
        owner_commit=owner_commit,
        owner_validator=owner_validator,
        owner_validation_status=owner_status,
        claim_classes=(claim_id,) if claim_id else (),
        subject_refs=(subject_ref,) if subject_ref else (),
        synthetic_indicators=tuple(indicators),
        diagnostics=tuple(diagnostics),
        value=value,
    )


def _validate_runtime_artifact(
    value: Any,
    *,
    subject_ref: str | None,
    viewport: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    schema_diagnostics: list[dict[str, Any]] = []
    subject_diagnostics: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return [
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_INVALID",
                "error",
                "$",
                "Runtime viewport evidence must be a JSON object.",
            )
        ], []
    for field_name in ("evidence_ref", "viewport", "run_id", "status"):
        if not isinstance(value.get(field_name), str) or not value.get(field_name):
            schema_diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_SCHEMA_INVALID",
                    "error",
                    f"$.{field_name}",
                    "Runtime viewport evidence is missing a required non-empty field.",
                    field=field_name,
                )
            )
    if value.get("status") != "confirmed":
        schema_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_STATUS_INVALID",
                "error",
                "$.status",
                "Runtime viewport evidence status must be confirmed.",
                actual=value.get("status"),
            )
        )
    if subject_ref is not None and value.get("evidence_ref") != subject_ref:
        subject_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_SUBJECT_MISMATCH",
                "error",
                "$.evidence_ref",
                "Runtime viewport artifact does not bind the expected subject.",
                expected=subject_ref,
                actual=value.get("evidence_ref"),
            )
        )
    if viewport is not None and value.get("viewport") != viewport:
        subject_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_VIEWPORT_MISMATCH",
                "error",
                "$.viewport",
                "Runtime viewport artifact does not bind the expected viewport.",
                expected=viewport,
                actual=value.get("viewport"),
            )
        )
    return schema_diagnostics, subject_diagnostics


def _safe_resolve(
    root: Path, artifact_ref: str
) -> tuple[Path | None, list[dict[str, Any]]]:
    diagnostics: list[dict[str, Any]] = []
    try:
        root = root.resolve(strict=True)
        candidate = (root / artifact_ref).resolve(strict=True)
        candidate.relative_to(root)
    except FileNotFoundError:
        return None, [
            _diag(
                "PG.EVIDENCE.FILE_MISSING",
                "insufficient_evidence",
                "$.artifact_ref",
                "Referenced evidence file does not exist.",
                artifact_ref=artifact_ref,
            )
        ]
    except (OSError, RuntimeError, ValueError):
        return None, [
            _diag(
                "PG.EVIDENCE.PATH_UNSAFE",
                "error",
                "$.artifact_ref",
                "Referenced evidence path is outside the owner repository or cannot be resolved safely.",
                artifact_ref=artifact_ref,
            )
        ]
    if not candidate.is_file():
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.NOT_REGULAR_FILE",
                "error",
                "$.artifact_ref",
                "Referenced evidence must be a regular file.",
                artifact_ref=artifact_ref,
            )
        )
        return None, diagnostics
    return candidate, diagnostics


def _has_blocking(diagnostics: list[dict[str, Any]]) -> bool:
    return any(item.get("severity") in _BLOCKING_SEVERITIES for item in diagnostics)


def _is_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _diag(
    code: str,
    severity: str,
    path: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
    }
    if details:
        item["details"] = details
    return item
