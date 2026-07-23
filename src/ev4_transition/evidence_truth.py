from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from .canonical_json import canonical_sha256

EvidenceClassification = Literal["real_verified", "synthetic", "insufficient_evidence"]
OwnerValidationStatus = Literal["accepted", "rejected", "not_available", "not_run"]


@dataclass(frozen=True)
class EvidenceResolution:
    classification: EvidenceClassification
    source_kind: str
    source_path: str | None
    embedded_object_present: bool
    actual_sha256: str | None
    declared_sha256: str | None
    hash_verified: bool
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
            "actual_sha256": self.actual_sha256,
            "declared_sha256": self.declared_sha256,
            "hash_verified": self.hash_verified,
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
    "architect_payload_valid": {"allowed_evidence_types": {"architect_stage_bundle"}, "required_owner": "rezahh107/EV4-Architect-Repo", "required_viewport": None},
    "architect_handoff_eligible": {"allowed_evidence_types": {"architect_stage_bundle", "producer_gate_export"}, "required_owner": "rezahh107/EV4-Architect-Repo", "required_viewport": None},
    "builder_completion_verified": {"allowed_evidence_types": {"action_batch", "layout_check", "completion_gate"}, "required_owner": "rezahh107/EV4-Builder-Assistant-Repo", "required_viewport": None},
    "execution_evidence_verified": {"allowed_evidence_types": {"execution_evidence"}, "required_owner": "rezahh107/EV4-Builder-Assistant-Repo", "required_viewport": None},
    "desktop_evidence_verified": {"allowed_evidence_types": {"execution_evidence", "viewport_evidence"}, "required_owner": "rezahh107/EV4-Builder-Assistant-Repo", "required_viewport": "desktop"},
    "tablet_evidence_verified": {"allowed_evidence_types": {"execution_evidence", "viewport_evidence"}, "required_owner": "rezahh107/EV4-Builder-Assistant-Repo", "required_viewport": "tablet"},
    "mobile_evidence_verified": {"allowed_evidence_types": {"execution_evidence", "viewport_evidence"}, "required_owner": "rezahh107/EV4-Builder-Assistant-Repo", "required_viewport": "mobile"},
    "responsive_validation_verified": {"allowed_evidence_types": {"responsive_output"}, "required_owner": "rezahh107/EV4-Responsive-Architect", "required_viewport": None},
    "kernel_decision_valid": {"allowed_evidence_types": {"kernel_intake_result"}, "required_owner": "rezahh107/EV4-Decision-Kernel", "required_viewport": None},
    "blocking_unknowns_absent": {"allowed_evidence_types": {"responsive_output", "kernel_intake_result"}, "required_owner": None, "required_viewport": None},
    "real_evidence_present": {"allowed_evidence_types": {"responsive_output", "execution_evidence", "viewport_evidence"}, "required_owner": None, "required_viewport": None},
}

_BOOLEAN_SYNTHETIC_KEYS = {"synthetic", "synthetic_only", "synthetic_fixture"}
_SYNTHETIC_VALUES = {"synthetic", "synthetic_fixture", "synthetic-fixture", "synthetic_validation_only", "fixture", "fixture_validation", "test_fixture"}
_MARKER_FIELDS = {"created_by", "source", "ref", "reference", "run_id", "export_id", "bundle_id", "kind", "type"}


def synthetic_indicators(value: Any) -> list[str]:
    indicators: set[str] = set()

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                child_path = f"{path}.{key}"
                key_lower = str(key).lower()
                if key_lower in _BOOLEAN_SYNTHETIC_KEYS and child not in (False, None, "", 0):
                    indicators.add(child_path)
                if isinstance(child, str):
                    token = child.strip().lower().replace(" ", "_")
                    normalized_path = child.replace("\\", "/").lower()
                    if token in _SYNTHETIC_VALUES:
                        indicators.add(child_path)
                    if key_lower == "fixture_classification" and ("synthetic" in token or "fixture" in token):
                        indicators.add(child_path)
                    if key_lower in _MARKER_FIELDS and ("synthetic" in token or "synthetic" in normalized_path or "/fixtures/" in f"/{normalized_path.strip('/')}/" or normalized_path.startswith("fixtures/") or ".synthetic." in normalized_path):
                        indicators.add(child_path)
                walk(child, child_path)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, "$")
    return sorted(indicators)


def derive_evidence_classification(value: Any, *, source_resolved: bool, hash_verified: bool, owner_validation_status: OwnerValidationStatus, claim_bindings_valid: bool = True) -> EvidenceClassification:
    if synthetic_indicators(value):
        return "synthetic"
    if not source_resolved or not hash_verified:
        return "insufficient_evidence"
    if owner_validation_status not in {"accepted", "not_available"}:
        return "insufficient_evidence"
    if not claim_bindings_valid:
        return "insufficient_evidence"
    return "real_verified"


def verify_evidence_claim(*, claim_id: str, evidence_type: str, owner_repository: str | None, subject_ref: str | None, expected_subject_ref: str | None = None, viewport: str | None = None) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    rule = CLAIM_COMPATIBILITY.get(claim_id)
    if rule is None:
        return [_diag("PG.EVIDENCE.CLAIM_UNKNOWN", "error", "$.claim_class", "Unknown consequential evidence claim.", claim_id=claim_id)]
    if evidence_type not in rule["allowed_evidence_types"]:
        diagnostics.append(_diag("PG.EVIDENCE.CLAIM_TYPE_INCOMPATIBLE", "error", "$.evidence_type", "Evidence type cannot satisfy the requested claim.", claim_id=claim_id, evidence_type=evidence_type))
    expected_owner = rule.get("required_owner")
    if expected_owner and owner_repository != expected_owner:
        diagnostics.append(_diag("PG.EVIDENCE.CLAIM_OWNER_MISMATCH", "error", "$.owner_repository", "Evidence owner does not match the claim owner.", claim_id=claim_id, expected=expected_owner, actual=owner_repository))
    required_viewport = rule.get("required_viewport")
    if required_viewport and viewport != required_viewport:
        diagnostics.append(_diag("PG.EVIDENCE.CLAIM_VIEWPORT_MISMATCH", "error", "$.viewport", "Evidence viewport cannot satisfy this claim.", claim_id=claim_id, expected=required_viewport, actual=viewport))
    if expected_subject_ref is not None and subject_ref != expected_subject_ref:
        diagnostics.append(_diag("PG.EVIDENCE.CLAIM_SUBJECT_MISMATCH", "error", "$.subject_ref", "Evidence subject does not match the consequential claim subject.", claim_id=claim_id, expected=expected_subject_ref, actual=subject_ref))
    return diagnostics


def resolve_evidence(*, embedded_object: Any | None = None, artifact_ref: str | None = None, declared_sha256: str | None, repository_root: str | Path | None = None, hash_scope: Literal["canonical_json", "file_bytes"] = "file_bytes", owner_repository: str | None = None, owner_commit: str | None = None, owner_validator: str | None = None, owner_validator_callback: Callable[[Path, Any], tuple[OwnerValidationStatus, list[dict[str, Any]]]] | None = None, claim_id: str | None = None, evidence_type: str | None = None, subject_ref: str | None = None, expected_subject_ref: str | None = None, viewport: str | None = None) -> EvidenceResolution:
    diagnostics: list[dict[str, Any]] = []
    value: Any = None
    source_path: Path | None = None
    actual_sha256: str | None = None
    source_kind = "missing"
    source_resolved = False

    if embedded_object is not None:
        value = embedded_object
        source_kind = "embedded"
        source_resolved = True
        try:
            actual_sha256 = canonical_sha256(embedded_object)
        except Exception as exc:
            diagnostics.append(_diag("PG.EVIDENCE.EMBEDDED_CANONICALIZATION_FAILED", "error", "$", "Embedded evidence could not be canonicalized.", error_type=type(exc).__name__))
    elif artifact_ref:
        source_kind = "referenced"
        if repository_root is None:
            diagnostics.append(_diag("PG.EVIDENCE.REPOSITORY_ROOT_REQUIRED", "insufficient_evidence", "$.artifact_ref", "Referenced evidence requires an owner repository root."))
        else:
            source_path, path_diagnostics = _safe_resolve(Path(repository_root), artifact_ref)
            diagnostics.extend(path_diagnostics)
            if source_path is not None:
                try:
                    raw = source_path.read_bytes()
                    actual_sha256 = hashlib.sha256(raw).hexdigest()
                    value = json.loads(raw.decode("utf-8"))
                    source_resolved = True
                except json.JSONDecodeError:
                    diagnostics.append(_diag("PG.EVIDENCE.JSON_INVALID", "error", "$.artifact_ref", "Referenced evidence is not valid JSON.", artifact_ref=artifact_ref))
                except (OSError, UnicodeDecodeError) as exc:
                    diagnostics.append(_diag("PG.EVIDENCE.READ_FAILED", "insufficient_evidence", "$.artifact_ref", "Referenced evidence bytes could not be read.", artifact_ref=artifact_ref, error_type=type(exc).__name__))
    else:
        diagnostics.append(_diag("PG.EVIDENCE.SOURCE_MISSING", "insufficient_evidence", "$", "Evidence source is missing."))

    if embedded_object is not None and hash_scope == "file_bytes":
        diagnostics.append(_diag("PG.EVIDENCE.HASH_SCOPE_UNSUPPORTED", "error", "$.hash_scope", "Embedded evidence requires canonical_json hashing."))
    if artifact_ref and hash_scope == "canonical_json" and value is not None:
        try:
            actual_sha256 = canonical_sha256(value)
        except Exception as exc:
            diagnostics.append(_diag("PG.EVIDENCE.CANONICALIZATION_FAILED", "error", "$.artifact_ref", "Referenced JSON could not be canonicalized.", error_type=type(exc).__name__))

    hash_verified = bool(actual_sha256 and declared_sha256 and actual_sha256 == declared_sha256)
    if not declared_sha256:
        diagnostics.append(_diag("PG.EVIDENCE.HASH_REQUIRED", "insufficient_evidence", "$.artifact_sha256", "A declared SHA-256 is required."))
    elif not _is_sha256(declared_sha256):
        diagnostics.append(_diag("PG.EVIDENCE.HASH_FORMAT_INVALID", "error", "$.artifact_sha256", "Declared SHA-256 must contain 64 hexadecimal characters."))
    elif actual_sha256 and not hash_verified:
        diagnostics.append(_diag("PG.EVIDENCE.HASH_MISMATCH", "error", "$.artifact_sha256", "Declared SHA-256 does not match the resolved evidence bytes.", declared=declared_sha256, actual=actual_sha256))

    owner_status: OwnerValidationStatus = "not_available" if owner_validator_callback is None else "not_run"
    if source_resolved and value is not None and owner_validator_callback is not None and source_path is not None:
        try:
            owner_status, owner_diags = owner_validator_callback(source_path, value)
            diagnostics.extend(owner_diags)
        except Exception as exc:
            owner_status = "rejected"
            diagnostics.append(_diag("PG.EVIDENCE.OWNER_VALIDATOR_FAILED", "error", "$.owner_validator", "Official owner validator execution failed.", error_type=type(exc).__name__))

    claim_diags: list[dict[str, Any]] = []
    if claim_id and evidence_type:
        claim_diags = verify_evidence_claim(claim_id=claim_id, evidence_type=evidence_type, owner_repository=owner_repository, subject_ref=subject_ref, expected_subject_ref=expected_subject_ref, viewport=viewport)
        diagnostics.extend(claim_diags)

    indicators = synthetic_indicators(value)
    classification = derive_evidence_classification(value, source_resolved=source_resolved, hash_verified=hash_verified, owner_validation_status=owner_status, claim_bindings_valid=not any(item.get("severity") == "error" for item in claim_diags))
    if classification == "synthetic":
        diagnostics.append(_diag("PG.EVIDENCE.SYNTHETIC_DERIVED", "insufficient_evidence", "$", "Runtime-derived evidence classification is synthetic.", indicators=indicators))
    elif classification == "insufficient_evidence" and not diagnostics:
        diagnostics.append(_diag("PG.EVIDENCE.INSUFFICIENT", "insufficient_evidence", "$", "Evidence could not be verified sufficiently for operational authority."))

    return EvidenceResolution(classification=classification, source_kind=source_kind, source_path=str(source_path) if source_path else None, embedded_object_present=embedded_object is not None, actual_sha256=actual_sha256, declared_sha256=declared_sha256, hash_verified=hash_verified, owner_repository=owner_repository, owner_commit=owner_commit, owner_validator=owner_validator, owner_validation_status=owner_status, claim_classes=(claim_id,) if claim_id else (), subject_refs=(subject_ref,) if subject_ref else (), synthetic_indicators=tuple(indicators), diagnostics=tuple(diagnostics), value=value)


def _safe_resolve(root: Path, artifact_ref: str) -> tuple[Path | None, list[dict[str, Any]]]:
    diagnostics: list[dict[str, Any]] = []
    try:
        root = root.resolve(strict=True)
        candidate = (root / artifact_ref).resolve(strict=True)
        candidate.relative_to(root)
    except FileNotFoundError:
        return None, [_diag("PG.EVIDENCE.FILE_MISSING", "insufficient_evidence", "$.artifact_ref", "Referenced evidence file does not exist.", artifact_ref=artifact_ref)]
    except (OSError, RuntimeError, ValueError):
        return None, [_diag("PG.EVIDENCE.PATH_UNSAFE", "error", "$.artifact_ref", "Referenced evidence path is outside the owner repository or cannot be resolved safely.", artifact_ref=artifact_ref)]
    if not candidate.is_file():
        diagnostics.append(_diag("PG.EVIDENCE.NOT_REGULAR_FILE", "error", "$.artifact_ref", "Referenced evidence must be a regular file.", artifact_ref=artifact_ref))
        return None, diagnostics
    return candidate, diagnostics


def _is_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _diag(code: str, severity: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "severity": severity, "path": path, "message": message}
    if details:
        item["details"] = details
    return item
