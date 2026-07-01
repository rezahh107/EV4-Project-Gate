# EV4 Validation Strategy

This document defines future validation strategy for shared contracts. No shared schema validation is active yet.

## Local Schema Validation

When schemas are eventually promoted, each schema must have local validation commands that parse the schema, validate positive fixtures, and reject negative fixtures.

Until promotion approval, local schema validation remains inactive in this repository.

## Cross-Repo Fixture Validation

Future shared contracts must be validated against fixtures from the relevant producer and consumer repositories.

Positive fixtures must prove accepted behavior. Negative fixtures must prove boundary rejection.

## Contract Compatibility Matrix

A compatibility matrix must define, for each contract:

- owner repo
- producer
- consumer
- schema version
- allowed compatibility path
- blocked compatibility path
- deprecation behavior
- migration status

## Producer/Consumer Contract Tests

No shared contract accepted without at least one producer test and one consumer test.

Producer tests must prove the owning repo can emit or carry the contract correctly.
Consumer tests must prove the downstream repo accepts valid input and rejects invalid or premature input.

## CI Requirement

CI evidence is required before schema promotion.

At minimum, CI must prove:

- `package.json` scripts run successfully
- schema files parse
- positive fixtures pass
- negative fixtures fail as expected
- producer validation passes
- consumer validation passes
- cross-repo compatibility tests pass

## Dependency Boundary

No runtime dependency from existing repos until promotion is approved.

Existing EV4 repositories must not import from this repository until an explicit ADR, migration plan, validation evidence, compatibility policy, and rollback guidance are approved.
