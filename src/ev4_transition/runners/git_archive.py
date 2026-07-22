from __future__ import annotations

from pathlib import Path
import subprocess


class GitArchiveRunnerError(RuntimeError):
    pass


def run_git(repository: str | Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *args],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
        raise GitArchiveRunnerError(f"git command failed: {' '.join(args)}: {detail}") from exc
    return completed.stdout.strip()
