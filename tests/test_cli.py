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


def test_cli_json_output_valid_bundle():
    completed = run_cli("validate", str(ROOT / "fixtures/valid/architect-stage-bundle.v1.json"))
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "valid"


def test_cli_invalid_input_exit_code():
    completed = run_cli("validate", str(ROOT / "fixtures/invalid/array-input.v1.json"))
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "invalid"


def test_cli_missing_file_returns_invalid_without_traceback():
    completed = run_cli("validate", str(ROOT / "fixtures/invalid/missing-file.v1.json"))
    assert completed.returncode == 1
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["status"] == "invalid"
    assert payload["diagnostics"][0]["code"] == "FILE_READ_ERROR"


def test_cli_persian_insufficient_evidence_output():
    completed = run_cli("validate", str(ROOT / "fixtures/insufficient-evidence/architect-stage-bundle.v1.json"), "--format", "persian")
    assert completed.returncode == 2
    assert "شواهد کافی نیست" in completed.stdout


def test_cli_inspect_json():
    completed = run_cli("inspect")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert "stage_bundle_validation" in payload["implemented"]
    assert "architect-to-ce transition" in payload["not_implemented"]
