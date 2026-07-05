from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SECRET_KEY_PATTERN = re.compile(r"(secret|token|password|api[_-]?key|credential)", re.IGNORECASE)
ENV_ASSIGNMENT_PATTERN = re.compile(r"\b[A-Z_][A-Z0-9_]{1,}=")
RAW_FORBIDDEN_KEYS = {"stdout", "stderr", "env", "environment", "raw_env", "raw_environment"}


class ProgressSanitizationError(ValueError):
    """Progress events must be safe runtime/UI metadata, not raw execution logs."""


@dataclass(frozen=True)
class ProgressEvent:
    event_type: str
    message: str
    status: str
    repo_path: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {"event_type": self.event_type, "message": self.message, "status": self.status, "details": dict(self.details)}
        if self.repo_path is not None:
            payload["repo_path"] = self.repo_path
        return payload


def sanitize_progress_event(
    event: ProgressEvent | dict[str, Any],
    *,
    repo_root: str | Path | None = None,
    allow_absolute_paths: bool = False,
) -> dict[str, Any]:
    payload = event.to_dict() if isinstance(event, ProgressEvent) else dict(event)
    _reject_forbidden_content(payload)
    if "repo_path" in payload and payload["repo_path"] is not None:
        payload["repo_path"] = _sanitize_path(str(payload["repo_path"]), repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
    if "details" in payload and isinstance(payload["details"], dict):
        payload["details"] = _sanitize_details(payload["details"], repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
    return payload


def emit_progress_event(sink: list[dict[str, Any]] | None, event: ProgressEvent | dict[str, Any], *, repo_root: str | Path | None = None) -> None:
    if sink is not None:
        sink.append(sanitize_progress_event(event, repo_root=repo_root))


def canonical_result_hash_without_progress(result: dict[str, Any]) -> str:
    from ev4_transition.canonical_json import canonical_sha256

    filtered = {key: value for key, value in result.items() if key not in {"progress", "progress_events", "runtime_progress"}}
    return canonical_sha256(filtered)


def _sanitize_details(details: dict[str, Any], *, repo_root: str | Path | None, allow_absolute_paths: bool) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in details.items():
        _reject_key_value(key, value)
        if key.endswith("_path") and isinstance(value, str):
            sanitized[key] = _sanitize_path(value, repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
        else:
            sanitized[key] = _sanitize_value(value, repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
    return sanitized


def _sanitize_value(value: Any, *, repo_root: str | Path | None, allow_absolute_paths: bool) -> Any:
    if isinstance(value, dict):
        return _sanitize_details(value, repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
    if isinstance(value, list):
        return [_sanitize_value(item, repo_root=repo_root, allow_absolute_paths=allow_absolute_paths) for item in value]
    if isinstance(value, str):
        if ENV_ASSIGNMENT_PATTERN.search(value):
            raise ProgressSanitizationError("progress event must not contain raw environment variables")
        if _looks_absolute(value):
            return _sanitize_path(value, repo_root=repo_root, allow_absolute_paths=allow_absolute_paths)
    return value


def _reject_forbidden_content(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        _reject_key_value(key, value)
        if isinstance(value, dict):
            _reject_forbidden_content(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _reject_forbidden_content(item)
                else:
                    _reject_key_value(key, item)


def _reject_key_value(key: str, value: Any) -> None:
    if key in RAW_FORBIDDEN_KEYS:
        raise ProgressSanitizationError(f"progress event must not contain raw {key}")
    if SECRET_KEY_PATTERN.search(key):
        raise ProgressSanitizationError("progress event key looks secret-bearing")
    if isinstance(value, str):
        if SECRET_KEY_PATTERN.search(value):
            raise ProgressSanitizationError("progress event value looks secret-bearing")
        if ENV_ASSIGNMENT_PATTERN.search(value):
            raise ProgressSanitizationError("progress event must not contain raw environment variables")


def _sanitize_path(value: str, *, repo_root: str | Path | None, allow_absolute_paths: bool) -> str:
    if not _looks_absolute(value):
        return value.replace("\\", "/")
    if allow_absolute_paths:
        return value
    if repo_root is not None:
        root = Path(repo_root).resolve()
        candidate = Path(value).resolve()
        try:
            return candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise ProgressSanitizationError("absolute path is outside repo_root") from exc
    raise ProgressSanitizationError("progress event must use repo-relative paths by default")


def _looks_absolute(value: str) -> bool:
    return os.path.isabs(value) or re.match(r"^[A-Za-z]:[\\/]", value) is not None
