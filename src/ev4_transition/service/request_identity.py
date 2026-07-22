from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps
from ev4_transition.io.secure_snapshot import JsonInputSnapshot, obtain_json_snapshot

from .models import GateRequest


@dataclass(frozen=True)
class GateRequestIdentity:
    fingerprint: str
    payload: dict[str, Any]
    source_identity: dict[str, Any]


def build_gate_request_identity(request: GateRequest) -> GateRequestIdentity:
    """Build a deterministic identity for every dispatch-affecting request value.

    Producer file identity is captured through the same immutable snapshot authority
    used by runtime. This function is read-only and creates no output directories.
    """

    source_identity = _source_identity(request)
    payload = {
        "schema_version": "ev4-gate-request-identity.v1",
        "transition_choice": str(request.transition_choice),
        "acquisition_mode": str(request.acquisition_mode),
        "source": source_identity,
        "repository_paths": _repository_paths(request),
        "schema_root": _path_text(request.schema_root),
        "lock_path": _path_text(request.lock_path),
        "output_dir": _path_text(request.output_dir),
        "output_path": _path_text(request.output_path),
        "receipt_path": _path_text(request.receipt_path),
        "required_evidence_ids": list(request.required_evidence_ids),
        "timeout_seconds": request.timeout_seconds,
        "require_real_evidence": request.require_real_evidence,
        "preflight_mode": request.preflight_mode,
    }
    encoded = canonical_dumps(payload).encode("utf-8")
    return GateRequestIdentity(hashlib.sha256(encoded).hexdigest(), payload, source_identity)


def _source_identity(request: GateRequest) -> dict[str, Any]:
    if request.acquisition_mode == "producer_emitted_gate_artifact":
        snapshot = obtain_json_snapshot(
            source_path=request.input_json_path,
            snapshot=request.input_snapshot,
        )
        return _snapshot_identity(snapshot)
    if request.input_json_text is not None:
        content = request.input_json_text.encode("utf-8")
        return {
            "kind": "json_text",
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    if request.input_data is not None:
        content = canonical_dumps(request.input_data).encode("utf-8")
        return {
            "kind": "input_data",
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    if request.input_json_path:
        path = Path(request.input_json_path).expanduser().resolve(strict=False)
        content = path.read_bytes()
        return {
            "kind": "json_file",
            "path": str(path),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    return {"kind": "missing"}


def _snapshot_identity(snapshot: JsonInputSnapshot) -> dict[str, Any]:
    return {
        "kind": "producer_file_snapshot",
        "path": str(snapshot.path),
        "sha256": snapshot.sha256_file_bytes,
        "bytes": snapshot.size,
        "device": snapshot.device,
        "inode": snapshot.inode,
        "mtime_ns": snapshot.mtime_ns,
    }


def _repository_paths(request: GateRequest) -> dict[str, str | None]:
    from .models import RepoPaths

    repos = request.repo_paths or RepoPaths()
    return {
        "project_gate_repo_path": _path_text(repos.project_gate_repo_path),
        "architect_repo_path": _path_text(repos.architect_repo_path),
        "ce_repo_path": _path_text(repos.ce_repo_path),
        "builder_repo_path": _path_text(repos.builder_repo_path),
        "responsive_repo_path": _path_text(repos.responsive_repo_path),
        "kernel_repo_path": _path_text(repos.kernel_repo_path),
    }


def _path_text(value: str | Path | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip()
    try:
        return str(Path(raw).expanduser().resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
        return raw
