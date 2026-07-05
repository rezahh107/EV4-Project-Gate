# EV4 Project Gate Diagnostic Codes

Status: `PROMPT-04` registry for Project Gate-owned diagnostics.

## Schema

Diagnostics are validated by:

```text
schemas/diagnostic/diagnostic.v1.schema.json
```

Required fields:

```yaml
code: stable Project Gate diagnostic code
severity: error | warning | info | insufficient_evidence
message: non-empty human-readable text
path: JSON path-like location
details: optional object
```

## Core diagnostics

| Code | Severity | Owner | Meaning |
|---|---|---|---|
| `INPUT_NOT_OBJECT` | `error` | Project Gate | Stage Evidence Bundle input is not a JSON object. |
| `MALFORMED_JSON` | `error` | Project Gate | Input file is not valid JSON. |
| `FILE_READ_ERROR` | `error` | Project Gate | Input file could not be read. |
| `SCHEMA_VALIDATION_FAILED` | `error` | Project Gate | Project Gate-owned envelope/result schema validation failed. |
| `NON_FINITE_NUMBER` | `error` | Project Gate | NaN or Infinity was found and rejected. |
| `REQUIRED_EVIDENCE_MISSING` | `insufficient_evidence` | Project Gate | Required evidence id is absent. |
| `BUNDLE_INSUFFICIENT_EVIDENCE` | `insufficient_evidence` | Project Gate | Bundle explicitly declares unresolved or insufficient evidence. |
| `PG.VALIDATOR.MISSING` | `insufficient_evidence` | Project Gate | Required official validator checkout/path is unavailable. |
| `PG.ADAPTER.MISSING` | `insufficient_evidence` | Project Gate | Required official adapter checkout/path is unavailable. |
| `PG.ADAPTER.EXECUTION_FAILED` | `insufficient_evidence` | Project Gate | Official adapter execution failed without acceptable structured output. |

## Generic lock diagnostics

| Code | Severity | Owner | Meaning |
|---|---|---|---|
| `PG_LOCK_SCHEMA_VERSION_MISSING` | `error` | Project Gate | Lock manifest has no schema version. |
| `PG_LOCK_SCHEMA_VERSION_UNKNOWN` | `error` | Project Gate | Lock manifest schema version is unsupported. |
| `PG_LOCK_TRANSITION_ID_INVALID` | `error` | Project Gate | Lock manifest `transition_id` is missing or invalid. |
| `PG_LOCK_FILES_NOT_ARRAY` | `error` | Project Gate | Lock manifest `files` is not an array. |
| `PG_LOCK_HASH_INVALID` | `error` | Project Gate | Lock entry file-byte hash is not a lowercase SHA-256 digest. |

## CE→Builder diagnostics

`PG.C2B.*` diagnostics are scoped to `ev4-ce-to-builder-transition@1.0.0`.

| Code | Severity | Owner | Meaning |
|---|---|---|---|
| `PG.C2B.LOCK_NOT_OBJECT` | `error` | Project Gate | CE→Builder lock manifest is not an object. |
| `PG.C2B.LOCK_VERSION_MISMATCH` | `error` | Project Gate | Lock schema version is missing or unsupported. |
| `PG.C2B.LOCK_TRANSITION_ID_MISMATCH` | `error` | Project Gate | Lock transition id does not match the CE→Builder transition module. |
| `PG.C2B.LOCK_FILES_NOT_ARRAY` | `error` | Project Gate | Lock `files` field is not an array. |
| `PG.C2B.LOCK_ENTRY_NOT_OBJECT` | `error` | Project Gate | A lock file entry is not an object. |
| `PG.C2B.LOCK_ROLE_UNEXPECTED` | `error` | Project Gate | A lock entry role is not one of the expected CE/Builder dependency roles. |
| `PG.C2B.LOCK_ROLE_DUPLICATE` | `error` | Project Gate | A lock entry role appears more than once. |
| `PG.C2B.LOCK_ROLE_MISSING` | `error` | Project Gate | One or more required owner dependency roles are missing. |
| `PG.C2B.LOCK_REPOSITORY_MISMATCH` | `error` | Project Gate | Lock repository does not match the transition-owned expected dependency. |
| `PG.C2B.LOCK_COMMIT_MISMATCH` | `error` | Project Gate | Lock accepted commit does not match the transition-owned expected dependency. |
| `PG.C2B.LOCK_PATH_MISMATCH` | `error` | Project Gate | Lock path does not match the transition-owned expected dependency. |
| `PG.C2B.LOCK_IDENTITY_MISMATCH` | `error` | Project Gate | Lock contract/schema id does not match the transition-owned expected dependency. |
| `PG.C2B.OWNER_FILE_READ_FAILED` | `insufficient_evidence` | Project Gate | A pinned CE/Builder owner file could not be read from the supplied checkout. |
| `PG.C2B.EXTERNAL_HASH_MISMATCH` | `error` | Project Gate | A pinned owner file SHA-256 digest does not match the lock manifest. |
| `PG.C2B.EXTERNAL_IDENTITY_MISMATCH` | `error` | Project Gate | The expected identity marker was not found in a pinned owner file. |
| `PG.C2B.INPUT_NOT_OBJECT` | `error` | Project Gate | CE→Builder input is not a JSON object. |
| `PG.C2B.CE_PACKAGE_MISSING` | `error` | Project Gate | Stage Evidence Bundle payload does not contain a CE Builder Executable Package. |
| `PG.C2B.CE_PACKAGE_NOT_OBJECT` | `error` | Project Gate | The CE Builder Executable Package is not an object. |
| `PG.C2B.CE_PACKAGE_SCHEMA_MISMATCH` | `error` | Project Gate | CE package schema identity is not `ev4-builder-executable-package@1.0.0`. |
| `PG.C2B.SYNTHETIC_ONLY_EVIDENCE` | `insufficient_evidence` | Project Gate | Synthetic CE fixture was presented where real evidence is required. |
| `PG.C2B.ADAPTER_OUTPUT_UNPARSEABLE` | `insufficient_evidence` | Project Gate | Official Builder adapter did not produce parseable JSON object output. |
| `PG.C2B.BUILDER_SCHEMA_UNAVAILABLE` | `insufficient_evidence` | Project Gate | Builder-owned output schema could not be read from the supplied owner checkout. |
| `PG.C2B.BUILDER_SCHEMA_VALIDATION_FAILED` | `error` | Project Gate | Builder adapter output does not satisfy the Builder-owned context schema. |
| `PG.C2B.FORBIDDEN_CLAIM` | `error` | Project Gate | CE→Builder encountered a forbidden readiness/runtime/production claim. |
| `PG.C2B.ACCEPTED_REQUIRES_MISSING` | `insufficient_evidence` | Project Gate | One or more `accepted_requires` entries remain false. |

## Boundary note

Architect→CE-specific `PG_A2C_*` diagnostics remain scoped to the existing Architect→CE transition and are not generalized to CE→Builder or Builder→Responsive.
