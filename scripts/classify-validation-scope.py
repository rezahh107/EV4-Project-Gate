#!/usr/bin/env python3
"""Fail-safe validation scope classifier for Project Gate CI.

The full internal test/build/install suite is always executed by CI. This module
only determines which external owner-boundary checks are additionally required.
Unknown or shared paths select every boundary.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
from typing import Iterable

BOUNDARIES = (
    "architect_to_ce",
    "ce_to_builder",
    "builder_to_responsive",
    "final_gate",
    "kernel_intake",
    "producer_integration",
)

SHARED_PATTERNS = (
    ".github/workflows/**",
    "scripts/classify-validation-scope.py",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "src/ev4_transition/service/**",
    "src/ev4_transition/models*",
    "src/ev4_transition/canonical*",
    "src/ev4_transition/cli*",
    "src/ev4_transition/runners/**",
    "src/ev4_transition/bundle_validator.py",
    "src/ev4_transition/contract_source.py",
    "src/ev4_transition/diagnostics.py",
    "schemas/stage-bundle/**",
    "schemas/transition-result/**",
    "schemas/diagnostic/**",
    "schemas/lock-manifest/**",
    "tests/service/**",
    "tests/boundary/**",
    "tests/e2e/**",
    "tests/personal_use/**",
    "tests/packaging/**",
    "tests/test_cli.py",
    "tests/test_canonical_json.py",
    "tests/test_bundle_validator.py",
    "tests/ci/**",
)

BOUNDARY_PATTERNS: dict[str, tuple[str, ...]] = {
    "architect_to_ce": (
        "src/ev4_transition/architect_to_ce.py",
        "src/ev4_transition/transitions/architect_to_ce.py",
        "contracts/locks/architect-to-ce-transition.v1.lock.json",
        "schemas/architect-to-ce-transition-result/**",
        "scripts/verify-architect-to-ce-lock.py",
        "scripts/transition-smoke.py",
        "scripts/pg-a2c-current-head-smoke.py",
        "tests/test_architect_to_ce_transition.py",
        "tests/producer_integration/test_pg_a2c_*.py",
    ),
    "ce_to_builder": (
        "src/ev4_transition/transitions/ce_to_builder.py",
        "contracts/locks/ce-to-builder-transition.v1.lock.json",
        "schemas/ce-to-builder-transition-result/**",
        "scripts/compute-ce-to-builder-lock.py",
        "scripts/verify-ce-to-builder-lock.py",
        "scripts/ce-to-builder-smoke.py",
        "tests/transitions/test_ce_to_builder.py",
        "tests/producer_integration/test_pg_c2b_*.py",
    ),
    "builder_to_responsive": (
        "src/ev4_transition/transitions/builder_to_responsive.py",
        "src/ev4_transition/runners/responsive_tools.py",
        "contracts/locks/builder-to-responsive-transition.v1.lock.json",
        "schemas/builder-to-responsive-transition-result/**",
        "scripts/compute-builder-to-responsive-lock.py",
        "tests/transitions/test_builder_to_responsive.py",
    ),
    "final_gate": (
        "src/ev4_transition/transitions/final_gate.py",
        "src/ev4_transition/reports/decision_receipts.py",
        "contracts/locks/final-gate.v1.lock.json",
        "schemas/final-gate-result/**",
        "scripts/compute-final-gate-lock.py",
        "tests/transitions/test_final_gate.py",
        "tests/reports/test_decision_receipts.py",
        "tests/test_cli_final_gate_kernel_repo.py",
    ),
    "kernel_intake": (
        "src/ev4_transition/kernel_decision_*.py",
        "src/ev4_transition/runners/kernel_decision.py",
        "contracts/locks/kernel-decision-intake.v1.lock.json",
        "schemas/kernel-decision-intake/**",
        "schemas/kernel-decision-intake-result/**",
        "scripts/compute-kernel-decision-intake-lock.py",
        "scripts/kernel-decision-intake-bridge.mjs",
        "planning/DECISION_ESCAPE_ROUTES.yml",
        "planning/decision-escape-routes.schema.json",
        "tests/kernel_decision_intake/**",
        "tests/planning/test_decision_escape_routes_schema.py",
    ),
    "producer_integration": (
        "src/ev4_transition/producer_integration/**",
        "src/ev4_transition/producer_gate_export.py",
        "src/ev4_transition/service/producer_handoff.py",
        "contracts/producer-adoption/**",
        "contracts/transition-targets/**",
        "schemas/producer-adoption/**",
        "schemas/transition-targets/**",
        "tests/producer_integration/**",
    ),
}

DOCS_ONLY_PATTERNS = (
    "docs/**",
    "README.md",
    "AGENTS.md",
)


def _matches(path: str, patterns: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def classify_paths(paths: Iterable[str], *, force_all: bool = False) -> dict[str, object]:
    normalized = sorted({p.replace("\\", "/").strip().lstrip("./") for p in paths if p.strip()})
    selected: set[str] = set()
    reasons: list[str] = []
    run_all = force_all

    if force_all:
        reasons.append("explicit_full_validation")

    for path in normalized:
        if _matches(path, SHARED_PATTERNS):
            run_all = True
            reasons.append(f"shared:{path}")
            continue

        matched = {boundary for boundary, patterns in BOUNDARY_PATTERNS.items() if _matches(path, patterns)}
        if matched:
            selected.update(matched)
            reasons.extend(f"{boundary}:{path}" for boundary in sorted(matched))
            continue

        if _matches(path, DOCS_ONLY_PATTERNS):
            reasons.append(f"docs_only:{path}")
            continue

        run_all = True
        reasons.append(f"unknown:{path}")

    if run_all:
        selected = set(BOUNDARIES)

    selected_list = [boundary for boundary in BOUNDARIES if boundary in selected]
    return {
        "run_all": run_all,
        "boundaries": selected_list,
        "boundary_count": len(selected_list),
        "changed_paths": normalized,
        "reasons": reasons,
    }


def _write_github_outputs(result: dict[str, object], output_path: Path) -> None:
    boundaries = list(result["boundaries"])
    with output_path.open("a", encoding="utf-8") as output:
        output.write(f"run_all={'true' if result['run_all'] else 'false'}\n")
        output.write(f"boundaries_json={json.dumps(boundaries, separators=(',', ':'))}\n")
        output.write(f"boundary_count={result['boundary_count']}\n")
        for boundary in BOUNDARIES:
            output.write(f"{boundary}={'true' if boundary in boundaries else 'false'}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed repository paths")
    parser.add_argument("--paths-file", type=Path)
    parser.add_argument("--force-all", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    paths = list(args.paths)
    if args.paths_file:
        paths.extend(args.paths_file.read_text(encoding="utf-8").splitlines())

    result = classify_paths(paths, force_all=args.force_all)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    output_path = args.github_output
    if output_path is None and os.environ.get("GITHUB_OUTPUT"):
        output_path = Path(os.environ["GITHUB_OUTPUT"])
    if output_path is not None:
        _write_github_outputs(result, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
