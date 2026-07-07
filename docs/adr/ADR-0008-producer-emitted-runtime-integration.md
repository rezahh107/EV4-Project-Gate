# ADR-0008: Producer-emitted runtime integration

Status: Proposed for human review

## Context

Prompt 5 adds an explicit Project Gate runtime path for Producer-emitted Gate Export artifacts after the repaired Join Evidence Packet allowed implementation. The legacy pinned-owner-file computation path remains available and is not an automatic fallback target.

## Decision

Project Gate records a versioned adoption registry at `contracts/producer-adoption/ev4-producer-adoption-set.v1.json` and a target registry at `contracts/transition-targets/ev4-transition-targets.v1.json`. The runtime accepts Producer-emitted artifacts only when `acquisition_mode.mode` is explicitly `producer_emitted_gate_artifact` and `silent_fallback_allowed` is false.

The shared intake validates the Project Gate common envelope, stage/repository/merged-commit pin, and exact handoff target before routing to transition IDs. It preserves the Producer artifact read-only and reports deterministic diagnostics. It does not implement Producer domain semantics, fabricate downstream outputs, or claim real non-synthetic E2E readiness.

## Consequences

- Legacy CLI and local-checkout transition behavior remain unchanged by default.
- Producer-emitted mode is explicit in CLI and UI.
- Unknown targets, evidence mixing, silent fallback, PR-head runtime pins, and registry drift fail closed.
- Real cross-repository E2E remains `insufficient_evidence` until lineage-bound real artifacts exist.
