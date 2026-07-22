from __future__ import annotations

import json
from pathlib import Path

import pytest

import ev4_transition.cli_handoff as cli_handoff
import ev4_transition.producer_integration.facade as facade
import ev4_transition.service.producer_handoff as service_module
from ev4_transition.io.safe_publication import (
    publish_staged_json,
    resolve_publication_paths,
    stage_canonical_json,
)
from ev4_transition.service.models import RepoPaths
from ev4_transition.service.producer_handoff import (
    ProducerHandoffRequest,
    ProducerHandoffResponse,
    run_producer_handoff_request,
)


ROOT = Path(__file__).resolve().parents[2]


def _accepted_intake(transition: str) -> dict:
    stage = "architect" if transition == "architect-to-ce" else "ce"
    repository = (
        "rezahh107/EV4-Architect-Repo"
        if stage == "architect"
        else "rezahh107/EV4-Constructability-Engineer-Repo"
    )
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": "accepted",
        "producer": {"stage": stage, "repository": repository},
        "resolved_transition": transition,
        "diagnostics": [],
        "handoff_allowed": False,
    }


def _write_source(tmp_path: Path, target: str = "ce-intake") -> Path:
    source = tmp_path / "producer.json"
    source.write_text(json.dumps({"handoff": {"target": target}}), encoding="utf-8")
    return source


def _fake_publishing_transition(captured: dict):
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
        captured.update(name=name, artifact=artifact, kwargs=kwargs)
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


def test_inspection_routes_architect_and_ce_from_validated_export_data():
    architect = facade.inspect_producer_handoff(
        ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json",
        project_gate_repo=ROOT,
    )
    ce = facade.inspect_producer_handoff(
        ROOT / "fixtures/producer-emitted/valid/ce-export.v1.json",
        project_gate_repo=ROOT,
    )

    assert architect["status"] == "accepted"
    assert architect["resolved_transition"] == "architect-to-ce"
    assert architect["routing"]["required_repository_roles"] == ["architect", "ce"]
    assert architect["routing"]["filename_used_for_routing"] is False
    assert architect["routing"]["operator_transition_selection_used"] is False

    assert ce["status"] == "accepted"
    assert ce["resolved_transition"] == "ce-to-builder"
    assert ce["routing"]["required_repository_roles"] == ["ce", "builder"]


def test_filename_cannot_override_validated_architect_route(tmp_path: Path):
    misleading = tmp_path / "ce-project-gate.json"
    misleading.write_text(
        (ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = facade.inspect_producer_handoff(misleading, project_gate_repo=ROOT)

    assert result["status"] == "accepted"
    assert result["resolved_transition"] == "architect-to-ce"
    assert result["source_snapshot"]["filename"] == "ce-project-gate.json"
    assert result["routing"]["filename_used_for_routing"] is False


def test_unsupported_builder_route_fails_closed():
    result = facade.inspect_producer_handoff(
        ROOT / "fixtures/producer-emitted/valid/builder-export.v1.json",
        project_gate_repo=ROOT,
    )

    assert result["status"] == "invalid"
    assert result["failure_class"] == "unsupported"
    assert result["handoff_allowed"] is False
    assert any(item["code"] == "PG_INT_UNSUPPORTED_TRANSITION" for item in result["diagnostics"])


def test_producer_target_mismatch_fails_closed(monkeypatch, tmp_path: Path):
    source = _write_source(tmp_path)
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: {
            **_accepted_intake("architect-to-ce"),
            "producer": {
                "stage": "ce",
                "repository": "rezahh107/EV4-Constructability-Engineer-Repo",
            },
        },
    )

    result = facade.inspect_producer_handoff(source, project_gate_repo=ROOT)

    assert result["status"] == "invalid"
    assert result["failure_class"] == "unsupported"
    assert any(item["code"] == "PG_INT_PRODUCER_TARGET_MISMATCH" for item in result["diagnostics"])


@pytest.mark.parametrize(
    ("transition", "target", "required_fields", "output_name", "receipt_name"),
    [
        (
            "architect-to-ce",
            "ce-intake",
            ("architect_repo", "ce_repo"),
            "ce-input.json",
            "project-gate-a2c-receipt.json",
        ),
        (
            "ce-to-builder",
            "builder-intake",
            ("ce_repo", "builder_repo"),
            "builder-input.json",
            "project-gate-c2b-receipt.json",
        ),
    ],
)
def test_execution_requires_only_route_specific_repositories_and_preserves_filenames(
    monkeypatch,
    tmp_path: Path,
    transition: str,
    target: str,
    required_fields: tuple[str, str],
    output_name: str,
    receipt_name: str,
):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path, target)
    repos = {name: tmp_path / name for name in ("architect_repo", "ce_repo", "builder_repo")}
    for field in required_fields:
        repos[field].mkdir()
    captured: dict = {}

    monkeypatch.setattr(facade, "intake_producer_export", lambda *args, **kwargs: _accepted_intake(transition))
    monkeypatch.setattr(facade, "transition_producer_export", _fake_publishing_transition(captured))

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo=repos["architect_repo"] if "architect_repo" in required_fields else None,
        ce_repo=repos["ce_repo"],
        builder_repo=repos["builder_repo"] if "builder_repo" in required_fields else None,
        output_dir=tmp_path / "out",
    )

    assert result["status"] == "accepted"
    assert captured["name"] == transition
    assert Path(captured["kwargs"]["output_path"]).name == output_name
    assert Path(captured["kwargs"]["receipt_path"]).name == receipt_name
    assert captured["kwargs"]["architect_repo"] == (
        repos["architect_repo"] if "architect_repo" in required_fields else None
    )
    assert captured["kwargs"]["builder_repo"] == (
        repos["builder_repo"] if "builder_repo" in required_fields else None
    )


def test_explicit_valid_output_directory_is_preserved(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    explicit = tmp_path / "operator-selected"
    captured: dict = {}

    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )
    monkeypatch.setattr(facade, "transition_producer_export", _fake_publishing_transition(captured))

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo=architect,
        ce_repo=ce,
        output_dir=explicit,
    )

    assert result["status"] == "accepted"
    assert Path(captured["kwargs"]["output_path"]).parent.parent == explicit
    assert Path(captured["kwargs"]["receipt_path"]).parent.parent == explicit


@pytest.mark.parametrize(
    ("project_gate_repo", "expected_code"),
    [
        ("missing-project-gate", "PG_INT_PROJECT_GATE_REPO_INVALID"),
        ("~definitely_missing_user/project-gate", "PG_INT_PATH_EXPANSION_FAILED"),
    ],
)
def test_invalid_project_gate_paths_return_structured_results(
    tmp_path: Path,
    project_gate_repo: str,
    expected_code: str,
):
    source = _write_source(tmp_path)
    result = facade.inspect_producer_handoff(source, project_gate_repo=project_gate_repo)

    assert result["status"] == "invalid"
    assert result["handoff_allowed"] is False
    assert result["diagnostics"][0]["code"] == expected_code


def test_project_gate_regular_file_returns_structured_invalid(tmp_path: Path):
    source = _write_source(tmp_path)
    project_gate_file = tmp_path / "not-a-repo"
    project_gate_file.write_text("x", encoding="utf-8")

    result = facade.inspect_producer_handoff(source, project_gate_repo=project_gate_file)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_PROJECT_GATE_REPO_INVALID"


def test_missing_adoption_registry_returns_structured_invalid(tmp_path: Path):
    source = _write_source(tmp_path)
    root = tmp_path / "project-gate"
    targets = root / "contracts/transition-targets"
    targets.mkdir(parents=True)
    (targets / "ev4-transition-targets.v1.json").write_text('{"targets":[]}', encoding="utf-8")

    result = facade.inspect_producer_handoff(source, project_gate_repo=root)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE"
    assert result["diagnostics"][0]["details"]["file"].endswith("ev4-producer-adoption-set.v1.json")


def test_malformed_transition_targets_return_structured_invalid(tmp_path: Path):
    source = _write_source(tmp_path)
    root = tmp_path / "project-gate"
    registry = root / "contracts/producer-adoption"
    targets = root / "contracts/transition-targets"
    registry.mkdir(parents=True)
    targets.mkdir(parents=True)
    (registry / "ev4-producer-adoption-set.v1.json").write_text('{"producers":[]}', encoding="utf-8")
    (targets / "ev4-transition-targets.v1.json").write_text("{", encoding="utf-8")

    result = facade.inspect_producer_handoff(source, project_gate_repo=root)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE"
    assert result["diagnostics"][0]["details"]["error_type"] == "JSONDecodeError"


def test_missing_required_checkout_is_insufficient_evidence(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    ce = tmp_path / "ce"
    ce.mkdir()
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo=tmp_path / "missing-architect",
        ce_repo=ce,
    )

    assert result["status"] == "insufficient_evidence"
    assert result["diagnostics"][0]["code"] == "PG_INT_REPOSITORY_PATH_NOT_FOUND"


def test_required_checkout_regular_file_is_invalid(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    architect = tmp_path / "architect-file"
    architect.write_text("not a checkout", encoding="utf-8")
    ce = tmp_path / "ce"
    ce.mkdir()
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo=architect,
        ce_repo=ce,
    )

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_REPOSITORY_PATH_UNSAFE"


def test_unsafe_required_checkout_is_invalid(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    ce = tmp_path / "ce"
    ce.mkdir()
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo="~definitely_missing_user/architect",
        ce_repo=ce,
    )

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_REPOSITORY_PATH_UNSAFE"


def test_invalid_output_directory_returns_structured_invalid(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    invalid_output_dir = tmp_path / "file-not-directory"
    invalid_output_dir.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    result = facade.execute_producer_handoff(
        source,
        project_gate_repo=ROOT,
        architect_repo=architect,
        ce_repo=ce,
        output_dir=invalid_output_dir,
    )

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE"


@pytest.mark.parametrize("field", ["output_path", "receipt_path"])
def test_invalid_explicit_publication_paths_return_structured_invalid(
    monkeypatch,
    tmp_path: Path,
    field: str,
):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    kwargs = {
        "source_path": source,
        "project_gate_repo": ROOT,
        "architect_repo": architect,
        "ce_repo": ce,
        field: "~definitely_missing_user/output.json",
    }
    result = facade.execute_producer_handoff(**kwargs)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG_INT_ADVANCED_PUBLICATION_PATH_UNSUPPORTED"


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("schema_root", "missing-schemas", "PG_INT_SCHEMA_ROOT_INVALID"),
        ("lock_path", "missing-lock.json", "PG_INT_LOCK_PATH_INVALID"),
    ],
)
def test_invalid_schema_or_lock_path_returns_structured_invalid(
    monkeypatch,
    tmp_path: Path,
    field: str,
    value: str,
    expected_code: str,
):
    monkeypatch.chdir(tmp_path)
    source = _write_source(tmp_path)
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    monkeypatch.setattr(
        facade,
        "intake_producer_export",
        lambda *args, **kwargs: _accepted_intake("architect-to-ce"),
    )

    kwargs = {
        "source_path": source,
        "project_gate_repo": ROOT,
        "architect_repo": architect,
        "ce_repo": ce,
        field: value,
    }
    result = facade.execute_producer_handoff(**kwargs)

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == expected_code


def test_service_downloads_only_consumable_artifact_but_preserves_receipt(monkeypatch, tmp_path: Path):
    output = tmp_path / "builder-input.json"
    receipt = tmp_path / "project-gate-c2b-receipt.json"
    output.write_text("{}", encoding="utf-8")
    receipt.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        service_module,
        "execute_producer_handoff",
        lambda *args, **kwargs: {
            "status": "insufficient_evidence",
            "resolved_transition": "ce-to-builder",
            "handoff_allowed": False,
            "diagnostics": [],
            "routing": {"producer_stage": "ce", "target_stage": "builder"},
            "operator_artifacts": {
                "next_stage": {
                    "path": output,
                    "downloadable": False,
                    "publication_state": "published_verified",
                },
                "receipt": {
                    "path": receipt,
                    "downloadable": True,
                    "publication_state": "published_verified",
                },
                "next_action_fa": "diagnostics را بررسی کنید.",
            },
        },
    )

    response = run_producer_handoff_request(ProducerHandoffRequest(source_path="source.json"))

    assert response.status == "insufficient_evidence"
    assert response.download_paths == [str(receipt)]
    assert response.artifact_metadata["next_stage"]["downloadable"] is False


def test_service_invalid_path_returns_structured_response(tmp_path: Path):
    source = _write_source(tmp_path)
    response = run_producer_handoff_request(
        ProducerHandoffRequest(
            source_path=str(source),
            repo_paths=RepoPaths(project_gate_repo_path=str(tmp_path / "missing")),
        )
    )

    assert response.status == "invalid"
    assert response.diagnostics[0]["code"] == "PG_INT_PROJECT_GATE_REPO_INVALID"


def test_cli_invalid_path_emits_structured_result_without_traceback(tmp_path: Path, capsys):
    source = _write_source(tmp_path)

    exit_code = cli_handoff.main(
        [
            str(source),
            "--project-gate-repo",
            str(tmp_path / "missing"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert payload["status"] == "invalid"
    assert payload["diagnostics"][0]["code"] == "PG_INT_PROJECT_GATE_REPO_INVALID"


def test_cli_has_no_transition_selector_and_emits_structured_result(monkeypatch, capsys):
    response = ProducerHandoffResponse(
        status="accepted",
        resolved_transition="architect-to-ce",
        routing={"producer_stage": "architect", "target_stage": "ce"},
        diagnostics=[],
        engine_result={"status": "accepted", "handoff_allowed": True},
        artifact_metadata={
            "next_stage": {"path": "ce-input.json"},
            "receipt": {"path": "project-gate-a2c-receipt.json"},
        },
        download_paths=["ce-input.json", "project-gate-a2c-receipt.json"],
        user_message_fa="accepted",
        next_action_fa="فایل ce-input.json را به CE بدهید.",
    )
    monkeypatch.setattr(cli_handoff, "run_producer_handoff_request", lambda request: response)

    exit_code = cli_handoff.main(["producer-export.json", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["resolved_transition"] == "architect-to-ce"
    assert payload["routing"]["producer_stage"] == "architect"
