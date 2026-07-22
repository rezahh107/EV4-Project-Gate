from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "classify-validation-scope.py"
SPEC = importlib.util.spec_from_file_location("validation_scope", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ALL = list(MODULE.BOUNDARIES)


def classify(*paths: str, force_all: bool = False):
    return MODULE.classify_paths(paths, force_all=force_all)


def test_unknown_path_selects_all_boundaries():
    assert classify("unexpected/new-surface.txt")["boundaries"] == ALL


def test_shared_service_path_selects_all_boundaries():
    assert classify("src/ev4_transition/service/dispatcher.py")["boundaries"] == ALL


def test_workflow_change_selects_all_boundaries():
    assert classify(".github/workflows/validate.yml")["boundaries"] == ALL


def test_docs_only_non_authoritative_change_selects_no_boundary():
    result = classify("docs/PERSONAL_USE_GUIDE.md")
    assert result["run_all"] is False
    assert result["boundaries"] == []


def test_architect_to_ce_path_selects_only_architect_boundary():
    assert classify("src/ev4_transition/transitions/architect_to_ce.py")["boundaries"] == ["architect_to_ce"]


def test_ce_to_builder_path_selects_only_ce_boundary():
    assert classify("src/ev4_transition/transitions/ce_to_builder.py")["boundaries"] == ["ce_to_builder"]


def test_builder_to_responsive_path_selects_only_responsive_boundary():
    assert classify("src/ev4_transition/transitions/builder_to_responsive.py")["boundaries"] == ["builder_to_responsive"]


def test_final_gate_path_selects_only_final_gate():
    assert classify("src/ev4_transition/transitions/final_gate.py")["boundaries"] == ["final_gate"]


def test_kernel_path_selects_only_kernel_intake():
    assert classify("scripts/kernel-decision-intake-bridge.mjs")["boundaries"] == ["kernel_intake"]


def test_producer_path_selects_only_producer_integration():
    assert classify("contracts/producer-adoption/ev4-producer-adoption-set.v1.json")["boundaries"] == ["producer_integration"]


def test_multiple_boundaries_are_combined_in_stable_order():
    result = classify(
        "src/ev4_transition/transitions/ce_to_builder.py",
        "src/ev4_transition/transitions/final_gate.py",
    )
    assert result["boundaries"] == ["ce_to_builder", "final_gate"]


def test_main_or_explicit_full_validation_selects_all_boundaries():
    assert classify(force_all=True)["boundaries"] == ALL
