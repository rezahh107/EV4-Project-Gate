# Prompt 00 Handoff — Common Contract Foundation

- PR: #39
- Branch: feature/project-gate-common-contract-foundation
- Base SHA observed before completion: 0c5c3e812b0aeac836e303094a25ca6ab4983105
- Initial head SHA observed before completion: a1c07092ad95fe1c67da490ffa2209b7633a3460
- Final head SHA: recorded in final PR body and final operator report after push; not embedded here to avoid self-referential commit drift
- Commits added in completion pass: completion commit on PR branch, `fix: complete Prompt 0 common contract foundation`

## Files changed

Prompt 0 completion updates the Producer Gate Export validator, common-contract verifier hardening, Prompt 0 fixtures/tests, active status files, behavioral coverage, active contract/compatibility/validation docs, and this handoff.

## Tests run

- ✅ `python -m pip install -e '.[dev]'`
- ✅ `pytest`
- ✅ `python scripts/verify-vendored-common-contract.py --help`
- ✅ `python scripts/validate-behavioral-rule-coverage.py`
- ✅ `python scripts/check-capability-truth.py`
- ✅ `python scripts/check-workflow-permissions.py`
- ✅ `python scripts/check-github-action-pinning.py`
- ✅ `npm run status`
- ✅ `npm run validate`

## Tests not run

Exact-head CI pending until the completion commit is pushed. No local required command was intentionally skipped.

## CI checks observed

Initial exact head `a1c07092ad95fe1c67da490ffa2209b7633a3460`: skeleton success, python-core failure, prompt-05 success, report-ux success, ui-runtime-smoke success.

## Coverage rules advanced

Prompt 0 rules PG-P00-001 through PG-P00-012 were added to active behavioral coverage with honest statuses. No downstream contract enforcement is claimed.

## Coverage gaps

Producer adoption, downstream Producer CI enforcement, Project Gate runtime integration, and real non-synthetic handoff evidence remain gaps.

## New diagnostics

Producer Gate Export diagnostics include `PG_EXPORT_*` semantic checks for duplicate stages, stage ordering, output integrity, handoff blockers, final Stage Bundle binding, acquisition mode, and self-validation overclaim. Common contract lock diagnostics include path safety, moving refs, exact byte mismatch, hash mismatch, owner/path drift, and file-read failure checks.

## CLI/CI changes

Reusable workflow remains read-only and deterministic. The local verifier remains filesystem-only and does not use network, subprocess, or git commands.

## Design decisions

Producer Gate Export v1 is run-level only and composes Stage Bundle v1. Stage Bundle v1 remains authoritative for single-stage evidence. Exact byte equality is mandatory for vendored common contracts.

## Web sources used

GitHub API endpoints for PR #39 metadata, files, comments, reviews, and check runs.

## Adoption and integration status

```yaml
producer_adoption: not_started
project_gate_runtime_integration: not_implemented
downstream_producer_ci_enforcement: not_implemented
real_non_synthetic_handoff: insufficient_evidence
project_gate_contract_pin:
  status: pending_merge
```

## Prompt 1 condition

Prompt 1 remains blocked until PR #39 is merged and the canonical Project Gate merged commit SHA is known for immutable Producer pinning.
