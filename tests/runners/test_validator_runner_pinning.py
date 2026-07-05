from __future__ import annotations

from pathlib import Path

from ev4_transition import validator_runner
from ev4_transition.diagnostics import diagnostic
from ev4_transition.external_lock import ARCHITECT_COMMIT, ARCHITECT_REPO, CE_COMMIT, CE_REPO


class _Outcome:
    diagnostics = []


def test_architect_validator_uses_pinned_lock_commit(monkeypatch) -> None:
    calls = []

    def fake_execute_validator(**kwargs):
        calls.append(kwargs)
        return _Outcome()

    monkeypatch.setattr(validator_runner, "execute_validator", fake_execute_validator)
    validator_runner.run_architect_validator(Path("/tmp/architect"), {"payload": True})

    assert calls[0]["owner_repo"] == ARCHITECT_REPO
    assert calls[0]["owner_commit"] == ARCHITECT_COMMIT
    assert calls[0]["owner_commit"] != "unknown"
    assert len(calls[0]["owner_commit"]) == 40


def test_ce_validator_uses_pinned_lock_commit(monkeypatch) -> None:
    calls = []

    def fake_execute_validator(**kwargs):
        calls.append(kwargs)
        return _Outcome()

    monkeypatch.setattr(validator_runner, "execute_validator", fake_execute_validator)
    validator_runner.run_ce_validator(Path("/tmp/ce"), {"payload": True}, {"bundle": True})

    assert calls[0]["owner_repo"] == CE_REPO
    assert calls[0]["owner_commit"] == CE_COMMIT
    assert calls[0]["owner_commit"] != "unknown"
    assert len(calls[0]["owner_commit"]) == 40
