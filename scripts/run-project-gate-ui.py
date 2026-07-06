#!/usr/bin/env python3
"""Local launcher for the future EV4 Project Gate operator UI.

This script intentionally does not implement the UI. It only discovers and
launches a UI module when Prompt 1 has supplied one, and otherwise reports a
clear next step for a personal/local user.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

DEFAULT_UI_MODULES = (
    "ev4_transition.ui.app",
    "ev4_transition.ui.operator_panel",
    "ev4_transition.ui.gradio_app",
    "ev4_transition.ui",
)

MISSING_UI_MESSAGE_EN = "UI is not installed yet. Merge Prompt 1 UI branch first."
MISSING_UI_MESSAGE_FA = "رابط کاربری هنوز نصب نشده است. ابتدا شاخه UI مربوط به Prompt 1 را merge کن."


def _bootstrap_src_path() -> None:
    if SRC.exists() and str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))


def _check_package_import() -> bool:
    try:
        import ev4_transition  # noqa: F401
    except Exception as exc:  # pragma: no cover - defensive user-facing path
        print("❌ Python package import failed.")
        print("بسته Python قابل import نیست. اول وابستگی‌ها را نصب کن:")
        print("python -m pip install -e '.[dev]'")
        print(f"error: {type(exc).__name__}: {exc}")
        return False
    return True


def _find_first_module(candidates: Iterable[str]) -> tuple[str | None, list[str]]:
    discovery_errors: list[str] = []
    for module_name in candidates:
        try:
        try:
            if importlib.util.find_spec(module_name) is not None:
                return module_name
        except Exception:
            continue
    return None, discovery_errors


def _launch_module(module_name: str) -> int:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        print(f"❌ UI module import failed: {module_name}")
        print("ماژول UI پیدا شد، اما هنگام import خطا داد.")
        print(f"error: {type(exc).__name__}: {exc}")
        return 3

    for attr in ("launch", "main", "run"):
        candidate = getattr(module, attr, None)
        if callable(candidate):
            result = candidate()
            return int(result) if isinstance(result, int) else 0
    print(f"❌ UI module was found but has no launch/main/run callable: {module_name}")
    print("ماژول UI پیدا شد، اما entry point قابل اجرا ندارد.")
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local EV4 Project Gate UI when it is available.")
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="Optional UI module candidate. Can be provided multiple times; useful for tests and local overrides.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only detect the UI module; do not launch it.")
    args = parser.parse_args(argv)

    _bootstrap_src_path()
    if not _check_package_import():
        return 1

    candidates = tuple(args.modules) if args.modules else DEFAULT_UI_MODULES
    module_name, discovery_errors = _find_first_module(candidates)
    if module_name is None:
        print(f"⚠️ {MISSING_UI_MESSAGE_FA}")
        print(MISSING_UI_MESSAGE_EN)
        if discovery_errors:
            print("Optional UI discovery errors:")
            for item in discovery_errors[:5]:
                print(f"- {item}")
        print("Next action: merge Prompt 1 UI branch, then run this launcher again.")
        print("اقدام بعدی: ابتدا Prompt 1 UI را merge کن، سپس launcher را دوباره اجرا کن.")
        print("Current safe fallback: run the controlled synthetic demo:")
        print("python scripts/run-project-gate-demo.py")
        return 2

    print(f"✅ UI module detected: {module_name}")
    if args.dry_run:
        return 0
    return _launch_module(module_name)


if __name__ == "__main__":
    raise SystemExit(main())
