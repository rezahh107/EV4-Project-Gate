from ev4_transition.io.atomic_writer import atomic_write_canonical_json, try_atomic_write_text


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
