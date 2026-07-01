# EV4 Shared Contract Promotion Rules

A repo-local contract may become a shared canonical contract only through explicit promotion.

## Promotion Checklist

A contract may be promoted only when:

- [ ] owner repo is explicit
- [ ] producer is explicit
- [ ] consumer is explicit
- [ ] schema is stable
- [ ] versioning is clear
- [ ] positive fixtures exist
- [ ] negative fixtures exist
- [ ] producer validation passes
- [ ] consumer validation passes
- [ ] cross-repo compatibility test exists
- [ ] deprecation/migration plan exists
- [ ] CI evidence exists

## Mandatory Governance

Promotion requires an explicit ADR.

Promotion requires a migration plan.

Promotion requires rollback guidance.

## Promotion Constraints

Promotion must not:

- freeze known drift
- rename public contracts without a migration path
- create runtime dependencies before approval
- bypass producer/consumer validation
- treat compatibility wrappers as canonical contracts without explicit deprecation strategy

## Rollback Requirement

Every promotion ADR must state how downstream repositories can revert to repo-local authority if the shared contract causes breakage or blocks active work.
