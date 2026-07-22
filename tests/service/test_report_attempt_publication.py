from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from ev4_transition.io.safe_publication import PublicationError
from ev4_transition.producer_integration.path_environment import prepare_attempt_paths
from ev4_transition.service import run_gate_request, run_preflight
from ev4_transition.service.report_publication import publish_report_bundle
from ev4_transition.service.reports import build_report_bundle
from ev4_transition.ui.adapters import build_gate_request, run_operator_check
from ev4_transition.ui.app import open_output_folder

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json"


def _ready_request(tmp_path: Path):
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir(exist_ok=True)
    ce.mkdir(exist_ok=True)
    request = build_gate_request(
        "Architect → CE",
        uploaded_file=str(SOURCE),
        acquisition_mode="producer_emitted_gate_artifact",
        project_gate_repo_path=str(ROOT),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
        output_dir=str(tmp_path / "output-root"),
    )
    preflight = run_preflight(request)
    assert preflight.status == "ready"
    return request, preflight.request_fingerprint


def _failed_run(tmp_path: Path):
    request, token = _ready_request(tmp_path)
    return run_operator_check(
        "Architect → CE",
        uploaded_file=request.input_json_path,
        acquisition_mode=request.acquisition_mode,
        project_gate_repo_path=request.repo_paths.project_gate_repo_path,
        architect_repo_path=request.repo_paths.architect_repo_path,
        ce_repo_path=request.repo_paths.ce_repo_path,
        output_dir=request.output_dir,
        preflight_fingerprint=token,
    )


def test_failed_run_preserves_existing_root_reports_and_uses_attempt_directory(tmp_path: Path):
    root = tmp_path / "output-root"
    root.mkdir()
    sentinels = {name: f"sentinel:{name}".encode() for name in ("result.json", "report.md", "report.html")}
    for name, content in sentinels.items():
        (root / name).write_bytes(content)

    output = _failed_run(tmp_path)

    assert output.result["status"] != "accepted"
    for name, content in sentinels.items():
        assert (root / name).read_bytes() == content
    attempt = Path(output.result["attempt_directory"])
    assert attempt.parent == root
    assert attempt.name.startswith("run-")
    assert {path.name for path in map(Path, output.download_paths)} == {"result.json", "report.md", "report.html"}
    assert all(Path(path).parent == attempt for path in output.download_paths)


def test_two_failed_runs_create_distinct_attempt_directories(tmp_path: Path):
    first = _failed_run(tmp_path)
    second = _failed_run(tmp_path)
    assert first.result["attempt_directory"] != second.result["attempt_directory"]
    assert Path(first.result["attempt_directory"]).is_dir()
    assert Path(second.result["attempt_directory"]).is_dir()


def test_report_group_collision_fails_closed_without_overwrite(tmp_path: Path):
    attempt = prepare_attempt_paths(tmp_path)
    attempt.result.write_text("sentinel", encoding="utf-8")
    state, metadata, paths, diagnostic = publish_report_bundle(
        attempt,
        build_report_bundle({"status": "invalid", "diagnostics": [], "output": None}),
    )
    assert state == "failed"
    assert metadata == []
    assert paths == []
    assert diagnostic is not None
    assert attempt.result.read_text(encoding="utf-8") == "sentinel"
    assert not attempt.report_markdown.exists()
    assert not attempt.report_html.exists()


def test_failure_after_first_link_rolls_back_and_exposes_no_complete_set(monkeypatch, tmp_path: Path):
    import ev4_transition.io.safe_publication as publication

    attempt = prepare_attempt_paths(tmp_path)
    real_link = publication.os.link
    calls = {"count": 0}

    def fail_second(source, destination, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated concurrent failure")
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(publication.os, "link", fail_second)
    state, metadata, paths, diagnostic = publish_report_bundle(
        attempt,
        build_report_bundle({"status": "invalid", "diagnostics": [], "output": None}),
    )
    assert state == "failed"
    assert metadata == []
    assert paths == []
    assert diagnostic is not None
    assert not any(path.exists() for path in attempt.report_paths())


def test_download_paths_are_verified_existing_files_only(tmp_path: Path):
    output = _failed_run(tmp_path)
    assert output.download_paths
    assert all(Path(path).is_file() for path in output.download_paths)
    assert output.result["publication_state"] == "published_verified"
    assert all(item["state"] == "published_verified" for item in output.result["published_artifacts"])


def test_open_output_folder_accepts_only_verified_run_directory(monkeypatch, tmp_path: Path):
    called = []
    monkeypatch.setattr("ev4_transition.ui.app.open_directory", lambda path: called.append(Path(path)))
    arbitrary = tmp_path / "arbitrary"
    arbitrary.mkdir()
    assert "معتبر" in open_output_folder(str(arbitrary))
    assert called == []

    attempt = prepare_attempt_paths(tmp_path)
    message = open_output_folder(str(attempt.execution_directory))
    assert "پوشه باز شد" in message
    assert called == [attempt.execution_directory]
