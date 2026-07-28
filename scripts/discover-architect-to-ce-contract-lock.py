#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ev4_transition.external_lock import (
    ARCHITECT_COMMIT,
    ARCHITECT_REPO,
    CE_COMMIT,
    CE_REPO,
    TRANSITION_ID,
)

ROLE_SPECS: tuple[dict[str, str], ...] = (
    {
        "role": "architect_payload_schema",
        "repository": ARCHITECT_REPO,
        "accepted_commit": ARCHITECT_COMMIT,
        "path": "schemas/ev4-architect-stage-payload.v1.schema.json",
        "contract_or_schema_id": "ev4-architect-stage-payload@1.0.0",
    },
    {
        "role": "architect_payload_validator",
        "repository": ARCHITECT_REPO,
        "accepted_commit": ARCHITECT_COMMIT,
        "path": "scripts/check-architect-stage-payload.py",
        "contract_or_schema_id": "ev4-architect-stage-payload-validator@1.0.0",
    },
    {
        "role": "architect_valid_fixture",
        "repository": ARCHITECT_REPO,
        "accepted_commit": ARCHITECT_COMMIT,
        "path": "fixtures/architect-stage-payload/valid/minimal-complete.v1.json",
        "contract_or_schema_id": "ev4-architect-stage-payload@1.0.0",
    },
    {
        "role": "architect_insufficient_fixture",
        "repository": ARCHITECT_REPO,
        "accepted_commit": ARCHITECT_COMMIT,
        "path": "fixtures/architect-stage-payload/insufficient-evidence/missing-real-stage-output.v1.json",
        "contract_or_schema_id": "ev4-architect-stage-payload@1.0.0",
    },
    {
        "role": "ce_intake_schema",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "schemas/ce_architect_stage_intake.v1_1.schema.json",
        "contract_or_schema_id": "ev4-ce-architect-stage-intake@1.1.0",
    },
    {
        "role": "ce_intake_validator",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "scripts/validate-ce-architect-stage-intake.py",
        "contract_or_schema_id": "ev4-ce-architect-stage-intake-validator@1.1.0",
    },
    {
        "role": "ce_mapping_contract",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "contracts/ARCHITECT_STAGE_TO_CE_INTAKE_MAPPING_V1_1.md",
        "contract_or_schema_id": "ev4-architect-stage-to-ce-intake-mapping@1.1.0",
    },
    {
        "role": "ce_valid_fixture",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "fixtures/architect-stage-intake-v1-1/valid/project-gate-transition-complete.v1_1.json",
        "contract_or_schema_id": "ev4-ce-architect-stage-intake@1.1.0",
    },
    {
        "role": "ce_insufficient_fixture",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "fixtures/architect-stage-intake-v1-1/insufficient-evidence/project-gate-transition-insufficient.v1_1.json",
        "contract_or_schema_id": "ev4-ce-architect-stage-intake@1.1.0",
    },
    {
        "role": "ce_synthetic_source_bundle_fixture",
        "repository": CE_REPO,
        "accepted_commit": CE_COMMIT,
        "path": "fixtures/architect-stage-intake-v1-1/source-bundles/synthetic-architect-stage-bundle.v1.json",
        "contract_or_schema_id": "ev4-architect-stage-payload@1.0.0",
    },
)

EXPECTED_ROLES = tuple(item["role"] for item in ROLE_SPECS)
ROLE_INDEX = {role: index for index, role in enumerate(EXPECTED_ROLES)}


def canonical_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        die(f"failed to read git HEAD for {path}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def verify_specs() -> None:
    seen: set[str] = set()
    for item in ROLE_SPECS:
        role = item["role"]
        if role in seen:
            die(f"duplicate role in discovery spec: {role}")
        seen.add(role)
        if role not in ROLE_INDEX:
            die(f"unexpected role in discovery spec: {role}")
        repository = item["repository"]
        accepted_commit = item["accepted_commit"]
        if repository == ARCHITECT_REPO and accepted_commit != ARCHITECT_COMMIT:
            die(f"architect commit mismatch for role {role}")
        if repository == CE_REPO and accepted_commit != CE_COMMIT:
            die(f"CE commit mismatch for role {role}")
        if repository not in {ARCHITECT_REPO, CE_REPO}:
            die(f"repository mismatch for role {role}: {repository}")
        if not item["path"] or item["path"].startswith("/") or ".." in Path(item["path"]).parts:
            die(f"unsafe or invalid path for role {role}: {item['path']}")
    missing = sorted(set(EXPECTED_ROLES) - seen)
    if missing:
        die(f"missing discovery roles: {', '.join(missing)}")


def read_exact_file_bytes(root: Path, relative_path: str, role: str) -> bytes:
    root = root.resolve()
    file_path = (root / relative_path).resolve()
    if root not in file_path.parents and file_path != root:
        die(f"path escapes checkout root for role {role}: {relative_path}")
    if not file_path.exists():
        die(f"missing file for role {role}: {relative_path}")
    if not file_path.is_file():
        die(f"non-regular file for role {role}: {relative_path}")
    return file_path.read_bytes()


def discover(architect_repo: Path, ce_repo: Path) -> dict[str, Any]:
    verify_specs()
    roots = {
        ARCHITECT_REPO: architect_repo.resolve(),
        CE_REPO: ce_repo.resolve(),
    }
    checkout_commits = [
        {"repository": ARCHITECT_REPO, "expected_commit": ARCHITECT_COMMIT, "actual_commit": git_head(architect_repo)},
        {"repository": CE_REPO, "expected_commit": CE_COMMIT, "actual_commit": git_head(ce_repo)},
    ]
    for item in checkout_commits:
        if item["actual_commit"] != item["expected_commit"]:
            die(
                "checkout commit mismatch for "
                f"{item['repository']}: expected {item['expected_commit']} got {item['actual_commit']}"
            )

    files: list[dict[str, Any]] = []
    for spec in sorted(ROLE_SPECS, key=lambda item: ROLE_INDEX[item["role"]]):
        content = read_exact_file_bytes(roots[spec["repository"]], spec["path"], spec["role"])
        files.append(
            {
                "role": spec["role"],
                "repository": spec["repository"],
                "accepted_commit": spec["accepted_commit"],
                "path": spec["path"],
                "contract_or_schema_id": spec["contract_or_schema_id"],
                "sha256_file_bytes": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        )

    return {
        "schema_version": "architect-to-ce-lock-discovery.v1",
        "transition_id": TRANSITION_ID,
        "checkout_commits": checkout_commits,
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--architect-repo", required=True)
    parser.add_argument("--ce-repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    payload = discover(Path(args.architect_repo), Path(args.ce_repo))
    text = canonical_dumps(payload) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
