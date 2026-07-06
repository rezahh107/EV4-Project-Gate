import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_demo(output_root: Path, *extra_args: str):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/run-project-gate-demo.py"), "--output-root", str(output_root), *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_controlled_demo_writes_safe_outputs_and_avoids_collisions(tmp_path):
    first = run_demo(tmp_path, "--run-id", "demo-fixed")
    second = run_demo(tmp_path, "--run-id", "demo-fixed")

    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert "synthetic" in first.stdout.lower()
    assert "Traceback" not in first.stdout + first.stderr + second.stdout + second.stderr

    run_dirs = sorted(path.name for path in tmp_path.glob("demo-fixed*"))
    assert run_dirs == ["demo-fixed", "demo-fixed-001"]

    run_dir = tmp_path / "demo-fixed"
    for filename in ["result.json", "report.md", "report.html", "input.snapshot.json", "diagnostics.json"]:
        assert (run_dir / filename).is_file()

    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["demo_mode"] == "controlled_synthetic_personal_use"
    assert result["real_evidence_claimed"] is False
    assert result["production_readiness_claimed"] is False
    assert result["real_elementor_validation_claimed"] is False
    assert result["export_validation_claimed"] is False
    assert result["accessibility_completion_claimed"] is False
    assert result["real_end_to_end_readiness_claimed"] is False
    assert result["final_gate_status"] == "insufficient_evidence"

    statuses = {sample["path"]: sample["validation_status"] for sample in result["samples"]}
    assert statuses["fixtures/personal-use/sample-valid-stage-bundle.synthetic.json"] in {"valid", "accepted"}
    assert statuses["fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json"] == "insufficient_evidence"
    assert all(sample["synthetic"] is True for sample in result["samples"])

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "insufficient_evidence" in report
    assert "production readiness" in report
    assert "real end-to-end readiness" in report


def test_controlled_demo_records_malformed_or_missing_fixture_without_traceback(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not json", encoding="utf-8")
    missing = tmp_path / "missing.json"

    completed = run_demo(
        tmp_path / "bad-fixtures",
        "--run-id",
        "demo-bad-fixtures",
        "--valid-fixture",
        str(malformed),
        "--insufficient-fixture",
        str(missing),
    )

    assert completed.returncode == 1
    combined = completed.stdout + completed.stderr
    assert "Traceback" not in combined

    run_dir = tmp_path / "bad-fixtures" / "demo-bad-fixtures"
    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["final_gate_status"] == "insufficient_evidence"
    assert result["real_evidence_claimed"] is False
    assert all(sample["synthetic"] is False for sample in result["samples"])
    assert all("metadata_error" in sample for sample in result["samples"])
    assert {sample["validation_status"] for sample in result["samples"]} == {"invalid"}

    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    flattened_codes = {
        diagnostic.get("code")
        for sample in diagnostics["diagnostics"]
        for diagnostic in sample["diagnostics"]
    }
    assert {"MALFORMED_JSON", "FILE_READ_ERROR"} <= flattened_codes
