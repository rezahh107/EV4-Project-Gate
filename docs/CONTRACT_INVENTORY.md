# EV4 Contract Inventory

This inventory is non-authoritative. It does not promote, rename, migrate, or canonicalize any contract.

Allowed status values used here:

- `local-authoritative`
- `compatibility-only`
- `adapter-boundary`
- `candidate-for-shared`
- `blocked-from-promotion`
- `inventory-only`
- `project-gate-orchestration`

| Contract / Concept | Current Owner Repo | Current Status | Promotion Risk | Candidate for Shared? | Notes |
|---|---|:---:|---|---|---|
| `ev4-architect-to-ce-transition@1.0.0` | `rezahh107/EV4-Project-Gate` | `project-gate-orchestration` | Medium: must remain deterministic orchestration and must not become CE authority | No | First real Project Gate transition. Uses pinned Architect and CE contracts and synthetic validation only. |
| `ev4-architect-stage-payload@1.0.0` | `rezahh107/EV4-Architect-Repo` | `local-authoritative` | Low for producer-side identity; real fixture evidence still unavailable | No | Source payload for Architect → CE transition v1. Specialist repo remains authoritative. |
| `ev4-ce-architect-stage-intake@1.0.0` | `rezahh107/EV4-Constructability-Engineer-Repo` | `local-authoritative` | Low for intake shape; CE processing remains separate | No | Target payload for Architect → CE transition v1. Specialist repo remains authoritative. |
| `ev4-architect-builder-feed-export@1.0.0` | `rezahh107/EV4-Architect-Repo` | `local-authoritative` | Medium: must remain CE intake / non-executable handoff unless migration evidence proves otherwise | Possible later | Architect-side handoff concept. It must not be treated as Builder-executable output by default. |
| `ev4-builder-context-package@1.0.0` | Split between `rezahh107/EV4-Architect-Repo` and `rezahh107/EV4-Builder-Assistant-Repo` | `blocked-from-promotion` | High: duplicate naming and semantic drift could freeze incompatible behavior | No, blocked | Current split: Architect-side historical compatibility/deprecated wrapper; Builder-side runtime intake package. Not safe for canonical promotion until validation evidence and naming strategy are finalized. |
| `ce-builder-executable-prerequisites` | `rezahh107/EV4-Constructability-Engineer-Repo` | `adapter-boundary` | Medium: prerequisite semantics must be validated by both CE producer and Builder consumer | Possible later | Represents CE-owned prerequisites for Builder executable handoff. |
| `EV4 Builder Executable Package` | `rezahh107/EV4-Constructability-Engineer-Repo` | `adapter-boundary` | High: promotion could imply shared canonical execution authority too early | Possible later, blocked until evidence | Current CE → Builder adapter-side executable handoff. Not yet a shared canonical contract. |
| `ev4-responsive-reference-family@1.0.0` | `rezahh107/EV4-Responsive-Architect` | `local-authoritative` | Medium: requires viewport scope, evidence gates, and family linkage proof | Possible later | Responsive reference-family linkage remains local-authoritative inside Responsive repo. |
| Golden Reference contract | `rezahh107/EV4-Constructability-Engineer-Repo` / downstream consumption by Builder | `candidate-for-shared` | High: Builder must consume, not invent; source authority must be explicit | Possible later | Must preserve CE/Responsive ownership boundaries and avoid Builder-side invention. |
| Build Intent Brief | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | High: Builder must not invent it; producer evidence required | Possible later | CE carries or produces this concept for executable handoff. |
| Spatial Lexicon | `rezahh107/EV4-Constructability-Engineer-Repo` / Builder consumption | `candidate-for-shared` | Medium: version usage and consumer validation required | Possible later | Builder consumes `spatial_lexicon_version_used`; shared migration requires versioning policy. |
| Experience Intent | `rezahh107/EV4-Architect-Repo` with optional/advisory CE carry | `inventory-only` | Medium: could blur Architect vs CE vs Builder intent ownership | Possible later | Architect owns design-level `experience_intent`; CE may carry optional/advisory `experience_intent`. |
| Visual Parity policy | `rezahh107/EV4-Builder-Assistant-Repo` / CE visual prerequisites | `inventory-only` | Medium: must not become Builder-invented visual authority | Possible later | Requires explicit visual-reference prerequisites and negative fixtures. |
| visual tolerance policy | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: must align with Builder adapter validation | Possible later | CE carries or produces `visual_tolerance_policy`. |
| reference paradigm lock | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: needs producer/consumer compatibility tests | Possible later | CE carries or produces `reference_paradigm_lock`. |
| paradigm-to-structure map | `rezahh107/EV4-Constructability-Engineer-Repo` | `candidate-for-shared` | Medium: needs versioning and fixture coverage | Possible later | CE carries or produces `paradigm_to_structure_map`. |
