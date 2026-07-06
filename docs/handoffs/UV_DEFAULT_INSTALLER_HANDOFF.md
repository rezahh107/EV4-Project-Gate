# UV Default Installer Handoff

## Branch

`project-gate-uv-default-installer`

## PR URL

Pending: not created yet at validation time.

## Commits

Pending: final commit will be recorded after this file is updated.

## Required change versus optional recommendation

Required: make `uv` the default local and CI Python installer/environment workflow while preserving a secondary `pip` fallback.

Optional recommendation: continue using `setuptools` and `[project.optional-dependencies]`; no migration to `[dependency-groups]` was needed.

## Repositories and contract boundaries affected

- Primary repository: `rezahh107/EV4-Project-Gate`.
- Specialist repository schemas, validators, adapters, and transition semantics were not changed.

## Official uv docs consulted

- Installation: `https://docs.astral.sh/uv/getting-started/installation/`
- Locking and syncing: `https://docs.astral.sh/uv/concepts/projects/sync/`
- Managing dependencies and extras: `https://docs.astral.sh/uv/concepts/projects/dependencies/`
- GitHub Actions: `https://docs.astral.sh/uv/guides/integration/github/`
- Python versions and `.python-version`: `https://docs.astral.sh/uv/concepts/python-versions/`

## uv version strategy

Local validation used `uv 0.7.22`. GitHub Actions install `astral-sh/setup-uv` pinned by full commit SHA and request `version: "0.7.22"` for lockfile consistency with the generated `uv.lock`.

## Python version policy

`pyproject.toml` remains `requires-python = ">=3.11"`. `.python-version` was added with `3.11` to select the default local interpreter for reproducible uv setup without raising the supported baseline.

## Dependency metadata decision

Kept `[project.optional-dependencies]` for `dev` and `ui`. They are documented as extras and synced with `uv sync --extra dev --extra ui`. They were not migrated to dependency groups because the existing metadata is valid project metadata and no dependency-group-only need was identified.

## Lockfile status

`uv.lock` was generated with `uv lock` and should be committed.

## CI changes

Python-installing workflows now install uv via a full-SHA-pinned `astral-sh/setup-uv`, run `uv lock --check`, sync with `uv sync --locked --extra dev --extra ui`, and execute Python tests/checks through `uv run` where changed.

## Docs updated

- `README.md`
- `docs/LOCAL_SETUP_GUIDE.md`
- `docs/PERSONAL_USE_GUIDE.md`
- `docs/E2E_DEMO_WORKFLOW.md`
- `docs/UI_OPERATOR_PANEL.md`
- `docs/VALIDATION_STRATEGY.md`
- `outputs/README.md`
- `examples/personal-use/README.md`
- `fixtures/personal-use/README.md`

## Scripts added

- `scripts/setup-windows-uv.ps1`: safe Windows setup helper that refuses to auto-install uv and prints official install options if uv is missing.

## Tests run

- `uv --version`
- `uv lock --check`
- `uv sync --locked --extra dev --extra ui`
- `uv run --locked pytest tests/personal_use tests/reporting/test_workflow_permissions.py tests/test_cli.py`
- `uv run --locked python scripts/check-github-action-pinning.py`
- `uv run --locked python scripts/check-workflow-permissions.py`
- `uv run --locked python scripts/check-capability-truth.py`
- `uv run --locked ev4-transition inspect`
- `uv run --locked python scripts/run-project-gate-demo.py --run-id uv-default-installer-smoke`
- `uv run --locked pytest`
- `npm run status`
- `npm run validate`

## Tests not run

- Native Windows execution of `scripts/setup-windows-uv.ps1` was not run in this Linux container.
- GitHub Actions CI was not inspected after local commit because no remote workflow run evidence was available in this session.

## Remaining gaps

- CI run status is unknown until GitHub Actions execute on the committed branch/PR.
- Native Windows script behavior needs a Windows runner/user validation pass.

## pip fallback status

Preserved only under sections titled `Fallback if uv is unavailable` or equivalent user-facing fallback guidance.

## Rollback guidance

Revert this branch commit to restore the previous `pip`-primary documentation and CI install path. Do not change transition locks or specialist contracts during rollback.

## Next safe action

Run `uv lock --check`, `uv sync --locked --extra dev --extra ui`, and the repository validation commands, then open a draft PR.

## Review follow-up fixes

A follow-up review found that required CI jobs still had uv ordering and bare command gaps. This branch now fixes those gaps by:

- installing and syncing uv before uv commands in the `validate.yml` `skeleton` job;
- replacing the CE→Builder bare `pytest` gate with `uv run pytest` while preserving tee/log capture;
- running Project Gate lock recompute, lock verification, smoke, behavioral coverage, CLI smoke, and Prompt 05 Python gates through `uv run`;
- adding workflow-structure tests that fail if a job runs uv before `setup-uv` or if uv workflows contain bare `python`, `pytest`, or `ev4-transition` commands.

Additional validation after the follow-up fix:

- `uv lock --check`
- `uv sync --locked --extra dev --extra ui`
- `uv run --locked pytest tests/personal_use tests/reporting/test_workflow_permissions.py tests/test_cli.py`
- `uv run --locked python scripts/check-github-action-pinning.py`
- `uv run --locked python scripts/check-workflow-permissions.py`
- `uv run --locked python scripts/check-capability-truth.py`
- `uv run --locked pytest`
- `npm run status`
- `npm run validate`
- `uv run --locked ev4-transition inspect`
- `uv run --locked python scripts/run-project-gate-demo.py --run-id uv-ci-fix-smoke`

Remote GitHub Actions still need to run on the updated head before CI can be reported as successful.

## External validator and Node validation boundary follow-up

A later CI review found two remaining environment-boundary failures. This branch now makes those boundaries explicit:

- Project Gate policy checks invoked by `scripts/validate.js` use `uv run --locked python` instead of system `python`/`python3`.
- Official owner-repository validators run from their owner repository working directories with the runner `python` provided by `actions/setup-python`, preserving the original owner-validator execution contract instead of running `uv` in an owner repository context.
- Regression tests now cover both Node-mediated Python invocation and the explicit owner-validator system-Python boundary.

Additional validation after this boundary fix:

- `uv lock --check`
- `uv sync --locked --extra dev --extra ui`
- `uv run --locked pytest tests/personal_use tests/reporting/test_workflow_permissions.py tests/test_cli.py`
- `uv run --locked python scripts/check-github-action-pinning.py`
- `uv run --locked python scripts/check-workflow-permissions.py`
- `uv run --locked python scripts/check-capability-truth.py`
- `npm run validate`
- `uv run --locked pytest`
- `npm run status`
- `uv run --locked ev4-transition inspect`
- `uv run --locked python scripts/run-project-gate-demo.py --run-id uv-boundary-fix-smoke`

Remote GitHub Actions still need to rerun on the updated head before CI success can be claimed.
