from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ev4_transition.io.secure_snapshot import JsonInputSnapshot, SnapshotError, validate_json_snapshot

from ev4_transition.producer_integration.facade import execute_producer_handoff, inspect_producer_handoff
from ev4_transition.producer_integration.path_environment import PublicationPaths

from .models import RepoPaths


@dataclass(frozen=True)
class ProducerHandoffRequest:
    source_path: str | None = None
    source_snapshot: JsonInputSnapshot | None = None
    repo_paths: RepoPaths = field(default_factory=RepoPaths)
    output_dir: str | None = None
    output_path: str | None = None
    receipt_path: str | None = None
    schema_root: str = "schemas"
    lock_path: str | None = None
    publication_paths: PublicationPaths | None = None


@dataclass(frozen=True)
class ProducerHandoffResponse:
    status: str
    resolved_transition: str | None
    routing: dict[str, Any]
    diagnostics: list[dict[str, Any]]
    engine_result: dict[str, Any]
    artifact_metadata: dict[str, Any]
    download_paths: list[str]
    user_message_fa: str
    next_action_fa: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_producer_handoff_request(
    source_path: str | None = None,
    *,
    source_snapshot: JsonInputSnapshot | None = None,
    project_gate_repo_path: str | None = ".",
) -> ProducerHandoffResponse:
    try:
        selected_source = _authoritative_source_path(source_path, source_snapshot)
    except SnapshotError as exc:
        return _response(_snapshot_failure(exc))
    result = inspect_producer_handoff(
        selected_source,
        project_gate_repo=project_gate_repo_path or ".",
    )
    return _response(result)


def run_producer_handoff_request(request: ProducerHandoffRequest) -> ProducerHandoffResponse:
    repos = request.repo_paths
    try:
        selected_source = _authoritative_source_path(request.source_path, request.source_snapshot)
    except SnapshotError as exc:
        return _response(_snapshot_failure(exc))
    result = execute_producer_handoff(
        selected_source,
        project_gate_repo=repos.project_gate_repo_path or ".",
        architect_repo=repos.architect_repo_path,
        ce_repo=repos.ce_repo_path,
        builder_repo=repos.builder_repo_path,
        output_dir=request.output_dir,
        output_path=request.output_path,
        receipt_path=request.receipt_path,
        schema_root=request.schema_root,
        lock_path=request.lock_path,
        publication_paths=request.publication_paths,
    )
    return _response(result)


def _authoritative_source_path(
    source_path: str | None,
    snapshot: JsonInputSnapshot | None,
) -> str | None:
    if snapshot is None:
        return source_path
    validated = validate_json_snapshot(snapshot, expected_source_path=source_path)
    return str(validated.path)


def _snapshot_failure(exc: SnapshotError) -> dict[str, Any]:
    severity = "insufficient_evidence" if exc.status == "insufficient_evidence" else "error"
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": exc.status,
        "acquisition_mode": "producer_emitted_gate_artifact",
        "resolved_transition": None,
        "handoff_allowed": False,
        "failure_class": "source_snapshot_failed",
        "diagnostics": [
            {
                "code": exc.code,
                "severity": severity,
                "path": "$.input_snapshot",
                "message": str(exc),
                "details": dict(exc.details),
            }
        ],
    }


def _response(result: dict[str, Any]) -> ProducerHandoffResponse:
    status = str(result.get("status", "invalid"))
    routing = deepcopy(result.get("routing")) if isinstance(result.get("routing"), dict) else {}
    artifacts = deepcopy(result.get("operator_artifacts")) if isinstance(result.get("operator_artifacts"), dict) else {}
    diagnostics = deepcopy(result.get("diagnostics")) if isinstance(result.get("diagnostics"), list) else []
    downloads: list[str] = []

    next_stage = artifacts.get("next_stage") if isinstance(artifacts.get("next_stage"), dict) else {}
    receipt = artifacts.get("receipt") if isinstance(artifacts.get("receipt"), dict) else {}
    if next_stage.get("downloadable") is True and _is_file(next_stage.get("path")):
        downloads.append(str(next_stage["path"]))
    if receipt.get("downloadable") is True and _is_file(receipt.get("path")):
        downloads.append(str(receipt["path"]))

    transition = result.get("resolved_transition")
    accepted = status == "accepted" and result.get("handoff_allowed") is True
    if accepted and transition == "architect-to-ce":
        user_message = "✅ Architect → CE با داده معتبر تشخیص داده شد و خروجی مستقل CE آماده است."
    elif accepted and transition == "ce-to-builder":
        user_message = "✅ CE → Builder با داده معتبر تشخیص داده شد و خروجی مستقل Builder آماده است."
    elif status == "insufficient_evidence":
        user_message = "⚠️ مسیر handoff تشخیص داده شد، اما شواهد یا checkout محلی کافی نیست."
    elif status == "repair_needed":
        user_message = "🛠️ ورودی قابل تشخیص است، اما قبل از handoff نیاز به اصلاح دارد."
    else:
        user_message = "❌ Producer Gate Export یا اجرای handoff نامعتبر است."

    next_action = artifacts.get("next_action_fa") if isinstance(artifacts.get("next_action_fa"), str) else "diagnostics را بررسی کنید."
    return ProducerHandoffResponse(
        status=status,
        resolved_transition=str(transition) if isinstance(transition, str) else None,
        routing=routing,
        diagnostics=diagnostics,
        engine_result=deepcopy(result),
        artifact_metadata=artifacts,
        download_paths=downloads,
        user_message_fa=user_message,
        next_action_fa=next_action,
    )


def _is_file(value: Any) -> bool:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        return False
    try:
        return Path(value).is_file()
    except (OSError, ValueError, RuntimeError):
        return False
