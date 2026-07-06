# UV Default Installer Handoff

## Branch

`codex/make-uv-the-default-installer`

## PR

`https://github.com/rezahh107/EV4-Project-Gate/pull/33`

## Commits

- `67033295dc91c26be27b50efc250ec687ced0375` — `Fix Prompt 05 owner validator Python environment`
- `688768d66bcac58612c3d23e56c81587c20b8d18` — `Fix Skeleton Health owner validator Python environment`
- `2af91baa5ac7c9db4a914b5eefeef93af0f821d4` — `Update uv owner-validator regression coverage`
- `9d622a33ff1013bc411d5fc2d8c222100a34d3d4` — `Update uv default installer handoff after CI repair`
- `12d73ff1c734e7fa17687093595bf50b6dbcda66` — `Restore behavioral coverage CI step evidence names`
- Current handoff update commit: see final repair report / branch history.

## Required change versus optional recommendation

Required: make `uv` the default local and CI Python installer/environment workflow while preserving a secondary `pip` fallback.

Optional: keep `setuptools` and `[project.optional-dependencies]`; no dependency-group migration was needed.

## Repositories and boundaries affected

- Primary repository: `rezahh107/EV4-Project-Gate`.
- Specialist repositories were not modified.
- Specialist schemas, validators, adapters, fixtures, and transition semantics were not changed.
- Official owner validators still run from owner repository working directories.
- CI now invokes those owner scripts with Project Gate's uv-managed interpreter at `${{ github.workspace }}/EV4-Project-Gate/.venv/bin/python` so dependencies such as `jsonschema` are present.

## Files changed in CI repair follow-up

- `.github/workflows/prompt-05.yml`
- `.github/workflows/validate.yml`
- `tests/personal_use/test_personal_use_package.py`
- `docs/handoffs/UV_DEFAULT_INSTALLER_HANDOFF.md`

## CI and CLI changes

- `Prompt 05 / Run pinned official Responsive validators` now uses `PROJECT_GATE_PYTHON` while preserving `working-directory: EV4-Responsive-Architect`.
- `Skeleton Health / Official Architect validator fixture suite` now uses `PROJECT_GATE_PYTHON` while preserving `working-directory: EV4-Architect-Repo`.
- `Skeleton Health / Official CE validator fixture suite` now uses `PROJECT_GATE_PYTHON` while preserving `working-directory: EV4-Constructability-Engineer-Repo`.
- `validate.yml` keeps behavioral coverage evidence carriers as real named steps, including `Static runner-boundary scanner`, `Runner tests`, `Behavioral coverage validator`, `Behavioral fixture validation`, `Prompt-05 transition tests`, and `CE-to-Builder lock verification`.

## Regression coverage advanced

`tests/personal_use/test_personal_use_package.py` now checks that owner-validator steps:

- keep the owner repo `working-directory`;
- define `PROJECT_GATE_PYTHON` as the Project Gate `.venv/bin/python` path;
- invoke official owner scripts through `"$PROJECT_GATE_PYTHON"` instead of bare system `python`.

## Root cause fixed

The reviewed head `02a832846fe3d56810f37961727dc6cab69a22fc` failed because official owner validators were launched with bare system `python`, and that interpreter did not have `jsonschema`. The repair uses the uv-managed Project Gate Python environment after `uv sync --locked --extra dev --extra ui`.

## Tests run before this repair

Earlier author-reported validation in the PR included:

- `uv lock --check`
- `uv sync --locked --extra dev --extra ui`
- `uv run --locked pytest tests/personal_use tests/reporting/test_workflow_permissions.py tests/test_cli.py`
- `uv run --locked pytest`
- `npm run status`
- `npm run validate`

## Tests / CI inspected during this repair

- Live GitHub Actions logs for the failing `Prompt 05` and `Skeleton Health` jobs were inspected.
- On intermediate head `9d622a33ff1013bc411d5fc2d8c222100a34d3d4`, `Prompt 05 Builder Responsive Final Gate` reached success.
- On the same intermediate head, `Prompt 06 Report UX` failed at `Behavioral coverage validator`; commit `12d73ff1c734e7fa17687093595bf50b6dbcda66` restored the real CI step names used as behavioral evidence.

## Tests not run / still pending

- No local test suite was run in this connector session.
- Native Windows execution of `scripts/setup-windows-uv.ps1` was not run.
- Final GitHub Actions status on the latest head is pending and must be inspected before merge.

## Coverage rules advanced

No behavioral rule was promoted to a stronger status. The repair preserves existing CI evidence carriers and avoids treating owner-validator execution as specialist logic copied into Project Gate.

## Remaining gaps

- Final CI success is not yet evidenced.
- Full `uv.lock` dependency audit remains outside this repair.
- Native Windows setup behavior remains unverified.

## Next safe action

Wait for GitHub Actions on the latest PR head and merge only if `Prompt 05 Builder Responsive Final Gate`, `Skeleton Health`, `Prompt 06 Report UX`, and `UI Runtime Smoke` all pass.
