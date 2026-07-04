# Builder → Responsive Freeze Matrix

Status: documented baseline only. The Builder → Responsive Project Gate transition is not implemented in this PR.

## Boundary model

```text
Builder output and build evidence
→ Project Gate file-byte pin/hash and validator orchestration
→ Responsive input boundary
→ Responsive output and viewport evidence
```

Project Gate coordinates contract identity, version checks, official validators, file-byte hashes, provenance, diagnostics, and handoff packaging. Builder and Responsive remain authoritative for their specialist behavior.

## Explicit non-claims

```yaml
project_gate_builder_to_responsive_transition: not_implemented
python_transition_module_added: false
builder_runtime_behavior_changed: false
responsive_repair_behavior_changed: false
real_elementor_validation_claimed: false
frontend_correctness_claimed: false
responsive_correctness_claimed: false
accessibility_completion_claimed: false
export_validation_claimed: false
production_ready_claimed: false
```

## Builder output and evidence artifacts

Builder currently does not define a single formal Builder-owned export schema named `ev4-builder-to-responsive-handoff`.

```yaml
builder_formal_responsive_export:
  status: not_implemented
  schema_file: null
  validator: null
  fixture_suite: null
  boundary_doc: EV4-Builder-Assistant-Repo/docs/BUILDER_TO_RESPONSIVE_HANDOFF_BOUNDARY.md
```

Current Builder-owned artifacts that may be pinned by future Project Gate work:

```yaml
builder_context_package:
  schema: ev4-builder-context-package@1.0.0
  schema_file: EV4-Builder-Assistant-Repo/schemas/builder-context-package.schema.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-package.mjs
  fixtures:
    - tests/valid/builder_context_package*.json
    - tests/valid/center_anchored_symmetric_reference_ready.json
    - examples/smart-home-connector/builder_context_package.json

action_batch:
  schema: ev4-action-batch@1.0.0
  schema_file: EV4-Builder-Assistant-Repo/schemas/action-batch.schema.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-action-batch.mjs
  command: npm run validate:action-batch

layout_check:
  schema: ev4-layout-check@0.1.0
  schema_file: EV4-Builder-Assistant-Repo/schemas/layout-check.schema.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-layout-check.mjs
  command: npm run validate:layout-check
  fixtures:
    - tests/valid/layout_check*.json
    - tests/invalid/layout_check*.json

completion_gate:
  schema: ev4-completion-gate@0.1.0
  schema_file: EV4-Builder-Assistant-Repo/schemas/completion-gate.schema.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-completion-gate.mjs
  command: npm run validate:completion-gate
  fixtures:
    - tests/valid/completion_gate*.json
    - tests/invalid/completion_gate*.json

real_elementor_execution_evidence:
  schema: ev4-real-elementor-execution-evidence@1.0.0
  schema_file: EV4-Builder-Assistant-Repo/schemas/real-elementor-execution-evidence.schema.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-real-elementor-execution-evidence.mjs
  positive_fixture:
    - examples/smart-home-connector/real_elementor_execution_evidence.template.json
  negative_fixtures:
    - tests/invalid/real_elementor_execution_evidence_claim_without_proof.json
    - tests/invalid/real_elementor_execution_evidence_duplicate_ref.json
    - tests/invalid/real_elementor_execution_evidence_conflicting_next_action.json
    - tests/invalid/real_elementor_execution_evidence_repair_next_action_conflict.json

central_validation:
  file: EV4-Builder-Assistant-Repo/scripts/validate.mjs
  command: npm run validate
  workflow: EV4-Builder-Assistant-Repo/.github/workflows/schema-validation.yml
```

## Responsive input and output artifacts

Responsive currently records a Builder-specific input boundary, but it does not yet implement a formal Builder-specific input package schema or validator.

```yaml
builder_to_responsive_input_package:
  status: not_implemented
  boundary_doc: EV4-Responsive-Architect/contracts/BUILDER_TO_RESPONSIVE_INPUT_BOUNDARY.md
  schema_file: null
  validator: null
  fixture_suite: null
```

Current Responsive-owned surfaces that may be pinned by future Project Gate work:

```yaml
main_pipeline_input_contract:
  file: EV4-Responsive-Architect/contracts/MAIN_PIPELINE_HANDOFF_INPUT_CONTRACT.md
  boundary: raw screenshots are evidence only, not authoritative baseline

submitted_packet_readiness:
  validator: EV4-Responsive-Architect/validation/e2e/run_submitted_packet_readiness_dry_run.py
  command: python validation/e2e/run_submitted_packet_readiness_dry_run.py --self-test
  status: pre-pilot dry run only

responsive_output:
  schema: ev4-responsive-output@0.3.0
  schema_file: EV4-Responsive-Architect/schemas/ev4-responsive-output.schema.json
  validator: EV4-Responsive-Architect/validation/e2e/run_responsive_tree_architecture_refactor_check.py
  command: python validation/e2e/run_responsive_tree_architecture_refactor_check.py
  positive_fixtures:
    - validation/fixtures/valid/responsive_output_same_tree.valid.json
    - validation/fixtures/valid/responsive_output_viewport_tree.valid.json
    - validation/fixtures/valid/responsive_output_hybrid.valid.json
    - validation/fixtures/valid/responsive_output_blocked.valid.json
  negative_fixtures:
    - validation/fixtures/invalid/responsive_output_missing_forbidden_claims.invalid.json
    - validation/fixtures/invalid/responsive_output_empty_steps.invalid.json
    - validation/fixtures/invalid/responsive_output_duplicate_step_id.invalid.json
    - validation/fixtures/invalid/responsive_output_route_mode_mismatch.invalid.json
    - validation/fixtures/invalid/responsive_output_builder_mode_mismatch.invalid.json
    - validation/fixtures/invalid/responsive_output_noncanonical_breakpoint_scope.invalid.json
    - validation/fixtures/invalid/responsive_output_unresolved_ready_mismatch.invalid.json

responsive_handoff_export:
  contract: EV4-Responsive-Architect/contracts/EV4_RESPONSIVE_HANDOFF_EXPORT_CONTRACT.md
  schema_family: ev4-responsive-handoff-export@0.3.0

central_validation:
  workflow: EV4-Responsive-Architect/.github/workflows/validate.yml
  commands:
    - python validation/e2e/run_responsive_tree_architecture_refactor_check.py
    - python validation/e2e/run_submitted_packet_readiness_dry_run.py --self-test
    - python validation/e2e/run_evidence_intake_fixture_matrix_check.py
    - python validation/e2e/run_pilot_readiness_boundary_check.py
    - python validation/e2e/run_issue_8_preflight_boundary_check.py
    - python validation/e2e/run_rtaq_ssot_guard_check.py
    - python validation/e2e/run_status_merged_foundation_guard_check.py
```

## Recommended future pin/hash set

```yaml
must_pin_and_hash:
  builder:
    - docs/BUILDER_TO_RESPONSIVE_HANDOFF_BOUNDARY.md
    - schemas/action-batch.schema.json
    - schemas/layout-check.schema.json
    - schemas/completion-gate.schema.json
    - schemas/real-elementor-execution-evidence.schema.json
    - scripts/validate-action-batch.mjs
    - scripts/validate-layout-check.mjs
    - scripts/validate-completion-gate.mjs
    - scripts/validate-real-elementor-execution-evidence.mjs
    - scripts/validate.mjs
    - examples/smart-home-connector/real_elementor_execution_evidence.template.json
    - tests/valid/layout_check*.json
    - tests/invalid/layout_check*.json
    - tests/valid/completion_gate*.json
    - tests/invalid/completion_gate*.json
    - tests/invalid/real_elementor_execution_evidence_claim_without_proof.json
    - tests/invalid/real_elementor_execution_evidence_duplicate_ref.json
    - tests/invalid/real_elementor_execution_evidence_conflicting_next_action.json
    - tests/invalid/real_elementor_execution_evidence_repair_next_action_conflict.json
  responsive:
    - contracts/BUILDER_TO_RESPONSIVE_INPUT_BOUNDARY.md
    - contracts/MAIN_PIPELINE_HANDOFF_INPUT_CONTRACT.md
    - contracts/EV4_RESPONSIVE_HANDOFF_EXPORT_CONTRACT.md
    - schemas/ev4-responsive-output.schema.json
    - validation/e2e/run_responsive_tree_architecture_refactor_check.py
    - validation/e2e/run_submitted_packet_readiness_dry_run.py
    - validation/e2e/run_evidence_intake_fixture_matrix_check.py
    - validation/e2e/run_pilot_readiness_boundary_check.py
    - validation/e2e/run_issue_8_preflight_boundary_check.py
    - validation/e2e/run_rtaq_ssot_guard_check.py
    - validation/e2e/run_status_merged_foundation_guard_check.py
    - validation/fixtures/valid/responsive_output_same_tree.valid.json
    - validation/fixtures/valid/responsive_output_viewport_tree.valid.json
    - validation/fixtures/valid/responsive_output_hybrid.valid.json
    - validation/fixtures/valid/responsive_output_blocked.valid.json
    - validation/fixtures/invalid/responsive_output_missing_forbidden_claims.invalid.json
    - validation/fixtures/invalid/responsive_output_empty_steps.invalid.json
    - validation/fixtures/invalid/responsive_output_duplicate_step_id.invalid.json
    - validation/fixtures/invalid/responsive_output_route_mode_mismatch.invalid.json
    - validation/fixtures/invalid/responsive_output_builder_mode_mismatch.invalid.json
    - validation/fixtures/invalid/responsive_output_noncanonical_breakpoint_scope.invalid.json
    - validation/fixtures/invalid/responsive_output_unresolved_ready_mismatch.invalid.json
```

```yaml
should_pin_and_hash:
  builder:
    - README.md
    - STATUS.md
    - AGENTS.md
    - package.json
    - .github/workflows/schema-validation.yml
  responsive:
    - README.md
    - STATUS.md
    - AGENTS.md
    - requirements.txt
    - .github/workflows/validate.yml
```

```yaml
files_not_to_pin:
  - changelog-only history unless a transition rule explicitly depends on it
  - patch reports that are not active contracts
  - old planning notes
  - copied specialist schemas inside Project Gate
```

## Known conflicts resolved

```yaml
builder_formal_responsive_export:
  resolution: explicitly documented as not_implemented
responsive_builder_specific_input_schema:
  resolution: explicitly documented as not_implemented
raw_screenshot_authority:
  resolution: evidence_only; never authoritative baseline
ci_success_boundary:
  resolution: repository checks only; not real frontend or responsive correctness evidence
```

## Remaining unknowns

```yaml
remaining_unknowns:
  - no single Builder-owned Builder→Responsive export schema exists yet
  - no Responsive-owned Builder-specific input package schema exists yet
  - real submitted packet remains absent
  - real Elementor/frontend/responsive/export/accessibility evidence remains absent
```

These unknowns do not block implementing a future Project Gate Python gate as a fail-closed verifier, but they do block any accepted Builder→Responsive handoff result until the required artifacts and evidence exist.
