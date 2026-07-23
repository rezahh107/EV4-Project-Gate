from __future__ import annotations

import ev4_transition.validator_runner as validator_runner


def test_nested_synthetic_architect_source_cannot_authorize_ce_handoff(monkeypatch):
    monkeypatch.setattr(validator_runner, "execute_ce_validator", lambda *args, **kwargs: object())
    monkeypatch.setattr(validator_runner, "diagnostics_from_outcome", lambda outcome: [])
    source_bundle = {
        "synthetic": False,
        "payload": {
            "data": {
                "evidence": {
                    "source": {"type": "synthetic_fixture"},
                }
            }
        },
    }

    diagnostics = validator_runner.run_ce_validator("/unused", {}, source_bundle)

    assert any(item.code == "PG_A2C_SYNTHETIC_OPERATIONAL_HANDOFF_FORBIDDEN" for item in diagnostics)
    assert any(item.severity == "insufficient_evidence" for item in diagnostics)
