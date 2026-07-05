# EV4 Project Gate Status Decision Matrix

Status: `PROMPT-05` Project Gate-owned status foundation with Builder→Responsive and Final Gate fail-closed rules.

## Target Project Gate statuses

| Status | Meaning | Exit code | Presentation |
|---|---|---:|---|
| `accepted` | Required evidence for this check is explicit and no blocking diagnostic exists. | `0` | ✅ / success / پذیرفته شد |
| `repair_needed` | Input is structurally understandable, but repairable warning diagnostics exist. | `1` | 🛠️ / warning / نیازمند اصلاح |
| `insufficient_evidence` | Input is parseable/understood, but required evidence is missing or unresolved. | `2` | ⚠️ / warning / شواهد کافی نیست |
| `invalid` | Input violates schema, identity, hash, lock, or fail-closed rules. | `1` | ❌ / danger / نامعتبر |

`insufficient_evidence` is a warning/blocking state, not ordinary info.

## Diagnostic-to-status mapping

Target transition mapping:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
warning: repair_needed
none_or_info_only: accepted
```

Legacy validation mapping remains only for older Stage Bundle and Architect→CE paths:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
none_or_warning_or_info: valid
```

## Builder → Responsive accepted policy

`ev4-builder-to-responsive-transition@1.0.0` may emit `accepted` only when all of the following are true:

```yaml
builder_evidence_refs_present: true
builder_lock_hashes_match: true
responsive_input_schema_verified: true
responsive_input_validator_passed: true
viewport_evidence_present: true
no_forbidden_claim: true
synthetic_only_evidence_not_used_as_real_evidence: true
result_schema_valid: true
```

Builder→Responsive must emit `insufficient_evidence` when Builder evidence refs, viewport refs, Responsive schema access, or official Responsive validator execution is absent or unverifiable.

Builder→Responsive must emit `invalid` when a lock/hash/schema identity mismatch or forbidden readiness/correctness claim is detected.

## Final Evidence Gate accepted policy

`ev4-final-evidence-gate@1.0.0` may emit `accepted` only when all of the following are true:

```yaml
prior_lock_chain_verified: true
responsive_output_present: true
responsive_output_schema_verified: true
responsive_output_validator_passed: true
real_evidence_present: true
no_forbidden_final_claim: true
result_schema_valid: true
```

The Final Gate must emit `invalid` for `production_ready`, `release_ready`, `frontend_correctness`, `responsive_correctness`, `pixel_perfect`, `accessibility_passed`, `export_json_validated`, or equivalent claims unless owner evidence and owner validators explicitly authorize them.

The Final Gate must emit `insufficient_evidence` when real non-synthetic Responsive evidence, Responsive output schema access, official validator execution, or prior lock-chain verification is missing.

## CI and screenshot limits

CI success is never frontend correctness evidence. Raw screenshots are never sufficient to prove responsive correctness. These inputs can be recorded as artifacts, but they cannot unlock `accepted` unless they are tied to explicit owner-validated evidence contracts.
