# Schemas

This directory contains active **EV4 Project Gate-owned envelope/result/diagnostic/lock schemas** only.

Active in this foundation:

```text
schemas/stage-bundle/stage-bundle.v1.schema.json
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
schemas/diagnostic/diagnostic.v1.schema.json
schemas/lock-manifest/lock-manifest.v1.schema.json
```

These schemas define Project Gate containers, diagnostics, lock carriers, and machine-readable results. They are not copied canonical schemas from EV4 specialist repositories.

Do not place Architect, CE, Builder, or Responsive domain-authoritative schemas here unless a future migration PR explicitly unlocks that scope.
