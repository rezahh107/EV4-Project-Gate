from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from ev4_transition.runners.contracts import REQUIRED_PACKAGED_RUNNER_MODULES

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp("runner-wheel")
    dist = tmp_path / "dist"
    dist.mkdir()
    completed = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist), "--python", sys.executable, "--no-python-downloads"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def test_built_wheel_contains_required_runner_modules(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as archive:
        names = set(archive.namelist())
    assert set(REQUIRED_PACKAGED_RUNNER_MODULES) <= names


def test_installed_wheel_imports_ui_and_all_runners(built_wheel: Path, tmp_path: Path) -> None:
    target = tmp_path / "installed"
    completed = subprocess.run(
        ["uv", "pip", "install", "--no-deps", "--target", str(target), str(built_wheel)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    script = """
from ev4_transition.runners.native_dialog import select_directory
from ev4_transition.runners.open_output_folder import open_directory
from ev4_transition.runners.git_archive import run_git
from ev4_transition.ui.app import build_demo
assert select_directory and open_directory and run_git and build_demo
print('PACKAGED_IMPORT_OK')
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(target)
    imported = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env, text=True, capture_output=True, check=False)
    assert imported.returncode == 0, imported.stdout + imported.stderr
    assert "PACKAGED_IMPORT_OK" in imported.stdout


def test_package_missing_required_runner_fails_ui_import(built_wheel: Path, tmp_path: Path) -> None:
    extracted = tmp_path / "malformed"
    with zipfile.ZipFile(built_wheel) as archive:
        archive.extractall(extracted)
    (extracted / "ev4_transition/runners/open_output_folder.py").unlink()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(extracted)
    completed = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(extracted)!r}); from ev4_transition.ui.app import build_demo"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "open_output_folder" in completed.stderr
