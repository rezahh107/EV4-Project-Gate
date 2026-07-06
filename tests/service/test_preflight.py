from __future__ import annotations

import json
from pathlib import Path

from ev4_transition.service import GateRequest, RepoPaths, run_preflight


def _repo(root: Path, files: list[str], *, git: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if git:
        (root / ".git").mkdir()
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    return root


def _write_lock(project_gate: Path, relative: str, files: list[dict[str, str]]) -> None:
    path = project_gate / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": "test-lock.v1", "files": files}, ensure_ascii=False), encoding="utf-8")


def _a2c_lock_files() -> list[dict[str, str]]:
    return [
        {"repository": "rezahh107/EV4-Architect-Repo", "path": "schemas/ev4-architect-stage-payload.v1.schema.json"},
        {"repository": "rezahh107/EV4-Constructability-Engineer-Repo", "path": "schemas/ce_architect_stage_intake.v1_1.schema.json"},
    ]


def test_architect_to_ce_requires_only_architect_and_ce_paths(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/architect-to-ce-transition.v1.lock.json", _a2c_lock_files())
    architect = _repo(tmp_path / "EV4-Architect-Repo", ["schemas/ev4-architect-stage-payload.v1.schema.json"])
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/ce_architect_stage_intake.v1_1.schema.json"])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), architect_repo_path=str(architect), ce_repo_path=str(ce))))

    assert result.status == "ready"
    by_id = {check.id: check for check in result.checks}
    assert by_id["path.builder_repo_path.not_required"].status == "not_required"
    assert by_id["path.responsive_repo_path.not_required"].status == "not_required"
    assert not any(check.status == "error" for check in result.checks)


def test_ce_to_builder_requires_only_ce_and_builder_paths(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/ce-to-builder-transition.v1.lock.json", [
        {"repository": "rezahh107/EV4-Constructability-Engineer-Repo", "path": "schemas/builder_executable_package.schema.json"},
        {"repository": "rezahh107/EV4-Builder-Assistant-Repo", "path": "schemas/builder-context-package.schema.json"},
    ])
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/builder_executable_package.schema.json"])
    builder = _repo(tmp_path / "EV4-Builder-Assistant-Repo", ["schemas/builder-context-package.schema.json"])

    result = run_preflight(GateRequest(transition_choice="ce_to_builder", input_data={"stage": "ce"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), ce_repo_path=str(ce), builder_repo_path=str(builder))))

    assert result.status == "ready"
    assert any(check.id == "path.architect_repo_path.not_required" for check in result.checks)
    assert not any(check.classification == "missing" for check in result.checks)


def test_github_url_in_local_path_field_blocks_preflight(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/architect-to-ce-transition.v1.lock.json", _a2c_lock_files())
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/ce_architect_stage_intake.v1_1.schema.json"])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), architect_repo_path="https://github.com/rezahh107/EV4-Architect-Repo", ce_repo_path=str(ce))))

    assert result.status == "blocked"
    assert any(check.classification == "looks_like_github_url" and check.status == "error" for check in result.checks)


def test_missing_required_path_produces_blocked_preflight(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/architect-to-ce-transition.v1.lock.json", _a2c_lock_files())
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/ce_architect_stage_intake.v1_1.schema.json"])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), ce_repo_path=str(ce))))

    assert result.status == "blocked"
    assert any(check.id == "path.architect_repo_path.missing" and check.status == "error" for check in result.checks)


def test_existing_folder_missing_expected_pinned_file_is_actionable(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/architect-to-ce-transition.v1.lock.json", _a2c_lock_files())
    architect = _repo(tmp_path / "EV4-Architect-Repo", ["schemas/ev4-architect-stage-payload.v1.schema.json"])
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", [])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), architect_repo_path=str(architect), ce_repo_path=str(ce))))

    check = next(check for check in result.checks if check.id == "pinned.ce_repo_path.missing")
    assert result.status == "blocked"
    assert "schemas/ce_architect_stage_intake.v1_1.schema.json" in (check.technical_detail or "")
    assert "GitHub Desktop" in (check.next_action_fa or "")


def test_validate_bundle_result_uploaded_into_architect_to_ce_is_detected_as_wrong_input_type(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    _write_lock(project_gate, "contracts/locks/architect-to-ce-transition.v1.lock.json", _a2c_lock_files())
    architect = _repo(tmp_path / "EV4-Architect-Repo", ["schemas/ev4-architect-stage-payload.v1.schema.json"])
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/ce_architect_stage_intake.v1_1.schema.json"])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"schema_version": "ev4-project-gate-ui-result.v1", "result_type": "service_response"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate), architect_repo_path=str(architect), ce_repo_path=str(ce))))

    assert result.status == "blocked"
    assert any(check.id == "json.source.project_gate_result" and check.status == "error" for check in result.checks)


def test_validate_bundle_choice_explains_validation_only_no_transition_output():
    result = run_preflight(GateRequest(transition_choice="validate_bundle", input_data={"schema_version": "stage-evidence-bundle.v1"}))

    assert result.status == "warnings"
    check = next(check for check in result.checks if check.id == "transition.validate_bundle.validation_only")
    assert check.status == "warning"
    assert "خروجی CE/Builder/Responsive نمی‌سازد" in check.message_fa


def test_irrelevant_paths_are_marked_not_required_not_errors(tmp_path: Path):
    result = run_preflight(GateRequest(transition_choice="validate_bundle", input_data={"schema_version": "stage-evidence-bundle.v1"}, repo_paths=RepoPaths(architect_repo_path="https://github.com/rezahh107/EV4-Architect-Repo", ce_repo_path=str(tmp_path / "missing-ce"), builder_repo_path=str(tmp_path / "missing-builder"))))

    assert result.status == "warnings"
    assert not any(check.status == "error" for check in result.checks)
    assert any(check.classification == "not_required_for_selected_transition" for check in result.checks)


def test_project_gate_path_is_not_required_for_architect_to_ce_preflight(tmp_path: Path):
    architect = _repo(tmp_path / "EV4-Architect-Repo", ["schemas/ev4-architect-stage-payload.v1.schema.json"])
    ce = _repo(tmp_path / "EV4-Constructability-Engineer-Repo", ["schemas/ce_architect_stage_intake.v1_1.schema.json"])

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path="https://github.com/rezahh107/EV4-Project-Gate", architect_repo_path=str(architect), ce_repo_path=str(ce))))

    assert not any(check.classification == "looks_like_github_url" for check in result.checks)
    assert any(check.id == "path.project_gate_repo_path.not_required_filled" for check in result.checks)


def test_malformed_lock_file_does_not_crash_preflight(tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    lock_path = project_gate / "contracts/locks/architect-to-ce-transition.v1.lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("[]", encoding="utf-8")

    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate))))

    assert result.status == "blocked"
    assert any(check.id == "lock_manifest.invalid_format" and check.classification == "invalid_format" for check in result.checks)


def test_lock_file_read_error_is_structured_preflight_check(monkeypatch, tmp_path: Path):
    project_gate = _repo(tmp_path / "EV4-Project-Gate", [])
    lock_path = project_gate / "contracts/locks/architect-to-ce-transition.v1.lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"files": []}), encoding="utf-8")
    original_read_text = Path.read_text

    def fail_lock_read(self: Path, *args, **kwargs):
        if self == lock_path:
            raise OSError("cannot read lock")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_lock_read)
    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=RepoPaths(project_gate_repo_path=str(project_gate))))

    assert result.status == "blocked"
    assert any(check.id == "lock_manifest.file_read_error" and check.classification == "file_read_error" for check in result.checks)


def test_none_repo_paths_defaults_to_empty_repo_paths_without_crashing():
    result = run_preflight(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=None))  # type: ignore[arg-type]

    assert result.status == "blocked"
    assert any(check.id == "path.architect_repo_path.missing" for check in result.checks)
