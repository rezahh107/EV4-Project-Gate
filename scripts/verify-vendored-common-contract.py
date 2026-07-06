#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ev4_transition.canonical_json import load_json_file
from ev4_transition.common_contracts import verify_vendored_common_contract


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify exact local canonical and vendored common-contract bytes.")
    parser.add_argument("--lock", required=True)
    parser.add_argument("--canonical-root", required=True)
    parser.add_argument("--vendored-root", required=True)
    parser.add_argument("--project-gate-root", default=".")
    args = parser.parse_args()
    result = verify_vendored_common_contract(
        load_json_file(Path(args.lock)),
        canonical_root=Path(args.canonical_root),
        vendored_root=Path(args.vendored_root),
        repository_root=Path(args.project_gate_root),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
