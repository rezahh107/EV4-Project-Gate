# EV4 Contract Inventory

This inventory describes active boundaries; it does not promote specialist contracts into shared canonical authority.

| Project Gate surface | Owner | External authority consumed | Validation role |
|---|---|---|---|
| Stage Evidence Bundle v1 | Project Gate | Specialist payload schema identified in the bundle | Canonical envelope, provenance, evidence and source-stage validation |
| `ev4-architect-to-ce-transition@1.0.0` | Project Gate | Architect payload/validator; CE mapping/intake/validator | Deterministic Architect → CE projection and result validation |
| `ev4-ce-to-builder-transition@1.0.0` | Project Gate | CE package validator; Builder contract gate, adapter, schema and output validator | Deterministic CE → Builder orchestration, publication and receipt |
| `ev4-builder-to-responsive-transition@1.0.0` | Project Gate orchestration | Pinned Builder schemas/validators/boundary; Responsive Builder-input boundary/schema/validator | Exact owner lock verification and deterministic B2R result validation; production pinned-runtime execution integration remains absent |
| Final Evidence Gate | Project Gate | Responsive evidence, prior lock chain, and verified runtime evidence when applicable | Final result, insufficient-evidence, decision receipt and runtime-evidence consistency validation; observed runtime propagation remains absent where required |
| `ev4-project-gate-kernel-decision-intake@1.0.0` | Project Gate carrier/binding | Pinned `EV4-Decision-Kernel` toolchain and semantics | Intake schema, semantic lock, official Kernel execution and result binding |
| Producer Gate Export v1 | Project Gate common contract | Producer-emitted artifact and producer validator | Exact artifact identity, adoption registry, target routing and dispatch |
| Optional EV4-PCVP v1 carrier reader | Decision Kernel canonical contract; Project Gate boundary adapter | Exact read-only Decision Kernel checkout at `069a50fa243b01fa578a7c1bcb8864d9e796d34b`, official PCVP validator, bundle and source Profiles | Legacy-compatible intake; owner bundle/carrier execution; explicit Profile effect-class and Stage endpoint binding; lossless validated projection |
| Runtime handoff receipts | Project Gate | Validated transition execution and verified snapshot metadata where applicable | Source/output binding, artifact ref/hash/byte-length identity, publication identity and post-write evidence |
| `VerifiedArtifactSnapshot` | Project Gate internal runtime value | Exact bytes emitted by an observed official producer execution | Durable exact-byte retention after worktree cleanup; never a specialist schema or public serialized contract |
| Pinned viewport execution helpers | Project Gate internal runtime implementation | Exact owner repository, commit, official tool path and execution result | Detached execution, one-read artifact capture, exact binding, cleanup revocation and snapshot creation primitives |
| Capability status v1 | Project Gate | None | Single machine-readable capability truth |

## Runtime contract boundary

The following distinction is mandatory:

```text
implemented runtime primitives
≠ production B2R runtime integration
≠ available Builder emitter
```

Implemented internal primitives include `execute_pinned_viewport_capture`, exact runtime binding, `VerifiedArtifactSnapshot`, metadata-only receipt derivation, exact-byte staging and grouped rollback.

The production `transition_builder_to_responsive` path does not currently invoke the pinned runtime execution helper or pass an observed `runtime_run` and exact expected runtime tool through viewport evidence resolution. Applicable Final Gate resolution also does not yet consume the verified snapshot and receipt.

The pinned Builder owner separately lacks the official viewport capture/export emitter and associated contract. An emitter alone does not complete the handoff; Project Gate production integration and Final Gate propagation remain required.

Active lock files under `contracts/locks/` pin exact repositories, commits, paths and relevant file identities. The current B2R lock does not include an official Builder viewport emitter because no such emitter exists at the pinned Builder commit. Historical and immutable owner contracts are unchanged by this documentation repair.

`contracts/locks/pcvp-v1.lock.json` pins the executable PCVP authority surface: official validator, manifest, checksum inventory, four Schemas, four source Profiles and locked Node package manifests. Project Gate executes that owner validator from the exact read-only checkout and retains only local integration predicates. It does not retain an executable or Schema mirror. Producer emission, specialist-output propagation, adoption and strict activation remain disabled.

The reusable external verifier remains `.github/workflows/verify-vendored-common-contract.yml` and must retain its public `workflow_call` contract.

`VerifiedArtifactSnapshot` is intentionally internal. Raw bytes are excluded from receipts, logs, diagnostics, UI/service payloads and repr output. Public receipt identity uses only canonical artifact ref, SHA-256 and byte length.

Current status remains:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
applicable_final_gate_runtime_integration: not_implemented
real_non_synthetic_handoff: insufficient_evidence
```

Historical prompt plans, merge ledgers, CI source archives and manual behavioral-coverage declarations are not active contracts. Nothing in this inventory proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.
