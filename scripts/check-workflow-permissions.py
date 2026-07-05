#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

WRITE_WORKFLOW_ALLOWLIST = {
    Path(".github/workflows/status-after-merge.yml"): {
        "actions": "write",
        "contents": "write",
        "pull-requests": "read",
    }
}


def _load_workflow(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: workflow must be a YAML mapping")
    return value


def _checkout_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return steps
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        job_steps = job.get("steps")
        if not isinstance(job_steps, list):
            continue
        for step in job_steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/checkout@"):
                steps.append(step)
    return steps


def check_repository(root: Path) -> list[str]:
    workflow_root = root / ".github" / "workflows"
    if not workflow_root.is_dir():
        return [f"{workflow_root}: workflow directory does not exist"]

    failures: list[str] = []
    workflows = sorted(
        path for path in workflow_root.iterdir() if path.is_file() and path.suffix in {".yml", ".yaml"}
    )
    if not workflows:
        return [f"{workflow_root}: no workflow files found"]

    for path in workflows:
        relative = path.relative_to(root)
        try:
            workflow = _load_workflow(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(str(exc))
            continue

        permissions = workflow.get("permissions")
        expected_write_permissions = WRITE_WORKFLOW_ALLOWLIST.get(relative)
        if expected_write_permissions is not None:
            if permissions != expected_write_permissions:
                failures.append(
                    f"{relative}: write-enabled workflow permissions must exactly equal "
                    f"{expected_write_permissions!r}"
                )
            continue

        if not isinstance(permissions, dict):
            failures.append(f"{relative}: read-only workflow must declare top-level permissions")
        else:
            if permissions.get("contents") != "read":
                failures.append(f"{relative}: read-only workflow must declare contents: read")
            for scope, level in sorted(permissions.items()):
                if level == "write":
                    failures.append(
                        f"{relative}: unexpected write permission {scope}: write"
                    )

        checkout_steps = _checkout_steps(workflow)
        for job_id, step_index, step in checkout_steps:
            with_config = step.get("with")
            persisted = with_config.get("persist-credentials") if isinstance(with_config, dict) else None
            if persisted is not False:
                failures.append(
                    f"{relative}: job {job_id!r} step {step_index + 1} must set persist-credentials: false"
                )

    return sorted(failures)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce explicit minimum GitHub token permissions and checkout credential handling."
    )
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    failures = check_repository(Path(args.root))
    if failures:
        print("Workflow permission policy violations found:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Workflow permissions and checkout credential handling satisfy policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
