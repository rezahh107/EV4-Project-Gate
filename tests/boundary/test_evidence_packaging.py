from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

import pytest

from ev4_transition.evidence_packaging import EvidencePackagingError, package_source_evidence


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "tests@example.com")
    _git(repo, "config", "user.name", "EV4 Tests")
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (repo / "nested").mkdir()
    (repo / "nested" / "file.json").write_text("{}\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt", "nested/file.json")
    _git(repo, "commit", "-m", "fixture")
    return repo, _git(repo, "rev-parse", "HEAD"), _git(repo, "rev-parse", "HEAD^{tree}")


def test_git_archive_excludes_generated_and_untracked_files(tmp_path: Path) -> None:
    source, head, tree = _repo(tmp_path)
    (source / "build").mkdir()
    (source / "build" / "generated.py").write_text("generated", encoding="utf-8")
    (source / "src" / "example.egg-info").mkdir(parents=True)
    (source / "src" / "example.egg-info" / "PKG-INFO").write_text("generated", encoding="utf-8")
    (source / "arbitrary-untracked.txt").write_text("untracked", encoding="utf-8")
    output = tmp_path / "evidence"
    archive = output / "source.tar"
    manifest = output / "manifest.json"

    result = package_source_evidence(source, archive, manifest, tested_head_sha=head)

    assert result == json.loads(manifest.read_text(encoding="utf-8"))
    assert result["schema_version"] == "ev4-ci-source-evidence.v2"
    assert result["commit_sha"] == head
    assert result["tree_sha"] == tree
    assert result["packaging_method"] == "git_archive"
    assert result["archive_format"] == "tar"
    assert result["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert result["tracked_entry_count"] == 2
    assert result["generated_files_included"] is False
    with tarfile.open(archive, "r:") as handle:
        names = {member.name.rstrip("/") for member in handle.getmembers() if member.isfile()}
    assert names == {"tracked.txt", "nested/file.json"}
    assert not any(name.startswith("build/") or ".egg-info/" in name for name in names)


def test_wrong_expected_head_fails(tmp_path: Path) -> None:
    source, _, _ = _repo(tmp_path)
    with pytest.raises(EvidencePackagingError, match="does not match checked-out HEAD"):
        package_source_evidence(
            source,
            tmp_path / "evidence" / "source.tar",
            tmp_path / "evidence" / "manifest.json",
            tested_head_sha="a" * 40,
        )


def test_archive_and_manifest_must_be_outside_checkout(tmp_path: Path) -> None:
    source, head, _ = _repo(tmp_path)
    with pytest.raises(EvidencePackagingError, match="outside source_root"):
        package_source_evidence(
            source,
            source / "source.tar",
            tmp_path / "manifest.json",
            tested_head_sha=head,
        )
    with pytest.raises(EvidencePackagingError, match="outside source_root"):
        package_source_evidence(
            source,
            tmp_path / "source.tar",
            source / "manifest.json",
            tested_head_sha=head,
        )
