from __future__ import annotations

from dataclasses import dataclass

KERNEL_REPOSITORY = "rezahh107/EV4-Decision-Kernel"
KERNEL_ACCEPTED_COMMIT = "76a82e28543ff8f0babca11b7d7dccac96b92894"
KERNEL_INTAKE_SCHEMA_ID = "ev4-project-gate-kernel-decision-intake@1.0.0"
KERNEL_INTAKE_RESULT_SCHEMA_ID = "kernel-decision-intake-result.v1"
KERNEL_LOCK_SCHEMA_VERSION = "kernel-decision-intake-lock.v1"


@dataclass(frozen=True)
class KernelSemanticDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str
    identity_kind: str
    identity_value: str


_DEPENDENCIES = (
    KernelSemanticDependency(
        role="decision_record_schema",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/schemas/decision-record.v2.schema.json",
        contract_or_schema_id="decision-record.v2",
        identity_kind="json_field",
        identity_value="$id=https://ev4.local/schemas/decision-record.v2.schema.json",
    ),
    KernelSemanticDependency(
        role="p0_decision_matrices",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/decision-governance/p0-decision-matrices.v0.json",
        contract_or_schema_id="p0-decision-matrices.v0",
        identity_kind="json_field",
        identity_value="matrix_registry_id=p0-decision-matrices.v0",
    ),
    KernelSemanticDependency(
        role="resolver_rule_registry",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/decision-governance/resolver-rule-registry.v0.json",
        contract_or_schema_id="resolver-rule-registry.v0",
        identity_kind="json_field",
        identity_value="registry_id=resolver-rule-registry.v0",
    ),
    KernelSemanticDependency(
        role="layout_structure_rule",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/decision-governance/resolver-rules/layout-structure.v0.json",
        contract_or_schema_id="resolver.contract.layout_structure.mvp.v0",
        identity_kind="json_field",
        identity_value="contract_id=resolver.contract.layout_structure.mvp.v0",
    ),
    KernelSemanticDependency(
        role="resolver_implementation",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/resolver-mvp/resolve-high-risk-p0.mjs",
        contract_or_schema_id="resolveDecision",
        identity_kind="text_marker",
        identity_value="export function resolveDecision",
    ),
    KernelSemanticDependency(
        role="l2_decision_correctness_audit",
        repository=KERNEL_REPOSITORY,
        accepted_commit=KERNEL_ACCEPTED_COMMIT,
        path="kernel/validator/validate-l2-decision-correctness.mjs",
        contract_or_schema_id="auditDecisionRecord",
        identity_kind="text_marker",
        identity_value="export function auditDecisionRecord",
    ),
)

EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES = {item.role: item for item in _DEPENDENCIES}
REQUIRED_KERNEL_SEMANTIC_ROLES = frozenset(EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES)
