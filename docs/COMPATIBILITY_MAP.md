# EV4 Compatibility Map

This document records current compatibility boundaries only. It does not promote any specialist schema or contract into shared canonical status.

## Architect → CE

Implemented Project Gate transition:

```text
ev4-architect-to-ce-transition@1.0.0
```

Allowed path:

```text
ev4-architect-stage-payload@1.0.0
→ ev4-ce-architect-stage-intake@1.1.0
```

The transition uses the CE-owned mapping contract:

```text
ev4-architect-stage-to-ce-intake-mapping@1.1.0
```

Historical compatibility-only path:

```text
ev4-ce-architect-stage-intake@1.0.0
ev4-architect-stage-to-ce-intake-mapping@1.0.0
```

Blocked paths:

```text
ev4-architect-output-contract@1.0.0
/builder-feed-export
Builder-ready claims before CE processing
```

Validation state:

```yaml
orchestration_baseline: implemented
cli_exposure: implemented
verification_state: synthetic_fixture_only
real_non_synthetic_handoff: insufficient_evidence
```

## CE → Builder

Implemented Project Gate orchestration baseline:

```text
ev4-ce-to-builder-transition@1.0.0
```

Layered status:

```yaml
orchestration_baseline: implemented
cli_exposure: not_implemented
owner_fixture_integration: verified
real_non_synthetic_handoff: insufficient_evidence
```

Allowed orchestration route:

```text
ev4-builder-executable-package@1.0.0
→ Project Gate owner-pin and file-byte verification
→ official CE validator
→ Builder CE→Builder Contract Gate
→ official Builder adapter
→ ev4-builder-context-package@1.0.0
→ official Builder output validator
→ Project Gate transition result
```

Project Gate coordinates exact owner pins, hashes, official validators, official adapters, provenance, diagnostics, and result packaging. CE and Builder remain authoritative for their specialist behavior.

PR #20 workflow run `28744810186` verified the owner-fixture integration path on head `42bfa484481c585f589d86c40424660c70b038a0`. This does not prove a real non-synthetic handoff and does not expose CE→Builder as a public CLI command.

## Builder → Responsive

Planned Project Gate transition:

```text
ev4-builder-to-responsive-transition@1.0.0
```

Implementation status:

```yaml
orchestration_baseline: not_implemented
cli_exposure: not_implemented
freeze_matrix: docs/BUILDER_TO_RESPONSIVE_FREEZE_MATRIX.md
builder_formal_responsive_export: not_implemented
responsive_builder_specific_input_schema: not_implemented
```

Future route:

```text
Builder output and build evidence
→ Project Gate file-byte pin/hash and validator orchestration
→ Responsive input boundary
→ Responsive output and viewport evidence
```

Project Gate must not claim an accepted Builder→Responsive handoff until Builder-owned output/evidence artifacts and Responsive-owned input requirements exist and pass official validators.

## Repository authority notes

### Architect

`ev4-builder-context-package@1.0.0` is a deprecated compatibility wrapper only. Architect-owned outputs are not Builder-executable output by default.

### Constructability Engineer

`EV4 Builder Executable Package` is the CE-owned executable handoff. It is not a shared canonical contract. CE owns constructability review, execution-strategy proof, package issuance, and execution prerequisites.

### Builder

Builder runtime intake remains local-authoritative. CE executable packages are normalized by the official Builder adapter after the Builder contract gate passes. Builder does not yet define a single formal Builder→Responsive export schema.

### Responsive Architect

Responsive reference-family linkage and responsive output remain local-authoritative. Responsive behavior must not be inferred from desktop screenshots or raw screenshot authority.

### Prompt 0 common-contract foundation note

Stage Bundle v1 remains the canonical single-stage evidence envelope. Producer Gate Export v1 is a Project Gate-owned run-level complement that composes Stage Bundle v1 through `final_stage_bundle`; it is not a replacement Stage Bundle and does not define Producer-specific payload schemas or exact Producer stage sequences. The common-contract lock is Project Gate-owned and requires exact file-byte equality to a pinned immutable Project Gate commit; semantic JSON equality is not sufficient. Producer adoption, Project Gate runtime integration, and downstream Producer CI enforcement remain pending/not implemented, and real non-synthetic handoff evidence remains `insufficient_evidence`. The canonical Producer pin is pending merge for PR #39; future Producer callers must pin the reusable workflow by immutable Project Gate commit SHA, not `@main`.
