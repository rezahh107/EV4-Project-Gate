from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ev4_transition.contract_source import LocalCheckoutContractSource

REPOSITORY = "example/contracts"
CONTRACT_PATH = "contracts/lock.json"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.name=EV4 Test",
        "-c",
        "user.email=ev4@example.invalid",
        "commit",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _initialized_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    contract = repo / CONTRACT_PATH
    contract.parent.mkdir(parents=True)
    return repo, contract


def test_git_checkout_reads_declared_commit_bytes_not_working_tree(tmp_path: Path) -> None:
    repo, contract = _initialized_repo(tmp_path)
    contract.write_text("old-bytes\n", encoding="utf-8")
    accepted_commit = _commit(repo, "add accepted contract")

    contract.write_text("new-working-tree-bytes\n", encoding="utf-8")
    _commit(repo, "change current contract")

    source = LocalCheckoutContractSource({REPOSITORY: repo})

    assert source.read_bytes(REPOSITORY, accepted_commit, CONTRACT_PATH) == b"old-bytes\n"


def test_git_checkout_fails_closed_when_declared_commit_is_unavailable(tmp_path: Path) -> None:
    repo, contract = _initialized_repo(tmp_path)
    contract.write_text("known-bytes\n", encoding="utf-8")
    _commit(repo, "add known contract")
    source = LocalCheckoutContractSource({REPOSITORY: repo})

    with pytest.raises(FileNotFoundError, match="Unable to read pinned contract"):
        source.read_bytes(REPOSITORY, "0" * 40, CONTRACT_PATH)


def test_non_git_fixture_directory_reads_direct_bytes(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture"
    contract = fixture_root / CONTRACT_PATH
    contract.parent.mkdir(parents=True)
    contract.write_text("fixture-bytes\n", encoding="utf-8")
    source = LocalCheckoutContractSource({REPOSITORY: fixture_root})

    assert source.read_bytes(REPOSITORY, "fixture-only", CONTRACT_PATH) == b"fixture-bytes\n"
