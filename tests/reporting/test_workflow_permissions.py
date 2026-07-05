from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/prompt-06.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_prompt_06_workflow_has_minimum_github_token_permissions():
    workflow = _load_workflow()
    assert workflow["permissions"] == {"contents": "read"}


def test_prompt_06_checkout_does_not_persist_credentials():
    workflow = _load_workflow()
    steps = workflow["jobs"]["report-ux"]["steps"]
    checkout_steps = [step for step in steps if step.get("uses", "").startswith("actions/checkout@")]
    assert checkout_steps
    for step in checkout_steps:
        assert step.get("with", {}).get("persist-credentials") is False
