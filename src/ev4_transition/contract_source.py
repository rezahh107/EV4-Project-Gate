from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ev4_transition.runners.git_contracts import read_pinned_git_bytes


class ContractSource(Protocol):
    def read_bytes(self, repository: str, commit: str, path: str) -> bytes: ...


@dataclass(frozen=True)
class LocalCheckoutContractSource:
    repository_roots: dict[str, Path]

    def read_bytes(self, repository: str, commit: str, path: str) -> bytes:
        if repository not in self.repository_roots:
            raise FileNotFoundError(f"Missing specialist checkout for {repository}@{commit}.")

        root = self.repository_roots[repository]
        file_path = (root / path).resolve()
        root_resolved = root.resolve()
        if root_resolved not in file_path.parents and file_path != root_resolved:
            raise FileNotFoundError(f"Contract path escapes checkout root: {path}")

        # Real Git checkouts resolve bytes from the declared immutable commit.
        # Hermetic non-Git fixture directories retain direct-file behavior.
        if (root_resolved / ".git").exists():
            try:
                return read_pinned_git_bytes(root_resolved, commit, path)
            except FileNotFoundError as exc:
                raise FileNotFoundError(
                    f"Unable to read pinned contract {repository}@{commit}:{path}."
                ) from exc
        return file_path.read_bytes()
