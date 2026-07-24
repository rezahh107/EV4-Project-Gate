# EV4 Role Boundary Map

## Authority rule

Specialist repositories remain authoritative for their own schemas, validators, adapters, fixtures, and domain behavior. Project Gate owns deterministic orchestration, result envelopes, diagnostics, contract locks, publication safety, and runtime handoff receipts. It must not copy or approximate specialist authority.

| Boundary | Producer authority | Consumer authority | Project Gate responsibility | Fail-closed condition |
|---|---|---|---|---|
| Architect → CE | `rezahh107/EV4-Architect-Repo` payload and official validator | `rezahh107/EV4-Constructability-Engineer-Repo` intake, mapping, validator | Pin exact owner bytes, validate source, execute deterministic projection, validate CE output | Missing owner checkout, pin mismatch, invalid source/output, insufficient evidence |
| CE → Builder | CE executable package and validator | `rezahh107/EV4-Builder-Assistant-Repo` contract gate, adapter, output validator | Verify lock/source binding, execute owner tools, publish standalone Builder input and receipt | Missing lineage/evidence, lock drift, partial publication failure, collision |
| Builder → Responsive | Builder-owned evidence and official viewport emitter/contract at an exact pinned Builder commit | `rezahh107/EV4-Responsive-Architect` schema-bound intake and official validators | Maintain pinned-runtime verification/publication primitives; wire production B2R to execute the official tool, propagate the observed runtime result, consume the verified snapshot/receipt, and execute Responsive validators | Missing Builder emitter, missing production wiring, absent observed runtime result/tool, cleanup failure, binding mismatch, snapshot inconsistency, contract drift, validator failure, insufficient evidence |
| Final Gate | Prior Project Gate lock chain, Responsive evidence, and verified runtime evidence when required | Final Gate result/receipt contracts; Decision Kernel when required | Validate prior chain, Responsive evidence, and the observed B2R runtime result/snapshot/receipt when applicable | Invalid/insufficient evidence, lock mismatch, absent runtime propagation, invalid receipt or Kernel result |
| Producer integration | Producer adoption records and emitted artifacts | Project Gate producer intake/dispatch facade | Verify exact producer artifact identity, validator existence, routing and dispatch | Unknown producer, artifact hash drift, invalid target, unsupported transition |

## Runtime ownership split

```text
implemented Project Gate runtime primitives
≠ production B2R runtime integration
≠ Builder-owned official emitter
```

### Project Gate primitives already owned and implemented

- detached pinned execution worktree;
- exact repository, commit, tool, working-directory, output-ref and output-hash binding;
- one-read emitted-artifact handling;
- immutable `VerifiedArtifactSnapshot`;
- metadata-only runtime receipt derivation;
- cleanup-failure revocation;
- exact-byte staging, post-write verification and grouped rollback.

### Project Gate integration still owned but not implemented

- invoke `execute_pinned_viewport_capture` from the production B2R flow;
- pass the exact observed runtime result and exact expected tool through evidence resolution;
- consume and publish the verified snapshot and receipt;
- propagate and verify applicable runtime evidence in Final Gate.

### Builder owner work still required

- implement the official viewport capture/export emitter;
- define its contract and exact tool path;
- provide a commit suitable for pinning.

The Builder owner is not the sole remaining implementation owner. Adding the emitter alone does not complete the root operational handoff.

## Runtime invariants

- one authoritative operator action;
- backend Preflight rerun on the same request;
- immutable source snapshot and request-bound fingerprint;
- warning/blocked non-authorization;
- duplicate-dispatch rejection;
- deterministic diagnostics and canonical JSON;
- detached execution worktree at the exact pinned owner commit when official runtime execution is invoked;
- one read of the official emitted artifact on the operational path;
- exact repository, commit, tool, working-directory, output-reference, output-hash, subject, viewport and process binding;
- immutable `VerifiedArtifactSnapshot` only after all positive predicates pass;
- no deleted temporary path returned as durable state;
- exact-byte staging and post-write byte/hash/length verification;
- cleanup failure revokes snapshot and receipt;
- file-only viewport evidence never substitutes for observed execution;
- the production B2R route must provide the observed `runtime_run` and exact expected runtime tool to evidence resolution;
- applicable Final Gate verification must consume the propagated observed runtime result, snapshot and receipt;
- atomic no-overwrite publication;
- runtime handoff receipt preservation without raw artifact bytes.

Current machine-readable capability truth is `src/ev4_transition/data/capability-status.v1.json`. Human-readable status remains:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
applicable_final_gate_runtime_integration: not_implemented
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
```

No role or invariant in this document proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.
