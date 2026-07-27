from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from .canonical_json import load_json_file
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics

POLICY_ID = "EV4-PCVP"
POLICY_VERSION = "1.0.0"
ARCHITECTURE_LOCK_ID = "EV4-PCVP-ROLL-LOCK-20260727-R1"
CANONICAL_REPOSITORY = "rezahh107/EV4-Decision-Kernel"
CANONICAL_COMMIT = "069a50fa243b01fa578a7c1bcb8864d9e796d34b"
LOCK_PATH = "contracts/locks/pcvp-v1.lock.json"
LOCK_SCHEMA_VERSION = "ev4-pcvp-execution-authority-lock.v1"
BUNDLE_ROOT = "kernel/pcvp/v1.0.0/bundle"
VALIDATOR_PATH = "kernel/validator/pcvp-v1.mjs"

SOURCE_STAGE_BY_PRODUCER = {
    "architect": "ARCHITECT",
    "ce": "CONSTRUCTABILITY_ENGINEER",
    "builder": "BUILDER_ASSISTANT",
    "responsive": "RESPONSIVE_ARCHITECT",
}
PROFILE_BINDINGS = {
    "ARCHITECT": {
        "path": f"{BUNDLE_ROOT}/03-PROFILES/architect.profile.yaml",
        "profile_id": "EV4-PCVP-PROFILE-ARCHITECT",
        "repository": "rezahh107/EV4-Architect-Repo",
    },
    "CONSTRUCTABILITY_ENGINEER": {
        "path": f"{BUNDLE_ROOT}/03-PROFILES/constructability.profile.yaml",
        "profile_id": "EV4-PCVP-PROFILE-CONSTRUCTABILITY",
        "repository": "rezahh107/EV4-Constructability-Engineer-Repo",
    },
    "BUILDER_ASSISTANT": {
        "path": f"{BUNDLE_ROOT}/03-PROFILES/builder.profile.yaml",
        "profile_id": "EV4-PCVP-PROFILE-BUILDER",
        "repository": "rezahh107/EV4-Builder-Assistant-Repo",
    },
    "RESPONSIVE_ARCHITECT": {
        "path": f"{BUNDLE_ROOT}/03-PROFILES/responsive.profile.yaml",
        "profile_id": "EV4-PCVP-PROFILE-RESPONSIVE",
        "repository": "rezahh107/EV4-Responsive-Architect",
    },
}

_NODE_BRIDGE = r"""
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const raw = fs.readFileSync(0, 'utf8');
let request;
try { request = JSON.parse(raw); }
catch (error) {
  process.stdout.write(JSON.stringify({schema_version:'ev4-pcvp-owner-bridge-response.v1',status:'BRIDGE_ERROR',error:{code:'REQUEST_JSON_INVALID',name:error.name,message:error.message}}));
  process.exit(0);
}
const keys = Object.keys(request).sort();
const expected = ['bundle_root','carrier_document','schema_version','validator_path'];
if (JSON.stringify(keys) !== JSON.stringify(expected) || request.schema_version !== 'ev4-pcvp-owner-bridge-request.v1' || typeof request.validator_path !== 'string' || typeof request.bundle_root !== 'string' || request.carrier_document === null || typeof request.carrier_document !== 'object' || Array.isArray(request.carrier_document)) {
  process.stdout.write(JSON.stringify({schema_version:'ev4-pcvp-owner-bridge-response.v1',status:'BRIDGE_ERROR',error:{code:'REQUEST_INVALID',name:'TypeError',message:'invalid bridge request'}}));
  process.exit(0);
}
try {
  const owner = await import(pathToFileURL(request.validator_path).href);
  if (typeof owner.validatePcvpBundle !== 'function' || typeof owner.evaluatePcvpCarrier !== 'function') throw new TypeError('required owner exports unavailable');
  const bundle = owner.validatePcvpBundle(request.bundle_root);
  const carrier = bundle.result === 'PASS' ? owner.evaluatePcvpCarrier(request.carrier_document, bundle.validateCarrier) : null;
  process.stdout.write(JSON.stringify({schema_version:'ev4-pcvp-owner-bridge-response.v1',status:'OK',bundle:{result:bundle.result,diagnostics:bundle.diagnostics,fixtures:bundle.fixtures,inventory:bundle.inventory},carrier}));
} catch (error) {
  process.stdout.write(JSON.stringify({schema_version:'ev4-pcvp-owner-bridge-response.v1',status:'BRIDGE_ERROR',error:{code:'OWNER_EXECUTION_FAILED',name:error?.name ?? 'Error',message:error?.message ?? String(error)}}));
}
""".strip()


@dataclass(frozen=True)
class OwnerAuthority:
    root: Path
    validator_path: Path
    bundle_root: Path
    profile_path: Path
    profile_binding: dict[str, str]
    git: str = "git"
    lock: dict[str, Any] | None = None
    initial_head: str = CANONICAL_COMMIT
    initial_tracked_status: str = ""
    initial_file_digests: dict[str, str] | None = None


def expected_authority_paths() -> set[str]:
    return {
        VALIDATOR_PATH,
        f"{BUNDLE_ROOT}/00-MANIFEST.yaml",
        f"{BUNDLE_ROOT}/SHA256SUMS.txt",
        f"{BUNDLE_ROOT}/04-SCHEMAS/authorization.schema.json",
        f"{BUNDLE_ROOT}/04-SCHEMAS/claim.schema.json",
        f"{BUNDLE_ROOT}/04-SCHEMAS/effect.schema.json",
        f"{BUNDLE_ROOT}/04-SCHEMAS/handoff.schema.json",
        *{item["path"] for item in PROFILE_BINDINGS.values()},
        "package.json",
        "package-lock.json",
    }


def verify_owner_authority(
    repository_root: Path,
    decision_kernel_repo: str | Path | None,
    source_stage: str | None,
) -> tuple[OwnerAuthority | None, list[Diagnostic]]:
    if decision_kernel_repo is None:
        return None, [_unverified("An exact Decision Kernel checkout is required.", reason="checkout_unavailable")]
    binding = PROFILE_BINDINGS.get(source_stage or "")
    if binding is None:
        return None, [_unverified("The source Stage has no locked Profile.", reason="profile_binding_unavailable")]
    try:
        root = Path(decision_kernel_repo).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        return None, [_unverified("The Decision Kernel checkout is unavailable.", reason="checkout_unavailable", error_type=type(exc).__name__)]
    if not root.is_dir():
        return None, [_unverified("The Decision Kernel checkout is not a directory.", reason="checkout_not_directory")]
    git = shutil.which("git")
    if git is None:
        return None, [_unverified("Git is unavailable for owner identity verification.", reason="git_unavailable")]
    try:
        top = Path(_git(git, root, "rev-parse", "--show-toplevel")).resolve(strict=True)
        head = _git(git, root, "rev-parse", "HEAD")
        remote = _git(git, root, "remote", "get-url", "origin")
        tracked_status = _git(git, root, "status", "--porcelain=v1", "--untracked-files=no")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return None, [_unverified("Owner Git identity could not be read.", reason="git_identity_unavailable", error_type=type(exc).__name__)]
    diagnostics: list[Diagnostic] = []
    if top != root:
        diagnostics.append(_unverified("The owner path is not the Git repository root.", reason="repository_root_mismatch", expected=str(root), actual=str(top)))
    if head != CANONICAL_COMMIT:
        diagnostics.append(_unverified("The owner checkout is not at the locked commit.", reason="commit_mismatch", expected=CANONICAL_COMMIT, actual=head))
    if not _remote_matches(remote):
        diagnostics.append(_unverified("The owner origin does not match the locked repository.", reason="repository_identity_mismatch", expected=CANONICAL_REPOSITORY, actual=remote))
    lock, lock_diags = _load_lock(repository_root)
    diagnostics.extend(lock_diags)
    file_digests: dict[str, str] | None = None
    if lock is not None:
        diagnostics.extend(_verify_files(root, lock, git))
        file_digests, digest_diags = _capture_file_digests(root, lock)
        diagnostics.extend(digest_diags)
    if diagnostics:
        return None, sort_diagnostics(_deduplicate(diagnostics))
    assert lock is not None and file_digests is not None
    return OwnerAuthority(
        root=root,
        validator_path=root / VALIDATOR_PATH,
        bundle_root=root / BUNDLE_ROOT,
        profile_path=root / binding["path"],
        profile_binding=binding,
        git=git,
        lock=copy.deepcopy(lock),
        initial_head=head,
        initial_tracked_status=tracked_status,
        initial_file_digests=file_digests,
    ), []


def run_owner_bridge(authority: OwnerAuthority, carrier_document: dict[str, Any]) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None:
        return None, [_execution_unavailable("Node.js is unavailable.", reason="node_unavailable")]
    if npm is None:
        return None, [_execution_unavailable("npm is unavailable.", reason="npm_unavailable")]
    if authority.lock is None:
        return None, [_unverified("The verified owner authority lock is unavailable.", reason="authority_lock_unavailable")]

    response: dict[str, Any] | None = None
    diagnostics: list[Diagnostic] = []
    env = _clean_node_environment()
    try:
        with TemporaryDirectory(prefix="ev4-pcvp-owner-") as directory:
            execution_root = Path(directory).resolve()
            diagnostics.extend(_materialize_tracked_tree(authority, execution_root))
            if not diagnostics:
                diagnostics.extend(_verify_materialized_files(execution_root, authority.lock))
            if not diagnostics:
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
                    diagnostics.append(_execution_unavailable(
                        "The locked owner dependencies could not be installed.",
                        reason="npm_ci_failed",
                        returncode=install.returncode,
                    ))
            if not diagnostics:
                diagnostics.extend(_verify_materialized_files(execution_root, authority.lock))
            if not diagnostics:
                response, bridge_diags = _execute_bridge(
                    node,
                    execution_root,
                    execution_root / VALIDATOR_PATH,
                    execution_root / BUNDLE_ROOT,
                    carrier_document,
                    env,
                )
                diagnostics.extend(bridge_diags)
    except (OSError, subprocess.SubprocessError, tarfile.TarError, ValueError) as exc:
        diagnostics.append(_execution_unavailable(
            "The clean owner execution environment could not be constructed.",
            reason="temporary_execution_environment_unavailable",
            error_type=type(exc).__name__,
        ))

    unchanged = _checkout_unchanged_diagnostics(authority)
    if unchanged:
        return None, sort_diagnostics(_deduplicate([*diagnostics, *unchanged]))
    if diagnostics:
        return None, sort_diagnostics(_deduplicate(diagnostics))
    return response, []


def _execute_bridge(
    node: str,
    execution_root: Path,
    validator_path: Path,
    bundle_root: Path,
    carrier_document: dict[str, Any],
    env: dict[str, str],
) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    request = {
        "schema_version": "ev4-pcvp-owner-bridge-request.v1",
        "validator_path": str(validator_path),
        "bundle_root": str(bundle_root),
        "carrier_document": carrier_document,
    }
    try:
        completed = subprocess.run(
            [node, "--input-type=module", "--eval", _NODE_BRIDGE],
            input=json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
            capture_output=True,
            text=True,
            cwd=execution_root,
            env=env,
            timeout=90,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return None, [_execution_unavailable("The owner validator could not be executed.", reason="subprocess_unavailable", error_type=type(exc).__name__)]
    if completed.returncode != 0:
        return None, [_execution_unavailable("The owner validator process failed.", reason="subprocess_failed", returncode=completed.returncode)]
    if completed.stderr.strip():
        return None, [_response_invalid("The bridge emitted stderr output.", reason="stderr_output")]
    response, error = _parse_response(completed.stdout)
    if error is not None:
        return None, [error]
    assert response is not None
    if response.get("schema_version") != "ev4-pcvp-owner-bridge-response.v1":
        return None, [_response_invalid("The bridge response schema is invalid.", reason="response_schema_invalid")]
    status = response.get("status")
    expected = {"schema_version", "status", "bundle", "carrier"} if status == "OK" else {"schema_version", "status", "error"}
    if set(response) != expected:
        return None, [_response_invalid("The bridge response shape is not exact.", reason="response_shape_invalid")]
    if status != "OK":
        return None, [_execution_unavailable("The owner module or locked dependencies were unavailable.", reason="owner_bridge_error", owner_error=copy.deepcopy(response.get("error")))]
    if not isinstance(response.get("bundle"), dict):
        return None, [_response_invalid("The owner bundle response is malformed.", reason="bundle_result_invalid")]
    return response, []


def load_profile(authority: OwnerAuthority) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    try:
        payload = yaml.safe_load(authority.profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return None, [diagnostic("PG_PCVP_PROFILE_UNAVAILABLE", "insufficient_evidence", "The locked source Profile could not be loaded.", "$.continuation_assurance", error_type=type(exc).__name__)]
    profile = payload.get("continuation_profile") if isinstance(payload, dict) else None
    if not isinstance(profile, dict):
        return None, [diagnostic("PG_PCVP_PROFILE_INVALID", "error", "The locked source Profile structure is invalid.", "$.continuation_assurance")]
    return profile, []


def profile_integration_diagnostics(
    profile: dict[str, Any],
    binding: dict[str, str],
    document: dict[str, Any],
    *,
    source_stage: str | None,
    downstream_stage: str | None,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    identity = {
        "profile_id": binding["profile_id"],
        "profile_version": POLICY_VERSION,
        "profile_status": "release_candidate",
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "repository": binding["repository"],
        "stage_id": source_stage,
    }
    for key, expected in identity.items():
        if profile.get(key) != expected:
            diagnostics.append(diagnostic("PG_PCVP_PROFILE_IDENTITY_MISMATCH", "error", "The source Profile identity does not match the integration binding.", f"$.continuation_assurance.profile.{key}", expected=expected, actual=profile.get(key), validator_layer="PROFILE_INTEGRATION"))
    produces_for = profile.get("produces_for")
    if not isinstance(produces_for, list) or downstream_stage not in produces_for:
        diagnostics.append(diagnostic("PG_PCVP_PROFILE_DOWNSTREAM_NOT_ALLOWED", "error", "The source Profile does not produce for the resolved downstream Stage.", "$.continuation_assurance.profile.produces_for", expected=downstream_stage, actual=produces_for, validator_layer="PROFILE_INTEGRATION"))
    raw_preauth = profile.get("preauthorized_effects")
    preauth = [item for item in raw_preauth if isinstance(item, dict)] if isinstance(raw_preauth, list) else []
    safe_classes = {item for item in profile.get("safe_reversible_default_effect_classes", []) if isinstance(item, str)}
    safe_enabled = profile.get("safe_reversible_default_enabled") is True
    carrier = document.get("continuation_assurance")
    if not isinstance(carrier, dict):
        return diagnostics
    effects = carrier.get("effects") if isinstance(carrier.get("effects"), list) else []
    auths = carrier.get("authorizations") if isinstance(carrier.get("authorizations"), list) else []
    by_auth: dict[str, list[dict[str, Any]]] = {}
    for effect in effects:
        if isinstance(effect, dict) and isinstance(effect.get("authorization_ref"), str):
            by_auth.setdefault(effect["authorization_ref"], []).append(effect)
    for index, auth in enumerate(auths):
        if not isinstance(auth, dict):
            continue
        path = f"$.continuation_assurance.authorizations[{index}]"
        scope = auth.get("stage_scope")
        if not isinstance(scope, dict):
            diagnostics.append(diagnostic("PG_PCVP_STAGE_SCOPE_MISMATCH", "error", "Authorization stage_scope is unavailable.", f"{path}.stage_scope", validator_layer="PROFILE_INTEGRATION"))
        else:
            if scope.get("from") != source_stage:
                diagnostics.append(diagnostic("PG_PCVP_STAGE_SCOPE_FROM_MISMATCH", "error", "stage_scope.from must equal source_stage.", f"{path}.stage_scope.from", expected=source_stage, actual=scope.get("from"), validator_layer="PROFILE_INTEGRATION"))
            if scope.get("through") != downstream_stage:
                diagnostics.append(diagnostic("PG_PCVP_STAGE_SCOPE_THROUGH_MISMATCH", "error", "stage_scope.through must equal the resolved downstream Stage.", f"{path}.stage_scope.through", expected=downstream_stage, actual=scope.get("through"), validator_layer="PROFILE_INTEGRATION"))
        auth_id = auth.get("authorization_id")
        linked = by_auth.get(auth_id, []) if isinstance(auth_id, str) else []
        for effect in linked:
            effect_class = effect.get("effect_class")
            if auth.get("basis") == "PROFILE_PREAUTHORIZED":
                class_candidates = [
                    item for item in preauth
                    if item.get("effect_class") == effect_class
                ]
                if not class_candidates:
                    diagnostics.append(diagnostic(
                        "PG_PCVP_PROFILE_PREAUTHORIZATION_REJECTED",
                        "error",
                        "The source Profile does not explicitly preauthorize this Effect class.",
                        path,
                        authorization_id=auth_id,
                        effect_id=effect.get("effect_id"),
                        effect_class=effect_class,
                        validator_layer="PROFILE_INTEGRATION",
                    ))
                effect_scope = effect.get("permitted_scope")
                authorization_scope = auth.get("permitted_scope")
                exact_candidates = [
                    item for item in class_candidates
                    if isinstance(item.get("scope"), str)
                    and item.get("scope") == effect_scope
                    and item.get("scope") == authorization_scope
                ]
                if not exact_candidates:
                    diagnostics.append(diagnostic(
                        "PG_PCVP_PROFILE_SCOPE_NOT_AUTHORIZED",
                        "error",
                        "The Effect and Authorization scope must exactly match one active Profile preauthorization entry.",
                        path,
                        authorization_id=auth_id,
                        effect_id=effect.get("effect_id"),
                        effect_class=effect_class,
                        effect_scope=effect_scope,
                        authorization_scope=authorization_scope,
                        profile_scopes=[item.get("scope") for item in class_candidates],
                        validator_layer="PROFILE_INTEGRATION",
                    ))
                elif len(exact_candidates) > 1:
                    diagnostics.append(diagnostic(
                        "PG_PCVP_PROFILE_PREAUTHORIZATION_AMBIGUOUS",
                        "error",
                        "More than one exact Profile preauthorization entry matches this Effect.",
                        path,
                        authorization_id=auth_id,
                        effect_id=effect.get("effect_id"),
                        effect_class=effect_class,
                        scope=effect_scope,
                        exact_match_count=len(exact_candidates),
                        validator_layer="PROFILE_INTEGRATION",
                    ))
            if auth.get("basis") == "SAFE_REVERSIBLE_DEFAULT" and (not safe_enabled or effect_class not in safe_classes):
                diagnostics.append(diagnostic("PG_PCVP_PROFILE_SAFE_DEFAULT_REJECTED", "error", "The source Profile does not explicitly allow this safe-default Effect class.", path, authorization_id=auth_id, effect_id=effect.get("effect_id"), effect_class=effect_class, validator_layer="PROFILE_INTEGRATION"))
    return diagnostics


def _load_lock(repository_root: Path) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    try:
        lock = load_json_file(repository_root / LOCK_PATH)
    except (OSError, ValueError, TypeError) as exc:
        return None, [_unverified("The PCVP execution lock could not be loaded.", reason="lock_unavailable", error_type=type(exc).__name__)]
    if not isinstance(lock, dict):
        return None, [_unverified("The PCVP execution lock must be an object.", reason="lock_shape_invalid")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION or lock.get("architecture_lock_id") != ARCHITECTURE_LOCK_ID:
        return None, [_unverified("The PCVP execution lock identity drifted.", reason="lock_identity_mismatch")]
    if lock.get("policy") != {"id": POLICY_ID, "version": POLICY_VERSION, "adoption_status": "not_yet_adopted", "activation": "NONE"}:
        return None, [_unverified("The dormant policy lock drifted.", reason="policy_lock_mismatch")]
    if lock.get("owner") != {"repository": CANONICAL_REPOSITORY, "commit_sha": CANONICAL_COMMIT, "bundle_root": BUNDLE_ROOT, "validator_path": VALIDATOR_PATH}:
        return None, [_unverified("The owner execution identity lock drifted.", reason="owner_lock_mismatch")]
    records = lock.get("authority_files")
    paths = [item.get("path") for item in records if isinstance(item, dict)] if isinstance(records, list) else []
    if not isinstance(records, list) or len(records) != len(expected_authority_paths()) or set(paths) != expected_authority_paths():
        return None, [_unverified("The execution-critical owner file set is incomplete.", reason="authority_file_set_invalid")]
    return lock, []


def _verify_files(root: Path, lock: dict[str, Any], git: str) -> list[Diagnostic]:
    diagnostics = _verify_materialized_files(root, lock)
    for record in sorted(lock["authority_files"], key=lambda item: item["path"]):
        relative = record["path"]
        try:
            content = (root / relative).read_bytes()
            tracked = _git(git, root, "rev-parse", f"HEAD:{relative}")
        except OSError as exc:
            diagnostics.append(_unverified("An execution-critical owner file is unavailable.", reason="owner_file_unavailable", owner_path=relative, error_type=type(exc).__name__))
        except subprocess.SubprocessError:
            diagnostics.append(_unverified("An owner file is not tracked at the locked commit.", reason="owner_file_not_tracked", owner_path=relative))
        else:
            if tracked != _blob_sha(content):
                diagnostics.append(_unverified("An owner worktree file differs from the locked commit.", reason="owner_worktree_drift", owner_path=relative))
    return diagnostics


def _verify_materialized_files(root: Path, lock: dict[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for record in sorted(lock["authority_files"], key=lambda item: item["path"]):
        relative = record["path"]
        try:
            content = (root / relative).read_bytes()
        except OSError as exc:
            diagnostics.append(_unverified("An execution-critical owner file is unavailable.", reason="owner_file_unavailable", owner_path=relative, error_type=type(exc).__name__))
            continue
        blob = _blob_sha(content)
        expected_sha = record.get("sha256_file_bytes")
        expected_blob = record.get("git_blob_sha")
        if expected_sha is not None and hashlib.sha256(content).hexdigest() != expected_sha:
            diagnostics.append(_unverified("An owner file SHA-256 does not match the lock.", reason="owner_file_sha256_mismatch", owner_path=relative))
        if expected_blob is not None and blob != expected_blob:
            diagnostics.append(_unverified("An owner file Git Blob does not match the lock.", reason="owner_file_blob_mismatch", owner_path=relative))
        if expected_sha is None and expected_blob is None:
            diagnostics.append(_unverified("An owner file lock lacks byte identity.", reason="owner_file_identity_missing", owner_path=relative))
    return diagnostics


def _capture_file_digests(root: Path, lock: dict[str, Any]) -> tuple[dict[str, str], list[Diagnostic]]:
    values: dict[str, str] = {}
    diagnostics: list[Diagnostic] = []
    for record in sorted(lock["authority_files"], key=lambda item: item["path"]):
        relative = record["path"]
        try:
            values[relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        except OSError as exc:
            diagnostics.append(_unverified("An execution-critical owner file could not be snapshotted.", reason="owner_file_snapshot_unavailable", owner_path=relative, error_type=type(exc).__name__))
    return values, diagnostics


def _materialize_tracked_tree(authority: OwnerAuthority, execution_root: Path) -> list[Diagnostic]:
    try:
        archived = subprocess.run(
            [authority.git, "-C", str(authority.root), "archive", "--format=tar", CANONICAL_COMMIT],
            capture_output=True,
            timeout=60,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return [_execution_unavailable("The locked tracked tree could not be archived.", reason="git_archive_unavailable", error_type=type(exc).__name__)]
    if archived.returncode != 0:
        return [_execution_unavailable("The locked tracked tree could not be archived.", reason="git_archive_failed", returncode=archived.returncode)]
    try:
        _extract_regular_archive(archived.stdout, execution_root)
    except (OSError, tarfile.TarError, ValueError) as exc:
        return [_execution_unavailable("The locked tracked tree could not be extracted.", reason="git_archive_extraction_failed", error_type=type(exc).__name__)]
    return []


def _extract_regular_archive(payload: bytes, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError("archive path escapes destination") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError("archive contains a non-regular entry")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("archive member bytes unavailable")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
            target.chmod(member.mode & 0o777)


def _checkout_unchanged_diagnostics(authority: OwnerAuthority) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    try:
        head = _git(authority.git, authority.root, "rev-parse", "HEAD")
        status = _git(authority.git, authority.root, "status", "--porcelain=v1", "--untracked-files=no")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return [_unverified("The supplied owner checkout could not be reverified after execution.", reason="post_execution_identity_unavailable", error_type=type(exc).__name__)]
    if head != authority.initial_head:
        diagnostics.append(_unverified("The supplied owner checkout HEAD changed during execution.", reason="post_execution_head_changed", expected=authority.initial_head, actual=head))
    if status != authority.initial_tracked_status:
        diagnostics.append(_unverified("The supplied owner checkout tracked status changed during execution.", reason="post_execution_tracked_status_changed", expected=authority.initial_tracked_status, actual=status))
    if authority.lock is None or authority.initial_file_digests is None:
        diagnostics.append(_unverified("The supplied owner checkout baseline is incomplete.", reason="post_execution_baseline_unavailable"))
        return diagnostics
    current, current_diags = _capture_file_digests(authority.root, authority.lock)
    diagnostics.extend(current_diags)
    if current != authority.initial_file_digests:
        diagnostics.append(_unverified("Execution-critical bytes in the supplied owner checkout changed during execution.", reason="post_execution_owner_bytes_changed"))
    return diagnostics


def _clean_node_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("NODE_OPTIONS", None)
    env.pop("NODE_PATH", None)
    return env


def _parse_response(stdout: str) -> tuple[dict[str, Any] | None, Diagnostic | None]:
    try:
        value, end = json.JSONDecoder().raw_decode(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        return None, _response_invalid("The bridge did not emit one strict JSON response.", reason="malformed_json", error_type=type(exc).__name__)
    if stdout[end:].strip():
        return None, _response_invalid("The bridge emitted extra output.", reason="extra_output")
    if not isinstance(value, dict):
        return None, _response_invalid("The bridge response must be an object.", reason="response_not_object")
    return value, None


def _git(git: str, root: Path, *args: str) -> str:
    return subprocess.run([git, "-C", str(root), *args], capture_output=True, text=True, timeout=20, shell=False, check=True).stdout.strip()


def _remote_matches(remote: str) -> bool:
    value = remote.strip().removesuffix(".git")
    return value in {
        f"https://github.com/{CANONICAL_REPOSITORY}",
        f"http://github.com/{CANONICAL_REPOSITORY}",
        f"git@github.com:{CANONICAL_REPOSITORY}",
        f"ssh://git@github.com/{CANONICAL_REPOSITORY}",
    }


def _blob_sha(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content, usedforsecurity=False).hexdigest()


def _unverified(message: str, **details: Any) -> Diagnostic:
    return diagnostic("PG_PCVP_OWNER_AUTHORITY_UNVERIFIED", "insufficient_evidence", message, "$.continuation_assurance", **details)


def _execution_unavailable(message: str, **details: Any) -> Diagnostic:
    return diagnostic("PG_PCVP_OWNER_EXECUTION_UNAVAILABLE", "insufficient_evidence", message, "$.continuation_assurance", **details)


def _response_invalid(message: str, **details: Any) -> Diagnostic:
    return diagnostic("PG_PCVP_OWNER_RESPONSE_INVALID", "insufficient_evidence", message, "$.continuation_assurance", **details)


def _deduplicate(items: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Diagnostic] = []
    for item in items:
        key = (item.code, item.path, item.message)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
