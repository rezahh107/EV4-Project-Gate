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
→ ev4-ce-architect-stage-intake@1.0.0
```

The transition uses the CE-owned mapping contract:

```text
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
verification_state: verified_by_synthetic_fixture
real_cross_repository_validation: not_available
```

## Architect

`ev4-builder-context-package@1.0.0` is deprecated compatibility wrapper only.

`ev4-architect-builder-feed-export@1.0.0` is CE intake / non-executable handoff.

Architect-owned outputs must not be treated as Builder-executable output by default.

## Constructability Engineer

`EV4 Builder Executable Package` is the current CE → Builder adapter-side executable handoff.

It is not yet a shared canonical contract.

CE owns constructability review, execution-strategy gate, Builder Executable Package issuance, and execution prerequisites.

## Builder

Builder runtime intake remains local-authoritative inside Builder repo.

CE executable packages must be normalized by Builder adapter before runtime use.

Builder must reject Architect-only packages as Builder-ready and must reject CE review-only packages as runtime-ready.

## Responsive Architect

Responsive reference-family linkage is local-authoritative inside Responsive repo for now.

It is not yet a canonical shared contract.

Responsive behavior must not be inferred from desktop screenshots or raw screenshot authority.
