# S-003 / PG-INT — Unified Producer Handoff

## Scope

This workflow integrates the already implemented producer-emitted transitions:

```text
Architect Producer Gate Export → Project Gate → standalone CE input
CE Producer Gate Export → Project Gate → standalone Builder input
```

It does not execute Architect, CE, Builder, Builder→Responsive, Responsive validation, Final Gate, browser automation, or Elementor.

## Routing authority

The operator supplies one local Producer Gate Export JSON file. Project Gate:

1. captures one immutable local file snapshot;
2. performs strict JSON parsing;
3. validates the common Producer Gate Export contract;
4. verifies producer adoption identity and merged runtime pin;
5. resolves the handoff target from the validated envelope;
6. verifies that producer stage and target form a supported pair;
7. invokes the existing `architect-to-ce` or `ce-to-builder` producer dispatcher.

The route is never selected from the filename, UI label, or an operator-authored transition identifier.

Supported pairs:

```text
architect + ce-intake      → architect-to-ce
ce        + builder-intake → ce-to-builder
```

Builder and Responsive producer exports remain outside `S-003 / PG-INT` and fail closed as unsupported in this entrypoint.

## CLI

Install the normal project environment, then run one of the following. Only repository paths required by the detected transition are required.

Architect export:

```bash
uv run ev4-handoff architect-project-gate.json \
  --project-gate-repo . \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --output-dir ./outputs \
  --format persian
```

CE export:

```bash
uv run ev4-handoff ce-project-gate.json \
  --project-gate-repo . \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --builder-repo ../EV4-Builder-Assistant-Repo \
  --output-dir ./outputs \
  --format persian
```

The existing explicit commands remain available and unchanged:

```bash
uv run ev4-transition transition architect-to-ce ...
uv run ev4-transition transition ce-to-builder ...
```

## Local operator UI

Launch the focused local integration panel:

```bash
uv sync --extra dev --extra ui
uv run ev4-project-gate-handoff-ui
```

The panel has no transition selector. After upload it displays the detected source and destination and reveals only the repository path fields required for that route.

When the output field is empty, the facade creates a unique `.ev4_pg_int_*` directory directly inside the current Project Gate publication workspace. It does not use the uploaded file's system-temporary parent or the operating-system temporary directory. An explicit operator-selected output directory remains supported only when it resolves inside that same workspace.

## Operator path boundary

All CLI, service, and UI path inputs cross the same fail-closed normalization boundary before dispatch:

- `project_gate_repo`;
- the transition-specific specialist repository checkouts;
- `output_dir`;
- explicit output and receipt paths;
- `schema_root`;
- `lock_path`.

The boundary catches `OSError`, `ValueError`, and `RuntimeError`, including unknown-user `~username` expansion. The Project Gate root must exist, be an accessible directory, and expose readable strict-JSON adoption-registry and transition-target files before intake runs.

Classification remains explicit:

```text
malformed or unsafe operator path → invalid
missing required specialist checkout → insufficient_evidence
```

Repository identity, exact commit pins, owner validators, and lock verification remain delegated to the existing A2C and C2B dispatchers.

## Service API

Use `run_producer_handoff_request` with `ProducerHandoffRequest` from:

```python
from ev4_transition.service import ProducerHandoffRequest, run_producer_handoff_request
```

The response preserves:

- validated routing metadata;
- structured diagnostics;
- transition status and `handoff_allowed`;
- partial-publication truth;
- standalone artifact metadata;
- separate receipt metadata;
- Persian operator guidance.

## Publication outputs

Architect→CE defaults:

```text
ce-input.json
project-gate-a2c-receipt.json
```

CE→Builder defaults:

```text
builder-input.json
project-gate-c2b-receipt.json
```

The existing safe publication layer remains authoritative for workspace containment, path traversal and collision rejection, no-overwrite behavior, source/output separation, atomic publication, snapshot re-verification, and post-write checks.

A next-stage artifact is offered as a primary download only when:

```text
status == accepted
and handoff_allowed == true
and publication_state == published_verified
```

A separately published receipt remains independently downloadable. A blocked or insufficient-evidence output is never presented as consumable next-stage input.

## Evidence limits

This integration does not establish:

```text
real_non_synthetic Architect→CE handoff
real_non_synthetic CE→Builder handoff
Builder runtime execution
Builder→Responsive completion
production readiness
```
