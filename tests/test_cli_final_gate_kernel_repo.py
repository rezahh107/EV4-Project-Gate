import json
from pathlib import Path

import ev4_transition.cli as cli

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "fixtures/valid/architect-stage-bundle.v1.json"


def _local_checkout_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_gate = tmp_path / "project-gate"
    responsive = tmp_path / "responsive"
    kernel = tmp_path / "kernel"
    for path in (project_gate, responsive, kernel):
        path.mkdir()
    return project_gate, responsive, kernel


def _parsed_output(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_final_gate_cli_requires_kernel_repo(tmp_path: Path, capsys):
    project_gate, responsive, _ = _local_checkout_paths(tmp_path)

    return_code = cli.main([
        "transition",
        "final-evidence-gate",
        str(BUNDLE),
        "--project-gate-repo",
        str(project_gate),
        "--responsive-repo",
        str(responsive),
    ])

    payload = _parsed_output(capsys)
    assert return_code == 2
    assert payload["status"] == "insufficient_evidence"
    assert payload["diagnostics"][0]["code"] == "CLI_LOCAL_PATH_REQUIRED"
    assert payload["diagnostics"][0]["details"]["option"] == "--kernel-repo"


def test_final_gate_cli_rejects_kernel_github_url(tmp_path: Path, capsys):
    project_gate, responsive, _ = _local_checkout_paths(tmp_path)

    return_code = cli.main([
        "transition",
        "final-evidence-gate",
        str(BUNDLE),
        "--project-gate-repo",
        str(project_gate),
        "--responsive-repo",
        str(responsive),
        "--kernel-repo",
        "https://github.com/rezahh107/EV4-Decision-Kernel",
    ])

    payload = _parsed_output(capsys)
    assert return_code == 2
    assert payload["diagnostics"][0]["code"] == "CLI_GITHUB_URL_REJECTED"
    assert payload["diagnostics"][0]["details"]["option"] == "--kernel-repo"


def test_final_gate_cli_rejects_missing_kernel_checkout(tmp_path: Path, capsys):
    project_gate, responsive, _ = _local_checkout_paths(tmp_path)
    missing_kernel = tmp_path / "missing-kernel"

    return_code = cli.main([
        "transition",
        "final-evidence-gate",
        str(BUNDLE),
        "--project-gate-repo",
        str(project_gate),
        "--responsive-repo",
        str(responsive),
        "--kernel-repo",
        str(missing_kernel),
    ])

    payload = _parsed_output(capsys)
    assert return_code == 2
    assert payload["diagnostics"][0]["code"] == "CLI_LOCAL_PATH_NOT_FOUND"
    assert payload["diagnostics"][0]["details"]["option"] == "--kernel-repo"
    assert payload["diagnostics"][0]["details"]["path"] == str(missing_kernel)


def test_final_gate_cli_forwards_exact_kernel_checkout(monkeypatch, tmp_path: Path, capsys):
    project_gate, responsive, kernel = _local_checkout_paths(tmp_path)
    observed = {}

    def fake_final_gate_from_local_paths(
        final_input,
        schema_root,
        lock_path,
        project_gate_repo,
        responsive_repo,
        *,
        kernel_repo=None,
        **kwargs,
    ):
        observed.update(
            final_input=final_input,
            schema_root=schema_root,
            lock_path=lock_path,
            project_gate_repo=project_gate_repo,
            responsive_repo=responsive_repo,
            kernel_repo=kernel_repo,
            kwargs=kwargs,
        )
        return {"status": "insufficient_evidence", "diagnostics": []}

    monkeypatch.setattr(cli, "final_gate_from_local_paths", fake_final_gate_from_local_paths)

    return_code = cli.main([
        "transition",
        "final-evidence-gate",
        str(BUNDLE),
        "--project-gate-repo",
        str(project_gate),
        "--responsive-repo",
        str(responsive),
        "--kernel-repo",
        str(kernel),
    ])

    _parsed_output(capsys)
    assert return_code == 2
    assert observed["project_gate_repo"] == str(project_gate)
    assert observed["responsive_repo"] == str(responsive)
    assert observed["kernel_repo"] == str(kernel)
