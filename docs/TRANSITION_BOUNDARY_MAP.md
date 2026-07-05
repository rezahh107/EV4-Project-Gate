# Transition Boundary Map

Status: active architecture map  
Authority: `docs/ARCHITECTURE.md`, `docs/CONTRACT_INVENTORY.md`, and `src/ev4_transition/data/capability-status.v1.json`

## Purpose

This document records which EV4 role-to-role transitions are currently implemented, which are represented only as contracts or freeze baselines, and which evidence boundaries must remain explicit.

## Current Transition State

| Transition | Project Gate state | Public CLI | Verification state | Notes |
|---|---|---|---|---|
| Architect → Constructability Engineer | orchestration baseline implemented | implemented | synthetic fixture only | Produces a CE v1.1 bundle through the official CE mapper and validator boundary. Real non-synthetic handoff remains insufficient evidence. |
| Constructability Engineer → Builder | orchestration baseline implemented | not implemented | pinned owner fixture integration verified | Project Gate validates the CE/Builder lock, invokes owner validators through the runner boundary, and produces a transition result. It is not exposed as a general public CLI transition. Real non-synthetic handoff remains insufficient evidence. |
| Builder → Responsive Architect | not implemented | not implemented | not applicable | No Project Gate orchestration baseline is active. |
| Responsive Architect → Final Evidence Gate | not implemented | not implemented | not applicable | No final evidence gate orchestration is active. |

## Boundary Rules

### Project Gate owns

- transition envelope and result validation;
- deterministic ordering and canonical hashing;
- lock-manifest verification;
- official owner-tool execution through the runner boundary;
- fail-closed diagnostics;
- transition status projection;
- preservation of evidence and provenance references.

### Project Gate does not own

- specialist canonical schemas;
- specialist domain inference;
- Builder runtime execution;
- Responsive correctness analysis;
- final production-readiness claims;
- repair or normalization of invalid specialist evidence.

## CE → Builder State

```yaml
transition_id: ev4-ce-to-builder-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: not_implemented
owner_fixture_integration: verified
real_non_synthetic_handoff: insufficient_evidence
source_repository: rezahh107/EV4-Constructability-Engineer-Repo
source_commit: cfceec5c20269c75a1cc19b2675d7087cede4599
consumer_repository: rezahh107/EV4-Builder-Assistant-Repo
consumer_commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
result_schema: schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
lock_manifest: contracts/locks/ce-to-builder-transition.v1.lock.json
```

## Evidence Interpretation

A green Project Gate CI run proves only that the checked transition implementation, fixtures, locks, and owner-tool integrations passed for the exact tested head.

It does not prove:

- a real non-synthetic Architect → CE handoff;
- a real non-synthetic CE → Builder handoff;
- Builder execution correctness;
- Responsive correctness;
- production readiness.

## Historical Records

Historical merge records are retained in `docs/EV4_SHARED_CONTRACTS_STATUS.md`. That file is a merge ledger and is not the active capability authority.
