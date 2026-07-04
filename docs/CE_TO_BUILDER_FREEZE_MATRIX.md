# CE → Builder Freeze Matrix

Status: documented baseline only. The CE → Builder Project Gate transition is not implemented in this PR.

## Boundary model

```text
CE Builder Executable Package
→ Builder CE→Builder Contract Gate
→ Builder CE→Builder adapter
→ Builder Context Package
```

Project Gate coordinates pins, hashes, official validators, official adapters, provenance, diagnostics, and handoff packaging. Specialist logic remains in the specialist repositories.

## CE output contract

```yaml
contract_id: ev4-builder-executable-package@1.0.0
schema_file: EV4-Constructability-Engineer-Repo/schemas/builder_executable_package.schema.json
producer_contract: EV4-Constructability-Engineer-Repo/docs/CE_TO_BUILDER_PRODUCER_CONTRACT.md
official_validators:
  - EV4-Constructability-Engineer-Repo/validator/engine.py
  - EV4-Constructability-Engineer-Repo/validator/rules.py
  - EV4-Constructability-Engineer-Repo/scripts/validate-role-alignment-fixtures.py
validator_commands:
  package_file: python -m validator.engine <path> --repo-root . --mode package --json
  role_alignment: python scripts/validate-role-alignment-fixtures.py
positive_fixtures:
  - tests/role-alignment/valid/executable_visual_reference_package.json
negative_fixtures:
  - tests/role-alignment/invalid/builder_package_with_decisions.json
  - tests/role-alignment/invalid/visual_package_missing_golden_reference.json
normative_tests:
  - tests/test_architect_contract.py
```

CE preserves structured source evidence. The structured CE `connector_layer` object is producer data; Builder compact projection belongs to the downstream Builder adapter.

## Builder input contract and adapter

```yaml
contract_id: ev4-builder-context-package@1.0.0
schema_file: EV4-Builder-Assistant-Repo/schemas/builder-context-package.schema.json
input_contract: EV4-Builder-Assistant-Repo/input-contracts/BUILDER_CONTEXT_INPUT_CONTRACT.md
contract_gate:
  file: EV4-Builder-Assistant-Repo/scripts/validate-ce-to-builder-contract-gate.mjs
  command: node scripts/validate-ce-to-builder-contract-gate.mjs
adapter:
  file: EV4-Builder-Assistant-Repo/scripts/normalize-ce-builder-executable-package.mjs
  entrypoint: normalizeCeBuilderExecutablePackage(cePackage)
registry:
  file: EV4-Builder-Assistant-Repo/data/ce-builder-transformation-registry.v1.json
  validator: EV4-Builder-Assistant-Repo/scripts/validate-ce-builder-transformation-registry.mjs
positive_fixtures:
  - tests/valid/ce_to_builder_contract_gate_valid.json
  - tests/valid/ce_builder_package_adapter_valid.json
  - tests/valid/ce_reference_map_adapter_valid.json
negative_fixtures:
  - tests/invalid/ce_to_builder_contract_gate_missing_architect_approved_classes.json
  - tests/invalid/ce_to_builder_contract_gate_missing_batch_action_ids.json
  - tests/invalid/ce_to_builder_contract_gate_class_map_item_not_object.json
  - tests/invalid/ce_builder_package_adapter_not_executable_ready.json
  - tests/invalid/ce_builder_package_adapter_missing_carriers.json
```

Builder runtime intake is the normalized Builder Context Package, after the Builder-owned gate and adapter route.

## Future pin/hash recommendation

```yaml
must_pin_and_hash:
  ce:
    - docs/CE_TO_BUILDER_PRODUCER_CONTRACT.md
    - schemas/builder_executable_package.schema.json
    - validator/engine.py
    - validator/rules.py
    - scripts/validate-role-alignment-fixtures.py
    - tests/test_architect_contract.py
    - tests/role-alignment/valid/executable_visual_reference_package.json
    - tests/role-alignment/invalid/builder_package_with_decisions.json
    - tests/role-alignment/invalid/visual_package_missing_golden_reference.json
  builder:
    - input-contracts/BUILDER_CONTEXT_INPUT_CONTRACT.md
    - schemas/builder-context-package.schema.json
    - schemas/ce-to-builder-contract-gate-report.schema.json
    - docs/CE_TO_BUILDER_CONTRACT_GATE.md
    - docs/CE_TO_BUILDER_TRANSFORMATION_SPEC.md
    - docs/CE_BUILDER_PACKAGE_ADAPTER_CONTRACT.md
    - data/ce-builder-transformation-registry.v1.json
    - scripts/validate-ce-to-builder-contract-gate.mjs
    - scripts/normalize-ce-builder-executable-package.mjs
    - scripts/normalize-ce-reference-map.mjs
    - scripts/ce-builder-transformation-registry.mjs
    - scripts/validate-ce-builder-transformation-registry.mjs
    - scripts/validate-ce-builder-package-adapter.mjs
    - scripts/validate-package.mjs
    - scripts/validate.mjs
should_pin_and_hash:
  ce:
    - README.md
    - STATUS.md
    - AGENTS.md
  builder:
    - README.md
    - STATUS.md
    - AGENTS.md
    - package.json
do_not_pin:
  - patch-reports/*
  - old handoff summaries
  - copied specialist schemas inside Project Gate
```

## Closure notes

```yaml
project_gate_ce_to_builder_transition: not_implemented
python_transition_module_added: false
builder_to_responsive_started: false
real_elementor_validation_claimed: false
remaining_unknowns:
  - live CI must be checked on the final implementation PR
  - real Elementor evidence remains unavailable
```
