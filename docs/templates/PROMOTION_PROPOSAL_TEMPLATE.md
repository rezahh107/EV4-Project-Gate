# EV4 Promotion Proposal Template

Use this template to prepare a proposal for moving a repo-local contract or concept toward shared canonical status.

This template is proposal-only. Filling it out does not promote a contract, migrate a schema, add a runtime dependency, or make `EV4-Shared-Contracts` authoritative.

## 1. Proposal Summary

| Field | Value |
|---|---|
| Proposal title | `TBD` |
| Contract / concept name | `TBD` |
| Proposed version | `TBD` |
| Current lifecycle state | `inventory-only` / `compatibility-only` / `adapter-boundary` / `candidate-for-shared` / `blocked-from-promotion` |
| Proposed lifecycle state | `promotion-proposal` |
| Owner repo | `TBD` |
| Producer | `TBD` |
| Consumer | `TBD` |
| Affected repositories | `TBD` |
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
- promote `ev4-builder-context-package@1.0.0` while its split risk remains unresolved

## 3. Current Authority Boundary

Describe where the contract or concept is authoritative today.

| Question | Answer |
|---|---|
| Which repo currently owns it? | `TBD` |
| Is it schema-backed today? | `yes` / `no` / `unknown` |
| Is it runtime-facing today? | `yes` / `no` / `unknown` |
| Is it producer output, consumer intake, or adapter boundary? | `TBD` |
| Is there known naming/version drift? | `yes` / `no` / `unknown` |
| Does any repo depend on `EV4-Shared-Contracts` for runtime behavior today? | `no` |

Unknowns must stay marked as `unknown`. Do not fill them by assumption.

## 4. Producer / Consumer Map

| Role | Repository | Evidence | Status |
|---|---|---|---|
| Owner | `TBD` | `TBD` | `missing` |
| Producer | `TBD` | `TBD` | `missing` |
| Consumer | `TBD` | `TBD` | `missing` |
| Adapter / normalizer, if any | `TBD` | `TBD` | `missing` |

Allowed evidence labels:

- `confirmed`
- `static-only`
- `CI-verified`
- `blocked`
- `assumption`

## 5. Compatibility Assessment

| Compatibility question | Answer | Evidence |
|---|---|---|
| Is the current schema stable? | `yes` / `no` / `unknown` | `TBD` |
| Is versioning clear? | `yes` / `no` / `unknown` | `TBD` |
| Are older versions or wrappers involved? | `yes` / `no` / `unknown` | `TBD` |
| Would promotion freeze known drift? | `yes` / `no` / `unknown` | `TBD` |
| Would promotion rename a public contract? | `yes` / `no` / `unknown` | `TBD` |
| Is a deprecation path required? | `yes` / `no` / `unknown` | `TBD` |
| Is rollback documented? | `yes` / `no` / `unknown` | `TBD` |

If any answer is `unknown`, the proposal is not migration-ready.

## 6. Required Fixtures

Fixtures must be added in the owning / producing / consuming repositories first unless a future ADR explicitly approves shared fixtures.

| Fixture type | Required? | Repository | Path | Status |
|---|---:|---|---|---|
| Positive fixture | yes | `TBD` | `TBD` | `missing` |
| Negative fixture — missing required field | yes | `TBD` | `TBD` | `missing` |
| Negative fixture — wrong producer | yes | `TBD` | `TBD` | `missing` |
| Negative fixture — consumer rejection case | yes | `TBD` | `TBD` | `missing` |
| Compatibility fixture | if needed | `TBD` | `TBD` | `missing` |

## 7. Required Validation

| Validation | Command / Check | Repository | Required result | Current status |
|---|---|---|---|---|
| Producer validation | `TBD` | `TBD` | pass | `missing` |
| Consumer validation | `TBD` | `TBD` | pass | `missing` |
| Cross-repo compatibility test | `TBD` | `TBD` | pass | `missing` |
| Shared repo skeleton health | `npm run status && npm run validate` | `rezahh107/EV4-Shared-Contracts` | pass | `missing` |
| CI evidence | `TBD` | `TBD` | pass | `missing` |

Do not mark validation as passed without visible output or CI/check evidence.

## 8. Migration Plan

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

## 9. Rollback Guidance

If a future promotion breaks downstream work, downstream repositories must be able to return to repo-local authority.

Rollback plan:

| Area | Rollback action | Owner | Status |
|---|---|---|---|
| Producer | `TBD` | `TBD` | `missing` |
| Consumer | `TBD` | `TBD` | `missing` |
| Adapter / normalizer | `TBD` | `TBD` | `missing` |
| Documentation | `TBD` | `TBD` | `missing` |
| CI/checks | `TBD` | `TBD` | `missing` |

## 10. Risk Review

| Risk | Status | Notes |
|---|---|---|
| Premature canonicalization | `open` | Must remain proposal-only until ADR and evidence exist. |
| Runtime dependency creep | `open` | No runtime dependency may point to this repo yet. |
| Producer/consumer mismatch | `open` | Must be validated before migration. |
| Missing negative fixtures | `open` | Blocks promotion. |
| Missing rollback guidance | `open` | Blocks promotion. |
| Missing CI evidence | `open` | Blocks promotion. |
| `ev4-builder-context-package@1.0.0` split risk | `blocked` / `not applicable` | Must be resolved before this contract can be considered. |

## 11. Promotion Readiness Checklist

A proposal is not migration-ready until every item below is checked with evidence.

- [ ] owner repo is explicit
- [ ] producer is explicit
- [ ] consumer is explicit
- [ ] schema or contract is stable
- [ ] versioning is clear
- [ ] positive fixtures exist
- [ ] negative fixtures exist
- [ ] producer validation passes
- [ ] consumer validation passes
- [ ] cross-repo compatibility test exists
- [ ] deprecation/migration plan exists
- [ ] rollback guidance exists
- [ ] ADR exists or is drafted for review
- [ ] CI evidence exists

## 12. Final Verdict

Choose exactly one:

```text
PROPOSAL_ONLY
READY_FOR_ADR_REVIEW
BLOCKED_NEEDS_EVIDENCE
REJECT_PROMOTION_RISK
```

Default verdict:

```text
PROPOSAL_ONLY
```

## 13. Simple Mental Model

Write one simple Persian mental model here.

Example:

```text
این فرم مثل برگه پذیرش پرونده است. تا مهر مالک، تولیدکننده، مصرف‌کننده، تست، CI و راه برگشت نداشته باشد، پرونده وارد آرشیو رسمی نمی‌شود.
```
