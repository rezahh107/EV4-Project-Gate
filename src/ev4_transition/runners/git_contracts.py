from __future__ import annotations

import subprocess
from pathlib import Path


def read_pinned_git_bytes(root: Path, commit: str, path: str) -> bytes:
    """Read one repository path from an explicit Git commit without a shell."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path}"],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise FileNotFoundError(
            f"Unable to execute Git for pinned contract {commit}:{path}."
        ) from exc
    if completed.returncode != 0:
        raise FileNotFoundError(f"Unable to read pinned contract {commit}:{path}.")
    return completed.stdout
