import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_controlled_demo_files_exist():
    for relative in [
        "scripts/run-project-gate-demo.py",
        "docs/E2E_DEMO_WORKFLOW.md",
        "fixtures/personal-use/sample-valid-stage-bundle.synthetic.json",
        "fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
    ]:
        assert (ROOT / relative).exists(), relative


def test_controlled_demo_runner_executes(tmp_path):
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run-project-gate-demo.py"),
        "--output-root",
        str(tmp_path),
        "--run-id",
        "demo-fixed",
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    run_dir = tmp_path / "demo-fixed"
    expected_files = [
        "result.json",
        "report.md",
        "report.html",
        "input.snapshot.json",
        "diagnostics.json",
        "demo-status.json",
    ]
    for name in expected_files:
        assert (run_dir / name).exists(), name

    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["final_gate_status"] == "insufficient_evidence"
    assert result["real_evidence_claimed"] is False
    assert result["production_readiness_claimed"] is False
    assert result["real_elementor_validation_claimed"] is False
    assert result["export_validation_claimed"] is False
    assert result["accessibility_completion_claimed"] is False
    assert result["real_end_to_end_readiness_claimed"] is False

    second = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert (tmp_path / "demo-fixed-001").exists()


def test_ui_launcher_missing_ui_dry_run_is_user_facing():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run-project-gate-ui.py"),
            "--dry-run",
            "--module",
            "ev4_transition.ui.__missing_for_personal_use_test__",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = completed.stdout + completed.stderr
    assert completed.returncode == 2, combined
    assert "UI is not installed yet. Merge Prompt 1 UI branch first." in combined
    assert "Next action: merge Prompt 1 UI branch" in combined
    assert "Traceback" not in combined


def test_controlled_demo_safety_contract_is_documented_in_code_and_docs():
    script = (ROOT / "scripts/run-project-gate-demo.py").read_text(encoding="utf-8")
    doc = (ROOT / "docs/E2E_DEMO_WORKFLOW.md").read_text(encoding="utf-8")

    for token in ["insufficient_evidence", "real_evidence_claimed", "production_readiness_claimed"]:
        assert token in script
    for token in ["insufficient_evidence", "real Elementor validation", "real end-to-end readiness"]:
        assert token in doc
