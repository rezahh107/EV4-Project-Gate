from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ports import RepoRef


class RepoAccessError(ValueError):
    pass


@dataclass(frozen=True)
class LocalRepoAccess:
    checkouts: dict[tuple[str, str], Path]

    def resolve(self, owner_repo: str, commit: str) -> RepoRef:
        key = (owner_repo, commit)
        if key not in self.checkouts:
            raise RepoAccessError(f"local checkout is not registered for {owner_repo}@{commit}")
        root = Path(self.checkouts[key]).resolve()
        if not root.is_dir():
            raise RepoAccessError(f"registered local checkout does not exist for {owner_repo}@{commit}")
        return RepoRef(owner_repo=owner_repo, commit=commit, root=root)

    def read_bytes(self, owner_repo: str, commit: str, path: str) -> bytes:
        repo_ref = self.resolve(owner_repo, commit)
        target = self._resolve_repo_path(repo_ref.root, path)
        return target.read_bytes()

    def exists(self, owner_repo: str, commit: str, path: str) -> bool:
        repo_ref = self.resolve(owner_repo, commit)
        try:
            target = self._resolve_repo_path(repo_ref.root, path)
        except RepoAccessError:
            return False
        return target.exists()

    @staticmethod
    def _resolve_repo_path(root: Path, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            raise RepoAccessError("repository path must be relative")
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise RepoAccessError("repository path escapes checkout root") from exc
        return resolved
