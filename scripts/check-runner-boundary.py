#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

BANNED_IMPORTS = {"subprocess", "importlib", "tkinter"}
BANNED_EXECUTABLE_STRINGS = {"python", "python3", "node", "npm", "npx"}
APPROVED_RUNNER_WRAPPERS = {"execute_official_tool"}
RUNNER_PARTS = ("ev4_transition", "runners")


@dataclass(frozen=True)
class BoundaryFinding:
    path: str
    line: int
    code: str
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


def scan_runner_boundary(root: str | Path = "src/ev4_transition") -> list[BoundaryFinding]:
    root_path = Path(root)
    findings: list[BoundaryFinding] = []
    for path in sorted(root_path.rglob("*.py")):
        if _is_runner_path(path):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            findings.append(
                BoundaryFinding(
                    _display_path(path),
                    exc.lineno or 1,
                    "PG.RUNNER_BOUNDARY.SYNTAX_ERROR",
                    "Python file could not be parsed.",
                )
            )
            continue
        visitor = _BoundaryVisitor(path)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    return findings


class _BoundaryVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[BoundaryFinding] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.split(".", 1)[0] in BANNED_IMPORTS:
                self._add(
                    node,
                    "PG.RUNNER_BOUNDARY.BANNED_IMPORT",
                    f"{alias.name} import is only allowed under src/ev4_transition/runners/.",
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module.split(".", 1)[0] in BANNED_IMPORTS:
            self._add(
                node,
                "PG.RUNNER_BOUNDARY.BANNED_IMPORT",
                f"{module} import is only allowed under src/ev4_transition/runners/.",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        dotted = _dotted_name(node.func)
        if dotted == "os.system":
            self._add(
                node,
                "PG.RUNNER_BOUNDARY.OS_SYSTEM",
                "os.system is forbidden outside runner boundary.",
            )
        if any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        ):
            self._add(
                node,
                "PG.RUNNER_BOUNDARY.SHELL_TRUE",
                "shell=True is forbidden outside runner boundary.",
            )
        if dotted.startswith("importlib."):
            self._add(
                node,
                "PG.RUNNER_BOUNDARY.IMPORTLIB_SPECIALIST",
                "importlib-based dynamic imports are forbidden outside runner boundary.",
            )
        if dotted not in APPROVED_RUNNER_WRAPPERS and _call_contains_direct_runtime_command(node):
            self._add(
                node,
                "PG.RUNNER_BOUNDARY.DIRECT_RUNTIME_COMMAND",
                "direct Python/Node command execution is only allowed in runner boundary.",
            )
        self.generic_visit(node)

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(
            BoundaryFinding(
                _display_path(self.path),
                getattr(node, "lineno", 1),
                code,
                message,
            )
        )


def _call_contains_direct_runtime_command(node: ast.Call) -> bool:
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Attribute)
            and child.attr == "executable"
            and _dotted_name(child.value) == "sys"
        ):
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if child.value.lower() in BANNED_EXECUTABLE_STRINGS:
                return True
    return False


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _is_runner_path(path: Path) -> bool:
    parts = path.parts
    for index in range(len(parts) - len(RUNNER_PARTS) + 1):
        if parts[index : index + len(RUNNER_PARTS)] == RUNNER_PARTS:
            return True
    return False


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enforce Project Gate runner subprocess boundary."
    )
    parser.add_argument("root", nargs="?", default="src/ev4_transition")
    args = parser.parse_args(list(argv) if argv is not None else None)
    findings = scan_runner_boundary(args.root)
    if findings:
        for finding in findings:
            print(finding.render())
        return 1
    print("runner boundary ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
