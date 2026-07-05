#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)")


def iter_workflows(root: Path):
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted(path for path in workflows.iterdir() if path.suffix in {".yml", ".yaml"})


def check_file(path: Path) -> list[str]:
    failures: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = USES_RE.match(line)
        if not match:
            continue
        value = match.group(1).strip().strip('"\'')
        if "@" not in value:
            failures.append(f"{path}:{lineno}: uses entry has no ref: {value}")
            continue
        action, ref = value.rsplit("@", 1)
        if action.startswith("./") or action.startswith("../"):
            continue
        if not FULL_SHA_RE.fullmatch(ref):
            failures.append(f"{path}:{lineno}: external action must use a full 40-character commit SHA, got {value}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if GitHub workflow external actions are not pinned to full commit SHAs.")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root)
    failures: list[str] = []
    for workflow in iter_workflows(root):
        failures.extend(check_file(workflow))
    if failures:
        print("Mutable or unpinned GitHub Actions references found:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("All external GitHub Actions uses entries are pinned to full commit SHAs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
