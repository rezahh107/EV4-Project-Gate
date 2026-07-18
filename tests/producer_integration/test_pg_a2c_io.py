from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ev4_transition.io.safe_publication import (
    PublicationError,
    publish_staged_json,
    resolve_publication_paths,
    stage_canonical_json,
)
from ev4_transition.io.secure_snapshot import (
    SnapshotError,
    capture_json_snapshot,
    verify_snapshot_unchanged,
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def test_snapshot_captures_exact_bytes_and_rejects_later_mutation(tmp_path: Path):
    source = tmp_path / "architect-project-gate.json"
    write_json(source, {"schema_version": "producer-gate-export.v1", "value": 1})
    snapshot = capture_json_snapshot(source)
    assert snapshot.content == source.read_bytes()
    assert snapshot.value["value"] == 1
    write_json(source, {"schema_version": "producer-gate-export.v1", "value": 2})
    with pytest.raises(SnapshotError) as exc:
        verify_snapshot_unchanged(snapshot)
    assert exc.value.code in {
        "PG_A2C_INPUT_REPLACED_BEFORE_PUBLICATION",
        "PG_A2C_INPUT_MUTATED_BEFORE_PUBLICATION",
    }


def test_snapshot_rejects_non_finite_json(tmp_path: Path):
    source = tmp_path / "architect-project-gate.json"
    source.write_text('{"value":NaN}\n', encoding="utf-8")
    with pytest.raises(SnapshotError) as exc:
        capture_json_snapshot(source)
    assert exc.value.code == "MALFORMED_JSON"


def test_snapshot_rejects_symlink_input(tmp_path: Path):
    target = tmp_path / "target.json"
    write_json(target, {"ok": True})
    alias = tmp_path / "architect-project-gate.json"
    try:
        alias.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(SnapshotError) as exc:
        capture_json_snapshot(alias)
    assert exc.value.code == "PG_A2C_INPUT_SYMLINK_FORBIDDEN"


def test_publication_rejects_collisions_traversal_and_existing_output(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "architect-project-gate.json"
    write_json(source, {"ok": True})
    with pytest.raises(PublicationError) as exc:
        resolve_publication_paths(source_path=source, output_path="same.json", receipt_path="same.json")
    assert exc.value.code == "PG_A2C_OUTPUT_PATH_COLLISION"
    with pytest.raises(PublicationError) as exc:
        resolve_publication_paths(source_path=source, output_path="../outside.json", receipt_path="receipt.json")
    assert exc.value.code == "PG_A2C_PATH_TRAVERSAL_FORBIDDEN"
    output = tmp_path / "ce-input.json"
    output.write_text("occupied", encoding="utf-8")
    with pytest.raises(PublicationError) as exc:
        resolve_publication_paths(source_path=source, output_path=output, receipt_path="receipt.json")
    assert exc.value.code == "PG_A2C_OUTPUT_EXISTS"


def test_staged_publication_is_canonical_atomic_and_no_overwrite(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "architect-project-gate.json"
    write_json(source, {"ok": True})
    output, _ = resolve_publication_paths(source_path=source, output_path="ce-input.json", receipt_path="receipt.json")
    staged = stage_canonical_json(output, {"z": "معماری", "a": 1})
    result = publish_staged_json(staged)
    assert result["state"] == "published_verified"
    assert output.read_bytes() == b'{"a":1,"z":"\xd9\x85\xd8\xb9\xd9\x85\xd8\xa7\xd8\xb1\xdb\x8c"}\n'
    staged_again = stage_canonical_json(output, {"a": 1})
    with pytest.raises(PublicationError) as exc:
        publish_staged_json(staged_again)
    assert exc.value.code in {"PG_A2C_OUTPUT_EXISTS", "PG_A2C_OUTPUT_CREATED_CONCURRENTLY"}
    staged_again.temporary_path.unlink(missing_ok=True)


def test_output_symlink_is_rejected(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "architect-project-gate.json"
    write_json(source, {"ok": True})
    target = tmp_path / "target.json"
    output = tmp_path / "ce-input.json"
    try:
        output.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(PublicationError) as exc:
        resolve_publication_paths(source_path=source, output_path=output, receipt_path="receipt.json")
    assert exc.value.code == "PG_A2C_OUTPUT_SYMLINK_FORBIDDEN"
