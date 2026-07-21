from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
from typing import Any

_EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}


class EvidencePackagingError(ValueError):
    pass


def package_source_evidence(
    source_root: str | Path,
    archive_path: str | Path,
    manifest_path: str | Path,
    *,
    tested_head_sha: str,
) -> dict[str, Any]:
    """Create a deterministic evidence carrier outside its source tree.

    The archive and manifest are rejected when located inside the source tree,
    eliminating self-inclusion and source mutation during packaging.
    """

    source = Path(source_root).expanduser().resolve(strict=True)
    archive = Path(archive_path).expanduser().resolve()
    manifest = Path(manifest_path).expanduser().resolve()
    if not source.is_dir():
        raise EvidencePackagingError(f"source_root is not a directory: {source}")
    _reject_inside_source(source, archive, "archive_path")
    _reject_inside_source(source, manifest, "manifest_path")
    if archive == manifest:
        raise EvidencePackagingError("archive_path and manifest_path must differ")
    if not tested_head_sha or len(tested_head_sha.strip()) < 7:
        raise EvidencePackagingError("tested_head_sha is required")

    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temp_archive = Path(tempfile.mkstemp(prefix=archive.name + ".", suffix=".tmp", dir=archive.parent)[1])
    try:
        with tarfile.open(temp_archive, mode="w:gz", format=tarfile.PAX_FORMAT) as handle:
            for path in sorted(source.rglob("*")):
                relative = path.relative_to(source)
                if _excluded(relative):
                    continue
                handle.add(path, arcname=relative.as_posix(), recursive=False)
        digest = _sha256_file(temp_archive)
        os.replace(temp_archive, archive)
    except Exception:
        temp_archive.unlink(missing_ok=True)
        raise

    payload: dict[str, Any] = {
        "schema_version": "ev4-ci-source-evidence.v1",
        "tested_head_sha": tested_head_sha.strip(),
        "archive_path": str(archive),
        "archive_sha256": digest,
        "packaging_result": "success",
    }
    temp_manifest = manifest.with_suffix(manifest.suffix + ".tmp")
    temp_manifest.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_manifest, manifest)
    return payload


def _reject_inside_source(source: Path, candidate: Path, field: str) -> None:
    try:
        candidate.relative_to(source)
    except ValueError:
        return
    raise EvidencePackagingError(f"{field} must be outside source_root")


def _excluded(relative: Path) -> bool:
    return any(part in _EXCLUDED_PARTS for part in relative.parts)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
