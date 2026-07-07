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

| Producer | PR | Merged | Expected SHA match | Exact-head CI | Handoff | Hashes | Prompt 5 |
|---|---:|---|---|---|---|---|---|
| `architect` | `14` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `blocked` |
| `ce` | `28` | `verified` | `verified` | `verified` | `missing` | `insufficient_evidence` | `blocked` |
| `builder` | `47` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `blocked` |
| `responsive` | `142` | `verified` | `verified` | `verified` | `stale` | `insufficient_evidence` | `blocked` |

## Handoff discrepancies

| Producer | Source | Status | Detail |
|---|---|---|---|
| `ce` | `docs/handoffs/PROMPT-02_HANDOFF.md` | `blocking` | Expected standard handoff not found; fallback report requires human acceptance. |
| `architect` | `docs/handoffs/PROMPT-01_HANDOFF.md` | `warning` | Handoff says pending_merge but PR is merged. |
| `architect` | `docs/handoffs/PROMPT-01_HANDOFF.md` | `warning` | Handoff references an old head SHA. |
| `builder` | `docs/handoffs/PROMPT-03_HANDOFF.md` | `warning` | Handoff says pending_merge but PR is merged. |
| `responsive` | `docs/handoffs/PROMPT-04_HANDOFF.md` | `warning` | Handoff says pending_merge but PR is merged. |
| `responsive` | `docs/handoffs/PROMPT-04_HANDOFF.md` | `warning` | Handoff branch differs from merged PR head branch. |

## Hash verification

Required method: `git show <commit_sha>:<path> | sha256sum`.

Status: `insufficient_evidence` for Prompt 0 contracts and all Producer required artifact records because git blob bytes were unavailable. GitHub connector file/PR evidence is fallback only.

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

- `project_gate_prompt_0_hashes_not_git_show_verified`
- `producer_required_artifact_hashes_not_git_show_verified`
- `ce_standard_handoff_missing_requires_human_acceptance`

## Read-only statement

Producer repositories inspected read-only; no Producer repository modifications were made. Project Gate runtime code, validators, schemas, contracts, and routing were not modified.
