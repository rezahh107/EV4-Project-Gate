from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256, canonical_sha256, load_json_file
from ev4_transition.contract_source import ContractSource, LocalCheckoutContractSource
from ev4_transition.diagnostics import Diagnostic, diagnostic, project_gate_status_from_diagnostics, sort_diagnostics
from ev4_transition.evidence_truth import EvidenceResolution, resolve_evidence, synthetic_indicators
from ev4_transition.runners.responsive_tools import execute_responsive_input_boundary_validator
from ev4_transition.runners.subprocess_runner import execute_official_tool

TRANSITION_ID = "ev4-builder-to-responsive-transition@1.0.0"
TRANSITION_VERSION = "1.1.0"
LOCK_SCHEMA_VERSION = "builder-to-responsive-transition-lock.v1"
BUILDER_REPO = "rezahh107/EV4-Builder-Assistant-Repo"
RESPONSIVE_REPO = "rezahh107/EV4-Responsive-Architect"
BUILDER_COMMIT = "69a2c61edf6d06b4418ad770fcefbfdffcf275d6"
RESPONSIVE_COMMIT = "df74c7ba2ffbed1a4136b5ea6be6ce30db4e161a"
RESPONSIVE_INPUT_SCHEMA = "ev4-builder-responsive-input@0.1.0"
RESPONSIVE_INPUT_SCHEMA_PATH = "schemas/ev4-builder-responsive-input.schema.json"
RESPONSIVE_INPUT_VALIDATOR = "validation/e2e/run_builder_responsive_input_boundary_check.py"

FORBIDDEN_CLAIMS = {
    "production_ready", "release_ready", "pixel_perfect", "live_render_validated",
    "export_json_validated", "accessibility_passed", "responsive_correctness_validated",
    "ci_success_as_frontend_evidence", "frontend_correctness", "production_readiness",
    "responsive_correctness",
}


@dataclass(frozen=True)
class ExpectedDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str
    identity_marker: str


_EXPECTED_ITEMS = [
    ExpectedDependency("builder_handoff_boundary", BUILDER_REPO, BUILDER_COMMIT, "docs/BUILDER_TO_RESPONSIVE_HANDOFF_BOUNDARY.md", "builder-to-responsive-handoff-boundary@0.1.0", "Builder"),
    ExpectedDependency("builder_context_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/builder-context-package.schema.json", "ev4-builder-context-package@1.0.0", "ev4-builder-context-package"),
    ExpectedDependency("builder_context_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-package.mjs", "builder-context-validator", "validate"),
    ExpectedDependency("builder_action_batch_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/action-batch.schema.json", "ev4-action-batch@1.0.0", "action"),
    ExpectedDependency("builder_action_batch_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-action-batch.mjs", "validate-action-batch", "action"),
    ExpectedDependency("builder_layout_check_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/layout-check.schema.json", "ev4-layout-check@0.1.0", "layout"),
    ExpectedDependency("builder_layout_check_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-layout-check.mjs", "validate-layout-check", "layout"),
    ExpectedDependency("builder_completion_gate_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/completion-gate.schema.json", "ev4-completion-gate@0.1.0", "completion"),
    ExpectedDependency("builder_completion_gate_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-completion-gate.mjs", "validate-completion-gate", "completion"),
    ExpectedDependency("builder_execution_evidence_schema", BUILDER_REPO, BUILDER_COMMIT, "schemas/real-elementor-execution-evidence.schema.json", "ev4-real-elementor-execution-evidence@1.0.0", "evidence"),
    ExpectedDependency("builder_execution_evidence_validator", BUILDER_REPO, BUILDER_COMMIT, "scripts/validate-real-elementor-execution-evidence.mjs", "validate-real-elementor-execution-evidence", "evidence"),
    ExpectedDependency("responsive_input_boundary", RESPONSIVE_REPO, RESPONSIVE_COMMIT, "contracts/BUILDER_TO_RESPONSIVE_INPUT_BOUNDARY.md", "builder-responsive-input-boundary", "Builder"),
    ExpectedDependency("responsive_input_schema", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_INPUT_SCHEMA_PATH, RESPONSIVE_INPUT_SCHEMA, "builder-responsive"),
    ExpectedDependency("responsive_input_validator", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_INPUT_VALIDATOR, "builder-responsive-input-boundary-validator", "boundary"),
]
EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES = {item.role: item for item in _EXPECTED_ITEMS}
REQUIRED_ROLES = set(EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES)


@dataclass(frozen=True)
class BuilderToResponsiveTransitionConfig:
    schema_root: Path
    lock: dict[str, Any]
    builder_repo_root: Path | None = None
    responsive_repo_root: Path | None = None
    timeout_seconds: float = 30
    require_real_evidence: bool = True


def verify_builder_to_responsive_lock(lock: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG.B2R.LOCK_NOT_OBJECT", "error", "Builder→Responsive lock manifest must be an object.", "$")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG.B2R.LOCK_VERSION_MISMATCH", "error", "Builder→Responsive lock schema version is missing or unknown.", "$.schema_version", expected=LOCK_SCHEMA_VERSION, actual=lock.get("schema_version")))
    if lock.get("transition_id") != TRANSITION_ID:
        diagnostics.append(diagnostic("PG.B2R.LOCK_TRANSITION_ID_MISMATCH", "error", "Builder→Responsive lock transition id does not match this transition.", "$.transition_id", expected=TRANSITION_ID, actual=lock.get("transition_id")))
    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG.B2R.LOCK_FILES_NOT_ARRAY", "error", "Builder→Responsive lock files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG.B2R.LOCK_ENTRY_NOT_OBJECT", "error", "Lock entry must be an object.", path))
            continue
        role = item.get("role")
        if not isinstance(role, str):
            diagnostics.append(diagnostic("PG.B2R.LOCK_ROLE_UNEXPECTED", "error", "Lock entry role must be a string.", f"{path}.role", observed_type=type(role).__name__))
            continue
        expected = EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES.get(role)
        if expected is None:
            diagnostics.append(diagnostic("PG.B2R.LOCK_ROLE_UNEXPECTED", "error", "Unexpected lock role.", f"{path}.role", role=role))
            continue
        if role in seen:
            diagnostics.append(diagnostic("PG.B2R.LOCK_ROLE_DUPLICATE", "error", "Duplicate lock role.", f"{path}.role", role=role))
        seen.add(role)
        for field, expected_value, code in [
            ("repository", expected.repository, "PG.B2R.LOCK_REPOSITORY_MISMATCH"),
            ("accepted_commit", expected.accepted_commit, "PG.B2R.LOCK_COMMIT_MISMATCH"),
            ("path", expected.path, "PG.B2R.LOCK_PATH_MISMATCH"),
            ("contract_or_schema_id", expected.contract_or_schema_id, "PG.B2R.LOCK_IDENTITY_MISMATCH"),
        ]:
            if item.get(field) != expected_value:
                diagnostics.append(diagnostic(code, "error", "Lock entry does not match expected dependency.", f"{path}.{field}", expected=expected_value, actual=item.get(field), role=role))
        try:
            content = source.read_bytes(expected.repository, expected.accepted_commit, expected.path)
        except Exception as exc:
            diagnostics.append(diagnostic("PG.B2R.OWNER_FILE_READ_FAILED", "insufficient_evidence", "Pinned owner file could not be read.", path, role=role, repository=expected.repository, file_path=expected.path, error_type=type(exc).__name__))
            continue
        if item.get("sha256_file_bytes") != bytes_sha256(content):
            diagnostics.append(diagnostic("PG.B2R.EXTERNAL_HASH_MISMATCH", "error", "Pinned owner file hash does not match lock manifest.", path, role=role, repository=expected.repository, file_path=expected.path))
        if expected.identity_marker not in content.decode("utf-8", errors="replace"):
            diagnostics.append(diagnostic("PG.B2R.EXTERNAL_IDENTITY_MISMATCH", "error", "Pinned owner file identity marker was not found.", path, role=role, repository=expected.repository, file_path=expected.path, expected_marker=expected.identity_marker))
    missing = sorted(REQUIRED_ROLES - seen)
    if missing:
        diagnostics.append(diagnostic("PG.B2R.LOCK_ROLE_MISSING", "error", "Builder→Responsive lock is missing required owner dependency roles.", "$.files", missing_roles=missing))
    return sort_diagnostics(diagnostics)


def transition_from_local_paths(builder_input: Any, schema_root: str | Path, lock_path: str | Path, builder_repo: str | Path, responsive_repo: str | Path, *, timeout_seconds: float = 30, require_real_evidence: bool = True) -> dict[str, Any]:
    config = BuilderToResponsiveTransitionConfig(Path(schema_root), load_json_file(lock_path), Path(builder_repo), Path(responsive_repo), timeout_seconds, require_real_evidence)
    source = LocalCheckoutContractSource({BUILDER_REPO: Path(builder_repo), RESPONSIVE_REPO: Path(responsive_repo)})
    return transition_builder_to_responsive(builder_input, source, config)


def transition_builder_to_responsive(builder_input: Any, contract_source: ContractSource, config: BuilderToResponsiveTransitionConfig, progress_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    accepted_requires = {
        "builder_evidence_refs_present": False,
        "evidence_sources_resolved": False,
        "evidence_hashes_verified": False,
        "owner_validators_passed": False,
        "claim_bindings_valid": False,
        "builder_lock_hashes_match": False,
        "responsive_input_schema_verified": False,
        "responsive_input_validator_passed": False,
        "viewport_evidence_present": False,
        "no_forbidden_claim": False,
        "synthetic_only_evidence_not_used_as_real_evidence": False,
        "result_schema_valid": False,
    }
    resolutions: dict[str, EvidenceResolution] = {}

    if not isinstance(builder_input, dict):
        diagnostics.append(diagnostic("PG.B2R.INPUT_NOT_OBJECT", "error", "Builder→Responsive input must be an object.", "$", observed_type=type(builder_input).__name__))
        return _result(builder_input, None, diagnostics, accepted_requires, config, resolutions)
    responsive_input = builder_input.get("responsive_input") if isinstance(builder_input.get("responsive_input"), dict) else builder_input
    if not isinstance(responsive_input, dict):
        diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_INPUT_MISSING", "insufficient_evidence", "Responsive input packet is missing.", "$.responsive_input"))
        return _result(builder_input, None, diagnostics, accepted_requires, config, resolutions)

    lock_diags = verify_builder_to_responsive_lock(config.lock, contract_source)
    diagnostics.extend(lock_diags)
    accepted_requires["builder_lock_hashes_match"] = not any(d.severity in {"error", "insufficient_evidence"} for d in lock_diags)

    forbidden = _find_forbidden_claims(builder_input)
    if forbidden:
        diagnostics.append(diagnostic("PG.B2R.FORBIDDEN_CLAIM", "error", "Builder→Responsive input contains forbidden readiness/correctness claims.", "$", forbidden_claims=forbidden))
    accepted_requires["no_forbidden_claim"] = not forbidden
    if _contains_key_or_value(builder_input, "ci_success_as_frontend_evidence"):
        diagnostics.append(diagnostic("PG.B2R.CI_FRONTEND_CORRECTNESS_CLAIM", "error", "CI success is not frontend correctness evidence.", "$"))
    if _contains_key_or_value(builder_input, "raw_screenshot") or _contains_key_or_value(builder_input, "screenshot_only"):
        diagnostics.append(diagnostic("PG.B2R.RAW_SCREENSHOT_CORRECTNESS_CLAIM", "insufficient_evidence", "Raw screenshots alone do not prove responsive correctness.", "$"))

    evidence_missing = _missing_builder_evidence(responsive_input)
    if evidence_missing:
        diagnostics.append(diagnostic("PG.B2R.BUILDER_EVIDENCE_MISSING", "insufficient_evidence", "Required Builder evidence references are missing.", "$.builder_evidence", missing_evidence=evidence_missing))
    accepted_requires["builder_evidence_refs_present"] = not evidence_missing
    viewport_missing = _missing_viewport_evidence(responsive_input)
    if viewport_missing:
        diagnostics.append(diagnostic("PG.B2R.VIEWPORT_EVIDENCE_MISSING", "insufficient_evidence", "Viewport evidence is required before accepted Responsive intake.", "$.viewport_evidence", missing_viewports=viewport_missing))
    accepted_requires["viewport_evidence_present"] = not viewport_missing

    bindings = builder_input.get("evidence_bindings") if isinstance(builder_input.get("evidence_bindings"), dict) else {}
    subject = builder_input.get("evidence_subject") if isinstance(builder_input.get("evidence_subject"), dict) else {}
    if not bindings:
        diagnostics.append(diagnostic("PG.B2R.EVIDENCE_BINDINGS_REQUIRED", "insufficient_evidence", "Project Gate evidence bindings are required; reference strings alone cannot authorize B2R.", "$.evidence_bindings"))
    elif config.builder_repo_root is None:
        diagnostics.append(diagnostic("PG.B2R.BUILDER_REPO_REQUIRED", "insufficient_evidence", "Builder checkout is required to resolve and validate evidence bytes.", "$.evidence_bindings"))
    else:
        slot_specs = _binding_specs(responsive_input)
        for slot, spec in slot_specs.items():
            binding = bindings.get(slot)
            if not isinstance(binding, dict):
                diagnostics.append(diagnostic("PG.B2R.EVIDENCE_BINDING_MISSING", "insufficient_evidence", "Required evidence binding is missing.", f"$.evidence_bindings.{slot}", slot=slot))
                continue
            owner_callback = _owner_validator_callback(config, spec["validator_role"], progress_sink) if spec.get("validator_role") else None
            resolution = resolve_evidence(
                artifact_ref=binding.get("artifact_ref"),
                declared_sha256=binding.get("artifact_sha256"),
                repository_root=config.builder_repo_root,
                hash_scope="file_bytes",
                owner_repository=BUILDER_REPO,
                owner_commit=BUILDER_COMMIT,
                owner_validator=(EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES[spec["validator_role"]].path if spec.get("validator_role") else None),
                owner_validator_callback=owner_callback,
                claim_id=spec["claim_class"],
                evidence_type=spec["evidence_type"],
                subject_ref=binding.get("subject_ref"),
                expected_subject_ref=spec["subject_ref"],
                viewport=spec.get("viewport"),
            )
            resolutions[slot] = resolution
            diagnostics.extend(_resolution_diagnostics(slot, resolution))
            if resolution.value is not None:
                diagnostics.extend(_owner_schema_diagnostics(contract_source, spec.get("schema_role"), resolution.value, slot))
                diagnostics.extend(_subject_binding_diagnostics(slot, spec, binding, resolution.value, responsive_input, subject))

        required_slots = set(slot_specs)
        all_present = required_slots <= set(resolutions)
        accepted_requires["evidence_sources_resolved"] = all_present and all(item.source_path for item in resolutions.values())
        accepted_requires["evidence_hashes_verified"] = all_present and all(item.hash_verified for item in resolutions.values())
        accepted_requires["owner_validators_passed"] = all_present and all(item.owner_validation_status in {"accepted", "not_available"} for item in resolutions.values())
        accepted_requires["claim_bindings_valid"] = all_present and not any(d.code.startswith("PG.B2R.BINDING_") or d.code.startswith("PG.EVIDENCE.CLAIM_") for d in diagnostics if d.severity == "error")
        real_verified = all_present and all(item.classification == "real_verified" for item in resolutions.values())
        accepted_requires["synthetic_only_evidence_not_used_as_real_evidence"] = real_verified
        if config.require_real_evidence and not real_verified:
            diagnostics.append(diagnostic("PG.B2R.REAL_VERIFIED_EVIDENCE_REQUIRED", "insufficient_evidence", "B2R operational authorization requires resolved, hash-verified, owner-validated, non-synthetic evidence.", "$.evidence_bindings"))

    if synthetic_indicators(builder_input):
        accepted_requires["synthetic_only_evidence_not_used_as_real_evidence"] = False
        diagnostics.append(diagnostic("PG.B2R.SYNTHETIC_ONLY_EVIDENCE", "insufficient_evidence", "Synthetic fixtures cannot be used as real Responsive evidence.", "$", indicators=synthetic_indicators(builder_input)))

    schema = _load_responsive_schema(contract_source, diagnostics)
    if schema is not None:
        accepted_requires["responsive_input_schema_verified"] = True
        for err in sorted(Draft202012Validator(schema).iter_errors(responsive_input), key=lambda item: (list(item.path), item.message)):
            diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_SCHEMA_VALIDATION_FAILED", "error", err.message, _json_path(list(err.path))))
    validator_ok = _run_responsive_validator(config, responsive_input, diagnostics, progress_sink)
    accepted_requires["responsive_input_validator_passed"] = validator_ok
    return _result(builder_input, responsive_input, diagnostics, accepted_requires, config, resolutions)


def _binding_specs(responsive_input: dict[str, Any]) -> dict[str, dict[str, Any]]:
    builder = responsive_input.get("builder_evidence") if isinstance(responsive_input.get("builder_evidence"), dict) else {}
    viewport = responsive_input.get("viewport_evidence") if isinstance(responsive_input.get("viewport_evidence"), dict) else {}
    output_ref = responsive_input.get("builder_output_ref") if isinstance(responsive_input.get("builder_output_ref"), dict) else {}
    specs: dict[str, dict[str, Any]] = {
        "builder_output": {"subject_ref": output_ref.get("artifact_ref"), "claim_class": "builder_completion_verified", "evidence_type": "completion_gate", "schema_role": "builder_context_schema", "validator_role": "builder_context_validator"},
        "action_batch": {"subject_ref": builder.get("action_batch_ref"), "claim_class": "builder_completion_verified", "evidence_type": "action_batch", "schema_role": "builder_action_batch_schema", "validator_role": "builder_action_batch_validator"},
        "execution_evidence": {"subject_ref": builder.get("execution_evidence_ref"), "claim_class": "execution_evidence_verified", "evidence_type": "execution_evidence", "schema_role": "builder_execution_evidence_schema", "validator_role": "builder_execution_evidence_validator"},
        "layout_check": {"subject_ref": builder.get("layout_check_ref"), "claim_class": "builder_completion_verified", "evidence_type": "layout_check", "schema_role": "builder_layout_check_schema", "validator_role": "builder_layout_check_validator"},
        "completion_gate": {"subject_ref": builder.get("completion_gate_ref"), "claim_class": "builder_completion_verified", "evidence_type": "completion_gate", "schema_role": "builder_completion_gate_schema", "validator_role": "builder_completion_gate_validator"},
    }
    for name in ("desktop", "tablet", "mobile"):
        item = viewport.get(name) if isinstance(viewport.get(name), dict) else {}
        specs[name] = {"subject_ref": item.get("evidence_ref"), "claim_class": f"{name}_evidence_verified", "evidence_type": "viewport_evidence", "viewport": name, "schema_role": None, "validator_role": None}
    return specs


def _owner_validator_callback(config: BuilderToResponsiveTransitionConfig, role: str, progress_sink: list[dict[str, Any]] | None) -> Callable[[Path, Any], tuple[str, list[dict[str, Any]]]]:
    dep = EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES[role]
    def run(path: Path, _: Any) -> tuple[str, list[dict[str, Any]]]:
        assert config.builder_repo_root is not None
        outcome = execute_official_tool(
            tool_kind="validator",
            owner_repo=BUILDER_REPO,
            owner_commit=BUILDER_COMMIT,
            tool_path=dep.path,
            command=["node", str(Path(config.builder_repo_root).resolve() / dep.path), str(path)],
            working_directory=config.builder_repo_root,
            timeout_seconds=config.timeout_seconds,
            parsed_result_ref="stdout:text",
            progress_sink=progress_sink,
        )
        return ("accepted" if outcome.status == "accepted" else "rejected", [item.to_dict() for item in outcome.diagnostics])
    return run


def _owner_schema_diagnostics(source: ContractSource, role: str | None, value: Any, slot: str) -> list[Diagnostic]:
    if role is None:
        return []
    dep = EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES[role]
    try:
        schema = json.loads(source.read_bytes(dep.repository, dep.accepted_commit, dep.path).decode("utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [diagnostic("PG.B2R.OWNER_SCHEMA_UNAVAILABLE", "insufficient_evidence", f"$.evidence_bindings.{slot}", "Pinned Builder schema is unavailable.", role=role, error_type=type(exc).__name__)]
    return [diagnostic("PG.B2R.OWNER_SCHEMA_INVALID", "error", error.message, f"$.evidence_bindings.{slot}{_json_path(list(error.path))[1:]}", role=role) for error in sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: (list(item.path), item.message))]


def _subject_binding_diagnostics(slot: str, spec: dict[str, Any], binding: dict[str, Any], value: Any, responsive_input: dict[str, Any], subject: dict[str, Any]) -> list[Diagnostic]:
    d: list[Diagnostic] = []
    if not isinstance(value, dict):
        return [diagnostic("PG.B2R.BINDING_VALUE_NOT_OBJECT", "error", "Referenced evidence JSON must be an object.", f"$.evidence_bindings.{slot}")]
    selected = responsive_input.get("selected_candidate_id")
    artifact_selected = value.get("selected_candidate_id")
    if artifact_selected is not None and selected is not None and artifact_selected != selected:
        d.append(diagnostic("PG.B2R.BINDING_SELECTED_CANDIDATE_MISMATCH", "error", "Evidence selected_candidate_id does not match Responsive intake.", f"$.evidence_bindings.{slot}", expected=selected, actual=artifact_selected))
    if subject.get("builder_session_ref") and value.get("builder_session_ref") is not None and value.get("builder_session_ref") != subject.get("builder_session_ref"):
        d.append(diagnostic("PG.B2R.BINDING_SESSION_MISMATCH", "error", "Evidence Builder session does not match the bound session.", f"$.evidence_bindings.{slot}"))
    if subject.get("source_package_ref") and value.get("source_package_ref") is not None and value.get("source_package_ref") != subject.get("source_package_ref"):
        d.append(diagnostic("PG.B2R.BINDING_PACKAGE_MISMATCH", "error", "Evidence source package does not match the bound package.", f"$.evidence_bindings.{slot}"))
    if slot == "action_batch" and subject.get("action_set_digest") and canonical_sha256(value) != subject.get("action_set_digest"):
        d.append(diagnostic("PG.B2R.BINDING_ACTION_SET_MISMATCH", "error", "Action Batch digest does not match the bound action set.", f"$.evidence_bindings.{slot}"))
    if slot == "completion_gate":
        expected_layout = ((responsive_input.get("builder_evidence") or {}).get("layout_check_ref"))
        if value.get("layout_check_ref") != expected_layout:
            d.append(diagnostic("PG.B2R.BINDING_LAYOUT_CHECK_MISMATCH", "error", "Completion Gate is not bound to the declared Layout Check.", f"$.evidence_bindings.{slot}"))
    if slot in {"desktop", "tablet", "mobile"}:
        if value.get("evidence_ref") != spec.get("subject_ref") or value.get("viewport") != slot or value.get("status") != "confirmed":
            d.append(diagnostic("PG.B2R.BINDING_VIEWPORT_MISMATCH", "error", "Viewport evidence must bind the exact ref, viewport, and confirmed status.", f"$.evidence_bindings.{slot}"))
    if slot == "builder_output":
        declared = ((responsive_input.get("builder_output_ref") or {}).get("artifact_hash"))
        if declared and binding.get("artifact_sha256") != declared:
            d.append(diagnostic("PG.B2R.BINDING_BUILDER_OUTPUT_HASH_MISMATCH", "error", "Builder output hash differs between Responsive input and evidence binding.", f"$.evidence_bindings.{slot}.artifact_sha256"))
    return d


def _resolution_diagnostics(slot: str, resolution: EvidenceResolution) -> list[Diagnostic]:
    result: list[Diagnostic] = []
    for item in resolution.diagnostics:
        details = dict(item.get("details") or {})
        details["slot"] = slot
        result.append(diagnostic(item["code"], item["severity"], item["message"], f"$.evidence_bindings.{slot}", **details))
    return result


def _load_responsive_schema(source: ContractSource, diagnostics: list[Diagnostic]) -> dict[str, Any] | None:
    try:
        raw = source.read_bytes(RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_INPUT_SCHEMA_PATH)
        schema = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_SCHEMA_UNAVAILABLE", "insufficient_evidence", "Responsive-owned input schema is absent or unreadable.", "$.responsive_schema", error_type=type(exc).__name__))
        return None
    return schema if isinstance(schema, dict) else None


def _run_responsive_validator(config: BuilderToResponsiveTransitionConfig, responsive_input: dict[str, Any], diagnostics: list[Diagnostic], progress_sink: list[dict[str, Any]] | None) -> bool:
    if config.responsive_repo_root is None:
        diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_VALIDATOR_MISSING", "insufficient_evidence", "Responsive repository checkout is required to run the official input boundary validator.", "$.responsive_validator"))
        return False
    validator = Path(config.responsive_repo_root) / RESPONSIVE_INPUT_VALIDATOR
    if not validator.exists():
        diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_VALIDATOR_MISSING", "insufficient_evidence", "Official Responsive input boundary validator is absent.", "$.responsive_validator", validator_path=RESPONSIVE_INPUT_VALIDATOR))
        return False
    outcome = execute_responsive_input_boundary_validator(repo_root=config.responsive_repo_root, owner_repo=RESPONSIVE_REPO, owner_commit=RESPONSIVE_COMMIT, validator_path=RESPONSIVE_INPUT_VALIDATOR, responsive_input=responsive_input, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)
    diagnostics.extend(outcome.diagnostics)
    if outcome.status != "accepted":
        diagnostics.append(diagnostic("PG.B2R.RESPONSIVE_VALIDATOR_FAILED", "insufficient_evidence", "Official Responsive input boundary validator did not pass.", "$.responsive_validator", runner_status=outcome.status, failure_code=outcome.execution_record.failure_code))
        return False
    return True


def _result(original: Any, responsive_input: dict[str, Any] | None, diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], config: BuilderToResponsiveTransitionConfig, resolutions: dict[str, EvidenceResolution]) -> dict[str, Any]:
    ordered = sort_diagnostics(diagnostics)
    accepted = {**accepted_requires, "result_schema_valid": True}
    if not ordered and not all(accepted.values()):
        missing = sorted(key for key, value in accepted.items() if not value)
        ordered = sort_diagnostics([diagnostic("PG.B2R.ACCEPTED_REQUIRES_MISSING", "insufficient_evidence", "Accepted status requires every accepted_requires item to be true.", "$.accepted_requires", missing=missing)])
    status = project_gate_status_from_diagnostics(ordered)
    result = {
        "schema_version": "builder-to-responsive-transition-result.v1",
        "result_type": "builder_to_responsive_transition",
        "transition_id": TRANSITION_ID,
        "transition_version": TRANSITION_VERSION,
        "status": status,
        "diagnostics": [item.to_dict() for item in ordered],
        "accepted_requires": accepted,
        "evidence_resolutions": {name: item.to_dict() for name, item in sorted(resolutions.items())},
        "hashes": {"source_input_hash": {"algorithm": "sha256", "canonicalization": "ev4-canonical-json.v1", "scope": "source_input", "value": _safe_hash(original)}},
        "output": responsive_input if status == "accepted" else None,
    }
    schema_path = config.schema_root / "builder-to-responsive-transition-result" / "builder-to-responsive-transition-result.v1.schema.json"
    schema_diagnostics: list[Diagnostic] = []
    if not schema_path.exists():
        schema_diagnostics.append(diagnostic("PG.B2R.RESULT_SCHEMA_MISSING", "insufficient_evidence", "Builder→Responsive result schema is required.", "$.schema_version", schema_path=str(schema_path)))
    else:
        try:
            schema = load_json_file(schema_path)
            Draft202012Validator.check_schema(schema)
            for error in sorted(Draft202012Validator(schema).iter_errors(result), key=lambda item: (list(item.path), item.message)):
                schema_diagnostics.append(diagnostic("PG.B2R.RESULT_SCHEMA_VALIDATION_FAILED", "error", error.message, _json_path(list(error.path))))
        except Exception as exc:
            schema_diagnostics.append(diagnostic("PG.B2R.RESULT_SCHEMA_INVALID", "error", "Builder→Responsive result schema could not be validated.", "$.schema_version", error_type=type(exc).__name__))
    if schema_diagnostics:
        accepted["result_schema_valid"] = False
        ordered = sort_diagnostics([*ordered, *schema_diagnostics])
        result["status"] = project_gate_status_from_diagnostics(ordered)
        result["diagnostics"] = [item.to_dict() for item in ordered]
        result["accepted_requires"] = accepted
        result["output"] = None
    return result


def _missing_builder_evidence(value: dict[str, Any]) -> list[str]:
    evidence = value.get("builder_evidence") if isinstance(value.get("builder_evidence"), dict) else {}
    required = ["action_batch_ref", "execution_evidence_ref", "layout_check_ref", "completion_gate_ref"]
    return [key for key in required if not evidence.get(key)]


def _missing_viewport_evidence(value: dict[str, Any]) -> list[str]:
    viewport = value.get("viewport_evidence") if isinstance(value.get("viewport_evidence"), dict) else {}
    return [key for key in ["desktop", "tablet", "mobile"] if not isinstance(viewport.get(key), dict) or not viewport[key].get("evidence_ref")]


def _find_forbidden_claims(value: Any) -> list[str]:
    found: set[str] = set()
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key == "forbidden_claims":
                    continue
                if isinstance(key, str) and key in FORBIDDEN_CLAIMS:
                    found.add(key)
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str) and node.strip() in FORBIDDEN_CLAIMS:
            found.add(node.strip())
    walk(value)
    return sorted(found)


def _contains_key_or_value(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(
            key == needle or _contains_key_or_value(child, needle)
            for key, child in value.items()
            if key != "forbidden_claims"
        )
    if isinstance(value, list):
        return any(_contains_key_or_value(child, needle) for child in value)
    return value == needle


def _safe_hash(value: Any) -> str:
    try:
        return canonical_sha256(value)
    except Exception:
        return bytes_sha256(b"unhashable")


def _json_path(parts: list[Any]) -> str:
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out
