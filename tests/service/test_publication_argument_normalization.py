from pathlib import Path

import pytest

from ev4_transition.producer_integration.path_environment import (
    PublicationPathError,
    is_absolute_path_for_platform,
    prepare_publication_paths,
    validate_publication_root,
)


def test_external_sibling_output_root_is_accepted_and_one_execution_directory_owns_all_files(tmp_path: Path) -> None:
    project_gate = tmp_path / "EV4 Shared Contracts"
    project_gate.mkdir()
    output_root = tmp_path / "EV4 Project Gate Outputs"

    paths = prepare_publication_paths(
        output_root,
        output_filename="ce-input.json",
        receipt_filename="project-gate-a2c-receipt.json",
        workspace=project_gate,
    )

    assert paths.output_root == output_root.resolve()
    assert paths.execution_directory.parent == output_root.resolve()
    assert {path.parent for path in paths.all_paths()} == {paths.execution_directory}
    assert {path.name for path in paths.all_paths()} == {
        "ce-input.json",
        "project-gate-a2c-receipt.json",
        "result.json",
        "report.md",
        "report.html",
    }


def test_preflight_validates_prospective_root_without_creating_it(tmp_path: Path) -> None:
    output_root = tmp_path / "future" / "outputs"
    validated, diagnostic = validate_publication_root(output_root, create=False)
    assert diagnostic is None
    assert validated == output_root.resolve()
    assert not output_root.exists()


def test_regular_file_and_advanced_path_escape_fail_closed(tmp_path: Path) -> None:
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("x", encoding="utf-8")
    _, diagnostic = validate_publication_root(output_file, create=False)
    assert diagnostic is not None
    assert diagnostic["code"] == "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE"

    with pytest.raises(PublicationPathError) as excinfo:
        prepare_publication_paths(
            tmp_path / "outputs",
            output_filename="ce-input.json",
            receipt_filename="project-gate-a2c-receipt.json",
            output_path="../escape.json",
        )
    assert excinfo.value.diagnostic["code"] == "PG_INT_ADVANCED_PUBLICATION_PATH_UNSUPPORTED"


def test_windows_drive_qualified_semantics_are_platform_aware() -> None:
    assert is_absolute_path_for_platform(r"E:\\GitHub\\EV4 Project Gate Outputs", "nt") is True
    assert is_absolute_path_for_platform(r"E:\\GitHub\\EV4 Project Gate Outputs", "posix") is False
