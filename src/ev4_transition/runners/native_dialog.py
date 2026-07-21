from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Callable


def select_directory(
    previous_value: str | None,
    *,
    timeout_seconds: float = 120.0,
    executable: str | None = None,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Select a directory in a child process and fail back to the prior value.

    Gradio callbacks execute in worker threads. Tk must therefore run in a
    separate process where it owns the process main thread. Cancellation,
    unavailable GUI facilities, malformed responses, non-zero exits, and
    timeouts all preserve the prior value.
    """

    prior = previous_value or ""
    command = [
        executable or sys.executable,
        "-m",
        "ev4_transition.runners.native_dialog_child",
        "--initial-directory",
        prior,
    ]
    try:
        completed = run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return prior

    try:
        payload = json.loads(completed.stdout.strip())
    except (TypeError, ValueError, json.JSONDecodeError):
        return prior
    if completed.returncode != 0 or not isinstance(payload, dict) or payload.get("status") != "selected":
        return prior
    selected = payload.get("selected_path")
    if not isinstance(selected, str) or not selected.strip():
        return prior
    candidate = Path(selected).expanduser()
    return str(candidate) if candidate.is_dir() else prior
