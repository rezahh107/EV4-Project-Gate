# EV4 Shared Contracts

This repository is currently a non-authoritative skeleton.
No canonical EV4 schemas are active here yet.
Existing repo-local schemas remain authoritative until explicitly promoted.
Canonical migration is blocked until full validation/CI evidence exists.
Patch 1 role alignment is a prerequisite, not final proof.

**Current readiness: skeleton only. Canonical schema migration remains blocked.**

## Purpose

`EV4-Shared-Contracts` is a coordination repository for future EV4 shared contracts. Its current purpose is to collect role-boundary documentation, non-authoritative contract inventory, compatibility notes, migration-readiness criteria, validation strategy, and promotion rules.

This repository is not yet a canonical shared contract source.

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

1. Complete cross-repo validation evidence across all four EV4 repositories.
2. Resolve or safely rename/deprecate duplicate `ev4-builder-context-package@1.0.0` drift.
3. Confirm producer/consumer ownership for candidate contracts.
4. Add positive and negative fixtures in owning repositories first.
5. Approve versioning, compatibility, migration, and rollback policies.
6. Promote shared contracts only through explicit ADRs.
