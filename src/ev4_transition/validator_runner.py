from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .canonical_json import write_canonical_json
from .diagnostics import Diagnostic, diagnostic


def run_architect_validator(repo_root: str | Path, payload: dict[str, Any]) -> list[Diagnostic]:
    return _run_validator(
        repo_root=repo_root,
        script_rel="scripts/check-architect-stage-payload.py",
        payload=payload,
        code="PG_A2C_ARCHITECT_OFFICIAL_VALIDATOR_FAILED",
        source_bundle=None,
    )


def run_ce_validator(repo_root: str | Path, payload: dict[str, Any], source_bundle: dict[str, Any]) -> list[Diagnostic]:
    return _run_validator(
        repo_root=repo_root,
        script_rel="scripts/validate-ce-architect-stage-intake.py",
        payload=payload,
        code="PG_A2C_CE_OFFICIAL_VALIDATOR_FAILED",
        source_bundle=source_bundle,
    )


def _run_validator(
    repo_root: str | Path,
    script_rel: str,
    payload: dict[str, Any],
    code: str,
    source_bundle: dict[str, Any] | None,
) -> list[Diagnostic]:
    root = Path(repo_root).resolve()
    script = root / script_rel
    if not script.exists():
        return [diagnostic(code, "error", "Official validator script is missing.", "$$".replace("$$", "$"), validator=str(script))]
    with tempfile.TemporaryDirectory(prefix="ev4-pg-validator-") as td:
        temp_root = Path(td)
        payload_path = temp_root / "payload.json"
        write_canonical_json(payload_path, payload)
        command = [sys.executable, str(script), "--repo-root", str(root), "--file", str(payload_path), "--format", "json"]
        if source_bundle is not None:
            source_bundle_path = temp_root / "source-bundle.json"
            write_canonical_json(source_bundle_path, source_bundle)
            command.extend(["--source-bundle", str(source_bundle_path)])
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PYTHONHASHSEED": "0",
            **{k: v for k, v in os.environ.items() if k in {"PATH", "PYTHONPATH", "HOME"}},
        }
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=30,
        )
    return _diagnostics_from_completed_process(completed, code)


def _diagnostics_from_completed_process(completed: subprocess.CompletedProcess[str], code: str) -> list[Diagnostic]:
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = None

    if completed.returncode == 0 and isinstance(result, dict) and result.get("status") == "valid":
        return []
    if completed.returncode == 2 and isinstance(result, dict) and result.get("status") == "insufficient_evidence":
        return [diagnostic(code, "insufficient_evidence", "Official validator returned insufficient evidence.", "$$".replace("$$", "$"), validator_status=result.get("status"), diagnostics=result.get("diagnostics", []))]

    details: dict[str, Any] = {"returncode": completed.returncode, "stderr": completed.stderr[:1000]}
    if isinstance(result, dict):
        details["validator_result"] = result
    else:
        details["stdout"] = completed.stdout[:1000]
    return [diagnostic(code, "error", "Official validator rejected the payload.", "$$".replace("$$", "$"), **details)]
