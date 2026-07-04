from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..diagnostics import Diagnostic, diagnostic, sort_diagnostics

LOCK_MANIFEST_SCHEMA_VERSION = "lock-manifest.v1"
LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION = "external-contract-lock.v1"
KNOWN_LOCK_SCHEMA_VERSIONS = {LOCK_MANIFEST_SCHEMA_VERSION, LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION}

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_COMMIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_TOP_KEYS = frozenset({"schema_version", "transition_id", "files"})
_FILE_KEYS = frozenset({"role", "repository", "accepted_commit", "path", "contract_or_schema_id", "sha256_file_bytes", "size_bytes"})


class LockManifestValidationError(ValueError):
    """Raised when a lock manifest cannot be interpreted structurally."""


@dataclass(frozen=True)
class LockManifestOptions:
    allow_legacy_external_lock: bool = True


def _unknown_fields(value: dict[str, Any], allowed: frozenset[str], path: str) -> list[Diagnostic]:
    return [
        diagnostic("PG_LOCK_UNKNOWN_FIELD", "error", "Lock manifest field is not allowed by schema.", f"{path}.{key}", field=key)
        for key in sorted(set(value) - allowed)
    ]


def validate_lock_manifest(lock: Any, options: LockManifestOptions | None = None) -> list[Diagnostic]:
    """Validate Project Gate-owned lock manifest carrier structure."""

    opts = options or LockManifestOptions()
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG_LOCK_NOT_OBJECT", "error", "Lock manifest must be a JSON object.", "$")]

    diagnostics.extend(_unknown_fields(lock, _TOP_KEYS, "$"))

    version = lock.get("schema_version")
    if version is None:
        diagnostics.append(diagnostic("PG_LOCK_SCHEMA_VERSION_MISSING", "error", "Lock manifest schema_version is required.", "$.schema_version"))
    elif version not in KNOWN_LOCK_SCHEMA_VERSIONS or (version == LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION and not opts.allow_legacy_external_lock):
        diagnostics.append(diagnostic("PG_LOCK_SCHEMA_VERSION_UNKNOWN", "error", "Lock manifest schema_version is not supported by this Project Gate core.", "$.schema_version", actual=version, supported=sorted(KNOWN_LOCK_SCHEMA_VERSIONS)))

    transition_id = lock.get("transition_id")
    if not isinstance(transition_id, str) or not transition_id:
        diagnostics.append(diagnostic("PG_LOCK_TRANSITION_ID_INVALID", "error", "Lock manifest transition_id must be a non-empty string.", "$.transition_id"))

    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG_LOCK_FILES_NOT_ARRAY", "error", "Lock manifest files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    if not files:
        diagnostics.append(diagnostic("PG_LOCK_FILES_EMPTY", "error", "Lock manifest files must contain at least one pinned file entry.", "$.files"))
        return sort_diagnostics(diagnostics)

    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG_LOCK_ENTRY_NOT_OBJECT", "error", "Lock manifest file entry must be an object.", path))
            continue

        diagnostics.extend(_unknown_fields(item, _FILE_KEYS, path))

        role = item.get("role")
        if not isinstance(role, str) or not role:
            diagnostics.append(diagnostic("PG_LOCK_ROLE_INVALID", "error", "Lock manifest role must be a non-empty string.", f"{path}.role"))
        elif role in seen:
            diagnostics.append(diagnostic("PG_LOCK_ROLE_DUPLICATE", "error", "Lock manifest contains a duplicate role.", f"{path}.role", role=role))
        else:
            seen.add(role)

        repository = item.get("repository")
        if not isinstance(repository, str) or not repository:
            diagnostics.append(diagnostic("PG_LOCK_FIELD_INVALID", "error", "Lock manifest entry field must be a non-empty string.", f"{path}.repository", field="repository"))
        elif not _REPOSITORY_RE.fullmatch(repository):
            diagnostics.append(diagnostic("PG_LOCK_REPOSITORY_INVALID", "error", "Lock manifest repository must match owner/repo.", f"{path}.repository", actual=repository))

        accepted_commit = item.get("accepted_commit")
        if not isinstance(accepted_commit, str) or not accepted_commit:
            diagnostics.append(diagnostic("PG_LOCK_FIELD_INVALID", "error", "Lock manifest entry field must be a non-empty string.", f"{path}.accepted_commit", field="accepted_commit"))
        elif not _COMMIT_SHA_RE.fullmatch(accepted_commit):
            diagnostics.append(diagnostic("PG_LOCK_COMMIT_INVALID", "error", "Lock manifest accepted_commit must be a 40-character lowercase hexadecimal commit SHA.", f"{path}.accepted_commit", actual=accepted_commit))

        for field in ("path", "contract_or_schema_id"):
            if not isinstance(item.get(field), str) or not item.get(field):
                diagnostics.append(diagnostic("PG_LOCK_FIELD_INVALID", "error", "Lock manifest entry field must be a non-empty string.", f"{path}.{field}", field=field))

        digest = item.get("sha256_file_bytes")
        if not isinstance(digest, str) or not digest:
            diagnostics.append(diagnostic("PG_LOCK_FIELD_INVALID", "error", "Lock manifest entry field must be a non-empty string.", f"{path}.sha256_file_bytes", field="sha256_file_bytes"))
        elif not _SHA256_RE.fullmatch(digest):
            diagnostics.append(diagnostic("PG_LOCK_HASH_INVALID", "error", "Lock manifest sha256_file_bytes must be a 64-character lowercase hexadecimal SHA-256 digest.", f"{path}.sha256_file_bytes", actual=digest))

        size_bytes = item.get("size_bytes")
        if "size_bytes" in item and (not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0):
            diagnostics.append(diagnostic("PG_LOCK_SIZE_BYTES_INVALID", "error", "Lock manifest size_bytes must be an integer greater than or equal to 0 when present.", f"{path}.size_bytes", actual=size_bytes))

    return sort_diagnostics(diagnostics)
