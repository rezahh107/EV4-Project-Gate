import os

import pytest

from ev4_transition.io import atomic_writer
from ev4_transition.io.atomic_writer import AtomicWriteError, atomic_write_canonical_json, atomic_write_text, try_atomic_write_text


def test_no_success_download_when_output_write_failed(tmp_path):
    destination = tmp_path / "result.md"

    def reject_output(_path):
        raise ValueError("not ok")

    result = try_atomic_write_text(destination, "ok", validate=reject_output)
    assert result.success is False
    assert result.download_available is False
    assert result.final_path_exists is False
    assert not destination.exists()


def test_atomic_result_write_success_only_after_final_path_exists(tmp_path):
    destination = tmp_path / "result.json"
    result = atomic_write_canonical_json(destination, {"status": "accepted"})
    assert result.success is True
    assert result.final_path_exists is True
    assert result.download_available is True
    assert destination.exists()
    assert result.bytes_written == len('{"status":"accepted"}\n'.encode("utf-8"))


def test_directory_fsync_error_after_replace_is_best_effort(tmp_path, monkeypatch):
    destination = tmp_path / "result.json"
    sentinel_directory_fd = 987654
    real_fsync = os.fsync
    real_close = os.close

    monkeypatch.setattr(atomic_writer.os, "open", lambda *_args, **_kwargs: sentinel_directory_fd)

    def fsync_or_raise(fd):
        if fd == sentinel_directory_fd:
            raise OSError("directory fsync unsupported")
        return real_fsync(fd)

    def close_or_ignore(fd):
        if fd != sentinel_directory_fd:
            real_close(fd)

    monkeypatch.setattr(atomic_writer.os, "fsync", fsync_or_raise)
    monkeypatch.setattr(atomic_writer.os, "close", close_or_ignore)

    result = atomic_write_canonical_json(destination, {"status": "accepted"})

    assert result.success is True
    assert result.final_path_exists is True
    assert result.download_available is True
    assert destination.exists()


def test_file_fsync_error_before_replace_fails_write(tmp_path, monkeypatch):
    destination = tmp_path / "result.json"

    def reject_all_fsync(_fd):
        raise OSError("file fsync failed")

    monkeypatch.setattr(atomic_writer.os, "fsync", reject_all_fsync)

    with pytest.raises(AtomicWriteError):
        atomic_write_text(destination, "payload")

    assert not destination.exists()
