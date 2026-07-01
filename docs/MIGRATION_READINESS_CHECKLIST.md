# EV4 Migration Readiness Checklist

Canonical schema migration is blocked until every item below is true.

- [ ] duplicate `ev4-builder-context-package@1.0.0` drift resolved or safely renamed/deprecated
- [ ] Architect direct-to-Builder path downgraded and verified
- [ ] Architect Stage 10/11 wording aligned
- [ ] CE producer/carry ownership explicit
- [ ] CE executable package gate validated
- [ ] Builder rejects Architect-only packages as Builder-ready
- [ ] Builder rejects CE review-only packages as runtime-ready
- [ ] Builder adapter validates visual-reference prerequisites
- [ ] Responsive has Golden Reference family/scope linkage
- [ ] Responsive rejects raw screenshot authority
- [ ] Responsive rejects desktop-to-mobile/tablet inference
- [ ] all four repos have passing CI/validation evidence
- [ ] shared schema promotion plan approved
- [ ] versioning policy approved
- [ ] backwards compatibility policy approved

If any item is unchecked, canonical schema migration remains blocked.

## Required Evidence Before Promotion

Each checked item must cite evidence from the owning repository, validation output, CI result, fixture coverage, or an approved ADR. Checklist completion by assertion is not sufficient.
