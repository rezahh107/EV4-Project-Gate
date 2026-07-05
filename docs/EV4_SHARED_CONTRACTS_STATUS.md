# Historical EV4 Shared-Contracts Merge Ledger

This file preserves pre-Project-Gate governance and merge history. It is not the current implementation or capability authority.

Current capability truth is defined by:

```text
src/ev4_transition/data/capability-status.v1.json
docs/IMPLEMENTATION_STATUS.yaml
```

## Latest Recorded Merge

- Repository: `rezahh107/EV4-Project-Gate`
- Main branch: `main`
- Last merged PR: `#20` — `PROMPT-04 CE to Builder transition orchestration baseline`
- PR #20 merge commit: `34b08240ad4deaf017a8f79236d0b8e214530dec`
- PR #20 head commit: `42bfa484481c585f589d86c40424660c70b038a0`
- PR #20 `Skeleton Health`: `CI_PASSED`
- Ledger role: `historical merge facts only`

The exact automatic post-merge `main` head audited after this merge was `dca39ed177d5660d96df04a05fff0a0314c6c339`. No workflow run was visible for that exact head, so this ledger does not claim its CI passed.

## Historical Phase Context

| Phase | Historical status |
|---|---|
| Phase 4 — Minimal shared governance | completed |
| Phase 4.1 — Promotion proposal intake | completed |
| Phase 4.2 — Audit correction | completed |
| Phase 5 — First proposal-only candidate | completed as `PROPOSAL_ONLY` |
| Phase 5.1 — Status-after-merge automation | completed and reframed as historical ledger automation |
| Phase 6 — Shared schema migration | blocked |

## Historical Shared-Contracts Notes

- `reference_paradigm_lock` was recorded as a proposal-only readiness candidate.
- The previous shared-contracts skeleton did not promote active schemas or become a runtime dependency.
- Canonical migration remained blocked.
- These notes do not override current Project Gate code, tests, capability truth, or implementation status.

## Historical Evidence

| Item | Value |
|---|---|
| PR #5 merge commit | `ba766ffc2894f6dd2cd98cbcb10b08c446d0149a` |
| PR #5 `Skeleton Health` | `CI_PASSED` |
| PR #6 merge commit | `27a4fab5ea33cd72ade1c626f674ae3166ae3a09` |
| PR #6 `Skeleton Health` | `CI_PASSED` |
| PR #7 title | `Automate status file merge ledger updates` |
| PR #7 head commit | `96548866ec544009645d4b501fba7eb617d666ad` |
| PR #7 merge commit | `4b48422bf7f95cc4682c0c4a871d441cef1a17a4` |
| Canonical migration | `blocked` |

## Automated Merge Ledger

This section is updated by GitHub Actions after a pull request is merged. It records historical merge facts only and is not the current capability-truth source. A `CI_PASSED` cell refers to the recorded PR head workflow, not automatically to the later bot-generated `main` commit.

| PR | Title | Head branch | Head commit | Merge commit | Skeleton Health | Recorded by |
|---|---|---|---|---|---|---|
| `#20` | `PROMPT-04 CE to Builder transition orchestration baseline` | `project-gate-prompt-04-ce-to-builder` | `42bfa484481c585f589d86c40424660c70b038a0` | `34b08240ad4deaf017a8f79236d0b8e214530dec` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#19` | `PROMPT-03 Runner boundary and official tool execution infrastructure` | `project-gate-prompt-03-runner-boundary` | `16268e56a9f80224c68621cdff2f87dbf50d5267` | `34fb7acd82b6ff94ed3c64a53ae3fb0582c2714a` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#18` | `PROMPT-02 Behavioral Rule Coverage enforcement` | `project-gate-prompt-02-behavioral-coverage` | `0a355b24fabd3f74ea73c1e66d85df359286fe03` | `cf0d1f40047bcd2479cec7359f99c969088267f8` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#17` | `PROMPT-01 Project Gate contracts and deterministic core hardening` | `project-gate-prompt-01-deterministic-core` | `4153c9df348e66626ed81d63ad1888ef41430fb6` | `4897d7c2e0d693a1df29447f4a010acf3a65feac` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#16` | `PROMPT-00 audit/freeze baseline` | `project-gate-prompt-00-audit-freeze-baseline` | `9fa656078ee1b8bf293a163be58f058f2f03ee64` | `e1d855740445f5cfcf23b6c2aac1fb44286369c2` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#15` | `Close Builder→Responsive readiness baseline` | `fix/builder-responsive-closure-pg` | `9c1c51b09dab13de076dbab256bf5a1f9fe96b0e` | `77bb41857be0d9862a609e66a2e707f274849e2f` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#14` | `Close CE→Builder readiness baseline` | `fix/ce-builder-closure-project-gate` | `443f8b1f0b2790bb82b3b512da6c5178bf5de424` | `0b076ab5b370f3de9098cd2a96a2c2302097fa8b` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#13` | `Add Architect-to-CE transition v1` | `architect-to-ce-transition-v1` | `6f824de7febd533f3b0f8d37a789798e15f7c3df` | `75d546e9e593aa578ef5a006b7f2b622249bdd5c` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#12` | `Add Python deterministic Stage Evidence core` | `python-deterministic-core-v1` | `a1b33339ed5d90c665899174da24ea2a32ee234f` | `d6ed11043229a8b83a6025e6cc22c267275c497b` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#10` | `Document the EV4 Project Gate workflow` | `docs/project-gate-workflow` | `127f04e7e996eeb7bfc162ed9994a46a58a02491` | `9f24400b4e96b30d728d704e5221d5899facddd7` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#9` | `Redefine repository as compatibility gate` | `docs/compatibility-gate-role` | `f9c4a9df205f9044ecd4b5708b9ae2f4e0dd24d1` | `bea674e033935da5a60a94dc4b78cb634c0491f1` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Shared-Contracts` |
| `#8` | `Fully automate post-merge status finalization` | `automation/finalize-status-after-merge` | `4f9ee4b1e25bb182f50e1431d0c5260df33a146d` | `e70650453879ac72b04cc38bfeafd5bfa813cdf8` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Shared-Contracts` |
| `#7` | `Automate status file merge ledger updates` | `automation/status-after-merge` | `96548866ec544009645d4b501fba7eb617d666ad` | `4b48422bf7f95cc4682c0c4a871d441cef1a17a4` | `CI_NOT_VERIFIED` | `rezahh107 on rezahh107/EV4-Shared-Contracts` |

## Current Startup Map

Read current state in this order:

1. `src/ev4_transition/data/capability-status.v1.json`
2. `docs/IMPLEMENTATION_STATUS.yaml`
3. `README.md`
4. `AGENTS.md`
5. `docs/ROLE_BOUNDARY_MAP.md`
6. `docs/VALIDATION_STRATEGY.md`
7. `docs/COMPATIBILITY_MAP.md`
8. this historical ledger only when merge history is needed
