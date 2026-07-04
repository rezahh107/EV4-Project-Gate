from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..diagnostics import Diagnostic, diagnostic, sort_diagnostics

LOCK_MANIFEST_SCHEMA_VERSION = "lock-manifest.v1"
LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION = "external-contract-lock.v1"
KNOWN_LOCK_SCHEMA_VERSIONS = {LOCK_MANIFEST_SCHEMA_VERSION, LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION}


class LockManifestValidationError(ValueError):
    """Raised when a lock manifest cannot be interpreted structurally."""


@dataclass(frozen=True)
class LockManifestOptions:
    allow_legacy_external_lock: bool = True


def validate_lock_manifest(lock: Any, options: LockManifestOptions | None = None) -> list[Diagnostic]:
    """Validate Project Gate-owned lock manifest carrier structure.

    This is intentionally structural. File-byte verification against a concrete
    repository source remains in transition-specific code such as
    `external_lock.verify_external_contract_lock`.
    """

    opts = options or LockManifestOptions()
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG_LOCK_NOT_OBJECT", "error", "Lock manifest must be a JSON object.", "$")]

    version = lock.get("schema_version")
    if version is None:
        diagnostics.append(diagnostic("PG_LOCK_SCHEMA_VERSION_MISSING", "error", "Lock manifest schema_version is required.", "$.schema_version"))
    elif version not in KNOWN_LOCK_SCHEMA_VERSIONS or (version == LEGACY_EXTERNAL_LOCK_SCHEMA_VERSION and not opts.allow_legacy_external_lock):
        diagnostics.append(
            diagnostic(
                "PG_LOCK_SCHEMA_VERSION_UNKNOWN",
                "error",
                "Lock manifest schema_version is not supported by this Project Gate core.",
                "$.schema_version",
                actual=version,
                supported=sorted(KNOWN_LOCK_SCHEMA_VERSIONS),
            )
        )

    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG_LOCK_FILES_NOT_ARRAY", "error", "Lock manifest files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)

    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG_LOCK_ENTRY_NOT_OBJECT", "error", "Lock manifest file entry must be an object.", path))
            continue
        role = item.get("role")
        if not isinstance(role, str) or not role:
            diagnostics.append(diagnostic("PG_LOCK_ROLE_INVALID", "error", "Lock manifest role must be a non-empty string.", f"{path}.role"))
        elif role in seen:
            diagnostics.append(diagnostic("PG_LOCK_ROLE_DUPLICATE", "error", "Lock manifest contains a duplicate role.", f"{path}.role", role=role))
        else:
            seen.add(role)
        for field in ("repository", "accepted_commit", "path", "contract_or_schema_id", "sha256_file_bytes"):
            if not isinstance(item.get(field), str) or not item.get(field):
                diagnostics.append(diagnostic("PG_LOCK_FIELD_INVALID", "error", "Lock manifest entry field must be a non-empty string.", f"{path}.{field}", field=field))
        digest = item.get("sha256_file_bytes")
        if isinstance(digest, str) and len(digest) == 64 and digest.lower() != digest:
            diagnostics.append(diagnostic("PG_LOCK_HASH_NOT_LOWERCASE", "error", "Lock file-byte SHA-256 must be lowercase hexadecimal.", f"{path}.sha256_file_bytes"))
    return sort_diagnostics(diagnostics)
