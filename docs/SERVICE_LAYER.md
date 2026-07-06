# Project Gate Service Layer

## Status

```yaml
scope: internal_python_service_api
ui_implementation: not_in_scope
public_cli_transitions_added: false
transition_semantics_changed: false
official_specialist_contracts_changed: false
real_non_synthetic_evidence_claimed: false
```

## Purpose

The service layer lets a future local operator UI call Project Gate checks through direct Python functions instead of asking the user to type CLI commands.

```text
UI/operator panel
→ ev4_transition.service.run_gate_request(...)
→ existing Project Gate Python boundaries
→ structured GateResponse + downloadable reports
```

The service layer is a safe adapter. It is not a new transition engine and it does not implement specialist logic.

## Package layout

```text
src/ev4_transition/service/
  __init__.py
  models.py
  json_input.py
  repo_paths.py
  capabilities.py
  dispatcher.py
  reports.py
```

## Responsibilities

- `models.py`: typed dataclasses for `GateRequest`, `GateResponse`, `RepoPaths`, `ServiceDiagnostic`, and `ReportBundle`.
- `json_input.py`: parses exactly one JSON source: file path, pasted JSON text, or already parsed data. Malformed, missing, unreadable, or ambiguous input returns structured invalid diagnostics.
- `repo_paths.py`: validates local checkout paths. Empty required paths, GitHub URLs, missing paths, and non-directory paths return `insufficient_evidence`.
- `capabilities.py`: reads `src/ev4_transition/data/capability-status.v1.json` and returns a deep copy without upgrading claims.
- `dispatcher.py`: exposes `run_gate_request(request: GateRequest) -> GateResponse` and calls existing Python transition boundaries directly.
- `reports.py`: builds canonical JSON, Persian plain text, Markdown, and HTML report strings without mutating the result.

## Supported choices

```text
validate_bundle
inspect_capabilities
architect_to_ce
ce_to_builder
builder_to_responsive
final_gate
```

## Direct execution boundaries

| Choice | Direct Python boundary |
|---|---|
| `validate_bundle` | `BundleValidator(...).validate_bundle(...)` |
| `inspect_capabilities` | `get_capabilities()` |
| `architect_to_ce` | `ev4_transition.architect_to_ce.transition_from_local_paths(...)` with current validator hooks |
| `ce_to_builder` | `ev4_transition.transitions.ce_to_builder.transition_from_local_paths(...)` |
| `builder_to_responsive` | `ev4_transition.transitions.builder_to_responsive.transition_from_local_paths(...)` |
| `final_gate` | `ev4_transition.transitions.final_gate.final_gate_from_local_paths(...)` |

## Fail-closed behavior

The service returns structured failure when JSON is missing or malformed, required local checkouts are missing, a GitHub URL is supplied where a local path is required, local files cannot be read, result schema validation fails, or an unknown transition choice is requested.

`accepted` is not invented by the service layer. If an engine result has a supported status, the service response preserves it. Legacy `valid` from Stage Evidence Bundle validation is mapped to service-level `accepted`, while the original engine result remains unchanged inside `engine_result`.

## Non-goals

This layer does not implement UI layout, new public CLI transitions, CE constructability logic, Builder runtime logic, Responsive repair logic, official specialist validators/adapters/schemas/locks, production readiness, real Elementor validation, frontend correctness, responsive correctness, accessibility completion, or export validation claims.
