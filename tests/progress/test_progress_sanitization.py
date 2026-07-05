from __future__ import annotations

from pathlib import Path

import pytest

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.progress import ProgressEvent, ProgressSanitizationError, canonical_result_hash_without_progress, sanitize_progress_event


def test_progress_event_contains_token_fails() -> None:
    with pytest.raises(ProgressSanitizationError):
        sanitize_progress_event(ProgressEvent("x", "token leaked", "running"))


def test_progress_event_contains_raw_env_fails() -> None:
    with pytest.raises(ProgressSanitizationError):
        sanitize_progress_event(ProgressEvent("x", "running", "running", details={"env": {"PATH": "/tmp"}}))


def test_progress_event_uses_relative_path_by_default(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "scripts" / "validator.py"
    target.parent.mkdir()
    target.write_text("", encoding="utf-8")
    event = sanitize_progress_event(ProgressEvent("run", "started", "running", repo_path=str(target)), repo_root=repo)
    assert event["repo_path"] == "scripts/validator.py"


def test_progress_event_does_not_affect_canonical_result_hash() -> None:
    result = {"status": "insufficient_evidence", "diagnostics": []}
    with_progress = {**result, "progress_events": [{"event_type": "run", "status": "running"}]}
    assert canonical_result_hash_without_progress(with_progress) == canonical_sha256(result)
