# PG-A2C Operator Workflow

## Purpose

This workflow accepts the exact Architect-owned `architect-project-gate.json`, executes the Project Gate-owned `architect-to-ce` transition, runs the official Architect and CE validators, and publishes two separate files:

- `ce-input.json`: the standalone CE-owned intake artifact (`ev4-ce-architect-stage-intake@1.1.0`)
- `project-gate-a2c-receipt.json`: Project Gate execution, validation, pin, diagnostic, and publication evidence

The operator does not extract nested JSON, inspect `result.output`, or rebuild an envelope.

When the Architect export contains the active optional PCVP `continuation_assurance`, Project Gate also requires the exact Decision Kernel policy checkout. Project Gate validates the carrier against the immutable policy authority, validates the separately pinned staged activation authority, and copies the already-validated carrier losslessly to the canonical CE intake field. PCVP never creates or upgrades ordinary handoff/publication authority.

## Required immutable checkouts

Prepare local checkouts at these exact accepted revisions:

```text
rezahh107/EV4-Architect-Repo@bd7cb512f9b61222cee2512fbfc53a2bb01a1175
rezahh107/EV4-Constructability-Engineer-Repo@bc4a901d82fcdbdb131e30058b399508262706c5
rezahh107/EV4-Decision-Kernel@069a50fa243b01fa578a7c1bcb8864d9e796d34b
```

The Decision Kernel checkout above is the immutable PCVP policy/Schema/Profile authority. The separately pinned staged activation authority is `ad0e7235929d7f6d847724f6b4d1a6a3c57453db`; Project Gate verifies and materializes that exact commit from the Decision Kernel Git object database without moving or modifying the policy checkout.

Project Gate verifies each checkout's GitHub repository identity and exact Git `HEAD`. A moving branch name cannot substitute for an accepted commit.

## Primary command

Run from the Project Gate repository root:

```bash
ev4-transition transition architect-to-ce architect-project-gate.json \
  --acquisition-mode producer_emitted_gate_artifact \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --kernel-repo ../EV4-Decision-Kernel \
  --output ce-input.json \
  --receipt-output project-gate-a2c-receipt.json \
  --format json
```

Defaults are `ce-input.json` and `project-gate-a2c-receipt.json`; explicit paths are recommended for automation. `--kernel-repo` is required when `continuation_assurance` is present. Carrier absence preserves the dependency-free legacy A2C path.

## Accepted behavior

An accepted run requires all of the following:

- strict JSON and Producer Gate Export validation;
- current Architect adoption pin match;
- exact Architect and CE checkout identity;
- valid Architect Stage Evidence Bundle extraction;
- official Architect semantic validation;
- for a present PCVP carrier, exact owner-backed carrier validation and canonical first-edge activation validation;
- lossless PCVP carrier attachment at CE `$.continuation_assurance` before CE owner validation;
- existing deterministic Project Gate A2C mapping;
- official CE intake and source-binding validation;
- canonical, atomic, post-write-verified publication.

The command exits `0`, writes both files, and reports `handoff_allowed: true` only when the pre-existing ordinary A2C handoff/publication predicates already authorize publication. A valid PCVP carrier cannot change `handoff_allowed: false` to `true`.

## Blocked and insufficient-evidence behavior

A valid synthetic or blocked source may produce a structurally valid CE input only when the active contracts permit it. The receipt remains explicit that the transition is not accepted and reports `handoff_allowed: false`.

Missing exact owner checkouts, unavailable owner validators, unavailable staged activation authority, or unprovable immutable identity produce `insufficient_evidence` and exit `2` where the failure is evidentiary rather than a semantic rejection.

## Invalid behavior

Malformed, tampered, stale-pin, wrong-target, mixed-source, silent-fallback, unsafe-path, overwrite, failed-publication, invalid-PCVP-carrier, or activation-mismatch inputs produce `invalid` and exit `1`. An accepted CE handoff is not reported.

`repair_needed` also exits `1`. `accepted` exits `0`.

## Publication and overwrite policy

- The source export is read-only and captured from stable bytes.
- Source, CE input, and receipt paths must be distinct.
- Parent traversal, output outside the current workspace, directory targets, and symlink targets are rejected.
- Existing output files are never overwritten.
- CE input is staged and published before the receipt.
- The receipt is published only after the CE input bytes are re-read and verified.
- If receipt publication fails after CE input publication, the command reports the surviving CE artifact truthfully and does not claim success.

Remove or archive prior outputs intentionally before rerunning. There is no implicit overwrite option.

## Acquisition-mode separation

`producer_emitted_gate_artifact` and `pinned_owner_file_computation` are explicit, separate paths. Project Gate does not silently fall back, combine evidence, or recover semantic fields from human-readable reports.

## Evidence limitations

Current-head CI uses Architect-generated synthetic evidence and classifies it as `cross_repository_integration`, not `real_run`. It does not prove a non-synthetic production handoff, CE constructability completion, Builder readiness, downstream PCVP activation, full PCVP rollout, or the full Golden Path.

## Next manual step

Submit the standalone `ce-input.json` to the Constructability Engineer workflow. The Project Gate receipt is retained separately for audit and diagnosis; it is not CE semantic input.
