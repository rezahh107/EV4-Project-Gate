from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile

import pytest

from ev4_transition.evidence_packaging import EvidencePackagingError, package_source_evidence


def test_evidence_archive_is_external_and_records_digest(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("evidence", encoding="utf-8")
    output = tmp_path / "evidence"
    archive = output / "source.tar.gz"
    manifest = output / "manifest.json"

    result = package_source_evidence(source, archive, manifest, tested_head_sha="a" * 40)

    assert result["packaging_result"] == "success"
    assert result["tested_head_sha"] == "a" * 40
    assert result["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert json.loads(manifest.read_text(encoding="utf-8")) == result
    with tarfile.open(archive, "r:gz") as handle:
        assert handle.getnames() == ["file.txt"]


def test_evidence_archive_inside_source_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(EvidencePackagingError, match="outside source_root"):
        package_source_evidence(
            source,
            source / "self.tar.gz",
            tmp_path / "manifest.json",
            tested_head_sha="b" * 40,
        )
