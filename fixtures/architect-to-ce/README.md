# Architect to CE transition fixtures

This directory is for `ev4-architect-to-ce-transition@1.0.0` fixture metadata.

The transition tests use pinned synthetic source snapshots from the authoritative specialist repositories. The executable source of truth for these pins is the external lock manifest and workflow, not this README:

- `contracts/locks/architect-to-ce-transition.v1.lock.json`
- `.github/workflows/validate.yml`

Current pins:

- `rezahh107/EV4-Architect-Repo@b0651668b97f682bb17f66840c8e8c503fd3935d`
- `rezahh107/EV4-Constructability-Engineer-Repo@546680a2e2a309c0d7e0ddbfc017e9e194ece7cb`

```yaml
classification: synthetic
real_cross_repository_validation: not_available
verification_state: synthetic_fixture_only
```

No fixture in this directory is a real Elementor project artifact.
