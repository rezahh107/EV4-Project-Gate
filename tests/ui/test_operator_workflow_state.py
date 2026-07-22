from __future__ import annotations

import inspect
from pathlib import Path

import ev4_transition.ui.app as app
from ev4_transition.ui.state import (
    begin_workflow,
    block_workflow,
    complete_workflow,
    initial_workflow_state,
    invalidate_workflow,
    mark_running,
    operation_is_current,
    record_preview,
)


def test_primary_action_is_available_without_persistent_token() -> None:
    source = inspect.getsource(app.build_demo)
    assert 'بررسی و اجرای Authoritative Project Gate' in source
    assert 'interactive=True' in source
    assert 'preflight_token = gr.State' not in source
    assert 'run_event.then(' in source


def test_not_checked_to_checking_to_blocked() -> None:
    started = begin_workflow(initial_workflow_state())
    blocked = block_workflow(
        started,
        started.operation_id,
        started.operation_revision or 0,
        detail_fa="blocked",
    )
    assert started.status == "checking"
    assert blocked.status == "blocked"


def test_not_checked_to_checking_to_running_to_completed() -> None:
    started = begin_workflow(initial_workflow_state())
    revision = started.operation_revision or 0
    running = mark_running(started, started.operation_id, revision)
    completed = complete_workflow(running, running.operation_id, revision)
    assert running.status == "running"
    assert completed.status == "completed"


def test_effective_input_change_during_checking_becomes_stale() -> None:
    started = begin_workflow(initial_workflow_state())
    changed = invalidate_workflow(started, relevant=True)
    assert changed.status == "stale"
    assert operation_is_current(
        changed,
        started.operation_id,
        started.operation_revision or 0,
    ) is False


def test_irrelevant_input_does_not_invalidate_current_operation() -> None:
    started = begin_workflow(initial_workflow_state())
    unchanged = invalidate_workflow(started, relevant=False)
    assert unchanged == started
    assert operation_is_current(
        unchanged,
        started.operation_id,
        started.operation_revision or 0,
    ) is True


def test_older_operation_cannot_complete_newer_state() -> None:
    first = begin_workflow(initial_workflow_state())
    second = begin_workflow(invalidate_workflow(first, relevant=True))
    result = complete_workflow(
        second,
        first.operation_id,
        first.operation_revision or 0,
    )
    assert result.status == "stale"


def test_preflight_preview_never_becomes_persistent_ready_state() -> None:
    preview = record_preview(initial_workflow_state(), "ready")
    assert preview.status == "not_checked"
    assert preview.preview_revision == preview.input_revision
    assert "دکمه اصلی" in preview.detail_fa


def test_warning_preview_is_visible_and_non_authorizing() -> None:
    preview = record_preview(initial_workflow_state(), "warnings")
    assert preview.status == "blocked"


def test_controlled_failure_has_distinct_workflow_state() -> None:
    started = begin_workflow(initial_workflow_state())
    revision = started.operation_revision or 0
    failed = complete_workflow(started, started.operation_id, revision, failed=True)
    assert failed.status == "failed"
    assert "خطای کنترل‌شده" in failed.detail_fa


def test_operator_docs_match_unified_non_authorizing_preview() -> None:
    root = Path(__file__).resolve().parents[2]
    quick = (root / "docs/LOCAL_OPERATOR_PANEL_QUICK_START.fa.md").read_text(encoding="utf-8")
    guide = (root / "docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md").read_text(encoding="utf-8")
    combined = quick + "\n" + guide
    assert "بررسی و اجرای Authoritative Project Gate" in combined
    assert "preview هیچ fingerprint ماندگار" in quick
    assert "ممکن است اجرای اصلی همچنان ممکن باشد" not in combined
    assert "Preflight و اجرای اصلی دو عملیات جدا هستند" not in combined
