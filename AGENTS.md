# AGENTS.md

## Scope

These instructions apply to the entire repository unless a nested `AGENTS.md` or `AGENTS.override.md` is more specific.

## Repository role

`EV4-Project-Gate` is the deterministic cross-repository validation and handoff orchestrator for:

- `EV4-Architect-Repo`
- `EV4-Constructability-Engineer-Repo`
- `EV4-Builder-Assistant-Repo`
- `EV4-Responsive-Architect`
- `EV4-Decision-Kernel` where Final Gate decision intake requires it

Specialist repositories remain authoritative for their own schemas, validators, adapters, fixtures, and domain decisions. Project Gate may pin, execute, and verify those authorities; it must not duplicate or replace them.

## Read first

1. `AGENTS.md`
2. `src/ev4_transition/data/capability-status.v1.json`
3. `README.md`
4. `docs/VALIDATION_STRATEGY.md`
5. the relevant active contract or lock under `contracts/`
6. the relevant source and executable tests
7. exact owner-repository contracts and official validators for cross-repository changes

`src/ev4_transition/data/capability-status.v1.json` is the only machine-readable capability authority. Human-readable documents may summarize it but must not maintain a competing status registry.

## Runtime transaction

The personal operator flow is intentionally small:

```text
select input
→ one authoritative action
→ Preflight the same request
→ execute the same request
→ publish the result
```

Preserve these invariants:

- preview is non-authorizing;
- backend Preflight rerun is mandatory;
- request fingerprint and immutable source snapshot are bound;
- source drift and fingerprint mismatch are rejected;
- warnings and blocked states do not authorize dispatch;
- the same prepared operation cannot dispatch twice;
- publication is atomic, collision-safe, and no-overwrite;
- runtime handoff receipts remain active evidence.

Do not restore persistent UI authorization tokens, mandatory preview, CI receipts, or historical merge bookkeeping to the operator flow.

## Cross-repository boundaries

Every active boundary remains fail-closed:

```text
immutable source snapshot
→ canonical parsing
→ schema validation
→ semantic validation
→ relevant repository identity
→ pinned owner contract verification
→ official owner validator
→ deterministic transition
→ output schema validation
→ safe publication
→ runtime handoff receipt
```

Do not:

- copy specialist schemas or logic as competing authority;
- invent missing evidence, values, decisions, or lineage;
- silently normalize undocumented drift;
- replace official owner validators with local approximations;
- weaken contract locks, source identity, or post-write verification;
- claim real non-synthetic readiness from synthetic fixtures.

When evidence is insufficient, return an explicit `insufficient_evidence` result.

## Deterministic implementation rules

- Use stable ordering and canonical UTF-8 JSON.
- Use SHA-256 for relevant source and contract identity.
- Reject NaN and infinities.
- Do not inject live timestamps into deterministic core logic.
- Keep diagnostics deterministic in code, order, and path.
- Validate every emitted result against its schema.
- Add positive, negative, insufficient-evidence, and regression fixtures for implemented behavior.
- Preserve public contracts unless a breaking change is explicitly approved.

## Validation

Repository-change validation is defined by `.github/workflows/validate.yml` and `docs/VALIDATION_STRATEGY.md`.

The full internal test suite, wheel build, clean install, packaged UI construction, CLI smokes, and capability validation run once per tested Head. External owner-boundary checks are selected by `scripts/classify-validation-scope.py`; shared, unknown, Workflow, dependency, schema-infrastructure, and contract-infrastructure changes fail safe to all boundaries.

Node is not a global project skeleton. It is used only where an actual owner boundary requires Node, currently the pinned Decision Kernel bridge/toolchain.

## Pull requests

A PR must report:

- exact base and Head identity;
- affected boundaries;
- tests and checks actually executed;
- contract/versioning impact;
- remaining evidence limits;
- whether merge, approval, deployment, settings changes, or additional PRs occurred.

Do not claim validation or CI success without exact-head evidence. Do not merge unless explicitly authorized.

## Temporary Shared UX/UI Policy Adapter

Use `policies/EV4_TEMP_CROSS_REPO_UX_UI_STANDARDS_POLICY_r002.md` only as a supplemental verifier reference below repository and owner-contract authority.

```yaml
policy_id: EV4-TEMP-CROSS-REPO-UX-UI-STANDARDS-POLICY-r002
revision: r002
filename: EV4_TEMP_CROSS_REPO_UX_UI_STANDARDS_POLICY_r002.md
sha256: f09b6978e10833c1ab3c3e35a9128db894684c5ed9cd876fa87699016b6def95
repository_role: project_gate
local_consumption_scope: policy identity, Rule references, allowed evaluation states, required reasons, owners, test obligations, and evidence-boundary claims carried by active owner contracts
role_must:
  - verify policy identity and revision
  - validate referenced Rule IDs and allowed states
  - require reasons, owners and test obligations where applicable
  - reject unsupported conformance and evidence-boundary claims
role_must_not:
  - select visual design
  - replace Architect, CE, Builder or Responsive judgment
  - treat Schema validity as proof of product quality
  - promote architecture evidence into runtime evidence
```

Keep nonmaterial routing internal. Represent material identity failures, unsupported claims, missing owners, and missing test obligations through existing Project Gate diagnostics or a concise visible status when authorization or owner action is affected. Do not create a competing Rule registry, local design validator, transition, capability claim, or hidden-storage mechanism.

`r001` remains an immutable historical revision. A filename, ID, revision, byte, or digest mismatch is `TEMP_UX_UI_POLICY_IDENTITY_MISMATCH`. This adapter does not create Kernel adoption or a parallel approval path.
