from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

_GITHUB_REPOSITORY = re.compile(r"(?:github\.com[:/])(?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$")


def inspect_checkout(
    repo_root: str | Path,
    *,
    expected_repository: str,
    expected_commit: str | None = None,
) -> dict[str, Any]:
    """Inspect a local Git checkout without trusting caller-supplied identity fields."""

    root = Path(repo_root).resolve()
    if not root.is_dir():
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            None,
            None,
            "PG_REPOSITORY_CHECKOUT_MISSING",
            "The required local repository checkout is unavailable.",
        )

    head = _git(root, "rev-parse", "HEAD")
    remote = _git(root, "remote", "get-url", "origin")
    if head[0] != 0 or remote[0] != 0:
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            None,
            None,
            "PG_REPOSITORY_IDENTITY_UNAVAILABLE",
            "The checkout could not prove its Git HEAD and origin identity.",
        )

    actual_commit = head[1].strip().lower()
    actual_repository = _repository_slug(remote[1].strip())
    if actual_repository is None:
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            actual_commit,
            None,
            "PG_REPOSITORY_ORIGIN_UNRECOGNIZED",
            "The checkout origin is not a recognizable GitHub repository identity.",
        )
    if actual_repository.lower() != expected_repository.lower():
        return _result(
            "invalid",
            expected_repository,
            expected_commit,
            actual_commit,
            actual_repository,
            "PG_REPOSITORY_IDENTITY_MISMATCH",
            "The checkout repository identity does not match the accepted owner repository.",
        )
    if expected_commit is not None and actual_commit != expected_commit:
        return _result(
            "invalid",
            expected_repository,
            expected_commit,
            actual_commit,
            actual_repository,
            "PG_REPOSITORY_COMMIT_MISMATCH",
            "The checkout HEAD does not match the accepted immutable commit.",
        )
    return {
        "status": "accepted",
        "repository": actual_repository,
        "commit": actual_commit,
        "path": str(root),
        "diagnostics": [],
    }


def _git(root: Path, *args: str) -> tuple[int, str]:
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME"}}
    env.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=10,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return completed.returncode, completed.stdout


def _repository_slug(remote: str) -> str | None:
    match = _GITHUB_REPOSITORY.search(remote.rstrip("/"))
    return match.group("slug") if match else None


def _result(
    status: str,
    expected_repository: str,
    expected_commit: str | None,
    actual_commit: str | None,
    actual_repository: str | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    severity = "insufficient_evidence" if status == "insufficient_evidence" else "error"
    return {
        "status": status,
        "repository": actual_repository,
        "commit": actual_commit,
        "diagnostics": [
            {
                "code": code,
                "severity": severity,
                "message": message,
                "path": "$",
                "details": {
                    "expected_repository": expected_repository,
                    "expected_commit": expected_commit,
                    "actual_repository": actual_repository,
                    "actual_commit": actual_commit,
                },
            }
        ],
    }
