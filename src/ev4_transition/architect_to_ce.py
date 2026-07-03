from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .bundle_validator import BundleValidator, ResultValidationError
from .canonical_json import CANONICAL_JSON_VERSION, canonical_sha256, load_json_file
from .contract_source import ContractSource, LocalCheckoutContractSource
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics, status_from_diagnostics
from .external_lock import lock_file_hash, verify_external_contract_lock

TRANSITION_ID = "ev4-architect-to-ce-transition@1.0.0"
TRANSITION_VERSION = "1.0.0"
SOURCE_SCHEMA_ID = "ev4-architect-stage-payload@1.0.0"
TARGET_SCHEMA_ID = "ev4-ce-architect-stage-intake@1.0.0"
MAPPING_CONTRACT_ID = "ev4-architect-stage-to-ce-intake-mapping@1.0.0"
ARCHITECT_REPO = "rezahh107/EV4-Architect-Repo"
CE_REPO = "rezahh107/EV4-Constructability-Engineer-Repo"
PG_REPO = "rezahh107/EV4-Project-Gate"
ARCHITECT_COMMIT = "b0651668b97f682bb17f66840c8e8c503fd3935d"
CE_COMMIT = "d3aadff91d9b6fcb38e2f5d3f4cbc2870484b0f7"

CE_FORBIDDEN_FIELDS = {
    "ce_review_units", "action_proposed", "proof_states", "constructability_review",
    "implementation_strategy_map", "builder_executable_package", "first_safe_builder_batch",
    "confirmation_request",
}


@dataclass(frozen=True)
class ArchitectToCeTransitionConfig:
    schema_root: Path
    lock: dict[str, Any]


def default_config(schema_root: str | Path = "schemas", lock_path: str | Path = "contracts/locks/architect-to-ce-transition.v1.lock.json") -> ArchitectToCeTransitionConfig:
    return ArchitectToCeTransitionConfig(schema_root=Path(schema_root), lock=load_json_file(lock_path))


def transition_architect_to_ce(source_bundle: Any, contract_source: ContractSource, transition_config: ArchitectToCeTransitionConfig) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    bundle_validator = BundleValidator(transition_config.schema_root)
    envelope = bundle_validator.validate_bundle(source_bundle)
    if envelope["status"] == "invalid":
        return _result(source_bundle, None, _import_diags(envelope["diagnostics"]), transition_config)

    diagnostics.extend(_source_identity_diagnostics(source_bundle))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)

    diagnostics.extend(verify_external_contract_lock(transition_config.lock, contract_source))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)

    payload_dict = source_bundle.get("payload") if isinstance(source_bundle, dict) else None
    source_payload = payload_dict.get("data") if isinstance(payload_dict, dict) else None
    if not isinstance(source_payload, dict):
        diagnostics.append(diagnostic("PG_A2C_SOURCE_PAYLOAD_NOT_OBJECT", "error", "Source payload data must be an object.", "$.payload.data"))
        return _result(source_bundle, None, diagnostics, transition_config)

    architect_schema = _load_external_json(contract_source, transition_config.lock, "architect_payload_schema")
    diagnostics.extend(_json_schema_diagnostics(architect_schema, source_payload, "PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED", "PG-A2C-01"))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)

    ce_payload = _map_payload(source_bundle, source_payload)
    diagnostics.extend(_mapping_invariant_diagnostics(source_payload, ce_payload))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)

    ce_schema = _load_external_json(contract_source, transition_config.lock, "ce_intake_schema")
    diagnostics.extend(_json_schema_diagnostics(ce_schema, ce_payload, "PG_A2C_CE_SCHEMA_VALIDATION_FAILED", "PG-A2C-10"))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)

    target_bundle = _target_bundle(source_bundle, ce_payload)
    target_envelope = bundle_validator.validate_bundle(target_bundle)
    diagnostics.extend(_import_diags(target_envelope["diagnostics"]))
    if _has_error(diagnostics):
        return _result(source_bundle, None, diagnostics, transition_config)
    return _result(source_bundle, target_bundle, diagnostics, transition_config)


def _has_error(diagnostics: list[Diagnostic]) -> bool:
    return any(item.severity == "error" for item in diagnostics)


def _source_identity_diagnostics(bundle: dict[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if bundle.get("stage") != "architect":
        diagnostics.append(diagnostic("PG_A2C_WRONG_SOURCE_STAGE", "error", "Source bundle stage must be architect.", "$.stage", rule_id="PG-A2C-01"))
    payload_schema = bundle.get("payload_schema") or {}
    if payload_schema.get("id") != SOURCE_SCHEMA_ID:
        diagnostics.append(diagnostic("PG_A2C_SOURCE_SCHEMA_ID_MISMATCH", "error", "Source payload schema id must be Architect Stage Payload v1.", "$.payload_schema.id", expected=SOURCE_SCHEMA_ID, actual=payload_schema.get("id")))
    if payload_schema.get("version") != "1.0.0":
        diagnostics.append(diagnostic("PG_A2C_SOURCE_SCHEMA_VERSION_MISMATCH", "error", "Source payload schema version must be 1.0.0.", "$.payload_schema.version"))
    if payload_schema.get("owner_repository") != ARCHITECT_REPO:
        diagnostics.append(diagnostic("PG_A2C_SOURCE_OWNER_MISMATCH", "error", "Source payload owner must remain the Architect repository.", "$.payload_schema.owner_repository", expected=ARCHITECT_REPO, actual=payload_schema.get("owner_repository")))
    payload = bundle.get("payload") or {}
    if payload.get("schema_id") != SOURCE_SCHEMA_ID:
        diagnostics.append(diagnostic("PG_A2C_SOURCE_PAYLOAD_SCHEMA_MISMATCH", "error", "Source payload wrapper schema_id must be Architect Stage Payload v1.", "$.payload.schema_id"))
    data = payload.get("data") or {}
    if isinstance(data, dict) and data.get("schema_id") != SOURCE_SCHEMA_ID:
        diagnostics.append(diagnostic("PG_A2C_SOURCE_PAYLOAD_DATA_SCHEMA_MISMATCH", "error", "Source payload data schema_id must be Architect Stage Payload v1.", "$.payload.data.schema_id"))
    if isinstance(data, dict) and data.get("owner_repository") != ARCHITECT_REPO:
        diagnostics.append(diagnostic("PG_A2C_SOURCE_PAYLOAD_OWNER_MISMATCH", "error", "Source payload data owner must be Architect.", "$.payload.data.owner_repository"))
    return diagnostics


def _lock_entry(lock: dict[str, Any], role: str) -> dict[str, Any]:
    for item in lock.get("files", []):
        if item.get("role") == role:
            return item
    raise KeyError(role)


def _load_external_json(source: ContractSource, lock: dict[str, Any], role: str) -> dict[str, Any]:
    entry = _lock_entry(lock, role)
    return json.loads(source.read_bytes(entry["repository"], entry["accepted_commit"], entry["path"]).decode("utf-8"))


def _json_schema_diagnostics(schema: dict[str, Any], value: dict[str, Any], code: str, rule_id: str) -> list[Diagnostic]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    return [diagnostic(code, "error", err.message, _json_path(list(err.path)), rule_id=rule_id) for err in sorted(validator.iter_errors(value), key=lambda e: (_json_path(list(e.path)), e.message))]


def _map_payload(source_bundle: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    architecture = p["architecture_identity"]
    decision = architecture["decision_source"]
    structure = p["approved_structure_model"]
    intent = p["architect_intent"]
    unresolved = list(p.get("unresolved_evidence", []))
    intake_status = "insufficient_evidence" if p.get("payload_status") == "insufficient_evidence" else "complete"
    ce_payload: dict[str, Any] = {
        "schema_id": TARGET_SCHEMA_ID,
        "schema_version": "1.0.0",
        "owner_repository": CE_REPO,
        "intake_status": intake_status,
        "synthetic": bool(p.get("synthetic")),
        "source_contract": {"schema_id": SOURCE_SCHEMA_ID, "schema_version": "1.0.0", "owner_repository": ARCHITECT_REPO, "accepted_main_merge_commit": ARCHITECT_COMMIT},
        "source_repository_ref": {"repository": ARCHITECT_REPO, "ref": source_bundle.get("produced_by", {}).get("ref", "unknown-source-ref"), "commit_sha": source_bundle.get("produced_by", {}).get("commit_sha", ARCHITECT_COMMIT), "bundle_id": source_bundle.get("bundle_id", "unknown-bundle")},
        "selected_architecture": {"selected_candidate_id": architecture["selected_candidate_id"], "selected_candidate_locked": architecture["selected_candidate_locked"], "architecture_family": architecture["architecture_family"], "decision_source_refs": sorted(set(decision["evidence_refs"] + decision["locked_decision_refs"] + decision["source_evidence_refs"])), "approved_structure_ref": decision["approved_structure_ref"]},
        "structure_projection": {"root_node_id": structure["root_node_id"], "nodes": [_map_node(node) for node in sorted(structure["structure_nodes"], key=lambda n: n["node_id"])]},
        "architect_intent_preserved": {"class_intent": {"approved_class_names": list(intent["class_intent"]["approved_class_names"])}, "responsive_risk_seeds": [{"risk_id": item["risk_id"], "state": item["state"], "evidence_refs": list(item["evidence_refs"])} for item in intent["responsive_risk_seeds"]], "dynamic_loop_intent": {"status": intent["dynamic_loop_intent"]["status"], "evidence_refs": list(intent["dynamic_loop_intent"].get("evidence_refs", []))}},
        "evidence_register": [dict(item) for item in p["evidence_register"]],
        "unresolved_evidence": [{"unresolved_id": item["unresolved_id"], "state": item["state"], "owner": item["owner"], "reason": item["reason"], "evidence_refs": list(item.get("evidence_refs", []))} for item in unresolved],
        "forbidden_work": list(p["forbidden_work"]),
        "negative_boundary_assertions": _negative_boundary_assertions(p["boundary_assertions"]),
        "ce_processing_prerequisites": {"ce_review_required": True, "intake_contains_ce_conclusions": False, "intake_contains_builder_authorization": False, "project_gate_transition_implemented": False, "real_cross_repository_validation_available": False},
        "mapping_contract": {"mapping_id": MAPPING_CONTRACT_ID, "mapping_version": "1.0.0", "source_schema_id": SOURCE_SCHEMA_ID, "target_schema_id": TARGET_SCHEMA_ID},
        "mapping_trace": _mapping_trace(),
        "legacy_contract_policy": {"canonical_architect_facing_intake": TARGET_SCHEMA_ID, "legacy_status": "compatibility_only"},
        "real_cross_repository_validation": "not_available",
        "validation_contract": {"rules": [f"CE-I{i:02d}" for i in range(1, 13)]},
    }
    if intake_status == "insufficient_evidence":
        ce_payload["missing_evidence"] = [_missing_evidence(item) for item in unresolved] or [{"missing_id": "missing-architect-evidence", "affected_ce_conclusion": "intake_acceptance", "required_source": "Architect payload declared insufficient evidence.", "current_evidence_owner": "architect", "ce_processing_can_partially_continue": False}]
    return ce_payload


def _map_node(node: dict[str, Any]) -> dict[str, Any]:
    return {"source_node_id": node["node_id"], "parent_node_id": node.get("parent_node_id"), "node_kind": node["node_kind"], "role": node["role"], "evidence_refs": list(node["evidence_refs"]), "children": sorted(node.get("children", []))}


def _negative_boundary_assertions(boundary: dict[str, Any]) -> dict[str, bool]:
    return {"constructability_proven": boundary["constructability_proven"], "ce_approved": boundary["ce_approved"], "implementation_strategy_selected": False, "elementor_feasibility_proven": False, "proof_state_resolved": False, "ce_review_complete": False, "builder_ready": boundary["builder_ready"], "builder_executable": boundary["builder_executable"], "builder_action_authorized": False, "builder_runtime_intake_authorized": boundary["builder_runtime_intake_authorized"], "production_ready": boundary["production_ready"], "responsive_complete": boundary["responsive_complete"]}


def _missing_evidence(item: dict[str, Any]) -> dict[str, Any]:
    blocks = set(item.get("blocks", []))
    conclusion = "intake_acceptance" if "ce_transition" in blocks or "architect_stage_payload_acceptance" in blocks else "constructability_review_scope"
    return {"missing_id": item["unresolved_id"], "affected_ce_conclusion": conclusion, "required_source": item["reason"], "current_evidence_owner": item["owner"], "ce_processing_can_partially_continue": conclusion != "intake_acceptance"}


def _mapping_trace() -> list[dict[str, str]]:
    return [_trace("$.schema_id", "$.source_contract.schema_id", "direct_evidence_copy", "not_applicable"), _trace("$.architecture_identity.selected_candidate_id", "$.selected_architecture.selected_candidate_id", "direct_evidence_copy", "not_applicable"), _trace("$.architecture_identity.decision_source.*refs", "$.selected_architecture.decision_source_refs", "deterministic_structural_projection", "sort_by_id"), _trace("$.approved_structure_model.structure_nodes[]", "$.structure_projection.nodes[]", "deterministic_structural_projection", "sort_by_id"), _trace("$.unresolved_evidence[]", "$.unresolved_evidence[]", "direct_evidence_copy", "preserve_source_order"), _trace("$.boundary_assertions", "$.negative_boundary_assertions", "allowed_representation_conversion", "sort_by_source_path_then_target_path")]


def _trace(source: str, target: str, classification: str, ordering: str) -> dict[str, str]:
    return {"source_path": source, "target_path": target, "classification": classification, "ordering_rule": ordering, "missing_source_behavior": "invalid", "duplicate_behavior": "reject", "unsupported_field_behavior": "reject", "provenance_behavior": "preserve_reference", "unresolved_evidence_behavior": "copy_exact" if "unresolved" in source else "not_applicable"}


def _mapping_invariant_diagnostics(source: dict[str, Any], target: dict[str, Any]) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    target_id = (target.get("selected_architecture") or {}).get("selected_candidate_id")
    source_id = (source.get("architecture_identity") or {}).get("selected_candidate_id")
    if target_id != source_id:
        out.append(diagnostic("PG_A2C_SELECTED_IDENTITY_CHANGED", "error", "Selected candidate identity changed during transition.", "$.selected_architecture.selected_candidate_id"))
    forbidden_found = sorted(CE_FORBIDDEN_FIELDS & _all_keys(target))
    if forbidden_found:
        out.append(diagnostic("PG_A2C_CE_OWNED_FIELD_EMITTED", "error", "Transition emitted CE-owned decision fields.", "$", forbidden_fields=forbidden_found))
    positives = [k for k, v in (target.get("negative_boundary_assertions") or {}).items() if v is not False]
    if positives:
        out.append(diagnostic("PG_A2C_POSITIVE_READINESS_CLAIM", "error", "Transition emitted positive downstream readiness assertions.", "$.negative_boundary_assertions", positive_fields=positives))
    return out


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys |= _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            keys |= _all_keys(child)
    return keys


def _target_bundle(source_bundle: dict[str, Any], ce_payload: dict[str, Any]) -> dict[str, Any]:
    evidence_status = ce_payload["intake_status"]
    bundle = {"schema_version": "stage-evidence-bundle.v1", "bundle_id": "pg-a2c-v1-" + canonical_sha256(ce_payload)[:16], "stage": "ce", "payload_schema": {"id": TARGET_SCHEMA_ID, "version": "1.0.0", "owner_repository": CE_REPO}, "produced_by": {"repository": PG_REPO, "ref": TRANSITION_ID}, "evidence_status": evidence_status, "payload": {"schema_id": TARGET_SCHEMA_ID, "data": ce_payload}, "evidence": list(source_bundle.get("evidence", [])) + [_transition_evidence(ce_payload)], "provenance": {"source": source_bundle.get("bundle_id", "unknown-source-bundle"), "created_by": TRANSITION_ID}, "synthetic": bool(source_bundle.get("synthetic"))}
    if evidence_status == "insufficient_evidence":
        bundle["missing_evidence"] = [{"id": item["missing_id"], "owner": item["current_evidence_owner"], "reason": item["required_source"]} for item in ce_payload.get("missing_evidence", [])]
    return bundle


def _transition_evidence(ce_payload: dict[str, Any]) -> dict[str, Any]:
    return {"id": "pg-a2c-transition-v1", "kind": "report", "state": "derived", "description": "Deterministic Project Gate Architect-to-CE transition result.", "artifact_hash": {"algorithm": "sha256", "value": canonical_sha256(ce_payload), "scope": "canonical_json"}, "source": {"type": "repo_path", "reference": "src/ev4_transition/architect_to_ce.py"}, "derivation_rule": {"id": TRANSITION_ID, "version": TRANSITION_VERSION}}


def _result(source_bundle: Any, output: dict[str, Any] | None, diagnostics: list[Diagnostic], config: ArchitectToCeTransitionConfig) -> dict[str, Any]:
    ordered = sort_diagnostics(diagnostics)
    status = status_from_diagnostics(ordered)
    if output is not None and status == "valid" and output.get("evidence_status") == "insufficient_evidence":
        status = "insufficient_evidence"
    if status == "invalid":
        output = None
    source_payload = source_bundle.get("payload", {}).get("data") if isinstance(source_bundle, dict) else None
    target_payload = output.get("payload", {}).get("data") if output else None
    result = {"schema_version": "architect-to-ce-transition-result.v1", "result_type": "architect_to_ce_transition", "transition": {"id": TRANSITION_ID, "version": TRANSITION_VERSION, "source_payload_schema": SOURCE_SCHEMA_ID, "target_payload_schema": TARGET_SCHEMA_ID, "mapping_contract": MAPPING_CONTRACT_ID}, "status": status, "source_stage": "architect", "target_stage": "ce", "diagnostics": [d.to_dict() for d in ordered], "hashes": {"source_bundle": _hash_or_none(source_bundle, "source_bundle"), "source_payload": _hash_or_none(source_payload, "source_payload"), "target_payload": _hash_or_none(target_payload, "target_payload"), "target_bundle": _hash_or_none(output, "target_bundle"), "external_contract_lock": {"algorithm": "sha256", "canonicalization": CANONICAL_JSON_VERSION, "scope": "external_contract_lock", "value": lock_file_hash(config.lock)}}, "provenance": {"source_bundle_id": source_bundle.get("bundle_id") if isinstance(source_bundle, dict) else None, "transition_id": TRANSITION_ID, "verification_state": "verified_by_synthetic_fixture"}, "output": output}
    _validate_transition_result(result, config.schema_root)
    return result


def _hash_or_none(value: Any, scope: str) -> dict[str, str] | None:
    if value is None:
        return None
    return {"algorithm": "sha256", "canonicalization": CANONICAL_JSON_VERSION, "scope": scope, "value": canonical_sha256(value)}


def _validate_transition_result(result: dict[str, Any], schema_root: Path) -> None:
    schema = load_json_file(schema_root / "architect-to-ce-transition-result" / "architect-to-ce-transition-result.v1.schema.json")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(result), key=lambda e: (_json_path(list(e.path)), e.message))
    if errors:
        raise ResultValidationError("; ".join(f"{_json_path(list(e.path))}: {e.message}" for e in errors))


def _import_diags(items: list[dict[str, Any]]) -> list[Diagnostic]:
    return [diagnostic(item["code"], item["severity"], item["message"], item["path"], **item.get("details", {})) for item in items]


def _json_path(parts: list[Any]) -> str:
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out


def transition_from_local_paths(source_bundle: Any, schema_root: str | Path, lock_path: str | Path, architect_repo: str | Path, ce_repo: str | Path) -> dict[str, Any]:
    lock = load_json_file(lock_path)
    source = LocalCheckoutContractSource({ARCHITECT_REPO: Path(architect_repo), CE_REPO: Path(ce_repo)})
    config = ArchitectToCeTransitionConfig(schema_root=Path(schema_root), lock=lock)
    return transition_architect_to_ce(source_bundle, source, config)
