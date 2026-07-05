import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_controlled_demo_writes_safe_outputs(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run-project-gate-demo.py"), "--output-root", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "synthetic" in completed.stdout.lower()

    run_dirs = list(tmp_path.glob("demo-*"))
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    for filename in ["result.json", "report.md", "report.html", "input.snapshot.json", "diagnostics.json"]:
        assert (run_dir / filename).is_file()

    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["demo_mode"] == "controlled_synthetic_personal_use"
    assert result["real_evidence_claimed"] is False
    assert result["production_readiness_claimed"] is False
    assert result["real_elementor_validation_claimed"] is False
    assert result["final_gate_status"] == "insufficient_evidence"

    statuses = {sample["path"]: sample["validation_status"] for sample in result["samples"]}
    assert statuses["fixtures/personal-use/sample-valid-stage-bundle.synthetic.json"] in {"valid", "accepted"}
    assert statuses["fixtures/personal-use/sample-insufficient-evidence-stage-bundle.synthetic.json"] == "insufficient_evidence"
    assert all(sample["synthetic"] is True for sample in result["samples"])

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "insufficient_evidence" in report
    assert "production readiness" in report
