# KROAD-011 — Project Gate Intake

Status: implementation complete on the feature branch; exact-head pull-request CI and semantic-lock artifact confirmation remain pending.

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
- the Final Gate requirement for an accepted intake result;
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

Authored L2 status, Resolver output and derived counts are never trusted. The pinned Kernel audit is rerun and Kernel diagnostics are preserved unchanged under `upstream_diagnostics`.

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

## Final Gate and receipt compatibility

A complete legacy seven-field `decision_lineage` trace is now a compatibility projection only. It cannot authenticate Final Gate acceptance and cannot create a success receipt.

Final Gate acceptance requires a schema-valid `kernel-decision-intake-result.v1` with:

- the approved pin;
- all acceptance requirements true;
- actual L2 execution for every packet;
- every packet status `accepted`;
- no rejected or unresolved derived counts.

Decision receipts remain presentation-only. They do not create lineage, evidence, Kernel acceptance, downstream enforcement, release readiness or production readiness.

## Governance classification

`planning/DECISION_ESCAPE_ROUTES.yml` records KROAD-011 as `sequence_ci_enforced`. `downstream_contract_enforced` is not claimed because no inspected downstream producer rejection evidence establishes that level.

## Validation

Repository checks:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run pytest
uv run python scripts/check-capability-truth.py
uv run python scripts/check-workflow-permissions.py
uv run python scripts/check-github-action-pinning.py
uv run python scripts/check-runner-boundary.py
npm run status
npm run validate
```

KROAD-011 checks:

```bash
uv run pytest tests/kernel_decision_intake
uv run pytest tests/transitions/test_final_gate.py
uv run pytest tests/reports/test_decision_receipts.py
uv run pytest tests/planning/test_decision_escape_routes_schema.py
python scripts/compute-kernel-decision-intake-lock.py \
  --kernel-repo ../EV4-Decision-Kernel \
  --output /tmp/kernel-decision-intake-lock.json
```

Pinned Kernel checks:

```bash
cd ../EV4-Decision-Kernel
npm ci --ignore-scripts
npm run validate:mvk
```

## Evidence limits

All KROAD-011 fixtures in this PR are explicitly synthetic. This implementation does not prove a real non-synthetic handoff, Builder execution, runtime/browser validity, downstream producer integration, ecosystem readiness, release readiness or production readiness.

The `EV4-Decision-Kernel` evidence-closure and roadmap-memory update remain deferred to ordered PR 2 after this PR is merged and exact merged-main evidence exists.
