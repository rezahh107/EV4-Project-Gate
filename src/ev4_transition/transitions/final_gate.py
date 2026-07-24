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
from ev4_transition.final_gate_authority import _authoritative_final_gate_result
from ev4_transition.kernel_decision_dependencies import KERNEL_REPOSITORY
from ev4_transition.kernel_decision_intake import KernelAuditExecution, KernelDecisionIntakeConfig, run_kernel_decision_intake
from ev4_transition.runners.responsive_tools import execute_responsive_output_validator

GATE_ID = "ev4-final-evidence-gate@1.0.0"
GATE_VERSION = "1.1.0"
LOCK_SCHEMA_VERSION = "final-gate-lock.v1"
PG_REPO = "rezahh107/EV4-Project-Gate"
PG_COMMIT = "4cc6a90188eafb2232aaf100efa4af5f0ed5d997"
RESPONSIVE_REPO = "rezahh107/EV4-Responsive-Architect"
RESPONSIVE_COMMIT = "df74c7ba2ffbed1a4136b5ea6be6ce30db4e161a"
RESPONSIVE_OUTPUT_SCHEMA = "ev4-responsive-output@0.3.0"
RESPONSIVE_OUTPUT_SCHEMA_PATH = "schemas/ev4-responsive-output.schema.json"
RESPONSIVE_OUTPUT_VALIDATOR = "validation/e2e/run_responsive_tree_architecture_refactor_check.py"
KERNEL_INTAKE_LOCK_PATH = "contracts/locks/kernel-decision-intake.v1.lock.json"

REQUIRED_DECISION_LINEAGE_FIELDS = ("decision_family", "decision_card_ref", "selected_option", "rejected_options", "evidence_refs", "evidence_state", "consumer_stage")
FORBIDDEN_FINAL_CLAIMS = {"production_ready", "release_ready", "pixel_perfect", "live_render_validated", "export_json_validated", "export_validated", "accessibility_passed", "responsive_correctness_validated", "ci_success_as_frontend_evidence", "frontend_correctness", "production_readiness", "responsive_correctness"}


@dataclass(frozen=True)
class ExpectedDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str
    identity_marker: str


_EXPECTED_ITEMS = [
    ExpectedDependency("project_gate_a2c_lock", PG_REPO, PG_COMMIT, "contracts/locks/architect-to-ce-transition.v1.lock.json", "architect-to-ce-transition-lock.v1", "architect"),
    ExpectedDependency("project_gate_c2b_lock", PG_REPO, PG_COMMIT, "contracts/locks/ce-to-builder-transition.v1.lock.json", "ce-to-builder-transition-lock.v1", "ce-to-builder"),
    ExpectedDependency("project_gate_b2r_lock", PG_REPO, PG_COMMIT, "contracts/locks/builder-to-responsive-transition.v1.lock.json", "builder-to-responsive-transition-lock.v1", "builder-to-responsive"),
    ExpectedDependency("responsive_input_boundary", RESPONSIVE_REPO, RESPONSIVE_COMMIT, "contracts/BUILDER_TO_RESPONSIVE_INPUT_BOUNDARY.md", "builder-responsive-input-boundary", "Builder"),
    ExpectedDependency("responsive_output_schema", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_SCHEMA_PATH, RESPONSIVE_OUTPUT_SCHEMA, "responsive-output"),
    ExpectedDependency("responsive_output_validator", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_VALIDATOR, "responsive-output-validator", "responsive"),
]
EXPECTED_FINAL_GATE_DEPENDENCIES = {item.role: item for item in _EXPECTED_ITEMS}
REQUIRED_ROLES = set(EXPECTED_FINAL_GATE_DEPENDENCIES)


@dataclass(frozen=True)
class FinalGateConfig:
    schema_root: Path
    lock: dict[str, Any]
    project_gate_repo_root: Path | None = None
    responsive_repo_root: Path | None = None
    timeout_seconds: float = 30
    require_real_evidence: bool = True
    kernel_intake_lock: dict[str, Any] | None = None
    kernel_repo_root: Path | None = None
    kernel_audit_executor: Callable[[dict[str, Any]], KernelAuditExecution] | None = None


def verify_final_gate_lock(lock: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG.FINAL.LOCK_NOT_OBJECT", "error", "Final gate lock manifest must be an object.", "$")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_VERSION_MISMATCH", "error", "Final gate lock schema version is missing or unknown.", "$.schema_version", expected=LOCK_SCHEMA_VERSION, actual=lock.get("schema_version")))
    if lock.get("gate_id") != GATE_ID:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_TRANSITION_ID_MISMATCH", "error", "Final gate id does not match this gate.", "$.gate_id", expected=GATE_ID, actual=lock.get("gate_id")))
    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG.FINAL.LOCK_FILES_NOT_ARRAY", "error", "Final gate lock files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ENTRY_NOT_OBJECT", "error", "Lock entry must be an object.", path))
            continue
        role = item.get("role")
        if not isinstance(role, str):
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_UNEXPECTED", "error", "Final gate lock role must be a string.", f"{path}.role", observed_type=type(role).__name__))
            continue
        expected = EXPECTED_FINAL_GATE_DEPENDENCIES.get(role)
        if expected is None:
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_UNEXPECTED", "error", "Unexpected final gate lock role.", f"{path}.role", role=role))
            continue
        if role in seen:
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_DUPLICATE", "error", "Final gate lock contains a duplicate role.", f"{path}.role", role=role))
            continue
        seen.add(role)
        for field, expected_value, code in [
            ("repository", expected.repository, "PG.FINAL.LOCK_REPOSITORY_MISMATCH"),
            ("accepted_commit", expected.accepted_commit, "PG.FINAL.LOCK_COMMIT_MISMATCH"),
            ("path", expected.path, "PG.FINAL.LOCK_PATH_MISMATCH"),
            ("contract_or_schema_id", expected.contract_or_schema_id, "PG.FINAL.LOCK_IDENTITY_MISMATCH"),
        ]:
            if item.get(field) != expected_value:
                diagnostics.append(diagnostic(code, "error", "Final gate lock entry does not match expected dependency.", f"{path}.{field}", expected=expected_value, actual=item.get(field), role=role))
        try:
            content = source.read_bytes(expected.repository, expected.accepted_commit, expected.path)
        except Exception as exc:
            diagnostics.append(diagnostic("PG.FINAL.OWNER_FILE_READ_FAILED", "insufficient_evidence", "Pinned final gate owner file could not be read.", path, role=role, repository=expected.repository, file_path=expected.path, error_type=type(exc).__name__))
            continue
        if item.get("sha256_file_bytes") != bytes_sha256(content):
            diagnostics.append(diagnostic("PG.FINAL.EXTERNAL_HASH_MISMATCH", "error", "Pinned final gate file hash does not match lock manifest.", path, role=role, repository=expected.repository, file_path=expected.path))
        if expected.identity_marker not in content.decode("utf-8", errors="replace"):
            diagnostics.append(diagnostic("PG.FINAL.EXTERNAL_IDENTITY_MISMATCH", "error", "Pinned final gate identity marker was not found.", path, role=role, repository=expected.repository, file_path=expected.path))
    missing = sorted(REQUIRED_ROLES - seen)
    if missing:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_MISSING", "error", "Final gate lock is missing required owner dependency roles.", "$.files", missing_roles=missing))
    return sort_diagnostics(diagnostics)


def final_gate_from_local_paths(final_input: Any, schema_root: str | Path, lock_path: str | Path, project_gate_repo: str | Path, responsive_repo: str | Path, *, kernel_repo: str | Path | None = None, timeout_seconds: float = 30, require_real_evidence: bool = True) -> dict[str, Any]:
    project_gate_root = Path(project_gate_repo)
    responsive_root = Path(responsive_repo)
    kernel_root = Path(kernel_repo) if kernel_repo is not None else None
    kernel_lock_path = project_gate_root / KERNEL_INTAKE_LOCK_PATH
    kernel_lock = load_json_file(kernel_lock_path) if kernel_lock_path.is_file() else None
    config = FinalGateConfig(Path(schema_root), load_json_file(lock_path), project_gate_root, responsive_root, timeout_seconds, require_real_evidence, kernel_lock, kernel_root)
    roots = {PG_REPO: project_gate_root, RESPONSIVE_REPO: responsive_root}
    if kernel_root is not None:
        roots[KERNEL_REPOSITORY] = kernel_root
    return run_final_gate(final_input, LocalCheckoutContractSource(roots), config)


def run_final_gate(final_input: Any, contract_source: ContractSource, config: FinalGateConfig, progress_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    accepted_requires = {
        "prior_lock_chain_verified": False,
        "responsive_output_present": False,
        "responsive_output_schema_verified": False,
        "responsive_output_validator_passed": False,
        "evidence_sources_resolved": False,
        "evidence_hashes_verified": False,
        "claim_bindings_valid": False,
        "required_viewports_verified": False,
        "real_evidence_present": False,
        "blocking_unknowns_absent": False,
        "no_forbidden_final_claim": False,
        "kernel_decision_intake_accepted": False,
        "decision_lineage_projection_valid": False,
        "result_schema_valid": True,
    }
    kernel_intake_result: dict[str, Any] | None = None
    resolutions: dict[str, EvidenceResolution] = {}
    if not isinstance(final_input, dict):
        diagnostics.append(diagnostic("PG.FINAL.INPUT_NOT_OBJECT", "error", "Final gate input must be an object.", "$", observed_type=type(final_input).__name__))
        return _result(final_input, None, kernel_intake_result, diagnostics, accepted_requires, config, resolutions)
    output = final_input.get("responsive_output") if isinstance(final_input.get("responsive_output"), dict) else final_input
    if not isinstance(output, dict):
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_OUTPUT_MISSING", "insufficient_evidence", "Responsive output evidence is missing.", "$.responsive_output"))
        return _result(final_input, None, kernel_intake_result, diagnostics, accepted_requires, config, resolutions)
    accepted_requires["responsive_output_present"] = True

    lock_diagnostics = verify_final_gate_lock(config.lock, contract_source)
    diagnostics.extend(lock_diagnostics)
    accepted_requires["prior_lock_chain_verified"] = not any(item.severity in {"error", "insufficient_evidence"} for item in lock_diagnostics)
    forbidden = _find_forbidden_claims(final_input)
    if forbidden:
        diagnostics.append(diagnostic("PG.FINAL.FORBIDDEN_CLAIM", "error", "Final gate input contains forbidden readiness/correctness claims.", "$", forbidden_claims=forbidden))
    accepted_requires["no_forbidden_final_claim"] = not forbidden
    if _contains_key_or_value(final_input, "ci_success_as_frontend_evidence"):
        diagnostics.append(diagnostic("PG.FINAL.CI_FRONTEND_CORRECTNESS_CLAIM", "error", "CI success is not frontend correctness evidence.", "$"))

    raw_intake = final_input.get("kernel_decision_intake")
    supplied_projection = final_input.get("kernel_decision_intake_result")
    if raw_intake is None:
        diagnostics.append(diagnostic("PG.FINAL.KERNEL_INTAKE_REQUIRED", "error", "Final Gate requires the raw KROAD-011 Kernel decision intake Stage Evidence Bundle.", "$.kernel_decision_intake"))
    elif not isinstance(raw_intake, dict):
        diagnostics.append(diagnostic("PG.FINAL.KERNEL_INTAKE_INVALID", "error", "Raw Kernel decision intake must be a Stage Evidence Bundle object.", "$.kernel_decision_intake"))
    elif not isinstance(config.kernel_intake_lock, dict):
        diagnostics.append(diagnostic("PG.FINAL.KERNEL_INTAKE_LOCK_UNAVAILABLE", "insufficient_evidence", "Committed KROAD-011 semantic lock is unavailable to Final Gate.", "$.kernel_decision_intake"))
    else:
        kernel_intake_result = run_kernel_decision_intake(
            raw_intake,
            contract_source,
            KernelDecisionIntakeConfig(config.schema_root, config.kernel_intake_lock, config.kernel_repo_root, config.project_gate_repo_root, config.timeout_seconds),
            audit_executor=_kernel_audit_executor(config),
        )
        diagnostics.extend(_kernel_intake_status_diagnostics(kernel_intake_result))
        if supplied_projection is not None and not _projection_matches(supplied_projection, kernel_intake_result):
            diagnostics.append(diagnostic("PG.FINAL.KERNEL_INTAKE_PROJECTION_MISMATCH", "error", "Supplied precomputed Kernel intake result does not match the result recomputed by Final Gate and is non-authoritative.", "$.kernel_decision_intake_result"))
        accepted_requires["kernel_decision_intake_accepted"] = kernel_intake_result.get("status") == "accepted" and not any(item.code == "PG.FINAL.KERNEL_INTAKE_PROJECTION_MISMATCH" for item in diagnostics)

    lineage_diagnostics = _validate_output_decision_lineage_projection(final_input, output)
    diagnostics.extend(lineage_diagnostics)
    accepted_requires["decision_lineage_projection_valid"] = not lineage_diagnostics

    schema = _load_responsive_output_schema(contract_source, diagnostics)
    if schema is not None:
        accepted_requires["responsive_output_schema_verified"] = True
        for error in sorted(Draft202012Validator(schema).iter_errors(output), key=lambda item: (list(item.path), item.message)):
            diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_SCHEMA_VALIDATION_FAILED", "error", error.message, _json_path(list(error.path))))

    bindings = final_input.get("evidence_bindings") if isinstance(final_input.get("evidence_bindings"), dict) else {}
    subject = final_input.get("evidence_subject") if isinstance(final_input.get("evidence_subject"), dict) else {}
    if not bindings:
        diagnostics.append(diagnostic("PG.FINAL.EVIDENCE_BINDINGS_REQUIRED", "insufficient_evidence", "Final Gate requires source-bound evidence; caller labels such as real_evidence are non-authoritative.", "$.evidence_bindings"))
    elif config.responsive_repo_root is None:
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_REPO_REQUIRED", "insufficient_evidence", "Responsive checkout is required to resolve source evidence.", "$.evidence_bindings"))
    else:
        specs = _binding_specs(output, subject)
        for slot, spec in specs.items():
            binding = bindings.get(slot)
            if not isinstance(binding, dict):
                diagnostics.append(diagnostic("PG.FINAL.EVIDENCE_BINDING_MISSING", "insufficient_evidence", "Required Final Gate evidence binding is missing.", f"$.evidence_bindings.{slot}", slot=slot))
                continue
            callback = _responsive_validator_callback(config, progress_sink) if slot == "responsive_output" else None
            resolution = resolve_evidence(
                artifact_ref=binding.get("artifact_ref"),
                declared_sha256=binding.get("artifact_sha256"),
                repository_root=config.responsive_repo_root,
                hash_scope="file_bytes",
                owner_repository=RESPONSIVE_REPO,
                owner_commit=RESPONSIVE_COMMIT,
                owner_validator=RESPONSIVE_OUTPUT_VALIDATOR if slot == "responsive_output" else None,
                owner_validator_callback=callback,
                claim_id=spec["claim_class"],
                evidence_type=spec["evidence_type"],
                subject_ref=binding.get("subject_ref"),
                expected_subject_ref=spec["subject_ref"],
                viewport=spec.get("viewport"),
            )
            resolutions[slot] = resolution
            diagnostics.extend(_resolution_diagnostics(slot, resolution))
            if slot == "responsive_output" and resolution.value is not None:
                try:
                    if canonical_sha256(resolution.value) != canonical_sha256(output):
                        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_OUTPUT_SOURCE_DRIFT", "error", "Resolved Responsive output bytes do not match the embedded output.", "$.evidence_bindings.responsive_output"))
                except Exception:
                    diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_OUTPUT_SOURCE_INVALID", "error", "Resolved Responsive output cannot be compared canonically.", "$.evidence_bindings.responsive_output"))
            elif slot in {"desktop", "tablet", "mobile"} and resolution.value is not None:
                diagnostics.extend(_viewport_binding_diagnostics(slot, spec, resolution.value))

        required = set(specs)
        all_present = required <= set(resolutions)
        accepted_requires["evidence_sources_resolved"] = all_present and all(item.source_path for item in resolutions.values())
        accepted_requires["evidence_hashes_verified"] = all_present and all(item.hash_verified for item in resolutions.values())
        accepted_requires["claim_bindings_valid"] = all_present and not any(item.severity == "error" and (item.code.startswith("PG.EVIDENCE.CLAIM_") or item.code.startswith("PG.FINAL.RESPONSIVE_OUTPUT_SOURCE") or item.code.startswith("PG.FINAL.VIEWPORT_")) for item in diagnostics)
        accepted_requires["required_viewports_verified"] = all(name in resolutions and resolutions[name].classification == "real_verified" for name in ("desktop", "tablet", "mobile"))
        accepted_requires["responsive_output_validator_passed"] = resolutions.get("responsive_output") is not None and resolutions["responsive_output"].owner_validation_status == "accepted"
        real_verified = all_present and all(item.classification == "real_verified" for item in resolutions.values())
        accepted_requires["real_evidence_present"] = real_verified
        if config.require_real_evidence and not real_verified:
            diagnostics.append(diagnostic("PG.FINAL.REAL_EVIDENCE_MISSING", "insufficient_evidence", "Final gate requires resolved, hash-verified, owner-validated, non-synthetic evidence.", "$.evidence_bindings"))

    if synthetic_indicators(final_input):
        accepted_requires["real_evidence_present"] = False
        diagnostics.append(diagnostic("PG.FINAL.SYNTHETIC_ONLY_EVIDENCE", "insufficient_evidence", "Synthetic fixtures cannot satisfy final real-evidence requirements.", "$", indicators=synthetic_indicators(final_input)))
    accepted_requires["blocking_unknowns_absent"] = isinstance(output.get("unresolved_unknowns"), list) and not output.get("unresolved_unknowns")
    if not accepted_requires["blocking_unknowns_absent"]:
        diagnostics.append(diagnostic("PG.FINAL.BLOCKING_UNKNOWNS_PRESENT", "insufficient_evidence", "Final Gate requires blocking unknowns to be absent.", "$.responsive_output.unresolved_unknowns"))
    return _result(final_input, output, kernel_intake_result, diagnostics, accepted_requires, config, resolutions)


def _binding_specs(output: dict[str, Any], subject: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packet_ref = output.get("source_packet_ref")
    viewport_refs = subject.get("viewport_refs") if isinstance(subject.get("viewport_refs"), dict) else {}
    specs: dict[str, dict[str, Any]] = {
        "responsive_output": {"subject_ref": packet_ref, "claim_class": "responsive_validation_verified", "evidence_type": "responsive_output"},
    }
    for name in ("desktop", "tablet", "mobile"):
        specs[name] = {"subject_ref": viewport_refs.get(name), "claim_class": "real_evidence_present", "evidence_type": "viewport_evidence", "viewport": name}
    return specs


def _responsive_validator_callback(config: FinalGateConfig, progress_sink: list[dict[str, Any]] | None) -> Callable[[Path, Any], tuple[str, list[dict[str, Any]]]]:
    def run(_: Path, value: Any) -> tuple[str, list[dict[str, Any]]]:
        if not isinstance(value, dict) or config.responsive_repo_root is None:
            return "rejected", [{"code": "PG.FINAL.RESPONSIVE_SOURCE_INVALID", "severity": "error", "message": "Resolved Responsive output must be an object.", "path": "$.evidence_bindings.responsive_output"}]
        outcome = execute_responsive_output_validator(repo_root=config.responsive_repo_root, owner_repo=RESPONSIVE_REPO, owner_commit=RESPONSIVE_COMMIT, validator_path=RESPONSIVE_OUTPUT_VALIDATOR, responsive_output=value, timeout_seconds=config.timeout_seconds, progress_sink=progress_sink)
        return ("accepted" if outcome.status == "accepted" else "rejected", [item.to_dict() for item in outcome.diagnostics])
    return run


def _viewport_binding_diagnostics(slot: str, spec: dict[str, Any], value: Any) -> list[Diagnostic]:
    if not isinstance(value, dict):
        return [diagnostic("PG.FINAL.VIEWPORT_EVIDENCE_INVALID", "error", "Viewport evidence must be a JSON object.", f"$.evidence_bindings.{slot}")]
    if value.get("evidence_ref") != spec.get("subject_ref") or value.get("viewport") != slot or value.get("status") != "confirmed":
        return [diagnostic("PG.FINAL.VIEWPORT_EVIDENCE_MISMATCH", "error", "Viewport evidence must bind the exact ref, viewport, and confirmed status.", f"$.evidence_bindings.{slot}")]
    return []


def _resolution_diagnostics(slot: str, resolution: EvidenceResolution) -> list[Diagnostic]:
    result: list[Diagnostic] = []
    for item in resolution.diagnostics:
        details = dict(item.get("details") or {})
        details["slot"] = slot
        result.append(diagnostic(item["code"], item["severity"], item["message"], f"$.evidence_bindings.{slot}", **details))
    return result


def _projection_matches(supplied: Any, recomputed: dict[str, Any]) -> bool:
    if not isinstance(supplied, dict):
        return False
    try:
        return canonical_sha256(supplied) == canonical_sha256(recomputed)
    except Exception:
        return False


def _kernel_audit_executor(config: FinalGateConfig) -> Callable[[dict[str, Any]], KernelAuditExecution] | None:
    if config.kernel_audit_executor is not None:
        return config.kernel_audit_executor
    if config.kernel_repo_root is None or config.project_gate_repo_root is None:
        return None
    from ev4_transition.runners.kernel_decision import execute_kernel_l2_audit
    return lambda packet: execute_kernel_l2_audit(packet, kernel_repo_root=config.kernel_repo_root, project_gate_repo_root=config.project_gate_repo_root, timeout_seconds=config.timeout_seconds)


def _kernel_intake_status_diagnostics(value: dict[str, Any]) -> list[Diagnostic]:
    status = value.get("status")
    if status == "accepted":
        return []
    severity = "warning" if status == "repair_needed" else ("insufficient_evidence" if status == "insufficient_evidence" else "error")
    return [diagnostic("PG.FINAL.KERNEL_INTAKE_NOT_ACCEPTED", severity, "Internally executed KROAD-011 intake did not return accepted.", "$.kernel_decision_intake", actual=status)]


def _validate_output_decision_lineage_projection(final_input: dict[str, Any], output: dict[str, Any]) -> list[Diagnostic]:
    output_path = "$.responsive_output" if isinstance(final_input.get("responsive_output"), dict) else "$"
    lineage, top_level = output.get("decision_lineage"), final_input.get("decision_lineage")
    if lineage is None and top_level is None:
        return []
    diagnostics = _validate_decision_lineage_at(output, f"{output_path}.decision_lineage")
    if isinstance(final_input.get("responsive_output"), dict) and top_level is not None and top_level != lineage:
        diagnostics.append(diagnostic("PG.FINAL.DECISION_LINEAGE_DRIFT", "error", "Top-level decision lineage must exactly match responsive_output decision lineage when both are supplied.", "$.decision_lineage"))
    return sort_diagnostics(diagnostics)


def _validate_decision_lineage_at(container: dict[str, Any], path: str) -> list[Diagnostic]:
    lineage = container.get("decision_lineage")
    if not isinstance(lineage, dict):
        return [diagnostic("PG.FINAL.DECISION_LINEAGE_PROJECTION_INVALID", "error", "Optional decision lineage projection must be an object when supplied.", path)]
    diagnostics: list[Diagnostic] = []
    missing = [field for field in REQUIRED_DECISION_LINEAGE_FIELDS if field not in lineage]
    if missing:
        diagnostics.append(diagnostic("PG.FINAL.DECISION_LINEAGE_INCOMPLETE", "error", "Decision lineage projection is missing required fields.", path, missing_fields=missing))
    for field in ("decision_family", "decision_card_ref", "selected_option", "evidence_state", "consumer_stage"):
        if field in lineage and (not isinstance(lineage[field], str) or not lineage[field]):
            diagnostics.append(diagnostic("PG.FINAL.DECISION_LINEAGE_FIELD_INVALID", "error", "Decision lineage projection field must be a non-empty string.", f"{path}.{field}", field=field))
    for field in ("rejected_options", "evidence_refs"):
        if field in lineage and (not isinstance(lineage[field], list) or not lineage[field] or not all(isinstance(item, str) and item for item in lineage[field])):
            diagnostics.append(diagnostic("PG.FINAL.DECISION_LINEAGE_FIELD_INVALID", "error", "Decision lineage projection field must be a non-empty string array.", f"{path}.{field}", field=field))
    return sort_diagnostics(diagnostics)


def _load_responsive_output_schema(source: ContractSource, diagnostics: list[Diagnostic]) -> dict[str, Any] | None:
    try:
        schema = json.loads(source.read_bytes(RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_SCHEMA_PATH).decode("utf-8"))
    except Exception as exc:
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_SCHEMA_UNAVAILABLE", "insufficient_evidence", "Responsive-owned output schema is absent or unreadable.", "$.responsive_schema", error_type=type(exc).__name__))
        return None
    return schema if isinstance(schema, dict) else None


def _result(original: Any, output: dict[str, Any] | None, kernel_intake: dict[str, Any] | None, diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], config: FinalGateConfig, resolutions: dict[str, EvidenceResolution]) -> dict[str, Any]:
    ordered, accepted = sort_diagnostics(diagnostics), dict(accepted_requires)
    if not ordered and not all(accepted.values()):
        ordered = [diagnostic("PG.FINAL.ACCEPTED_REQUIRES_MISSING", "insufficient_evidence", "Accepted final status requires every accepted_requires item to be true.", "$.accepted_requires", missing=sorted(key for key, value in accepted.items() if not value))]
    status = project_gate_status_from_diagnostics(ordered)
    candidate = {
        "schema_version": "final-gate-result.v1",
        "result_type": "final_evidence_gate",
        "gate_id": GATE_ID,
        "gate_version": GATE_VERSION,
        "status": status,
        "diagnostics": [item.to_dict() for item in ordered],
        "accepted_requires": accepted,
        "evidence_resolutions": {name: item.to_dict() for name, item in sorted(resolutions.items())},
        "decision_lineage_authority": "informational_projection_only",
        "hashes": {"source_input_hash": {"algorithm": "sha256", "canonicalization": "ev4-canonical-json.v1", "scope": "source_input", "value": _safe_hash(original)}},
        "kernel_decision_intake_result": kernel_intake,
        "output": output if status == "accepted" else None,
    }
    schema_path = config.schema_root / "final-gate-result/final-gate-result.v1.schema.json"
    try:
        schema = load_json_file(schema_path)
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return _fallback_result(candidate, ordered, accepted, diagnostic("PG.FINAL.RESULT_SCHEMA_MISSING", "insufficient_evidence", "Final gate result schema is required and must be valid.", "$.schema_version", schema_path=str(schema_path), error_type=type(exc).__name__))
    errors = sorted(Draft202012Validator(schema).iter_errors(candidate), key=lambda item: (list(item.path), item.message))
    if not errors:
        return _authoritative_final_gate_result(candidate)
    fallback = _fallback_result(candidate, ordered, accepted, *[diagnostic("PG.FINAL.RESULT_SCHEMA_VALIDATION_FAILED", "error", error.message, _json_path(list(error.path))) for error in errors])
    if list(Draft202012Validator(schema).iter_errors(fallback)):
        raise ValueError("Final Gate fail-closed result does not satisfy final-gate-result.v1 schema.")
    return fallback


def _fallback_result(candidate: dict[str, Any], diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], *extra: Diagnostic) -> dict[str, Any]:
    ordered = sort_diagnostics([*diagnostics, *extra])
    return _authoritative_final_gate_result({**candidate, "status": project_gate_status_from_diagnostics(ordered), "diagnostics": [item.to_dict() for item in ordered], "accepted_requires": {**accepted_requires, "result_schema_valid": False}, "output": None})


def _find_forbidden_claims(value: Any) -> list[str]:
    found: set[str] = set()
    def walk(node: Any, path: str = "$") -> None:
        if path.startswith("$.kernel_decision_intake_result"):
            return
        if isinstance(node, dict):
            for key, child in node.items():
                if key == "forbidden_claims":
                    continue
                if key in FORBIDDEN_FINAL_CLAIMS:
                    found.add(key)
                walk(child, f"{path}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")
        elif isinstance(node, str) and node.strip() in FORBIDDEN_FINAL_CLAIMS:
            found.add(node.strip())
    walk(value)
    return sorted(found)


def _contains_key_or_value(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(key == needle or _contains_key_or_value(child, needle) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_key_or_value(child, needle) for child in value)
    return value == needle


def _safe_hash(value: Any) -> str:
    try:
        return canonical_sha256(value)
    except Exception:
        return bytes_sha256(b"unhashable")


def _json_path(parts: list[Any]) -> str:
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path
