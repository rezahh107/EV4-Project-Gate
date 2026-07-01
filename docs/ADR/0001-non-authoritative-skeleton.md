# ADR-0001: Start as Non-Authoritative Skeleton

Status: Accepted

Date: 2026-07-01

## Context

Patch 1 alignment exists.

Static hardening evidence exists.

Full cross-repo CI evidence is incomplete.

Current schemas are still repo-local.

The EV4 ecosystem needs a coordination point for shared contract planning, but current evidence is not sufficient to migrate or canonicalize schemas.

## Decision

Initialize `EV4-Shared-Contracts` as a skeleton only.

Defer canonical schema migration.

Use this repo first for inventory, readiness, compatibility mapping, and future promotion planning.

This repository remains non-authoritative until explicit promotion occurs through approved ADRs, migration plans, validation evidence, and rollback guidance.

## Consequences

This decision avoids freezing drift into a premature shared schema.

It gives the ecosystem a coordination point for contract governance.

It requires later migration patches before shared contracts can become canonical.

It does not change runtime behavior of existing repos.

Existing repo-local schemas remain authoritative until explicitly promoted.

## Non-goals

- Do not migrate canonical schemas.
- Do not make this repository the source of truth.
- Do not modify existing EV4 ecosystem repositories.
- Do not create runtime dependencies from existing repositories to this repository.
- Do not resolve schema drift in this pass.

## Future Promotion Path

Future promotion requires:

1. explicit contract owner, producer, and consumer
2. stable schema and versioning policy
3. positive and negative fixtures
4. producer validation
5. consumer validation
6. cross-repo compatibility tests
7. CI evidence
8. explicit ADR
9. migration plan
10. rollback guidance
