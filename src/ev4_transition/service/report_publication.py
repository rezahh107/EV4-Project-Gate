from __future__ import annotations

from pathlib import Path
from typing import Any

from ev4_transition.io.safe_publication import (
    PublicationError,
    publish_staged_group,
    stage_exact_bytes,
    stage_exact_text,
)
from ev4_transition.producer_integration.path_environment import AttemptPaths, prepare_attempt_paths

from .models import ReportBundle
from .reports import build_report_bundle


def publish_report_bundle(
    attempt: AttemptPaths,
    report_bundle: ReportBundle,
) -> tuple[str, list[dict[str, Any]], list[str], dict[str, Any] | None]:
    """Publish result/Markdown/HTML as one verified no-overwrite group."""

    markdown = report_bundle.markdown_report
    html = report_bundle.html_report
    if markdown is None or html is None:
        return (
            "failed",
            [],
            [],
            {
                "code": "PG.REPORT.RENDER_INCOMPLETE",
                "severity": "error",
                "path": "$.report_publication",
                "message": "All three report artifacts must render before publication.",
                "details": {
                    "markdown_available": markdown is not None,
                    "html_available": html is not None,
                    "attempt_directory": str(attempt.execution_directory),
                },
            },
        )

    staged = []
    try:
        staged = [
            stage_exact_bytes(
                attempt.result,
                report_bundle.canonical_json.encode("utf-8"),
                verify_json=True,
            ),
            stage_exact_text(attempt.report_markdown, markdown),
            stage_exact_text(attempt.report_html, html),
        ]
        metadata = publish_staged_group(staged)
    except (PublicationError, OSError, ValueError) as exc:
        for item in staged:
            item.temporary_path.unlink(missing_ok=True)
        code = exc.code if isinstance(exc, PublicationError) else "PG.REPORT.PUBLICATION_FAILED"
        details = dict(exc.details) if isinstance(exc, PublicationError) else {"error_type": type(exc).__name__}
        details["attempt_directory"] = str(attempt.execution_directory)
        return (
            "failed",
            [],
            [],
            {
                "code": code,
                "severity": "error",
                "path": "$.report_publication",
                "message": str(exc),
                "details": details,
            },
        )

    verified_paths = [item["path"] for item in metadata if _verified_file(item)]
    state = "published_verified" if len(verified_paths) == 3 else "partial"
    return state, metadata, verified_paths, None


def publish_result_payload(
    result: dict[str, Any],
    output_root: str | Path | None,
) -> tuple[str | None, list[dict[str, Any]], list[str], dict[str, Any] | None]:
    """Compatibility entrypoint that delegates all filesystem authority to service."""

    try:
        attempt = prepare_attempt_paths(output_root)
    except Exception as exc:
        diagnostic = getattr(exc, "diagnostic", None)
        if not isinstance(diagnostic, dict):
            diagnostic = {
                "code": "PG.REPORT.ATTEMPT_DIRECTORY_FAILED",
                "severity": "error",
                "path": "$.output_dir",
                "message": str(exc),
                "details": {"error_type": type(exc).__name__},
            }
        return None, [], [], diagnostic
    state, metadata, paths, diagnostic = publish_report_bundle(
        attempt,
        build_report_bundle(result),
    )
    return str(attempt.execution_directory), metadata, paths, diagnostic


def verified_existing_paths(paths: list[str]) -> list[str]:
    verified: list[str] = []
    for value in paths:
        try:
            path = Path(value)
            if path.is_file() and str(path) not in verified:
                verified.append(str(path))
        except (OSError, RuntimeError, ValueError):
            continue
    return verified


def _verified_file(metadata: dict[str, Any]) -> bool:
    if metadata.get("state") != "published_verified":
        return False
    try:
        return Path(str(metadata.get("path", ""))).is_file()
    except (OSError, RuntimeError, ValueError):
        return False
