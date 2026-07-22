from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "ev4-project-gate-operator-settings.v1"
DEFAULT_SETTINGS: dict[str, str] = {
    "schema_version": SCHEMA_VERSION,
    "project_gate_repo_path": r"E:\GitHub\EV4 Shared Contracts",
    "architect_repo_path": r"E:\GitHub\EV4-Architect-Repo",
    "ce_repo_path": r"E:\GitHub\EV4 Constructability Engineer Repo",
    "builder_repo_path": r"E:\GitHub\Builder Assistant",
    "responsive_repo_path": r"E:\GitHub\EV4 Responsive Architect",
    "kernel_repo_path": r"E:\GitHub\EV4-Decision-Kernel",
    "default_output_directory": r"E:\GitHub\EV4 Project Gate Outputs",
    "default_transition": "Architect → CE",
    "default_acquisition_mode": "producer_emitted_gate_artifact",
}


def settings_path() -> Path:
    appdata = os.environ.get("APPDATA")
    root = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return root / "EV4-Project-Gate" / "operator-settings.json"


def default_settings() -> dict[str, str]:
    return deepcopy(DEFAULT_SETTINGS)


def load_settings(path: str | Path | None = None) -> dict[str, str]:
    target = Path(path) if path is not None else settings_path()
    defaults = default_settings()
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return defaults
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        return defaults
    for key in defaults:
        observed = value.get(key)
        if isinstance(observed, str) and observed.strip():
            defaults[key] = observed.strip()
    return defaults


def save_settings(value: dict[str, Any], path: str | Path | None = None) -> Path:
    target = Path(path) if path is not None else settings_path()
    payload = default_settings()
    for key in payload:
        observed = value.get(key)
        if isinstance(observed, str) and observed.strip():
            payload[key] = observed.strip()
    payload["schema_version"] = SCHEMA_VERSION
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def reset_settings(path: str | Path | None = None) -> dict[str, str]:
    target = Path(path) if path is not None else settings_path()
    try:
        target.unlink()
    except FileNotFoundError:
        pass
    return default_settings()
