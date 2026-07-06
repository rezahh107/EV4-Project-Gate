from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_controlled_demo_output_collision_contract_is_present():
    text = read("scripts/run-project-gate-demo.py")
    assert "def _create_unique_run_dir" in text
    assert "FileExistsError" in text
    assert "-{index:03d}" in text


def test_controlled_demo_metadata_error_contract_is_present():
    text = read("scripts/run-project-gate-demo.py")
    assert "def _safe_fixture_metadata" in text
    assert "metadata_error" in text
    assert "validator.validate_file(path)" in text
    assert '"diagnostics": result.get("diagnostics", [])' in text


def test_controlled_demo_never_claims_real_readiness():
    text = read("scripts/run-project-gate-demo.py")
    for required in [
        '"final_gate_status": "insufficient_evidence"',
        '"real_evidence_claimed": False',
        '"production_readiness_claimed": False',
        '"real_elementor_validation_claimed": False',
        '"export_validation_claimed": False',
        '"accessibility_completion_claimed": False',
        '"frontend_correctness_claimed": False',
        '"responsive_correctness_claimed": False',
        '"real_end_to_end_readiness_claimed": False',
    ]:
        assert required in text


def test_demo_workflow_doc_remains_controlled_not_real_e2e():
    text = read("docs/E2E_DEMO_WORKFLOW.md")
    assert "demo" in text.lower()
    assert "insufficient_evidence" in text
    assert "real Elementor validation" in text
    assert "real end-to-end readiness" in text
