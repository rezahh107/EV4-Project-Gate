from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from ev4_transition.runners.native_dialog import select_directory
from ev4_transition.runners.open_output_folder import OpenDirectoryError, open_directory


def test_native_dialog_selection_uses_child_process_without_shell(tmp_path: Path) -> None:
    observed = {}

    def fake_run(command, **kwargs):
        observed.update(command=command, kwargs=kwargs)
        return subprocess.CompletedProcess(command, 0, json.dumps({"status": "selected", "selected_path": str(tmp_path)}), "")

    assert select_directory("old", run=fake_run) == str(tmp_path)
    assert observed["command"][1:3] == ["-m", "ev4_transition.runners.native_dialog_child"]
    assert observed["kwargs"]["shell"] is False
    assert observed["kwargs"]["timeout"] == 120.0


def test_native_dialog_cancellation_preserves_prior_value() -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, json.dumps({"status": "cancelled", "selected_path": None}), "")

    assert select_directory("C:/prior", run=fake_run) == "C:/prior"


def test_native_dialog_timeout_preserves_prior_value() -> None:
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    assert select_directory("C:/prior", run=fake_run, timeout_seconds=0.01) == "C:/prior"


def test_open_directory_runner_uses_argument_vector_without_shell(tmp_path: Path) -> None:
    observed = {}

    def fake_popen(command, **kwargs):
        observed.update(command=command, kwargs=kwargs)
        return SimpleNamespace()

    open_directory(tmp_path, platform="linux", popen=fake_popen)
    assert observed["command"] == ["xdg-open", str(tmp_path.resolve())]
    assert observed["kwargs"]["shell"] is False


def test_open_directory_rejects_missing_directory(tmp_path: Path) -> None:
    try:
        open_directory(tmp_path / "missing", platform="linux")
    except OpenDirectoryError:
        pass
    else:
        raise AssertionError("missing output directory was accepted")
