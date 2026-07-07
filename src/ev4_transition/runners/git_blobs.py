from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any


def git_blob_sha256_from_runner(repo: str | Path, commit_sha: str, path: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit_sha}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        return {
            "status": "insufficient_evidence",
            "diagnostic": {
                "code": "PG-P05-EXACT-BLOB-UNAVAILABLE",
                "severity": "insufficient_evidence",
                "path": "$.path",
                "message": "Exact Git blob bytes are unavailable; no mismatch is claimed.",
                "details": {"stderr": proc.stderr.decode("utf-8", "replace")},
                "repair_owner": "Project Gate",
            },
        }
    return {"status": "verified", "sha256": hashlib.sha256(proc.stdout).hexdigest()}
