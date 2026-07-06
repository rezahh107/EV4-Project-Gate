from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .canonical_json import load_json_file
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics

PROJECT_GATE_REPOSITORY = "rezahh107/EV4-Project-Gate"
LOCK_SCHEMA_VERSION = "project-gate-common-contract-lock.v1"
CONTRACT_ID = "producer-gate-export.v1"
CONTRACT_VERSION = "1.0.0"
CANONICAL_PATH = "contracts/common/producer-gate-export.v1.schema.json"
VERIFIER_ID = "ev4-project-gate-vendored-common-contract-verifier"
VERIFIER_VERSION = "1.0.0"


def validate_common_contract_lock(lock: Any, repository_root: str | Path = ".") -> list[Diagnostic]:
    if not isinstance(lock, dict):
        return [diagnostic("PG_COMMON_LOCK_NOT_OBJECT", "error", "Common contract lock must be an object.", "$")]
    schema = load_json_file(Path(repository_root) / "contracts/common/common-contract-lock.v1.schema.json")
    diagnostics: list[Diagnostic] = []
    for error in sorted(Draft202012Validator(schema).iter_errors(lock), key=lambda item: (_path(list(item.absolute_path)), item.message)):
        diagnostics.append(diagnostic("PG_COMMON_LOCK_SCHEMA_INVALID", "error", error.message, _path(list(error.absolute_path))))

    if lock.get("lock_schema") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG_COMMON_LOCK_SCHEMA_VERSION_INVALID", "error", "Unknown lock schema.", "$.lock_schema"))
    if lock.get("contract_owner") != PROJECT_GATE_REPOSITORY:
        diagnostics.append(diagnostic("PG_COMMON_LOCK_OWNER_DRIFT", "error", "Contract owner must remain EV4-Project-Gate.", "$.contract_owner"))
    if lock.get("contract_id") != CONTRACT_ID:
        diagnostics.append(diagnostic("PG_COMMON_LOCK_CONTRACT_ID_DRIFT", "error", "Contract identity mismatch.", "$.contract_id"))
    if lock.get("contract_version") != CONTRACT_VERSION:
        diagnostics.append(diagnostic("PG_COMMON_LOCK_CONTRACT_VERSION_DRIFT", "error", "Contract version mismatch.", "$.contract_version"))

    canonical = lock.get("canonical")
    if isinstance(canonical, dict):
        if canonical.get("repository") != PROJECT_GATE_REPOSITORY:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_CANONICAL_OWNER_DRIFT", "error", "Canonical repository must remain EV4-Project-Gate.", "$.canonical.repository"))
        if canonical.get("path") != CANONICAL_PATH:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_PATH_DRIFT", "error", "Canonical path mismatch.", "$.canonical.path"))
        if canonical.get("commit_sha") in {"main", "master", "HEAD"}:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_MOVING_REF_FORBIDDEN", "error", "Moving refs are forbidden.", "$.canonical.commit_sha"))

    vendored = lock.get("vendored")
    if isinstance(vendored, dict):
        if vendored.get("local_copy_authoritative") is not False:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_LOCAL_COPY_AUTHORITY_FORBIDDEN", "error", "Vendored copy cannot claim canonical authority.", "$.vendored.local_copy_authoritative"))
        diagnostics.extend(_safe_path_diagnostics(vendored.get("path"), "$.vendored.path"))
    if isinstance(canonical, dict):
        diagnostics.extend(_safe_path_diagnostics(canonical.get("path"), "$.canonical.path"))

    verification = lock.get("verification")
    if isinstance(verification, dict):
        if verification.get("byte_equality_required") is not True:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_BYTE_EQUALITY_REQUIRED", "error", "Exact byte equality is mandatory.", "$.verification.byte_equality_required"))
        if verification.get("compare_against_moving_default_branch") is not False:
            diagnostics.append(diagnostic("PG_COMMON_LOCK_MOVING_DEFAULT_BRANCH_COMPARISON_FORBIDDEN", "error", "Moving default-branch comparison is forbidden.", "$.verification.compare_against_moving_default_branch"))
    return sort_diagnostics(_deduplicate(diagnostics))


def verify_vendored_common_contract(
    lock: Any,
    canonical_root: str | Path,
    vendored_root: str | Path,
    repository_root: str | Path = ".",
) -> dict[str, Any]:
    diagnostics = validate_common_contract_lock(lock, repository_root)
    result: dict[str, Any] = {
        "schema_version": "common-contract-verification-result.v1",
        "verifier_id": VERIFIER_ID,
        "verifier_version": VERIFIER_VERSION,
        "status": "invalid",
        "contract_id": lock.get("contract_id") if isinstance(lock, dict) else None,
        "contract_version": lock.get("contract_version") if isinstance(lock, dict) else None,
        "hashes": {"canonical_expected": None, "canonical_actual": None, "vendored_declared": None, "vendored_actual": None},
        "byte_equal": False,
        "schema_identity_valid": False,
        "diagnostics": [],
    }
    if any(item.severity == "error" for item in diagnostics):
        result["diagnostics"] = [item.to_dict() for item in diagnostics]
        return result

    canonical_path = _resolve_within(Path(canonical_root).resolve(), lock["canonical"]["path"], "$.canonical.path", diagnostics)
    vendored_path = _resolve_within(Path(vendored_root).resolve(), lock["vendored"]["path"], "$.vendored.path", diagnostics)
    if canonical_path is None or vendored_path is None:
        result["diagnostics"] = [item.to_dict() for item in sort_diagnostics(_deduplicate(diagnostics))]
        return result
    canonical_bytes = _read(canonical_path, "canonical", diagnostics)
    vendored_bytes = _read(vendored_path, "vendored", diagnostics)

    expected = lock["canonical"]["file_sha256"]
    declared = lock["vendored"]["file_sha256"]
    result["hashes"]["canonical_expected"] = expected
    result["hashes"]["vendored_declared"] = declared

    if canonical_bytes is not None:
        actual = hashlib.sha256(canonical_bytes).hexdigest()
        result["hashes"]["canonical_actual"] = actual
        if actual != expected:
            diagnostics.append(diagnostic("PG_COMMON_CONTRACT_CANONICAL_HASH_MISMATCH", "error", "Canonical bytes do not match the lock hash.", "$.canonical.file_sha256", expected=expected, actual=actual))
    if vendored_bytes is not None:
        actual = hashlib.sha256(vendored_bytes).hexdigest()
        result["hashes"]["vendored_actual"] = actual
        if actual != declared:
            diagnostics.append(diagnostic("PG_COMMON_CONTRACT_VENDORED_HASH_MISMATCH", "error", "Vendored bytes do not match the declared hash.", "$.vendored.file_sha256", expected=declared, actual=actual))

    if canonical_bytes is not None and vendored_bytes is not None:
        result["byte_equal"] = canonical_bytes == vendored_bytes
        if not result["byte_equal"]:
            diagnostics.append(diagnostic("PG_COMMON_CONTRACT_BYTE_MISMATCH", "error", "Vendored contract must be byte-identical to the canonical file.", "$.vendored.path"))
            if _parse(canonical_bytes) == _parse(vendored_bytes) and _parse(canonical_bytes) is not None:
                diagnostics.append(diagnostic("PG_COMMON_CONTRACT_SEMANTIC_EQUALITY_ONLY", "warning", "JSON is semantically equal but byte-different; the lock still fails.", "$.vendored.path"))
        identity_valid = _identity_valid(canonical_bytes, lock, "canonical", diagnostics)
        identity_valid = _identity_valid(vendored_bytes, lock, "vendored", diagnostics) and identity_valid
        result["schema_identity_valid"] = identity_valid

    ordered = sort_diagnostics(_deduplicate(diagnostics))
    result["diagnostics"] = [item.to_dict() for item in ordered]
    result["status"] = "valid" if not any(item.severity == "error" for item in ordered) else "invalid"
    return result


def _identity_valid(data: bytes, lock: dict[str, Any], label: str, diagnostics: list[Diagnostic]) -> bool:
    parsed = _parse(data)
    if not isinstance(parsed, dict) or "$schema" not in parsed:
        return True
    valid = True
    if parsed.get("x-ev4-contract-id") != lock["contract_id"]:
        diagnostics.append(diagnostic("PG_COMMON_CONTRACT_IDENTITY_MISMATCH", "error", "Contract identity does not match lock.", f"$.{label}.path"))
        valid = False
    if parsed.get("x-ev4-contract-version") != lock["contract_version"]:
        diagnostics.append(diagnostic("PG_COMMON_CONTRACT_VERSION_MISMATCH", "error", "Contract version does not match lock.", f"$.{label}.path"))
        valid = False
    return valid


def _read(path: Path, label: str, diagnostics: list[Diagnostic]) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError as exc:
        diagnostics.append(diagnostic("PG_COMMON_CONTRACT_FILE_READ_ERROR", "error", "Contract file could not be read.", f"$.{label}.path", error_type=type(exc).__name__, file_path=str(path)))
        return None


def _parse(data: bytes) -> Any | None:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _resolve_within(root: Path, relative: str, path: str, diagnostics: list[Diagnostic]) -> Path | None:
    path_diagnostics = _safe_path_diagnostics(relative, path)
    diagnostics.extend(path_diagnostics)
    if path_diagnostics or not isinstance(relative, str):
        return None
    try:
        root = root.resolve()
        candidate = (root / relative).resolve()
        if not _is_relative_to(candidate, root):
            diagnostics.append(diagnostic("PG_COMMON_LOCK_PATH_TRAVERSAL", "error", "Path escapes repository root.", path, actual=relative))
            return None
        return candidate
    except (OSError, RuntimeError, ValueError) as exc:
        diagnostics.append(diagnostic("PG_COMMON_LOCK_PATH_INVALID", "error", "Path could not be resolved safely.", path, actual=relative, error_type=type(exc).__name__))
        return None


def _safe_path_diagnostics(value: Any, path: str) -> list[Diagnostic]:
    if not isinstance(value, str) or not value:
        return []
    if value.startswith("/"):
        return [diagnostic("PG_COMMON_LOCK_PATH_DRIFT", "error", "Root-relative or absolute paths are forbidden; use normalized repository-relative POSIX paths.", path, actual=value)]
    if "\\" in value:
        return [diagnostic("PG_COMMON_LOCK_PATH_DRIFT", "error", "Windows-style backslash paths are forbidden; use normalized repository-relative POSIX paths.", path, actual=value)]
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return [diagnostic("PG_COMMON_LOCK_PATH_DRIFT", "error", "Path traversal and non-normalized path segments are forbidden.", path, actual=value)]
    return []


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _deduplicate(items: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Diagnostic] = []
    for item in items:
        key = (item.code, item.path, item.message)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _path(parts: list[Any]) -> str:
    value = "$"
    for part in parts:
        value += f"[{part}]" if isinstance(part, int) else f".{part}"
    return value
