from __future__ import annotations

import json
from typing import Any

from .contract_source import ContractSource
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics
from .kernel_decision_dependencies import EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES, KERNEL_ACCEPTED_COMMIT, KERNEL_REPOSITORY

FORBIDDEN_AUTHORED_FIELDS = frozenset({
    "l2_audit_status", "resolver_output", "audit_passed", "kernel_validated",
    "accepted_decision_count", "rejected_decision_count", "provisional_count",
    "human_override_count", "unresolved_decision_count",
})
UNSUPPORTED_ASSERTED_CLAIMS = frozenset({
    "builder_execution_proof", "builder_ready", "runtime_validated", "browser_validated",
    "downstream_enforced", "project_gate_accepted", "release_ready", "production_ready",
    "frontend_correctness", "responsive_correctness",
})
FORBIDDEN_CLAIM_KEYS = UNSUPPORTED_ASSERTED_CLAIMS | {"resolved", "accepted"}


def scan_authored_fields(value: Any, diagnostics: list[Diagnostic], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_AUTHORED_FIELDS:
                diagnostics.append(diagnostic("PG.KERNEL_INTAKE.AUTHORED_DERIVED_FIELD", "error", "Authored Kernel/Project Gate derived fields are forbidden in intake.", child_path, field=key))
            scan_authored_fields(child, diagnostics, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_authored_fields(child, diagnostics, f"{path}[{index}]")


def scan_forbidden_claims(value: Any, diagnostics: list[Diagnostic], path: str = "$", parent_key: str | None = None) -> None:
    if any(token in path for token in (".forbidden_overclaims", ".limitations", ".notes")):
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_CLAIM_KEYS:
                diagnostics.append(diagnostic("PG.KERNEL_INTAKE.FORBIDDEN_CLAIM", "error", "Unsupported readiness/correctness claim is forbidden outside asserted_claims.", child_path, claim=key))
            scan_forbidden_claims(child, diagnostics, child_path, key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden_claims(child, diagnostics, f"{path}[{index}]", parent_key)
    elif isinstance(value, str) and parent_key in {"claim", "claims", "assertion", "status"} and value in UNSUPPORTED_ASSERTED_CLAIMS:
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.FORBIDDEN_CLAIM", "error", "Unsupported readiness/correctness claim was found outside accepted evidence.", path, claim=value))


def binding_diagnostics(packets: list[Any], source: ContractSource) -> dict[int, list[Diagnostic]]:
    result = {index: [] for index in range(len(packets))}
    packet_ids: dict[str, int] = {}
    decision_ids: dict[str, int] = {}
    packet_decision_ids = {item.get("decision_id") for item in packets if isinstance(item, dict) and isinstance(item.get("decision_id"), str)}
    known_families = _known_families(source)
    for index, packet in enumerate(packets):
        base = f"$.payload.data.decision_packets[{index}]"
        if not isinstance(packet, dict):
            continue
        packet_id, decision_id, family = packet.get("packet_id"), packet.get("decision_id"), packet.get("decision_family_id")
        _unique(result[index], packet_ids, packet_id, index, "PG.KERNEL_INTAKE.DUPLICATE_PACKET_ID", f"{base}.packet_id")
        _unique(result[index], decision_ids, decision_id, index, "PG.KERNEL_INTAKE.DUPLICATE_DECISION_ID", f"{base}.decision_id")
        record, resolver, audit, provenance = (packet.get(name) for name in ("decision_record", "resolver_input", "audit_context", "provenance"))
        if not all(isinstance(item, dict) for item in (record, resolver, audit, provenance)):
            continue
        for name, value in (("decision_record", record), ("resolver_input", resolver), ("audit_context", audit)):
            if value.get("decision_id") != decision_id:
                result[index].append(diagnostic("PG.KERNEL_INTAKE.DECISION_ID_MISMATCH", "error", "Decision ID must match every packet wrapper.", f"{base}.{name}.decision_id"))
            if value.get("decision_family_id") != family:
                result[index].append(diagnostic("PG.KERNEL_INTAKE.DECISION_FAMILY_MISMATCH", "error", "Decision family must match every packet wrapper.", f"{base}.{name}.decision_family_id"))
        if family == "layout_structure" and (record.get("rule_id"), record.get("rule_version")) != ("resolver.rule.layout_structure.mvp.v0", "0.1.0"):
            result[index].append(diagnostic("PG.KERNEL_INTAKE.RULE_BINDING_MISMATCH", "error", "Decision rule ID/version must match the pinned active rule.", f"{base}.decision_record.rule_version"))
        elif known_families and family not in known_families:
            result[index].append(diagnostic("PG.KERNEL_INTAKE.UNKNOWN_DECISION_FAMILY", "error", "Decision family is absent from the pinned P0 matrix registry.", f"{base}.decision_family_id"))
        record_ids, resolver_ids = _evidence_ids(record.get("evidence_refs")), _evidence_ids(resolver.get("evidence_refs"))
        if record_ids != resolver_ids:
            result[index].append(diagnostic("PG.KERNEL_INTAKE.EVIDENCE_REF_MISMATCH", "error", "Decision Record and Resolver input evidence references must match exactly.", f"{base}.resolver_input.evidence_refs"))
        context = resolver.get("context") if isinstance(resolver.get("context"), dict) else {}
        required = set(context.get("required_evidence_refs", [])) if isinstance(context.get("required_evidence_refs"), list) else set()
        if not required.issubset(record_ids):
            result[index].append(diagnostic("PG.KERNEL_INTAKE.REQUIRED_EVIDENCE_REF_MISSING", "error", "Resolver-required evidence refs must be bound into the decision packet.", f"{base}.resolver_input.context.required_evidence_refs"))
        if any(ref in packet_decision_ids - {decision_id} for ref in required):
            result[index].append(diagnostic("PG.KERNEL_INTAKE.CROSS_PACKET_SUBSTITUTION", "error", "Cross-packet decision/evidence substitution is forbidden.", f"{base}.resolver_input.context.required_evidence_refs"))
        if audit.get("provenance_ref") != provenance.get("provenance_id"):
            result[index].append(diagnostic("PG.KERNEL_INTAKE.PROVENANCE_MISMATCH", "error", "Audit context provenance_ref must bind to packet provenance.", f"{base}.audit_context.provenance_ref"))
        for claim_index, claim in enumerate(packet.get("asserted_claims", [])):
            if not isinstance(claim, dict):
                continue
            claim_path = f"{base}.asserted_claims[{claim_index}]"
            if claim.get("claim") in UNSUPPORTED_ASSERTED_CLAIMS:
                result[index].append(diagnostic("PG.KERNEL_INTAKE.UNSUPPORTED_ASSERTED_CLAIM", "error", "Unsupported assertion is not proof.", f"{claim_path}.claim", claim=claim.get("claim")))
            if claim.get("provenance_ref") != provenance.get("provenance_id"):
                result[index].append(diagnostic("PG.KERNEL_INTAKE.CLAIM_PROVENANCE_MISMATCH", "error", "Claim provenance must match packet provenance.", f"{claim_path}.provenance_ref"))
            source_value = claim.get("source")
            expected_source = (provenance.get("source_repository"), provenance.get("source_commit"), provenance.get("source_path"))
            actual_source = (source_value.get("repository"), source_value.get("commit"), source_value.get("path")) if isinstance(source_value, dict) else None
            if actual_source != expected_source:
                result[index].append(diagnostic("PG.KERNEL_INTAKE.CLAIM_SOURCE_MISMATCH", "error", "Claim source must match packet provenance.", f"{claim_path}.source"))
    return {index: sort_diagnostics(items) for index, items in result.items()}


def _unique(diagnostics: list[Diagnostic], seen: dict[str, int], value: Any, index: int, code: str, path: str) -> None:
    if not isinstance(value, str):
        return
    if value in seen:
        diagnostics.append(diagnostic(code, "error", "Identifier must be unique across decision packets.", path, first_index=seen[value]))
    else:
        seen[value] = index


def _known_families(source: ContractSource) -> set[str]:
    try:
        path = EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES["p0_decision_matrices"].path
        matrix = json.loads(source.read_bytes(KERNEL_REPOSITORY, KERNEL_ACCEPTED_COMMIT, path))
    except Exception:
        return set()
    return {item.get("decision_family_id") for item in matrix.get("matrices", []) if isinstance(item, dict) and isinstance(item.get("decision_family_id"), str)}


def _evidence_ids(refs: Any) -> set[str]:
    return {item.get("evidence_id") for item in refs if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)} if isinstance(refs, list) else set()
