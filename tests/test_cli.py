import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ev4_transition.cli",
            "--schema-root",
            str(ROOT / "schemas"),
            *args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_script(script: str, *args: str):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_json_output_valid_bundle():
    completed = run_cli("validate", str(ROOT / "fixtures/valid/architect-stage-bundle.v1.json"))
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "valid"


def test_cli_invalid_input_exit_code():
    completed = run_cli("validate", str(ROOT / "fixtures/invalid/array-input.v1.json"))
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["status"] == "invalid"


def test_cli_missing_file_returns_invalid_without_traceback():
    completed = run_cli("validate", str(ROOT / "fixtures/invalid/missing-file.v1.json"))
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["diagnostics"][0]["code"] == "FILE_READ_ERROR"


def test_cli_persian_insufficient_evidence_output():
    completed = run_cli(
        "validate",
        str(ROOT / "fixtures/insufficient-evidence/architect-stage-bundle.v1.json"),
        "--format",
        "persian",
    )
    assert completed.returncode == 2
    assert "شواهد کافی نیست" in completed.stdout


def test_cli_inspect_persian_reports_guarded_transition_truth():
    completed = run_cli("inspect", "--format", "persian")
    assert completed.returncode == 0
    for expected in (
        "Architect → CE",
        "CE → Builder",
        "Builder → Responsive",
        "Final Evidence Gate",
        "guarded/fail-closed",
        "insufficient_evidence",
    ):
        assert expected in completed.stdout


def test_cli_inspect_reports_layered_ce_to_builder_truth():
    completed = run_cli("inspect")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert "stage_bundle_validation" in payload["implemented"]
    assert "architect-to-ce transition" in payload["implemented"]
    assert payload["capabilities"]["ce_to_builder"] == {
        "orchestration_baseline": "implemented",
        "cli_exposure": "guarded",
        "owner_fixture_integration": "verified",
        "real_non_synthetic_handoff": "insufficient_evidence",
    }
    assert "ce-to-builder" in payload["public_cli_transitions"]


def test_cli_inspect_does_not_overclaim_real_ce_to_builder_handoff():
    payload = json.loads(run_cli("inspect").stdout)
    assert payload["capabilities"]["ce_to_builder"]["real_non_synthetic_handoff"] == "insufficient_evidence"
    assert payload["evidence"]["current_main_head_ci"]["status"] == "insufficient_evidence"


def test_capability_truth_gate_passes_single_authority_repository():
    completed = run_script("scripts/check-capability-truth.py", str(ROOT))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "capability-status.v1.json" in completed.stdout


def test_capability_truth_gate_detects_missing_required_capability(tmp_path):
    for relative in (
        "src/ev4_transition/data/capability-status.v1.json",
        "README.md",
        "AGENTS.md",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    authority_path = tmp_path / "src/ev4_transition/data/capability-status.v1.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    del authority["capabilities"]["ce_to_builder"]
    authority_path.write_text(json.dumps(authority), encoding="utf-8")
    completed = run_script("scripts/check-capability-truth.py", str(tmp_path))
    assert completed.returncode == 1
    assert "ce_to_builder" in completed.stdout


def test_lean_pipeline_has_no_removed_automation_or_duplicate_workflows():
    removed = (
        ".github/workflows/status-after-merge.yml",
        ".github/workflows/prompt-05.yml",
        ".github/workflows/prompt-06.yml",
        ".github/workflows/ui-runtime-smoke.yml",
        ".github/workflows/kroad-011.yml",
        ".github/workflows/prompt-05-producer-integration.yml",
        "scripts/update-status-after-merge.js",
        "scripts/package-ci-evidence.py",
        "scripts/check-workflow-permissions.py",
        "scripts/check-github-action-pinning.py",
        "package.json",
        "docs/IMPLEMENTATION_STATUS.yaml",
        "docs/EV4_SHARED_CONTRACTS_STATUS.md",
        "docs/BEHAVIORAL_RULE_COVERAGE.md",
    )
    for relative in removed:
        assert not (ROOT / relative).exists(), relative


def test_unified_workflow_runs_core_once_and_keeps_reusable_contract():
    workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    assert workflow.count("Run full internal quality suite once") == 1
    assert workflow.count("Build wheel once") == 1
    assert workflow.count("Clean-install package and construct UI once") == 1
    assert "actions/upload-artifact" not in workflow
    assert "contents: write" not in workflow
    assert "Setup Node for Kernel boundary only" in workflow
    reusable = ROOT / ".github/workflows/verify-vendored-common-contract.yml"
    assert reusable.is_file()
    assert "workflow_call:" in reusable.read_text(encoding="utf-8")


def test_cli_inspect_reports_builder_responsive_and_final_gate_truth():
    payload = json.loads(run_cli("inspect").stdout)
    assert payload["capabilities"]["builder_to_responsive"]["verification_state"] == "verified_by_exact_head_ci"
    assert payload["capabilities"]["final_evidence_gate"]["verification_state"] == "verified_by_exact_head_ci"
    assert payload["capabilities"]["final_evidence_gate"]["real_non_synthetic_evidence"] == "insufficient_evidence"


def test_cli_guarded_ce_to_builder_requires_local_paths():
    completed = run_cli("transition", "ce-to-builder", str(ROOT / "fixtures/valid/architect-stage-bundle.v1.json"))
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["status"] == "insufficient_evidence"
    assert payload["diagnostics"][0]["code"] == "CLI_LOCAL_PATH_REQUIRED"


def test_cli_guarded_builder_to_responsive_rejects_github_url():
    completed = run_cli(
        "transition",
        "builder-to-responsive",
        str(ROOT / "fixtures/valid/architect-stage-bundle.v1.json"),
        "--builder-repo",
        "https://github.com/rezahh107/EV4-Builder-Assistant-Repo",
        "--responsive-repo",
        str(ROOT),
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["diagnostics"][0]["code"] == "CLI_GITHUB_URL_REJECTED"


def test_cli_guarded_final_gate_missing_path_fails_closed():
    completed = run_cli(
        "transition",
        "final-evidence-gate",
        str(ROOT / "fixtures/valid/architect-stage-bundle.v1.json"),
        "--project-gate-repo",
        str(ROOT),
        "--responsive-repo",
        str(ROOT / "missing-responsive-repo"),
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["diagnostics"][0]["code"] == "CLI_LOCAL_PATH_NOT_FOUND"
