# Behavioral Rule Coverage

Status: `PROMPT-01` Project Gate-owned contracts and deterministic core hardening. This file records current behavioral enforcement status honestly. It does not claim enforcement without a carrier, validator, fixture, CI step, or downstream contract.

Allowed statuses:

```text
prose_only
schema_backed
validator_backed
fixture_tested
ci_enforced
downstream_contract_enforced
```

## Coverage table

| Rule ID | Rule | Current carrier | Validator | Fixture/test | CI | Downstream evidence | Current status | Next enforcement step |
|---|---|---|---|---|---|---|---|---|
| `PG-BOUNDARY-001` | Project Gate must remain an orchestrator/checkpoint, not a specialist engine. | `README.md`, `AGENTS.md`, `docs/ROLE_BOUNDARY_MAP.md`, `docs/ARCHITECTURE.md` | Partial: schema allowlist in CI prevents unexpected copied schema files. | No dedicated boundary scanner. | Partial via `.github/workflows/validate.yml` schema allowlist. | Specialist repo boundary docs. | `ci_enforced` for schema-copy subset; broader rule remains partial. | Add static boundary scanner for forbidden specialist logic/imports/prose claims. |
| `PG-SCHEMA-001` | Project Gate must not copy specialist schemas as competing canonical contracts. | `AGENTS.md`, `docs/VALIDATION_STRATEGY.md`, `schemas/README.md`, workflow schema allowlist. | Workflow `find schemas` allowlist. | CI checks current `schemas/` allowlist. | Final R2 CI must pass before merge. | Specialist schemas remain in owner repos. | `fixture_tested` until final R2 CI passes. | Extend scanner to future contract folders and lock manifests. |
| `PG-EVIDENCE-001` | No accepted/final result without explicit evidence. | `docs/RESULT_MODEL.md`, `docs/STATUS_DECISION_MATRIX.md`, Stage Bundle schema, validators, docs. | `BundleValidator`; `transition-result.v1` now requires concrete `source_stage`, property-specific hash scopes, non-empty provenance identity, and no warning/error/insufficient_evidence diagnostics under `accepted`. | Result status-correlation negative tests cover accepted-with-error, accepted-without-hash/provenance, empty provenance objects, swapped hash scopes, null source stage, and repair/insufficient/invalid contradictions. | Final R2 CI must pass before merge. | Limited to Stage Bundle and A2C synthetic fixtures. | `fixture_tested` at carrier level; full future transition evidence acquisition remains a gap. | Add transition-specific accepted-gate validators when CE→Builder/Builder→Responsive/final gates are implemented. |
| `PG-SYNTH-001` | Synthetic fixtures must not be treated as real EV4 evidence. | README, AGENTS, Stage Bundle `synthetic`, docs. | Stage Bundle schema requires top-level `synthetic`. | Prompt 01 adds missing synthetic-label negative fixture test. | Final R2 CI must pass before merge. | No real downstream evidence. | `fixture_tested` at carrier level. | Add report-level guard that blocks real-readiness wording when `synthetic=true` or verification is `synthetic_fixture_only`. |
| `PG-ADAPTER-001` | Project Gate may call official adapters but must not implement specialist adapter logic. | A2C mapping exists; Builder adapter documented in Builder repo. | Current Project Gate does not yet call Builder adapter. | None for CE→Builder in Project Gate. | None in Project Gate. | Builder adapter contract and registry exist downstream. | `prose_only` for future adapters; A2C has implemented deterministic projection only because CE-owned mapping is pinned. | In `PROMPT-03/04`, isolate adapter execution behind runner and prove no internal Builder adapter implementation. |
| `PG-VALIDATOR-001` | Project Gate must call official specialist validators where transition claims depend on them. | `validator_runner.py`; A2C transition. | Architect and CE validators called by subprocess when local checkouts supplied. | A2C transition tests and CI smoke. | Python CI runs official Architect and CE validator fixture suites when workflow executes. | Architect/CE official validators exist. | `ci_enforced` for A2C baseline when workflow passes; Prompt 01 did not expand validator execution. | Generalize runner boundary for future validator execution. |
| `PG-HASH-001` | Canonical JSON/file-byte hashes must be deterministic. | `canonical_json.py`; `src/ev4_transition/core/`; `external_lock.py`; schemas. | Canonical hash functions, explicit file-byte helper, and lock verifier; compatibility namespace re-exports `file_sha256` rather than reimplementing it. | Prompt 01 adds tests for stable JSON, NaN/Infinity rejection, object-key sorting, array preservation, file-byte hash change detection, and Unicode no-normalization. | Final R2 CI must pass before merge. | External A2C contract locks use file bytes. | `fixture_tested` for Prompt 01 additions; baseline A2C lock remains CI-configured. | Keep final CI evidence with PR #17 before merge. |
| `PG-LOCK-001` | External locks must verify pinned repo/ref/path/hash/identity and not trust themselves. | `external_lock.py`; `src/ev4_transition/locks/`; `schemas/lock-manifest/lock-manifest.v1.schema.json`; `contracts/locks/architect-to-ce-transition.v1.lock.json`. | `verify_external_contract_lock`; structural `validate_lock_manifest` now enforces non-empty `files`, schema allowlisted fields, `owner/repo`, 40-char lowercase commit SHA, 64-char lowercase SHA-256, and non-negative `size_bytes`. | Prompt 01 adds missing/unknown lock schema version tests and fail-closed negative tests for empty files, malformed repository, short/uppercase commit SHA, short/non-hex/uppercase hash, negative `size_bytes`, and unknown top-level/file-entry fields. | Final R2 CI must pass before merge. | Architect/CE pinned files. | `fixture_tested`; can be marked `ci_enforced` only after corrected-head CI passes. | Add transition-specific lock baselines for CE→Builder and Builder→Responsive in later prompts. |
| `PG-STATUS-001` | Status decisions must be evidence-driven and fail closed. | `docs/STATUS_DECISION_MATRIX.md`, `src/ev4_transition/presentation/status_mapping.py`, `diagnostics.py`, result schemas. | Legacy `status_from_diagnostics`; target `project_gate_status_from_diagnostics`; `transition-result.v1` status/diagnostic correlation; legacy `valid` permits warning to match the current producer. | Prompt 01 adds warning→repair_needed, insufficient_evidence→warning-tone, result schema contradiction tests, and an end-to-end legacy warning producer/schema test. | Final R2 CI must pass before merge. | Partial; current A2C implementation still emits legacy `valid`. | `fixture_tested` for mapping and carrier; direct target transition emission remains a gap. | Move future transition result emission to `accepted/repair_needed/insufficient_evidence/invalid` when evidence gates are implemented. |
| `PG-OUTPUT-001` | Machine-readable JSON and Persian summaries must be truthful. | CLI `_emit`; `persian_summary`; status mapping. | Result schemas validate JSON; Persian summary maps icon + label + meaning. | CLI tests include Persian insufficient evidence; Prompt 01 mapping tests added. | Final R2 CI must pass before merge. | No full UX contract enforcement. | `fixture_tested` for status presentation subset. | Add Persian RTL/LTR report fixtures and status icon + text + tone checks in `PROMPT-06`. |
| `PG-UNICODE-001` | Project Gate must not silently normalize Unicode for canonical hashing. | `canonical_json.py`; `src/ev4_transition/core/canonical_json.py`. | Canonical JSON implementation does not call Unicode normalization; explicit regression test added. | Prompt 01 adds composed/decomposed Unicode hash inequality test. | Final R2 CI must pass before merge. | None. | `fixture_tested`; can be marked `ci_enforced` only after corrected-head CI passes. | Add fixture-level Unicode corpus later if needed. |
| `PG-PROGRESS-001` | Project Gate reports must not claim unexecuted progress. | README/AGENTS no-false-execution policy; handoff requirement. | No validator for progress claims. | Handoff records run/fail/pass/not-run states. | No dedicated CI. | None. | `prose_only` | Add handoff/report schema or linter for executed/not-run/test fields. |
| `PG-BRC-001` | Behavioral coverage must be tracked honestly. | This file. | None yet. | None yet. | None yet. | None. | `prose_only` | Add behavioral coverage schema/validator/fixtures/CI in `PROMPT-02`. |
| `PG-DOWNSTREAM-001` | Downstream rejection evidence is required before claiming downstream compatibility. | Validation strategy docs; downstream validators in specialist repos. | A2C has Architect/CE validators; future transitions not wired. | Synthetic A2C fixtures only. | A2C official validator CI only when workflow executes. | CE/Builder/Responsive rejection evidence exists in owner repos but not orchestrated by Project Gate for future transitions. | `ci_enforced` for A2C baseline only; `prose_only` for CE→Builder and Builder→Responsive. | In `PROMPT-04/05`, run official downstream gates/adapters and capture rejection fixtures. |

## Critical / High gaps

```yaml
critical:
  - PG-ADAPTER-001 for CE-to-Builder and Builder-to-Responsive is prose_only in Project Gate.
  - PG-DOWNSTREAM-001 is not enforced for CE-to-Builder or Builder-to-Responsive.
high:
  - PG-BRC-001 has no schema/validator/fixture/CI yet.
  - PG-PROGRESS-001 lacks automated no-false-progress/handoff validation.
  - PG-OUTPUT-001 Persian UX is minimal and not yet full RTL/LTR/report-contract enforced.
  - Existing A2C and Stage Bundle paths still use legacy `valid`; target status vocabulary is available through mapping and docs but not emitted everywhere.
```

## Rules advanced by PROMPT-01

```yaml
advanced:
  - PG-HASH-001: explicit file-byte SHA-256 helper and deterministic canonical JSON regression tests added; compatibility namespace now re-exports the canonical helper.
  - PG-LOCK-001: Project Gate-owned lock manifest schema, strict structural lock manifest validator, schema allowlist checks, and fail-closed negative tests added.
  - PG-STATUS-001: target status presentation mapping and result schema status/diagnostic correlation added; legacy valid warning compatibility is explicit and tested.
  - PG-UNICODE-001: explicit no-hidden-Unicode-normalization test added.
  - PG-EVIDENCE-001: accepted carrier now requires concrete stage, property-specific hashes, non-empty provenance, and no blocking diagnostics.
  - PG-SYNTH-001: synthetic-label negative fixture path added.
not_advanced_to_full_enforcement:
  - no CE-to-Builder implementation added
  - no Builder-to-Responsive implementation added
  - no final evidence gate added
  - no new specialist schema copied
  - final R2 CI result must be checked before merge
```

## Inspector follow-up

The first PR Inspector pass reported that `validate_lock_manifest()` was weaker than `schemas/lock-manifest/lock-manifest.v1.schema.json` and `docs/LOCK_MANIFEST_POLICY.md`; strict format and fail-closed negative tests were added.

The second PR Inspector pass reported that `transition-result.v1` accepted contradictory `accepted` payloads and that `validate_lock_manifest()` still accepted unknown fields despite schema `additionalProperties: false`; result status correlation and lock unknown-field checks were added.

The R2 PR Inspector pass reported accepted evidence bypasses for null stage, empty provenance, and swapped hash scopes, plus a legacy `valid + warning` producer/schema conflict. The accepted carrier was tightened and legacy warning compatibility was made explicit and tested.

## Enforcement honesty note

No Critical/High future-transition rule should be described as fully enforced until the required carrier, official validator/adapter execution, fixture, CI step, and downstream rejection evidence exist.
