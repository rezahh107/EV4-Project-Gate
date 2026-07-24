from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

_GITHUB_REPOSITORY = re.compile(r"(?:github\.com[:/])(?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$")


@dataclass(frozen=True)
class PinnedExecutionWorktree:
    root: Path
    repository: str
    commit: str
    clean_verified: bool = True


class PinnedWorktreeError(RuntimeError):
    def __init__(self, code: str, message: str, **details: Any):
        super().__init__(message)
        self.code = code
        self.details = details

    def to_diagnostic(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": "insufficient_evidence",
            "path": "$.runtime_execution.worktree",
            "message": str(self),
            "details": dict(self.details),
        }


def inspect_checkout(
    repo_root: str | Path,
    *,
    expected_repository: str,
    expected_commit: str | None = None,
) -> dict[str, Any]:
    """Inspect a local Git checkout without trusting caller-supplied identity fields."""

    root = Path(repo_root).resolve()
    if not root.is_dir():
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            None,
            None,
            "PG_REPOSITORY_CHECKOUT_MISSING",
            "The required local repository checkout is unavailable.",
        )

    head = _git(root, "rev-parse", "HEAD")
    remote = _git(root, "remote", "get-url", "origin")
    if head[0] != 0 or remote[0] != 0:
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            None,
            None,
            "PG_REPOSITORY_IDENTITY_UNAVAILABLE",
            "The checkout could not prove its Git HEAD and origin identity.",
        )

    actual_commit = head[1].strip().lower()
    actual_repository = _repository_slug(remote[1].strip())
    if actual_repository is None:
        return _result(
            "insufficient_evidence",
            expected_repository,
            expected_commit,
            actual_commit,
            None,
            "PG_REPOSITORY_ORIGIN_UNRECOGNIZED",
            "The checkout origin is not a recognizable GitHub repository identity.",
        )
    if actual_repository.lower() != expected_repository.lower():
        return _result(
            "invalid",
            expected_repository,
            expected_commit,
            actual_commit,
            actual_repository,
            "PG_REPOSITORY_IDENTITY_MISMATCH",
            "The checkout repository identity does not match the accepted owner repository.",
        )
    if expected_commit is not None and actual_commit != expected_commit.lower():
        return _result(
            "invalid",
            expected_repository,
            expected_commit,
            actual_commit,
            actual_repository,
            "PG_REPOSITORY_COMMIT_MISMATCH",
            "The checkout HEAD does not match the accepted immutable commit.",
        )
    return {
        "status": "accepted",
        "repository": actual_repository,
        "commit": actual_commit,
        "path": str(root),
        "diagnostics": [],
    }


def inspect_tracked_worktree_clean(repo_root: str | Path) -> dict[str, Any]:
    """Verify staged and unstaged tracked bytes remain equal to HEAD.

    Runtime output may be an untracked file, so this post-execution check
    intentionally excludes untracked paths.
    """

    root = Path(repo_root).resolve()
    result = _run_git(root, "status", "--porcelain=v1", "--untracked-files=no")
    if result[0] != 0:
        return {
            "status": "insufficient_evidence",
            "diagnostics": [{
                "code": "PG.RUNTIME.WORKTREE_STATUS_UNAVAILABLE",
                "severity": "insufficient_evidence",
                "path": "$.runtime_execution.worktree",
                "message": "Pinned execution worktree status could not be verified.",
            }],
        }
    if result[1]:
        return {
            "status": "invalid",
            "diagnostics": [{
                "code": "PG.RUNTIME.WORKTREE_TRACKED_BYTES_CHANGED",
                "severity": "error",
                "path": "$.runtime_execution.worktree",
                "message": "Tracked files in the pinned execution worktree changed during execution.",
                "details": {"status": result[1].splitlines()},
            }],
        }
    return {"status": "accepted", "diagnostics": []}


@contextmanager
def materialize_pinned_worktree(
    source_repository: str | Path,
    expected_repository: str,
    expected_commit: str,
    *,
    cleanup_diagnostics: list[dict[str, Any]] | None = None,
) -> Iterator[PinnedExecutionWorktree]:
    """Materialize a clean detached worktree at one exact local commit.

    The ordinary source checkout may be dirty. Only committed bytes from the
    pinned tree are exposed to the execution callback.
    """

    source = Path(source_repository).resolve()
    identity = inspect_checkout(source, expected_repository=expected_repository)
    if identity.get("status") != "accepted":
        first = (identity.get("diagnostics") or [{}])[0]
        raise PinnedWorktreeError(
            first.get("code", "PG.RUNTIME.SOURCE_REPOSITORY_INVALID"),
            first.get("message", "Source repository identity could not be verified."),
            expected_repository=expected_repository,
            actual_repository=identity.get("repository"),
        )

    commit = expected_commit.lower()
    exists = _run_git(source, "cat-file", "-e", f"{commit}^{{commit}}")
    if exists[0] != 0:
        raise PinnedWorktreeError(
            "PG.RUNTIME.PINNED_COMMIT_MISSING",
            "The pinned execution commit does not exist in the source repository.",
            expected_commit=commit,
            stderr=exists[2],
        )

    parent = Path(tempfile.mkdtemp(prefix="ev4-pinned-worktree-"))
    root = parent / "tree"
    added = False
    active_error: BaseException | None = None
    try:
        created = _run_git(source, "worktree", "add", "--detach", str(root), commit)
        if created[0] != 0:
            raise PinnedWorktreeError(
                "PG.RUNTIME.WORKTREE_CREATE_FAILED",
                "Detached pinned execution worktree could not be created.",
                expected_commit=commit,
                stderr=created[2],
            )
        added = True

        worktree_identity = inspect_checkout(
            root,
            expected_repository=expected_repository,
            expected_commit=commit,
        )
        if worktree_identity.get("status") != "accepted":
            first = (worktree_identity.get("diagnostics") or [{}])[0]
            raise PinnedWorktreeError(
                first.get("code", "PG.RUNTIME.WORKTREE_IDENTITY_INVALID"),
                first.get("message", "Detached worktree identity could not be verified."),
                expected_repository=expected_repository,
                expected_commit=commit,
            )

        status = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
        if status[0] != 0:
            raise PinnedWorktreeError(
                "PG.RUNTIME.WORKTREE_STATUS_UNAVAILABLE",
                "Detached worktree cleanliness could not be verified.",
                stderr=status[2],
            )
        if status[1]:
            raise PinnedWorktreeError(
                "PG.RUNTIME.WORKTREE_NOT_CLEAN",
                "Detached pinned execution worktree is not clean.",
                status=status[1].splitlines(),
            )

        yield PinnedExecutionWorktree(
            root=root.resolve(strict=True),
            repository=worktree_identity["repository"],
            commit=worktree_identity["commit"],
            clean_verified=True,
        )
    except BaseException as exc:
        active_error = exc
        raise
    finally:
        cleanup_errors: list[dict[str, Any]] = []
        if added:
            removed = _run_git(source, "worktree", "remove", "--force", str(root))
            if removed[0] != 0:
                cleanup_errors.append(_cleanup_diag(
                    "PG.RUNTIME.WORKTREE_REMOVE_FAILED",
                    "Detached execution worktree could not be removed through Git.",
                    stderr=removed[2],
                    worktree=str(root),
                ))
                try:
                    shutil.rmtree(root)
                except OSError as exc:
                    cleanup_errors.append(_cleanup_diag(
                        "PG.RUNTIME.WORKTREE_DIRECTORY_CLEANUP_FAILED",
                        "Detached execution directory could not be removed.",
                        error_type=type(exc).__name__,
                        worktree=str(root),
                    ))
            pruned = _run_git(source, "worktree", "prune")
            if pruned[0] != 0:
                cleanup_errors.append(_cleanup_diag(
                    "PG.RUNTIME.WORKTREE_PRUNE_FAILED",
                    "Git worktree metadata could not be pruned.",
                    stderr=pruned[2],
                ))
        try:
            shutil.rmtree(parent)
        except FileNotFoundError:
            pass
        except OSError as exc:
            cleanup_errors.append(_cleanup_diag(
                "PG.RUNTIME.WORKTREE_PARENT_CLEANUP_FAILED",
                "Temporary worktree parent directory could not be removed.",
                error_type=type(exc).__name__,
                parent=str(parent),
            ))

        if cleanup_diagnostics is not None:
            cleanup_diagnostics.extend(cleanup_errors)
        if cleanup_errors:
            if active_error is not None:
                active_error.add_note(f"Pinned worktree cleanup diagnostics: {cleanup_errors!r}")
            else:
                raise PinnedWorktreeError(
                    "PG.RUNTIME.WORKTREE_CLEANUP_FAILED",
                    "Pinned execution completed but worktree cleanup was not fully successful.",
                    cleanup_errors=cleanup_errors,
                )


def _cleanup_diag(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "error",
        "path": "$.runtime_execution.worktree.cleanup",
        "message": message,
        "details": details,
    }


def _git(root: Path, *args: str) -> tuple[int, str]:
    result = _run_git(root, *args)
    return result[0], result[1]


def _run_git(root: Path, *args: str) -> tuple[int, str, str]:
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "SYSTEMROOT", "WINDIR"}}
    env.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=30,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", type(exc).__name__
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _repository_slug(remote: str) -> str | None:
    match = _GITHUB_REPOSITORY.search(remote.rstrip("/"))
    return match.group("slug") if match else None


def _result(
    status: str,
    expected_repository: str,
    expected_commit: str | None,
    actual_commit: str | None,
    actual_repository: str | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    severity = "insufficient_evidence" if status == "insufficient_evidence" else "error"
    return {
        "status": status,
        "repository": actual_repository,
        "commit": actual_commit,
        "diagnostics": [
            {
                "code": code,
                "severity": severity,
                "message": message,
                "path": "$",
                "details": {
                    "expected_repository": expected_repository,
                    "expected_commit": expected_commit,
                    "actual_repository": actual_repository,
                    "actual_commit": actual_commit,
                },
            }
        ],
    }
