# Wave 5 — UX-Safe Kernel Decision Receipts

## Scope

Wave 5 adds a human-readable receipt layer for Project Gate reports and service/API output bundles.

This is a presentation-layer extension only. It does not change Kernel decision semantics, transition status, result schemas, evidence requirements, repair authority, or release readiness.

## Source of truth

A success receipt is allowed only when the machine-readable result already contains a complete Kernel decision trace with these fields:

- `decision_family`
- `decision_card_ref`
- `selected_option`
- `rejected_options`
- `evidence_refs`
- `evidence_state`
- `consumer_stage`

Receipt text is never accepted as lineage, evidence, readiness, downstream enforcement, runtime enforcement, or repair authority.

## User-facing receipt messages

Success:

```text
✅ این Gate decision به decision card کرنل وصل است؛ Project Gate فقط lineage و evidence را اعتبارسنجی کرده و تصمیم جدیدی ایجاد نکرده است.
```

Warning:

```text
⚠️ این Gate item هنوز رسید معتبر کرنل ندارد؛ بدون machine-readable trace کامل نباید به‌عنوان gate-pass معتبر عبور کند.
```

Blocked:

```text
⛔ Gate مسدود شد؛ decision lineage یا evidence کافی نیست و باید repair/reopen شود.
```

## Explicit non-claims

Wave 5 does not claim or add:

- CI enforcement
- sequence CI enforcement
- downstream contract enforcement
- runtime monitor enforcement
- release readiness
- production readiness
- Project Gate repair authority
- authored resolved state

## Implementation surfaces

The receipt helper is reusable from `ev4_transition.reports` and is included in:

- Persian plain summaries
- Markdown reports
- optional HTML reports through the Markdown renderer
- service/API `report_bundle.decision_receipt`

## Safety rule

Receipt status is derived from the existing machine-readable result and trace only:

- `accepted` with complete trace emits a success receipt.
- `accepted` with missing or invalid trace emits a warning receipt instead of a success receipt.
- every non-accepted status emits a blocked receipt, while preserving trace completeness metadata.

Project Gate must not use the receipt to upgrade a result, repair missing lineage, or convert text into gate-pass evidence.
