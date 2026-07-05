from copy import deepcopy

from ev4_transition.reports import canonical_result_hash_for_report, render_json_result, render_markdown_report


def test_report_rendering_does_not_mutate_result():
    result = {
        "status": "insufficient_evidence",
        "diagnostics": [{"code": "PG_TEST", "severity": "insufficient_evidence", "message": "missing", "path": "$"}],
        "progress_events": [{"message": "running"}],
    }
    before = deepcopy(result)
    render_markdown_report(result)
    render_json_result(result)
    assert result == before


def test_progress_events_not_in_canonical_result_hash():
    base = {"status": "accepted", "diagnostics": [], "hashes": {"canonical_payload_hash": "a" * 64}}
    with_progress = deepcopy(base)
    with_progress["progress_events"] = [{"step": "render", "state": "started"}]
    assert canonical_result_hash_for_report(base) == canonical_result_hash_for_report(with_progress)


def test_render_json_result_is_machine_readable_and_deterministic():
    rendered = render_json_result({"status": "accepted", "b": 2, "a": 1})
    assert rendered == '{"a":1,"b":2,"status":"accepted"}\n'
