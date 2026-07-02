# EV4 Cross-Repo Compatibility Gate

The repository name is retained for continuity. Its active role has changed.

## Role

```yaml
role: non_authoritative_cross_repo_compatibility_gate
canonical_schema_owner: false
runtime_dependency: false
repair_authority: false
python_status: not_implemented
```

The four EV4 repositories remain authoritative for their own schemas, validators, adapters, fixtures, and runtime behavior:

```text
rezahh107/EV4-Architect-Repo
rezahh107/EV4-Constructability-Engineer-Repo
rezahh107/EV4-Builder-Assistant-Repo
rezahh107/EV4-Responsive-Architect
```

This repository will host deterministic compatibility verification across those repositories. It detects and reports incompatibilities. Repairs are performed later in the owning repositories after review.

## Verification Model

A schema diff is useful but insufficient. Compatibility must be evaluated through the real path:

```text
Producer schema and validator
            ↓
      validated fixture
            ↓
 documented adapter/normalizer
            ↓
Consumer schema and validator
            ↓
preservation and semantic rules
            ↓
deterministic compatibility report
```

The verifier should answer:

```text
Can a supported Producer-valid output pass through the documented Adapter,
be accepted by the Consumer,
and preserve required identity, authority, and meaning?
```

## Main Conclusions

### 1. Structural difference is not automatically a defect

CE emits a rich object-shaped `paradigm_to_structure_map`. Builder has an explicit adapter that converts it to Builder runtime carriers. The representation difference is intentional for the supported path.

### 2. Adapter existence does not prove full compatibility

The current Builder reference adapter requires explicit left/right evidence and produces a `left-center-right` model. CE also permits paradigms such as `grid`, `vertical-list`, `split-hero`, `radial-diagram`, and `unknown`.

```yaml
finding: producer_domain_adapter_gap
status: confirmed_contract_incompatibility
repair_owner: unresolved
```

### 3. Information preservation must be verified

The CE-to-Builder executable-package normalizer requires these visual-reference artifacts on input:

```text
golden_reference_contract
build_intent_brief
spatial_lexicon_version_used
visual_tolerance_policy
```

They are not preserved in the current normalized Builder package.

```yaml
finding: required_visual_artifacts_not_preserved
status: confirmed_contract_inconsistency
repair_strategy: unresolved
```

The correct representation may be embedded data or an immutable sidecar reference. That choice is an architecture decision, not a detector decision.

## Python Verifier Scope

The first implementation should provide:

1. versioned compatibility manifests;
2. Producer schema and validator execution;
3. documented Adapter execution;
4. Consumer schema and validator execution;
5. field-lineage and preservation checks;
6. versioned semantic rules;
7. canonical JSON reports with pinned repository refs and SHA-256 evidence.

Initial diagnostic targets:

```text
producer_variant_not_supported_by_adapter
required_field_lost
```

Later phases may add boundary generation, property-based tests, mutation testing, and issue fingerprinting.

## Evidence Policy

Use explicit states:

```text
observed
validated
resolved
derived
proposed
unverified
insufficient_evidence
```

A shape check is not full Producer validation. Runtime or CI success requires retained execution evidence. Synthetic fixtures must be identified as synthetic.

## Boundaries

This repository is:

- a compatibility test harness;
- a host for deterministic Python rules and reports;
- an independent evidence surface.

This repository is not:

- a canonical schema source;
- a fifth architectural authority;
- an automatic repair system;
- a runtime dependency of the EV4 repositories.

## Transition Status

The role transition is documented in `README.md` and `AGENTS.md`. Older governance and promotion documents describe the previous skeleton role and are historical context when they conflict with these two files.

No Python verifier is implemented yet.

## Next Step

```text
CE valid fixture
→ CE schema and validator
→ Builder adapter
→ Builder schema and validator
→ preservation and semantic checks
→ canonical JSON report
```
