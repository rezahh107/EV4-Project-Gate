# EV4 Shared Contracts Status

## 1. Current Status Summary

```text
EV4-Shared-Contracts currently exists as a non-authoritative shared-contracts handbook skeleton.
Canonical schema migration remains blocked.
PR #2 was merged into main.
Skeleton Health for PR #2 completed successfully.
Phase 4 minimal shared governance is now open as PR #3.
```

- Repository: `rezahh107/EV4-Shared-Contracts`
- Main branch: `main`
- Active work branch: `phase4/status-and-minimal-governance`
- Active PR: `#3` — `Start Phase 4 minimal shared governance`
- Active PR URL: `https://github.com/rezahh107/EV4-Shared-Contracts/pull/3`
- Last merged PR: `#2` — `Add repository memory guidance and status handoff`
- PR #2 merge commit: `6ec4de7f5bb3a107fc99bb332c5cbdace5e2d66d`
- PR #2 head commit: `e1bba23cc388c3a94d578634baec37d791abbf34`
- PR #2 Skeleton Health: `CI_PASSED`
- Current Phase 4 work commits:
  - `e4cda4d8f27cbbae4931ee23c5ab69eab5da2c02` — added `docs/GOVERNANCE.md`
  - `4a9ee7f7d89cc9900de78b974d8004c53f7de629` — linked governance handbook from `README.md`
  - `2bcaad9ea8bfb42b9d92e09c17fa38e25f13b579` — updated status for Phase 4 governance work
  - `pending final report` — this PR-number status update commit
- Current status: `Phase 4 governance PR open`
- Canonical migration: `blocked`
- CI status for current PR: `CI_PENDING` until the latest matching `Skeleton Health` run completes

## 2. Mental Model

چهار repo اصلی EV4 مثل چهار کارگاه جدا هستند.

`EV4-Shared-Contracts` مثل دفتر مرکزی قوانین است. اسکلت دفتر ساخته و PR قبلی merge شده است. حالا آیین‌نامه داخلی دفتر در یک PR جدا روی میز بررسی است.

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

## 4. Known Limitations / Risks

- [!] Full CI evidence across all four EV4 repos is incomplete.  
  The ecosystem-wide validation set is still incomplete, so promotion cannot rely on full cross-repo CI evidence yet.

- [!] EV4-Shared-Contracts PR #3 CI is pending.  
  Do not report PR #3 as CI-verified until the matching `Skeleton Health` run is visible and successful.

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
| Phase 4 — Minimal shared governance | add only low-risk shared policies and vocabulary | PR open | office writes internal rules before accepting legal documents | verify `Skeleton Health` for PR #3 |
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

Do not:

- do not migrate schemas yet
- do not make this repo source of truth yet
- do not touch the four existing EV4 repos from this branch
- do not promote `ev4-builder-context-package@1.0.0` first
- do not claim CI passed without workflow evidence
- do not treat `docs/GOVERNANCE.md` as authorization for canonical schema migration

## 7. Latest Completed Task Record

| Field | Value |
|---|---|
| Phase/task completed | Phase 4 start — status update and minimal shared governance handbook |
| Branch | `phase4/status-and-minimal-governance` |
| Commit SHA | `e4cda4d8f27cbbae4931ee23c5ab69eab5da2c02`, `4a9ee7f7d89cc9900de78b974d8004c53f7de629`, `2bcaad9ea8bfb42b9d92e09c17fa38e25f13b579`, `pending final report` |
| PR number or PR URL | `#3` — `https://github.com/rezahh107/EV4-Shared-Contracts/pull/3` |
| CI status | `CI_PENDING` until the latest matching `Skeleton Health` run completes |
| Files changed | `docs/GOVERNANCE.md`, `README.md`, `docs/EV4_SHARED_CONTRACTS_STATUS.md` |
| Remaining blockers | canonical migration blocked; full cross-repo CI incomplete; `ev4-builder-context-package@1.0.0` split risk unresolved |
| Next action | Verify `Skeleton Health` for PR #3, then review/merge only if checks pass and no blocker appears |
| Simple Persian mental model | دفتر ساخته شده؛ آیین‌نامه داخلی در PR باز است، ولی آرشیو رسمی schemaها هنوز قفل است. |

## 8. Next Immediate Step

Verify PR #3:

```text
phase4/status-and-minimal-governance → main
```

Then:

```text
Wait for GitHub Actions / Skeleton Health result.
If CI passes, review and merge the Phase 4 governance PR.
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
