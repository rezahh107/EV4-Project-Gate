from __future__ import annotations

import os
from pathlib import Path

import pytest

from ev4_transition.io import safe_publication
from ev4_transition.io.safe_publication import (
    PublicationError,
    publish_staged_group,
    stage_canonical_json,
)


def _staged_pair(tmp_path: Path):
    output = tmp_path / "ce-input.json"
    receipt = tmp_path / "a2c-receipt.json"
    staged_output = stage_canonical_json(output, {"kind": "ce-input", "value": 1})
    staged_receipt = stage_canonical_json(receipt, {"kind": "receipt", "value": 2})
    return output, receipt, staged_output, staged_receipt


def _temporary_files(tmp_path: Path) -> list[Path]:
    return sorted(tmp_path.glob(".*.tmp"))


def test_group_success_commits_both_exact_artifacts_and_removes_temporaries(tmp_path: Path):
    output, receipt, staged_output, staged_receipt = _staged_pair(tmp_path)

    records = publish_staged_group([staged_output, staged_receipt])

    assert [item["state"] for item in records] == [
        "published_verified",
        "published_verified",
    ]
    assert output.read_bytes() == staged_output.content
    assert receipt.read_bytes() == staged_receipt.content
    assert _temporary_files(tmp_path) == []


def test_second_link_failure_rolls_back_first_and_cleans_staging(tmp_path: Path, monkeypatch):
    output, receipt, staged_output, staged_receipt = _staged_pair(tmp_path)
    real_link = os.link
    calls = 0

    def fail_second_link(source, destination, *, follow_symlinks=True):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FileExistsError("forced second-link failure")
        return real_link(source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(safe_publication.os, "link", fail_second_link)

    with pytest.raises(PublicationError) as caught:
        publish_staged_group([staged_output, staged_receipt])

    assert caught.value.code == "PG.REPORT.OUTPUT_CREATED_CONCURRENTLY"
    assert caught.value.details["rollback_complete"] is True
    assert caught.value.details["persisted_paths"] == []
    assert not output.exists()
    assert not receipt.exists()
    assert _temporary_files(tmp_path) == []


def test_second_file_post_write_verification_failure_rolls_back_both(tmp_path: Path, monkeypatch):
    output, receipt, staged_output, staged_receipt = _staged_pair(tmp_path)
    real_verify = safe_publication._verify_exact_bytes
    calls = 0

    def fail_second_verification(path, expected, *, verify_json):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise PublicationError(
                "PG.TEST.SECOND_VERIFY_FAILED",
                "forced second verification failure",
                path=str(path),
            )
        return real_verify(path, expected, verify_json=verify_json)

    monkeypatch.setattr(safe_publication, "_verify_exact_bytes", fail_second_verification)

    with pytest.raises(PublicationError) as caught:
        publish_staged_group([staged_output, staged_receipt])

    assert caught.value.code == "PG.TEST.SECOND_VERIFY_FAILED"
    assert caught.value.details["rollback_complete"] is True
    assert not output.exists()
    assert not receipt.exists()
    assert _temporary_files(tmp_path) == []


def test_concurrent_receipt_destination_blocks_group_and_cleans_staging(tmp_path: Path):
    output, receipt, staged_output, staged_receipt = _staged_pair(tmp_path)
    receipt.write_text("concurrent-owner-content", encoding="utf-8")

    with pytest.raises(PublicationError) as caught:
        publish_staged_group([staged_output, staged_receipt])

    assert caught.value.code == "PG_A2C_OUTPUT_EXISTS"
    assert caught.value.details["rollback_complete"] is True
    assert not output.exists()
    assert receipt.read_text(encoding="utf-8") == "concurrent-owner-content"
    assert _temporary_files(tmp_path) == []


def test_rollback_failure_reports_original_error_and_truthful_persisted_state(tmp_path: Path, monkeypatch):
    output, receipt, staged_output, staged_receipt = _staged_pair(tmp_path)
    real_link = os.link
    calls = 0

    def fail_second_link(source, destination, *, follow_symlinks=True):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FileExistsError("forced second-link failure")
        return real_link(source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(safe_publication.os, "link", fail_second_link)
    monkeypatch.setattr(
        safe_publication,
        "_rollback_published",
        lambda paths: [f"{paths[0]}:PermissionError:forced rollback failure"],
    )

    with pytest.raises(PublicationError) as caught:
        publish_staged_group([staged_output, staged_receipt])

    assert caught.value.code == "PG.REPORT.OUTPUT_CREATED_CONCURRENTLY"
    assert caught.value.details["rollback_errors"]
    assert caught.value.details["rollback_complete"] is False
    assert str(output) in caught.value.details["persisted_paths"]
    assert output.exists()
    assert not receipt.exists()
    assert _temporary_files(tmp_path) == []
    output.unlink()
