from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ev4_transition.runners.records import ExecutionRecord, repo_relative
from ev4_transition.runners.repository_identity import inspect_checkout

RUNTIME_EVIDENCE_RECEIPT_SCHEMA = "ev4_runtime_evidence_receipt_v2"
LEGACY_RUNTIME_EVIDENCE_RECEIPT_SCHEMA = "ev4_runtime_evidence_receipt_v1"
OFFICIAL_RUNTIME_NOT_OBSERVED_REASON = "official_runtime_execution_not_observed"


@dataclass(frozen=True)
class ViewportEvidenceRun:
    """Observed output of one official viewport producer execution.

    This is runtime state, not an authorization token. Project Gate rechecks the
    checkout, tool, execution record, and artifact bytes before using it.
    """

    run_id: str
    producer_repository: str
    producer_commit: str
    producer_tool: str
    subject_ref: str
    viewport: str
    artifact_path: Path
    artifact_sha256: str
    capture_status: str
    validation_status: str
    execution_record: ExecutionRecord | None


@dataclass(frozen=True)
class ViewportRunVerification:
    classification: str
    positive_proof_verified: bool
    source_resolved: bool
    hash_verified: bool
    schema_valid: bool
    claim_binding_valid: bool
    subject_binding_valid: bool
    synthetic_conflict: bool
    actual_sha256: str | None
    artifact_ref: str | None
    value: Any = None
    derived_receipt: dict[str, Any] | None = None
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)


def verify_viewport_evidence_run(
    *,
    run: ViewportEvidenceRun | None,
    producer_checkout: str | Path | None,
    expected_repository: str,
    expected_commit: str,
    expected_tool: str,
    expected_subject_ref: str,
    expected_viewport: str,
) -> ViewportRunVerification:
    diagnostics: list[dict[str, Any]] = []
    value: Any = None
    actual_sha256: str | None = None
    artifact_ref: str | None = None
    source_resolved = False
    schema_valid = False
    claim_binding_valid = False
    subject_binding_valid = False
    hash_verified = False
    synthetic_conflict = False

    if run is None:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.OFFICIAL_RUNTIME_EXECUTION_NOT_OBSERVED",
                "insufficient_evidence",
                "$.runtime_execution",
                "Viewport evidence cannot be operationally verified without an observed official producer execution.",
                reason=OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
            )
        )
        return _verification(
            diagnostics=diagnostics,
            source_resolved=False,
            hash_verified=False,
            schema_valid=False,
            claim_binding_valid=False,
            subject_binding_valid=False,
            synthetic_conflict=False,
            actual_sha256=None,
            artifact_ref=None,
            value=None,
            derived_receipt=None,
        )

    if producer_checkout is None:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_CHECKOUT_REQUIRED",
                "insufficient_evidence",
                "$.runtime_execution.producer_checkout",
                "Viewport runtime verification requires the observed producer checkout.",
            )
        )
        return _verification(
            diagnostics=diagnostics,
            source_resolved=False,
            hash_verified=False,
            schema_valid=False,
            claim_binding_valid=False,
            subject_binding_valid=False,
            synthetic_conflict=False,
            actual_sha256=None,
            artifact_ref=None,
            value=None,
            derived_receipt=None,
        )

    root = Path(producer_checkout)
    identity = inspect_checkout(
        root,
        expected_repository=expected_repository,
        expected_commit=expected_commit,
    )
    diagnostics.extend(_identity_diagnostics(identity))
    identity_valid = identity.get("status") == "accepted"

    if run.producer_repository != expected_repository:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_REPOSITORY_MISMATCH",
                "error",
                "$.runtime_execution.producer_repository",
                "Viewport runtime producer repository does not match the pinned owner.",
                expected=expected_repository,
                actual=run.producer_repository,
            )
        )
    if run.producer_commit != expected_commit:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_COMMIT_MISMATCH",
                "error",
                "$.runtime_execution.producer_commit",
                "Viewport runtime producer commit does not match the pinned owner commit.",
                expected=expected_commit,
                actual=run.producer_commit,
            )
        )
    if run.producer_tool != expected_tool:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_TOOL_MISMATCH",
                "error",
                "$.runtime_execution.producer_tool",
                "Viewport runtime tool does not match the approved producer entrypoint.",
                expected=expected_tool,
                actual=run.producer_tool,
            )
        )

    tool_valid = _verify_tool_identity(root, expected_tool, diagnostics)
    record_valid = _verify_execution_record(
        run,
        expected_repository=expected_repository,
        expected_commit=expected_commit,
        expected_tool=expected_tool,
        diagnostics=diagnostics,
    )

    artifact = _resolve_run_artifact(root, run.artifact_path, diagnostics)
    if artifact is not None:
        artifact_ref = repo_relative(artifact, root)
        try:
            raw = artifact.read_bytes()
            source_resolved = True
            actual_sha256 = hashlib.sha256(raw).hexdigest()
            value = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_JSON_INVALID",
                    "error",
                    "$.runtime_execution.artifact_path",
                    "Viewport runtime artifact is not valid JSON.",
                )
            )
        except (OSError, UnicodeDecodeError) as exc:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_READ_FAILED",
                    "insufficient_evidence",
                    "$.runtime_execution.artifact_path",
                    "Viewport runtime artifact bytes could not be read.",
                    error_type=type(exc).__name__,
                )
            )

    record = run.execution_record
    record_output_hash = record.output_hash if isinstance(record, ExecutionRecord) else None
    hash_verified = bool(
        actual_sha256
        and actual_sha256 == run.artifact_sha256
        and record_output_hash == actual_sha256
    )
    if actual_sha256 and actual_sha256 != run.artifact_sha256:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_MUTATED",
                "error",
                "$.runtime_execution.artifact_sha256",
                "Viewport artifact bytes changed after the observed execution result was created.",
                recorded=run.artifact_sha256,
                actual=actual_sha256,
            )
        )
    if actual_sha256 and record_output_hash != actual_sha256:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_EXECUTION_OUTPUT_HASH_MISMATCH",
                "error",
                "$.runtime_execution.execution_record.output_hash",
                "Execution record output hash does not match the current artifact bytes.",
                recorded=record_output_hash,
                actual=actual_sha256,
            )
        )

    schema_diagnostics, binding_diagnostics = _validate_runtime_artifact(
        value,
        run=run,
        expected_subject_ref=expected_subject_ref,
        expected_viewport=expected_viewport,
    )
    diagnostics.extend(schema_diagnostics)
    diagnostics.extend(binding_diagnostics)
    schema_valid = not _has_blocking(schema_diagnostics)
    claim_binding_valid = not _has_blocking(binding_diagnostics)
    subject_binding_valid = claim_binding_valid

    if run.capture_status != "completed":
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_CAPTURE_INCOMPLETE",
                "insufficient_evidence",
                "$.runtime_execution.capture_status",
                "Viewport runtime capture must be completed.",
                actual=run.capture_status,
            )
        )
    if run.validation_status != "accepted":
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_VALIDATION_NOT_ACCEPTED",
                "insufficient_evidence",
                "$.runtime_execution.validation_status",
                "Viewport runtime validation must be accepted.",
                actual=run.validation_status,
            )
        )

    from ev4_transition.evidence_truth import synthetic_indicators

    indicators = synthetic_indicators(value)
    synthetic_conflict = bool(indicators)
    if synthetic_conflict:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.SYNTHETIC_DERIVED",
                "insufficient_evidence",
                "$.runtime_execution.artifact_path",
                "Observed viewport runtime artifact contains a synthetic conflict.",
                indicators=indicators,
            )
        )

    positive_proof_verified = all(
        (
            identity_valid,
            run.producer_repository == expected_repository,
            run.producer_commit == expected_commit,
            run.producer_tool == expected_tool,
            tool_valid,
            record_valid,
            source_resolved,
            hash_verified,
            schema_valid,
            claim_binding_valid,
            subject_binding_valid,
            run.capture_status == "completed",
            run.validation_status == "accepted",
            not synthetic_conflict,
        )
    )
    derived_receipt = (
        build_runtime_evidence_receipt(
            run=run,
            producer_checkout=root,
            artifact_sha256=actual_sha256,
        )
        if positive_proof_verified and actual_sha256
        else None
    )
    return _verification(
        diagnostics=diagnostics,
        source_resolved=source_resolved,
        hash_verified=hash_verified,
        schema_valid=schema_valid,
        claim_binding_valid=claim_binding_valid,
        subject_binding_valid=subject_binding_valid,
        synthetic_conflict=synthetic_conflict,
        actual_sha256=actual_sha256,
        artifact_ref=artifact_ref,
        value=value,
        derived_receipt=derived_receipt,
    )


def build_runtime_evidence_receipt(
    *,
    run: ViewportEvidenceRun,
    producer_checkout: str | Path,
    artifact_sha256: str,
) -> dict[str, Any]:
    record = run.execution_record
    if not isinstance(record, ExecutionRecord):
        raise ValueError("A typed execution record is required before receipt derivation.")
    return {
        "schema": RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
        "evidence_type": "viewport_artifact",
        "run_id": run.run_id,
        "producer_repository": run.producer_repository,
        "producer_commit": run.producer_commit,
        "producer_tool": run.producer_tool,
        "execution_status": "accepted",
        "execution_record_digest": record.execution_record_hash,
        "subject_ref": run.subject_ref,
        "viewport": run.viewport,
        "artifact_ref": repo_relative(run.artifact_path, producer_checkout),
        "artifact_sha256": artifact_sha256,
        "capture_status": run.capture_status,
        "validation_status": run.validation_status,
    }


def inspect_adjacent_runtime_receipt(
    *,
    repository_root: str | Path | None,
    artifact_ref: str | None,
    receipt_ref: str | None = None,
) -> tuple[Path | None, Any, list[dict[str, Any]]]:
    """Read a legacy/derived receipt for diagnostics without granting authority."""

    if repository_root is None or not artifact_ref:
        return None, None, []
    raw_ref = receipt_ref or f"{artifact_ref}.receipt.json"
    root = Path(repository_root)
    try:
        resolved_root = root.resolve(strict=True)
        path = (resolved_root / raw_ref).resolve(strict=True)
        path.relative_to(resolved_root)
    except FileNotFoundError:
        return None, None, []
    except (OSError, RuntimeError, ValueError):
        return None, None, [
            _diag(
                "PG.EVIDENCE.RUNTIME_RECEIPT_PATH_UNSAFE",
                "warning",
                "$.runtime_receipt_ref",
                "An adjacent runtime receipt path could not be inspected safely.",
                receipt_ref=raw_ref,
            )
        ]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return path, None, [
            _diag(
                "PG.EVIDENCE.RUNTIME_RECEIPT_DIAGNOSTIC_READ_FAILED",
                "warning",
                "$.runtime_receipt_ref",
                "Adjacent runtime receipt could not be parsed for diagnostics.",
                receipt_ref=raw_ref,
                error_type=type(exc).__name__,
            )
        ]
    schema = value.get("schema") if isinstance(value, dict) else None
    return path, value, [
        _diag(
            "PG.EVIDENCE.RUNTIME_RECEIPT_NON_AUTHORITATIVE",
            "warning",
            "$.runtime_receipt_ref",
            "Adjacent runtime receipt is diagnostic metadata only; an observed official execution is required.",
            receipt_ref=raw_ref,
            observed_schema=schema,
            reason=OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
        )
    ]


def _verify_tool_identity(root: Path, expected_tool: str, diagnostics: list[dict[str, Any]]) -> bool:
    try:
        resolved_root = root.resolve(strict=True)
        tool = (resolved_root / expected_tool).resolve(strict=True)
        tool.relative_to(resolved_root)
    except FileNotFoundError:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_TOOL_MISSING",
                "insufficient_evidence",
                "$.runtime_execution.producer_tool",
                "The pinned official viewport producer tool is unavailable.",
                expected_tool=expected_tool,
            )
        )
        return False
    except (OSError, RuntimeError, ValueError):
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_TOOL_PATH_INVALID",
                "error",
                "$.runtime_execution.producer_tool",
                "The official viewport producer tool path is invalid.",
                expected_tool=expected_tool,
            )
        )
        return False
    if not tool.is_file():
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_TOOL_NOT_FILE",
                "error",
                "$.runtime_execution.producer_tool",
                "The official viewport producer entrypoint must be a regular file.",
                expected_tool=expected_tool,
            )
        )
        return False
    return True


def _verify_execution_record(
    run: ViewportEvidenceRun,
    *,
    expected_repository: str,
    expected_commit: str,
    expected_tool: str,
    diagnostics: list[dict[str, Any]],
) -> bool:
    record = run.execution_record
    if not isinstance(record, ExecutionRecord):
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_EXECUTION_RECORD_REQUIRED",
                "insufficient_evidence",
                "$.runtime_execution.execution_record",
                "Viewport runtime authority requires a typed execution record.",
            )
        )
        return False
    valid = True
    expected_pairs = (
        ("tool_kind", "adapter", record.tool_kind),
        ("owner_repo", expected_repository, record.owner_repo),
        ("owner_commit", expected_commit, record.owner_commit),
        ("adapter_path", expected_tool, record.adapter_path),
    )
    for field_name, expected, actual in expected_pairs:
        if actual != expected:
            valid = False
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_EXECUTION_RECORD_MISMATCH",
                    "error",
                    f"$.runtime_execution.execution_record.{field_name}",
                    "Viewport execution record does not match the official producer context.",
                    field=field_name,
                    expected=expected,
                    actual=actual,
                )
            )
    if record.exit_code != 0 or record.failure_code is not None:
        valid = False
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_EXECUTION_FAILED",
                "insufficient_evidence",
                "$.runtime_execution.execution_record.exit_code",
                "Viewport producer process did not complete successfully.",
                exit_code=record.exit_code,
                failure_code=record.failure_code,
            )
        )
    if not _entrypoint_mentions_tool(record.command_or_entrypoint, record.command, expected_tool):
        valid = False
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ENTRYPOINT_MISMATCH",
                "error",
                "$.runtime_execution.execution_record.command_or_entrypoint",
                "Viewport execution record does not identify the approved producer entrypoint.",
                expected_tool=expected_tool,
            )
        )
    return valid


def _entrypoint_mentions_tool(entrypoint: list[str] | str | None, command: list[str], expected_tool: str) -> bool:
    values: list[str] = []
    if isinstance(entrypoint, str):
        values.append(entrypoint)
    elif isinstance(entrypoint, list):
        values.extend(str(item) for item in entrypoint)
    values.extend(str(item) for item in command)
    return any(value == expected_tool or value.endswith(f"/{expected_tool}") for value in values)


def _resolve_run_artifact(root: Path, raw_path: Path, diagnostics: list[dict[str, Any]]) -> Path | None:
    candidate = raw_path if raw_path.is_absolute() else root / raw_path
    try:
        resolved_root = root.resolve(strict=True)
        if candidate.is_symlink():
            raise ValueError("symlink")
        artifact = candidate.resolve(strict=True)
        artifact.relative_to(resolved_root)
    except FileNotFoundError:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_MISSING",
                "insufficient_evidence",
                "$.runtime_execution.artifact_path",
                "Observed viewport runtime artifact is missing.",
                artifact_path=str(raw_path),
            )
        )
        return None
    except (OSError, RuntimeError, ValueError):
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_PATH_INVALID",
                "error",
                "$.runtime_execution.artifact_path",
                "Observed viewport runtime artifact is outside the producer checkout or cannot be resolved safely.",
                artifact_path=str(raw_path),
            )
        )
        return None
    if not artifact.is_file():
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_NOT_FILE",
                "error",
                "$.runtime_execution.artifact_path",
                "Observed viewport runtime artifact must be a regular file.",
                artifact_path=str(raw_path),
            )
        )
        return None
    return artifact


def _validate_runtime_artifact(
    value: Any,
    *,
    run: ViewportEvidenceRun,
    expected_subject_ref: str,
    expected_viewport: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    schema_diagnostics: list[dict[str, Any]] = []
    binding_diagnostics: list[dict[str, Any]] = []
    if not isinstance(value, dict):
        return [
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_INVALID",
                "error",
                "$.runtime_execution.artifact_path",
                "Viewport runtime artifact must be a JSON object.",
            )
        ], []
    for field_name in ("evidence_ref", "viewport", "run_id", "status"):
        if not isinstance(value.get(field_name), str) or not value.get(field_name):
            schema_diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_SCHEMA_INVALID",
                    "error",
                    f"$.runtime_execution.artifact.{field_name}",
                    "Viewport runtime artifact is missing a required non-empty field.",
                    field=field_name,
                )
            )
    if value.get("status") != "confirmed":
        schema_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_ARTIFACT_STATUS_INVALID",
                "error",
                "$.runtime_execution.artifact.status",
                "Viewport runtime artifact status must be confirmed.",
                actual=value.get("status"),
            )
        )
    expected = {
        "run_id": run.run_id,
        "evidence_ref": expected_subject_ref,
        "viewport": expected_viewport,
    }
    for field_name, expected_value in expected.items():
        actual = value.get(field_name)
        if actual != expected_value:
            binding_diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_BINDING_MISMATCH",
                    "error",
                    f"$.runtime_execution.artifact.{field_name}",
                    "Viewport runtime artifact does not match the observed execution context.",
                    field=field_name,
                    expected=expected_value,
                    actual=actual,
                )
            )
    if run.subject_ref != expected_subject_ref:
        binding_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_SUBJECT_MISMATCH",
                "error",
                "$.runtime_execution.subject_ref",
                "Viewport runtime result does not match the expected subject.",
                expected=expected_subject_ref,
                actual=run.subject_ref,
            )
        )
    if run.viewport != expected_viewport:
        binding_diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_VIEWPORT_MISMATCH",
                "error",
                "$.runtime_execution.viewport",
                "Viewport runtime result does not match the expected viewport.",
                expected=expected_viewport,
                actual=run.viewport,
            )
        )
    return schema_diagnostics, binding_diagnostics


def _identity_diagnostics(identity: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in identity.get("diagnostics", []) if isinstance(item, dict)]


def _verification(
    *,
    diagnostics: list[dict[str, Any]],
    source_resolved: bool,
    hash_verified: bool,
    schema_valid: bool,
    claim_binding_valid: bool,
    subject_binding_valid: bool,
    synthetic_conflict: bool,
    actual_sha256: str | None,
    artifact_ref: str | None,
    value: Any,
    derived_receipt: dict[str, Any] | None,
) -> ViewportRunVerification:
    positive = all(
        (
            source_resolved,
            hash_verified,
            schema_valid,
            claim_binding_valid,
            subject_binding_valid,
            not synthetic_conflict,
            not _has_blocking(diagnostics),
        )
    )
    classification = "synthetic" if synthetic_conflict else ("real_verified" if positive else "insufficient_evidence")
    return ViewportRunVerification(
        classification=classification,
        positive_proof_verified=positive,
        source_resolved=source_resolved,
        hash_verified=hash_verified,
        schema_valid=schema_valid,
        claim_binding_valid=claim_binding_valid,
        subject_binding_valid=subject_binding_valid,
        synthetic_conflict=synthetic_conflict,
        actual_sha256=actual_sha256,
        artifact_ref=artifact_ref,
        value=value,
        derived_receipt=derived_receipt,
        diagnostics=tuple(diagnostics),
    )


def _has_blocking(diagnostics: list[dict[str, Any]]) -> bool:
    return any(item.get("severity") in {"error", "insufficient_evidence"} for item in diagnostics)


def _diag(code: str, severity: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
    }
    if details:
        item["details"] = details
    return item
