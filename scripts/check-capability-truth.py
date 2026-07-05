#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

CAPABILITY_PATH = Path("src/ev4_transition/data/capability-status.v1.json")
IMPLEMENTATION_STATUS_PATH = Path("docs/IMPLEMENTATION_STATUS.yaml")
ACTIVE_STATUS_DOCS = (Path("README.md"), Path("AGENTS.md"))
CURRENT_STATUS_HEADING = "## Current Status"
YAML_FENCE = "```yaml"
CLOSING_FENCE = "```"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level YAML value must be a mapping")
    return value


def _load_current_status(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        heading_index = lines.index(CURRENT_STATUS_HEADING)
    except ValueError as exc:
        raise ValueError(f"{path}: missing {CURRENT_STATUS_HEADING!r} heading") from exc

    fence_index = next(
        (index for index in range(heading_index + 1, len(lines)) if lines[index] == YAML_FENCE),
        None,
    )
    if fence_index is None:
        raise ValueError(f"{path}: missing YAML fence after {CURRENT_STATUS_HEADING!r}")

    closing_index = next(
        (index for index in range(fence_index + 1, len(lines)) if lines[index] == CLOSING_FENCE),
        None,
    )
    if closing_index is None:
        raise ValueError(f"{path}: missing closing fence for Current Status YAML")

    value = yaml.safe_load("\n".join(lines[fence_index + 1 : closing_index]))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: Current Status YAML must be a mapping")
    return value


def _compare_capability_subset(
    source: dict[str, Any],
    target: dict[str, Any],
    label: str,
) -> list[str]:
    failures: list[str] = []
    for capability_id in sorted(source):
        expected = source[capability_id]
        actual = target.get(capability_id)
        if not isinstance(expected, dict):
            failures.append(f"capability source {capability_id!r} must be an object")
            continue
        if not isinstance(actual, dict):
            failures.append(f"{label}: missing capability {capability_id!r}")
            continue
        for key in sorted(expected):
            if actual.get(key) != expected[key]:
                failures.append(
                    f"{label}: {capability_id}.{key} expected {expected[key]!r}, "
                    f"got {actual.get(key)!r}"
                )
    return failures


def check_repository(root: Path) -> list[str]:
    failures: list[str] = []
    try:
        capability = _load_json(root / CAPABILITY_PATH)
        implementation = _load_yaml(root / IMPLEMENTATION_STATUS_PATH)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return [str(exc)]

    source_capabilities = capability.get("capabilities")
    if not isinstance(source_capabilities, dict):
        return [f"{CAPABILITY_PATH}: capabilities must be an object"]

    implementation_capabilities = implementation.get("capabilities")
    if not isinstance(implementation_capabilities, dict):
        failures.append(f"{IMPLEMENTATION_STATUS_PATH}: capabilities must be a mapping")
    else:
        failures.extend(
            _compare_capability_subset(
                source_capabilities,
                implementation_capabilities,
                str(IMPLEMENTATION_STATUS_PATH),
            )
        )

    expected_public_cli = capability.get("public_cli_transitions")
    if not isinstance(expected_public_cli, list):
        failures.append(f"{CAPABILITY_PATH}: public_cli_transitions must be an array")
        expected_public_cli = []

    for relative_path in ACTIVE_STATUS_DOCS:
        try:
            current_status = _load_current_status(root / relative_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(str(exc))
            continue
        actual_capabilities = current_status.get("capabilities")
        if actual_capabilities != source_capabilities:
            failures.append(
                f"{relative_path}: Current Status capabilities must exactly match {CAPABILITY_PATH}"
            )
        if current_status.get("public_cli_transitions") != expected_public_cli:
            failures.append(
                f"{relative_path}: public_cli_transitions must exactly match {CAPABILITY_PATH}"
            )

    return sorted(failures)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate active capability truth across machine-readable status and active docs."
    )
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    failures = check_repository(Path(args.root))
    if failures:
        print("Capability truth drift detected:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Capability truth is aligned across source, implementation status, README, and AGENTS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
