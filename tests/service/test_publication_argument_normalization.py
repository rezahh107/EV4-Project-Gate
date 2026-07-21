from pathlib import Path

from ev4_transition.service.producer_handoff import ProducerHandoffRequest, _publication_arguments


def test_explicit_relative_outputs_share_existing_parent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    request = ProducerHandoffRequest(
        output_path="evidence/ce-input.json",
        receipt_path="evidence/receipt.json",
    )

    output_dir, output_path, receipt_path = _publication_arguments(request)

    assert output_dir == str(evidence)
    assert output_path == "ce-input.json"
    assert receipt_path == "receipt.json"


def test_no_explicit_paths_preserves_facade_unique_directory() -> None:
    assert _publication_arguments(ProducerHandoffRequest()) == (None, None, None)
