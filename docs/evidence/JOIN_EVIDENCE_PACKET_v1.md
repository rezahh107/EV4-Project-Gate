# Join Evidence Packet v1 — Prompt 4.5

Purpose: reconcile live Producer evidence before Prompt 5 without modifying Producer repositories or Project Gate runtime code.

## Capability handshake

| Capability | Status |
|---|---|
| `read_all_five_github_repositories` | `AVAILABLE` |
| `inspect_pr_merged_state` | `AVAILABLE` |
| `inspect_exact_pr_head_sha` | `AVAILABLE` |
| `inspect_merge_commit_sha` | `AVAILABLE` |
| `inspect_ci_workflow_run_conclusion_for_exact_pr_head_sha` | `AVAILABLE` |
| `read_files_at_immutable_commit_refs` | `AVAILABLE` |
| `compute_sha256_from_git_show_blob_bytes` | `UNAVAILABLE` |
| `write_branch_and_pr_in_project_gate` | `AVAILABLE` |

## Producer evidence

| Producer | PR | Merged | Expected SHA match | Exact-head CI | Handoff | Hashes | Stage Bundle | Prompt 5 |
|---|---:|---|---|---|---|---|---|---|
| `architect` | `14` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `verified_path_unhashed` | `blocked` |
| `ce` | `28` | `verified` | `verified` | `verified` | `missing` | `insufficient_evidence` | `insufficient_evidence` | `blocked` |
| `builder` | `47` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `verified_path_unhashed` | `blocked` |
| `responsive` | `142` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `verified_path_unhashed` | `blocked` |

## Terminology note

`verified` in metadata columns means observed through GitHub PR/CI evidence. `verified_path_unhashed` means the path was observed, but SHA-256 verification by `git show <commit_sha>:<path> | sha256sum` was not completed. No `verified` or `verified_path_unhashed` artifact status overrides `prompt_5_ready: false` or `blocking_insufficient_evidence`.

## Project Gate branch CI note

CI evidence is head-specific. Head `321999282693dc818d34bfaa3bc81204324bb808` was observed with these Project Gate workflow conclusions: `success`.

- `UI Runtime Smoke`
- `Prompt 05 Builder Responsive Final Gate`
- `Prompt 06 Report UX`
- `Skeleton Health`

This note records the exact-head CI evidence that was current when the PRF-001 stale-CI-text repair was applied. If the PR head changes after this documentation update, exact-head CI must be rechecked before merge.

## Handoff discrepancy table

| Producer | Source | Status | Detail |
|---|---|---|---|
| `ce` | `docs/handoffs/PROMPT-02_HANDOFF.md` | `blocking` | Expected standard handoff not found; fallback report requires human acceptance. |
| `architect` | `docs/handoffs/PROMPT-01_HANDOFF.md` | `warning` | Handoff says `pending_merge` but PR is merged. |
| `architect` | `docs/handoffs/PROMPT-01_HANDOFF.md` | `warning` | Handoff references an old head SHA. |
| `builder` | `docs/handoffs/PROMPT-03_HANDOFF.md` | `warning` | Handoff says `pending_merge` but PR is merged. |
| `responsive` | `docs/handoffs/PROMPT-04_HANDOFF.md` | `warning` | Handoff says `pending_merge` but PR is merged. |
| `responsive` | `docs/handoffs/PROMPT-04_HANDOFF.md` | `warning` | Handoff branch differs from merged PR head branch. |

## Hash verification table

Required method: `git show <commit_sha>:<path> | sha256sum`.

| Scope | Status | Discrepancy coverage |
|---|---|---|
| `project_gate_prompt_0` / `contracts/common/producer-gate-export.v1.schema.json` | `insufficient_evidence` | `recorded` |
| `project_gate_prompt_0` / `schemas/stage-bundle/stage-bundle.v1.schema.json` | `insufficient_evidence` | `recorded` |
| `architect` required artifacts | `insufficient_evidence` | `recorded` |
| `ce` required artifacts | `insufficient_evidence` | `recorded` |
| `builder` required artifacts | `insufficient_evidence` | `recorded` |
| `responsive` required artifacts | `insufficient_evidence` | `recorded` |

## CE Stage Bundle repair note

Earlier packet text treated CE `stage_bundle_schema` as `not_applicable`. This has been repaired to `insufficient_evidence` because the common Producer Gate Export contract requires `final_stage_bundle`, and no contract-backed CE exception was verified in this Prompt 4.5 run.

## Prompt 5 readiness decision

`prompt_5_ready: false`

Decision: `blocked`.

## prompt_5_substitution

```yaml
FROM_PROMPT_1_FINAL_REPORT:
  source: docs/evidence/JOIN_EVIDENCE_PACKET_v1.json#/producers/architect
  replacement_status: blocked
  notes:
    - Do not use as Prompt 5 input until blocking_insufficient_evidence is empty.
FROM_PROMPT_2_FINAL_REPORT:
  source: docs/evidence/JOIN_EVIDENCE_PACKET_v1.json#/producers/ce
  replacement_status: blocked
  notes:
    - Do not use as Prompt 5 input until blocking_insufficient_evidence is empty.
FROM_PROMPT_3_FINAL_REPORT:
  source: docs/evidence/JOIN_EVIDENCE_PACKET_v1.json#/producers/builder
  replacement_status: blocked
  notes:
    - Do not use as Prompt 5 input until blocking_insufficient_evidence is empty.
FROM_PROMPT_4_FINAL_REPORT:
  source: docs/evidence/JOIN_EVIDENCE_PACKET_v1.json#/producers/responsive
  replacement_status: blocked
  notes:
    - Do not use as Prompt 5 input until blocking_insufficient_evidence is empty.
```

## Remaining blockers

- `project_gate_prompt_0_producer_gate_export_hash_not_git_show_verified`
- `project_gate_prompt_0_stage_bundle_hash_not_git_show_verified`
- `architect_required_artifact_hashes_not_git_show_verified`
- `ce_required_artifact_hashes_not_git_show_verified`
- `builder_required_artifact_hashes_not_git_show_verified`
- `responsive_required_artifact_hashes_not_git_show_verified`
- `ce_stage_bundle_schema_not_verified`
- `ce_standard_handoff_missing_requires_human_acceptance`

## Read-only statement

Producer repositories inspected read-only; no Producer repository modifications were made. Project Gate runtime code, validators, schemas, contracts, and routing were not modified.
