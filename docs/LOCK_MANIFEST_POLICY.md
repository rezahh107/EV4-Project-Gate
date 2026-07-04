# EV4 Project Gate Lock Manifest Policy

Status: `PROMPT-01` Project Gate-owned lock carrier baseline.

## Purpose

A lock manifest records pinned external contract bytes for Project Gate orchestration. It is not a competing specialist schema and it must not authenticate itself.

Project Gate may use lock manifests to verify:

```text
repository → accepted commit/ref → path → file-byte SHA-256 → declared contract/schema identity
```

## Schema

```text
schemas/lock-manifest/lock-manifest.v1.schema.json
```

The schema accepts:

```text
lock-manifest.v1
external-contract-lock.v1
```

`external-contract-lock.v1` is retained for the existing Architect→CE lock file. New generic lock manifests should use `lock-manifest.v1` unless a transition-specific compatibility reason is documented.

## Required entry fields

```yaml
role: Project Gate expected dependency role
repository: owner/repo
accepted_commit: exact 40-character lowercase commit SHA
path: repo-local file path
contract_or_schema_id: expected contract/schema identity
sha256_file_bytes: lowercase SHA-256 over exact file bytes
size_bytes: optional byte count
```

## Verification rules

Project Gate lock verification must be fail-closed:

- missing `schema_version` is invalid;
- unknown `schema_version` is invalid;
- duplicate roles are invalid;
- missing repository/ref/path/hash/identity is invalid;
- file-byte hash mismatch is invalid;
- schema/contract identity mismatch is invalid when identity is machine-checkable.

## Boundary rule

Lock manifests are Project Gate orchestration metadata only. They do not copy specialist schemas and they do not replace official specialist validators or adapters.
