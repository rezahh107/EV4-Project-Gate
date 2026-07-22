#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Iterable

from ev4_transition.evidence_packaging import EvidencePackagingError, package_source_evidence


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package exact-head source evidence outside the checkout tree.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--tested-head-sha", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = package_source_evidence(
            args.source,
            args.archive,
            args.manifest,
            tested_head_sha=args.tested_head_sha,
        )
    except (EvidencePackagingError, OSError) as exc:
        print(json.dumps({"packaging_result": "failure", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
