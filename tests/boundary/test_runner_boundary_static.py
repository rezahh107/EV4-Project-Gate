from __future__ import annotations

import runpy
from pathlib import Path


def _scanner():
    return runpy.run_path(str(Path("scripts/check-runner-boundary.py")))


def test_only_runners_can_execute_specialist_tools() -> None:
    scan_runner_boundary = _scanner()["scan_runner_boundary"]
    assert scan_runner_boundary("src/ev4_transition") == []


def test_static_boundary_scanner_detects_subprocess_outside_runners(tmp_path: Path) -> None:
    root = tmp_path / "src" / "ev4_transition"
    root.mkdir(parents=True)
    (root / "bad.py").write_text("import subprocess\n", encoding="utf-8")
    findings = _scanner()["scan_runner_boundary"](root)
    assert any(item.code == "PG.RUNNER_BOUNDARY.BANNED_IMPORT" for item in findings)


def test_static_boundary_scanner_detects_os_system_outside_runners(tmp_path: Path) -> None:
    root = tmp_path / "src" / "ev4_transition"
    root.mkdir(parents=True)
    (root / "bad.py").write_text("import os\nos.system('echo bad')\n", encoding="utf-8")
    findings = _scanner()["scan_runner_boundary"](root)
    assert any(item.code == "PG.RUNNER_BOUNDARY.OS_SYSTEM" for item in findings)


def test_static_boundary_scanner_allows_runner_subprocess(tmp_path: Path) -> None:
    root = tmp_path / "src" / "ev4_transition"
    runner = root / "runners"
    runner.mkdir(parents=True)
    (runner / "ok.py").write_text("import subprocess\n", encoding="utf-8")
    findings = _scanner()["scan_runner_boundary"](root)
    assert findings == []


def test_static_boundary_scanner_detects_tkinter_outside_runners(tmp_path: Path) -> None:
    root = tmp_path / "src" / "ev4_transition"
    root.mkdir(parents=True)
    (root / "bad.py").write_text("import tkinter\n", encoding="utf-8")
    findings = _scanner()["scan_runner_boundary"](root)
    assert any(item.code == "PG.RUNNER_BOUNDARY.BANNED_IMPORT" for item in findings)
