# EV4 Transition Boundary Map

Status: `PROMPT-05` adds Builder→Responsive transition orchestration and a Final Evidence Gate baseline. Project Gate remains a checkpoint: it pins, hashes, validates, calls official owner tools where available, emits diagnostics/results, and does not implement specialist semantics.

## Status vocabulary

Project Gate transition decisions use:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

`accepted` is allowed only when every transition-specific `accepted_requires` item is true and no blocking diagnostic exists.

## Architect → CE

```yaml
transition_id: ev4-architect-to-ce-transition@1.0.0
project_gate_status: implemented_synthetic_verified
source_repository: rezahh107/EV4-Architect-Repo
target_repository: rezahh107/EV4-Constructability-Engineer-Repo
```

Allowed Project Gate behavior:

```text
Architect Stage Evidence Bundle
→ Project Gate envelope validation
→ pinned Architect/CE contract hash checks
→ official Architect validator
→ deterministic Project Gate projection using CE-owned mapping contract
→ official CE validator
→ Architect→CE transition result validation
```

Forbidden Project Gate behavior:

```text
- create CE constructability decisions
- prove Elementor buildability
- authorize Builder runtime
- claim production readiness
```

## CE → Builder

```yaml
transition_id: ev4-ce-to-builder-transition@1.0.0
project_gate_status: ci_evidenced_baseline_with_synthetic_owner_fixture_smoke
source_repository: rezahh107/EV4-Constructability-Engineer-Repo
consumer_repository: rezahh107/EV4-Builder-Assistant-Repo
project_gate_lock: contracts/locks/ce-to-builder-transition.v1.lock.json
project_gate_result_schema: schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
```

Current boundary:

```text
CE Builder Executable Package
→ Project Gate envelope/package identity check
→ Project Gate lock verification for pinned CE and Builder owner files
→ official CE package validator
→ official Builder CE→Builder Contract Gate
→ official Builder adapter
→ Builder-owned context schema validation
→ official Builder output validator
→ Project Gate CE→Builder transition result
```

Project Gate must not copy CE or Builder canonical schemas, implement CE constructability rules, implement Builder normalization/adapter logic, bypass the Builder Contract Gate, silently repair CE output, or treat synthetic fixtures as real EV4 evidence.

## Builder → Responsive

```yaml
transition_id: ev4-builder-to-responsive-transition@1.0.0
project_gate_status: prompt_05_fail_closed_baseline
producer_repository: rezahh107/EV4-Builder-Assistant-Repo
consumer_repository: rezahh107/EV4-Responsive-Architect
project_gate_module: src/ev4_transition/transitions/builder_to_responsive.py
project_gate_lock: contracts/locks/builder-to-responsive-transition.v1.lock.json
project_gate_result_schema: schemas/builder-to-responsive-transition-result/builder-to-responsive-transition-result.v1.schema.json
```

Current boundary:

```text
Builder context / evidence handoff
→ Project Gate Builder evidence reference checks
→ Project Gate Builder/Responsive lock verification
→ Responsive-owned input schema load from owner repository
→ official Responsive input boundary validator when checkout is available
→ Project Gate Builder→Responsive transition result
```

Project Gate may verify Builder evidence refs, verify viewport evidence refs, verify lock role/path/hash identity, load the Responsive-owned input schema, run the Responsive-owned input boundary validator, and emit fail-closed diagnostics.

Project Gate must not invent Responsive input semantics, create a Project Gate-owned Responsive schema, implement Responsive repair logic, claim responsive correctness, treat raw screenshots as correctness evidence, or treat CI success as frontend evidence.

Current lock state:

```yaml
hash_state: placeholder_not_refreshed_from_owner_checkouts
accepted_state: intentionally_blocked_until_exact_owner_hash_refresh
```

## Final Evidence Gate

```yaml
gate_id: ev4-final-evidence-gate@1.0.0
project_gate_status: prompt_05_fail_closed_baseline
project_gate_module: src/ev4_transition/transitions/final_gate.py
project_gate_lock: contracts/locks/final-gate.v1.lock.json
project_gate_result_schema: schemas/final-gate-result/final-gate-result.v1.schema.json
```

Current boundary:

```text
Prior Project Gate lock manifests
→ Responsive output/evidence packet
→ Final Gate lock chain verification
→ Responsive-owned output schema load from owner repository
→ official Responsive output validator when checkout is available
→ forbidden readiness/correctness claim scan
→ Project Gate final evidence result
```

The Final Gate refuses `production_ready`, `release_ready`, `frontend_correctness`, `responsive_correctness`, accessibility completion, export validation completion, and any equivalent readiness claim unless explicit validated owner evidence exists. CI success is never counted as frontend evidence. Synthetic fixtures are never counted as real final evidence.
