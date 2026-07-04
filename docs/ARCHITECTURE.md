# EV4 Project Gate Architecture

Status: `PROMPT-01` Project Gate-owned contracts and deterministic core hardening.

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

Project Gate is a deterministic checkpoint/customs system. It is not a fifth EV4 specialist engine.

## Architectural authority

Project Gate may own:

- Stage Evidence Bundle envelope validation;
- Project Gate transition/result/diagnostic/lock carrier schemas;
- deterministic canonical JSON and SHA-256 utilities;
- file-byte hash verification for pinned external contracts;
- lock manifests and expected dependency configuration;
- structured diagnostics;
- transition orchestration that calls official specialist validators/adapters;
- machine-readable JSON results;
- Persian user-facing summaries;
- behavioral rule coverage tracking.

Project Gate must not own:

- Architect architecture decisions;
- CE constructability proof or implementation strategy;
- Builder runtime behavior or Elementor execution logic;
- Responsive repair semantics or viewport correctness claims;
- copied specialist schemas as competing canonical contracts;
- invented or silently normalized evidence.

## Current implemented architecture

```text
Stage Evidence Bundle JSON
→ BundleValidator
→ schema + semantic evidence checks
→ canonical JSON / SHA-256 hashes
→ structured diagnostics
→ transition-result.v1 JSON or Persian summary
```

Implemented package:

```text
src/ev4_transition
```

Prompt 01 adds explicit package namespaces without replacing the existing public modules:

```text
src/ev4_transition/core/
src/ev4_transition/stage_bundle/
src/ev4_transition/locks/
src/ev4_transition/presentation/status_mapping.py
```

Implemented Project Gate-owned schemas:

```text
schemas/stage-bundle/stage-bundle.v1.schema.json
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
schemas/diagnostic/diagnostic.v1.schema.json
schemas/lock-manifest/lock-manifest.v1.schema.json
```

These are envelope/result/diagnostic/lock carrier contracts only. They are not Architect, CE, Builder, or Responsive specialist schemas.

## Current transition architecture

### Architect → CE

Implemented transition:

```text
ev4-architect-to-ce-transition@1.0.0
```

Current flow:

```text
Architect Stage Evidence Bundle
→ Project Gate envelope validation
→ source identity validation
→ external pin/file-byte hash verification
→ pinned Architect payload schema validation
→ official Architect semantic validator
→ deterministic projection using CE-owned mapping contract
→ pinned CE intake schema validation
→ official CE semantic validator with source-bundle binding
→ CE Stage Evidence Bundle
→ architect-to-ce transition-result schema validation
```

Verification state:

```yaml
verification_state: synthetic_fixture_only
real_cross_repository_validation: not_available
```

### CE → Builder

Not implemented in Project Gate.

Allowed future flow:

```text
CE Builder Executable Package
→ Builder CE→Builder Contract Gate
→ Builder CE→Builder adapter
→ Builder Context Package
```

Project Gate may later pin/hash/call the official CE and Builder artifacts. It must not implement CE constructability logic or Builder adapter behavior internally.

### Builder → Responsive

Not implemented in Project Gate.

Allowed future flow:

```text
Builder output and build evidence
→ Project Gate pin/hash/validator orchestration
→ Responsive Builder-specific input eligibility boundary
→ Responsive output and viewport evidence
```

Responsive Builder-specific input eligibility is not responsive correctness. Project Gate must stay fail-closed on missing Builder evidence.

### Final evidence gate

Not implemented.

A future final gate must remain fail-closed unless explicit Responsive, frontend, export, accessibility, and production-readiness evidence exists and validates under the owning repository contracts.

## Determinism model

Implemented deterministic behavior:

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
file_byte_sha256: explicit helper
```

Canonical JSON hashing is suitable for deterministic evidence and lock operations. File-byte SHA-256 is used for external contract lock verification.

## Status model note

Target Project Gate transition statuses are:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

Current Stage Bundle validation and existing Architect→CE paths retain legacy `valid` compatibility. `src/ev4_transition/presentation/status_mapping.py` maps `valid` to `accepted` for presentation and exit-code behavior. Future transition-specific prompts should emit the target vocabulary directly once their evidence gates are implemented.

## UX/reporting boundary

Persian summaries must preserve result truth:

- status uses icon + text + semantic tone;
- `insufficient_evidence` is warning/blocking, not ordinary info;
- technical identifiers remain LTR/copyable;
- result immutability must not be changed by presentation.

## Current architecture classification

```yaml
repository_role: project_workflow_control_center
architecture_state: prompt_01_core_foundation_hardened
python_deterministic_core: implemented_initial_v1_plus_prompt_01_hardening
architect_to_ce_transition: implemented_synthetic_verified
ce_to_builder_transition: not_implemented
builder_to_responsive_transition: not_implemented
final_evidence_gate: not_implemented
ui: not_implemented
real_ev4_evidence_validation: not_available
```
