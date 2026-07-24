# EV4 Contract Inventory

This inventory describes active boundaries; it does not promote specialist contracts into shared canonical authority.

| Project Gate surface | Owner | External authority consumed | Validation role |
|---|---|---|---|
| Stage Evidence Bundle v1 | Project Gate | Specialist payload schema identified in the bundle | Canonical envelope, provenance, evidence and source-stage validation |
| `ev4-architect-to-ce-transition@1.0.0` | Project Gate | Architect payload/validator; CE mapping/intake/validator | Deterministic Architect → CE projection and result validation |
| `ev4-ce-to-builder-transition@1.0.0` | Project Gate | CE package validator; Builder contract gate, adapter, schema and output validator | Deterministic CE → Builder orchestration, publication and receipt |
| `ev4-builder-to-responsive-transition@1.0.0` | Project Gate orchestration | Pinned Builder schemas/validators/boundary; Responsive Builder-input boundary/schema/validator | Exact owner lock verification, pinned-worktree runtime binding, deterministic transition and result validation |
| Final Evidence Gate | Project Gate | Responsive evidence, prior lock chain, and verified runtime evidence when applicable | Final result, insufficient-evidence, snapshot/receipt identity and decision receipt validation |
| `ev4-project-gate-kernel-decision-intake@1.0.0` | Project Gate carrier/binding | Pinned `EV4-Decision-Kernel` toolchain and semantics | Intake schema, semantic lock, official Kernel execution and result binding |
| Producer Gate Export v1 | Project Gate common contract | Producer-emitted artifact and producer validator | Exact artifact identity, adoption registry, target routing and dispatch |
| Runtime handoff receipts | Project Gate | Validated transition execution and verified snapshot metadata where applicable | Source/output binding, artifact ref/hash/byte-length identity, publication identity and post-write evidence |
| `VerifiedArtifactSnapshot` | Project Gate internal runtime value | Exact bytes emitted by an observed official producer execution | Durable exact-byte retention after worktree cleanup; never a specialist schema or public serialized contract |
| Capability status v1 | Project Gate | None | Single machine-readable capability truth |

Active lock files under `contracts/locks/` pin exact repositories, commits, paths and relevant file-byte SHA-256 values. The reusable external verifier remains `.github/workflows/verify-vendored-common-contract.yml` and must retain its public `workflow_call` contract.

`VerifiedArtifactSnapshot` is intentionally internal. Raw bytes are excluded from receipts, logs, diagnostics, UI/service payloads and repr output. Public receipt identity uses only canonical artifact ref, SHA-256 and byte length.

Historical prompt plans, merge ledgers, CI source archives and manual behavioral-coverage declarations are not active contracts.
