from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    files = sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file())
    payload = {"root": str(root), "files": [{"path": f, "sha256_file_bytes": sha256_file(root / f)} for f in files]}
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
