from __future__ import annotations

import json
from pathlib import Path

from ev4_transition.producer_integration.intake import transition_producer_export
from ev4_transition.producer_integration.join_preflight import (
    REQUIRED_EVIDENCE_STATE,
    validate_join_evidence_packet,
)

ROOT = Path(__file__).resolve().parents[2]


def _valid_packet() -> dict:
    return {
        "prompt_5_ready": True,
        "blocking_insufficient_evidence": [],
        "ready_decision": "ready",
        "evidence_state": dict(REQUIRED_EVIDENCE_STATE),
        "prompt_5_substitution": {
            marker: {"replacement_status": "verified"}
            for marker in (
                "FROM_PROMPT_1_FINAL_REPORT",
                "FROM_PROMPT_2_FINAL_REPORT",
                "FROM_PROMPT_3_FINAL_REPORT",
                "FROM_PROMPT_4_FINAL_REPORT",
            )
        },
    }


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_explicit_valid_legacy_packet_is_supported(tmp_path: Path) -> None:
    packet = tmp_path / "legacy-ready.json"
    _write(packet, _valid_packet())
    result = validate_join_evidence_packet(packet)
    assert result["status"] == "passed"
    assert result["authorization_effect"] == "legacy_explicit_caller_only"


def test_explicit_missing_legacy_packet_fails_closed(tmp_path: Path) -> None:
    result = validate_join_evidence_packet(tmp_path / "missing.json")
    assert result["status"] == "blocked"
    assert result["prompt_5_execution_allowed"] is False


def test_explicit_malformed_legacy_packet_fails_closed(tmp_path: Path) -> None:
    packet = tmp_path / "malformed.json"
    packet.write_text("{", encoding="utf-8")
    result = validate_join_evidence_packet(packet)
    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "PG-P05-JOIN-EVIDENCE-NOT-READY"


def test_explicit_not_ready_legacy_packet_fails_closed(tmp_path: Path) -> None:
    packet = tmp_path / "blocked.json"
    _write(packet, {"prompt_5_ready": False, "blocking_insufficient_evidence": ["x"], "ready_decision": "blocked"})
    result = validate_join_evidence_packet(packet)
    assert result["status"] == "blocked"
    assert result["prompt_5_execution_allowed"] is False


def test_valid_legacy_packet_cannot_bypass_runtime_evidence(tmp_path: Path) -> None:
    packet = tmp_path / "legacy-ready.json"
    _write(packet, _valid_packet())
    artifact = json.loads((ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json").read_text(encoding="utf-8"))
    result = transition_producer_export(
        "architect-to-ce",
        artifact,
        join_packet_path=packet,
    )
    assert result["join_evidence_preflight"]["status"] == "passed"
    assert result["status"] == "insufficient_evidence"
    assert result["handoff_allowed"] is False
    assert any(item["code"] == "PG_A2C_RUNTIME_EVIDENCE_REQUIRED" for item in result["diagnostics"])
