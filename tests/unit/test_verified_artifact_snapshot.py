from __future__ import annotations

import hashlib
import json
import subprocess
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from ev4_transition.io import safe_publication
from ev4_transition.io.safe_publication import (
    PublicationError,
    publish_staged_group,
    stage_canonical_json,
    stage_verified_artifact_snapshot,
    verify_published_artifact_snapshot,
)
from ev4_transition.runners import repository_identity
from ev4_transition.runners.repository_identity import materialize_pinned_worktree
from ev4_transition.verified_artifact import VerifiedArtifactSnapshot
from ev4_transition import viewport_runtime
from ev4_transition.viewport_runtime import (
    ViewportEvidenceRun,
    execute_pinned_viewport_capture,
    execute_viewport_capture,
    verify_viewport_evidence_run,
)

REPOSITORY = "rezahh107/EV4-Builder-Assistant-Repo"
TOOL = "scripts/capture-viewports.py"
SUBJECT = "desktop-proof"
VIEWPORT = "desktop"
DISTINCTIVE = "SNAPSHOT-BYTES-MUST-NOT-APPEAR-IN-REPR"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def _expected_bytes(*, padding_size: int = 0) -> bytes:
    padding = "x" * padding_size
    return (
        "{\n"
        f'  "viewport": "{VIEWPORT}",\n'
        f'  "evidence_ref": "{SUBJECT}",\n'
        '  "run_id": "RUN-DESKTOP",\n'
        '  "status": "confirmed",\n'
        f'  "marker": "{DISTINCTIVE}",\n'
        f'  "padding": "{padding}"\n'
        "}\n"
    ).encode("utf-8")


def _source_repo(tmp_path: Path, *, padding_size: int = 0) -> tuple[Path, str]:
    root = tmp_path / "builder"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "EV4 Tests")
    _git(root, "remote", "add", "origin", f"https://github.com/{REPOSITORY}.git")
    tool = root / TOOL
    tool.parent.mkdir(parents=True)
    tool.write_text(
        f'''from __future__ import annotations
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--subject-ref", required=True)
parser.add_argument("--viewport", required=True)
args = parser.parse_args()
run_id = f"RUN-{{args.viewport.upper()}}"
artifact_ref = f"runtime/{{args.viewport}}.json"
padding = "x" * {padding_size}
raw = (
    "{{\\n"
    f'  "viewport": "{{args.viewport}}",\\n'
    f'  "evidence_ref": "{{args.subject_ref}}",\\n'
    f'  "run_id": "{{run_id}}",\\n'
    '  "status": "confirmed",\\n'
    '  "marker": "{DISTINCTIVE}",\\n'
    f'  "padding": "{{padding}}"\\n'
    "}}\\n"
).encode("utf-8")
artifact = Path(artifact_ref)
artifact.parent.mkdir(parents=True, exist_ok=True)
artifact.write_bytes(raw)
print(json.dumps({{
    "status": "valid",
    "run_id": run_id,
    "artifact_ref": artifact_ref,
    "capture_status": "completed",
    "validation_status": "accepted",
}}, sort_keys=True))
''',
        encoding="utf-8",
    )
    _git(root, "add", TOOL)
    _git(root, "commit", "--quiet", "-m", "add exact-byte viewport harness")
    return root, _git(root, "rev-parse", "HEAD")


def _execute(worktree) -> ViewportEvidenceRun:
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


def _with_artifact_bytes(run: ViewportEvidenceRun, raw: bytes) -> ViewportEvidenceRun:
    digest = hashlib.sha256(raw).hexdigest()
    assert run.execution_record is not None
    return replace(
        run,
        artifact_sha256=digest,
        execution_record=replace(run.execution_record, output_hash=digest),
    )


def test_exact_original_bytes_survive_worktree_cleanup(tmp_path: Path, monkeypatch):
    source, commit = _source_repo(tmp_path)
    materialized: list[Path] = []
    artifact_reads = 0
    real_materialize = viewport_runtime.materialize_pinned_worktree
    real_read_bytes = Path.read_bytes

    def counting_read_bytes(path: Path) -> bytes:
        nonlocal artifact_reads
        if path.as_posix().endswith("/runtime/desktop.json"):
            artifact_reads += 1
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counting_read_bytes)

    @contextmanager
    def recording_materialize(*args, **kwargs):
        with real_materialize(*args, **kwargs) as worktree:
            materialized.append(worktree.root)
            yield worktree

    monkeypatch.setattr(viewport_runtime, "materialize_pinned_worktree", recording_materialize)
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

    expected = _expected_bytes()
    assert result.classification == "real_verified", result.diagnostics
    assert result.artifact_snapshot is not None
    assert result.artifact_snapshot.exact_bytes == expected
    assert result.artifact_snapshot.sha256 == result.actual_sha256
    assert result.artifact_snapshot.byte_length == len(expected)
    assert result.ephemeral_artifact_path is None
    assert result.verified_artifact_path is None
    assert artifact_reads == 1
    assert materialized and not materialized[0].exists()


def test_receipt_uses_snapshot_metadata_only(tmp_path: Path):
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
    snapshot = result.artifact_snapshot
    receipt = result.derived_receipt
    assert snapshot is not None and receipt is not None
    assert receipt["artifact_ref"] == snapshot.artifact_ref
    assert receipt["artifact_sha256"] == snapshot.sha256
    assert receipt["artifact_byte_length"] == snapshot.byte_length
    assert "exact_bytes" not in receipt


def test_noncanonical_json_is_published_without_reserialization(tmp_path: Path, monkeypatch):
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
    snapshot = result.artifact_snapshot
    assert snapshot is not None
    expected = _expected_bytes()
    assert snapshot.exact_bytes == expected

    def forbidden(*_args, **_kwargs):
        raise AssertionError("JSON serialization is forbidden for snapshot publication")

    monkeypatch.setattr(safe_publication, "canonical_dumps", forbidden)
    monkeypatch.setattr(json, "dumps", forbidden)
    destination = tmp_path / "published.json"
    staged = stage_verified_artifact_snapshot(destination, snapshot)
    records = publish_staged_group([staged])

    assert records[0]["state"] == "published_verified"
    assert destination.read_bytes() == expected
    assert verify_published_artifact_snapshot(destination, snapshot) == snapshot.metadata()


def test_snapshot_integrity_and_reference_are_constructor_invariants():
    payload = b'{"ok": true}\n'
    digest = hashlib.sha256(payload).hexdigest()
    valid = VerifiedArtifactSnapshot.from_verified_bytes(
        artifact_ref="runtime/desktop.json",
        exact_bytes=payload,
    )
    valid.validate_integrity()

    with pytest.raises(ValueError, match="SHA-256"):
        VerifiedArtifactSnapshot("runtime/desktop.json", payload, "0" * 64, len(payload))
    with pytest.raises(ValueError, match="length"):
        VerifiedArtifactSnapshot("runtime/desktop.json", payload, digest, len(payload) + 1)
    with pytest.raises(ValueError):
        VerifiedArtifactSnapshot.from_verified_bytes(
            artifact_ref="../runtime/desktop.json",
            exact_bytes=payload,
        )


def test_failed_verifications_never_return_snapshot(tmp_path: Path):
    source, commit = _source_repo(tmp_path)
    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        run = _execute(worktree)
        assert run.execution_record is not None
        cases = [
            replace(run, producer_repository="other/repo"),
            replace(run, producer_commit="0" * 40),
            replace(run, producer_tool_ref="scripts/other.py"),
            replace(run, working_directory_ref="scripts"),
            replace(run, artifact_ref="other/desktop.json"),
            replace(run, artifact_sha256="0" * 64),
            replace(run, execution_record=replace(run.execution_record, exit_code=1, failure_code="failed")),
            replace(run, subject_ref="other-subject"),
            replace(run, viewport="tablet"),
            replace(run, capture_status="started"),
            replace(run, validation_status="not_run"),
        ]
        for candidate in cases:
            result = _verify(worktree, candidate, commit)
            assert result.positive_proof_verified is False
            assert result.artifact_snapshot is None

        artifact = worktree.root / run.artifact_ref
        invalid_json = b"not-json\n"
        artifact.write_bytes(invalid_json)
        result = _verify(worktree, _with_artifact_bytes(run, invalid_json), commit)
        assert result.artifact_snapshot is None

        schema_failure = b'{"evidence_ref":"desktop-proof","viewport":"desktop","run_id":"RUN-DESKTOP"}\n'
        artifact.write_bytes(schema_failure)
        result = _verify(worktree, _with_artifact_bytes(run, schema_failure), commit)
        assert result.artifact_snapshot is None

        synthetic = b'{"evidence_ref":"desktop-proof","viewport":"desktop","run_id":"RUN-DESKTOP","status":"confirmed","source":"synthetic_fixture"}\n'
        artifact.write_bytes(synthetic)
        result = _verify(worktree, _with_artifact_bytes(run, synthetic), commit)
        assert result.classification == "synthetic"
        assert result.artifact_snapshot is None


def test_cleanup_failure_revokes_snapshot_and_receipt(tmp_path: Path, monkeypatch):
    source, commit = _source_repo(tmp_path)
    real_run_git = repository_identity._run_git
    failed_once = False

    def fail_remove(root: Path, *args: str):
        nonlocal failed_once
        if args[:3] == ("worktree", "remove", "--force") and not failed_once:
            failed_once = True
            return 1, "", "forced remove failure"
        return real_run_git(root, *args)

    monkeypatch.setattr(repository_identity, "_run_git", fail_remove)
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
    assert result.positive_proof_verified is False
    assert result.reason == "pinned_worktree_cleanup_failed"
    assert result.artifact_snapshot is None
    assert result.ephemeral_artifact_path is None
    assert result.derived_receipt is None


def test_group_post_write_mutation_rolls_back_snapshot_and_receipt(tmp_path: Path, monkeypatch):
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
    snapshot = result.artifact_snapshot
    assert snapshot is not None and result.derived_receipt is not None
    artifact_destination = tmp_path / "viewport.json"
    receipt_destination = tmp_path / "viewport.receipt.json"
    staged_artifact = stage_verified_artifact_snapshot(artifact_destination, snapshot)
    staged_receipt = stage_canonical_json(receipt_destination, result.derived_receipt)

    real_verify = safe_publication._verify_exact_bytes
    mutated = False

    def mutate_then_verify(path, expected, *, verify_json):
        nonlocal mutated
        if Path(path) == artifact_destination and not mutated:
            mutated = True
            artifact_destination.write_bytes(b'{"mutated":true}\n')
        return real_verify(path, expected, verify_json=verify_json)

    monkeypatch.setattr(safe_publication, "_verify_exact_bytes", mutate_then_verify)
    with pytest.raises(PublicationError):
        publish_staged_group([staged_artifact, staged_receipt])

    assert not artifact_destination.exists()
    assert not receipt_destination.exists()
    assert not staged_artifact.temporary_path.exists()
    assert not staged_receipt.temporary_path.exists()


def test_metadata_and_repr_never_expose_raw_snapshot_bytes(tmp_path: Path):
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
    snapshot = result.artifact_snapshot
    assert snapshot is not None
    destination = tmp_path / "staged.json"
    staged = stage_verified_artifact_snapshot(destination, snapshot)
    try:
        assert "exact_bytes=" not in repr(snapshot)
        assert "exact_bytes=" not in repr(result)
        assert "content=" not in repr(staged)
        encoded = json.dumps(snapshot.metadata(), sort_keys=True)
        assert "exact_bytes" not in encoded
        assert DISTINCTIVE not in encoded
    finally:
        staged.temporary_path.unlink(missing_ok=True)


def test_bounded_multimegabyte_snapshot_is_not_truncated(tmp_path: Path):
    padding_size = 2 * 1024 * 1024
    source, commit = _source_repo(tmp_path, padding_size=padding_size)
    result = execute_pinned_viewport_capture(
        source_repository=source,
        expected_repository=REPOSITORY,
        expected_commit=commit,
        producer_tool_ref=TOOL,
        working_directory_ref=".",
        subject_ref=SUBJECT,
        viewport=VIEWPORT,
        timeout_seconds=20,
    )
    snapshot = result.artifact_snapshot
    expected = _expected_bytes(padding_size=padding_size)
    assert snapshot is not None
    assert snapshot.exact_bytes == expected
    assert snapshot.byte_length == len(expected)
    assert snapshot.sha256 == hashlib.sha256(expected).hexdigest()
    destination = tmp_path / "large.json"
    staged = stage_verified_artifact_snapshot(destination, snapshot)
    publish_staged_group([staged])
    assert destination.read_bytes() == expected
