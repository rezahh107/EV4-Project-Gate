# Contract Inventory — Prompt 0 Addendum

| Contract | Owner | Status | Compatibility |
|---|---|---|---|
| `stage-evidence-bundle.v1` | `rezahh107/EV4-Project-Gate` | canonical single-stage contract | unchanged |
| `producer-gate-export.v1` | `rezahh107/EV4-Project-Gate` | run-level common contract | strictly references Stage Bundle v1 |
| `project-gate-common-contract-lock.v1` | `rezahh107/EV4-Project-Gate` | vendoring lock | immutable commit and exact-byte verification |

Producer-specific payload schemas and exact stage sequences remain Producer-owned. Producer adoption and Project Gate runtime routing are not implemented in Prompt 0.
