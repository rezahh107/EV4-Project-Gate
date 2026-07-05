# Report UX Contract

Status: `PROMPT-06` implementation-ready contract for CLI + generated Persian reports.

## Scope

Phase 1 interface remains:

```text
CLI + generated Persian reports
```

This contract does not introduce a local web UI, Gradio UI, desktop UI, or a new primary interface. Future HTML output is optional report rendering only.

## Non-mutation boundary

Report rendering must not mutate deterministic transition result objects.

Allowed report-layer operations:

- deep-copy result payloads before rendering;
- map status to user-facing label, icon, tone, and exit-code metadata;
- render Persian plain text, Markdown, optional HTML, and canonical JSON text;
- compute a report-only hash that excludes UI/progress-only events.

Forbidden report-layer operations:

- changing transition status;
- appending diagnostics to a validated final result;
- repairing missing evidence;
- normalizing specialist output;
- including progress events in the canonical final result hash.

## Status presentation

`src/ev4_transition/presentation/status_mapping.py` is the SSOT for status presentation:

| status | icon | semantic tone | Persian label | exit |
|---|---:|---|---|---:|
| `accepted` | ✅ | `success` | پذیرفته شد | `0` |
| `repair_needed` | 🛠️ | `warning` | نیازمند اصلاح | `1` |
| `insufficient_evidence` | ⚠️ | `warning` | شواهد کافی نیست | `2` |
| `invalid` | ❌ | `danger` | نامعتبر | `1` |

Status meaning must not rely on color alone. Every report status must include icon + text + semantic tone.

`insufficient_evidence` is warning/blocking. It must not be displayed as ordinary info.

## Persian RTL and technical LTR handling

Persian Markdown reports use `<section lang="fa" dir="rtl">`.

Technical fragments must remain LTR, isolated, monospace, and copyable:

- repository paths;
- commands;
- SHA-256 hashes;
- schema IDs;
- diagnostic codes;
- JSON/YAML keys;
- repo refs.

Markdown/HTML reports use `<bdi dir="ltr"><code>...</code></bdi>`.

Plain-text reports use Unicode LTR isolate characters around technical fragments.

Persian/Arabic text must not receive arbitrary or negative letter-spacing.

## Report sections

Generated Persian Markdown reports must include title, status, Persian explanation, next action, diagnostics summary, `Advanced / Evidence / Diagnostics`, and LTR technical references.

Plain-text reports must include the same primary meaning, with technical fragments isolated as LTR text.

Machine-readable JSON output remains canonical JSON and is not decorated with Persian UX text.

## Theme token contract

`src/ev4_transition/presentation/theme_tokens.py` defines explicit light/dark tokens for status, surfaces, text, border, and focus ring.

Dark mode must not be simple inversion. Status/error text must remain readable and must not be low-emphasis.

## Output writing contract

`src/ev4_transition/io/atomic_writer.py` owns output-write safety:

1. write to a temporary file in the destination directory;
2. flush Python buffers;
3. call `os.fsync()` when available;
4. validate written output when a validator is supplied;
5. atomically replace the final path with `os.replace()`;
6. report success only after the final path exists.

If output writing fails, the write result must stay failed and `download_available` must be `false`.

## Progress events

Long-running operations may emit progress events, but progress events are UI/runtime state. They must not be included in the canonical final result hash used for report verification.

## Tests

Coverage lives in `tests/ux_acceptance/`, `tests/typography_acceptance/`, `tests/theme_acceptance/`, and `tests/reporting/`.

CI wiring lives in `.github/workflows/prompt-06.yml`.
