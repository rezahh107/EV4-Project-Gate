# ADR 0002: Producer Gate Export common-contract foundation

- Status: Proposed for human review
- Date: 2026-07-06
- Scope: Prompt 0

## Context

`schemas/stage-bundle/stage-bundle.v1.schema.json` is the published canonical envelope for one stage. It already owns Producer identity, Producer payload extension, evidence, hashes, provenance, synthetic classification, complete versus insufficient-evidence state, and structured missing evidence. It does not own a complete Producer run, ordered stage manifest, or final handoff decision.

The existing transitions compute and verify pinned owner-file bytes. The four Producer repositories have not adopted a Project Gate common run-level contract.

## Decision

1. Keep `stage-evidence-bundle.v1` unchanged and authoritative for single-stage evidence.
2. Add `producer-gate-export.v1` as a thin run-level complement that strictly references Stage Bundle v1.
3. Do not duplicate Stage Bundle fields or create a competing single-stage envelope.
4. Add `project-gate-common-contract-lock.v1` for immutable exact-byte vendoring.
5. Keep the deterministic verifier local-filesystem-only; network checkout belongs to workflow orchestration.
6. Preserve dual-path coexistence:

```yaml
legacy_path:
  id: pinned_owner_file_computation
  status: preserved
new_path:
  id: producer_emitted_gate_artifact
  status_after_prompt_0: common_contract_published_pending_producer_adoption
silent_fallback:
  allowed: false
```

7. Producer-owned validators remain authoritative for exact Producer stage lists. The common validator enforces generic manifest integrity only.
8. User summaries are presentation only and cannot replace or mutate the validated machine artifact.

## Compatibility consequences

No Stage Bundle v2 is introduced. Existing locks, transition schemas, runners, fixtures, CLI paths, CI checks, and the legacy Node skeleton remain available. Producer adoption, Project Gate runtime routing, downstream enforcement, and real non-synthetic handoff evidence are not established by Prompt 0.

## Retirement gate

Legacy retirement is forbidden in this change. It requires a separate ADR and pull request, adoption by all four Producers, Producer CI rejection evidence, Project Gate runtime integration, non-synthetic cross-repository E2E evidence, and no regression in pinned transition checks.

## Release boundary

The pull-request head is not a canonical Producer pin. Producers may pin only the exact merged commit and exact contract file SHA-256 after human review and merge.
