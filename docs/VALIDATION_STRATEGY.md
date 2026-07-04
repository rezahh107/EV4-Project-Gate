# EV4 Validation Strategy

This document defines validation strategy for EV4 Project Gate.

The active implementation includes the deterministic Python foundation, Stage Evidence Bundle envelope validation, and the first narrow synthetic-verified transition: `ev4-architect-to-ce-transition@1.0.0`.

## Active Foundation Validation

Current Python checks validate:

- canonical JSON v1 behavior;
- stable SHA-256 over canonical UTF-8 JSON;
- NaN and infinity rejection;
- structured diagnostics;
- malformed JSON values without crashes;
- Stage Evidence Bundle envelope structure;
- explicit `insufficient_evidence`;
- provenance preservation;
- validation-result schema enforcement;
- Architect-to-CE transition-result schema enforcement;
- minimal CLI JSON and Persian output.

Current commands:

```bash
python -m pip install -e '.[dev]'
pytest
ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
ev4-transition validate fixtures/invalid/array-input.v1.json
ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
```

Existing Node skeleton checks remain temporarily available:

```bash
npm run status
npm run validate
```

## Verification State Vocabulary

Project Gate uses this canonical value for synthetic-only transition evidence:

```yaml
verification_state: synthetic_fixture_only
```

Historical equivalents that may appear in old reports are compatibility wording only and should be normalized to `synthetic_fixture_only` in active Project Gate documents:

```yaml
legacy_equivalents:
  - verified_by_synthetic_fixture
  - synthetic_cross_repository_fixtures_only
canonical: synthetic_fixture_only
```

## Architect-to-CE Transition Validation

The first active transition is:

```text
ev4-architect-to-ce-transition@1.0.0
```

It validates:

- source Stage Evidence Bundle envelope;
- exact source stage and payload identity;
- pinned external contract file hashes;
- Architect payload schema from the Architect repository;
- deterministic Architect-to-CE mapping without semantic derivation;
- CE intake schema from the CE repository;
- target CE Stage Evidence Bundle envelope;
- Architect-to-CE transition result schema;
- official Architect validator and official CE intake validator in CLI/CI.

Required pinned local checkouts:

```text
rezahh107/EV4-Architect-Repo@b0651668b97f682bb17f66840c8e8c503fd3935d
rezahh107/EV4-Constructability-Engineer-Repo@546680a2e2a309c0d7e0ddbfc017e9e194ece7cb
```

## CE-to-Builder Transition Validation Baseline

The CE → Builder transition is documented as a freeze baseline only. It is not implemented in Project Gate yet.

When implemented later, it should validate:

- CE Stage Evidence Bundle envelope;
- CE package identity `ev4-builder-executable-package@1.0.0`;
- pinned CE producer contract, schema, validators, and proving fixtures;
- Builder CE→Builder Contract Gate;
- Builder transformation registry;
- Builder CE→Builder adapter;
- generated Builder Context Package schema validation;
- generated Builder Context Package cross-field validation;
- target Stage Evidence Bundle envelope;
- transition result schema for the future CE→Builder transition.

The current freeze matrix is:

```text
docs/CE_TO_BUILDER_FREEZE_MATRIX.md
```

## Builder-to-Responsive Transition Validation Baseline

The Builder → Responsive transition is documented as a freeze baseline only. It is not implemented in Project Gate yet.

When implemented later, it should validate:

- Builder Stage Evidence Bundle envelope or equivalent Project Gate transport envelope;
- pinned Builder action batch, layout check, completion gate, and real Elementor execution evidence contracts;
- pinned Builder validators and proving fixtures;
- explicit absence or presence of a formal Builder→Responsive export schema;
- Responsive Builder→Responsive input boundary;
- Responsive output schema validation;
- Responsive submitted-packet dry-run boundary validation;
- Responsive evidence-intake, pilot-boundary, Issue #8, RTAQ, and STATUS guard checks;
- target Stage Evidence Bundle envelope;
- transition result schema for the future Builder→Responsive transition.

The current freeze matrix is:

```text
docs/BUILDER_TO_RESPONSIVE_FREEZE_MATRIX.md
```

The transition may be implemented as fail-closed while formal Builder and Responsive handoff package schemas remain absent. It must not emit an accepted handoff result unless current pinned artifacts and official validators support that result.

## Local Schema Validation

The active schemas in this repository are Project Gate envelope/result schemas only:

```text
schemas/stage-bundle/stage-bundle.v1.schema.json
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
```

They are not copied specialist-domain schemas and are not canonical Architect, CE, Builder, or Responsive contracts.

## Cross-Repo Fixture Validation

Transition PRs validate against fixtures from the relevant producer and consumer repositories.

Positive fixtures prove accepted behavior. Negative fixtures prove boundary rejection.

For Architect-to-CE v1:

```yaml
real_cross_repository_validation: not_available
verification_state: synthetic_fixture_only
```

No real EV4 fixture validation is claimed by this transition.

## Contract Compatibility Matrix

A compatibility matrix defines, for each future transition contract:

- owner repo
- producer
- consumer
- schema version
- allowed compatibility path
- blocked compatibility path
- deprecation behavior
- migration status

## Producer/Consumer Contract Tests

No real transition is accepted without at least one producer-side fixture and one consumer-side fixture.

Producer tests prove the owning repo can emit or carry the contract correctly. Consumer tests prove the downstream repo accepts valid input and rejects invalid or premature input.

## CI Requirement

CI evidence is required before schema promotion or transition activation.

At minimum, transition CI should prove:

- Python package installs
- unit tests pass
- CLI smoke tests pass
- schema files parse
- positive fixtures pass
- negative fixtures fail as expected
- producer validation passes
- consumer validation passes
- cross-repo compatibility tests pass when that transition claims cross-repo compatibility

## Dependency Boundary

Existing EV4 repositories should not import from this repository until an explicit ADR, migration plan, validation evidence, compatibility policy, and rollback guidance are approved.
