from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/validate.yml"
CLASSIFIER = ROOT / "scripts/classify-validation-scope.py"


def test_workflow_uses_separate_exact_pcvp_owner_checkout() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "path: EV4-Decision-Kernel-PCVP" in workflow
    assert "ref: 069a50fa243b01fa578a7c1bcb8864d9e796d34b" in workflow
    assert "EV4_PCVP_KERNEL_REPO" in workflow
    assert "npm ci --ignore-scripts" in workflow
    assert "tests/producer_integration/test_pcvp_boundary_reader.py" in workflow
    legacy_block = workflow.split("Checkout pinned Decision Kernel for legacy intake", 1)[1]
    assert "ref: 76a82e28543ff8f0babca11b7d7dccac96b92894" in legacy_block
    assert "path: EV4-Decision-Kernel\n" in legacy_block


def test_pcvp_changes_select_kernel_owner_boundary() -> None:
    classifier = CLASSIFIER.read_text(encoding="utf-8")
    assert '"src/ev4_transition/pcvp_carrier.py"' in classifier
    assert '"contracts/locks/pcvp-v1.lock.json"' in classifier
    assert '"tests/producer_integration/test_pcvp_*.py"' in classifier
