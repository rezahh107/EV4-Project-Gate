# Project Gate common contracts

This directory contains Project Gate-owned cross-repository contracts that complement the canonical single-stage Stage Evidence Bundle.

- `producer-gate-export.v1.schema.json`: run-level Producer export that strictly references Stage Evidence Bundle v1.
- `common-contract-lock.v1.schema.json`: immutable exact-byte vendoring lock.

These contracts do not own Producer-specific payload schemas or stage sequences. Producer adoption remains pending until exact merged bytes are vendored and enforced in Producer CI.

### Prompt 0 common-contract foundation note

Stage Bundle v1 remains the canonical single-stage evidence envelope. Producer Gate Export v1 is a Project Gate-owned run-level complement that composes Stage Bundle v1 through `final_stage_bundle`; it is not a replacement Stage Bundle and does not define Producer-specific payload schemas or exact Producer stage sequences. The common-contract lock is Project Gate-owned and requires exact file-byte equality to a pinned immutable Project Gate commit; semantic JSON equality is not sufficient. Producer adoption, Project Gate runtime integration, and downstream Producer CI enforcement remain pending/not implemented, and real non-synthetic handoff evidence remains `insufficient_evidence`. The canonical Producer pin is pending merge for PR #39; future Producer callers must pin the reusable workflow by immutable Project Gate commit SHA, not `@main`.
