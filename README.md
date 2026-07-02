# EV4 Shared Contracts

This repository is currently a non-authoritative skeleton.
No canonical EV4 schemas are active here yet.
Existing repo-local schemas remain authoritative until explicitly promoted.
Canonical migration is blocked until full validation/CI evidence exists.
Patch 1 role alignment is a prerequisite, not final proof.

**Current readiness: skeleton only. Canonical schema migration remains blocked.**

## Repository Memory Files

For AI coding agents and future chats:

- `AGENTS.md` is the building entrance sign: what this repository is, what is allowed, and what is forbidden.
- `README.md` is the building brochure: the short human-facing overview.
- `docs/EV4_SHARED_CONTRACTS_STATUS.md` is the control-room status board: current phase, commit/PR/CI evidence, changed files, next action, and simple mental model.

Read `AGENTS.md` first.
Current project status is tracked in `docs/EV4_SHARED_CONTRACTS_STATUS.md`.

## Purpose

`EV4-Shared-Contracts` is a coordination repository for future EV4 shared contracts. Its current purpose is to collect role-boundary documentation, non-authoritative contract inventory, compatibility notes, migration-readiness criteria, validation strategy, and promotion rules.

This repository is not yet a canonical shared contract source.

## Governance Documents

Use these documents as the current handbook surface:

- `docs/GOVERNANCE.md` — minimal shared governance rules, lifecycle states, evidence labels, and migration lock.
- `docs/CONTRACT_INVENTORY.md` — non-authoritative contract and concept inventory.
- `docs/COMPATIBILITY_MAP.md` — current compatibility boundaries only.
- `docs/MIGRATION_READINESS_CHECKLIST.md` — gates that must be satisfied before canonical migration.
- `docs/PROMOTION_RULES.md` — required evidence before any shared canonical promotion.
- `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md` — proposal-only intake form for future promotion candidates.
- `docs/ADR/0001-non-authoritative-skeleton.md` — accepted decision to start as a non-authoritative skeleton.

If these documents appear to conflict, do not migrate or promote anything. Add a governance clarification patch or ADR instead.

## Current Status

The repository is initialized as a clean, minimal, non-authoritative skeleton.

Current EV4 readiness state:

- Static role-boundary evidence: mostly confirmed
- Constructability Engineer validation evidence: partially available
- Full cross-repo CI evidence: incomplete
- Canonical schema migration: blocked
- Shared-contract readiness: skeleton only

## EV4 Pipeline

```text
Architect → Constructability Engineer → Builder → Responsive Architect
```

## Role Boundaries

### Architect

Owns approved design/handoff intent, `reference_role`, `experience_intent`, desired outcome, design-level source evidence, and approved architecture handoff.

Must not own Builder executable authorization, Builder runtime intake, CE execution proof, or responsive behavior inference. Architect must not emit Builder-executable output by default.

### Constructability Engineer

Owns constructability review, execution-strategy gate, Builder Executable Package issuance, and execution prerequisites.

Carries or produces `golden_reference_contract`, `reference_paradigm_lock`, `paradigm_to_structure_map`, `build_intent_brief`, `spatial_lexicon_version_used`, `visual_tolerance_policy`, and optional/advisory `experience_intent`.

### Builder

Owns runtime intake validation, CE package normalization, rendering/execution, and Builder-side gates.

Consumes only validated Builder runtime intake packages and normalized CE Builder Executable Packages. Builder must not invent Golden Reference, Build Intent Brief, Spatial Lexicon, visual intent, reference family, or responsive behavior.

### Responsive Architect

Owns responsive adaptation contracts, scoped Golden Reference family linkage, viewport-specific authorization, and responsive evidence gates.

Must not infer mobile/tablet behavior from desktop screenshots and must not treat raw screenshots as responsive authority.

## What This Repository Is For Now

- Non-authoritative role-boundary map
- Non-authoritative contract/concept inventory
- Compatibility boundary documentation
- Migration-readiness checklist
- Minimal shared governance handbook
- Promotion proposal template
- Future validation strategy
- Future promotion rules
- ADRs for governance decisions

## What This Repository Is Not Yet

- Not a canonical schema source
- Not a runtime dependency target
- Not a replacement for repo-local schemas
- Not a producer/consumer validation authority
- Not a schema drift resolution patch

## Canonical Migration Warning

Do not import schemas from this repository yet. Do not treat any directory here as canonical until promotion is approved through an explicit ADR, migration plan, validation evidence, and rollback guidance.

Existing repo-local schemas remain authoritative until explicitly promoted.

## Next Safe Steps

1. Keep `docs/EV4_SHARED_CONTRACTS_STATUS.md` aligned with merged PR and CI evidence.
2. Use `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md` for proposal-only intake before any candidate is considered.
3. Harden minimal shared governance without promoting or migrating schemas.
4. Complete cross-repo validation evidence across all four EV4 repositories.
5. Resolve or safely rename/deprecate duplicate `ev4-builder-context-package@1.0.0` drift.
6. Confirm producer/consumer ownership for candidate contracts.
7. Add positive and negative fixtures in owning repositories first.
8. Approve versioning, compatibility, migration, and rollback policies.
9. Promote shared contracts only through explicit ADRs.
