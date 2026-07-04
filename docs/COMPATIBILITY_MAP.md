# EV4 Compatibility Map

This document records current compatibility boundaries only. It does not promote any schema or contract into shared canonical status.

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
verification_state: synthetic_fixture_only
real_cross_repository_validation: not_available
```

## CE → Builder

Planned Project Gate transition:

```text
ev4-ce-to-builder-transition@1.0.0
```

Implementation status:

```yaml
implemented: false
freeze_matrix: docs/CE_TO_BUILDER_FREEZE_MATRIX.md
```

Allowed future route:

```text
ev4-builder-executable-package@1.0.0
→ Builder CE→Builder Contract Gate
→ Builder CE→Builder adapter
→ ev4-builder-context-package@1.0.0
```

Project Gate later coordinates file-byte pins, hashes, official validators, official adapters, provenance, diagnostics, and handoff packaging for this route. CE and Builder remain the owners of their specialist behavior.

## Architect

`ev4-builder-context-package@1.0.0` is deprecated compatibility wrapper only.

`ev4-architect-builder-feed-export@1.0.0` is CE intake / non-executable handoff.

Architect-owned outputs are not Builder-executable output by default.

## Constructability Engineer

`EV4 Builder Executable Package` is the current CE → Builder adapter-side executable handoff.

It is not yet a shared canonical contract.

CE owns constructability review, execution-strategy gate, Builder Executable Package issuance, and execution prerequisites.

## Builder

Builder runtime intake remains local-authoritative inside Builder repo.

CE executable packages are normalized by Builder adapter before runtime use.

Builder rejects Architect-only packages as Builder-ready and rejects CE review-only packages as runtime-ready.

## Responsive Architect

Responsive reference-family linkage is local-authoritative inside Responsive repo for now.

It is not yet a canonical shared contract.

Responsive behavior is not inferred from desktop screenshots or raw screenshot authority.
