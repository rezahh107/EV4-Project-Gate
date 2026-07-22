from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence


class OpenDirectoryError(OSError):
    """Raised when a validated local directory cannot be opened."""


def open_directory(
    directory: str | Path,
    *,
    platform: str | None = None,
    startfile: Callable[[str], object] | None = None,
    popen: Callable[..., object] = subprocess.Popen,
) -> None:
    """Open an existing directory through an explicit OS runner boundary.

    The command is always passed as an argument vector with ``shell=False``.
    Tests can inject the OS launcher without opening a real window.
    """

    target = Path(directory).expanduser().resolve()
    if not target.is_dir():
        raise OpenDirectoryError(f"Output directory does not exist: {target}")

    selected_platform = platform or sys.platform
    if selected_platform.startswith("win"):
        launcher = startfile or getattr(os, "startfile", None)
        if launcher is None:
            raise OpenDirectoryError("os.startfile is unavailable on this Windows runtime")
        launcher(str(target))
        return

    command: Sequence[str]
    if selected_platform == "darwin":
        command = ("open", str(target))
    else:
        command = ("xdg-open", str(target))
    try:
        popen(list(command), shell=False)
    except OSError as exc:
        raise OpenDirectoryError(str(exc)) from exc
