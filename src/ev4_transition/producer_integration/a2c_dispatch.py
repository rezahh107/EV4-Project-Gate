from __future__ import annotations

from pathlib import Path
from typing import Any

from ev4_transition.architect_to_ce import (
    PG_REPO,
    TRANSITION_ID,
    TRANSITION_VERSION,
    TransitionValidatorHooks,
    transition_from_local_paths,
)
from ev4_transition.bundle_validator import ResultValidationError
from ev4_transition.canonical_json import CANONICAL_JSON_VERSION, canonical_sha256
from ev4_transition.external_lock import ARCHITECT_COMMIT, ARCHITECT_REPO, CE_COMMIT, CE_REPO, load_lock, lock_file_hash
from ev4_transition.io.safe_publication import (
    PublicationError,
    StagedJson,
    discard_staged_json,
    publish_staged_json,
    resolve_publication_paths,
    stage_canonical_json,
)
from ev4_transition.io.secure_snapshot import JsonInputSnapshot, SnapshotError, verify_snapshot_unchanged
from ev4_transition.presentation.status_mapping import normalize_status
from ev4_transition.runners.records import ToolExecutionOutcome
from ev4_transition.runners.repository_identity import inspect_checkout
from ev4_transition.validator_runner import execute_architect_validator, execute_ce_validator

RECEIPT_SCHEMA_ID = "project-gate-a2c-receipt.v1"


def dispatch_architect_export(
    artifact: dict[str, Any],
    intake_result: dict[str, Any],
    *,
    snapshot: JsonInputSnapshot,
    schema_root: str | Path,
    lock_path: str | Path,
    architect_repo: str | Path,
    ce_repo: str | Path,
    project_gate_repo: str | Path,
    output_path: str | Path,
    receipt_path: str | Path,
) -> dict[str, Any]:
    """Execute the existing A2C authority and publish standalone operator artifacts."""

    identities = {
        "project_gate": inspect_checkout(project_gate_repo, expected_repository=PG_REPO),
        "architect": inspect_checkout(architect_repo, expected_repository=ARCHITECT_REPO, expected_commit=ARCHITECT_COMMIT),
        "ce": inspect_checkout(ce_repo, expected_repository=CE_REPO, expected_commit=CE_COMMIT),
    }
    identity_diagnostics = [
        diagnostic
        for identity in identities.values()
        for diagnostic in identity.get("diagnostics", [])
        if isinstance(diagnostic, dict)
    ]
    if identity_diagnostics:
        status = "invalid" if any(item.get("severity") == "error" for item in identity_diagnostics) else "insufficient_evidence"
        return _base_result(intake_result, status, identity_diagnostics, identities=identities)

    final_bundle = artifact.get("final_stage_bundle")
    if not isinstance(final_bundle, dict):
        return _base_result(
            intake_result,
            "invalid",
            [_diag("PG_A2C_FINAL_STAGE_BUNDLE_MISSING", "error", "$.final_stage_bundle", "The validated Producer Gate Export does not contain an Architect Stage Evidence Bundle.")],
            identities=identities,
        )

    architect_outcome: ToolExecutionOutcome | None = None
    ce_outcome: ToolExecutionOutcome | None = None
    events: list[str] = []

    def _architect(payload: dict[str, Any]):
        nonlocal architect_outcome
        architect_outcome = execute_architect_validator(architect_repo, payload)
        return architect_outcome.diagnostics

    def _ce(payload: dict[str, Any], source_bundle: dict[str, Any]):
        nonlocal ce_outcome
        ce_outcome = execute_ce_validator(ce_repo, payload, source_bundle)
        return ce_outcome.diagnostics

    hooks = TransitionValidatorHooks(architect=_architect, ce=_ce, events=events)
    try:
        transition_result = transition_from_local_paths(
            final_bundle,
            schema_root,
            lock_path,
            architect_repo,
            ce_repo,
            validator_hooks=hooks,
        )
    except ResultValidationError as exc:
        return _base_result(
            intake_result,
            "invalid",
            [_diag("TRANSITION_RESULT_SCHEMA_VALIDATION_FAILED", "error", "$", "The complete A2C transition result failed its Project Gate schema.", error=str(exc))],
            identities=identities,
            architect_outcome=architect_outcome,
            ce_outcome=ce_outcome,
            events=events,
        )

    transition_status = normalize_status(str(transition_result.get("status")))
    diagnostics = list(transition_result.get("diagnostics") or [])
    source_handoff_allowed = bool((artifact.get("handoff") or {}).get("allowed"))
    if transition_status == "accepted" and not source_handoff_allowed:
        transition_status = "insufficient_evidence"
        diagnostics.append(
            _diag(
                "PG_A2C_SOURCE_HANDOFF_NOT_ALLOWED",
                "insufficient_evidence",
                "$.handoff.allowed",
                "The producer export is structurally valid but does not authorize an accepted handoff.",
            )
        )

    target_bundle = transition_result.get("output")
    ce_input = (target_bundle.get("payload") or {}).get("data") if isinstance(target_bundle, dict) else None
    if not isinstance(ce_input, dict):
        return _base_result(
            intake_result,
            transition_status,
            diagnostics,
            identities=identities,
            transition_result=transition_result,
            architect_outcome=architect_outcome,
            ce_outcome=ce_outcome,
            events=events,
        )

    try:
        output, receipt = resolve_publication_paths(
            source_path=snapshot.path,
            output_path=output_path,
            receipt_path=receipt_path,
        )
    except PublicationError as exc:
        diagnostics.append(_publication_diag(exc))
        return _base_result(
            intake_result,
            "invalid",
            diagnostics,
            identities=identities,
            transition_result=transition_result,
            architect_outcome=architect_outcome,
            ce_outcome=ce_outcome,
            events=events,
        )

    handoff_allowed = transition_status == "accepted" and source_handoff_allowed and ce_input.get("intake_status") == "complete"
    lock = load_lock(lock_path)
    receipt_payload = _build_receipt(
        artifact=artifact,
        snapshot=snapshot,
        identities=identities,
        transition_status=transition_status,
        handoff_allowed=handoff_allowed,
        diagnostics=diagnostics,
        ce_input=ce_input,
        output_path=output,
        lock=lock,
        architect_outcome=architect_outcome,
        ce_outcome=ce_outcome,
        events=events,
    )

    staged_output: StagedJson | None = None
    staged_receipt: StagedJson | None = None
    output_publication: dict[str, Any] | None = None
    try:
        staged_output = stage_canonical_json(output, ce_input)
        staged_receipt = stage_canonical_json(receipt, receipt_payload)
        verify_snapshot_unchanged(snapshot)
        output_publication = publish_staged_json(staged_output)
        staged_output = None
        receipt_publication = publish_staged_json(staged_receipt)
        staged_receipt = None
    except (PublicationError, SnapshotError) as exc:
        cleanup_diagnostics: list[dict[str, Any]] = []
        for staged in (staged_output, staged_receipt):
            try:
                discard_staged_json(staged)
            except PublicationError as cleanup_exc:
                cleanup_diagnostics.append(_publication_diag(cleanup_exc))
        diagnostics.append(_publication_diag(exc))
        diagnostics.extend(cleanup_diagnostics)
        result = _base_result(
            intake_result,
            "invalid",
            diagnostics,
            identities=identities,
            transition_result=transition_result,
            architect_outcome=architect_outcome,
            ce_outcome=ce_outcome,
            events=events,
        )
        result["publication"] = {
            "ce_input": output_publication or {"path": str(output), "state": "not_published"},
            "receipt": {"path": str(receipt), "state": "not_published"},
        }
        result["handoff_allowed"] = False
        return result

    result = _base_result(
        intake_result,
        transition_status,
        diagnostics,
        identities=identities,
        transition_result=transition_result,
        architect_outcome=architect_outcome,
        ce_outcome=ce_outcome,
        events=events,
    )
    result.update(
        {
            "handoff_allowed": handoff_allowed,
            "downstream_artifact": {
                "status": "published_verified",
                "schema_id": ce_input.get("schema_id"),
                "path": str(output),
                "canonical_sha256": canonical_sha256(ce_input),
                "sha256_file_bytes": output_publication["sha256_file_bytes"],
            },
            "receipt": {
                "status": "published_verified",
                "schema_id": RECEIPT_SCHEMA_ID,
                "path": str(receipt),
                "receipt_id": receipt_payload["receipt_id"],
                "canonical_sha256": canonical_sha256(receipt_payload),
                "sha256_file_bytes": receipt_publication["sha256_file_bytes"],
            },
            "publication": {"ce_input": output_publication, "receipt": receipt_publication},
        }
    )
    return result


def _build_receipt(
    *,
    artifact: dict[str, Any],
    snapshot: JsonInputSnapshot,
    identities: dict[str, dict[str, Any]],
    transition_status: str,
    handoff_allowed: bool,
    diagnostics: list[dict[str, Any]],
    ce_input: dict[str, Any],
    output_path: Path,
    lock: dict[str, Any],
    architect_outcome: ToolExecutionOutcome | None,
    ce_outcome: ToolExecutionOutcome | None,
    events: list[str],
) -> dict[str, Any]:
    final_bundle = artifact["final_stage_bundle"]
    base: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_ID,
        "transition": {"id": TRANSITION_ID, "version": TRANSITION_VERSION},
        "project_gate": {
            "repository": PG_REPO,
            "commit": identities["project_gate"].get("commit"),
        },
        "source_export": {
            "path": snapshot.path.name,
            "sha256_file_bytes": snapshot.sha256_file_bytes,
            "export_id": artifact.get("export_id"),
            "producer_repository": (artifact.get("producer") or {}).get("repository"),
            "producer_commit": (artifact.get("producer") or {}).get("commit_sha"),
        },
        "source_bundle": {
            "bundle_id": final_bundle.get("bundle_id"),
            "canonical_sha256": canonical_sha256(final_bundle),
        },
        "owner_checkouts": {name: _stable_identity(value) for name, value in sorted(identities.items())},
        "owner_validators": {
            "architect": _outcome_record(architect_outcome),
            "ce": _outcome_record(ce_outcome),
        },
        "external_lock": {
            "schema_version": lock.get("schema_version"),
            "canonicalization": CANONICAL_JSON_VERSION,
            "canonical_sha256": lock_file_hash(lock),
        },
        "transition_status": transition_status,
        "handoff_allowed": handoff_allowed,
        "ce_input": {
            "path": _workspace_relative(output_path),
            "schema_id": ce_input.get("schema_id"),
            "canonical_sha256": canonical_sha256(ce_input),
            "publication_state": "published_verified",
        },
        "diagnostics": sorted(diagnostics, key=lambda item: (item.get("path", "$"), item.get("code", ""))),
        "evidence_classification": "cross_repository_integration",
        "synthetic": bool(final_bundle.get("synthetic")),
        "acquisition_mode": "producer_emitted_gate_artifact",
        "execution_events": list(events),
    }
    base["receipt_id"] = "pg-a2c-receipt-" + canonical_sha256(base)[:24]
    return base


def _stable_identity(identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": identity.get("status"),
        "repository": identity.get("repository"),
        "commit": identity.get("commit"),
    }


def _outcome_record(outcome: ToolExecutionOutcome | None) -> dict[str, Any]:
    if outcome is None:
        return {"status": "not_run", "execution": None}
    record = outcome.execution_record
    return {
        "status": normalize_status(outcome.status),
        "execution": {
            "owner_repository": record.owner_repo,
            "owner_commit": record.owner_commit,
            "validator_path": record.validator_path,
            "exit_code": record.exit_code,
            "timeout_seconds": record.timeout_policy.seconds,
            "stdout_hash": outcome.stdout_hash,
            "stderr_hash": outcome.stderr_hash,
        },
    }


def _workspace_relative(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def _base_result(
    intake_result: dict[str, Any],
    status: str,
    diagnostics: list[dict[str, Any]],
    *,
    identities: dict[str, dict[str, Any]] | None = None,
    transition_result: dict[str, Any] | None = None,
    architect_outcome: ToolExecutionOutcome | None = None,
    ce_outcome: ToolExecutionOutcome | None = None,
    events: list[str] | None = None,
) -> dict[str, Any]:
    result = dict(intake_result)
    result["status"] = status
    result["diagnostics"] = sorted(diagnostics, key=lambda item: (item.get("path", "$"), item.get("code", "")))
    result["repository_identities"] = identities or {}
    result["producer_validation"] = {
        "status": "passed" if architect_outcome and normalize_status(architect_outcome.status) == "accepted" else "not_accepted",
        "official_validator_status": normalize_status(architect_outcome.status) if architect_outcome else "not_run",
        "execution_record": architect_outcome.execution_record.to_dict() if architect_outcome else None,
    }
    result["consumer_validation"] = {
        "status": normalize_status(ce_outcome.status) if ce_outcome else "not_run",
        "execution_record": ce_outcome.execution_record.to_dict() if ce_outcome else None,
    }
    result["transition_events"] = list(events or [])
    result["transition_result"] = transition_result
    result["handoff_allowed"] = False
    result.setdefault("downstream_artifact", {"status": "not_published"})
    result.setdefault("receipt", {"status": "not_published"})
    return result


def _publication_diag(exc: Exception) -> dict[str, Any]:
    code = getattr(exc, "code", "PG_A2C_PUBLICATION_FAILED")
    status = getattr(exc, "status", "invalid")
    severity = "insufficient_evidence" if status == "insufficient_evidence" else "error"
    return _diag(code, severity, "$", str(exc), **getattr(exc, "details", {}))


def _diag(code: str, severity: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, "path": path, "message": message, "details": details, "repair_owner": "Project Gate"}
