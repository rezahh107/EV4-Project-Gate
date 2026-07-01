# EV4 Shared Contracts Status

## 1. Current Status Summary

```text
EV4-Shared-Contracts currently exists as a non-authoritative skeleton.
Canonical schema migration remains blocked.
The skeleton branch is initialized and locally verified.
GitHub Actions / CI evidence must be checked for the latest commit before claiming CI-verified status.
```

- Repository: `rezahh107/EV4-Shared-Contracts`
- Current branch: `init/non-authoritative-skeleton`
- Current baseline commit: `f1595091474eacd9d58e8a3f92e364f980c08e58`
- Previous status-dashboard commit: `0233e677adfef0a27d32c16d004382a765eb5aca`
- Latest repository-memory hardening commits:
  - `5d23abc731c76ac662fa35b6d101a9955d1c9335` — hardened `AGENTS.md` with repository memory rule
  - `82648f244f1593b7b9572eae0be773701e0c99bf` — clarified repository memory files in `README.md`
  - `pending final report` — this status update commit
- Status: `skeleton verified with limitations`
- Canonical migration: `blocked`
- CI status: `CI_NOT_VERIFIED for latest status update until Skeleton Health evidence is available`

## 2. Mental Model

چهار repo اصلی EV4 مثل چهار کارگاه جدا هستند.

`EV4-Shared-Contracts` مثل دفتر مرکزی تازه‌ساخته است. فعلاً این دفتر فقط نقشه‌ها، چک‌لیست‌ها، inventory و قوانین promotion را نگه می‌دارد.

`AGENTS.md` تابلوی ورودی ساختمان است. `README.md` بروشور معرفی ساختمان است. `docs/EV4_SHARED_CONTRACTS_STATUS.md` تابلوی وضعیت اتاق کنترل است.

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
- [x] Skeleton local checks passed.
- [x] No canonical schemas were migrated.
- [x] Existing EV4 repos were not modified during skeleton initialization.
- [x] Project status dashboard was added.
- [x] Repository-level agent guidance was added in `AGENTS.md`.
- [x] Repository memory rule was added to `AGENTS.md`.
- [x] README now explains the three memory files: `AGENTS.md`, `README.md`, and `docs/EV4_SHARED_CONTRACTS_STATUS.md`.

## 4. Known Limitations / Risks

- [!] Full CI evidence across all four EV4 repos is incomplete.  
  The ecosystem-wide validation set is still incomplete, so promotion cannot rely on full cross-repo CI evidence yet.

- [!] EV4-Shared-Contracts skeleton CI must be checked after each new commit.  
  Do not report the latest branch state as CI-verified until the matching `Skeleton Health` run is visible and successful.

- [!] ev4-builder-context-package@1.0.0 still has historical split risk.  
  This contract/version name has carried different producer and consumer assumptions historically.

- [!] Canonical schema migration is not allowed yet.  
  Shared schemas must wait for checklist approval, CI evidence, migration plan, rollback guidance, and promotion ADR.

- [!] Builder/CE adapter boundary still exists.  
  CE-to-Builder normalization remains a boundary that must be preserved until a safe shared contract is promoted.

## 5. Phase Checklist

| Phase | Goal | Status | Mental Image | Next Action |
|---|---|---|---|---|
| Phase 0 — Cross-repo role alignment | align Architect, CE, Builder, Responsive roles | mostly done, CI incomplete | road signs between workshops were corrected | no conceptual hardening unless CI reveals issues |
| Phase 1 — Shared repo skeleton | create non-authoritative coordination repo | initialized and locally verified | central office building created, but not legal archive yet | open PR and get CI evidence |
| Phase 2 — Skeleton PR and merge | review and merge skeleton into main | pending | office documents are waiting for approval stamp | PR from init/non-authoritative-skeleton to main |
| Phase 3 — Status-driven continuation | continue from repo memory files in a new chat | repo memory files are now explicit | project map pinned to the wall beside the entrance sign | use `AGENTS.md`, `README.md`, and this file as first context in the new chat |
| Phase 4 — Minimal shared governance | add only low-risk shared policies and vocabulary | future | office creates naming rules before accepting legal documents | propose minimal governance, not schema migration |
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

Do not:

- do not migrate schemas yet
- do not make this repo source of truth yet
- do not touch the four existing EV4 repos from this branch
- do not promote `ev4-builder-context-package@1.0.0` first
- do not claim CI passed without workflow evidence

## 7. Latest Completed Task Record

| Field | Value |
|---|---|
| Phase/task completed | Repository memory hardening for agent continuation |
| Commit SHA | `5d23abc731c76ac662fa35b6d101a9955d1c9335`, `82648f244f1593b7b9572eae0be773701e0c99bf`, `pending final report` |
| PR number or PR URL | `none yet` |
| CI status | `CI_NOT_VERIFIED` until latest `Skeleton Health` evidence exists |
| Files changed | `AGENTS.md`, `README.md`, `docs/EV4_SHARED_CONTRACTS_STATUS.md` |
| Next action | Open PR from `init/non-authoritative-skeleton` to `main`, then check `Skeleton Health` |
| Simple Persian mental model | repo خودش حافظه پروژه است: ورودی، بروشور، و تابلوی اتاق کنترل کنار هم قرار گرفته‌اند. |

## 8. Next Immediate Step

Open PR:

```text
init/non-authoritative-skeleton → main
```

Then:

```text
Wait for GitHub Actions / Skeleton Health result.
If CI passes, merge skeleton.
If CI does not trigger, report CI_NOT_TRIGGERED.
If CI fails, fix only skeleton-health issues.
```

## 9. New Chat Handoff Prompt

```text
You are helping me continue the EV4-Shared-Contracts workflow.

Read AGENTS.md first.
Then read README.md.
Then read docs/EV4_SHARED_CONTRACTS_STATUS.md as the current source of project status.

Do not perform canonical schema migration unless the status file says all promotion blockers are resolved.

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
- commit SHA
- PR number or PR URL, or none yet
- CI status
- files changed
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
