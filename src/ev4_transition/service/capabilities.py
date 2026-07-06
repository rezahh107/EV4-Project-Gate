from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import load_json_file

_CAPABILITY_STATUS_PATH = Path(__file__).resolve().parents[1] / "data" / "capability-status.v1.json"


def get_capabilities() -> dict[str, Any]:
    """Return packaged capability truth without mutating the source file."""

    return deepcopy(load_json_file(_CAPABILITY_STATUS_PATH))
