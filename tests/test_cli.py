import json
import subprocess
import sys
from pathlib import Path

import yaml

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


def test_cli_inspect_reports_layered_ce_to_builder_truth():
    completed = run_cli("inspect")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert "stage_bundle_validation" in payload["implemented"]
    assert "architect-to-ce transition" in payload["implemented"]
    ce_to_builder = payload["capabilities"]["ce_to_builder"]
    assert ce_to_builder == {
        "orchestration_baseline": "implemented",
        "cli_exposure": "not_implemented",
        "owner_fixture_integration": "verified",
        "real_non_synthetic_handoff": "insufficient_evidence",
    }
    assert "ce-to-builder transition" not in payload["not_implemented"]
    assert "ce-to-builder public CLI exposure" in payload["not_implemented"]
    assert "ce-to-builder" not in payload["public_cli_transitions"]


def test_cli_inspect_does_not_overclaim_real_ce_to_builder_handoff():
    completed = run_cli("inspect")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["capabilities"]["ce_to_builder"]["real_non_synthetic_handoff"] == "insufficient_evidence"
    assert payload["evidence"]["current_main_head_ci"]["status"] == "insufficient_evidence"


def test_implementation_status_matches_all_capability_truth():
    capability = json.loads((ROOT / "src/ev4_transition/data/capability-status.v1.json").read_text(encoding="utf-8"))
    implementation = yaml.safe_load((ROOT / "docs/IMPLEMENTATION_STATUS.yaml").read_text(encoding="utf-8"))
    for capability_id, expected in capability["capabilities"].items():
        actual = implementation["capabilities"][capability_id]
        for key, value in expected.items():
            assert actual[key] == value
    assert implementation["repository"]["pull_request_20"]["state"] == "merged"
    assert implementation["repository"]["current_main_head_ci"]["status"] == "insufficient_evidence"


def test_active_docs_do_not_restore_flat_ce_to_builder_not_implemented_claim():
    active_paths = [
        "README.md",
        "AGENTS.md",
        "docs/VALIDATION_STRATEGY.md",
        "docs/COMPATIBILITY_MAP.md",
    ]
    forbidden = [
        "The CE → Builder transition is documented as a freeze baseline only. It is not implemented in Project Gate yet.",
        "Do not describe CE → Builder, Builder → Responsive",
        "implemented: false\nfreeze_matrix: docs/CE_TO_BUILDER_FREEZE_MATRIX.md",
    ]
    for relative in active_paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text
        assert "orchestration_baseline" in text or relative == "README.md"


def test_capability_truth_gate_passes_repository():
    completed = run_script("scripts/check-capability-truth.py", str(ROOT))
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_capability_truth_gate_detects_active_doc_drift(tmp_path):
    relative_paths = [
        "src/ev4_transition/data/capability-status.v1.json",
        "docs/IMPLEMENTATION_STATUS.yaml",
        "README.md",
        "AGENTS.md",
    ]
    for relative in relative_paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(
            "orchestration_baseline: implemented",
            "orchestration_baseline: not_implemented",
            1,
        ),
        encoding="utf-8",
    )

    completed = run_script("scripts/check-capability-truth.py", str(tmp_path))
    assert completed.returncode == 1
    assert "AGENTS.md" in completed.stdout


def test_action_pinning_guard_scans_all_workflows_by_default(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "pinned.yml").write_text(
        "steps:\n  - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5\n",
        encoding="utf-8",
    )
    (workflows / "mutable.yaml").write_text(
        "permissions:\n  contents: write\nsteps:\n  - uses: actions/setup-node@v4\n",
        encoding="utf-8",
    )
    completed = run_script("scripts/check-github-action-pinning.py", str(tmp_path))
    assert completed.returncode == 1
    assert "mutable.yaml" in completed.stdout
    assert "actions/setup-node@v4" in completed.stdout


def test_repository_workflows_use_full_sha_action_pins():
    completed = run_script("scripts/check-github-action-pinning.py", str(ROOT))
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_workflow_permission_gate_passes_repository():
    completed = run_script("scripts/check-workflow-permissions.py", str(ROOT))
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_workflow_permission_gate_rejects_persisted_checkout_credentials(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "unsafe.yml").write_text(
        """name: Unsafe
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
""",
        encoding="utf-8",
    )
    completed = run_script("scripts/check-workflow-permissions.py", str(tmp_path))
    assert completed.returncode == 1
    assert "persist-credentials: false" in completed.stdout


def test_post_merge_workflow_dispatches_exact_main_head_validation():
    post_merge = (ROOT / ".github/workflows/status-after-merge.yml").read_text(encoding="utf-8")
    assert "actions: write" in post_merge
    assert "FINAL_MAIN_SHA=$(git rev-parse HEAD)" in post_merge
    assert "actions/workflows/${workflow}/dispatches" in post_merge
    assert "validate.yml prompt-05.yml" in post_merge
    assert "expected_head_sha" in post_merge

    for relative in [".github/workflows/validate.yml", ".github/workflows/prompt-05.yml"]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text
        assert "expected_head_sha:" in text
        assert 'test "$TESTED_SHA" = "$EXPECTED_HEAD_SHA"' in text


def test_cli_inspect_reports_prompt05_layered_truth():
    completed = run_cli("inspect")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["capabilities"]["builder_to_responsive"] == {
        "orchestration_baseline": "implemented",
        "cli_exposure": "not_implemented",
        "owner_contract_lock": "computed_from_pinned_owner_file_bytes",
        "official_responsive_validator_integration": "implemented",
        "verification_state": "verified_by_exact_head_ci",
        "real_non_synthetic_handoff": "insufficient_evidence",
    }
    assert payload["capabilities"]["final_evidence_gate"] == {
        "orchestration_baseline": "implemented",
        "cli_exposure": "not_implemented",
        "prior_lock_chain": "pinned_to_immutable_project_gate_commit",
        "official_responsive_validator_integration": "implemented",
        "verification_state": "verified_by_exact_head_ci",
        "real_non_synthetic_evidence": "insufficient_evidence",
    }
    assert payload["evidence"]["prompt_05_owner_contract_and_validator_integration"]["result"] == "success"
    assert "builder-to-responsive public CLI exposure" in payload["not_implemented"]
    assert "final evidence gate public CLI exposure" in payload["not_implemented"]
    assert "builder-to-responsive" not in payload["public_cli_transitions"]
