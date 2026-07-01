# AGENTS.md

## Repository Purpose

EV4-Shared-Contracts is currently a non-authoritative skeleton repository for future EV4 shared contracts.
It is not yet the canonical source of truth for schemas.
Existing repo-local schemas remain authoritative until explicitly promoted.
Canonical migration is blocked.

Keep this file concise and operational. Put long project history in `docs/EV4_SHARED_CONTRACTS_STATUS.md`, not here.

## First Files to Read

Read files in this order:

1. `AGENTS.md`
2. `docs/EV4_SHARED_CONTRACTS_STATUS.md`
3. `README.md`
4. `docs/MIGRATION_READINESS_CHECKLIST.md`
5. `docs/CONTRACT_INVENTORY.md`
6. `docs/COMPATIBILITY_MAP.md`
7. `docs/PROMOTION_RULES.md`
8. `docs/ADR/0001-non-authoritative-skeleton.md`

## Current Operating Mode

Current mode: skeleton / non-authoritative / coordination-only.
No canonical schemas are active.
No runtime dependencies should point to this repo yet.

## Repository Memory Model

Use these files as the repository's memory:

- `AGENTS.md` is the building entrance sign: where this is, what is allowed, and what is forbidden.
- `README.md` is the building brochure: what this repository is for.
- `docs/EV4_SHARED_CONTRACTS_STATUS.md` is the control-room status board: current phase, evidence, blockers, and next action.

A new chat should be able to continue safely by reading these three files first.

## EV4 Pipeline Mental Model

```text
Architect → Constructability Engineer → Builder → Responsive Architect
```

Architect designs and hands off intent.
Constructability Engineer proves execution readiness.
Builder executes only validated runtime intake or normalized CE executable packages.
Responsive Architect handles scoped responsive adaptation.
EV4-Shared-Contracts currently documents coordination rules only.

## Allowed Actions

Agents may:

- update documentation
- update the status dashboard
- update checklist status after verified work
- improve non-authoritative inventory clarity
- run skeleton checks
- fix skeleton-health workflow issues
- prepare promotion proposals as documents only, when explicitly requested

## Forbidden Actions

Agents must not:

- migrate canonical schemas
- add active schema files under `schemas/`
- declare this repository authoritative
- modify the four existing EV4 ecosystem repositories
- create runtime dependencies from existing repos to this repo
- promote any contract without explicit ADR, migration plan, rollback guidance, and CI evidence
- mark CI as passed without visible workflow evidence
- treat docs inventory as canonical schema authority

Existing EV4 ecosystem repositories that must not be modified from this branch:

```text
rezahh107/EV4-Architect-Repo
rezahh107/EV4-Constructability-Engineer-Repo
rezahh107/EV4-Builder-Assistant-Repo
rezahh107/EV4-Responsive-Architect
```

## Validation Commands

```bash
npm run status
npm run validate
```

These are skeleton-health checks only.
They do not validate canonical schemas because no canonical schemas are active yet.

## Directory Rules

- `schemas/` must contain `README.md` only until schema promotion is explicitly approved.
- `fixtures/` must contain `README.md` only until shared fixture migration is approved.
- `scripts/` may contain `README.md` and approved skeleton-health helper scripts only until shared validation scripts are approved.

Do not add active schema files, shared fixtures, or shared validation scripts without explicit promotion approval.

## Status Update Rule

After every completed phase or repository-changing task, update `docs/EV4_SHARED_CONTRACTS_STATUS.md` with:

- phase or task completed
- commit SHA
- PR number or PR URL, or `none yet`
- CI status, using `CI_PASSED`, `CI_FAILED`, `CI_PENDING`, `CI_NOT_TRIGGERED`, or `CI_NOT_VERIFIED`
- files changed
- next action
- one simple Persian mental model

If the current commit SHA or PR number is not known at edit time, write `pending final report` and update it in the next status pass.

## Reporting Rules

Final reports must be in Persian.

Keep repository names, branch names, commit SHAs, file paths, schema names, commands, workflow names, and identifiers in English.

Every report must clearly distinguish:

```text
confirmed
static-only
CI-verified
blocked
assumption
```

## Guardrail

Canonical migration remains blocked until explicitly unlocked by checklist completion, CI evidence, and promotion ADR.
