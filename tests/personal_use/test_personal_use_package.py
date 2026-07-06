import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_personal_use_package_files_exist():
    for relative in [
        "docs/LOCAL_SETUP_GUIDE.md",
        "docs/PERSONAL_USE_GUIDE.md",
        "docs/E2E_DEMO_WORKFLOW.md",
        "scripts/run-project-gate-ui.py",
        "scripts/run-project-gate-demo.py",
        "outputs/README.md",
        "outputs/.gitkeep",
    ]:
        assert (ROOT / relative).exists(), relative


def test_personal_use_samples_are_synthetic_json():
    for relative in [
        "fixtures/personal-use/sample-valid-stage-bundle.synthetic.json",
        "fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
        "examples/personal-use/sample-valid-stage-bundle.synthetic.json",
        "examples/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
    ]:
        data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        assert data.get("synthetic") is True


def test_personal_use_docs_explain_statuses_and_outputs():
    guide = (ROOT / "docs/PERSONAL_USE_GUIDE.md").read_text(encoding="utf-8")
    for token in ["accepted", "invalid", "insufficient_evidence", "repair_needed", "outputs/runs/<timestamp-or-run-id>/"]:
        assert token in guide


def test_demo_runner_keeps_safety_markers():
    text = (ROOT / "scripts/run-project-gate-demo.py").read_text(encoding="utf-8")
    for token in [
        "_safe_fixture_metadata",
        "_create_unique_run_dir",
        "metadata_error",
        "FileExistsError",
        '"final_gate_status": "insufficient_evidence"',
        '"real_evidence_claimed": False',
    ]:
        assert token in text
