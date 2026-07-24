from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ev4_transition.runners import repository_identity
from ev4_transition.runners.repository_identity import (
    PinnedWorktreeError,
    materialize_pinned_worktree,
)

REPOSITORY = "rezahh107/EV4-Builder-Assistant-Repo"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def _repo(tmp_path: Path, *, repository: str = REPOSITORY) -> tuple[Path, str]:
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "EV4 Tests")
    _git(root, "remote", "add", "origin", f"https://github.com/{repository}.git")
    (root / "tracked.txt").write_text("commit-a\n", encoding="utf-8")
    _git(root, "add", "tracked.txt")
    _git(root, "commit", "--quiet", "-m", "commit A")
    return root, _git(root, "rev-parse", "HEAD")


def test_materializes_clean_detached_exact_commit_and_cleans_after_success(tmp_path: Path):
    source, commit = _repo(tmp_path)
    (source / "tracked.txt").write_text("dirty operator bytes\n", encoding="utf-8")
    (source / "untracked.txt").write_text("operator only\n", encoding="utf-8")
    materialized: Path | None = None

    with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
        materialized = worktree.root
        assert worktree.repository == REPOSITORY
        assert worktree.commit == commit
        assert worktree.clean_verified is True
        assert (worktree.root / "tracked.txt").read_text(encoding="utf-8") == "commit-a\n"
        assert not (worktree.root / "untracked.txt").exists()
        assert _git(worktree.root, "status", "--porcelain=v1", "--untracked-files=all") == ""

    assert materialized is not None and not materialized.exists()
    assert (source / "tracked.txt").read_text(encoding="utf-8") == "dirty operator bytes\n"
    assert (source / "untracked.txt").read_text(encoding="utf-8") == "operator only\n"


def test_missing_commit_is_rejected(tmp_path: Path):
    source, _ = _repo(tmp_path)
    with pytest.raises(PinnedWorktreeError) as exc:
        with materialize_pinned_worktree(source, REPOSITORY, "0" * 40):
            pass
    assert exc.value.code == "PG.RUNTIME.PINNED_COMMIT_MISSING"


def test_wrong_repository_is_rejected(tmp_path: Path):
    source, commit = _repo(tmp_path, repository="other/repo")
    with pytest.raises(PinnedWorktreeError) as exc:
        with materialize_pinned_worktree(source, REPOSITORY, commit):
            pass
    assert exc.value.code == "PG_REPOSITORY_IDENTITY_MISMATCH"


def test_worktree_is_cleaned_after_body_failure(tmp_path: Path):
    source, commit = _repo(tmp_path)
    materialized: Path | None = None
    with pytest.raises(RuntimeError, match="process failed"):
        with materialize_pinned_worktree(source, REPOSITORY, commit) as worktree:
            materialized = worktree.root
            raise RuntimeError("process failed")
    assert materialized is not None and not materialized.exists()


def test_cleanup_failure_is_reported_without_hiding_persisted_state(tmp_path: Path, monkeypatch):
    source, commit = _repo(tmp_path)
    original = repository_identity._run_git
    failed_once = False

    def fail_remove(root: Path, *args: str):
        nonlocal failed_once
        if args[:3] == ("worktree", "remove", "--force") and not failed_once:
            failed_once = True
            return 1, "", "forced remove failure"
        return original(root, *args)

    monkeypatch.setattr(repository_identity, "_run_git", fail_remove)
    diagnostics: list[dict] = []
    with pytest.raises(PinnedWorktreeError) as exc:
        with materialize_pinned_worktree(
            source,
            REPOSITORY,
            commit,
            cleanup_diagnostics=diagnostics,
        ):
            pass
    assert exc.value.code == "PG.RUNTIME.WORKTREE_CLEANUP_FAILED"
    assert any(item["code"] == "PG.RUNTIME.WORKTREE_REMOVE_FAILED" for item in diagnostics)
