# PG-C2B Operator Workflow

## Purpose

`S-002 / PG-C2B` accepts the official CE-produced `ce-project-gate.json`, executes the existing Project Gate-owned CE→Builder orchestration, and publishes two independent files:

- `builder-input.json`: the Builder-owned `ev4-builder-context-package@1.0.0` input.
- `project-gate-c2b-receipt.json`: Project Gate evidence, diagnostics, identities, hashes, and publication state.

The receipt is not Builder semantic input.

## Required local checkouts

The command requires clean local Git checkouts at the exact immutable revisions adopted by Project Gate:

- `rezahh107/EV4-Constructability-Engineer-Repo` at `6650c31304e5a0472b276c36018c1df8f42ac983`
- `rezahh107/EV4-Builder-Assistant-Repo` at `b599c000118dcbe77572d6f387da5da0f46d1f91`

Project Gate verifies each checkout's `origin` and `HEAD`; moving branch names do not replace these identities.

## Primary command

```bash
ev4-transition transition ce-to-builder ce-project-gate.json \
  --acquisition-mode producer_emitted_gate_artifact \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --builder-repo ../EV4-Builder-Assistant-Repo \
  --output builder-input.json \
  --receipt-output project-gate-c2b-receipt.json \
  --format json
```

## Accepted flow

The command performs this sequence without manual JSON extraction or field copying:

1. captures immutable source bytes from `ce-project-gate.json`;
2. validates the Producer Gate Export and CE Stage Evidence Bundle;
3. verifies the adopted CE and Builder repositories and commits;
4. extracts the CE Stage Evidence Bundle;
5. runs the existing `ev4-ce-to-builder-transition@1.0.0`;
6. runs CE `validator/engine.py`;
7. runs Builder `scripts/validate-ce-to-builder-contract-gate.mjs`;
8. runs Builder `scripts/normalize-ce-builder-executable-package.mjs`;
9. runs Builder `scripts/validate-package.mjs` (`Cross-field validation`);
10. atomically publishes `builder-input.json`;
11. rereads and revalidates the exact published Builder input;
12. publishes the separate Project Gate receipt.

The operator does not inspect `result.output`, `downstream_artifact`, `builder_context_package`, or another nested transition envelope.

## Fail-closed behavior

No accepted Builder handoff is reported when any of these conditions occurs:

- malformed, duplicate-key, non-finite, tampered, replaced, or mixed-mode CE input;
- wrong producer repository, commit, stage, target, schema, payload, or bundle identity;
- `handoff.allowed` is false;
- stale CE or Builder checkout;
- owner tool, Contract Gate, adapter, or `Cross-field validation` failure;
- invalid Action Batch, package digest, source ledger, or authorization;
- required authoritative decision lineage is absent;
- unsafe, colliding, existing, symlinked, or directory output paths.

There is no silent fallback to `pinned_owner_file_computation` and no evidence mixing.

## Decision lineage

The current Builder adapter declares only the CE Builder Executable Package in `source_payload_ledger`. Therefore `decision_lineage` is not required by the active Builder input contract for this adapter output. Project Gate neither fabricates nor infers lineage. If a future Builder-owned ledger declares `Kernel_Decision_Lineage`, the required authoritative lineage must be present or the transition fails closed.

## Publication policy

- input, Builder output, and receipt paths must be distinct;
- overwrite is refused by default;
- writes are canonical UTF-8 JSON with stable key ordering;
- Builder output is published before the success receipt;
- if post-write validation or receipt publication fails, the result truthfully records partial publication;
- repeated runs require new output paths or explicit removal by the operator after review.

## Status and exit codes

| Status | Exit code | Meaning |
|---|---:|---|
| `accepted` | `0` | Builder input and receipt were published and verified. |
| `repair_needed` | `3` | The transition completed with repairable warnings and did not authorize an accepted handoff. |
| `insufficient_evidence` | `2` | Required identity, evidence, lineage, or owner-tool proof was unavailable. |
| `invalid` | `1` | Contract, semantic, tamper, path, or publication validation failed. |

## Next manual step

After an `accepted` result, provide only `builder-input.json` to the Builder workflow. Retain `project-gate-c2b-receipt.json` as Project Gate evidence; do not merge it into Builder input.
