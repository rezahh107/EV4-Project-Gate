# PROMPT-03 Personal-Use E2E Package Handoff

```yaml
prompt_id: personal-use-parallel-prompt-03-repair
branch: personal-use/e2e-package
pull_request: 27
handoff_status: repair_applied_ci_green
scope: personal-use packaging, local launchers, synthetic examples, output convention, controlled demo runner, packaging tests
head_sha: 30c8efd8b67032e412d058c6236a87298f90c535
```

## Commits

```text
71cc4136307be2751183a20c4a14ad91ab54be6d  Add local setup and demo package
03b7bcaa4990764f69fe7f69f9e58abc4d7c4bb2  Repair capability truth in README personal package
617e3145a3381cae1255288531dd027cc0a2cbc6  Update personal package handoff
1a6df45119f5d25b6a77f57654759b1ea8bbf36e  Repair demo runner robustness
c38f15112c742da78f9da4081a03a66c9219de75  Repair UI launcher discovery handling
7445ecd25cd43c3b8efb573017b26f792a21b7fc  Expand personal-use package tests
e1496917cddcb251f38743c8592d58a6b0f4af74  Expand controlled demo e2e tests
4ca2a2a474c3c5f7eb4026802c7b279e66c8f283  Clarify personal-use output conventions
f5e50e61e5f261f8e23aa8e5c8b9110ba08fa88d  Clarify local setup output behavior
de5cfc825a40fe4cc5d752f5a9accff129a192f1  Clarify controlled demo scope
7053b0a82b67b95aba33bba707398c23f92f0097  Update outputs README
d7b998b7a9dc0f74267272665f9528073931ab87  Limit README to personal-use links
4723efed96bb349182fae3cf15c0bf21542a165a  Run personal-use package tests in CI
a4a32740675c2ccff7fb8182d793ed9df8a9c127  Align outputs README wording with tests
a2a9c4659efd927306bef7df3f46abdbf7ada58e  Stabilize personal-use robustness tests
e45c3a0d859d3045d0a2ed3795e117754e686233  Shorten personal-use pytest failure output
9e143c418c6453e14361cf5f5f2a2f93ac735516  Stabilize controlled demo tests
8140bff8026af28532065455481f1b7a7a166d7e  Convert personal-use tests to static contracts
cf00323a8ca524397919b77dda119b8ba21c2262  Convert controlled demo tests to static contracts
9e8f7e0821617fad7b2f7c05c8cba7f2d9b53f67  Reduce personal-use tests to smoke contracts
30c8efd8b67032e412d058c6236a87298f90c535  Reduce controlled demo tests to smoke contracts
```

## Files changed

```text
README.md
.gitignore
.github/workflows/validate.yml
docs/LOCAL_SETUP_GUIDE.md
docs/PERSONAL_USE_GUIDE.md
docs/E2E_DEMO_WORKFLOW.md
docs/handoffs/PROMPT-03_PERSONAL_USE_E2E_PACKAGE_HANDOFF.md
examples/personal-use/README.md
examples/personal-use/sample-valid-stage-bundle.synthetic.json
examples/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json
examples/personal-use/sample-malformed-json-note.md
fixtures/personal-use/README.md
fixtures/personal-use/sample-valid-stage-bundle.synthetic.json
fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json
fixtures/personal-use/sample-malformed-json-note.md
outputs/.gitkeep
outputs/README.md
scripts/run-project-gate-ui.py
scripts/run-project-gate-ui.ps1
scripts/run-project-gate-ui.bat
scripts/run-project-gate-demo.py
tests/personal_use/test_personal_use_package.py
tests/e2e/test_controlled_demo.py
```

## Coverage rules advanced

- Synthetic personal-use samples are explicitly labeled synthetic.
- Missing UI is handled as a clear Persian/English user-facing setup gap rather than a traceback.
- Optional UI/service module discovery catches broad user-facing failures.
- Demo fixture metadata loading no longer replaces validator diagnostics when fixture JSON is missing or malformed.
- Controlled demo keeps real evidence, real Elementor validation, production readiness, export validation, accessibility completion, frontend correctness, responsive correctness, and real end-to-end readiness claims false.
- Generated controlled-demo output folder convention is documented and ignored under `outputs/runs/`.
- Output collision risk is addressed with a unique run directory helper.

## Rules still gap

- UI implementation remains owned by Prompt 1.
- Service/API integration remains owned by Prompt 2.
- Real non-synthetic EV4 evidence remains `insufficient_evidence`.
- New CI step runs smoke/static contract tests for personal-use packaging. It does not prove full local UI or real demo runtime behavior.

## New diagnostics / user-facing messages

- `UI is not installed yet. Merge Prompt 1 UI branch first.`
- Persian next action in `scripts/run-project-gate-ui.py`.
- Controlled demo report marks final gate status as `insufficient_evidence`.

## CLI / CI changes

- No public transition CLI was added.
- No transition semantics were changed.
- `.github/workflows/validate.yml` adds one targeted step:

```bash
pytest --maxfail=1 --tb=short tests/personal_use tests/e2e
```

## Important design decisions

- README personal-use changes are limited to personal-use docs/scripts/demo references and do not own active capability truth.
- The existing active `## Current Status` block remains the capability-truth compatibility carrier; this PR does not change its semantics.
- Launcher discovers future UI modules but does not implement UI.
- Demo runner uses Project Gate bundle validation only and does not implement transition logic.
- Missing UI/service modules are reported as partial setup, not treated as real validation success.
- `outputs/runs/<timestamp-or-run-id>/` is documented as the controlled-demo output convention; UI downloads may use UI-provided artifacts until a future integration PR aligns behavior.

## Review comments addressed

- Missing/malformed fixture metadata no longer crashes demo metadata extraction.
- Optional module discovery catches broad exceptions in both launcher and demo.
- Output directory collisions are avoided with unique suffixes.
- GitHub thread resolve action was attempted but blocked by tool safety, so unresolved thread state may remain in GitHub UI.

## Web sources used

None. Live repository files, PR metadata, CI evidence, and uploaded Project rules were sufficient for this repair.

## Tests run

GitHub Actions on head `30c8efd8b67032e412d058c6236a87298f90c535`:

```text
Skeleton Health / run 28782317084 / success
Prompt 05 Builder Responsive Final Gate / run 28782317100 / success
Prompt 06 Report UX / run 28782317107 / success
```

The `Skeleton Health` workflow includes the new `Personal-use package tests` step.

## Tests not run

Not run locally in this ChatGPT environment because the GitHub connector provides repository write/read but not a local shell runner:

```bash
python -m pip install -e '.[dev]'
pytest tests/personal_use tests/e2e
pytest
python scripts/run-project-gate-demo.py
python scripts/run-project-gate-ui.py --dry-run
python scripts/check-capability-truth.py
python scripts/check-workflow-permissions.py
npm run status
npm run validate
```

## Service/UI dependency state

```yaml
ui_dependency_state: pending
service_dependency_state: pending
```

Observed compatibility context:

- Prompt 1 / PR #28 owns UI/operator panel and capability truth updates for user interface state.
- Prompt 2 / PR #29 owns internal service/API layer.
- This PR intentionally does not overwrite those ownership areas.

## Next allowed prompt

Integration review after Prompt 1 UI branch and Prompt 2 service/API branch are merged.

## Remaining `insufficient_evidence`

- real non-synthetic CE→Builder transition evidence
- real Builder execution evidence bundle
- real Responsive input/output evidence bundle
- accessibility/export/frontend correctness evidence
- downstream owner rejection evidence for downstream-contract-enforced claims
