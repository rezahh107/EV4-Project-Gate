# EV4 Shared Contracts Governance

This document defines the minimal governance rules for `EV4-Shared-Contracts` while it remains a non-authoritative shared-contracts handbook.

## Current Authority Boundary

`EV4-Shared-Contracts` is a coordination repository only.

It may document:

- shared terminology
- role boundaries
- non-authoritative contract inventory
- compatibility boundaries
- readiness requirements
- promotion requirements
- migration and rollback expectations

It must not be treated as:

- a canonical schema source
- a runtime dependency target
- a replacement for repo-local schemas
- proof that a contract is promoted
- proof that producer or consumer validation passed

Existing repo-local schemas remain authoritative until a specific contract is promoted through an accepted ADR, a migration plan, rollback guidance, and CI-backed producer/consumer evidence.

## Decision Order

When deciding whether a shared contract action is allowed, use this order:

1. Repository guardrails in `AGENTS.md`.
2. Current state in `docs/EV4_SHARED_CONTRACTS_STATUS.md`.
3. Migration gates in `docs/MIGRATION_READINESS_CHECKLIST.md`.
4. Promotion gates in `docs/PROMOTION_RULES.md`.
5. Inventory and compatibility notes in `docs/CONTRACT_INVENTORY.md` and `docs/COMPATIBILITY_MAP.md`.
6. ADRs under `docs/ADR/`.

If these documents conflict, do not proceed with migration or promotion. Open a governance clarification patch or ADR instead.

## Contract Lifecycle States

Use these states consistently in documentation:

| State | Meaning | Allowed Action |
|---|---|---|
| `inventory-only` | Recorded for visibility only | clarify wording and ownership questions |
| `compatibility-only` | Exists to document current compatibility behavior | document limits and deprecation path |
| `adapter-boundary` | Defines a boundary between producer and consumer behavior | document normalization and rejection rules |
| `candidate-for-shared` | May later be proposed for promotion | prepare evidence and proposal only |
| `blocked-from-promotion` | Known drift or missing evidence makes promotion unsafe | report blockers; do not promote |
| `promotion-proposal` | A written proposal exists, but no canonical migration is approved | review evidence; do not add active schemas |
| `canonical-approved` | Future state only after accepted ADR and evidence | migrate only within the approved scope |
| `deprecated` | A contract or wrapper is being phased out | maintain compatibility plan and rollback path |

`canonical-approved` must not be used until the status file and an accepted ADR explicitly unlock the specific promotion.

## Minimum Contract Record

Before any contract can move beyond inventory-level documentation, the record must identify:

- contract or concept name
- version, if applicable
- current owner repository
- producer
- consumer
- current status
- promotion risk
- compatibility impact
- known drift or blockers
- required positive fixtures
- required negative fixtures
- required producer validation
- required consumer validation
- required cross-repo compatibility evidence
- migration and rollback requirements

Missing information must be marked as unknown. Do not fill gaps by assumption.

## Promotion Proposal Requirements

A promotion proposal may be prepared before migration, but it must remain proposal-only until all required evidence exists.

A proposal must include:

- owner repository
- producer and consumer roles
- schema or contract stability assessment
- versioning rule
- compatibility rule
- deprecation or migration strategy
- rollback guidance
- required fixtures
- required validation commands
- required CI evidence
- affected repositories
- explicit non-goals

A proposal must not add active schema files under `schemas/`.

## Migration Lock

Canonical migration remains blocked unless all of these are true:

- `docs/MIGRATION_READINESS_CHECKLIST.md` shows the relevant gates as complete with evidence
- an ADR explicitly approves the specific promotion
- producer validation evidence exists
- consumer validation evidence exists
- cross-repo compatibility evidence exists
- rollback guidance is written
- CI evidence is visible and linked or recorded

If any item is missing, the only valid output is a readiness report or promotion proposal.

## Evidence Classes

Use these evidence labels in reports and status updates:

| Label | Meaning |
|---|---|
| `confirmed` | verified from repository content or connector evidence |
| `static-only` | verified only by reading files, not by executing validation |
| `CI-verified` | backed by visible CI/check evidence |
| `blocked` | explicitly blocked by checklist, ADR, status file, or missing evidence |
| `assumption` | not verified; must not be used as proof |

Do not report CI as passed unless the matching workflow/check evidence is visible.

## Safe Phase 4 Work

Phase 4 may improve the handbook by adding or refining:

- governance vocabulary
- lifecycle states
- evidence labels
- promotion proposal templates
- compatibility wording
- deprecation policy wording
- status update discipline

Phase 4 must not:

- promote a contract
- migrate schemas
- add shared fixtures
- add shared validation scripts beyond skeleton-health helpers
- alter runtime behavior in any EV4 repository
- modify the four existing EV4 ecosystem repositories

## High-Risk Contract Guardrail

`ev4-builder-context-package@1.0.0` is blocked from first promotion while the historical split risk remains unresolved.

Current risk:

- Architect-side historical compatibility/deprecated wrapper
- Builder-side runtime intake package

Allowed work is limited to readiness reporting, naming/deprecation strategy, or compatibility clarification until the split is resolved and verified.

## Status Update Rule

After every repository-changing task, update `docs/EV4_SHARED_CONTRACTS_STATUS.md` with:

- current phase
- completed action
- branch
- commit SHA, or `pending final report` when the current SHA is not known at edit time
- PR number or URL, if available
- CI/check status
- files changed
- remaining blockers
- next immediate action
- one simple Persian mental model
