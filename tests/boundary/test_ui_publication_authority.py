from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_modules_have_no_direct_report_filesystem_publication_authority():
    forbidden_calls = {"write_text", "write_bytes", "rename", "link"}
    for relative in ("src/ev4_transition/ui/adapters.py", "src/ev4_transition/ui/app.py"):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not (calls & forbidden_calls), f"{relative} has direct publication calls: {calls & forbidden_calls}"


def test_ui_does_not_import_attempt_or_report_publication_primitives():
    for relative in ("src/ev4_transition/ui/adapters.py", "src/ev4_transition/ui/app.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "prepare_attempt_paths" not in text
        assert "publish_report_bundle" not in text
        assert "publish_result_payload" not in text
        assert "stage_exact_" not in text
