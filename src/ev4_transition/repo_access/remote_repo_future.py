from __future__ import annotations


class RemoteRepoAccessUnavailable(RuntimeError):
    pass


def unavailable_remote_repo_access() -> None:
    """Placeholder: remote connectors stay outside deterministic core in Phase 1."""

    raise RemoteRepoAccessUnavailable("remote repository access is intentionally unavailable in deterministic core")
