from __future__ import annotations

import copy

import pytest

from ev4_transition.locks.manifest import validate_lock_manifest


def valid_lock_manifest() -> dict:
    return {
        "schema_version": "lock-manifest.v1",
        "transition_id": "ev4-demo-transition@1.0.0",
        "files": [
            {
                "role": "demo_schema",
                "repository": "rezahh107/EV4-Demo-Repo",
                "accepted_commit": "0123456789abcdef0123456789abcdef01234567",
                "path": "schemas/demo.schema.json",
                "contract_or_schema_id": "ev4-demo@1.0.0",
                "sha256_file_bytes": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
                "size_bytes": 123,
            }
        ],
    }


def codes(lock: dict) -> set[str]:
    return {item.code for item in validate_lock_manifest(lock)}


def test_valid_lock_manifest_has_no_structural_diagnostics():
    assert validate_lock_manifest(valid_lock_manifest()) == []


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_code"),
    [
        ("repository", "invalid-repository", "PG_LOCK_REPOSITORY_INVALID"),
        ("accepted_commit", "abc", "PG_LOCK_COMMIT_INVALID"),
        ("accepted_commit", "A" * 40, "PG_LOCK_COMMIT_INVALID"),
        ("sha256_file_bytes", "abc", "PG_LOCK_HASH_INVALID"),
        ("sha256_file_bytes", "g" * 64, "PG_LOCK_HASH_INVALID"),
        ("sha256_file_bytes", "A" * 64, "PG_LOCK_HASH_INVALID"),
        ("size_bytes", -1, "PG_LOCK_SIZE_BYTES_INVALID"),
    ],
)
def test_lock_manifest_rejects_malformed_file_entry_fields(field: str, bad_value: object, expected_code: str):
    lock = copy.deepcopy(valid_lock_manifest())
    lock["files"][0][field] = bad_value
    assert expected_code in codes(lock)


def test_lock_manifest_rejects_empty_files_array():
    lock = valid_lock_manifest()
    lock["files"] = []
    assert "PG_LOCK_FILES_EMPTY" in codes(lock)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda lock: lock.__setitem__("unexpected", True),
        lambda lock: lock["files"][0].__setitem__("unexpected", True),
    ],
)
def test_lock_manifest_rejects_unknown_fields(mutator):
    lock = copy.deepcopy(valid_lock_manifest())
    mutator(lock)
    assert "PG_LOCK_UNKNOWN_FIELD" in codes(lock)
