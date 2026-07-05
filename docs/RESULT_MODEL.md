# EV4 Project Gate Result Model

Status: `PROMPT-03` runner boundary infrastructure added on branch `project-gate-prompt-03-runner-boundary`.

## Scope

This document describes Project Gate-owned result envelopes. It does not define any Architect, CE, Builder, or Responsive specialist payload semantics.

## Result schemas

```text
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
schemas/diagnostic/diagnostic.v1.schema.json
```

`transition-result.v1` is the common Stage Evidence Bundle validation result. It is intentionally narrow:

```yaml
schema_version: transition-result.v1
result_type: stage_bundle_validation
status: accepted | valid | repair_needed | insufficient_evidence | invalid
source_stage: architect | ce | builder | responsive | null
diagnostics: ordered diagnostic list
hashes: source bundle and payload canonical hashes when computable
provenance: preserved input provenance and producer identity
output: null
```

`valid` remains a legacy validation alias for the current Stage Bundle and Architect→CE implementation. The target Project Gate transition vocabulary is:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

`presentation/status_mapping.py` normalizes `valid` to `accepted` for exit-code and Persian presentation purposes.

## Status/schema correlation

`transition-result.v1` enforces the target result correlation at carrier level:

```yaml
accepted:
  source_stage: architect | ce | builder | responsive
  diagnostics: empty or info-only
  source_bundle_hash: required non-null hashRecord with scope=source_bundle
  canonical_payload_hash: required non-null hashRecord with scope=payload
  source_provenance: required object with non-empty kind
  produced_by: required object with non-empty tool
valid:
  diagnostics: empty, info, or warning
  evidence_requirement: legacy compatibility, not a future-transition acceptance rule
repair_needed:
  diagnostics: at least one warning
  forbidden_diagnostics: error, insufficient_evidence
insufficient_evidence:
  diagnostics: at least one insufficient_evidence
  forbidden_diagnostics: error
invalid:
  diagnostics: at least one error
```

## Diagnostic ordering

Diagnostics must be deterministic. Current ordering is:

```text
path → severity rank → code → message
```

Severity rank is:

```text
error
insufficient_evidence
warning
info
```

## Hash behavior

Project Gate result hashes use:

```yaml
algorithm: sha256
canonicalization: ev4-canonical-json.v1
encoding: utf8
object_keys: lexicographic
arrays: order_preserved
nan_infinity: rejected
unicode_normalization: not_applied
```

For `accepted`, each hash property has a property-specific scope: `source_bundle_hash.scope` must be `source_bundle`, and `canonical_payload_hash.scope` must be `payload`.

Progress/runtime state must not be appended after final result schema validation and must not be included in canonical result hashes.

## Official tool execution record

`PROMPT-03` adds Project Gate-owned execution-record infrastructure under `src/ev4_transition/runners/`. Execution records are runtime evidence metadata for official specialist validators/adapters. They are not specialist schemas and do not encode specialist business rules.

Validator execution record minimum children:

```yaml
owner_repo: owner/repo of official validator
owner_commit: pinned owner commit; successful official validator runs must not use unknown
validator_path: repo-relative validator path
command: command list used by the runner
working_directory: repo-relative/safe working directory label
exit_code: integer or null if execution never completed
stdout_hash: SHA-256 of exact stdout bytes
stderr_hash: SHA-256 of exact stderr bytes
execution_record_hash: SHA-256 over canonical execution record without this field
started_by: runner identity
timeout_policy:
  seconds: numeric timeout
  kill_process_tree: bool
parsed_result_ref: reference to parsed result source, usually stdout:json
```

Adapter execution record minimum children:

```yaml
owner_repo: owner/repo of official adapter
owner_commit: pinned owner commit or explicit unresolved marker
adapter_path: repo-relative adapter path
command_or_entrypoint: command list or entrypoint name used by the runner; must execute adapter_path directly or through a trusted interpreter
input_ref: input artifact reference
input_hash: SHA-256 of canonical input/artifact bytes
output_ref: output artifact reference, if produced
output_hash: SHA-256 of output artifact bytes, if produced
execution_record_hash: SHA-256 over canonical execution record without this field
validator_after_adapter_ref: validator evidence reference required after adapter output is produced
```

Failure mapping is deterministic and fail-closed:

```yaml
validator_timeout:
  status: insufficient_evidence
  diagnostic: PG.VALIDATOR.TIMEOUT
adapter_timeout:
  status: insufficient_evidence
  diagnostic: PG.ADAPTER.TIMEOUT
command_not_found:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.COMMAND_NOT_FOUND
validator_missing:
  status: insufficient_evidence
  diagnostic: PG.VALIDATOR.MISSING
adapter_missing:
  status: insufficient_evidence
  diagnostic: PG.ADAPTER.MISSING
nonzero_exit_with_structured_repair:
  status: repair_needed
  diagnostic: PG.VALIDATOR.REPAIR_NEEDED
nonzero_exit_with_contract_violation:
  status: invalid
  diagnostic: PG.VALIDATOR.CONTRACT_VIOLATION
unparseable_output:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.UNPARSEABLE_OUTPUT
execution_crash_without_structured_result:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.EXECUTION_FAILED
fallback_adapter_used:
  status: invalid
  diagnostic: PG.ADAPTER.FALLBACK_FORBIDDEN
adapter_command_path_mismatch:
  status: invalid
  diagnostic: PG.ADAPTER.COMMAND_PATH_MISMATCH
```

Raw stdout/stderr are not stored in execution records. Only `stdout_hash` and `stderr_hash` are retained.

## Progress events

Progress events are runtime/UI artifacts only. They must not be included in canonical final result hashes.

Progress event sanitization rejects:

```yaml
- secret/token/password/API-key-like keys or values
- raw environment variables
- raw stdout
- raw stderr
- private absolute paths unless explicitly allowed
```

By default, paths in progress events are converted to repo-relative paths when a `repo_root` is provided.

## Evidence rule

No result may be presented as `accepted` unless the required evidence for that result scope is explicit. Missing, empty, swapped, or unresolved evidence must remain `insufficient_evidence` or `invalid` according to the diagnostic set.
