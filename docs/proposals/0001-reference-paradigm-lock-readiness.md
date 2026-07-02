# Proposal 0001: reference_paradigm_lock Readiness

Status: `PROPOSAL_ONLY`

Lifecycle target: `promotion-proposal`

This document starts Phase 5 with a proposal-only readiness pass. It does not promote a contract, migrate a schema, add fixtures, add validation scripts, create runtime dependencies, or make `EV4-Shared-Contracts` authoritative.

## 1. Proposal Summary

| Field | Value |
|---|---|
| Proposal title | `reference_paradigm_lock` readiness proposal |
| Contract / concept name | `reference_paradigm_lock` |
| Proposed version | `TBD` |
| Current lifecycle state | `candidate-for-shared` |
| Proposed lifecycle state | `promotion-proposal` |
| Owner repo | `rezahh107/EV4-Constructability-Engineer-Repo` |
| Producer | `Constructability Engineer` |
| Consumer | `Builder`, after CE-owned executable handoff / adapter normalization |
| Affected repositories | `rezahh107/EV4-Constructability-Engineer-Repo`, `rezahh107/EV4-Builder-Assistant-Repo`, future `rezahh107/EV4-Shared-Contracts` only if promotion is later approved |
| Proposal status | `draft` |

## 2. Non-Goals

This proposal must not:

- add active schema files under `schemas/`
- add shared fixtures under `fixtures/`
- add shared runtime validation scripts
- create runtime dependencies from EV4 repos to this repo
- modify the four existing EV4 ecosystem repositories
- declare this repository authoritative
- bypass producer/consumer validation
- promote `ev4-builder-context-package@1.0.0`

## 3. Why This Candidate

`reference_paradigm_lock` is a safer first proposal-only candidate than `ev4-builder-context-package@1.0.0` because the latter has a known split between Architect-side compatibility behavior and Builder-side runtime intake behavior.

`reference_paradigm_lock` is still not migration-ready. It is selected only for readiness mapping because the inventory already identifies it as CE-carried/produced and requiring producer/consumer compatibility tests.

## 4. Current Authority Boundary

| Question | Answer |
|---|---|
| Which repo currently owns it? | `rezahh107/EV4-Constructability-Engineer-Repo` |
| Is it schema-backed today? | `unknown` |
| Is it runtime-facing today? | `unknown` |
| Is it producer output, consumer intake, or adapter boundary? | CE-carried or CE-produced concept consumed downstream by Builder after valid handoff |
| Is there known naming/version drift? | `unknown` |
| Does any repo depend on `EV4-Shared-Contracts` for runtime behavior today? | `no` |

Unknowns remain marked as `unknown`. They must not be filled by assumption.

## 5. Producer / Consumer Map

| Role | Repository | Evidence | Status |
|---|---|---|---|
| Owner | `rezahh107/EV4-Constructability-Engineer-Repo` | `docs/CONTRACT_INVENTORY.md` lists `reference paradigm lock` as CE-carried or CE-produced | `static-only` |
| Producer | `Constructability Engineer` | Current inventory wording says CE carries or produces `reference_paradigm_lock` | `static-only` |
| Consumer | `rezahh107/EV4-Builder-Assistant-Repo` | Downstream Builder consumption is implied by CE → Builder handoff boundaries, but direct Builder validation evidence is not recorded here yet | `blocked` |
| Adapter / normalizer | Builder adapter / runtime intake path | Needs direct Builder repo evidence | `missing` |

## 6. Compatibility Assessment

| Compatibility question | Answer | Evidence |
|---|---|---|
| Is the current schema stable? | `unknown` | No schema evidence recorded in this repo |
| Is versioning clear? | `unknown` | No approved versioning policy recorded for this concept |
| Are older versions or wrappers involved? | `unknown` | Needs source repo audit |
| Would promotion freeze known drift? | `unknown` | Needs CE and Builder evidence |
| Would promotion rename a public contract? | `unknown` | Needs source repo audit |
| Is a deprecation path required? | `unknown` | Cannot decide without current source shape |
| Is rollback documented? | `no` | No rollback guidance exists yet for this candidate |

If any answer is `unknown`, this proposal is not migration-ready.

## 7. Required Fixtures

Fixtures must be added in the owning / producing / consuming repositories first unless a future ADR explicitly approves shared fixtures.

| Fixture type | Required? | Repository | Path | Status |
|---|---:|---|---|---|
| Positive fixture | yes | `rezahh107/EV4-Constructability-Engineer-Repo` | `TBD` | `missing` |
| Negative fixture — missing `reference_paradigm_lock` when required | yes | `rezahh107/EV4-Constructability-Engineer-Repo` and/or `rezahh107/EV4-Builder-Assistant-Repo` | `TBD` | `missing` |
| Negative fixture — wrong producer / non-CE source | yes | `rezahh107/EV4-Builder-Assistant-Repo` | `TBD` | `missing` |
| Negative fixture — Builder accepts package before CE executable authorization | yes | `rezahh107/EV4-Builder-Assistant-Repo` | `TBD` | `missing` |
| Compatibility fixture | if needed | `TBD` | `TBD` | `missing` |

## 8. Required Validation

| Validation | Command / Check | Repository | Required result | Current status |
|---|---|---|---|---|
| Producer validation | `TBD` | `rezahh107/EV4-Constructability-Engineer-Repo` | pass | `missing` |
| Consumer validation | `TBD` | `rezahh107/EV4-Builder-Assistant-Repo` | pass | `missing` |
| Cross-repo compatibility test | `TBD` | `TBD` | pass | `missing` |
| Shared repo skeleton health | `npm run status && npm run validate` | `rezahh107/EV4-Shared-Contracts` | pass | `missing` |
| CI evidence | `TBD` | `TBD` | pass | `missing` |

Do not mark validation as passed without visible output or CI/check evidence.

## 9. Migration Plan

Migration is blocked until this proposal is accepted through a future ADR.

If this proposal later becomes eligible, define:

1. exact source schema or contract location
2. exact target location, if any
3. version naming rule
4. compatibility rule
5. deprecation rule
6. producer update path
7. consumer update path
8. adapter or normalization impact
9. documentation changes
10. CI/check additions

Current migration status:

```text
blocked
```

## 10. Rollback Guidance

If a future promotion breaks downstream work, downstream repositories must be able to return to repo-local authority.

| Area | Rollback action | Owner | Status |
|---|---|---|---|
| Producer | Keep CE repo-local authority and remove any shared import/use | `rezahh107/EV4-Constructability-Engineer-Repo` | `draft` |
| Consumer | Keep Builder local validation and reject unapproved shared package assumptions | `rezahh107/EV4-Builder-Assistant-Repo` | `draft` |
| Adapter / normalizer | Keep Builder adapter behavior local until approved shared compatibility tests exist | `rezahh107/EV4-Builder-Assistant-Repo` | `draft` |
| Documentation | Revert proposal state to `candidate-for-shared` or `blocked-from-promotion` | `rezahh107/EV4-Shared-Contracts` | `draft` |
| CI/checks | Disable only future candidate-specific shared checks, not repo-local checks | owning repo(s) | `draft` |

Rollback guidance is draft-only and does not approve promotion.

## 11. Risk Review

| Risk | Status | Notes |
|---|---|---|
| Premature canonicalization | `open` | This document is proposal-only. |
| Runtime dependency creep | `open` | No runtime dependency may point to this repo yet. |
| Producer/consumer mismatch | `open` | Builder consumer evidence is missing. |
| Missing negative fixtures | `open` | Blocks promotion. |
| Missing rollback guidance | `draft` | Needs future ADR-level hardening. |
| Missing CI evidence | `open` | Blocks promotion. |
| `ev4-builder-context-package@1.0.0` split risk | `not applicable` | This proposal does not promote that contract. |

## 12. Promotion Readiness Checklist

This proposal is not migration-ready until every item below is checked with evidence.

- [x] owner repo is explicit — `static-only`
- [x] producer is explicit — `static-only`
- [ ] consumer is explicit with direct repo evidence
- [ ] schema or contract is stable
- [ ] versioning is clear
- [ ] positive fixtures exist
- [ ] negative fixtures exist
- [ ] producer validation passes
- [ ] consumer validation passes
- [ ] cross-repo compatibility test exists
- [ ] deprecation/migration plan exists
- [ ] rollback guidance exists at ADR-ready quality
- [ ] ADR exists or is drafted for review
- [ ] CI evidence exists

## 13. Final Verdict

```text
PROPOSAL_ONLY
```

`reference_paradigm_lock` is suitable for a first readiness proposal, but it is not suitable for canonical migration.

## 14. Simple Mental Model

این سند مثل فرم پذیرش یک پرونده است.

نام پرونده نوشته شده و مالک اولیه مشخص است، اما هنوز مهر تست، مصرف‌کننده، CI، نسخه، fixture و راه برگشت ندارد.

پس پرونده فقط روی میز بررسی می‌ماند و وارد آرشیو رسمی schemaها نمی‌شود.
