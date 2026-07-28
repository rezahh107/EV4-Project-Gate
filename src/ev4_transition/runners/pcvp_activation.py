from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from ev4_transition.canonical_json import load_json_file

from .pcvp_owner import (
    CANONICAL_COMMIT,
    CANONICAL_REPOSITORY,
    LOCK_PATH,
    _blob_sha,
    _clean_node_environment,
    _extract_regular_archive,
    _git,
    _remote_matches,
)

ACTIVATION_COMMIT = "ad0e7235929d7f6d847724f6b4d1a6a3c57453db"
ACTIVATION_ID = "EV4-PCVP-ACT-ARCH-PG-CE-20260728-R1"
ACTIVATION_EDGE = "ARCHITECT_TO_PROJECT_GATE_TO_CE"
DISABLED_EDGES = [
    "CE_TO_BUILDER",
    "BUILDER_TO_RESPONSIVE",
    "RESPONSIVE_TO_FINAL",
]
ACTIVATION_RECORD_PATH = "kernel/pcvp/pcvp-activation.v1.json"
ACTIVATION_SCHEMA_PATH = "kernel/pcvp/pcvp-activation.v1.schema.json"
ACTIVATION_VALIDATOR_PATH = "kernel/validator/pcvp-activation-v1.mjs"
ACTIVATION_RUNNER_PATH = "tools/validate-pcvp-activation-v1.mjs"
ACTIVATION_SCOPE_PATH = "planning/governance/scopes/pcvp-v1-activation.scope.json"


def validate_first_edge_activation(
    repository_root: str | Path,
    decision_kernel_repo: str | Path | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Execute the exact Decision Kernel staged-activation authority fail closed.

    The supplied checkout remains the immutable PCVP policy checkout at
    ``CANONICAL_COMMIT``. The separately pinned activation commit is materialized
    from Git object bytes into a disposable tree and its official runner executes
    the canonical ``validateActivationRecord()`` implementation there.
    """

    if decision_kernel_repo is None:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "An exact Decision Kernel checkout is required for active PCVP propagation.",
            reason="checkout_unavailable",
        )]

    try:
        root = Path(decision_kernel_repo).expanduser().resolve(strict=True)
        project_root = Path(repository_root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "The staged activation authority checkout is unavailable.",
            reason="checkout_unavailable",
            error_type=type(exc).__name__,
        )]
    if not root.is_dir():
        return None, [_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "The staged activation authority checkout is not a directory.",
            reason="checkout_not_directory",
        )]

    git = shutil.which("git")
    node = shutil.which("node")
    npm = shutil.which("npm")
    if git is None or node is None or npm is None:
        missing = [
            name for name, value in (("git", git), ("node", node), ("npm", npm))
            if value is None
        ]
        return None, [_diag(
            "PG_PCVP_ACTIVATION_EXECUTION_UNAVAILABLE",
            "insufficient_evidence",
            "The canonical staged activation validator cannot execute.",
            reason="tool_unavailable",
            missing=missing,
        )]

    try:
        top = Path(_git(git, root, "rev-parse", "--show-toplevel")).resolve(strict=True)
        initial_head = _git(git, root, "rev-parse", "HEAD")
        initial_status = _git(git, root, "status", "--porcelain=v1", "--untracked-files=no")
        remote = _git(git, root, "remote", "get-url", "origin")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "The Decision Kernel Git identity could not be read.",
            reason="git_identity_unavailable",
            error_type=type(exc).__name__,
        )]

    identity_errors: list[dict[str, Any]] = []
    if top != root:
        identity_errors.append(_diag(
            "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
            "error",
            "The supplied Decision Kernel path is not the repository root.",
            expected=str(root),
            actual=str(top),
        ))
    if initial_head != CANONICAL_COMMIT:
        identity_errors.append(_diag(
            "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
            "error",
            "The carrier-validation checkout must remain at the immutable PCVP policy commit.",
            expected=CANONICAL_COMMIT,
            actual=initial_head,
        ))
    if not _remote_matches(remote):
        identity_errors.append(_diag(
            "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
            "error",
            "The Decision Kernel origin does not match the canonical repository.",
            expected=CANONICAL_REPOSITORY,
            actual=remote,
        ))
    if identity_errors:
        return None, identity_errors

    lock, lock_errors = _load_activation_lock(project_root)
    if lock_errors:
        return None, lock_errors
    assert lock is not None

    try:
        _git(git, root, "cat-file", "-e", f"{ACTIVATION_COMMIT}^{{commit}}")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "The exact staged activation commit is unavailable in the Decision Kernel object database.",
            reason="activation_commit_unavailable",
            expected=ACTIVATION_COMMIT,
            error_type=type(exc).__name__,
        )]

    tracked_errors = _verify_tracked_activation_files(git, root, lock)
    if tracked_errors:
        return None, tracked_errors

    response: dict[str, Any] | None = None
    execution_errors: list[dict[str, Any]] = []
    try:
        with TemporaryDirectory(prefix="ev4-pcvp-activation-") as directory:
            execution_root = Path(directory).resolve()
            archived = subprocess.run(
                [git, "-C", str(root), "archive", "--format=tar", ACTIVATION_COMMIT],
                capture_output=True,
                timeout=60,
                shell=False,
                check=False,
            )
            if archived.returncode != 0:
                execution_errors.append(_diag(
                    "PG_PCVP_ACTIVATION_EXECUTION_UNAVAILABLE",
                    "insufficient_evidence",
                    "The exact staged activation tree could not be archived.",
                    reason="git_archive_failed",
                    returncode=archived.returncode,
                ))
            else:
                try:
                    _extract_regular_archive(archived.stdout, execution_root)
                except (OSError, tarfile.TarError, ValueError) as exc:
                    execution_errors.append(_diag(
                        "PG_PCVP_ACTIVATION_EXECUTION_UNAVAILABLE",
                        "insufficient_evidence",
                        "The exact staged activation tree could not be materialized.",
                        reason="git_archive_extraction_failed",
                        error_type=type(exc).__name__,
                    ))

            if not execution_errors:
                execution_errors.extend(_verify_materialized_activation_files(execution_root, lock))

            env = _clean_node_environment()
            if not execution_errors:
                install = subprocess.run(
                    [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                    capture_output=True,
                    text=True,
                    cwd=execution_root,
                    env=env,
                    timeout=300,
                    shell=False,
                    check=False,
                )
                if install.returncode != 0:
                    execution_errors.append(_diag(
                        "PG_PCVP_ACTIVATION_EXECUTION_UNAVAILABLE",
                        "insufficient_evidence",
                        "The exact staged activation dependencies could not be installed.",
                        reason="npm_ci_failed",
                        returncode=install.returncode,
                    ))

            if not execution_errors:
                execution_errors.extend(_verify_materialized_activation_files(execution_root, lock))

            if not execution_errors:
                completed = subprocess.run(
                    [node, ACTIVATION_RUNNER_PATH],
                    capture_output=True,
                    text=True,
                    cwd=execution_root,
                    env=env,
                    timeout=90,
                    shell=False,
                    check=False,
                )
                if completed.returncode != 0:
                    execution_errors.append(_diag(
                        "PG_PCVP_ACTIVATION_REJECTED",
                        "error",
                        "The canonical Decision Kernel staged activation validator rejected the authority record.",
                        reason="validator_failed",
                        returncode=completed.returncode,
                    ))
                elif completed.stderr.strip():
                    execution_errors.append(_diag(
                        "PG_PCVP_ACTIVATION_RESPONSE_INVALID",
                        "error",
                        "The canonical staged activation runner emitted unexpected stderr output.",
                        reason="stderr_output",
                    ))
                else:
                    try:
                        parsed = json.loads(completed.stdout)
                    except (json.JSONDecodeError, TypeError) as exc:
                        execution_errors.append(_diag(
                            "PG_PCVP_ACTIVATION_RESPONSE_INVALID",
                            "error",
                            "The canonical staged activation runner did not emit valid JSON.",
                            reason="malformed_json",
                            error_type=type(exc).__name__,
                        ))
                    else:
                        if not isinstance(parsed, dict):
                            execution_errors.append(_diag(
                                "PG_PCVP_ACTIVATION_RESPONSE_INVALID",
                                "error",
                                "The canonical staged activation response must be an object.",
                                reason="response_not_object",
                            ))
                        else:
                            response = parsed
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        execution_errors.append(_diag(
            "PG_PCVP_ACTIVATION_EXECUTION_UNAVAILABLE",
            "insufficient_evidence",
            "The canonical staged activation execution environment failed.",
            reason="execution_environment_failed",
            error_type=type(exc).__name__,
        ))

    post_errors: list[dict[str, Any]] = []
    try:
        observed_head = _git(git, root, "rev-parse", "HEAD")
        observed_status = _git(git, root, "status", "--porcelain=v1", "--untracked-files=no")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        post_errors.append(_diag(
            "PG_PCVP_ACTIVATION_AUTHORITY_UNAVAILABLE",
            "insufficient_evidence",
            "The supplied Decision Kernel checkout could not be reverified after activation validation.",
            reason="post_execution_identity_unavailable",
            error_type=type(exc).__name__,
        ))
    else:
        if observed_head != initial_head:
            post_errors.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "The supplied Decision Kernel checkout HEAD changed during activation validation.",
                expected=initial_head,
                actual=observed_head,
            ))
        if observed_status != initial_status:
            post_errors.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "The supplied Decision Kernel tracked status changed during activation validation.",
                expected=initial_status,
                actual=observed_status,
            ))

    if execution_errors or post_errors:
        return None, sorted(
            [*execution_errors, *post_errors],
            key=lambda item: (item["path"], item["code"]),
        )
    assert response is not None

    response_errors = _validate_official_response(response)
    if response_errors:
        return None, response_errors
    return {
        "status": "validated",
        "authority_repository": CANONICAL_REPOSITORY,
        "immutable_policy_commit": CANONICAL_COMMIT,
        "activation_commit": ACTIVATION_COMMIT,
        "activation_id": ACTIVATION_ID,
        "enabled_edge": ACTIVATION_EDGE,
        "full_rollout_authorized": False,
        "validator": ACTIVATION_VALIDATOR_PATH,
        "runner": ACTIVATION_RUNNER_PATH,
    }, []


def _load_activation_lock(project_root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        lock = load_json_file(project_root / LOCK_PATH)
    except (OSError, ValueError, TypeError) as exc:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_LOCK_INVALID",
            "error",
            "The Project Gate PCVP execution lock could not be loaded.",
            reason="lock_unavailable",
            error_type=type(exc).__name__,
        )]
    if not isinstance(lock, dict):
        return None, [_diag(
            "PG_PCVP_ACTIVATION_LOCK_INVALID",
            "error",
            "The Project Gate PCVP execution lock must be an object.",
            reason="lock_shape_invalid",
        )]
    activation = lock.get("activation_authority")
    if not isinstance(activation, dict):
        return None, [_diag(
            "PG_PCVP_ACTIVATION_LOCK_INVALID",
            "error",
            "The exact staged activation authority pin is absent.",
            reason="activation_pin_missing",
        )]
    expected = {
        "repository": CANONICAL_REPOSITORY,
        "commit_sha": ACTIVATION_COMMIT,
        "record_path": ACTIVATION_RECORD_PATH,
        "schema_path": ACTIVATION_SCHEMA_PATH,
        "validator_path": ACTIVATION_VALIDATOR_PATH,
        "runner_path": ACTIVATION_RUNNER_PATH,
        "scope_path": ACTIVATION_SCOPE_PATH,
    }
    for key, value in expected.items():
        if activation.get(key) != value:
            return None, [_diag(
                "PG_PCVP_ACTIVATION_LOCK_INVALID",
                "error",
                "The staged activation execution identity lock drifted.",
                reason="activation_pin_mismatch",
                field=key,
                expected=value,
                actual=activation.get(key),
            )]
    records = activation.get("authority_files")
    if not isinstance(records, list):
        return None, [_diag(
            "PG_PCVP_ACTIVATION_LOCK_INVALID",
            "error",
            "The staged activation authority file set is unavailable.",
            reason="activation_file_set_invalid",
        )]
    paths = [item.get("path") for item in records if isinstance(item, dict)]
    expected_paths = {
        ACTIVATION_RECORD_PATH,
        ACTIVATION_SCHEMA_PATH,
        ACTIVATION_VALIDATOR_PATH,
        ACTIVATION_RUNNER_PATH,
        ACTIVATION_SCOPE_PATH,
        "package.json",
        "package-lock.json",
    }
    if len(records) != len(expected_paths) or set(paths) != expected_paths:
        return None, [_diag(
            "PG_PCVP_ACTIVATION_LOCK_INVALID",
            "error",
            "The staged activation authority file set is incomplete or ambiguous.",
            reason="activation_file_set_invalid",
        )]
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "git_blob_sha"}:
            return None, [_diag(
                "PG_PCVP_ACTIVATION_LOCK_INVALID",
                "error",
                "A staged activation authority file pin is malformed.",
                reason="activation_file_pin_invalid",
            )]
        blob = record.get("git_blob_sha")
        if not isinstance(blob, str) or len(blob) != 40:
            return None, [_diag(
                "PG_PCVP_ACTIVATION_LOCK_INVALID",
                "error",
                "A staged activation authority file pin lacks exact Git blob identity.",
                reason="activation_file_pin_invalid",
                path=record.get("path"),
            )]
    return activation, []


def _verify_tracked_activation_files(
    git: str,
    root: Path,
    lock: dict[str, Any],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for record in sorted(lock["authority_files"], key=lambda item: item["path"]):
        relative = record["path"]
        try:
            observed = _git(git, root, "rev-parse", f"{ACTIVATION_COMMIT}:{relative}")
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            diagnostics.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "A staged activation authority file is not tracked at the exact activation commit.",
                reason="activation_file_not_tracked",
                authority_path=relative,
                error_type=type(exc).__name__,
            ))
            continue
        if observed != record["git_blob_sha"]:
            diagnostics.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "A staged activation authority Git blob does not match the Project Gate replay pin.",
                reason="activation_file_blob_mismatch",
                authority_path=relative,
                expected=record["git_blob_sha"],
                actual=observed,
            ))
    return diagnostics


def _verify_materialized_activation_files(
    root: Path,
    lock: dict[str, Any],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for record in sorted(lock["authority_files"], key=lambda item: item["path"]):
        relative = record["path"]
        try:
            content = (root / relative).read_bytes()
        except OSError as exc:
            diagnostics.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "A staged activation authority file is unavailable in the disposable execution tree.",
                reason="activation_file_unavailable",
                authority_path=relative,
                error_type=type(exc).__name__,
            ))
            continue
        observed = _blob_sha(content)
        if observed != record["git_blob_sha"]:
            diagnostics.append(_diag(
                "PG_PCVP_ACTIVATION_IDENTITY_MISMATCH",
                "error",
                "A staged activation authority file changed during materialization or dependency installation.",
                reason="activation_materialized_blob_mismatch",
                authority_path=relative,
                expected=record["git_blob_sha"],
                actual=observed,
            ))
    return diagnostics


def _validate_official_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    expected_keys = {
        "result",
        "activation_id",
        "official_adoption_authorization",
        "enabled_edges",
        "disabled_edges",
        "full_rollout_authorized",
        "remote_prerequisites_verified",
    }
    if set(response) != expected_keys:
        return [_diag(
            "PG_PCVP_ACTIVATION_RESPONSE_INVALID",
            "error",
            "The canonical staged activation runner response shape drifted.",
            reason="response_shape_invalid",
            observed_keys=sorted(response),
        )]
    expected_values = {
        "result": "PASS",
        "activation_id": ACTIVATION_ID,
        "official_adoption_authorization": True,
        "enabled_edges": [ACTIVATION_EDGE],
        "disabled_edges": DISABLED_EDGES,
        "full_rollout_authorized": False,
        "remote_prerequisites_verified": False,
    }
    for key, expected in expected_values.items():
        if response.get(key) != expected:
            return [_diag(
                "PG_PCVP_ACTIVATION_REJECTED",
                "error",
                "The canonical staged activation authority does not authorize the exact first PCVP edge.",
                reason="activation_response_mismatch",
                field=key,
                expected=expected,
                actual=response.get(key),
            )]
    return []


def _diag(
    code: str,
    severity: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": "$.continuation_assurance",
        "message": message,
        "details": details,
        "repair_owner": "Project Gate",
    }
