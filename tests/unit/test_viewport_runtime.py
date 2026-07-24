from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ev4_transition.runners.repo_paths import (
    RepoPathError,
    normalize_repo_relative_ref,
    resolve_repo_relative_file,
)
from ev4_transition.runners.repository_identity import materialize_pinned_worktree
from ev4_transition.viewport_runtime import (
    OUTPUT_REF_BINDING_MISMATCH_REASON,
    RUNTIME_EVIDENCE_RECEIPT_SCHEMA,
    ViewportEvidenceRun,
    build_runtime_evidence_receipt,
    execute_pinned_viewport_capture,
    execute_viewport_capture,
    verify_viewport_evidence_run,
)

REPOSITORY = "rezahh107/EV4-Builder-Assistant-Repo"
TOOL = "scripts/capture-viewports.py"
SUBJECT = "desktop-proof"
VIEWPORT = "desktop"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def _source_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "builder"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "EV4 Tests")
    _git(root, "remote", "add", "origin", f"https://github.com/{REPOSITORY}.git")

    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "capture_helper.py").write_text('MARKER = "commit-a-helper"\n', encoding="utf-8")
    (scripts / "capture-viewports.py").write_text(
        """from __future__ import annotations
import argparse
import json
from pathlib import Path
from capture_helper import MARKER

parser = argparse.ArgumentParser()
parser.add_argument('--subject-ref', required=True)
parser.add_argument('--viewport', required=True)
args = parser.parse_args()
run_id = f'RUN-{args.viewport.upper()}'
artifact_ref = f'runtime/{args.viewport}.json'
artifact = Path(artifact_ref)
artifact.parent.mkdir(parents=True, exist_ok=True)
artifact.write_text(json.dumps({
    'evidence_ref': args.subject_ref,
    'viewport': args.viewport,
    'run_id': run_id,
    'status': 'confirmed',
    'helper_marker': MARKER,
}, sort_keys=True), encoding='utf-8')
print(json.dumps({
    'status': 'valid',
    'run_id': run_id,
    'artifact_ref': artifact_ref,
    'capture_status': 'completed',
    'validation_status': 'accepted',
}, sort_keys=True))
""",
        encoding="utf-8",
    )
    _git(root, "add", "scripts")
    _git(root, "commit", "--quiet", "-m", "add bounded viewport harness")
    return root, _git(root, "rev-parse", "HEAD")


def _execute(worktree):
    return execute_viewport_capture(
        execution_worktree=worktree,
        producer_tool_ref=TOOL,
        working_directory_ref=".",
        subject_ref=SUBJECT,
        viewport=VIEWPORT,
        timeout_seconds=10,
    )


def _verify(worktree, run: ViewportEvidenceRun, commit: str):
    return verify_viewport_evidence_run(
        run=run,
        execution_worktree=worktree,
        expected_repository=REPOSITORY,
        expected_commit=commit,
        expected_tool_ref=TOOL,
        expected_working_directory_ref=".",
        expected_subject_ref=SUBJECT,
        expected_viewport=VIEWPORT,
    )


def _codes(result) -> set[str]:
    return {item["code"] for item in result.diagnostics}


def test_dirty_checkout_and_modified_helper_are_isolated_by_pinned_worktree(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    (source / TOOL).write_text("raise SystemExit('dirty adapter executed')\n", encoding="utf-8")
    (source / "scripts/capture_helper.py").write_text('MARKER = "dirty-helper"\n', encoding="utf-8")

    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        verification = _verify(worktree, run, commit)
        assert verification.classification == "real_verified", verification.diagnostics
        assert verification.positive_proof_verified is True
        assert verification.value["helper_marker"] == "commit-a-helper"
        assert run.execution_record is not None
        assert run.execution_record.output_ref == "runtime/desktop.json"
        assert run.execution_record.working_directory_ref == "."
        assert run.artifact_ref == "runtime/desktop.json"
        assert verification.verified_artifact_ref == "runtime/desktop.json"
        assert verification.derived_receipt is not None
        assert verification.derived_receipt["artifact_ref"] == "runtime/desktop.json"
        assert verification.derived_receipt["working_directory_ref"] == "."
        assert verification.derived_receipt["schema"] == RUNTIME_EVIDENCE_RECEIPT_SCHEMA

    assert "dirty adapter executed" in (source / TOOL).read_text(encoding="utf-8")
    assert "dirty-helper" in (source / "scripts/capture_helper.py").read_text(encoding="utf-8")


def test_official_operational_api_creates_record_internally_and_cleans(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    result = execute_pinned_viewport_capture(
        source_repository=source,
        expected_repository=REPOSITORY,
        expected_commit=commit,
        producer_tool_ref=TOOL,
        working_directory_ref=".",
        subject_ref=SUBJECT,
        viewport=VIEWPORT,
        timeout_seconds=10,
    )
    assert result.classification == "real_verified", result.diagnostics
    assert result.execution_record_digest
    assert result.verified_repository == REPOSITORY
    assert result.verified_commit == commit


def test_caller_supplied_checkout_and_record_cannot_authorize(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = verify_viewport_evidence_run(
            run=run,
            producer_checkout=worktree.root,
            expected_repository=REPOSITORY,
            expected_commit=commit,
            expected_tool=TOOL,
            expected_subject_ref=SUBJECT,
            expected_viewport=VIEWPORT,
        )
    assert result.classification == "insufficient_evidence"
    assert result.positive_proof_verified is False
    assert "PG.EVIDENCE.RUNTIME_PINNED_WORKTREE_REQUIRED" in _codes(result)


def test_wrong_output_ref_with_identical_bytes_is_rejected(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        original = worktree.root / run.artifact_ref
        other = worktree.root / "other/desktop.json"
        other.parent.mkdir()
        other.write_bytes(original.read_bytes())
        result = _verify(worktree, replace(run, artifact_ref="other/desktop.json"), commit)
    assert result.classification == "insufficient_evidence"
    assert result.reason == OUTPUT_REF_BINDING_MISMATCH_REASON
    assert "PG.EVIDENCE.RUNTIME_OUTPUT_REF_BINDING_MISMATCH" in _codes(result)


def test_wrong_working_directory_is_rejected(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = _verify(worktree, replace(run, working_directory_ref="scripts"), commit)
    assert result.classification == "insufficient_evidence"
    assert "PG.EVIDENCE.RUNTIME_WORKING_DIRECTORY_MISMATCH" in _codes(result)


@pytest.mark.parametrize("raw", ["../runtime/desktop.json", "/runtime/desktop.json", r"C:\runtime\desktop.json"])
def test_unsafe_repository_refs_are_rejected(raw: str):
    with pytest.raises(RepoPathError):
        normalize_repo_relative_ref(raw)


def test_symlink_output_is_rejected(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        artifact = worktree.root / run.artifact_ref
        target = worktree.root / "target.json"
        target.write_bytes(artifact.read_bytes())
        artifact.unlink()
        try:
            artifact.symlink_to(target)
        except OSError:
            pytest.skip("symlink creation is unavailable")
        result = _verify(worktree, run, commit)
    assert result.classification == "insufficient_evidence"
    assert "PG.RUNTIME.REF_SYMLINK_FORBIDDEN" in _codes(result)


def test_subdirectory_identity_is_never_shortened(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = _verify(worktree, run, commit)
        assert resolve_repo_relative_file(worktree.root, run.artifact_ref).name == "desktop.json"
        assert run.artifact_ref == "runtime/desktop.json"
        assert result.verified_artifact_ref == "runtime/desktop.json"
        assert result.derived_receipt["artifact_ref"] == "runtime/desktop.json"


def test_receipt_cannot_be_built_from_unverified_result(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = _verify(worktree, replace(run, artifact_sha256="a" * 64), commit)
    assert result.classification == "insufficient_evidence"
    with pytest.raises(ValueError):
        build_runtime_evidence_receipt(verification=result)


@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    [
        (lambda run: replace(run, producer_repository="other/repo"), "PG.EVIDENCE.RUNTIME_REPOSITORY_MISMATCH"),
        (lambda run: replace(run, producer_commit="0" * 40), "PG.EVIDENCE.RUNTIME_COMMIT_MISMATCH"),
        (lambda run: replace(run, producer_tool_ref="scripts/other.py"), "PG.EVIDENCE.RUNTIME_TOOL_MISMATCH"),
        (lambda run: replace(run, execution_record=None), "PG.EVIDENCE.RUNTIME_EXECUTION_RECORD_REQUIRED"),
        (lambda run: replace(run, capture_status="started"), "PG.EVIDENCE.RUNTIME_CAPTURE_INCOMPLETE"),
        (lambda run: replace(run, validation_status="not_run"), "PG.EVIDENCE.RUNTIME_VALIDATION_NOT_ACCEPTED"),
        (lambda run: replace(run, run_id="RUN-OTHER"), "PG.EVIDENCE.RUNTIME_ARTIFACT_BINDING_MISMATCH"),
        (lambda run: replace(run, subject_ref="other-subject"), "PG.EVIDENCE.RUNTIME_SUBJECT_MISMATCH"),
        (lambda run: replace(run, viewport="tablet"), "PG.EVIDENCE.RUNTIME_VIEWPORT_MISMATCH"),
    ],
)
def test_runtime_context_mismatches_are_rejected(tmp_path: Path, mutator, expected_code: str):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = _verify(worktree, mutator(run), commit)
    assert result.classification in {"insufficient_evidence", "synthetic"}
    assert result.positive_proof_verified is False
    assert expected_code in _codes(result)


def test_failed_process_and_artifact_mutation_are_rejected(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        assert run.execution_record is not None
        failed = replace(run.execution_record, exit_code=1, failure_code="capture_failed")
        failed_result = _verify(worktree, replace(run, execution_record=failed), commit)
        assert "PG.EVIDENCE.RUNTIME_EXECUTION_FAILED" in _codes(failed_result)

        artifact = worktree.root / run.artifact_ref
        value = json.loads(artifact.read_text(encoding="utf-8"))
        value["mutated"] = True
        artifact.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        mutation_result = _verify(worktree, run, commit)
        assert "PG.EVIDENCE.RUNTIME_OUTPUT_HASH_BINDING_MISMATCH" in _codes(mutation_result)


def _worktree_listing(source: Path) -> str:
    return _git(source, "worktree", "list", "--porcelain")


def test_operational_worktree_is_cleaned_after_process_failure(tmp_path: Path):
    source, _ = _source_repo(tmp_path)
    (source / TOOL).write_text("raise SystemExit(7)\n", encoding="utf-8")
    _git(source, "add", TOOL)
    _git(source, "commit", "--quiet", "-m", "make bounded harness fail")
    commit = _git(source, "rev-parse", "HEAD")
    before = _worktree_listing(source)

    result = execute_pinned_viewport_capture(
        source_repository=source,
        expected_repository=REPOSITORY,
        expected_commit=commit,
        producer_tool_ref=TOOL,
        working_directory_ref=".",
        subject_ref=SUBJECT,
        viewport=VIEWPORT,
        timeout_seconds=10,
    )

    assert result.classification == "insufficient_evidence"
    assert _worktree_listing(source) == before


def test_operational_worktree_is_cleaned_after_verifier_failure(tmp_path: Path):
    source, _ = _source_repo(tmp_path)
    script = (source / TOOL).read_text(encoding="utf-8")
    script = script.replace("'evidence_ref': args.subject_ref", "'evidence_ref': 'wrong-subject'")
    (source / TOOL).write_text(script, encoding="utf-8")
    _git(source, "add", TOOL)
    _git(source, "commit", "--quiet", "-m", "emit mismatched subject")
    commit = _git(source, "rev-parse", "HEAD")
    before = _worktree_listing(source)

    result = execute_pinned_viewport_capture(
        source_repository=source,
        expected_repository=REPOSITORY,
        expected_commit=commit,
        producer_tool_ref=TOOL,
        working_directory_ref=".",
        subject_ref=SUBJECT,
        viewport=VIEWPORT,
        timeout_seconds=10,
    )

    assert result.classification == "insufficient_evidence"
    assert "PG.EVIDENCE.RUNTIME_ARTIFACT_BINDING_MISMATCH" in _codes(result)
    assert _worktree_listing(source) == before


@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    [
        (lambda run: replace(run, artifact_ref=""), "PG.EVIDENCE.RUNTIME_OUTPUT_REF_BINDING_MISMATCH"),
        (
            lambda run: replace(run, execution_record=replace(run.execution_record, output_ref=None)),
            "PG.EVIDENCE.RUNTIME_OUTPUT_REF_BINDING_MISMATCH",
        ),
        (
            lambda run: replace(run, execution_record=replace(run.execution_record, output_hash=None)),
            "PG.EVIDENCE.RUNTIME_OUTPUT_HASH_BINDING_MISMATCH",
        ),
        (
            lambda run: replace(run, execution_record=replace(run.execution_record, working_directory_ref="scripts")),
            "PG.EVIDENCE.RUNTIME_WORKING_DIRECTORY_MISMATCH",
        ),
    ],
)
def test_missing_or_mismatched_record_bindings_are_rejected(tmp_path: Path, mutator, expected_code: str):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        result = _verify(worktree, mutator(run), commit)
    assert result.classification == "insufficient_evidence"
    assert expected_code in _codes(result)
