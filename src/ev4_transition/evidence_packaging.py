from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
from typing import Any

from ev4_transition.runners.git_archive import GitArchiveRunnerError, run_git


class EvidencePackagingError(ValueError):
    pass


def package_source_evidence(
    source_root: str | Path,
    archive_path: str | Path,
    manifest_path: str | Path,
    *,
    tested_head_sha: str,
    repository: str = "rezahh107/EV4-Project-Gate",
) -> dict[str, Any]:
    """Archive the exact Git commit tree and keep generated evidence separate."""

    source = Path(source_root).expanduser().resolve(strict=True)
    archive = Path(archive_path).expanduser().resolve()
    manifest = Path(manifest_path).expanduser().resolve()
    if not source.is_dir():
        raise EvidencePackagingError(f"source_root is not a directory: {source}")
    _reject_inside_source(source, archive, "archive_path")
    _reject_inside_source(source, manifest, "manifest_path")
    if archive == manifest:
        raise EvidencePackagingError("archive_path and manifest_path must differ")
    expected = tested_head_sha.strip()
    if len(expected) != 40 or any(char not in "0123456789abcdefABCDEF" for char in expected):
        raise EvidencePackagingError("tested_head_sha must be a full 40-character commit SHA")

    actual = run_git(source, "rev-parse", "HEAD")
    if actual != expected:
        raise EvidencePackagingError(f"tested_head_sha does not match checked-out HEAD: expected={expected} actual={actual}")
    run_git(source, "cat-file", "-e", f"{expected}^{{commit}}")
    tree_sha = run_git(source, "rev-parse", f"{expected}^{{tree}}")
    tracked_entries = _git_tree_entries(source, expected)

    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=archive.name + ".", suffix=".tmp", dir=archive.parent)
    os.close(descriptor)
    temp_archive = Path(temp_name)
    try:
        run_git(source, "archive", "--format=tar", f"--output={temp_archive}", expected)
        archived_entries = _archive_file_entries(temp_archive)
        if archived_entries != tracked_entries:
            missing = sorted(tracked_entries - archived_entries)
            extra = sorted(archived_entries - tracked_entries)
            raise EvidencePackagingError(
                f"git archive file set differs from commit tree: missing={missing[:10]} extra={extra[:10]}"
            )
        digest = _sha256_file(temp_archive)
        os.replace(temp_archive, archive)
    except Exception:
        temp_archive.unlink(missing_ok=True)
        raise

    payload: dict[str, Any] = {
        "schema_version": "ev4-ci-source-evidence.v2",
        "repository": repository,
        "commit_sha": expected,
        "tree_sha": tree_sha,
        "packaging_method": "git_archive",
        "archive_format": "tar",
        "archive_path": str(archive),
        "archive_sha256": digest,
        "tracked_entry_count": len(tracked_entries),
        "generated_files_included": False,
        "packaging_result": "success",
    }
    temp_manifest = manifest.with_suffix(manifest.suffix + ".tmp")
    temp_manifest.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_manifest, manifest)
    return payload


def _git_tree_entries(source: Path, commit_sha: str) -> set[str]:
    raw = run_git(source, "ls-tree", "-r", "-z", "--name-only", commit_sha)
    return {item for item in raw.split("\0") if item}


def _archive_file_entries(path: Path) -> set[str]:
    with tarfile.open(path, "r:") as handle:
        return {member.name.rstrip("/") for member in handle.getmembers() if member.isfile() or member.issym()}


def _reject_inside_source(source: Path, candidate: Path, field: str) -> None:
    try:
        candidate.relative_to(source)
    except ValueError:
        return
    raise EvidencePackagingError(f"{field} must be outside source_root")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
