# EV4 Project Gate Architecture

## Mental model

```text
Architect
→ [Project Gate]
→ CE
→ [Project Gate]
→ Builder
→ [Project Gate]
→ Responsive
→ [Project Gate]
→ final evidence
```

Project Gate is a deterministic checkpoint system. It is not a fifth EV4 specialist engine.

## Architectural authority

Project Gate may own Stage Evidence Bundle validation, Project Gate result/diagnostic/lock carriers, canonical JSON and SHA-256, exact external file-byte pin verification, runner-based orchestration of official specialist tools, diagnostics, machine-readable results, Persian summaries, report rendering, atomic report writing, and behavioral coverage tracking.

Project Gate must not own Architect decisions, CE constructability logic, Builder runtime or adapter logic, Responsive repair logic, copied specialist schemas, invented evidence, or silent normalization.

## Capability truth

The machine-readable source is `src/ev4_transition/data/capability-status.v1.json`. The summary below reflects the closure audit after `PROMPT-06`:

```yaml
architect_to_ce:
  orchestration_baseline: implemented
  cli_exposure: implemented
  verification_state: synthetic_fixture_only
  real_non_synthetic_handoff: insufficient_evidence
ce_to_builder:
  orchestration_baseline: implemented
  cli_exposure: not_implemented
  owner_fixture_integration: verified
  real_non_synthetic_handoff: insufficient_evidence
builder_to_responsive:
  orchestration_baseline: implemented
  cli_exposure: not_implemented
  official_responsive_validator_integration: implemented
  real_non_synthetic_handoff: insufficient_evidence
final_evidence_gate:
  orchestration_baseline: implemented
  cli_exposure: not_implemented
  official_responsive_validator_integration: implemented
  real_non_synthetic_evidence: insufficient_evidence
user_interface:
  status: not_implemented
```

## Deterministic foundation

```text
Stage Evidence Bundle JSON
→ BundleValidator
→ schema + semantic evidence checks
→ canonical JSON / SHA-256 hashes
→ structured diagnostics
→ Project Gate result JSON or Persian summary
```

Project Gate-owned schemas include envelope, result, diagnostic, lock, behavioral coverage, validator evidence, Architect→CE result, CE→Builder result, Builder→Responsive result, and Final Gate result carriers. They are not specialist-domain schemas.

## Architect → CE

Implemented transition:

```text
ev4-architect-to-ce-transition@1.0.0
```

```text
Architect Stage Evidence Bundle
→ Project Gate envelope and source identity validation
→ external pin/file-byte hash verification
→ Architect-owned schema and official validator
→ deterministic projection using CE-owned mapping contract
→ CE-owned intake schema and official validator
→ CE Stage Evidence Bundle
→ Project Gate result validation
```

Verification remains `synthetic_fixture_only`; real non-synthetic handoff evidence is not available.

## CE → Builder

Implemented orchestration baseline:

```text
ev4-ce-to-builder-transition@1.0.0
```

```text
CE Stage Evidence Bundle or Builder Executable Package
→ Project Gate identity and evidence checks
→ exact CE/Builder lock verification
→ official CE package validator
→ official Builder Contract Gate
→ official Builder adapter
→ Builder-owned context schema
→ official Builder output validator
→ Project Gate CE→Builder result
```

Official tools execute only through `src/ev4_transition/runners/`. Project Gate does not implement their specialist rules.

Owner-fixture integration is verified by PR #20 workflow run `28744810186` on head `42bfa484481c585f589d86c40424660c70b038a0`. This is not real non-synthetic handoff evidence. CE→Builder is not exposed as a general public CLI transition.

## Builder → Responsive

Implemented orchestration baseline:

```text
ev4-builder-to-responsive-transition@1.0.0
```

```text
Builder evidence references and Responsive input packet
→ Project Gate identity and evidence checks
→ exact Builder/Responsive lock verification
→ Responsive-owned input schema validation
→ official Responsive input boundary validator through runner infrastructure
→ Project Gate Builder→Responsive result
```

Exact-head Prompt-05 evidence is recorded in `docs/handoffs/PROMPT-05_HANDOFF.md`. The baseline proves pinned owner-contract and official-validator integration, not real non-synthetic Builder execution, Responsive correctness, frontend correctness, accessibility completion, export validation, or production readiness.

Builder→Responsive is not exposed as a public CLI transition.

## Final evidence gate

Implemented orchestration baseline:

```text
ev4-final-evidence-gate@1.0.0
```

```text
Final evidence packet
→ immutable prior lock-chain verification
→ Responsive-owned output schema validation
→ official Responsive output validator through runner infrastructure
→ forbidden readiness/correctness claim checks
→ Project Gate Final Gate result
```

The final gate must not emit final readiness without explicit owning-repository evidence for Responsive, frontend, export, accessibility, and production-readiness concerns. Real non-synthetic final evidence remains `insufficient_evidence`.

Final Evidence Gate is not exposed as a public CLI transition.

## Persian reports and output writing

`PROMPT-06` adds an implementation-ready CLI/report layer:

```text
Project Gate result
→ non-mutating Persian plain-text / Markdown report rendering
→ status icon + text + semantic tone
→ RTL Persian container with LTR-isolated technical fragments
→ atomic output writer
```

Report rendering must not change transition decisions, add diagnostics, repair evidence, normalize specialist output, or include progress events in canonical final result hashes.

## Determinism model

```yaml
canonicalization: ev4-canonical-json.v1
key_ordering: deterministic_lexicographic
array_ordering: preserved
encoding: utf8
serialization: compact_json
nan_and_infinity: rejected
implicit_current_timestamp: not_generated
hidden_unicode_normalization: not_performed
hash_algorithm: sha256
file_byte_sha256: explicit_helper
```
