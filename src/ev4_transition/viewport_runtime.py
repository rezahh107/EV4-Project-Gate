from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from ev4_transition.runners.records import ExecutionRecord
from ev4_transition.runners.repo_paths import (
    RepoPathError,
    normalize_repo_relative_ref,
    repo_relative_ref,
    resolve_repo_relative_directory,
    resolve_repo_relative_file,
)
from ev4_transition.runners.repository_identity import (
    PinnedExecutionWorktree,
    PinnedWorktreeError,
    inspect_checkout,
    inspect_tracked_worktree_clean,
    materialize_pinned_worktree,
)
from ev4_transition.runners.subprocess_runner import execute_official_tool
from ev4_transition.verified_artifact import VerifiedArtifactSnapshot

RUNTIME_EVIDENCE_RECEIPT_SCHEMA = "ev4_runtime_evidence_receipt_v2"
LEGACY_RUNTIME_EVIDENCE_RECEIPT_SCHEMA = "ev4_runtime_evidence_receipt_v1"
OFFICIAL_RUNTIME_NOT_OBSERVED_REASON = "official_runtime_execution_not_observed"
OUTPUT_REF_BINDING_MISMATCH_REASON = "runtime_output_ref_binding_mismatch"


@dataclass(frozen=True)
class ViewportEvidenceRun:
    """Typed result created internally after one viewport producer process run.

    The pure verifier accepts this value for tests and diagnostics. Operational
    authority must use ``execute_pinned_viewport_capture`` so the record and
    output bindings originate inside Project Gate's detached-worktree runner.
    """

    run_id: str
    producer_repository: str
    producer_commit: str
    producer_tool_ref: str
    working_directory_ref: str
    subject_ref: str
    viewport: str
    artifact_ref: str
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
    reason: str | None = None
    verified_repository: str | None = None
    verified_commit: str | None = None
    verified_tool_ref: str | None = None
    verified_working_directory_ref: str | None = None
    verified_artifact_ref: str | None = None
    ephemeral_artifact_path: Path | None = None
    artifact_snapshot: VerifiedArtifactSnapshot | None = None
    execution_record_digest: str | None = None
    verified_subject_ref: str | None = None
    verified_viewport: str | None = None
    verified_run_id: str | None = None
    value: Any = None
    derived_receipt: dict[str, Any] | None = None
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def artifact_ref(self) -> str | None:
        """Compatibility alias for callers that consume verification output."""

        return self.verified_artifact_ref

    @property
    def verified_artifact_path(self) -> Path | None:
        """Compatibility alias; operational results clear this ephemeral path."""

        return self.ephemeral_artifact_path

    def artifact_metadata(self) -> dict[str, Any] | None:
        return self.artifact_snapshot.metadata() if self.artifact_snapshot else None


@dataclass(frozen=True, slots=True)
class _ObservedViewportExecution:
    run: ViewportEvidenceRun
    artifact_path: Path | None
    exact_bytes: bytes | None = field(repr=False)


def execute_viewport_capture(
    *,
    execution_worktree: PinnedExecutionWorktree,
    producer_tool_ref: str,
    working_directory_ref: str,
    subject_ref: str,
    viewport: str,
    timeout_seconds: float,
) -> ViewportEvidenceRun:
    """Execute a producer adapter and return its internally created typed run.

    This lower-level function remains useful for bounded pure-verifier tests.
    Operational authority must use :func:`execute_pinned_viewport_capture`.
    """

    return _execute_viewport_capture_observed(
        execution_worktree=execution_worktree,
        producer_tool_ref=producer_tool_ref,
        working_directory_ref=working_directory_ref,
        subject_ref=subject_ref,
        viewport=viewport,
        timeout_seconds=timeout_seconds,
    ).run


def _execute_viewport_capture_observed(
    *,
    execution_worktree: PinnedExecutionWorktree,
    producer_tool_ref: str,
    working_directory_ref: str,
    subject_ref: str,
    viewport: str,
    timeout_seconds: float,
) -> _ObservedViewportExecution:
    """Execute and read the emitted artifact exactly once.

    The one observed byte sequence supplies the runtime hash, execution-record
    output hash, later semantic parse, immutable snapshot, receipt identity, and
    publication payload. The bytes are internal and excluded from repr output.
    """

    root = execution_worktree.root.resolve(strict=True)
    tool_ref = normalize_repo_relative_ref(producer_tool_ref)
    cwd_ref = normalize_repo_relative_ref(working_directory_ref, allow_root=True)
    tool = resolve_repo_relative_file(root, tool_ref)
    cwd = resolve_repo_relative_directory(root, cwd_ref)
    command = _adapter_command(tool, subject_ref=subject_ref, viewport=viewport)

    outcome = execute_official_tool(
        tool_kind="adapter",
        owner_repo=execution_worktree.repository,
        owner_commit=execution_worktree.commit,
        tool_path=tool,
        command=command,
        working_directory=cwd,
        repository_root=root,
        working_directory_ref=cwd_ref,
        timeout_seconds=timeout_seconds,
        parsed_result_ref="stdout:json",
        started_by="ev4-project-gate-pinned-viewport-runner",
        env=_runtime_env(root),
    )
    parsed = outcome.parsed_result if isinstance(outcome.parsed_result, dict) else {}

    raw_artifact_ref = parsed.get("artifact_ref")
    artifact_ref = ""
    artifact_sha256 = ""
    artifact_path: Path | None = None
    exact_bytes: bytes | None = None
    failure_code = outcome.execution_record.failure_code
    if isinstance(raw_artifact_ref, str):
        try:
            artifact_ref = normalize_repo_relative_ref(raw_artifact_ref)
            artifact_path = resolve_repo_relative_file(root, artifact_ref)
            exact_bytes = artifact_path.read_bytes()
            artifact_sha256 = hashlib.sha256(exact_bytes).hexdigest()
        except (RepoPathError, OSError):
            artifact_ref = raw_artifact_ref
            artifact_path = None
            exact_bytes = None
            failure_code = failure_code or "PG.EVIDENCE.RUNTIME_OUTPUT_REF_INVALID"
    else:
        failure_code = failure_code or "PG.EVIDENCE.RUNTIME_OUTPUT_REF_REQUIRED"

    record = replace(
        outcome.execution_record,
        owner_repo=execution_worktree.repository,
        owner_commit=execution_worktree.commit,
        adapter_path=tool_ref,
        working_directory=str(cwd),
        working_directory_ref=cwd_ref,
        output_ref=artifact_ref or None,
        output_hash=artifact_sha256 or None,
        failure_code=failure_code,
    )
    run = ViewportEvidenceRun(
        run_id=parsed.get("run_id") if isinstance(parsed.get("run_id"), str) else "",
        producer_repository=execution_worktree.repository,
        producer_commit=execution_worktree.commit,
        producer_tool_ref=tool_ref,
        working_directory_ref=cwd_ref,
        subject_ref=subject_ref,
        viewport=viewport,
        artifact_ref=artifact_ref,
        artifact_sha256=artifact_sha256,
        capture_status=(
            parsed.get("capture_status")
            if isinstance(parsed.get("capture_status"), str)
            else "not_completed"
        ),
        validation_status=(
            parsed.get("validation_status")
            if isinstance(parsed.get("validation_status"), str)
            else "not_run"
        ),
        execution_record=record,
    )
    return _ObservedViewportExecution(run, artifact_path, exact_bytes)


def execute_pinned_viewport_capture(
    *,
    source_repository: str | Path,
    expected_repository: str,
    expected_commit: str,
    producer_tool_ref: str,
    working_directory_ref: str,
    subject_ref: str,
    viewport: str,
    timeout_seconds: float = 30,
) -> ViewportRunVerification:
    """Official operational path: materialize, execute, snapshot, clean, return."""

    cleanup_diagnostics: list[dict[str, Any]] = []
    verification: ViewportRunVerification | None = None
    try:
        with materialize_pinned_worktree(
            source_repository,
            expected_repository,
            expected_commit,
            cleanup_diagnostics=cleanup_diagnostics,
        ) as worktree:
            observed = _execute_viewport_capture_observed(
                execution_worktree=worktree,
                producer_tool_ref=producer_tool_ref,
                working_directory_ref=working_directory_ref,
                subject_ref=subject_ref,
                viewport=viewport,
                timeout_seconds=timeout_seconds,
            )
            verification = verify_viewport_evidence_run(
                run=observed.run,
                execution_worktree=worktree,
                expected_repository=expected_repository,
                expected_commit=expected_commit,
                expected_tool_ref=producer_tool_ref,
                expected_working_directory_ref=working_directory_ref,
                expected_subject_ref=subject_ref,
                expected_viewport=viewport,
                _observed_artifact_path=observed.artifact_path,
                _observed_artifact_bytes=observed.exact_bytes,
            )
    except (PinnedWorktreeError, RepoPathError, OSError) as exc:
        diagnostic = (
            exc.to_diagnostic()
            if isinstance(exc, PinnedWorktreeError)
            else _diag(
                getattr(exc, "code", "PG.EVIDENCE.RUNTIME_EXECUTION_SETUP_FAILED"),
                "insufficient_evidence",
                "$.runtime_execution",
                str(exc),
            )
        )
        if cleanup_diagnostics and verification is not None:
            return _revoke_for_cleanup_failure(
                verification,
                [diagnostic, *cleanup_diagnostics],
            )
        reason = (
            "pinned_worktree_cleanup_failed"
            if cleanup_diagnostics
            else "pinned_runtime_execution_failed"
        )
        return _empty_verification(
            [diagnostic, *cleanup_diagnostics],
            reason=reason,
        )

    if verification is None:
        return _empty_verification(
            [
                _diag(
                    "PG.EVIDENCE.RUNTIME_VERIFICATION_MISSING",
                    "insufficient_evidence",
                    "$.runtime_execution",
                    "Pinned viewport execution did not produce a verification result.",
                )
            ],
            reason="pinned_runtime_execution_failed",
        )
    if cleanup_diagnostics:
        return _revoke_for_cleanup_failure(verification, cleanup_diagnostics)

    # The worktree has been removed. Exact bytes survive in the immutable
    # snapshot; the deleted temporary path is never advertised as durable.
    return replace(verification, ephemeral_artifact_path=None)


def verify_viewport_evidence_run(
    *,
    run: ViewportEvidenceRun | None,
    expected_repository: str,
    expected_commit: str,
    expected_subject_ref: str,
    expected_viewport: str,
    execution_worktree: PinnedExecutionWorktree | None = None,
    expected_tool_ref: str | None = None,
    expected_working_directory_ref: str = ".",
    producer_checkout: str | Path | None = None,
    expected_tool: str | None = None,
    _observed_artifact_path: Path | None = None,
    _observed_artifact_bytes: bytes | None = None,
) -> ViewportRunVerification:
    """Pure exact-binding verifier for an internally produced runtime result.

    The official operational path supplies the one byte sequence read directly
    after process completion. Standalone tests omit it; the verifier then reads
    the resolved artifact once while the worktree is still alive.
    """

    diagnostics: list[dict[str, Any]] = []
    if run is None:
        return _empty_verification(
            [
                _diag(
                    "PG.EVIDENCE.OFFICIAL_RUNTIME_EXECUTION_NOT_OBSERVED",
                    "insufficient_evidence",
                    "$.runtime_execution",
                    "Viewport evidence cannot be operationally verified without an observed official producer execution.",
                    reason=OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
                )
            ],
            reason=OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
        )
    if execution_worktree is None:
        details = {}
        if producer_checkout is not None:
            details["caller_checkout_ignored"] = str(producer_checkout)
        return _empty_verification(
            [
                _diag(
                    "PG.EVIDENCE.RUNTIME_PINNED_WORKTREE_REQUIRED",
                    "insufficient_evidence",
                    "$.runtime_execution.worktree",
                    "Caller-supplied checkouts and runtime records cannot authorize; the official path must create a detached pinned worktree internally.",
                    **details,
                )
            ],
            reason="pinned_execution_worktree_required",
        )

    expected_tool_ref = expected_tool_ref or expected_tool
    if not expected_tool_ref:
        return _empty_verification(
            [
                _diag(
                    "PG.EVIDENCE.RUNTIME_TOOL_CONTRACT_REQUIRED",
                    "insufficient_evidence",
                    "$.runtime_execution.expected_tool_ref",
                    "An exact official producer tool reference is required.",
                )
            ],
            reason="official_runtime_tool_required",
        )

    root = execution_worktree.root.resolve()
    expected_commit = expected_commit.lower()
    identity = inspect_checkout(
        root,
        expected_repository=expected_repository,
        expected_commit=expected_commit,
    )
    diagnostics.extend(_identity_diagnostics(identity))
    identity_valid = identity.get("status") == "accepted"

    tracked = inspect_tracked_worktree_clean(root)
    diagnostics.extend(_identity_diagnostics(tracked))
    tracked_clean = tracked.get("status") == "accepted"
    declared_worktree_valid = all(
        (
            execution_worktree.clean_verified,
            _same_repository(execution_worktree.repository, expected_repository),
            _same_commit(execution_worktree.commit, expected_commit),
        )
    )
    if not declared_worktree_valid:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_WORKTREE_BINDING_MISMATCH",
                "error",
                "$.runtime_execution.worktree",
                "Detached worktree identity does not match the expected runtime context.",
                expected_repository=expected_repository,
                expected_commit=expected_commit,
                actual_repository=execution_worktree.repository,
                actual_commit=execution_worktree.commit,
                clean_verified=execution_worktree.clean_verified,
            )
        )

    refs: dict[str, str | None] = {
        "expected_tool": _normalize_ref(
            expected_tool_ref,
            diagnostics,
            "$.runtime_execution.expected_tool_ref",
        ),
        "run_tool": _normalize_ref(
            run.producer_tool_ref,
            diagnostics,
            "$.runtime_execution.producer_tool_ref",
        ),
        "expected_cwd": _normalize_ref(
            expected_working_directory_ref,
            diagnostics,
            "$.runtime_execution.expected_working_directory_ref",
            allow_root=True,
        ),
        "run_cwd": _normalize_ref(
            run.working_directory_ref,
            diagnostics,
            "$.runtime_execution.working_directory_ref",
            allow_root=True,
        ),
        "run_output": _normalize_ref(
            run.artifact_ref,
            diagnostics,
            "$.runtime_execution.artifact_ref",
        ),
    }

    record = run.execution_record
    if not isinstance(record, ExecutionRecord):
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_EXECUTION_RECORD_REQUIRED",
                "insufficient_evidence",
                "$.runtime_execution.execution_record",
                "Viewport runtime authority requires a typed execution record created by the runner.",
            )
        )
        record_tool = record_cwd = record_output = None
    else:
        record_tool = _normalize_ref(
            record.adapter_path,
            diagnostics,
            "$.runtime_execution.execution_record.adapter_path",
        )
        record_cwd = _normalize_ref(
            record.working_directory_ref,
            diagnostics,
            "$.runtime_execution.execution_record.working_directory_ref",
            allow_root=True,
        )
        record_output = _normalize_ref(
            record.output_ref,
            diagnostics,
            "$.runtime_execution.execution_record.output_ref",
        )

    repository_binding = identity_valid and declared_worktree_valid and all(
        (
            _same_repository(run.producer_repository, expected_repository),
            isinstance(record, ExecutionRecord)
            and _same_repository(record.owner_repo, expected_repository),
        )
    )
    if not repository_binding:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_REPOSITORY_MISMATCH",
                "error",
                "$.runtime_execution.producer_repository",
                "Runtime repository values do not all match the detached pinned owner repository.",
                expected=expected_repository,
                run=run.producer_repository,
                record=(record.owner_repo if isinstance(record, ExecutionRecord) else None),
            )
        )

    commit_binding = identity_valid and declared_worktree_valid and all(
        (
            _same_commit(run.producer_commit, expected_commit),
            isinstance(record, ExecutionRecord)
            and _same_commit(record.owner_commit, expected_commit),
        )
    )
    if not commit_binding:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_COMMIT_MISMATCH",
                "error",
                "$.runtime_execution.producer_commit",
                "Runtime commit values do not all match the detached pinned commit.",
                expected=expected_commit,
                run=run.producer_commit,
                record=(record.owner_commit if isinstance(record, ExecutionRecord) else None),
            )
        )

    tool_binding = bool(
        refs["expected_tool"]
        and refs["expected_tool"] == refs["run_tool"] == record_tool
    )
    tool_path: Path | None = None
    if tool_binding:
        try:
            tool_path = resolve_repo_relative_file(root, refs["expected_tool"] or "")
        except RepoPathError as exc:
            diagnostics.append(_path_diag(exc, "$.runtime_execution.producer_tool_ref"))
            tool_binding = False
    if not tool_binding:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_TOOL_MISMATCH",
                "error",
                "$.runtime_execution.producer_tool_ref",
                "Runtime tool reference is not exactly bound across request, result, record, and worktree.",
                expected=refs["expected_tool"],
                run=refs["run_tool"],
                record=record_tool,
            )
        )

    cwd_binding = bool(
        refs["expected_cwd"]
        and refs["expected_cwd"] == refs["run_cwd"] == record_cwd
    )
    cwd_path: Path | None = None
    if cwd_binding:
        try:
            cwd_path = resolve_repo_relative_directory(root, refs["expected_cwd"] or ".")
            record_cwd_absolute = (
                Path(record.working_directory).resolve(strict=True)
                if isinstance(record, ExecutionRecord)
                else None
            )
            if record_cwd_absolute != cwd_path:
                cwd_binding = False
        except (RepoPathError, OSError, TypeError):
            cwd_binding = False
    if not cwd_binding:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_WORKING_DIRECTORY_MISMATCH",
                "error",
                "$.runtime_execution.working_directory_ref",
                "Runtime working directory is not exactly bound to the subprocess working directory.",
                expected=refs["expected_cwd"],
                run=refs["run_cwd"],
                record=record_cwd,
                record_absolute=(
                    record.working_directory if isinstance(record, ExecutionRecord) else None
                ),
            )
        )

    process_valid = bool(
        isinstance(record, ExecutionRecord)
        and record.tool_kind == "adapter"
        and record.exit_code == 0
        and record.failure_code is None
        and tool_path is not None
        and isinstance(record.command, list)
        and _command_invokes_tool(record.command, tool_path)
    )
    if not process_valid:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_EXECUTION_FAILED",
                "insufficient_evidence",
                "$.runtime_execution.execution_record",
                "Viewport producer process or exact entrypoint binding did not complete successfully.",
                exit_code=(record.exit_code if isinstance(record, ExecutionRecord) else None),
                failure_code=(
                    record.failure_code if isinstance(record, ExecutionRecord) else None
                ),
            )
        )

    output_binding = bool(refs["run_output"] and refs["run_output"] == record_output)
    if not output_binding:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_OUTPUT_REF_BINDING_MISMATCH",
                "insufficient_evidence",
                "$.runtime_execution.artifact_ref",
                "ExecutionRecord.output_ref must exactly equal the runtime artifact reference.",
                reason=OUTPUT_REF_BINDING_MISMATCH_REASON,
                run=refs["run_output"],
                record=record_output,
            )
        )

    artifact_path: Path | None = None
    verified_artifact_ref: str | None = None
    value: Any = None
    actual_sha256: str | None = None
    raw: bytes | None = None
    source_resolved = False
    if refs["run_output"]:
        try:
            artifact_path = resolve_repo_relative_file(root, refs["run_output"])
            verified_artifact_ref = repo_relative_ref(artifact_path, root)
            if _observed_artifact_path is not None:
                if _observed_artifact_path.resolve(strict=True) != artifact_path:
                    raise RepoPathError(
                        "PG.RUNTIME.OBSERVED_ARTIFACT_PATH_MISMATCH",
                        str(_observed_artifact_path),
                        "Observed artifact path does not match the exact runtime output reference.",
                    )
            raw = (
                bytes(_observed_artifact_bytes)
                if _observed_artifact_bytes is not None
                else artifact_path.read_bytes()
            )
            actual_sha256 = hashlib.sha256(raw).hexdigest()
            value = json.loads(raw.decode("utf-8"))
            source_resolved = True
        except RepoPathError as exc:
            diagnostics.append(_path_diag(exc, "$.runtime_execution.artifact_ref"))
        except json.JSONDecodeError:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_JSON_INVALID",
                    "error",
                    "$.runtime_execution.artifact_ref",
                    "Viewport runtime artifact is not valid JSON.",
                )
            )
        except (OSError, UnicodeDecodeError) as exc:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_ARTIFACT_READ_FAILED",
                    "insufficient_evidence",
                    "$.runtime_execution.artifact_ref",
                    "Viewport runtime artifact bytes could not be read.",
                    error_type=type(exc).__name__,
                )
            )

    output_binding = output_binding and verified_artifact_ref == refs["run_output"]
    record_output_hash = record.output_hash if isinstance(record, ExecutionRecord) else None
    hash_verified = bool(
        actual_sha256
        and actual_sha256 == run.artifact_sha256 == record_output_hash
    )
    if source_resolved and not hash_verified:
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_OUTPUT_HASH_BINDING_MISMATCH",
                "error",
                "$.runtime_execution.artifact_sha256",
                "Runtime output bytes are not exactly bound across artifact, run, record, and verification.",
                actual=actual_sha256,
                run=run.artifact_sha256,
                record=record_output_hash,
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
                "Viewport runtime capture must be completed by the producer result.",
                actual=run.capture_status,
            )
        )
    if run.validation_status != "accepted":
        diagnostics.append(
            _diag(
                "PG.EVIDENCE.RUNTIME_VALIDATION_NOT_ACCEPTED",
                "insufficient_evidence",
                "$.runtime_execution.validation_status",
                "Viewport runtime validation must be explicitly accepted by the official result contract.",
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
                "$.runtime_execution.artifact_ref",
                "Observed viewport runtime artifact contains a synthetic conflict.",
                indicators=indicators,
            )
        )

    exact_context = all(
        (
            identity_valid,
            tracked_clean,
            declared_worktree_valid,
            repository_binding,
            commit_binding,
            tool_binding,
            cwd_binding,
            process_valid,
            output_binding,
        )
    )
    positive = all(
        (
            exact_context,
            source_resolved,
            hash_verified,
            schema_valid,
            claim_binding_valid,
            subject_binding_valid,
            run.capture_status == "completed",
            run.validation_status == "accepted",
            not synthetic_conflict,
            not _has_blocking(diagnostics),
        )
    )
    reason = None
    if not positive:
        reason = (
            OUTPUT_REF_BINDING_MISMATCH_REASON
            if any(
                item.get("code")
                == "PG.EVIDENCE.RUNTIME_OUTPUT_REF_BINDING_MISMATCH"
                for item in diagnostics
            )
            else "official_runtime_execution_not_verified"
        )

    snapshot: VerifiedArtifactSnapshot | None = None
    if positive and raw is not None and verified_artifact_ref is not None:
        try:
            snapshot = VerifiedArtifactSnapshot.from_verified_bytes(
                artifact_ref=verified_artifact_ref,
                exact_bytes=raw,
            )
            if snapshot.sha256 != actual_sha256:
                raise ValueError("Snapshot hash differs from verification hash.")
        except ValueError as exc:
            diagnostics.append(
                _diag(
                    "PG.EVIDENCE.RUNTIME_SNAPSHOT_INVARIANT_FAILED",
                    "error",
                    "$.runtime_execution.artifact_snapshot",
                    "Verified artifact snapshot could not preserve the exact verified bytes.",
                    error_type=type(exc).__name__,
                )
            )
            positive = False
            reason = "runtime_snapshot_invariant_failed"
            snapshot = None

    verification = ViewportRunVerification(
        classification=(
            "synthetic"
            if synthetic_conflict
            else ("real_verified" if positive else "insufficient_evidence")
        ),
        positive_proof_verified=positive,
        source_resolved=source_resolved,
        hash_verified=hash_verified,
        schema_valid=schema_valid,
        claim_binding_valid=claim_binding_valid,
        subject_binding_valid=subject_binding_valid,
        synthetic_conflict=synthetic_conflict,
        actual_sha256=actual_sha256,
        reason=reason,
        verified_repository=expected_repository if repository_binding else None,
        verified_commit=expected_commit if commit_binding else None,
        verified_tool_ref=refs["expected_tool"] if tool_binding else None,
        verified_working_directory_ref=(
            refs["expected_cwd"] if cwd_binding else None
        ),
        verified_artifact_ref=verified_artifact_ref if output_binding else None,
        ephemeral_artifact_path=(
            artifact_path if output_binding and source_resolved else None
        ),
        artifact_snapshot=snapshot,
        execution_record_digest=(
            record.execution_record_hash
            if positive and isinstance(record, ExecutionRecord)
            else None
        ),
        verified_subject_ref=expected_subject_ref if positive else None,
        verified_viewport=expected_viewport if positive else None,
        verified_run_id=run.run_id if positive else None,
        value=value,
        derived_receipt=None,
        diagnostics=tuple(diagnostics),
    )
    if positive:
        verification = replace(
            verification,
            derived_receipt=build_runtime_evidence_receipt(verification=verification),
        )
    return verification


def build_runtime_evidence_receipt(
    *,
    verification: ViewportRunVerification,
) -> dict[str, Any]:
    """Build deterministic audit metadata from a verified snapshot only."""

    snapshot = verification.artifact_snapshot
    if (
        not verification.positive_proof_verified
        or verification.classification != "real_verified"
        or snapshot is None
    ):
        raise ValueError(
            "A successful exact-bound verification with an artifact snapshot is required before receipt derivation."
        )
    snapshot.validate_integrity()
    mandatory = {
        "producer_repository": verification.verified_repository,
        "producer_commit": verification.verified_commit,
        "producer_tool": verification.verified_tool_ref,
        "working_directory_ref": verification.verified_working_directory_ref,
        "execution_record_digest": verification.execution_record_digest,
        "subject_ref": verification.verified_subject_ref,
        "viewport": verification.verified_viewport,
        "run_id": verification.verified_run_id,
    }
    missing = sorted(
        key
        for key, value in mandatory.items()
        if not isinstance(value, str) or not value
    )
    if missing:
        raise ValueError(f"Verified receipt fields are missing: {', '.join(missing)}")
    if verification.actual_sha256 != snapshot.sha256:
        raise ValueError("Verified receipt hash does not match the artifact snapshot.")
    return {
        "schema": RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
        "evidence_type": "viewport_artifact",
        "run_id": mandatory["run_id"],
        "producer_repository": mandatory["producer_repository"],
        "producer_commit": mandatory["producer_commit"],
        "producer_tool": mandatory["producer_tool"],
        "working_directory_ref": mandatory["working_directory_ref"],
        "execution_status": "accepted",
        "execution_record_digest": mandatory["execution_record_digest"],
        "subject_ref": mandatory["subject_ref"],
        "viewport": mandatory["viewport"],
        "artifact_ref": snapshot.artifact_ref,
        "artifact_sha256": snapshot.sha256,
        "artifact_byte_length": snapshot.byte_length,
        "capture_status": "completed",
        "validation_status": "accepted",
    }


def inspect_adjacent_runtime_receipt(
    *,
    repository_root: str | Path | None,
    artifact_ref: str | None,
    receipt_ref: str | None = None,
) -> tuple[Path | None, Any, list[dict[str, Any]]]:
    """Read a stored receipt for diagnostics without granting authority."""

    if repository_root is None or not artifact_ref:
        return None, None, []
    try:
        normalized_artifact = normalize_repo_relative_ref(artifact_ref)
        raw_ref = receipt_ref or f"{normalized_artifact}.receipt.json"
        normalized_receipt = normalize_repo_relative_ref(raw_ref)
        path = resolve_repo_relative_file(repository_root, normalized_receipt)
    except RepoPathError as exc:
        if exc.code == "PG.RUNTIME.REF_MISSING":
            return None, None, []
        return None, None, [
            _path_diag(exc, "$.runtime_receipt_ref", severity="warning")
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
                receipt_ref=normalized_receipt,
                error_type=type(exc).__name__,
            )
        ]
    schema = value.get("schema") if isinstance(value, dict) else None
    return path, value, [
        _diag(
            "PG.EVIDENCE.RUNTIME_RECEIPT_NON_AUTHORITATIVE",
            "warning",
            "$.runtime_receipt_ref",
            "Stored runtime receipt is diagnostic metadata only; an observed pinned execution is required.",
            receipt_ref=normalized_receipt,
            observed_schema=schema,
            reason=OFFICIAL_RUNTIME_NOT_OBSERVED_REASON,
        )
    ]


def _revoke_for_cleanup_failure(
    verification: ViewportRunVerification,
    cleanup_diagnostics: list[dict[str, Any]],
) -> ViewportRunVerification:
    return replace(
        verification,
        classification="insufficient_evidence",
        positive_proof_verified=False,
        reason="pinned_worktree_cleanup_failed",
        ephemeral_artifact_path=None,
        artifact_snapshot=None,
        execution_record_digest=None,
        verified_subject_ref=None,
        verified_viewport=None,
        verified_run_id=None,
        derived_receipt=None,
        diagnostics=tuple([*verification.diagnostics, *cleanup_diagnostics]),
    )


def _same_repository(actual: Any, expected: str) -> bool:
    return isinstance(actual, str) and actual.lower() == expected.lower()


def _same_commit(actual: Any, expected: str) -> bool:
    return isinstance(actual, str) and actual.lower() == expected.lower()


def _adapter_command(tool: Path, *, subject_ref: str, viewport: str) -> list[str]:
    suffix = tool.suffix.lower()
    args = ["--subject-ref", subject_ref, "--viewport", viewport]
    if suffix == ".py":
        return [sys.executable, str(tool), *args]
    if suffix in {".js", ".mjs", ".cjs"}:
        return ["node", str(tool), *args]
    return [str(tool), *args]


def _runtime_env(root: Path) -> dict[str, str]:
    allowed = {"PATH", "HOME", "SYSTEMROOT", "WINDIR"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update(
        {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": str(root),
        }
    )
    return env


def _command_invokes_tool(command: list[str], expected_tool: Path) -> bool:
    expected = expected_tool.resolve(strict=True)
    for value in command[:2]:
        try:
            if Path(value).resolve(strict=True) == expected:
                return True
        except (OSError, RuntimeError):
            continue
    return False


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
                "$.runtime_execution.artifact_ref",
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


def _normalize_ref(
    raw: Any,
    diagnostics: list[dict[str, Any]],
    path: str,
    *,
    allow_root: bool = False,
) -> str | None:
    try:
        return normalize_repo_relative_ref(raw, allow_root=allow_root)
    except RepoPathError as exc:
        diagnostics.append(_path_diag(exc, path))
        return None


def _path_diag(
    exc: RepoPathError,
    path: str,
    *,
    severity: str = "error",
) -> dict[str, Any]:
    return _diag(exc.code, severity, path, str(exc), raw_ref=exc.raw_ref)


def _identity_diagnostics(identity: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in identity.get("diagnostics", [])
        if isinstance(item, dict)
    ]


def _empty_verification(
    diagnostics: list[dict[str, Any]],
    *,
    reason: str,
) -> ViewportRunVerification:
    return ViewportRunVerification(
        classification="insufficient_evidence",
        positive_proof_verified=False,
        source_resolved=False,
        hash_verified=False,
        schema_valid=False,
        claim_binding_valid=False,
        subject_binding_valid=False,
        synthetic_conflict=False,
        actual_sha256=None,
        reason=reason,
        ephemeral_artifact_path=None,
        artifact_snapshot=None,
        derived_receipt=None,
        diagnostics=tuple(diagnostics),
    )


def _has_blocking(diagnostics: list[dict[str, Any]]) -> bool:
    return any(
        item.get("severity") in {"error", "insufficient_evidence"}
        for item in diagnostics
    )


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
