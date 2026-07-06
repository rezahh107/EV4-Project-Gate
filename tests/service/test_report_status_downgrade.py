from __future__ import annotations

import json

import ev4_transition.service.reports as service_reports
from ev4_transition.service import GateRequest, run_gate_request
from ev4_transition.service import dispatcher


def test_report_render_failure_downgrades_accepted_service_response(monkeypatch):
    engine_result = {"status": "accepted", "diagnostics": [], "output": {"ok": True}}

    class FakeBundleValidator:
        def __init__(self, schema_root):
            self.schema_root = schema_root

        def validate_bundle(self, payload, required_evidence_ids=None):
            return engine_result

    def explode(_result):
        raise RuntimeError("renderer failed")

    monkeypatch.setattr(dispatcher, "BundleValidator", FakeBundleValidator)
    monkeypatch.setattr(service_reports, "render_json_result", explode)

    response = run_gate_request(
        GateRequest(
            transition_choice="validate_bundle",
            input_data={"schema_version": "stage-evidence-bundle.v1"},
        )
    )

    assert response.status == "invalid"
    assert any(item["code"] == "PG.SERVICE.REPORT_JSON_RENDER_FAILED" for item in response.service_diagnostics)
    assert not response.user_message_fa.startswith("✅")
    assert response.engine_result == engine_result
    assert response.report_bundle is not None
    assert json.loads(response.report_bundle.canonical_json)["status"] == "invalid"
