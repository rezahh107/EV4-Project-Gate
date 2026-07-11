# EV4 Contract Inventory

This inventory is non-authoritative. It does not promote, rename, migrate, or canonicalize any specialist contract.

Allowed status values used here:

- `local-authoritative`
- `compatibility-only`
- `adapter-boundary`
- `candidate-for-shared`
- `blocked-from-promotion`
- `inventory-only`
- `project-gate-orchestration`
- `documented-not-implemented`

| Contract / Concept | Current Owner Repo | Current Status | Promotion Risk | Candidate for Shared? | Notes |
|---|---|:---:|---|---|---|
| `ev4-architect-to-ce-transition@1.0.0` | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | Medium: must remain deterministic orchestration and must not become CE authority | No | Implemented public CLI transition. Uses pinned Architect and CE contracts; verification remains synthetic-only. |
| `ev4-ce-to-builder-transition@1.0.0` | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | High: must orchestrate official CE/Builder tools without duplicating specialist logic | No | Orchestration baseline implemented; public CLI exposure is guarded/fail-closed; owner-fixture integration verified; real non-synthetic handoff remains insufficient evidence. |
| `ev4-project-gate-kernel-decision-intake@1.0.0` | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | High: Project Gate may own the intake carrier and binding policy but must not copy Kernel schemas or implement Resolver/L2 semantics | No | Carried through Stage Evidence Bundle v1. Embeds Decision Record, Resolver input and Audit Context; rejects authored derived status/counts and unsupported claims; runs the pinned Kernel API. |
| `kernel-decision-intake-result.v1` | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | High: result may report Kernel execution but must not become Kernel semantic authority or downstream proof | No | Project Gate-owned validated result envelope. Preserves Kernel diagnostics, derives counts, records exact pin/hashes/provenance, and is mandatory for Final Gate acceptance. |
| KROAD-011 semantic lock | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | High: adding toolchain or roadmap files would falsely expand semantic acceptance evidence | No | Contains exactly six Kernel-owned semantic artifacts pinned to `76a82e28543ff8f0babca11b7d7dccac96b92894`; `package.json` and `package-lock.json` are toolchain-only. |
| `ev4-architect-stage-payload@1.0.0` | `rezahh107/EV4-Architect-Repo` | `local-authoritative` | Low for producer-side identity; real fixture evidence still unavailable | No | Source payload for Architect → CE transition v1. Specialist repo remains authoritative. |
| `ev4-ce-architect-stage-intake@1.1.0` | `rezahh107/EV4-Constructability-Engineer-Repo` | `local-authoritative` | Low for intake shape; CE processing remains separate | No | Current target payload for Architect → CE transition v1. |
| `ev4-ce-architect-stage-intake@1.0.0` | `rezahh107/EV4-Constructability-Engineer-Repo` | `compatibility-only` | Low if kept historical | No | Historical compatibility path only. Current Project Gate Architect → CE implementation uses v1.1. |
| `ev4-architect-builder-feed-export@1.0.0` | `rezahh107/EV4-Architect-Repo` | `local-authoritative` | Medium: must remain CE intake / non-executable handoff unless migration evidence proves otherwise | Possible later | Architect-side handoff concept. It is not Builder-executable output by default. |
| `ev4-builder-context-package@1.0.0` | Split between `rezahh107/EV4-Architect-Repo` and `rezahh107/EV4-Builder-Assistant-Repo` | `blocked-from-promotion` | High: duplicate naming and semantic drift could freeze incompatible behavior | No, blocked | Architect-side historical wrapper and Builder-side runtime package must remain distinct. |
| `ce-builder-executable-prerequisites` | `rezahh107/EV4-Constructability-Engineer-Repo` | `adapter-boundary` | Medium: prerequisite semantics must be validated by both CE producer and Builder consumer | Possible later | CE-owned prerequisites for Builder executable handoff. |
| `EV4 Builder Executable Package` | `rezahh107/EV4-Constructability-Engineer-Repo` | `adapter-boundary` | High: promotion could imply shared canonical execution authority too early | Possible later, blocked until evidence | CE-owned executable handoff consumed by the Project Gate baseline and Builder gate. |
| Builder CE→Builder Contract Gate | `rezahh107/EV4-Builder-Assistant-Repo` | `adapter-boundary` | Medium: Project Gate may orchestrate it but not replace it | No | Builder-owned fail-closed gate for CE executable packages. |
| Builder CE→Builder adapter | `rezahh107/EV4-Builder-Assistant-Repo` | `adapter-boundary` | Medium: Project Gate may call/pin/hash it but not duplicate it | No | Converts CE Builder Executable Package into Builder Context Package after the Builder gate passes. |
| Builder action batch / layout check / completion gate / real Elementor execution evidence | `rezahh107/EV4-Builder-Assistant-Repo` | `local-authoritative` | Medium: evidence artifacts must not become responsive conclusions | No | Builder-owned evidence surfaces for future Builder→Responsive verification. |
| Builder→Responsive formal export package | `rezahh107/EV4-Builder-Assistant-Repo` | `documented-not-implemented` | High: inventing it in Project Gate would duplicate Builder authority | No | No single formal Builder-owned Responsive export schema exists yet. |
| Builder→Responsive input package | `rezahh107/EV4-Responsive-Architect` | `documented-not-implemented` | High: inventing it in Project Gate would duplicate Responsive authority | No | Responsive boundary is documented; Project Gate has a guarded orchestration baseline, while a formal Responsive-owned Builder-specific input package schema remains not implemented. |
| `ev4-responsive-output@0.3.0` | `rezahh107/EV4-Responsive-Architect` | `local-authoritative` | Medium: Project Gate may validate/pin, not own viewport semantics | No | Responsive output schema validated by Responsive checks. |
| Golden Reference contract | `rezahh107/EV4-Constructability-Engineer-Repo` / downstream consumption by Builder | `candidate-for-shared` | High: Builder must consume, not invent | Possible later | Source authority must remain explicit. |
| Build Intent Brief | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | High: Builder must not invent it | Possible later | CE carries or produces this concept for executable handoff. |
| Spatial Lexicon | `rezahh107/EV4-Constructability-Engineer-Repo` / Builder consumption | `candidate-for-shared` | Medium: version usage and consumer validation required | Possible later | Builder consumes the declared version. |
| Experience Intent | `rezahh107/EV4-Architect-Repo` with optional/advisory CE carry | `inventory-only` | Medium: could blur intent ownership | Possible later | Architect owns design-level intent. |
| Visual Parity policy | `rezahh107/EV4-Builder-Assistant-Repo` / CE visual prerequisites | `inventory-only` | Medium: must not become Builder-invented visual authority | Possible later | Requires explicit visual-reference prerequisites and negative fixtures. |
| visual tolerance policy | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: must align with Builder validation | Possible later | CE carries or produces this policy. |
| reference paradigm lock | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: needs producer/consumer compatibility tests | Possible later | No promotion is implied by Project Gate orchestration. |
| paradigm-to-structure map | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: needs versioning and fixture coverage | Possible later | CE carries or produces this mapping. |

### KROAD-011 authority note

Kernel remains authoritative for Decision Record v2, the Resolver registry/rule/implementation, and L2 Decision Correctness semantics. Project Gate owns only the intake/result envelopes, semantic lock verification, packet binding, deterministic status mapping, Final Gate requirement, and presentation-only receipt behavior. Synthetic fixtures do not prove a real handoff, Builder execution, runtime/browser validity, downstream producer integration, release readiness, or production readiness.

### Prompt 0 common-contract foundation note

Stage Bundle v1 remains the canonical single-stage evidence envelope. Producer Gate Export v1 is a Project Gate-owned run-level complement that composes Stage Bundle v1 through `final_stage_bundle`; it is not a replacement Stage Bundle and does not define Producer-specific payload schemas or exact Producer stage sequences. The common-contract lock is Project Gate-owned and requires exact file-byte equality to a pinned immutable Project Gate commit; semantic JSON equality is not sufficient. Producer adoption, Project Gate runtime integration, and downstream Producer CI enforcement are implemented at the documented immutable-SHA workflow scope, and real non-synthetic handoff evidence remains `insufficient_evidence`. Producer callers must pin the reusable workflow by immutable Project Gate commit SHA, not `@main`.
