from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


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
        return file_path.read_bytes()
