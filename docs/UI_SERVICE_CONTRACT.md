# UI Service Contract

## Purpose

The local operator UI calls the internal Python API directly:

```text
UI/operator panel -> run_gate_request(...) -> GateResponse
```

Normal UI use should not require typing Project Gate CLI commands.

## Imports

```python
from ev4_transition.service import GateRequest, RepoPaths, run_gate_request
```

## Choices

```text
validate_bundle
inspect_capabilities
architect_to_ce
ce_to_builder
builder_to_responsive
final_gate
```

## Required local paths

| choice | required local paths |
|---|---|
| `validate_bundle` | none; `project_gate_repo_path="."` resolves `schema_root` |
| `inspect_capabilities` | none |
| `architect_to_ce` | `architect_repo_path`, `ce_repo_path` |
| `ce_to_builder` | `ce_repo_path`, `builder_repo_path` |
| `builder_to_responsive` | `builder_repo_path`, `responsive_repo_path` |
| `final_gate` | `project_gate_repo_path`, `responsive_repo_path` |

Paths must be local checkout directories. GitHub URLs are rejected. Missing required paths return `insufficient_evidence`.

## Request shape

```python
GateRequest(
    transition_choice="validate_bundle",
    input_json_path=None,
    input_json_text=None,
    input_data=None,
    repo_paths=RepoPaths(project_gate_repo_path="."),
    schema_root="schemas",
    lock_path=None,
    required_evidence_ids=[],
    timeout_seconds=30,
    require_real_evidence=True,
)
```

Use exactly one JSON source for all choices except `inspect_capabilities`: `input_json_path`, `input_json_text`, or `input_data`.

## Response shape

```python
response.status
response.transition_choice
response.engine_result
response.service_diagnostics
response.capabilities_snapshot
response.report_bundle
response.download_filenames
response.user_message_fa
response.next_action_fa
```

`response.to_dict()` returns a plain UI-friendly dictionary.

## Status meanings

| status | meaning |
|---|---|
| `accepted` | Accepted only within the explicit evidence scope. |
| `repair_needed` | Understood, but needs repair before safe transition. |
| `insufficient_evidence` | Required local checkout, official validator, real evidence, lock data, or owner evidence is missing. |
| `invalid` | JSON, schema, identity, transition choice, or service/engine execution failed. |

## UI must not claim

The UI must not claim production readiness, real Elementor validation, frontend correctness, responsive correctness, accessibility completion, export validation, real end-to-end EV4 readiness, CE constructability completion, Builder runtime authorization, or Responsive repair completion.

## Minimal example

```python
from ev4_transition.service import GateRequest, RepoPaths, run_gate_request

response = run_gate_request(
    GateRequest(
        transition_choice="validate_bundle",
        input_json_text='{"schema_version":"stage-evidence-bundle.v1"}',
        repo_paths=RepoPaths(project_gate_repo_path="."),
    )
)

print(response.status)
print(response.user_message_fa)
print(response.report_bundle.persian_plain_summary)
```

## CE to Builder example

```python
from ev4_transition.service import GateRequest, RepoPaths, run_gate_request

response = run_gate_request(
    GateRequest(
        transition_choice="ce_to_builder",
        input_json_path="/path/to/ce-stage-bundle.json",
        repo_paths=RepoPaths(
            project_gate_repo_path="/path/to/EV4-Project-Gate",
            ce_repo_path="/path/to/EV4-Constructability-Engineer-Repo",
            builder_repo_path="/path/to/EV4-Builder-Assistant-Repo",
        ),
    )
)

if response.status == "insufficient_evidence":
    print(response.next_action_fa)
```

## Download fields

- `canonical_json` -> `response.download_filenames["json"]`
- `persian_plain_summary` -> `response.download_filenames["summary_txt"]`
- `markdown_report` -> `response.download_filenames["markdown"]`
- `html_report` -> `response.download_filenames["html"]`

If a report field is `None`, hide that download option.
