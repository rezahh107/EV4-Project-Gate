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

Project Gate may own Stage Evidence Bundle validation, Project Gate result/diagnostic/lock carriers, canonical JSON and SHA-256, exact external file-byte pin verification, runner-based orchestration of official specialist tools, diagnostics, machine-readable results, Persian summaries, and behavioral coverage tracking.

Project Gate must not own Architect decisions, CE constructability logic, Builder runtime or adapter logic, Responsive repair logic, copied specialist schemas, invented evidence, or silent normalization.

## Capability truth

```yaml
architect_to_ce:
  orchestration_baseline: implemented
  cli_exposure: implemented
  verification_state: synthetic_fixture_only
ce_to_builder:
  orchestration_baseline: implemented
  cli_exposure: not_implemented
  owner_fixture_integration: verified
  real_non_synthetic_handoff: insufficient_evidence
builder_to_responsive:
  orchestration_baseline: not_implemented
final_evidence_gate:
  orchestration_baseline: not_implemented
```

The machine-readable source is `src/ev4_transition/data/capability-status.v1.json`.

## Deterministic foundation

```text
Stage Evidence Bundle JSON
→ BundleValidator
→ schema + semantic evidence checks
→ canonical JSON / SHA-256 hashes
→ structured diagnostics
→ Project Gate result JSON or Persian summary
```

Project Gate-owned schemas include envelope, result, diagnostic, lock, behavioral coverage, validator evidence, Architect→CE result, and CE→Builder result carriers. They are not specialist-domain schemas.

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

Not implemented in Project Gate. Future work must remain fail-closed until Builder-owned output/evidence and Responsive-owned input requirements are explicit, pinned, and validated.

## Final evidence gate

Not implemented. It must not emit final readiness without explicit owning-repository evidence for Responsive, frontend, export, accessibility, and production-readiness concerns.

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
