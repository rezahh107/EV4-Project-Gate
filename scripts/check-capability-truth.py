#!/usr/bin/env python3
"""Validate the single machine-readable Project Gate capability authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CAPABILITY_PATH = Path("src/ev4_transition/data/capability-status.v1.json")
ACTIVE_DOCS = (Path("README.md"), Path("AGENTS.md"))
REQUIRED_CAPABILITIES = {
    "architect_to_ce",
    "ce_to_builder",
    "builder_to_responsive",
    "final_evidence_gate",
    "producer_emitted_gate_artifact",
    "user_interface",
}
REQUIRED_PUBLIC_TRANSITIONS = {
    "architect-to-ce",
    "ce-to-builder",
    "builder-to-responsive",
    "final-evidence-gate",
}
FORBIDDEN_DUPLICATE_AUTHORITY_REFERENCES = {
    "docs/IMPLEMENTATION_STATUS.yaml",
    "docs/EV4_SHARED_CONTRACTS_STATUS.md",
}


def _reject_non_finite(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _load_authority(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite)
    if not isinstance(value, dict):
        raise ValueError("top-level capability authority must be an object")
    return value


def check_repository(root: Path) -> list[str]:
    failures: list[str] = []
    authority_path = root / CAPABILITY_PATH
    try:
        authority = _load_authority(authority_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{CAPABILITY_PATH}: {exc}"]

    capabilities = authority.get("capabilities")
    if not isinstance(capabilities, dict):
        failures.append(f"{CAPABILITY_PATH}: capabilities must be an object")
    else:
        missing = sorted(REQUIRED_CAPABILITIES - set(capabilities))
        if missing:
            failures.append(f"{CAPABILITY_PATH}: missing capabilities: {', '.join(missing)}")
        for capability_id, status in sorted(capabilities.items()):
            if not isinstance(status, dict) or not status:
                failures.append(f"{CAPABILITY_PATH}: {capability_id} must be a non-empty object")

    public_transitions = authority.get("public_cli_transitions")
    if not isinstance(public_transitions, list) or any(not isinstance(item, str) for item in public_transitions):
        failures.append(f"{CAPABILITY_PATH}: public_cli_transitions must be an array of strings")
    elif set(public_transitions) != REQUIRED_PUBLIC_TRANSITIONS:
        failures.append(
            f"{CAPABILITY_PATH}: public_cli_transitions must equal {sorted(REQUIRED_PUBLIC_TRANSITIONS)}"
        )

    for relative_path in ACTIVE_DOCS:
        path = root / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"{relative_path}: {exc}")
            continue
        if str(CAPABILITY_PATH) not in text:
            failures.append(f"{relative_path}: must identify {CAPABILITY_PATH} as capability authority")
        for forbidden in sorted(FORBIDDEN_DUPLICATE_AUTHORITY_REFERENCES):
            if forbidden in text:
                failures.append(f"{relative_path}: references removed duplicate authority {forbidden}")

    return sorted(failures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    failures = check_repository(Path(args.root))
    if failures:
        print("Capability authority validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Capability authority is valid: {CAPABILITY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
