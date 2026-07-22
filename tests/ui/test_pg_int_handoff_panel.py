from __future__ import annotations

import json
from pathlib import Path

import pytest

import ev4_transition.producer_integration.facade as facade
import ev4_transition.ui.handoff_app as handoff_app
from ev4_transition.io.safe_publication import (
    publish_staged_json,
    resolve_publication_paths,
    stage_canonical_json,
)
from ev4_transition.service.producer_handoff import ProducerHandoffResponse


ROOT = Path(__file__).resolve().parents[2]


def _accepted_intake(transition: str) -> dict:
    stage = "architect" if transition == "architect-to-ce" else "ce"
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": "accepted",
        "producer": {
            "stage": stage,
            "repository": (
                "rezahh107/EV4-Architect-Repo"
                if stage == "architect"
                else "rezahh107/EV4-Constructability-Engineer-Repo"
            ),
        },
        "resolved_transition": transition,
        "diagnostics": [],
        "handoff_allowed": False,
    }


def _publishing_transition(captured: dict):
    def fake_transition(name, artifact, **kwargs):
        output, receipt = resolve_publication_paths(
            source_path=kwargs["snapshot"].path,
            output_path=kwargs["output_path"],
            receipt_path=kwargs["receipt_path"],
        )
        output_publication = publish_staged_json(
            stage_canonical_json(output, {"kind": "next-stage", "transition": name})
        )
        receipt_publication = publish_staged_json(
            stage_canonical_json(receipt, {"kind": "receipt", "transition": name})
        )
        captured.update(name=name, output=output, receipt=receipt)
        artifact_key = "ce_input" if name == "architect-to-ce" else "builder_input"
        return {
            "status": "accepted",
            "resolved_transition": name,
            "handoff_allowed": True,
            "diagnostics": [],
            "downstream_artifact": {
                "status": "published_verified",
                "path": str(output),
            },
            "receipt": {
                "status": "published_verified",
                "path": str(receipt),
            },
            "publication": {
                artifact_key: output_publication,
                "receipt": receipt_publication,
            },
        }

    return fake_transition


def test_ui_detects_architect_and_ce_routes_without_operator_transition_choice():
    architect = handoff_app.inspect_uploaded_route(
        str(ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json"),
        str(ROOT),
    )
    ce = handoff_app.inspect_uploaded_route(
        str(ROOT / "fixtures/producer-emitted/valid/ce-export.v1.json"),
        str(ROOT),
    )

    assert architect["resolved_transition"] == "architect-to-ce"
    assert architect["routing"]["required_repository_roles"] == ["architect", "ce"]
    assert ce["resolved_transition"] == "ce-to-builder"
    assert ce["routing"]["required_repository_roles"] == ["ce", "builder"]


def test_route_summary_escapes_untrusted_values():
    rendered = handoff_app.route_summary_html(
        {
            "status": "invalid",
            "resolved_transition": "<script>alert(1)</script>",
            "routing": {"producer_stage": "architect", "target_stage": "ce"},
            "user_message_fa": "<img src=x onerror=alert(1)>",
        }
    )

    assert "<script>" not in rendered
    assert "<img" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "&lt;img" in rendered


@pytest.mark.parametrize(
    (
        "transition",
        "target",
        "architect_required",
        "builder_required",
        "output_name",
        "receipt_name",
    ),
    [
        (
            "architect-to-ce",
            "ce-intake",
            True,
            False,
            "ce-input.json",
            "project-gate-a2c-receipt.json",
        ),
        (
            "ce-to-builder",
            "builder-intake",
            False,
            True,
            "builder-input.json",
            "project-gate-c2b-receipt.json",
        ),
    ],
)
def test_ui_empty_output_uses_unique_directory_inside_real_publication_workspace(
    monkeypatch,
    tmp_path: Path,
    transition: str,
    target: str,
    architect_required: bool,
    builder_required: bool,
    output_name: str,
    receipt_name: str,
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "producer.json"
    source.write_text(json.dumps({"handoff": {"target": target}}), encoding="utf-8")
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    builder = tmp_path / "builder"
    ce.mkdir()
    if architect_required:
        architect.mkdir()
    if builder_required:
        builder.mkdir()
    captured: dict = {}

    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake(transition),
    )
    monkeypatch.setattr(
        facade,
        "transition_producer_export",
        _publishing_transition(captured),
    )

    status, diagnostics, preview, downloads = handoff_app.run_uploaded_handoff(
        str(source),
        str(ROOT),
        str(architect) if architect_required else None,
        str(ce),
        str(builder) if builder_required else None,
        "",
    )

    payload = json.loads(preview)
    output = Path(captured["output"])
    receipt = Path(captured["receipt"])
    assert "پذیرفته شد" in status
    assert diagnostics == []
    assert payload["status"] == "accepted"
    assert output.name == output_name
    assert receipt.name == receipt_name
    assert output.parent == receipt.parent
    assert output.parent.name.startswith("run-")
    assert output.is_relative_to(tmp_path)
    assert receipt.is_relative_to(tmp_path)
    assert not any(
        item.get("code", "").endswith("OUTPUT_OUTSIDE_WORKSPACE")
        for item in payload["diagnostics"]
    )
    assert downloads == [str(output), str(receipt)]


def test_ui_returns_standalone_output_and_receipt_downloads(monkeypatch, tmp_path: Path):
    output = tmp_path / "ce-input.json"
    receipt = tmp_path / "project-gate-a2c-receipt.json"
    output.write_text("{}", encoding="utf-8")
    receipt.write_text("{}", encoding="utf-8")
    response = ProducerHandoffResponse(
        status="accepted",
        resolved_transition="architect-to-ce",
        routing={"producer_stage": "architect", "target_stage": "ce"},
        diagnostics=[],
        engine_result={
            "status": "accepted",
            "resolved_transition": "architect-to-ce",
            "handoff_allowed": True,
            "diagnostics": [],
            "operator_artifacts": {
                "next_stage": {"path": str(output), "downloadable": True},
                "receipt": {"path": str(receipt), "downloadable": True},
            },
        },
        artifact_metadata={
            "next_stage": {"path": str(output), "downloadable": True},
            "receipt": {"path": str(receipt), "downloadable": True},
        },
        download_paths=[str(output), str(receipt)],
        user_message_fa="accepted",
        next_action_fa="فایل ce-input.json را به CE بدهید.",
    )
    monkeypatch.setattr(handoff_app, "run_producer_handoff_request", lambda request: response)

    status, diagnostics, preview, downloads = handoff_app.run_uploaded_handoff(
        "architect-project-gate.json",
        str(ROOT),
        "/local/architect",
        "/local/ce",
        None,
        str(tmp_path),
    )

    assert "پذیرفته شد" in status
    assert diagnostics == []
    assert "architect-to-ce" in preview
    assert downloads == [str(output), str(receipt)]


def test_ui_does_not_offer_blocked_next_stage_artifact(monkeypatch, tmp_path: Path):
    receipt = tmp_path / "project-gate-c2b-receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    response = ProducerHandoffResponse(
        status="insufficient_evidence",
        resolved_transition="ce-to-builder",
        routing={"producer_stage": "ce", "target_stage": "builder"},
        diagnostics=[
            {
                "code": "PG_C2B_SOURCE_HANDOFF_NOT_ALLOWED",
                "severity": "insufficient_evidence",
                "path": "$.handoff.allowed",
                "message": "blocked",
            }
        ],
        engine_result={
            "status": "insufficient_evidence",
            "resolved_transition": "ce-to-builder",
            "handoff_allowed": False,
            "diagnostics": [],
        },
        artifact_metadata={
            "next_stage": {
                "path": str(tmp_path / "builder-input.json"),
                "downloadable": False,
            },
            "receipt": {"path": str(receipt), "downloadable": True},
        },
        download_paths=[str(receipt)],
        user_message_fa="blocked",
        next_action_fa="diagnostics را بررسی کنید.",
    )
    monkeypatch.setattr(handoff_app, "run_producer_handoff_request", lambda request: response)

    status, diagnostics, preview, downloads = handoff_app.run_uploaded_handoff(
        "ce-project-gate.json",
        str(ROOT),
        None,
        "/local/ce",
        "/local/builder",
        str(tmp_path),
    )

    assert "شواهد کافی نیست" in status
    assert diagnostics
    assert "handoff_allowed" in preview
    assert downloads == [str(receipt)]


def test_ui_invalid_project_gate_path_returns_structured_result_without_traceback(
    tmp_path: Path,
):
    source = tmp_path / "producer.json"
    source.write_text("{}", encoding="utf-8")

    status, diagnostics, preview, downloads = handoff_app.run_uploaded_handoff(
        str(source),
        str(tmp_path / "missing-project-gate"),
        None,
        None,
        None,
        "",
    )

    payload = json.loads(preview)
    assert "نامعتبر" in status
    assert diagnostics
    assert payload["status"] == "invalid"
    assert payload["diagnostics"][0]["code"] == "PG_INT_PROJECT_GATE_REPO_INVALID"
    assert downloads == []
