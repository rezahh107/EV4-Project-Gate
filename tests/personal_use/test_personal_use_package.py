import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_personal_use_contract_files_exist():
    for relative in [
        "docs/LOCAL_SETUP_GUIDE.md",
        "docs/PERSONAL_USE_GUIDE.md",
        "docs/E2E_DEMO_WORKFLOW.md",
        "scripts/run-project-gate-ui.py",
        "scripts/run-project-gate-demo.py",
        "outputs/README.md",
    ]:
        assert (ROOT / relative).is_file()


def test_status_explanations_include_all_project_gate_statuses():
    text = read("docs/PERSONAL_USE_GUIDE.md")
    for status in ["accepted", "invalid", "insufficient_evidence", "repair_needed"]:
        assert status in text


def test_synthetic_samples_are_explicitly_marked_synthetic():
    for relative in [
        "fixtures/personal-use/sample-valid-stage-bundle.synthetic.json",
        "fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
        "examples/personal-use/sample-valid-stage-bundle.synthetic.json",
        "examples/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json",
    ]:
        text = read(relative)
        data = json.loads(text)
        assert data["synthetic"] is True
        assert "synthetic" in text.lower()


def test_launcher_and_demo_robustness_contracts_are_present():
    ui = read("scripts/run-project-gate-ui.py")
    demo = read("scripts/run-project-gate-demo.py")

    assert "UI is not installed yet. Merge Prompt 1 UI branch first." in ui
    assert "اقدام بعدی" in ui
    assert "except Exception" in ui
    assert "discovery_errors" in ui

    assert "def _safe_fixture_metadata" in demo
    assert "metadata_error" in demo
    assert "validator.validate_file(path)" in demo
    assert "def _create_unique_run_dir" in demo
    assert "FileExistsError" in demo


def test_output_and_download_conventions_are_documented():
    outputs = read("outputs/README.md")
    assert "outputs/runs/<timestamp-or-run-id>/" in outputs
    assert "result.json" in outputs
    assert "diagnostics.json" in outputs

    for relative in ["docs/PERSONAL_USE_GUIDE.md", "docs/LOCAL_SETUP_GUIDE.md", "docs/E2E_DEMO_WORKFLOW.md"]:
        text = read(relative)
        assert "outputs/runs/<timestamp-or-run-id>/" in text
        assert "UI" in text


def test_demo_runner_source_does_not_claim_real_evidence():
    text = read("scripts/run-project-gate-demo.py")
    for claim in [
        '"real_evidence_claimed": False',
        '"production_readiness_claimed": False',
        '"real_elementor_validation_claimed": False',
        '"export_validation_claimed": False',
        '"accessibility_completion_claimed": False',
        '"real_end_to_end_readiness_claimed": False',
        '"final_gate_status": "insufficient_evidence"',
    ]:
        assert claim in text


def test_readme_personal_section_does_not_own_capability_truth():
    readme = read("README.md")
    assert "## Personal local use" in readme
    assert readme.count("## Current Status") == 1
    personal_section = readme.split("## Personal local use", 1)[1].split("\n## ", 1)[0]
    assert "capabilities:" not in personal_section
    assert "user_interface:" not in personal_section
