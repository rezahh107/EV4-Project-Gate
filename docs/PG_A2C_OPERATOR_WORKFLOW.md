# PG-A2C Operator Workflow

## Purpose

This workflow accepts the exact Architect-owned `architect-project-gate.json`, executes the Project Gate-owned `architect-to-ce` transition, runs the official Architect and CE validators, and publishes two separate files:

- `ce-input.json`: the standalone CE-owned intake artifact (`ev4-ce-architect-stage-intake@1.1.0`)
- `project-gate-a2c-receipt.json`: Project Gate execution, validation, pin, diagnostic, and publication evidence

The operator does not extract nested JSON, inspect `result.output`, or rebuild an envelope.

## Required immutable checkouts

Prepare local checkouts at these exact accepted revisions:

```text
rezahh107/EV4-Architect-Repo@be9bdea9ae246b1587043f2582c1a950ea2a6ec5
rezahh107/EV4-Constructability-Engineer-Repo@6650c31304e5a0472b276c36018c1df8f42ac983
```

Project Gate verifies each checkout's GitHub repository identity and exact Git `HEAD`. A moving branch name cannot substitute for the accepted commit.

## Primary command

Run from the Project Gate repository root:

```bash
ev4-transition transition architect-to-ce architect-project-gate.json \
  --acquisition-mode producer_emitted_gate_artifact \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --output ce-input.json \
  --receipt-output project-gate-a2c-receipt.json \
  --format json
```

Defaults are `ce-input.json` and `project-gate-a2c-receipt.json`; explicit paths are recommended for automation.

## Accepted behavior

An accepted run requires all of the following:

- strict JSON and Producer Gate Export validation;
- current Architect adoption pin match;
- exact Architect and CE checkout identity;
- valid Architect Stage Evidence Bundle extraction;
- official Architect semantic validation;
- existing deterministic Project Gate A2C mapping;
- official CE intake and source-binding validation;
- canonical, atomic, post-write-verified publication.

The command exits `0`, writes both files, and reports `handoff_allowed: true`.

## Blocked and insufficient-evidence behavior

A valid synthetic or blocked source may produce a structurally valid CE input only when the active contracts permit it. The receipt remains explicit that the transition is not accepted and reports `handoff_allowed: false`.

Missing exact owner checkouts, unavailable owner validators, or unprovable immutable identity produce `insufficient_evidence` and exit `2`.

## Invalid behavior

Malformed, tampered, stale-pin, wrong-target, mixed-source, silent-fallback, unsafe-path, overwrite, or failed-publication inputs produce `invalid` and exit `1`. An accepted CE handoff is not reported.

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

Current-head CI uses Architect-generated synthetic evidence and classifies it as `cross_repository_integration`, not `real_run`. It does not prove a non-synthetic production handoff, CE constructability completion, Builder readiness, or the full Golden Path.

## Next manual step

Submit the standalone `ce-input.json` to the Constructability Engineer workflow. The Project Gate receipt is retained separately for audit and diagnosis; it is not CE semantic input.
