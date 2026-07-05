from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RepoRef:
    owner_repo: str
    commit: str
    root: Path


class RepoAccess(Protocol):
    def resolve(self, owner_repo: str, commit: str) -> RepoRef:
        """Resolve a pinned owner repository to a local deterministic checkout."""

    def read_bytes(self, owner_repo: str, commit: str, path: str) -> bytes:
        """Read file bytes from a pinned local checkout."""

    def exists(self, owner_repo: str, commit: str, path: str) -> bool:
        """Return whether a repository-relative path exists in a pinned checkout."""
