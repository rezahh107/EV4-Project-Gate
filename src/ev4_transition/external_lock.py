from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical_json import bytes_sha256, load_json_file
from .contract_source import ContractSource
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics

TRANSITION_ID = "ev4-architect-to-ce-transition@1.0.0"
LOCK_SCHEMA_VERSION = "external-contract-lock.v1"
ARCHITECT_REPO = "rezahh107/EV4-Architect-Repo"
ARCHITECT_COMMIT = "be9bdea9ae246b1587043f2582c1a950ea2a6ec5"
ARCHITECT_RUNTIME_COMMIT = ARCHITECT_COMMIT
CE_REPO = "rezahh107/EV4-Constructability-Engineer-Repo"
CE_COMMIT = "6650c31304e5a0472b276c36018c1df8f42ac983"


@dataclass(frozen=True)
class ExpectedDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str


EXPECTED_ARCHITECT_TO_CE_DEPENDENCIES: dict[str, ExpectedDependency] = {
    "architect_payload_schema": ExpectedDependency(
        role="architect_payload_schema",
        repository=ARCHITECT_REPO,
        accepted_commit=ARCHITECT_RUNTIME_COMMIT,
        path="schemas/ev4-architect-stage-payload.v1.schema.json",
        contract_or_schema_id="ev4-architect-stage-payload@1.0.0",
    ),
    "architect_payload_validator": ExpectedDependency(
        role="architect_payload_validator",
        repository=ARCHITECT_REPO,
        accepted_commit=ARCHITECT_RUNTIME_COMMIT,
        path="scripts/check-architect-stage-payload.py",
        contract_or_schema_id="ev4-architect-stage-payload-validator@1.0.0",
    ),
    "architect_valid_fixture": ExpectedDependency(
        role="architect_valid_fixture",
        repository=ARCHITECT_REPO,
        accepted_commit=ARCHITECT_RUNTIME_COMMIT,
        path="fixtures/architect-stage-payload/valid/minimal-complete.v1.json",
        contract_or_schema_id="ev4-architect-stage-payload@1.0.0",
    ),
    "architect_insufficient_fixture": ExpectedDependency(
        role="architect_insufficient_fixture",
        repository=ARCHITECT_REPO,
        accepted_commit=ARCHITECT_RUNTIME_COMMIT,
        path="fixtures/architect-stage-payload/insufficient-evidence/missing-real-stage-output.v1.json",
        contract_or_schema_id="ev4-architect-stage-payload@1.0.0",
    ),
    "ce_intake_schema": ExpectedDependency(
        role="ce_intake_schema",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="schemas/ce_architect_stage_intake.v1_1.schema.json",
        contract_or_schema_id="ev4-ce-architect-stage-intake@1.1.0",
    ),
    "ce_intake_validator": ExpectedDependency(
        role="ce_intake_validator",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="scripts/validate-ce-architect-stage-intake.py",
        contract_or_schema_id="ev4-ce-architect-stage-intake-validator@1.1.0",
    ),
    "ce_mapping_contract": ExpectedDependency(
        role="ce_mapping_contract",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="contracts/ARCHITECT_STAGE_TO_CE_INTAKE_MAPPING_V1_1.md",
        contract_or_schema_id="ev4-architect-stage-to-ce-intake-mapping@1.1.0",
    ),
    "ce_valid_fixture": ExpectedDependency(
        role="ce_valid_fixture",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="fixtures/architect-stage-intake-v1-1/valid/project-gate-transition-complete.v1_1.json",
        contract_or_schema_id="ev4-ce-architect-stage-intake@1.1.0",
    ),
    "ce_insufficient_fixture": ExpectedDependency(
        role="ce_insufficient_fixture",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="fixtures/architect-stage-intake-v1-1/insufficient-evidence/project-gate-transition-insufficient.v1_1.json",
        contract_or_schema_id="ev4-ce-architect-stage-intake@1.1.0",
    ),
    "ce_synthetic_source_bundle_fixture": ExpectedDependency(
        role="ce_synthetic_source_bundle_fixture",
        repository=CE_REPO,
        accepted_commit=CE_COMMIT,
        path="fixtures/architect-stage-intake-v1-1/source-bundles/synthetic-architect-stage-bundle.v1.json",
        contract_or_schema_id="ev4-architect-stage-payload@1.0.0",
    ),
}
REQUIRED_ROLES = set(EXPECTED_ARCHITECT_TO_CE_DEPENDENCIES)


def load_lock(path: str | Path) -> dict[str, Any]:
    return load_json_file(path)


def lock_file_hash(lock: dict[str, Any]) -> str:
    from .canonical_json import canonical_sha256
    return canonical_sha256(lock)


def verify_external_contract_lock(lock: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG_A2C_LOCK_NOT_OBJECT", "error", "External lock manifest must be an object.", "$")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG_A2C_LOCK_VERSION_MISMATCH", "error", "External lock manifest version is not the expected Project Gate lock version.", "$.schema_version", expected=LOCK_SCHEMA_VERSION, actual=lock.get("schema_version")))
    if lock.get("transition_id") != TRANSITION_ID:
        diagnostics.append(diagnostic("PG_A2C_LOCK_TRANSITION_ID_MISMATCH", "error", "External lock manifest transition id does not match this transition.", "$.transition_id", expected=TRANSITION_ID, actual=lock.get("transition_id")))
    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG_A2C_LOCK_FILES_NOT_ARRAY", "error", "External lock manifest files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    seen_roles: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG_A2C_LOCK_ENTRY_NOT_OBJECT", "error", "Lock entry must be an object.", path))
            continue
        role = item.get("role")
        if not isinstance(role, str):
            diagnostics.append(diagnostic("PG_A2C_LOCK_ROLE_INVALID", "error", "Lock entry role must be a string.", f"{path}.role", actual=role))
            continue
        expected = EXPECTED_ARCHITECT_TO_CE_DEPENDENCIES.get(role)
        if expected is None:
            diagnostics.append(diagnostic("PG_A2C_LOCK_ROLE_UNEXPECTED", "error", "External lock manifest contains an unexpected role.", f"{path}.role", role=role))
            continue
        if role in seen_roles:
            diagnostics.append(diagnostic("PG_A2C_LOCK_ROLE_DUPLICATE", "error", "External lock manifest contains a duplicate role.", f"{path}.role", role=role))
            continue
        seen_roles.add(role)
        diagnostics.extend(_entry_expected_value_diagnostics(item, expected, path))
        try:
            content = source.read_bytes(expected.repository, expected.accepted_commit, expected.path)
        except Exception as exc:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_FILE_READ_FAILED", "error", "Pinned external file could not be read.", path, repository=expected.repository, commit=expected.accepted_commit, file_path=expected.path, role=role, error_type=type(exc).__name__))
            continue
        actual_hash = bytes_sha256(content)
        expected_hash = item.get("sha256_file_bytes")
        if actual_hash != expected_hash:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_HASH_MISMATCH", "error", "Pinned external file hash does not match lock manifest.", path, role=role, repository=expected.repository, commit=expected.accepted_commit, file_path=expected.path, expected_sha256=expected_hash, actual_sha256=actual_hash))
        diagnostics.extend(_identity_diagnostics(content, expected, path))
    missing = sorted(REQUIRED_ROLES - seen_roles)
    if missing:
        diagnostics.append(diagnostic("PG_A2C_LOCK_ROLE_MISSING", "error", "External lock manifest is missing required roles.", "$.files", missing_roles=missing))
    return sort_diagnostics(diagnostics)


def _entry_expected_value_diagnostics(item: dict[str, Any], expected: ExpectedDependency, path: str) -> list[Diagnostic]:
    checks = [
        ("repository", expected.repository, "PG_A2C_LOCK_REPOSITORY_MISMATCH"),
        ("accepted_commit", expected.accepted_commit, "PG_A2C_LOCK_COMMIT_MISMATCH"),
        ("path", expected.path, "PG_A2C_LOCK_PATH_MISMATCH"),
        ("contract_or_schema_id", expected.contract_or_schema_id, "PG_A2C_LOCK_IDENTITY_MISMATCH"),
    ]
    out: list[Diagnostic] = []
    for field, expected_value, code in checks:
        actual = item.get(field)
        if actual != expected_value:
            out.append(diagnostic(code, "error", "External lock manifest entry does not match Project Gate-owned expected dependency configuration.", f"{path}.{field}", role=expected.role, expected=expected_value, actual=actual))
    return out


def _identity_diagnostics(content: bytes, expected: ExpectedDependency, path: str) -> list[Diagnostic]:
    role = expected.role
    expected_id = expected.contract_or_schema_id
    diagnostics: list[Diagnostic] = []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return [diagnostic("PG_A2C_EXTERNAL_FILE_NOT_UTF8", "error", "Pinned external file is not valid UTF-8.", path, role=role)]
    if role in {"architect_payload_schema", "ce_intake_schema"}:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [diagnostic("PG_A2C_EXTERNAL_JSON_INVALID", "error", "Pinned external JSON file is malformed.", path, role=role)]
        schema_id_const = (((data.get("properties") or {}).get("schema_id") or {}).get("const"))
        if schema_id_const != expected_id:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_SCHEMA_ID_MISMATCH", "error", "Pinned external schema identity does not match Project Gate expected dependency configuration.", path, role=role, expected_schema_id=expected_id, actual_schema_id=schema_id_const))
    elif role in {"architect_valid_fixture", "architect_insufficient_fixture", "ce_valid_fixture", "ce_insufficient_fixture"}:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [diagnostic("PG_A2C_EXTERNAL_JSON_INVALID", "error", "Pinned external JSON fixture is malformed.", path, role=role)]
        actual = data.get("schema_id")
        if actual != expected_id:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_FIXTURE_SCHEMA_ID_MISMATCH", "error", "Pinned external fixture identity does not match Project Gate expected dependency configuration.", path, role=role, expected_schema_id=expected_id, actual_schema_id=actual))
    elif role == "ce_mapping_contract":
        if expected_id not in text:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_MAPPING_ID_MISMATCH", "error", "Pinned CE mapping contract identity was not found.", path, role=role, expected_contract_id=expected_id))
    elif role in {"architect_payload_validator", "ce_intake_validator"}:
        if "--format" not in text or "json" not in text:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_VALIDATOR_MODE_UNCONFIRMED", "warning", "Pinned validator does not visibly expose JSON format support.", path, role=role))
    elif role == "ce_synthetic_source_bundle_fixture":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [diagnostic("PG_A2C_EXTERNAL_JSON_INVALID", "error", "Pinned external JSON fixture is malformed.", path, role=role)]
        actual = (((data.get("source_bundle") or {}).get("payload_schema") or {}).get("id"))
        if actual != expected_id:
            diagnostics.append(diagnostic("PG_A2C_EXTERNAL_SOURCE_BUNDLE_SCHEMA_ID_MISMATCH", "error", "Pinned source-bundle fixture identity does not match Project Gate expected dependency configuration.", path, role=role, expected_schema_id=expected_id, actual_schema_id=actual))
    return diagnostics
