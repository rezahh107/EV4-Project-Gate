# PROMPT-06 Handoff

```yaml
prompt_id: PROMPT-06
branch: project-gate-prompt-06-ux
pull_request: 24
base_branch: main
latest_head_sha_recorded: dbdab5239085aadf015ec4ec8dd03606f11d712d
review_repair_source:
  review_package: review-package.json
  original_review_status: RED_DO_NOT_MERGE
  blocking_findings_repaired:
    - PRF-001: missing explicit minimum workflow permissions
    - PRF-002: directory fsync could falsely fail completed atomic replace
  non_blocking_findings_deferred:
    - PRF-003: optional HTML renderer wraps Markdown; clarify before promoting HTML as a real UI surface
commits:
  original_prompt_06_commits: see PR #24 branch history before review repair
  review_repair_commits:
    - a0110893b013c346860246df545507a28e6faa12
    - d43202fe1acab213ab8080bbf4b21364c95921b9
    - e38b35b937ee21ce612090dcc822c783bc8d98f4
    - bce78d673343c3560489aa04d18b8b1be2284ce9
    - e57cb29612e400b0aa0041d754e9d74970fb1160
    - 2c2b9f0913ea74f7609d9394e7705f90c6d55cd4
    - 625eb8428e40d55595790344f7a1f2a247c5b9a4
    - 17dc19f323ddae10c64cd4baf80ad56c7db96b59
    - 5b0855b4c8b8724d5a3a1c14a6d10d9bdc01e383
    - 5436edcace1e1908e4fdc8528868ddba41cbd04a
    - dbdab5239085aadf015ec4ec8dd03606f11d712d
files_changed:
  - .github/workflows/prompt-06.yml
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/REPORT_UX_CONTRACT.md
  - docs/STANDARDS_TRACEABILITY.md
  - docs/handoffs/PROMPT-06_HANDOFF.md
  - src/ev4_transition/cli.py
  - src/ev4_transition/io/__init__.py
  - src/ev4_transition/io/atomic_writer.py
  - src/ev4_transition/presentation/__init__.py
  - src/ev4_transition/presentation/bidi.py
  - src/ev4_transition/presentation/theme_tokens.py
  - src/ev4_transition/reports/__init__.py
  - src/ev4_transition/reports/renderers.py
  - tests/reporting/test_output_writer.py
  - tests/reporting/test_report_rendering.py
  - tests/reporting/test_workflow_permissions.py
  - tests/theme_acceptance/test_theme_tokens.py
  - tests/typography_acceptance/test_persian_bidi_typography.py
  - tests/ux_acceptance/test_report_status_ux.py
tests_run:
  - local limited prototype before repository writes: PYTHONPATH=src pytest -q tests/ux_acceptance tests/typography_acceptance tests/theme_acceptance tests/reporting
  - GitHub Actions on head dbdab5239085aadf015ec4ec8dd03606f11d712d: Prompt 06 Report UX
  - GitHub Actions on head dbdab5239085aadf015ec4ec8dd03606f11d712d: Prompt 05 Builder Responsive Final Gate
  - GitHub Actions on head dbdab5239085aadf015ec4ec8dd03606f11d712d: Skeleton Health
tests_passed:
  - local limited prototype before repository writes: 19 passed in 0.19s
  - Prompt 06 Report UX run 28752370265: success
  - Prompt 05 Builder Responsive Final Gate run 28752370270: success
  - Skeleton Health run 28752370274: success
tests_failed: []
tests_not_run:
  - full local live-checkout pytest from this environment: unavailable because github.com DNS resolution failed earlier
  - dependency metadata scan: not performed
coverage_rules_advanced:
  - PG-STATUS-001: validator_backed
  - PG-OUTPUT-001: validator_backed
  - PG-PROGRESS-001: validator_backed
  - PG-UNICODE-001: validator_backed
  - PG-THEME-001: validator_backed
  - PG-BRC-001: remains fixture_tested; standards traceability added as carrier
coverage_rules_still_gap:
  - Prompt-06 UX/report rules are not promoted to fixture_tested because dedicated behavioral fixtures are not yet bound through the behavioral coverage validator.
  - No downstream_contract_enforced status is claimed.
new_diagnostics:
  - none added to deterministic transition decision logic
  - report renderers surface existing diagnostic codes as LTR/copyable technical fragments
new_or_changed_cli:
  - ev4-transition --format persian now uses report renderer for status payloads
  - JSON output remains canonical and undecorated
new_or_changed_ci:
  - .github/workflows/prompt-06.yml added
  - Prompt-06 workflow now explicitly sets permissions.contents=read
  - Prompt-06 checkout now sets persist-credentials=false
  - tests/reporting/test_workflow_permissions.py validates Prompt-06 least-privilege workflow contract
  - Prompt-06 workflow runs UX acceptance, typography acceptance, theme acceptance, reporting, atomic writer, and behavioral coverage checks
important_design_decisions:
  - Phase 1 remains CLI plus generated Persian reports; no local web UI or desktop UI was added.
  - status_mapping.py remains the status-presentation SSOT.
  - Report rendering deep-copies result payloads and does not mutate deterministic result objects.
  - Progress events are excluded only from report-level hash calculation; transition logic was not changed.
  - File fsync before os.replace remains strict.
  - Directory fsync after os.replace is best-effort to avoid false failure after a successful atomic replacement.
  - Atomic writer reports success/download only after final path existence is confirmed.
  - Persian reports use RTL containers; technical identifiers use LTR isolation and monospace code wrappers.
  - Theme tokens are explicit for light/dark mode; dark tokens are not simple inversion.
web_sources_used:
  - Python official docs: os.replace atomic destination replacement semantics
  - Python official docs: os.fsync after file flush for disk write
  - Python official docs: tempfile.NamedTemporaryFile temporary output behavior
  - GitHub official docs: permissions key configures minimum required workflow access
  - actions/checkout README: persist-credentials false disables persisted checkout credentials
next_allowed_prompt: PROMPT-07 closure audit / stale prose cleanup / release readiness review
blocking_issues:
  - none known after PRF-001 and PRF-002 repair, subject to later PR Inspector re-review
remaining_insufficient_evidence:
  - real non-synthetic CE-to-Builder transition evidence
  - real Builder execution evidence bundle
  - real Responsive input/output evidence bundle
  - accessibility, export, and frontend correctness evidence
  - downstream owner rejection evidence for downstream_contract_enforced claims
```

## Review repair notes

- `PRF-001` was fixed by adding explicit `permissions: contents: read` and `persist-credentials: false` to `.github/workflows/prompt-06.yml`, plus a static regression test.
- `PRF-002` was fixed by making only directory-level fsync after `os.replace()` best-effort while preserving strict file fsync before replacement, plus regression tests for both cases.
- `PRF-003` remains non-blocking. Optional HTML output should not be advertised as a real HTML report until renamed or converted/tested as true HTML.
- This prompt intentionally did not change transition acceptance, invalid, repair-needed, or insufficient-evidence decision logic.
