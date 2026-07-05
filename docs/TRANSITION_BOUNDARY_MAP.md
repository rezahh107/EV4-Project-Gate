# EV4 Transition Boundary Map

Status: `PROMPT-04` CE→Builder baseline is CI-evidenced on PR `#20` head `87a4a84640c999cee049a0d40865c25efabeafb0`. This map records Project Gate-owned orchestration boundaries. Specialist schemas and runtime logic remain owner-repository artifacts; Project Gate pins, hashes, validates, calls official tools, and emits diagnostics/results only.

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
verification_state: synthetic_fixture_and_ci_coverage_existing_before_PROMPT_04
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
source_commit: cfceec5c20269c75a1cc19b2675d7087cede4599
consumer_repository: rezahh107/EV4-Builder-Assistant-Repo
consumer_commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
project_gate_lock: contracts/locks/ce-to-builder-transition.v1.lock.json
project_gate_result_schema: schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
project_gate_transition_module: src/ev4_transition/transitions/ce_to_builder.py
ci_lock_verifier: scripts/verify-ce-to-builder-lock.py
ci_smoke: scripts/ce-to-builder-smoke.py
latest_checked_ci_run: 28741498875
latest_checked_ci_head: 87a4a84640c999cee049a0d40865c25efabeafb0
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

Project Gate may:

```text
- verify CE/Builder repository, commit, path, identity marker, and file-byte SHA-256 pins;
- run official CE validator through runner infrastructure;
- run official Builder Contract Gate through runner infrastructure;
- call the official Builder adapter only after the Builder gate passes;
- validate Builder output with Builder-owned schema and validator;
- record stdout/stderr hashes and structured execution records;
- emit accepted/invalid/insufficient_evidence diagnostics and a Project Gate-owned result envelope.
```

Project Gate must not:

```text
- copy CE or Builder canonical schemas into Project Gate;
- implement CE constructability rules;
- implement Builder normalization/adapter logic;
- bypass the Builder Contract Gate;
- silently repair or normalize CE output;
- treat synthetic fixtures as real EV4 evidence;
- emit accepted when any accepted_requires item is false.
```

Important current limitation:

```yaml
lock_hash_state: exact_file_byte_sha256_values_committed_from_pinned_owner_ci_checkouts
merge_state: ci_green_but_pr_kept_draft_pending_review
real_handoff_evidence_state: not_proven_by_PROMPT_04_smoke
```

## Builder → Responsive

```yaml
transition_id: ev4-builder-to-responsive-transition@1.0.0
project_gate_status: not_implemented
producer_repository: rezahh107/EV4-Builder-Assistant-Repo
consumer_repository: rezahh107/EV4-Responsive-Architect
```

Current boundary remains future-only:

```text
verified Builder execution evidence
→ future Project Gate transport/eligibility checks
→ Responsive-owned input validation
→ Responsive output and viewport evidence
```

Project Gate must not claim Responsive correctness, frontend correctness, accessibility completion, export validation completion, or production readiness before explicit Responsive/frontend evidence exists.
