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
| `#55` | `feat: complete producer-emitted CE to Builder handoff` | `feature/project-gate-ce-export-dispatch` | `6ea6dd6940260e663f0c5e86a95bf914ee2c7f58` | `47ac93c14d801f2c12c473004a3913ce9a0b373b` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#54` | `feat: complete Architect-to-CE producer export dispatch` | `feature/project-gate-architect-export-dispatch` | `b6290c7862d83ff7c1b4ea20031dc6842b2c2ddf` | `2f31c2049980cf5f7cbf7a2a5df8a5fc56828303` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#53` | `docs(status): reconcile capability truth with verified closure evidence` | `agent/docs-status-kroad-011-20260715` | `2174643a54ddcdebb1d6513cf4bb392a0be6e4b8` | `8cf32c65a3934ef79295d59de85daca124607ee9` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#52` | `Post-merge KROAD-011 evidence and governance correction` | `fix/kroad-011-evidence-and-governance-correction` | `9b3c48634f8921446979c1b93c1bc4f3eae8ed13` | `c030460aa90b0b234c2e421554d4f8eb45061210` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#51` | `Implement KROAD-011 Project Gate Kernel decision intake` | `feature/kroad-011-project-gate-intake` | `765fd4b1f086141e6453bd57ed4674d2025caf73` | `01fdc126f834e0c0d8fbb297a2d44488487e5379` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#50` | `Add UX-safe Kernel decision receipts for Project Gate outputs` | `ux/project-gate-kernel-decision-receipts-wave-5` | `cc1083ad78d5c548ec39488d114d243952002303` | `1b813da05837b43ea71047662b43bb64c89fd857` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#49` | `Add Project Gate decision lineage enforcement (Wave 4)` | `codex/add-project-gate-decision-lineage-enforcement` | `46d83e062b45722d8defff5e479648bd4a6d5043` | `70a6abc3aa88d2384095597c69a88212b6c0b825` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#48` | `Adopt EV4 consumer decision trigger architecture baseline (Wave 0)` | `codex/implement-wave-0-architecture-baseline` | `e95a0744a1393f6cf1530c4758eb2435dfb6c7e4` | `908055328a7dac611c0096951ff77e01be6e5636` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#47` | `docs: adopt EV4 consumer decision trigger architecture v0.4.1` | `adopt-ev4-consumer-decision-trigger-architecture-v0-4-1` | `ecdf2d33de15a301e3c442837d8b1ba71fdfec4e` | `c94f2fef6d2652573888694d13c2e40ac04e83b8` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#46` | `Polish operator panel radio indicators and dark header` | `project-gate-prompt-07-ui-polish` | `8d85d10167a80a26c53cf01e428312282bb1bad0` | `cad4c5d571cc75059d327b36e67946bfb15ca96f` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#45` | `Fix operator panel theme readability and contrast system` | `project-gate-prompt-06-theme-readability` | `757a1ca9eecb64ce2eaef27aee743b6003be75e6` | `f4d17765adfdad6bf8383f1f431d0ebc91e9dc4b` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#44` | `Docs and tests: mark CE→Builder/Builder→Responsive/Final Gate CLI as guarded and update orchestration status` | `codex-aj4m3l` | `c4a30f9f10c888c70da8dd8549d3860c4f2e6bde` | `6ce830d7e8d566fd57d955a75326173993291fd4` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#43` | `Add explicit producer_emitted_gate_artifact intake, adoption registry, and routing (Prompt 5)` | `codex/implement-prompt-5-integration` | `0db90978d25e3392d42b9a0f6d2eeb954553e095` | `4e33085a97715a882a906c727f034c6d15d9e5fa` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#42` | `Repair Prompt 4.5 join evidence packet` | `codex/repair-prompt-4.5-join-evidence-packet` | `22e0915561dafb6f7857edf76b5fb31027614924` | `c92af08573463d7732d795f67e8376e5796f2975` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#41` | `Add Prompt 4.5 join evidence packet` | `project-gate-prompt-04-5-join-evidence-packet` | `befdc25e9e2c4607a7d9dc12923c451834118bbc` | `bb02dd6c0e4ff5d00324568c9cd432332d5d86b0` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#40` | `feat: Prompt 0 — Add Producer Gate Export validator and harden vendored common-contract verifier` | `codex/complete-pr-#39-for-prompt-0-requirements` | `ff75e319ee382e7c024d088e8794b4b5ece845cc` | `ea19c22c32458068e167b267da8b819e9263cdf7` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#38` | `Harden operator panel UX contracts and regression tests` | `ux/operator-panel-final-hardening-patch-4` | `c5ddda6cc43d27a46d056876aa7ea0c2afe73eba` | `e44edeb4d4c0ea49ec2632856c5b140d2a2aefe1` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#37` | `Add local repository preflight assistant` | `ux/local-repo-preflight-setup-assistant-patch-3` | `558bc4be24310c603b4589779cc51964a071089b` | `a18ed34dc818b6927dbd98d0ba13297c5345a65f` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#36` | `Add operator guidance and diagnostic help layer` | `ux/operator-guidance-diagnostic-help-patch-2` | `1126e728d24a71bf5c3f5372bbbf1ff59f1aa193` | `4cf75a13ea7bb436c137b9b3b4b7b8ad480770a6` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#35` | `Polish operator panel RTL layout and visual theme` | `ux/operator-panel-rtl-visual-polish-patch-1` | `ec1775c16447ea65457b3dffd86c82c124712f9a` | `3e4a92ecf57f6045147e4b819e7f26d4915ff78f` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#34` | `Add double-click Windows launcher for the local UI` | `chore/windows-double-click-launcher` | `3a6720840002332a42087642d889ed6441d259f7` | `961d9665665849e23e519ec60d34931c852c1a6c` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#33` | `Make uv the default local and CI installer` | `codex/make-uv-the-default-installer` | `ae970cafc0454d322bab28e7fe687635f1da7dbd` | `23dcf5342706efb0c689f6503429cf20b7f6f703` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#32` | `Operator UI: route through internal service, add theme CSS/TYPEKIT, tests and docs for Prompt 06` | `codex/complete-ui/ux-and-service-integration-gaps-978dcl` | `c904cbac4227275474fab99a6264ecaa6447d31c` | `cf6bb8846ae705aa7f18476d569f566631803c94` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#30` | `Expose guarded fail-closed CLI entries for CE→Builder, Builder→-Responsive, and Final Evidence Gate` | `codex/implement-public-cli-support-for-transitions` | `ba5310ee3b00b6b64a737aa9264ab7208657b498` | `d921975b3e22062c33c81bd1b9265df7af3b6121` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#27` | `Add personal-use setup and controlled demo package` | `personal-use/e2e-package` | `fbe0bfbdeeec90ad73b6aae165df8caf34e43d7c` | `88c7e1a491b08cd0bb21d211ec14c3c92d2ea92b` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#28` | `Add local Project Gate operator UI` | `ui/operator-panel` | `daafd4b870ced063dbeb6d8e5da756c32787ee8e` | `50ac6a812ecc95704a553a2769e153cb3991cb3c` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#29` | `Add Project Gate service API for UI integration` | `feature/gate-service-api` | `534873d1bf17bb95a12ff8701e9343710d098d20` | `89cf4f52abc7273989dccb51016e26c92d836fc1` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#26` | `PROMPT-07 Closure audit and stale prose cleanup` | `project-gate-prompt-07-closure-audit` | `cb8343bd273de616aa91e6c37daa628f5aefa68a` | `c69da17db3fb60e8b733905b81cde71645777805` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#25` | `Add capability-truth, exact-head, and workflow-permission CI gates` | `fix/ci-governance-evidence-gates` | `cda3121313bdb476bffe006f2c259755d742eb93` | `572bb6d78bdb8d56d10f48d27e37cd278731e876` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#24` | `PROMPT-06 Report UX, Persian RTL/LTR, and atomic writing hardening` | `project-gate-prompt-06-ux` | `c8522cf36e65243dfebc3f9b2f0b3feb97cbedf4` | `d522e7d4b434cc337bfe9314116f5b4af61466cf` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#23` | `Repair Prompt-05 foundation, immutable locks, and CI gates` | `fix/prompt-05-foundation-reconciliation` | `b8ac70e6acd2c2c6201b7a1e924751dcdc6f07c9` | `fed7a77f1e0c7be617e87ba757f35dae673c6e2e` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
| `#21` | `Fix post-merge capability truth and workflow pinning coverage` | `fix/capability-truth-post-merge-hardening` | `ce356b6f6a8dee5f807679aed0f78aa057152d1b` | `5aaf2b93f0d18c8ac557f0d0e3d958693a1ec2f4` | `CI_PASSED` | `rezahh107 on rezahh107/EV4-Project-Gate` |
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
