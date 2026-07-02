# EV4 Shared Contracts Status

## 1. Current Status Summary

```text
EV4-Shared-Contracts currently exists as a non-authoritative shared-contracts handbook skeleton.
Canonical schema migration remains blocked.
PR #3 was merged into main.
Skeleton Health for PR #3 completed successfully.
Phase 4.1 promotion proposal template work is in progress on a dedicated branch.
```

- Repository: `rezahh107/EV4-Shared-Contracts`
- Main branch: `main`
- Active work branch: `phase4.1/promotion-proposal-template`
- Last merged PR: `#3` — `Start Phase 4 minimal shared governance`
- PR #3 merge commit: `21119349b8090eb4b0b501b00689e4dcc26dc2c9`
- PR #3 head commit: `df83f681de8c72d499d9f3f5ce231d6422a96e22`
- PR #3 Skeleton Health: `CI_PASSED`
- Current Phase 4.1 work commits:
  - `842e61c8f223e3efd8d7831169d5f3d6b093e4da` — added `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md`
  - `04d6c7d477ed1c9d620f9ac34a966ba17b25129c` — linked proposal template from `README.md`
  - `pending final report` — this status update commit
- Current status: `promotion proposal template branch prepared`
- Canonical migration: `blocked`
- CI status for current branch: `CI_NOT_TRIGGERED` until a PR/check run is visible for this branch

## 2. Mental Model

چهار repo اصلی EV4 مثل چهار کارگاه جدا هستند.

`EV4-Shared-Contracts` مثل دفتر مرکزی قوانین است. آیین‌نامه داخلی وارد دفتر شده است. حالا فرم پذیرش پرونده‌ها آماده می‌شود تا هیچ contract بدون مهر مالک، تولیدکننده، مصرف‌کننده، تست، CI و راه برگشت وارد صف رسمی نشود.

هنوز اداره رسمی ثبت schemaها نیست.

## 3. Completed Work

- [x] Cross-repo drift was audited.
- [x] Patch 1 — Cross-Repo Role Alignment was implemented.
- [x] Patch 1 hardening was statically confirmed.
- [x] Architect direct-to-Builder execution was downgraded.
- [x] CE role as execution gate was clarified.
- [x] Builder runtime intake ownership was clarified.
- [x] Responsive Golden Reference family/scope linkage was added.
- [x] EV4-Shared-Contracts repository was created by the user.
- [x] Non-authoritative skeleton was initialized.
- [x] Skeleton local checks passed during skeleton initialization.
- [x] No canonical schemas were migrated.
- [x] Existing EV4 repos were not modified during skeleton initialization.
- [x] Project status dashboard was added.
- [x] Repository-level agent guidance was added in `AGENTS.md`.
- [x] Repository memory rule was added to `AGENTS.md`.
- [x] README explains the three memory files: `AGENTS.md`, `README.md`, and `docs/EV4_SHARED_CONTRACTS_STATUS.md`.
- [x] PR #2 was merged into `main`.
- [x] `Skeleton Health` for PR #2 completed with `success`.
- [x] Phase 4 minimal shared governance branch was started.
- [x] `docs/GOVERNANCE.md` was added as the minimal shared governance handbook.
- [x] `README.md` was updated to point to the governance handbook.
- [x] PR #3 was opened for Phase 4 minimal shared governance.
- [x] PR #3 was merged into `main`.
- [x] `Skeleton Health` for PR #3 completed with `success`.
- [x] Phase 4.1 promotion proposal template branch was started.
- [x] `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md` was added as a proposal-only intake form.
- [x] `README.md` was updated to point to the promotion proposal template.

## 4. Known Limitations / Risks

- [!] Full CI evidence across all four EV4 repos is incomplete.  
  The ecosystem-wide validation set is still incomplete, so promotion cannot rely on full cross-repo CI evidence yet.

- [!] EV4-Shared-Contracts Phase 4.1 branch CI must be checked after opening a PR.  
  Do not report the current Phase 4.1 branch as CI-verified until a matching `Skeleton Health` run is visible and successful.

- [!] `ev4-builder-context-package@1.0.0` still has historical split risk.  
  This contract/version name has carried different producer and consumer assumptions historically.

- [!] Canonical schema migration is not allowed yet.  
  Shared schemas must wait for checklist approval, CI evidence, migration plan, rollback guidance, and promotion ADR.

- [!] Builder/CE adapter boundary still exists.  
  CE-to-Builder normalization remains a boundary that must be preserved until a safe shared contract is promoted.

## 5. Phase Checklist

| Phase | Goal | Status | Mental Image | Next Action |
|---|---|---|---|---|
| Phase 0 — Cross-repo role alignment | align Architect, CE, Builder, Responsive roles | mostly done, CI incomplete | road signs between workshops were corrected | no conceptual hardening unless CI reveals issues |
| Phase 1 — Shared repo skeleton | create non-authoritative coordination repo | completed | central office building created, but not legal archive yet | keep skeleton constraints intact |
| Phase 2 — Skeleton PR and merge | review and merge skeleton into main | completed | office documents received their first approval stamp | no further action unless CI history is needed |
| Phase 3 — Status-driven continuation | continue from repo memory files in a new chat | completed | project map pinned to the wall beside the entrance sign | continue reading `AGENTS.md`, `README.md`, and this file first |
| Phase 4 — Minimal shared governance | add only low-risk shared policies and vocabulary | completed | office wrote internal rules before accepting legal documents | keep governance current |
| Phase 4.1 — Promotion proposal intake | add proposal-only intake form | in progress | reception desk gets a required form for every future contract file | open PR and verify `Skeleton Health` |
| Phase 5 — First promotion candidate | choose one safe contract/concept for future promotion proposal | future | one document is reviewed before entering the archive | choose low-risk candidate; avoid `ev4-builder-context-package@1.0.0` first |
| Phase 6 — Canonical migration | migrate canonical schemas only after evidence | blocked | legal archive opens only after all locks are tested | wait for full CI and promotion approval |

## 6. Do / Do Not Rules

Do:

- keep `EV4-Shared-Contracts` non-authoritative for now
- use checklists before migration
- require CI evidence before promotion
- document mental model after each phase
- update this status file after each completed phase or repository-changing task
- read `AGENTS.md` first when an AI coding agent connects to this repo
- use `docs/GOVERNANCE.md` as the minimal Phase 4 handbook surface
- use `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md` as proposal-only intake before considering promotion candidates

Do not:

- do not migrate schemas yet
- do not make this repo source of truth yet
- do not touch the four existing EV4 repos from this branch
- do not promote `ev4-builder-context-package@1.0.0` first
- do not claim CI passed without workflow evidence
- do not treat `docs/GOVERNANCE.md` or the proposal template as authorization for canonical schema migration

## 7. Latest Completed Task Record

| Field | Value |
|---|---|
| Phase/task completed | Phase 4.1 start — promotion proposal template |
| Branch | `phase4.1/promotion-proposal-template` |
| Commit SHA | `842e61c8f223e3efd8d7831169d5f3d6b093e4da`, `04d6c7d477ed1c9d620f9ac34a966ba17b25129c`, `pending final report` |
| PR number or PR URL | `pending final report` |
| CI status | `CI_NOT_TRIGGERED` until this branch has a visible `Skeleton Health` run |
| Files changed | `docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md`, `README.md`, `docs/EV4_SHARED_CONTRACTS_STATUS.md` |
| Remaining blockers | canonical migration blocked; full cross-repo CI incomplete; `ev4-builder-context-package@1.0.0` split risk unresolved |
| Next action | Open PR from `phase4.1/promotion-proposal-template` to `main`, then check `Skeleton Health` |
| Simple Persian mental model | فرم پذیرش روی میز دفتر گذاشته شده، ولی آرشیو رسمی schemaها هنوز قفل است. |

## 8. Next Immediate Step

Open PR:

```text
phase4.1/promotion-proposal-template → main
```

Then:

```text
Wait for GitHub Actions / Skeleton Health result.
If CI passes, review and merge the Phase 4.1 template PR.
If CI does not trigger, report CI_NOT_TRIGGERED.
If CI fails, fix only skeleton-health issues.
```

## 9. New Chat Handoff Prompt

```text
You are helping me continue the EV4-Shared-Contracts workflow.

Read AGENTS.md first.
Then read docs/EV4_SHARED_CONTRACTS_STATUS.md.
Then read README.md.
Then read docs/GOVERNANCE.md.
Then read docs/templates/PROMOTION_PROPOSAL_TEMPLATE.md.

Do not perform canonical schema migration unless the status file and an accepted ADR explicitly unlock the specific promotion.

First, summarize:
1. current status
2. next immediate action
3. blocked actions
4. mental model

Then wait for my next instruction.
```

## 10. Update Protocol

After every completed phase or repository-changing task, update this file:

```text
- phase or task completed
- branch
- commit SHA
- PR number or PR URL, or none yet
- CI status
- files changed
- remaining blockers
- next action
- one simple Persian mental model
```

Allowed CI status values:

```text
CI_PASSED
CI_FAILED
CI_PENDING
CI_NOT_TRIGGERED
CI_NOT_VERIFIED
```

## 11. Final Guardrail

```text
Canonical migration remains blocked until explicitly unlocked by checklist, CI evidence, and promotion ADR.
```
