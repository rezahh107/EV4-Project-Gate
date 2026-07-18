from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ev4_transition.io.secure_snapshot import JsonInputSnapshot, SnapshotError, capture_json_snapshot

from .intake import intake_producer_export, transition_producer_export

_SUPPORTED_ROUTES: dict[str, dict[str, Any]] = {
    "architect-to-ce": {
        "producer_stage": "architect",
        "target_stage": "ce",
        "required_repo_fields": ("architect_repo", "ce_repo"),
        "required_repository_roles": ("architect", "ce"),
        "output_filename": "ce-input.json",
        "receipt_filename": "project-gate-a2c-receipt.json",
        "lock_filename": "contracts/locks/architect-to-ce-transition.v1.lock.json",
        "next_action_fa": "فایل ce-input.json را به CE بدهید.",
    },
    "ce-to-builder": {
        "producer_stage": "ce",
        "target_stage": "builder",
        "required_repo_fields": ("ce_repo", "builder_repo"),
        "required_repository_roles": ("ce", "builder"),
        "output_filename": "builder-input.json",
        "receipt_filename": "project-gate-c2b-receipt.json",
        "lock_filename": "contracts/locks/ce-to-builder-transition.v1.lock.json",
        "next_action_fa": "فایل builder-input.json را به Builder بدهید.",
    },
}

_ROUTING_FILES = (
    "contracts/producer-adoption/ev4-producer-adoption-set.v1.json",
    "contracts/transition-targets/ev4-transition-targets.v1.json",
)
_PATH_ERRORS = (OSError, ValueError, RuntimeError)


def inspect_producer_handoff(
    source_path: str | Path,
    *,
    project_gate_repo: str | Path = ".",
) -> dict[str, Any]:
    """Validate immutable source bytes and resolve a PG-INT route from contract data."""

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
) -> dict[str, Any]:
    """Reuse the existing A2C/C2B dispatchers through one validated routing facade."""

    root, failure = _project_gate_root(project_gate_repo)
    if failure is not None:
        return _with_operator_artifacts(failure)

    snapshot, inspection = _capture_and_inspect(source_path, root)
    if snapshot is None or inspection.get("status") != "accepted":
        return _with_operator_artifacts(inspection)

    resolved = str(inspection["resolved_transition"])
    route = _SUPPORTED_ROUTES[resolved]
    workspace, diagnostic = _workspace()
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic)

    supplied = {
        "architect_repo": architect_repo,
        "ce_repo": ce_repo,
        "builder_repo": builder_repo,
    }
    normalized: dict[str, Path | None] = dict.fromkeys(supplied)
    diagnostics: list[dict[str, Any]] = []
    for field in route["required_repo_fields"]:
        normalized[field], field_diagnostics = _repository_path(
            field,
            supplied[field],
            workspace=workspace,
        )
        diagnostics.extend(field_diagnostics)
    if diagnostics:
        result = deepcopy(inspection)
        result.update(
            status=_status_from_diagnostics(diagnostics),
            diagnostics=sorted(diagnostics, key=_diagnostic_key),
            handoff_allowed=False,
            failure_class="repository_path_validation_failed",
        )
        return _with_operator_artifacts(result)

    publication_root, diagnostic = _publication_root(output_dir, workspace=workspace)
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic, "publication_failed")

    selected_output, diagnostic = _path(
        output_path,
        base=publication_root,
        path_expr="$.output_path",
        default=route["output_filename"],
    )
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic)

    selected_receipt, diagnostic = _path(
        receipt_path,
        base=publication_root,
        path_expr="$.receipt_path",
        default=route["receipt_filename"],
    )
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic)

    selected_schema_root, diagnostic = _existing_path(
        schema_root,
        base=root,
        path_expr="$.schema_root",
        expected_kind="directory",
        code="PG_INT_SCHEMA_ROOT_INVALID",
        default="schemas",
    )
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic)

    selected_lock, diagnostic = _existing_path(
        lock_path,
        base=root,
        path_expr="$.lock_path",
        expected_kind="file",
        code="PG_INT_LOCK_PATH_INVALID",
        default=route["lock_filename"],
    )
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic)

    join_packet, diagnostic = _existing_path(
        "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json",
        base=root,
        path_expr="$.project_gate_repo.join_evidence_packet",
        expected_kind="file",
        code="PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
    )
    if diagnostic is not None:
        return _operator_failure(inspection, diagnostic, "project_gate_files_unavailable")

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
            output_path=selected_output,
            receipt_path=selected_receipt,
            registry_path=root / _ROUTING_FILES[0],
            targets_path=root / _ROUTING_FILES[1],
            repository_root=root,
        )
    except Exception as exc:
        return _operator_failure(
            inspection,
            _diag(
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
    return _with_operator_artifacts(result)


def required_repository_fields(resolved_transition: str) -> tuple[str, ...]:
    route = _SUPPORTED_ROUTES.get(resolved_transition)
    return tuple(route["required_repo_fields"]) if route else ()


def _project_gate_root(value: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
    workspace, diagnostic = _workspace()
    if diagnostic is not None:
        return None, _empty_failure("invalid", "operator_path_validation_failed", diagnostic)

    root, diagnostic = _path(
        value,
        base=workspace,
        path_expr="$.project_gate_repo",
        default=".",
        resolve=True,
    )
    if diagnostic is not None:
        return None, _empty_failure("invalid", "operator_path_validation_failed", diagnostic)

    try:
        if not root.exists() or not root.is_dir():
            raise NotADirectoryError(str(root))
        root.stat()
        next(root.iterdir(), None)
    except _PATH_ERRORS as exc:
        return None, _empty_failure(
            "invalid",
            "project_gate_repo_invalid",
            _diag(
                "PG_INT_PROJECT_GATE_REPO_INVALID",
                "error",
                "$.project_gate_repo",
                "The Project Gate repository root does not exist, is not a directory, or is inaccessible.",
                project_gate_repo=str(root),
                error_type=type(exc).__name__,
            ),
        )

    for relative in _ROUTING_FILES:
        candidate = root / relative
        try:
            if not candidate.is_file():
                raise FileNotFoundError(relative)
            json.loads(candidate.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
        except Exception as exc:
            return None, _empty_failure(
                "invalid",
                "project_gate_files_unavailable",
                _diag(
                    "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
                    "error",
                    "$.project_gate_repo.routing_files",
                    "A required Project Gate routing file is missing, unreadable, or malformed.",
                    file=relative,
                    error_type=type(exc).__name__,
                ),
            )
    return root, None


def _capture_and_inspect(
    source_path: str | Path,
    project_gate_root: Path,
) -> tuple[JsonInputSnapshot | None, dict[str, Any]]:
    workspace, diagnostic = _workspace()
    if diagnostic is not None:
        return None, _empty_failure("invalid", "operator_path_validation_failed", diagnostic)

    normalized_source, diagnostic = _path(
        source_path,
        base=workspace,
        path_expr="$.source_path",
    )
    if diagnostic is not None:
        return None, _empty_failure("invalid", "source_snapshot_failed", diagnostic)

    try:
        snapshot = capture_json_snapshot(normalized_source)
    except SnapshotError as exc:
        return None, _snapshot_failure(exc)
    except _PATH_ERRORS as exc:
        return None, _empty_failure(
            "invalid",
            "source_snapshot_failed",
            _diag(
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
            registry_path=project_gate_root / _ROUTING_FILES[0],
            targets_path=project_gate_root / _ROUTING_FILES[1],
            repository_root=project_gate_root,
        )
    except Exception as exc:
        failure = _empty_failure(
            "invalid",
            "project_gate_files_unavailable",
            _diag(
                "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
                "error",
                "$.project_gate_repo",
                "Project Gate contract files could not be loaded or validated.",
                error_type=type(exc).__name__,
            ),
        )
        failure["source_snapshot"] = _snapshot_metadata(snapshot)
        return snapshot, failure

    result = deepcopy(intake)
    result["source_snapshot"] = _snapshot_metadata(snapshot)
    resolved = result.get("resolved_transition")
    route = _SUPPORTED_ROUTES.get(str(resolved))
    result["routing"] = _routing_metadata(snapshot.value, result, route)

    if result.get("status") != "accepted":
        result["handoff_allowed"] = False
        return snapshot, result
    if route is None:
        result.update(status="invalid", failure_class="unsupported", handoff_allowed=False)
        result.setdefault("diagnostics", []).append(
            _diag(
                "PG_INT_UNSUPPORTED_TRANSITION",
                "error",
                "$.handoff.target",
                "The validated Producer Gate Export resolves outside S-003 / PG-INT.",
                resolved_transition=resolved,
                supported_transitions=sorted(_SUPPORTED_ROUTES),
            )
        )
        return snapshot, result

    producer = result.get("producer") if isinstance(result.get("producer"), dict) else {}
    observed_stage = producer.get("stage")
    if observed_stage != route["producer_stage"]:
        result.update(status="invalid", failure_class="unsupported", handoff_allowed=False)
        result.setdefault("diagnostics", []).append(
            _diag(
                "PG_INT_PRODUCER_TARGET_MISMATCH",
                "error",
                "$.handoff.target",
                "Producer stage and handoff target do not form a supported transition pair.",
                producer_stage=observed_stage,
                expected_producer_stage=route["producer_stage"],
                resolved_transition=resolved,
            )
        )
    result["diagnostics"] = sorted(result.get("diagnostics", []), key=_diagnostic_key)
    return snapshot, result


def _repository_path(
    field: str,
    value: str | Path | None,
    *,
    workspace: Path,
) -> tuple[Path | None, list[dict[str, Any]]]:
    path_expr = f"$.repository_paths.{field}"
    if value is None or not str(value).strip():
        return None, [
            _diag(
                "PG_INT_REPOSITORY_PATH_REQUIRED",
                "insufficient_evidence",
                path_expr,
                "A required local repository checkout path is missing.",
                field=field,
            )
        ]
    if _looks_like_url(str(value).strip()):
        return None, [
            _diag(
                "PG_INT_GITHUB_URL_REJECTED",
                "error",
                path_expr,
                "A local checkout directory is required; repository URLs are not accepted.",
                field=field,
            )
        ]

    candidate, diagnostic = _path(
        value,
        base=workspace,
        path_expr=path_expr,
        code="PG_INT_REPOSITORY_PATH_UNSAFE",
        message="The required local repository checkout path is invalid or inaccessible.",
    )
    if diagnostic is not None:
        return None, [diagnostic]

    try:
        if not candidate.exists():
            return None, [
                _diag(
                    "PG_INT_REPOSITORY_PATH_NOT_FOUND",
                    "insufficient_evidence",
                    path_expr,
                    "The required local repository checkout does not exist.",
                    field=field,
                )
            ]
        if not candidate.is_dir():
            return None, [
                _diag(
                    "PG_INT_REPOSITORY_PATH_UNSAFE",
                    "error",
                    path_expr,
                    "The required local repository checkout path is not a directory.",
                    field=field,
                    observed_path=str(candidate),
                )
            ]
    except _PATH_ERRORS as exc:
        return None, [
            _diag(
                "PG_INT_REPOSITORY_PATH_UNSAFE",
                "error",
                path_expr,
                "The required local repository checkout path is invalid or inaccessible.",
                field=field,
                error_type=type(exc).__name__,
            )
        ]
    return candidate, []


def _publication_root(
    value: str | Path | None,
    *,
    workspace: Path,
) -> tuple[Path | None, dict[str, Any] | None]:
    if value is None or not str(value).strip():
        try:
            created = Path(tempfile.mkdtemp(prefix=".ev4_pg_int_", dir=workspace)).resolve(strict=True)
        except _PATH_ERRORS as exc:
            return None, _diag(
                "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
                "error",
                "$.output_dir",
                "A unique temporary output directory could not be created inside the publication workspace.",
                workspace=str(workspace),
                error_type=type(exc).__name__,
            )
        return created, None

    candidate, diagnostic = _path(
        value,
        base=workspace,
        path_expr="$.output_dir",
        code="PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
        message="The requested output directory path is invalid or inaccessible.",
        resolve=True,
    )
    if diagnostic is not None:
        return None, diagnostic

    try:
        candidate.relative_to(workspace)
        candidate.mkdir(parents=True, exist_ok=True)
        if not candidate.is_dir():
            raise NotADirectoryError(str(candidate))
    except _PATH_ERRORS as exc:
        return None, _diag(
            "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
            "error",
            "$.output_dir",
            "The requested output directory must be a usable directory inside the current publication workspace.",
            workspace=str(workspace),
            output_dir=str(candidate),
            error_type=type(exc).__name__,
        )
    return candidate, None


def _existing_path(
    value: str | Path | None,
    *,
    base: Path,
    path_expr: str,
    expected_kind: str,
    code: str,
    default: str | Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    candidate, diagnostic = _path(
        value,
        base=base,
        path_expr=path_expr,
        default=default,
    )
    if diagnostic is not None:
        return None, diagnostic
    try:
        valid = candidate.is_dir() if expected_kind == "directory" else candidate.is_file()
    except _PATH_ERRORS as exc:
        return None, _diag(
            code,
            "error",
            path_expr,
            "The required local path is invalid or inaccessible.",
            observed_path=str(candidate),
            expected_kind=expected_kind,
            error_type=type(exc).__name__,
        )
    if not valid:
        return None, _diag(
            code,
            "error",
            path_expr,
            "The required local path is missing or has the wrong type.",
            observed_path=str(candidate),
            expected_kind=expected_kind,
        )
    return candidate, None


def _path(
    value: str | Path | None,
    *,
    base: Path,
    path_expr: str,
    default: str | Path | None = None,
    code: str = "PG_INT_PATH_EXPANSION_FAILED",
    message: str = "The operator-supplied path could not be expanded or resolved safely.",
    resolve: bool = False,
) -> tuple[Path | None, dict[str, Any] | None]:
    selected = value if value is not None and str(value).strip() else default
    if selected is None:
        return None, _diag(code, "error", path_expr, message, error_type="MissingPath")
    try:
        candidate = Path(str(selected).strip()).expanduser()
        if not candidate.is_absolute():
            candidate = base / candidate
        return (candidate.resolve(strict=False) if resolve else candidate), None
    except _PATH_ERRORS as exc:
        return None, _diag(code, "error", path_expr, message, error_type=type(exc).__name__)


def _workspace() -> tuple[Path | None, dict[str, Any] | None]:
    try:
        root = Path.cwd().resolve(strict=True)
        if not root.is_dir():
            raise NotADirectoryError(str(root))
    except _PATH_ERRORS as exc:
        return None, _diag(
            "PG_INT_PATH_EXPANSION_FAILED",
            "error",
            "$.workspace",
            "The current publication workspace is unavailable.",
            error_type=type(exc).__name__,
        )
    return root, None


def _routing_metadata(
    artifact: dict[str, Any],
    result: dict[str, Any],
    route: dict[str, Any] | None,
) -> dict[str, Any]:
    producer = result.get("producer") if isinstance(result.get("producer"), dict) else {}
    handoff = artifact.get("handoff") if isinstance(artifact.get("handoff"), dict) else {}
    return {
        "authority": "validated_producer_gate_export",
        "producer_stage": producer.get("stage"),
        "producer_repository": producer.get("repository"),
        "handoff_target": handoff.get("target"),
        "resolved_transition": result.get("resolved_transition"),
        "target_stage": route.get("target_stage") if route else None,
        "required_repository_roles": list(route.get("required_repository_roles", ())) if route else [],
        "filename_used_for_routing": False,
        "operator_transition_selection_used": False,
    }


def _with_operator_artifacts(result: dict[str, Any]) -> dict[str, Any]:
    route = _SUPPORTED_ROUTES.get(str(result.get("resolved_transition")))
    artifact = result.get("downstream_artifact") if isinstance(result.get("downstream_artifact"), dict) else {}
    receipt = result.get("receipt") if isinstance(result.get("receipt"), dict) else {}
    publication = result.get("publication") if isinstance(result.get("publication"), dict) else {}
    artifact_publication = publication.get("ce_input") or publication.get("builder_input")
    receipt_publication = publication.get("receipt")
    artifact_state = artifact.get("status") or (
        artifact_publication.get("state") if isinstance(artifact_publication, dict) else "not_generated"
    )
    receipt_state = receipt.get("status") or (
        receipt_publication.get("state") if isinstance(receipt_publication, dict) else "not_generated"
    )
    artifact_path = artifact.get("path") or (
        artifact_publication.get("path") if isinstance(artifact_publication, dict) else None
    )
    receipt_path = receipt.get("path") or (
        receipt_publication.get("path") if isinstance(receipt_publication, dict) else None
    )
    accepted = result.get("status") == "accepted" and result.get("handoff_allowed") is True
    result["operator_artifacts"] = {
        "next_stage": {
            "filename": route.get("output_filename") if route else None,
            "path": artifact_path,
            "publication_state": artifact_state,
            "downloadable": bool(accepted and artifact_state == "published_verified"),
            "consumable": bool(accepted and artifact_state == "published_verified"),
        },
        "receipt": {
            "filename": route.get("receipt_filename") if route else None,
            "path": receipt_path,
            "publication_state": receipt_state,
            "downloadable": bool(receipt_state == "published_verified"),
        },
        "next_action_fa": (
            route.get("next_action_fa")
            if route and accepted
            else "diagnostics را بررسی و مانع فعلی را رفع کنید."
        ),
    }
    return result


def _operator_failure(
    inspection: dict[str, Any],
    diagnostic: dict[str, Any],
    failure_class: str = "operator_path_validation_failed",
) -> dict[str, Any]:
    result = deepcopy(inspection)
    result.update(
        status="invalid",
        handoff_allowed=False,
        failure_class=failure_class,
        diagnostics=[diagnostic],
    )
    return _with_operator_artifacts(result)


def _snapshot_failure(exc: SnapshotError) -> dict[str, Any]:
    return _empty_failure(
        exc.status,
        "source_snapshot_failed",
        _diag(
            exc.code,
            "insufficient_evidence" if exc.status == "insufficient_evidence" else "error",
            "$",
            str(exc),
            **exc.details,
        ),
    )


def _empty_failure(
    status: str,
    failure_class: str,
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": status,
        "acquisition_mode": "producer_emitted_gate_artifact",
        "producer": {},
        "resolved_transition": None,
        "handoff_allowed": False,
        "failure_class": failure_class,
        "diagnostics": [diagnostic],
        "routing": {
            "authority": "validated_producer_gate_export",
            "resolved_transition": None,
            "filename_used_for_routing": False,
            "operator_transition_selection_used": False,
            "required_repository_roles": [],
        },
    }


def _snapshot_metadata(snapshot: JsonInputSnapshot) -> dict[str, Any]:
    return {
        "path": str(snapshot.path),
        "filename": snapshot.path.name,
        "sha256_file_bytes": snapshot.sha256_file_bytes,
    }


def _looks_like_url(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("git@", "github.com/", "www.github.com/")):
        return True
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc)


def _status_from_diagnostics(diagnostics: list[dict[str, Any]]) -> str:
    return "invalid" if any(item.get("severity") == "error" for item in diagnostics) else "insufficient_evidence"


def _diagnostic_key(item: Any) -> tuple[str, str]:
    return (item.get("path", "$"), item.get("code", "")) if isinstance(item, dict) else ("$", "")


def _diag(code: str, severity: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
        "details": details,
        "repair_owner": "Project Gate",
    }


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"Non-finite JSON constant is forbidden: {value}")
