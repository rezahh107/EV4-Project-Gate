from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ev4_transition.bundle_validator import BundleValidator, ResultValidationError
from ev4_transition.canonical_json import CANONICAL_JSON_VERSION, CanonicalJsonError, bytes_sha256, canonical_sha256, load_json_file
from ev4_transition.contract_source import ContractSource, LocalCheckoutContractSource
from ev4_transition.diagnostics import Diagnostic, diagnostic, project_gate_status_from_diagnostics, sort_diagnostics
from ev4_transition.runners import execute_builder_adapter, execute_builder_contract_gate, execute_builder_output_validator, execute_ce_package_validator

TRANSITION_ID = "ev4-ce-to-builder-transition@1.0.0"
TRANSITION_VERSION = "1.0.0"
LOCK_SCHEMA_VERSION = "ce-to-builder-transition-lock.v1"
CE_REPO = "rezahh107/EV4-Constructability-Engineer-Repo"
BUILDER_REPO = "rezahh107/EV4-Builder-Assistant-Repo"
CE_COMMIT = "cfceec5c20269c75a1cc19b2675d7087cede4599"
BUILDER_COMMIT = "69a2c61edf6d06b4418ad770fcefbfdffcf275d6"
CE_PACKAGE_SCHEMA = "ev4-builder-executable-package@1.0.0"
BUILDER_CONTEXT_SCHEMA = "ev4-builder-context-package@1.0.0"
PG_REPO = "rezahh107/EV4-Project-Gate"


@dataclass(frozen=True)
class ExpectedDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str
    identity_marker: str


_EXPECTED_ITEMS = [
    ExpectedDependency("ce_producer_contract", CE_REPO, CE_COMMIT, "docs/CE_TO_BUILDER_PRODUCER_CONTRACT.md", CE_PACKAGE_SCHEMA, CE_PACKAGE_SCHEMA),
    ExpectedDependency("ce_builder_executable_schema", CE_REPO, CE_COMMIT, "schemas/builder_executable_package.schema.json", CE_PACKAGE_SCHEMA, "EV4 Builder Executable Package"),
    ExpectedDependency("ce_validator_engine", CE_REPO, CE_COMMIT, "validator/engine.py", "validator/engine.py", "builder_executable_package"),
    ExpectedDependency("ce_validator_rules", CE_REPO, CE_COMMIT, "validator/rules.py", "validator/rules.py", "ConstructabilityViolation"),
    ExpectedDependency("ce_valid_fixture", CE_REPO, CE_COMMIT, "tests/role-alignment/valid/executable_visual_reference_package.json", CE_PACKAGE_SCHEMA, CE_PACKAGE_SCHEMA),
    ExpectedDependency("builder_input_contract", BUILDER_REPO, BUILDER_COMMIT, "input-contracts/BUILDER_CONTEXT_INPUT_CONTRACT.md", BUILDER_CONTEXT_SCHEMA, BUILDER_CONTEXT_SCHEMA),
    ExpectedDependency("builder_context_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/builder-context-package.schema.json", BUILDER_CONTEXT_SCHEMA, BUILDER_CONTEXT_SCHEMA),
    ExpectedDependency("builder_gate_doc", BUILDER_REPO, BUILDER_COMMIT, "docs/CE_TO_BUILDER_CONTRACT_GATE.md", "ce_to_builder_contract_gate", "ce_to_builder_contract_gate"),
    ExpectedDependency("builder_gate_script", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-ce-to-builder-contract-gate.mjs", "ce_to_builder_contract_gate", "ce_to_builder_contract_gate"),
    ExpectedDependency("builder_adapter_contract", BUILDER_REPO, BUILDER_COMMIT, "docs/CE_BUILDER_PACKAGE_ADAPTER_CONTRACT.md", "normalizeCeBuilderExecutablePackage", "CE Builder Package Adapter Contract"),
    ExpectedDependency("builder_adapter_script", BUILDER_REPO, BUILDER_COMMIT, "scripts/normalize-ce-builder-executable-package.mjs", "normalizeCeBuilderExecutablePackage", "CE_BUILDER_PACKAGE_TRANSFORM_IDS"),
    ExpectedDependency("builder_transform_registry", BUILDER_REPO, BUILDER_COMMIT, "data/ce-builder-transformation-registry.v1.json", "ce-builder-transformation-registry.v1", "ce-builder-transformation-registry"),
    ExpectedDependency("builder_output_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-package.mjs", "Cross-field validation", "validateReferenceParadigmGate"),
]
EXPECTED_CE_TO_BUILDER_DEPENDENCIES: dict[str, ExpectedDependency] = {item.role: item for item in _EXPECTED_ITEMS}
REQUIRED_ROLES = set(EXPECTED_CE_TO_BUILDER_DEPENDENCIES)


@dataclass(frozen=True)
class CeToBuilderTransitionConfig:
    schema_root: Path
    lock: dict[str, Any]
    ce_repo_root: Path | None = None
    builder_repo_root: Path | None = None
    timeout_seconds: float = 30
    require_real_evidence: bool = True


def verify_ce_to_builder_lock(lock: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG.C2B.LOCK_NOT_OBJECT", "error", "CE→Builder lock manifest must be an object.", "$")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG.C2B.LOCK_VERSION_MISMATCH", "error", "CE→Builder lock schema version is missing or unknown.", "$.schema_version", expected=LOCK_SCHEMA_VERSION, actual=lock.get("schema_version")))
    if lock.get("transition_id") != TRANSITION_ID:
        diagnostics.append(diagnostic("PG.C2B.LOCK_TRANSITION_ID_MISMATCH", "error", "CE→Builder lock transition id does not match this transition.", "$.transition_id", expected=TRANSITION_ID, actual=lock.get("transition_id")))
    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG.C2B.LOCK_FILES_NOT_ARRAY", "error", "CE→Builder lock files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG.C2B.LOCK_ENTRY_NOT_OBJECT", "error", "CE→Builder lock entry must be an object.", path))
            continue
        role = item.get("role")
        expected = EXPECTED_CE_TO_BUILDER_DEPENDENCIES.get(role) if isinstance(role, str) else None
        if expected is None:
            diagnostics.append(diagnostic("PG.C2B.LOCK_ROLE_UNEXPECTED", "error", "CE→Builder lock contains an unexpected role.", f"{path}.role", role=role))
            continue
        if role in seen:
            diagnostics.append(diagnostic("PG.C2B.LOCK_ROLE_DUPLICATE", "error", "CE→Builder lock contains a duplicate role.", f"{path}.role", role=role))
        seen.add(role)
        for field, expected_value, code in [
            ("repository", expected.repository, "PG.C2B.LOCK_REPOSITORY_MISMATCH"),
            ("accepted_commit", expected.accepted_commit, "PG.C2B.LOCK_COMMIT_MISMATCH"),
            ("path", expected.path, "PG.C2B.LOCK_PATH_MISMATCH"),
            ("contract_or_schema_id", expected.contract_or_schema_id, "PG.C2B.LOCK_IDENTITY_MISMATCH"),
        ]:
            if item.get(field) != expected_value:
                diagnostics.append(diagnostic(code, "error", "CE→Builder lock entry does not match expected owner dependency.", f"{path}.{field}", expected=expected_value, actual=item.get(field), role=role))
        try:
            content = source.read_bytes(expected.repository, expected.accepted_commit, expected.path)
        except Exception as exc:
            diagnostics.append(diagnostic("PG.C2B.OWNER_FILE_READ_FAILED", "insufficient_evidence", "Pinned CE/Builder file could not be read from the owner repository checkout.", path, repository=expected.repository, commit=expected.accepted_commit, file_path=expected.path, role=role, error_type=type(exc).__name__))
            continue
        actual_hash = bytes_sha256(content)
        if item.get("sha256_file_bytes") != actual_hash:
            diagnostics.append(diagnostic("PG.C2B.EXTERNAL_HASH_MISMATCH", "error", "Pinned owner file hash does not match CE→Builder lock manifest.", path, role=role, repository=expected.repository, commit=expected.accepted_commit, file_path=expected.path, expected_sha256=item.get("sha256_file_bytes"), actual_sha256=actual_hash))
        if expected.identity_marker not in content.decode("utf-8", errors="replace"):
            diagnostics.append(diagnostic("PG.C2B.EXTERNAL_IDENTITY_MISMATCH", "error", "Pinned CE/Builder owner file identity marker was not found.", path, role=role, expected_marker=expected.identity_marker))
    missing = sorted(REQUIRED_ROLES - seen)
    if missing:
        diagnostics.append(diagnostic("PG.C2B.LOCK_ROLE_MISSING", "error", "CE→Builder lock is missing required owner dependency roles.", "$.files", missing_roles=missing))
    return sort_diagnostics(diagnostics)


def transition_ce_to_builder(ce_input: Any, contract_source: ContractSource, transition_config: CeToBuilderTransitionConfig, progress_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    execution_records: dict[str, dict[str, Any]] = {}
    accepted_requires = _accepted_requires_template()
    source_bundle, ce_package = _extract_ce_package(ce_input, transition_config.schema_root, diagnostics, accepted_requires)
    if _has_blocking(diagnostics):
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    diagnostics.extend(_ce_package_identity_diagnostics(ce_package))
    accepted_requires["ce_package_identity_verified"] = not _has_error(diagnostics)
    diagnostics.extend(_real_evidence_diagnostics(source_bundle, transition_config.require_real_evidence))
    accepted_requires["synthetic_only_evidence_not_used_as_real_evidence"] = not any(d.code == "PG.C2B.SYNTHETIC_ONLY_EVIDENCE" for d in diagnostics)
    accepted_requires["required_evidence_present"] = not any(d.code in {"PG.C2B.REAL_EVIDENCE_REQUIRED", "PG.C2B.SYNTHETIC_ONLY_EVIDENCE"} for d in diagnostics)
    if _has_blocking(diagnostics):
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    lock_diags = verify_ce_to_builder_lock(transition_config.lock, contract_source)
    diagnostics.extend(lock_diags)
    accepted_requires["ce_producer_pin_hash_matches"] = not any(d.severity in {"error", "insufficient_evidence"} and d.details.get("repository") == CE_REPO for d in lock_diags)
    accepted_requires["builder_consumer_pin_hash_matches"] = not any(d.severity in {"error", "insufficient_evidence"} and d.details.get("repository") == BUILDER_REPO for d in lock_diags)
    if _has_blocking(diagnostics):
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    ce_outcome = _run_ce_validator(transition_config, ce_package, progress_sink)
    execution_records["ce_validator"] = ce_outcome.execution_record.to_dict()
    diagnostics.extend(ce_outcome.diagnostics)
    accepted_requires["official_ce_validator_passed"] = ce_outcome.status == "accepted"
    if _has_blocking(diagnostics) or ce_outcome.status != "accepted":
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    gate_outcome = _run_builder_gate(transition_config, ce_package, progress_sink)
    execution_records["builder_contract_gate"] = gate_outcome.execution_record.to_dict()
    diagnostics.extend(gate_outcome.diagnostics)
    accepted_requires["builder_contract_gate_passed"] = gate_outcome.status == "accepted"
    if _has_blocking(diagnostics) or gate_outcome.status != "accepted":
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    adapter_outcome = _run_builder_adapter(transition_config, ce_package, progress_sink)
    execution_records["builder_adapter"] = adapter_outcome.execution_record.to_dict()
    diagnostics.extend(adapter_outcome.diagnostics)
    builder_context_package = adapter_outcome.parsed_result if isinstance(adapter_outcome.parsed_result, dict) else None
    if builder_context_package is None:
        diagnostics.append(diagnostic("PG.C2B.ADAPTER_OUTPUT_UNPARSEABLE", "insufficient_evidence", "Official Builder adapter did not produce a parseable JSON object output.", "$.adapter_output"))
    accepted_requires["official_builder_adapter_passed"] = adapter_outcome.status == "accepted" and isinstance(builder_context_package, dict)
    if _has_blocking(diagnostics) or adapter_outcome.status != "accepted" or builder_context_package is None:
        return _result(ce_input, source_bundle, ce_package, None, diagnostics, accepted_requires, execution_records, transition_config)
    diagnostics.extend(_builder_schema_validation_diagnostics(builder_context_package, contract_source))
    if not _has_blocking(diagnostics):
        output_outcome = _run_builder_output_validator(transition_config, builder_context_package, progress_sink)
        execution_records["builder_output_validator"] = output_outcome.execution_record.to_dict()
        diagnostics.extend(output_outcome.diagnostics)
        accepted_requires["builder_output_validates"] = output_outcome.status == "accepted"
    accepted_requires["no_forbidden_claim"] = not _has_forbidden_claim(ce_package, builder_context_package)
    if not accepted_requires["no_forbidden_claim"]:
        diagnostics.append(diagnostic("PG.C2B.FORBIDDEN_CLAIM", "error", "CE→Builder transition encountered a forbidden readiness/production claim.", "$"))
    return _result(ce_input, source_bundle, ce_package, builder_context_package, diagnostics, accepted_requires, execution_records, transition_config)


def transition_from_local_paths(ce_input: Any, schema_root: str | Path, lock_path: str | Path, ce_repo: str | Path, builder_repo: str | Path, *, timeout_seconds: float = 30, require_real_evidence: bool = True) -> dict[str, Any]:
    config = CeToBuilderTransitionConfig(Path(schema_root), load_json_file(lock_path), Path(ce_repo), Path(builder_repo), timeout_seconds, require_real_evidence)
    source = LocalCheckoutContractSource({CE_REPO: Path(ce_repo), BUILDER_REPO: Path(builder_repo)})
    return transition_ce_to_builder(ce_input, source, config)


def _run_ce_validator(config: CeToBuilderTransitionConfig, ce_package: dict[str, Any], progress_sink: list[dict[str, Any]] | None):
    if config.ce_repo_root is None:
        return _missing_local_root("validator", "ce_repo_root", "validator/engine.py", CE_REPO, CE_COMMIT)
    return execute_ce_package_validator(repo_root=config.ce_repo_root, owner_repo=CE_REPO, owner_commit=CE_COMMIT, validator_path="validator/engine.py", ce_package=ce_package, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)


def _run_builder_gate(config: CeToBuilderTransitionConfig, ce_package: dict[str, Any], progress_sink: list[dict[str, Any]] | None):
    if config.builder_repo_root is None:
        return _missing_local_root("validator", "builder_repo_root", "scripts/validate-ce-to-builder-contract-gate.mjs", BUILDER_REPO, BUILDER_COMMIT)
    return execute_builder_contract_gate(repo_root=config.builder_repo_root, owner_repo=BUILDER_REPO, owner_commit=BUILDER_COMMIT, gate_path="scripts/validate-ce-to-builder-contract-gate.mjs", ce_package=ce_package, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)


def _run_builder_adapter(config: CeToBuilderTransitionConfig, ce_package: dict[str, Any], progress_sink: list[dict[str, Any]] | None):
    if config.builder_repo_root is None:
        return _missing_local_root("adapter", "builder_repo_root", "scripts/normalize-ce-builder-executable-package.mjs", BUILDER_REPO, BUILDER_COMMIT)
    return execute_builder_adapter(repo_root=config.builder_repo_root, owner_repo=BUILDER_REPO, owner_commit=BUILDER_COMMIT, adapter_path="scripts/normalize-ce-builder-executable-package.mjs", ce_package=ce_package, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)


def _run_builder_output_validator(config: CeToBuilderTransitionConfig, builder_context_package: dict[str, Any], progress_sink: list[dict[str, Any]] | None):
    if config.builder_repo_root is None:
        return _missing_local_root("validator", "builder_repo_root", "scripts/validate-package.mjs", BUILDER_REPO, BUILDER_COMMIT)
    return execute_builder_output_validator(repo_root=config.builder_repo_root, owner_repo=BUILDER_REPO, owner_commit=BUILDER_COMMIT, validator_path="scripts/validate-package.mjs", builder_context_package=builder_context_package, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)


def _missing_local_root(kind: str, root_name: str, path: str, owner_repo: str, owner_commit: str):
    from ev4_transition.runners.records import TimeoutPolicy, ToolExecutionOutcome, build_adapter_execution_record, build_validator_execution_record
    code = "PG.VALIDATOR.MISSING" if kind == "validator" else "PG.ADAPTER.MISSING"
    diag = diagnostic(code, "insufficient_evidence", f"Local {root_name} checkout is required for official CE→Builder tool execution.", "$", root=root_name, tool_path=path)
    if kind == "validator":
        record = build_validator_execution_record(owner_repo=owner_repo, owner_commit=owner_commit, validator_path=path, command=[], working_directory=root_name, exit_code=None, stdout_hash=bytes_sha256(b""), stderr_hash=bytes_sha256(b""), started_by="ev4-project-gate-runner", timeout_policy=TimeoutPolicy(seconds=0), parsed_result_ref=None, failure_code=diag.code)
    else:
        record = build_adapter_execution_record(owner_repo=owner_repo, owner_commit=owner_commit, adapter_path=path, command_or_entrypoint=[], command=[], working_directory=root_name, exit_code=None, stdout_hash=bytes_sha256(b""), stderr_hash=bytes_sha256(b""), started_by="ev4-project-gate-runner", timeout_policy=TimeoutPolicy(seconds=0), input_ref=None, input_hash=None, output_ref=None, output_hash=None, validator_after_adapter_ref=None, failure_code=diag.code)
    return ToolExecutionOutcome("insufficient_evidence", [diag], record, None, bytes_sha256(b""), bytes_sha256(b""))


def _extract_ce_package(ce_input: Any, schema_root: Path, diagnostics: list[Diagnostic], accepted_requires: dict[str, bool]):
    if not isinstance(ce_input, dict):
        diagnostics.append(diagnostic("PG.C2B.INPUT_NOT_OBJECT", "error", "CE→Builder input must be a JSON object.", "$", observed_type=type(ce_input).__name__))
        return None, None
    accepted_requires["input_parses"] = True
    if ce_input.get("schema_version") == "stage-evidence-bundle.v1" or "payload" in ce_input:
        envelope = BundleValidator(schema_root).validate_bundle(ce_input)
        diagnostics.extend(_import_diags(envelope["diagnostics"]))
        accepted_requires["envelope_valid_when_applicable"] = envelope["status"] == "valid"
        data = ce_input.get("payload", {}).get("data") if isinstance(ce_input.get("payload"), dict) else None
        if isinstance(data, dict) and isinstance(data.get("builder_executable_package"), dict):
            return ce_input, data["builder_executable_package"]
        if isinstance(data, dict) and data.get("schema") == CE_PACKAGE_SCHEMA:
            return ce_input, data
        diagnostics.append(diagnostic("PG.C2B.CE_PACKAGE_MISSING", "error", "CE Stage Evidence Bundle payload must contain a builder_executable_package object.", "$.payload.data"))
        return ce_input, None
    accepted_requires["envelope_valid_when_applicable"] = True
    if isinstance(ce_input.get("builder_executable_package"), dict):
        return None, ce_input["builder_executable_package"]
    return None, ce_input


def _ce_package_identity_diagnostics(ce_package: dict[str, Any] | None) -> list[Diagnostic]:
    if not isinstance(ce_package, dict):
        return [diagnostic("PG.C2B.CE_PACKAGE_NOT_OBJECT", "error", "CE Builder Executable Package must be an object.", "$.ce_builder_executable_package")]
    if ce_package.get("schema") != CE_PACKAGE_SCHEMA:
        return [diagnostic("PG.C2B.CE_PACKAGE_SCHEMA_MISMATCH", "error", "CE package schema identity must match the CE-owned Builder Executable Package contract.", "$.schema", expected=CE_PACKAGE_SCHEMA, actual=ce_package.get("schema"))]
    return []


def _real_evidence_diagnostics(source_bundle: dict[str, Any] | None, require_real_evidence: bool) -> list[Diagnostic]:
    if not require_real_evidence:
        return []
    if source_bundle is None:
        return [diagnostic("PG.C2B.REAL_EVIDENCE_REQUIRED", "insufficient_evidence", "Raw CE package input cannot count as real CE→Builder handoff evidence; provide a non-synthetic Stage Evidence Bundle.", "$")]
    if source_bundle.get("synthetic") is True:
        return [diagnostic("PG.C2B.SYNTHETIC_ONLY_EVIDENCE", "insufficient_evidence", "Synthetic CE fixture cannot count as real CE→Builder transition evidence.", "$.synthetic")]
    return []


def _builder_schema_validation_diagnostics(builder_context_package: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    try:
        schema = json.loads(source.read_bytes(BUILDER_REPO, BUILDER_COMMIT, "schemas/builder-context-package.schema.json").decode("utf-8"))
    except Exception as exc:
        return [diagnostic("PG.C2B.BUILDER_SCHEMA_UNAVAILABLE", "insufficient_evidence", "Builder-owned output schema could not be read.", "$.builder_output", error_type=type(exc).__name__)]
    return [diagnostic("PG.C2B.BUILDER_SCHEMA_VALIDATION_FAILED", "error", err.message, _json_path(list(err.path))) for err in sorted(Draft202012Validator(schema).iter_errors(builder_context_package), key=lambda e: (_json_path(list(e.path)), e.message))]


def _accepted_requires_template() -> dict[str, bool]:
    return {"input_parses": False, "envelope_valid_when_applicable": False, "ce_package_identity_verified": False, "ce_producer_pin_hash_matches": False, "builder_consumer_pin_hash_matches": False, "official_ce_validator_passed": False, "builder_contract_gate_passed": False, "official_builder_adapter_passed": False, "builder_output_validates": False, "required_evidence_present": False, "no_forbidden_claim": True, "result_schema_validated": True, "synthetic_only_evidence_not_used_as_real_evidence": False}


def _result(original_input: Any, source_bundle: dict[str, Any] | None, ce_package: dict[str, Any] | None, builder_context_package: dict[str, Any] | None, diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], execution_records: dict[str, dict[str, Any]], config: CeToBuilderTransitionConfig) -> dict[str, Any]:
    if builder_context_package is not None:
        accepted_requires["official_builder_adapter_passed"] = accepted_requires["official_builder_adapter_passed"] and builder_context_package.get("schema") == BUILDER_CONTEXT_SCHEMA
    missing = sorted(key for key, ok in accepted_requires.items() if not ok)
    local = list(diagnostics)
    if not _has_blocking(local) and missing:
        local.append(diagnostic("PG.C2B.ACCEPTED_REQUIRES_MISSING", "insufficient_evidence", "CE→Builder transition cannot be accepted until every accepted_requires item is true.", "$.accepted_requires", missing_requires=missing))
    ordered = sort_diagnostics(local)
    status = project_gate_status_from_diagnostics(ordered)
    result = {"schema_version": "ce-to-builder-transition-result.v1", "result_type": "ce_to_builder_transition", "transition": {"id": TRANSITION_ID, "version": TRANSITION_VERSION, "source_payload_schema": CE_PACKAGE_SCHEMA, "target_payload_schema": BUILDER_CONTEXT_SCHEMA}, "status": status, "source_stage": "ce", "target_stage": "builder", "accepted_requires": accepted_requires, "diagnostics": [item.to_dict() for item in ordered], "hashes": {"input": _hash_or_none(original_input, "input"), "source_bundle": _hash_or_none(source_bundle, "source_bundle"), "ce_package": _hash_or_none(ce_package, "ce_package"), "builder_context_package": _hash_or_none(builder_context_package, "builder_context_package"), "external_contract_lock": {"algorithm": "sha256", "canonicalization": CANONICAL_JSON_VERSION, "scope": "external_contract_lock", "value": canonical_sha256(config.lock)}}, "execution_records": execution_records, "provenance": {"producer_repository": PG_REPO, "source_bundle_id": source_bundle.get("bundle_id") if isinstance(source_bundle, dict) else None, "transition_id": TRANSITION_ID, "verification_state": "live_owner_tools_required"}, "output": builder_context_package if status == "accepted" else None}
    _validate_transition_result(result, config.schema_root)
    return result


def _validate_transition_result(result: dict[str, Any], schema_root: Path) -> None:
    schema = load_json_file(schema_root / "ce-to-builder-transition-result" / "ce-to-builder-transition-result.v1.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(result), key=lambda e: (_json_path(list(e.path)), e.message))
    if errors:
        raise ResultValidationError("; ".join(f"{_json_path(list(err.path))}: {err.message}" for err in errors))


def _hash_or_none(value: Any, scope: str) -> dict[str, str] | None:
    if value is None:
        return None
    try:
        return {"algorithm": "sha256", "canonicalization": CANONICAL_JSON_VERSION, "scope": scope, "value": canonical_sha256(value)}
    except CanonicalJsonError:
        return None


def _import_diags(items: list[dict[str, Any]]) -> list[Diagnostic]:
    return [diagnostic(str(item.get("code", "SCHEMA_VALIDATION_FAILED")), str(item.get("severity", "error")), str(item.get("message", "Imported Project Gate diagnostic.")), str(item.get("path", "$")), **(item.get("details") if isinstance(item.get("details"), dict) else {})) for item in items]


def _has_error(items: list[Diagnostic]) -> bool:
    return any(item.severity == "error" for item in items)


def _has_insufficient(items: list[Diagnostic]) -> bool:
    return any(item.severity == "insufficient_evidence" for item in items)


def _has_blocking(items: list[Diagnostic]) -> bool:
    return _has_error(items) or _has_insufficient(items)


def _has_forbidden_claim(ce_package: dict[str, Any] | None, builder_context_package: dict[str, Any] | None) -> bool:
    forbidden_keys = {"production_ready", "builder_runtime_authorized", "production_ready_allowed"}

    def scan(value: Any) -> bool:
        if isinstance(value, dict):
            return any((key in forbidden_keys and item is True) or scan(item) for key, item in value.items())
        if isinstance(value, list):
            return any(scan(item) for item in value)
        return False

    return scan(ce_package) or scan(builder_context_package)


def _json_path(parts: list[Any]) -> str:
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out
