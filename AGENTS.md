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

## Temporary Shared UX/UI Policy

For cross-repository verification involving UX/UI Rule references, read and apply only the verifier portion of:

```text
policies/EV4_TEMP_CROSS_REPO_UX_UI_STANDARDS_POLICY_r001.md
```

Pinned identity:

```yaml
policy_id: EV4-TEMP-CROSS-REPO-UX-UI-STANDARDS-POLICY-r001
revision: r001
sha256: fd023d9b815b6d525539d595700a1768245ae83cca401c71fb61ba22d4f76483
git_blob_sha: b52182c54577189d1b7832199fb699ee67f7d7fb
```

Project Gate may verify policy identity, referenced Rule IDs, allowed statuses, required rationale or ownership fields, downstream test obligations, prohibited conformance claims, and repository-role boundaries only when an active owner contract actually carries those fields.

Policy presence, Markdown validity, Rule-ID recognition, or evaluation-shape validity does not activate a new transition, extend an owner Schema, prove design quality, prove semantic correctness, prove runtime behavior, or establish WCAG, ISO, usability, or production conformance. Project Gate must not select, score, reinterpret, or repair UX/UI decisions.

Do not create a competing Rule registry, local semantic validator, transition field, capability claim, or hard gate solely from this temporary policy. `HEURISTIC` and `PREFERRED_DEFAULT` rules are not automatic blocking results. This policy becomes historical only after an explicitly adopted, pinned Kernel replacement exists.
