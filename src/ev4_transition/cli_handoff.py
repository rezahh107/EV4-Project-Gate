from __future__ import annotations

import argparse
from typing import Any

from ev4_transition.canonical_json import canonical_dumps
from ev4_transition.presentation.status_mapping import exit_code_for_status
from ev4_transition.service.models import RepoPaths
from ev4_transition.service.producer_handoff import ProducerHandoffRequest, run_producer_handoff_request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ev4-handoff",
        description="Route one validated Producer Gate Export to Architect→CE or CE→Builder.",
    )
    parser.add_argument("source", help="Local Producer Gate Export JSON file.")
    parser.add_argument("--project-gate-repo", default=".")
    parser.add_argument("--architect-repo")
    parser.add_argument("--ce-repo")
    parser.add_argument("--builder-repo")
    parser.add_argument("--output-dir")
    parser.add_argument("--output")
    parser.add_argument("--receipt-output")
    parser.add_argument("--schema-root", default="schemas")
    parser.add_argument("--lock")
    parser.add_argument("--format", choices=["json", "persian"], default="json")
    args = parser.parse_args(argv)

    response = run_producer_handoff_request(
        ProducerHandoffRequest(
            source_path=args.source,
            repo_paths=RepoPaths(
                project_gate_repo_path=args.project_gate_repo,
                architect_repo_path=args.architect_repo,
                ce_repo_path=args.ce_repo,
                builder_repo_path=args.builder_repo,
            ),
            output_dir=args.output_dir,
            output_path=args.output,
            receipt_path=args.receipt_output,
            schema_root=args.schema_root,
            lock_path=args.lock,
        )
    )
    payload = response.to_dict()
    if args.format == "persian":
        print(_persian_summary(payload), end="")
    else:
        print(canonical_dumps(payload))
    return exit_code_for_status(response.status)


def _persian_summary(payload: dict[str, Any]) -> str:
    routing = payload.get("routing") if isinstance(payload.get("routing"), dict) else {}
    artifacts = payload.get("artifact_metadata") if isinstance(payload.get("artifact_metadata"), dict) else {}
    next_stage = artifacts.get("next_stage") if isinstance(artifacts.get("next_stage"), dict) else {}
    receipt = artifacts.get("receipt") if isinstance(artifacts.get("receipt"), dict) else {}
    lines = [
        payload.get("user_message_fa") or "وضعیت handoff مشخص نشد.",
        f"status: {payload.get('status', 'invalid')}",
        f"transition: {payload.get('resolved_transition') or 'not_resolved'}",
        f"source stage: {routing.get('producer_stage') or 'unknown'}",
        f"target stage: {routing.get('target_stage') or 'unknown'}",
        f"next-stage artifact: {next_stage.get('path') or next_stage.get('publication_state') or 'not_generated'}",
        f"receipt: {receipt.get('path') or receipt.get('publication_state') or 'not_generated'}",
        f"اقدام بعدی: {payload.get('next_action_fa') or 'diagnostics را بررسی کنید.'}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
