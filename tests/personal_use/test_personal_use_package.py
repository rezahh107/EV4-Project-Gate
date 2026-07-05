import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_personal_use_guides_exist():
    assert (ROOT / "docs/LOCAL_SETUP_GUIDE.md").is_file()
    assert (ROOT / "docs/PERSONAL_USE_GUIDE.md").is_file()
    assert (ROOT / "docs/E2E_DEMO_WORKFLOW.md").is_file()


def test_status_explanations_include_all_project_gate_statuses():
    text = (ROOT / "docs/PERSONAL_USE_GUIDE.md").read_text(encoding="utf-8")
    for status in ["accepted", "invalid", "insufficient_evidence", "repair_needed"]:
        assert status in text


def test_synthetic_samples_are_explicitly_marked_synthetic():
    for relative in [
        "fixtures/personal-use/sample-valid-stage-bundle.synthetic.json",
        "fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
        "examples/personal-use/sample-valid-stage-bundle.synthetic.json",
        "examples/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
    ]:
        path = ROOT / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["synthetic"] is True
        assert "synthetic" in path.read_text(encoding="utf-8").lower()


def test_launcher_detects_missing_ui_gracefully():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run-project-gate-ui.py"),
            "--module",
            "ev4_transition.ui.__missing_for_personal_use_test__",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    combined = completed.stdout + completed.stderr
    assert "UI is not installed yet. Merge Prompt 1 UI branch first." in combined
    assert "Traceback" not in combined


def test_output_folder_convention_is_documented():
    text = (ROOT / "outputs/README.md").read_text(encoding="utf-8")
    assert "outputs/runs/<timestamp-or-run-id>/" in text
    for filename in ["result.json", "report.md", "report.html", "input.snapshot.json", "diagnostics.json"]:
        assert filename in text


def test_generated_outputs_are_ignored_but_placeholders_tracked():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "outputs/runs/" in text
    assert "!outputs/.gitkeep" in text
    assert "!outputs/README.md" in text


def test_demo_runner_source_does_not_claim_real_evidence():
    text = (ROOT / "scripts/run-project-gate-demo.py").read_text(encoding="utf-8")
    assert '"real_evidence_claimed": False' in text
    assert '"production_readiness_claimed": False' in text
    assert '"real_elementor_validation_claimed": False' in text
