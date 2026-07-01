# EV4 Compatibility Map

This document records current compatibility boundaries only. It does not promote any schema or contract into shared canonical status.

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
