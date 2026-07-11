# KROAD-011 — Project Gate Intake

Status: implementation and focused trust-boundary repair are complete on PR #51. Exact-head CI is successful for `bc8bf394174e08d3a3a9e60cb4652440ac062885`.

## Ownership boundary

`rezahh107/EV4-Decision-Kernel` remains authoritative for:

- Decision Record v2 schema and semantics;
- P0 decision matrices;
- Resolver registry and active `layout_structure` rule;
- Resolver implementation;
- L2 Decision Correctness audit behavior and diagnostics.

`rezahh107/EV4-Project-Gate` owns only:

- `ev4-project-gate-kernel-decision-intake@1.0.0` as a Stage Evidence Bundle payload contract;
- `kernel-decision-intake-result.v1` as an orchestration result;
- the six-file immutable semantic lock and its verification;
- packet binding, anti-substitution, unsupported-claim rejection and deterministic status mapping;
- official pinned Kernel bridge/runner execution;
- Final Gate orchestration that reruns KROAD-011 from the raw intake;
- presentation-only decision receipt behavior.

Project Gate does not copy a Kernel schema as competing canonical truth and does not implement Resolver or L2 logic.

## Immutable Kernel pin

```yaml
repository: rezahh107/EV4-Decision-Kernel
accepted_commit: 76a82e28543ff8f0babca11b7d7dccac96b92894
semantic_dependencies:
  - kernel/schemas/decision-record.v2.schema.json
  - kernel/decision-governance/p0-decision-matrices.v0.json
  - kernel/decision-governance/resolver-rule-registry.v0.json
  - kernel/decision-governance/resolver-rules/layout-structure.v0.json
  - kernel/resolver-mvp/resolve-high-risk-p0.mjs
  - kernel/validator/validate-l2-decision-correctness.mjs
```

`package.json` and `package-lock.json` are toolchain dependencies only. Decision cards, vertical-slice manifests, downstream-consumer contracts, Architect fixtures and planning documents are not semantic acceptance evidence.

## Intake and binding behavior

The intake embeds every L2 input per packet: Decision Record, Resolver input and Audit Context. Project Gate rejects duplicate packet/decision IDs, wrapper drift, rule/version drift, evidence-ref mismatch, missing required references, provenance drift, claim-source drift, cross-packet substitution, unsupported claims and authored Kernel/Project Gate derived fields.

Authored L2 status, Resolver output, derived counts and evidence projection arrays are never trusted. The pinned Kernel audit is rerun and Kernel diagnostics are preserved unchanged under `upstream_diagnostics`.

## Evidence projection derivation

`source_evidence_refs` and `runtime_evidence_refs` are derived only from validated `decision_record.evidence_refs`:

- `source_type == project_export` is projected only to `source_evidence_refs`;
- `source_type == runtime_browser` is projected only to `runtime_evidence_refs`;
- other source types, including `manual_note` and `kernel_fixture`, are not projected.

Each projection preserves `evidence_id`, `source_type` and `ref` as `reference`. `audit_context.source_evidence_refs` and `audit_context.runtime_evidence_refs` are forbidden authored fields.

A carried `runtime_browser` reference is not evidence that Project Gate performed runtime or browser validation. It does not establish KROAD-013 completion, release readiness or production readiness.

## Status mapping

```text
L2 pass without a blocker                     → accepted
L2 pass with explicit human override only     → accepted + informational diagnostic
requires_reaudit                              → repair_needed
L2 fail                                       → invalid
known but unsupported family                  → insufficient_evidence
Resolver unresolvable                         → insufficient_evidence
schema/hash/identity/unknown-output failure    → invalid
Kernel checkout or process execution missing  → insufficient_evidence
unsupported assertion                         → invalid
```

Overall precedence is fail-closed: `invalid`, then `insufficient_evidence`, then `repair_needed`, then `accepted` only when every packet is accepted.

## Final Gate trust boundary

Final Gate accepts the raw `kernel_decision_intake` Stage Evidence Bundle, not a precomputed result as authority. During the current operation it reruns KROAD-011 with:

- the approved Kernel checkout;
- the committed Project Gate semantic lock;
- Project Gate-owned schemas;
- the official pinned Kernel bridge.

The result returned by that internal execution is the only intake result used for Final Gate authority. A supplied `kernel_decision_intake_result` is non-authoritative projection/cache data only. When supplied, it must exactly match the recomputed result; otherwise Final Gate fails closed.

An authored producer string, accepted status, boolean, execution record, unsigned hash or self-declared trust flag cannot authenticate Final Gate acceptance.

A complete legacy seven-field `decision_lineage` trace remains a compatibility projection only. It cannot authenticate Final Gate acceptance.

## Decision receipt trust boundary

Decision receipts remain presentation-only. A success receipt is available only while consuming the in-process authoritative Final Gate result created by the current Final Gate execution. The receipt does not search arbitrary nested input objects for an intake result and does not independently upgrade authored JSON to authority.

Serialization intentionally removes the in-process authority capability. A persisted or externally authored JSON object must be rerun through Final Gate before it can produce a success receipt.

Receipts do not create lineage, evidence, Kernel acceptance, downstream enforcement, release readiness or production readiness.

## Governance classification

`planning/DECISION_ESCAPE_ROUTES.yml` records KROAD-011 as `sequence_ci_enforced`. `downstream_contract_enforced` is not claimed because no inspected downstream producer rejection evidence establishes that level.

## Validation

Exact-head checks executed successfully:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run pytest
uv run pytest tests/kernel_decision_intake tests/transitions/test_final_gate.py tests/reports/test_decision_receipts.py tests/planning/test_decision_escape_routes_schema.py
uv run python scripts/check-capability-truth.py
uv run python scripts/check-workflow-permissions.py
uv run python scripts/check-github-action-pinning.py
uv run python scripts/check-runner-boundary.py
npm run status
npm run validate
```

The KROAD-011 workflow also reproduced and compared the committed semantic lock and ran the official pinned Kernel bridge smoke after:

```bash
cd ../EV4-Decision-Kernel
npm ci --ignore-scripts
npm run validate:mvk
```

## Evidence limits

All KROAD-011 fixtures in this PR are explicitly synthetic. This implementation does not prove a real non-synthetic handoff, Builder execution, runtime/browser validity, downstream producer integration, ecosystem readiness, release readiness or production readiness.

The `EV4-Decision-Kernel` evidence-closure and roadmap-memory update remain deferred to ordered PR 2 after this PR is merged and exact merged-main evidence exists.
