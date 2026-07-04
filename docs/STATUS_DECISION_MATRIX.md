# EV4 Project Gate Status Decision Matrix

Status: `PROMPT-01` Project Gate-owned status foundation.

## Target Project Gate statuses

| Status | Meaning | Exit code | Presentation |
|---|---|---:|---|
| `accepted` | Required evidence for this check is explicit and no blocking diagnostic exists. | `0` | ✅ / success / پذیرفته شد |
| `repair_needed` | Input is structurally understandable, but repairable warning diagnostics exist. | `1` | 🛠️ / warning / نیازمند اصلاح |
| `insufficient_evidence` | Input is parseable/understood, but required evidence is missing or unresolved. | `2` | ⚠️ / warning / شواهد کافی نیست |
| `invalid` | Input violates schema, identity, hash, lock, or fail-closed rules. | `1` | ❌ / danger / نامعتبر |

`insufficient_evidence` is a warning/blocking state, not ordinary info.

## Schema-level carrier rules

`schemas/transition-result/transition-result.v1.schema.json` enforces basic status/diagnostic/evidence correlation:

```yaml
accepted:
  source_stage: concrete stage, not null
  hashes: non-null, property-specific scopes
  provenance: non-empty source_provenance.kind and produced_by.tool
  diagnostics: empty or info-only
repair_needed: at least one warning and no error/insufficient_evidence diagnostics
insufficient_evidence: at least one insufficient_evidence diagnostic and no error diagnostics
invalid: at least one error diagnostic
valid: legacy compatibility with empty/info/warning diagnostics
```

## Legacy compatibility

Current Stage Bundle validation and the existing Architect→CE transition still emit `valid` in some established result paths. `valid` is treated as a legacy alias of `accepted` only for presentation and exit-code mapping.

This compatibility preserves the current legacy producer behavior where warning-only diagnostics still map to `valid`. It does not authorize future transition code to invent evidence or emit `accepted` without explicit evidence.

## Diagnostic-to-status mapping

Target transition mapping:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
warning: repair_needed
none_or_info_only: accepted
```

Current legacy validation mapping:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
none_or_warning_or_info: valid
```

The legacy mapping remains only to avoid breaking existing `Architect→CE` behavior in `PROMPT-01`. Future transition-specific prompts should move transition result status production to the target mapping.
