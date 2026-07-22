from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ev4_transition.io.secure_snapshot import JsonInputSnapshot, SnapshotError, capture_json_snapshot

from .. import _legacy_facade as _legacy
from ..path_environment import (
    PublicationPathError,
    PublicationPaths,
    prepare_publication_paths,
    validate_project_gate_root,
    validate_repository_checkout,
)

# Keep intake and transition functions patchable for compatibility tests and callers.
intake_producer_export = _legacy.intake_producer_export
transition_producer_export = _legacy.transition_producer_export
required_repository_fields = _legacy.required_repository_fields


def inspect_producer_handoff(
    source_path: str | Path,
    *,
    project_gate_repo: str | Path = ".",
) -> dict[str, Any]:
    root, failure = _project_gate_root(project_gate_repo)
    if failure is not None:
        return failure
    _, result = _capture_and_inspect(source_path, root)
    return result


def execute_producer_handoff(
    source_path: str | Path,
    *,
    project_gate_repo: str | Path = ".",
    architect_repo: str | Path | None = None,
    ce_repo: str | Path | None = None,
    builder_repo: str | Path | None = None,
    output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    schema_root: str | Path = "schemas",
    lock_path: str | Path | None = None,
    publication_paths: PublicationPaths | None = None,
) -> dict[str, Any]:
    """Execute one producer-emitted lifecycle with one publication-path authority."""

    root, failure = _project_gate_root(project_gate_repo)
    if failure is not None:
        return _legacy._with_operator_artifacts(failure)

    snapshot, inspection = _capture_and_inspect(source_path, root)
    if snapshot is None or inspection.get("status") != "accepted":
        return _legacy._with_operator_artifacts(inspection)

    resolved = str(inspection["resolved_transition"])
    route = _legacy._SUPPORTED_ROUTES[resolved]
    workspace, diagnostic = _legacy._workspace()
    if diagnostic is not None:
        return _legacy._operator_failure(inspection, diagnostic)

    supplied = {
        "architect_repo": architect_repo,
        "ce_repo": ce_repo,
        "builder_repo": builder_repo,
    }
    normalized: dict[str, Path | None] = dict.fromkeys(supplied)
    diagnostics: list[dict[str, Any]] = []
    for field in route["required_repo_fields"]:
        normalized[field], field_diagnostics = validate_repository_checkout(
            field,
            supplied[field],
            workspace=workspace,
        )
        diagnostics.extend(field_diagnostics)
    if diagnostics:
        result = deepcopy(inspection)
        result.update(
            status=_legacy._status_from_diagnostics(diagnostics),
            diagnostics=sorted(diagnostics, key=_legacy._diagnostic_key),
            handoff_allowed=False,
            failure_class="repository_path_validation_failed",
        )
        return _legacy._with_operator_artifacts(result)

    selected_schema_root, diagnostic = _legacy._existing_path(
        schema_root,
        base=root,
        path_expr="$.schema_root",
        expected_kind="directory",
        code="PG_INT_SCHEMA_ROOT_INVALID",
        default="schemas",
    )
    if diagnostic is not None:
        return _legacy._operator_failure(inspection, diagnostic)

    selected_lock, diagnostic = _legacy._existing_path(
        lock_path,
        base=root,
        path_expr="$.lock_path",
        expected_kind="file",
        code="PG_INT_LOCK_PATH_INVALID",
        default=route["lock_filename"],
    )
    if diagnostic is not None:
        return _legacy._operator_failure(inspection, diagnostic)

    join_packet, diagnostic = _legacy._existing_path(
        "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json",
        base=root,
        path_expr="$.project_gate_repo.join_evidence_packet",
        expected_kind="file",
        code="PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
    )
    if diagnostic is not None:
        return _legacy._operator_failure(inspection, diagnostic, "project_gate_files_unavailable")

    try:
        selected_publication_paths = publication_paths or prepare_publication_paths(
            output_dir,
            output_filename=route["output_filename"],
            receipt_filename=route["receipt_filename"],
            output_path=output_path,
            receipt_path=receipt_path,
            workspace=workspace,
        )
    except PublicationPathError as exc:
        return _legacy._operator_failure(inspection, exc.diagnostic, "publication_failed")

    try:
        result = transition_producer_export(
            resolved,
            snapshot.value,
            join_packet_path=join_packet,
            snapshot=snapshot,
            schema_root=selected_schema_root,
            lock_path=selected_lock,
            architect_repo=normalized["architect_repo"],
            ce_repo=normalized["ce_repo"],
            builder_repo=normalized["builder_repo"],
            project_gate_repo=root,
            output_path=selected_publication_paths.downstream_artifact,
            receipt_path=selected_publication_paths.receipt,
            registry_path=root / _legacy._ROUTING_FILES[0],
            targets_path=root / _legacy._ROUTING_FILES[1],
            repository_root=root,
        )
    except Exception as exc:
        return _legacy._operator_failure(
            inspection,
            _legacy._diag(
                "PG_INT_EXECUTION_FAILED",
                "error",
                "$",
                "The handoff execution boundary rejected an unavailable or malformed local dependency.",
                error_type=type(exc).__name__,
            ),
            "execution_boundary_failed",
        )

    result["routing"] = deepcopy(inspection["routing"])
    result["source_snapshot"] = deepcopy(inspection["source_snapshot"])
    result["publication_paths"] = {
        "output_root": str(selected_publication_paths.output_root),
        "execution_directory": str(selected_publication_paths.execution_directory),
        "downstream_artifact": str(selected_publication_paths.downstream_artifact),
        "receipt": str(selected_publication_paths.receipt),
        "result": str(selected_publication_paths.result),
        "report_markdown": str(selected_publication_paths.report_markdown),
        "report_html": str(selected_publication_paths.report_html),
    }
    return _legacy._with_operator_artifacts(result)


def _capture_and_inspect(
    source_path: str | Path,
    project_gate_root: Path,
) -> tuple[JsonInputSnapshot | None, dict[str, Any]]:
    workspace, diagnostic = _legacy._workspace()
    if diagnostic is not None:
        return None, _legacy._empty_failure("invalid", "operator_path_validation_failed", diagnostic)

    normalized_source, diagnostic = _legacy._path(
        source_path,
        base=workspace,
        path_expr="$.source_path",
    )
    if diagnostic is not None:
        return None, _legacy._empty_failure("invalid", "source_snapshot_failed", diagnostic)

    try:
        snapshot = capture_json_snapshot(normalized_source)
    except SnapshotError as exc:
        return None, _legacy._snapshot_failure(exc)
    except _legacy._PATH_ERRORS as exc:
        return None, _legacy._empty_failure(
            "invalid",
            "source_snapshot_failed",
            _legacy._diag(
                "PG_INT_PATH_EXPANSION_FAILED",
                "error",
                "$.source_path",
                "The Producer Gate Export path could not be inspected safely.",
                error_type=type(exc).__name__,
            ),
        )

    try:
        intake = intake_producer_export(
            snapshot.value,
            registry_path=project_gate_root / _legacy._ROUTING_FILES[0],
            targets_path=project_gate_root / _legacy._ROUTING_FILES[1],
            repository_root=project_gate_root,
        )
    except Exception as exc:
        failure = _legacy._empty_failure(
            "invalid",
            "project_gate_files_unavailable",
            _legacy._diag(
                "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
                "error",
                "$.project_gate_repo",
                "Project Gate contract files could not be loaded or validated.",
                error_type=type(exc).__name__,
            ),
        )
        failure["source_snapshot"] = _legacy._snapshot_metadata(snapshot)
        return snapshot, failure

    result = deepcopy(intake)
    result["source_snapshot"] = _legacy._snapshot_metadata(snapshot)
    resolved = result.get("resolved_transition")
    route = _legacy._SUPPORTED_ROUTES.get(str(resolved))
    result["routing"] = _legacy._routing_metadata(snapshot.value, result, route)
    if result.get("status") != "accepted":
        result["handoff_allowed"] = False
        return snapshot, result
    if route is None:
        result.update(status="invalid", failure_class="unsupported", handoff_allowed=False)
        result.setdefault("diagnostics", []).append(
            _legacy._diag(
                "PG_INT_UNSUPPORTED_TRANSITION",
                "error",
                "$.handoff.target",
                "The validated Producer Gate Export resolves outside S-003 / PG-INT.",
                resolved_transition=resolved,
                supported_transitions=sorted(_legacy._SUPPORTED_ROUTES),
            )
        )
        return snapshot, result

    producer = result.get("producer") if isinstance(result.get("producer"), dict) else {}
    observed_stage = producer.get("stage")
    if observed_stage != route["producer_stage"]:
        result.update(status="invalid", failure_class="unsupported", handoff_allowed=False)
        result.setdefault("diagnostics", []).append(
            _legacy._diag(
                "PG_INT_PRODUCER_TARGET_MISMATCH",
                "error",
                "$.handoff.target",
                "Producer stage and handoff target do not form a supported transition pair.",
                producer_stage=observed_stage,
                expected_producer_stage=route["producer_stage"],
                resolved_transition=resolved,
            )
        )
    result["diagnostics"] = sorted(result.get("diagnostics", []), key=_legacy._diagnostic_key)
    return snapshot, result


def _project_gate_root(value: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
    root, diagnostics = validate_project_gate_root(
        value,
        required_files=_legacy._ROUTING_FILES,
    )
    if diagnostics:
        diagnostic = diagnostics[0]
        return None, _legacy._empty_failure(
            "invalid" if diagnostic.get("severity") == "error" else "insufficient_evidence",
            (
                "project_gate_files_unavailable"
                if diagnostic.get("code") == "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE"
                else "project_gate_repo_invalid"
            ),
            diagnostic,
        )
    return root, None


__all__ = [
    "execute_producer_handoff",
    "intake_producer_export",
    "inspect_producer_handoff",
    "required_repository_fields",
    "transition_producer_export",
]
