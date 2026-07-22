# EV4 Role Boundary Map

## Authority rule

Specialist repositories remain authoritative for their own schemas, validators, adapters, fixtures, and domain behavior. Project Gate owns deterministic orchestration, result envelopes, diagnostics, contract locks, publication safety, and runtime handoff receipts. It must not copy or approximate specialist authority.

| Boundary | Producer authority | Consumer authority | Project Gate responsibility | Fail-closed condition |
|---|---|---|---|---|
| Architect → CE | `rezahh107/EV4-Architect-Repo` payload and official validator | `rezahh107/EV4-Constructability-Engineer-Repo` intake, mapping, validator | Pin exact owner bytes, validate source, execute deterministic projection, validate CE output | Missing owner checkout, pin mismatch, invalid source/output, insufficient evidence |
| CE → Builder | CE executable package and validator | `rezahh107/EV4-Builder-Assistant-Repo` contract gate, adapter, output validator | Verify lock/source binding, execute owner tools, publish standalone Builder input and receipt | Missing lineage/evidence, lock drift, partial publication failure, collision |
| Builder → Responsive | Builder output contract | `rezahh107/EV4-Responsive-Architect` input/output validators | Verify both owner pins, run official Responsive validators, emit deterministic transition result | Owner validator failure, contract drift, insufficient viewport evidence |
| Final Gate | Prior Project Gate lock chain and Responsive evidence | Final Gate result/receipt contracts; Decision Kernel when required | Validate prior chain, evidence, result schema, receipts, and Kernel intake | Invalid/insufficient evidence, lock mismatch, invalid receipt or Kernel result |
| Producer integration | Producer adoption records and emitted artifacts | Project Gate producer intake/dispatch facade | Verify exact producer artifact identity, validator existence, routing and dispatch | Unknown producer, artifact hash drift, invalid target, unsupported transition |

## Runtime invariants

- one authoritative operator action;
- backend Preflight rerun on the same request;
- immutable source snapshot and request-bound fingerprint;
- warning/blocked non-authorization;
- duplicate-dispatch rejection;
- deterministic diagnostics and canonical JSON;
- atomic no-overwrite publication;
- runtime handoff receipt preservation.

Current machine-readable capability truth is `src/ev4_transition/data/capability-status.v1.json`. Real non-synthetic readiness must remain `insufficient_evidence` until exact owner evidence proves otherwise.
