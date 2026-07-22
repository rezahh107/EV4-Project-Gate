from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def _top_level_mutations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Attribute) for target in targets):
                findings.append(f"attribute assignment line {node.lineno}")
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            findings.append(f"top-level call line {node.lineno}")
    return findings


def test_ui_and_service_package_imports_have_no_behavioral_mutation() -> None:
    for relative in ("src/ev4_transition/ui/__init__.py", "src/ev4_transition/service/__init__.py"):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        assert "importlib" not in text
        assert "object.__setattr__" not in text
        assert _top_level_mutations(path) == []


def test_importing_service_does_not_replace_dispatcher_authority() -> None:
    script = """
import ev4_transition.service.dispatcher as dispatcher
before = dispatcher._run_producer_emitted_request
import ev4_transition.service
assert dispatcher._run_producer_emitted_request is before
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_importing_ui_does_not_replace_app_or_adapter_functions() -> None:
    script = """
import ev4_transition.ui.app as app
import ev4_transition.ui.adapters as adapters
before_header = app.operator_header_html
before_preflight = adapters._ui_preflight_diagnostics
import ev4_transition.ui
assert app.operator_header_html is before_header
assert adapters._ui_preflight_diagnostics is before_preflight
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
