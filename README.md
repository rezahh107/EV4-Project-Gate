# EV4 Project Gate

Status: planned workflow documented; Python engine and user interface are not implemented.

## Purpose

`EV4-Project-Gate` is the planned control center between the four EV4 specialist repositories:

```text
Architect → Project Gate → CE → Project Gate → Builder
→ Project Gate → Responsive → Project Gate → final evidence
```

Each specialist repository remains authoritative for its own schemas, validators, adapters, fixtures, and domain behavior. This repository coordinates cross-repository checks and package handoffs. It is not a canonical shared-schema owner or a fifth architecture authority.

## User Workflow

The intended daily experience is simple:

```text
1. Receive the current stage output.
2. Upload it to EV4 Project Gate.
3. Run one check.
4. Download the next-stage package or a repair package.
```

A successful screen shows a large success symbol, explicit accepted text, the completed stage, and one action to download the next-stage package.

A repair-needed screen shows an explicit repair status, a plain Persian explanation, and one action to download the repair package. Meaning must not depend on color alone. Technical evidence is optional detail.

The planned primary interface is a simple local browser application. GitHub Actions is the hidden automation and regression-testing layer, not the normal daily interface.

## Stage Gates

### Architect → CE

```text
Architect output
→ Architect validation
→ accepted: CE Input Package
→ repair needed: Architect Repair Package
```

### CE → Builder

```text
CE output
→ CE validation
→ official adapter
→ Builder intake validation
→ preservation checks
→ accepted: Builder Input Package
→ repair needed: CE or evidenced upstream repair package
```

### Builder → Responsive

```text
Builder output plus build evidence
→ Builder and evidence validation
→ Responsive intake validation
→ accepted: Responsive Input Package
→ repair needed: Builder or evidenced upstream repair package
```

### Responsive → Final Evidence

```text
Responsive output plus viewport evidence
→ responsive and regression checks
→ accepted: final evidence package
→ repair needed: Responsive or evidenced upstream repair package
```

## Package Loop

A repair package will identify the failed stage, explain the problem in plain Persian, retain the original output identity, include deterministic diagnostics, and describe the required complete corrected output. The user gives it to the model connected to the relevant repository and uploads the corrected output for another check.

A next-stage package contains only validated input and retained evidence needed by the next stage.

When responsibility cannot be established, the result remains:

```yaml
status: insufficient_evidence
repair_owner: unresolved
```

## Planned Python Engine

The internal verification engine is called `EV4 Contract Watch`.

Planned responsibilities:

```text
schema and provenance validation
official validator and adapter execution
field-lineage and preservation checks
versioned semantic rules
deterministic diagnostics and evidence bundles
repair-package and next-stage package assembly
```

It does not invent missing data, silently repair specialist outputs, select a winning schema, or claim success without evidence.

## Evidence Policy

Use explicit states:

```text
observed
exported
validated
resolved
derived
proposed
unverified
insufficient_evidence
```

Compatibility is checked through the real Producer → Adapter → Consumer path. A schema difference alone is not a compatibility verdict. Synthetic fixtures remain clearly identified as synthetic.

## Repository Responsibilities

```text
EV4-Architect-Repo
  architecture decisions and architecture handoff

EV4-Constructability-Engineer-Repo
  constructability and implementation-strategy proof

EV4-Builder-Assistant-Repo
  interactive Elementor execution and build evidence

EV4-Responsive-Architect
  post-build responsive validation and repair

EV4-Project-Gate
  cross-repository verification, user workflow, and evidence packaging
```

## Implementation Order

```text
1. Align README.md and agents.me in all five repositories.
2. Freeze the first user workflow and Phase 1 boundaries.
3. Identify real schemas, validators, adapters, and fixtures.
4. Build the offline-tested Python core.
5. Add Architect → CE.
6. Add CE → Builder.
7. Add Builder → Responsive and final responsive evidence checks.
8. Add GitHub Actions regression automation.
```

## Current Status

```yaml
repository_role: project_workflow_control_center
workflow_documentation: in_review
python_engine: not_implemented
user_interface: not_implemented
package_generation: not_implemented
canonical_schema_owner: false
```
