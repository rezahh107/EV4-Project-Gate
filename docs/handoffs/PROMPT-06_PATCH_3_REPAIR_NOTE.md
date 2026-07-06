# PROMPT-06 Patch 3 Repair Note

This note records the follow-up repair applied to PR #37.

## Applied repair

- Added `src/ev4_transition/service/preflight_core.py` as the hardened implementation.
- Kept `src/ev4_transition/service/preflight.py` as the compatibility import path.
- Updated service exports to use the hardened preflight implementation.
- Added regression tests for malformed lock manifests, lock file read errors, and `repo_paths=None`.

## Defensive cases

- Non-dict lock JSON returns a structured `PreflightCheck` with `lock_manifest.invalid_format`.
- Invalid lock JSON returns `lock_manifest.invalid_json`.
- Lock read failure returns `lock_manifest.file_read_error`.
- Missing or non-array `files` returns `lock_manifest.files_not_array`.
- Required pinned-file read failure returns `pinned.<field>.file_read_error`.
- `request.repo_paths is None` falls back to `RepoPaths()`.

## Scope guard

No transition decision logic, schema rule, canonical JSON, hash verification, official validator, adapter, or specialist contract was changed.

## Validation status

Local full pytest and browser QA were not executed from this environment. CI result for PR #37 remains the merge gate.
