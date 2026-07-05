#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.transitions.ce_to_builder import transition_from_local_paths


def _resolve_fixture_path(builder_repo: Path, requested: Path) -> tuple[Path, str]:
    builder_owned = builder_repo / "tests" / "valid" / "ce_builder_package_adapter_valid.json"
    if builder_owned.exists():
        return builder_owned, "builder_owned_adapter_valid_fixture"
    return requested, "requested_fixture_fallback"


def _extract_fixture_package(fixture: Any) -> Any:
    if isinstance(fixture, dict) and isinstance(fixture.get("builder_executable_package"), dict):
        return fixture["builder_executable_package"]
    if isinstance(fixture, dict) and isinstance(fixture.get("ce_builder_executable_package"), dict):
        return fixture["ce_builder_executable_package"]
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CE→Builder synthetic owner-fixture smoke through live owner tools.")
    parser.add_argument("--schema-root", default="schemas")
    parser.add_argument("--lock", default="contracts/locks/ce-to-builder-transition.v1.lock.json")
    parser.add_argument("--ce-repo", required=True)
    parser.add_argument("--builder-repo", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    fixture_path, fixture_source = _resolve_fixture_path(Path(args.builder_repo), Path(args.fixture))
    fixture = load_json_file(fixture_path)
    ce_package = _extract_fixture_package(fixture)
    result = transition_from_local_paths(
        ce_package,
        Path(args.schema_root),
        Path(args.lock),
        Path(args.ce_repo),
        Path(args.builder_repo),
        require_real_evidence=False,
    )
    report = {
        "status": result.get("status"),
        "accepted_requires": result.get("accepted_requires"),
        "diagnostics": result.get("diagnostics", []),
        "execution_record_keys": sorted((result.get("execution_records") or {}).keys()),
        "smoke_scope": "builder_owner_fixture_not_real_handoff_evidence",
        "fixture_path": str(fixture_path),
        "fixture_source": fixture_source,
    }
    print(canonical_dumps(report))
    return 0 if result.get("status") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
