"""Operator-mode API used by the control-room Incident panel.

Offline: the live-advisory path is exercised with the fake transport from
test_e2e_incident; no Meta request is ever made.
"""
import pytest
from fastapi.testclient import TestClient

from eden.sentinel import muse
from eden.sentinel.api import app
from eden.sentinel.m4_routes import workflow
from test_e2e_incident import FakeClient, _finish, _initial

TOKEN = "not-a-real-credential-test-only-xxxxxxxx"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
SCENARIO = "critical_priority_school"


@pytest.fixture
def operator_env(monkeypatch):
    monkeypatch.setenv("M4_ENABLE_LOCAL_API", "1")
    monkeypatch.setenv("M4_OPERATOR_TOKEN", TOKEN)
    monkeypatch.setenv("M4_OPERATOR_ID", "panel-operator")
    monkeypatch.delenv("M4_ALLOW_LIVE_ADVISORY", raising=False)
    return TestClient(app)


def _no_client():
    pytest.fail("model client must not be built")


def test_status_requires_operator_token(operator_env):
    assert operator_env.get("/m4/status").status_code == 401
    ok = operator_env.get("/m4/status", headers=AUTH)
    assert ok.status_code == 200
    assert ok.json() == {"mode": "simulation", "operator_id": "panel-operator",
                         "live_advisory_enabled": False}


def test_status_disabled_without_local_api(monkeypatch):
    monkeypatch.delenv("M4_ENABLE_LOCAL_API", raising=False)
    assert TestClient(app).get("/m4/status", headers=AUTH).status_code == 503


def test_live_advisory_refused_unless_explicitly_enabled(operator_env, monkeypatch):
    monkeypatch.setattr(muse, "build_meta_client", _no_client)
    before = len(workflow.records)
    r = operator_env.post("/m4/proposals", headers=AUTH,
                          json={"scenario": SCENARIO, "live_advisory": True})
    assert r.status_code == 403 and r.json()["detail"] == "live_advisory_disabled"
    assert len(workflow.records) == before


def test_live_advisory_attached_as_advisory_only(operator_env, monkeypatch):
    monkeypatch.setenv("M4_ALLOW_LIVE_ADVISORY", "1")
    fake = FakeClient([_initial(), _finish()])
    monkeypatch.setattr(muse, "build_meta_client", lambda: fake)
    assert operator_env.get("/m4/status", headers=AUTH).json()["live_advisory_enabled"] is True
    r = operator_env.post("/m4/proposals", headers=AUTH,
                          json={"scenario": SCENARIO, "live_advisory": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(fake.calls) == 2
    assert body["status"] == "pending" and body["approved_by"] is None
    assert body["advisory_model"] == muse.DEFAULT_MODEL
    assert body["advisory_risk_level"] == "high"
    assert body["advisory_headline"] and body["advisory_explanation"] and body["advisory_next_step"]
    # The advisory cannot execute: the plan still needs a human decision.
    pid = body["proposal_id"]
    denied = operator_env.post(f"/m4/proposals/{pid}/execute-simulation", headers=AUTH)
    assert denied.status_code == 409 and denied.json()["detail"] == "execution_requires_approval"


def test_model_failure_fails_closed_without_proposal(operator_env, monkeypatch):
    monkeypatch.setenv("M4_ALLOW_LIVE_ADVISORY", "1")
    monkeypatch.setattr(muse, "build_meta_client",
                        lambda: FakeClient([_initial(name="energize_relay"), _finish()]))
    before = len(workflow.records)
    r = operator_env.post("/m4/proposals", headers=AUTH,
                          json={"scenario": SCENARIO, "live_advisory": True})
    assert r.status_code == 502 and r.json()["detail"] == "advisory_unavailable"
    assert len(workflow.records) == before


def test_missing_key_reports_not_configured(operator_env, monkeypatch):
    monkeypatch.setenv("M4_ALLOW_LIVE_ADVISORY", "1")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    r = operator_env.post("/m4/proposals", headers=AUTH,
                          json={"scenario": SCENARIO, "live_advisory": True})
    assert r.status_code == 503 and r.json()["detail"] == "advisory_not_configured"


def test_live_advisory_requires_default_policy(operator_env, monkeypatch):
    monkeypatch.setenv("M4_ALLOW_LIVE_ADVISORY", "1")
    monkeypatch.setattr(muse, "build_meta_client", _no_client)
    r = operator_env.post("/m4/proposals", headers=AUTH, json={
        "scenario": SCENARIO, "live_advisory": True, "policy": {"max_moves": 3}})
    assert r.status_code == 422 and r.json()["detail"] == "advisory_requires_default_policy"


def test_unknown_scenario_with_advisory_never_calls_model(operator_env, monkeypatch):
    monkeypatch.setenv("M4_ALLOW_LIVE_ADVISORY", "1")
    monkeypatch.setattr(muse, "build_meta_client", _no_client)
    r = operator_env.post("/m4/proposals", headers=AUTH,
                          json={"scenario": "power_plant", "live_advisory": True})
    assert r.status_code == 404


def test_default_proposal_has_no_advisory(operator_env):
    r = operator_env.post("/m4/proposals", headers=AUTH, json={"scenario": SCENARIO})
    assert r.status_code == 200
    body = r.json()
    assert body["advisory_model"] is None and body["advisory_explanation"] is None


# --- Frontend contract fixture (apps/control-room/tests/fixtures/m4_proposals.json) ---
import json
from datetime import datetime, timezone
from pathlib import Path

from eden.sentinel.m4_workflow import LocalApprovalWorkflow, WorkflowError
from eden.sentinel.muse import assess_m3_scenario

PANEL_FIXTURE = (Path(__file__).resolve().parents[2] / "apps" / "control-room"
                 / "tests" / "fixtures" / "m4_proposals.json")
# Random per run (uuid4), or derived from it: excluded from the honesty comparison.
VOLATILE = {"proposal_id", "hash", "previous_hash", "audit_head_hash"}


def build_panel_fixture() -> dict:
    """Real ProposalView payloads for each panel state (fake model transport)."""
    advisory = assess_m3_scenario(FakeClient([_initial(), _finish()]), SCENARIO)
    wf = LocalApprovalWorkflow(clock=lambda: datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc))
    pending = wf.create(SCENARIO, advisory=advisory)
    rejected = wf.create(SCENARIO)
    wf.decide(rejected.proposal_id, operator="panel-operator", decision="rejected")
    applied = wf.create(SCENARIO)
    wf.decide(applied.proposal_id, operator="panel-operator", decision="approved")
    wf.apply_simulation(applied.proposal_id, operator="panel-operator")
    for pid in (rejected.proposal_id, applied.proposal_id):
        with pytest.raises(WorkflowError):
            wf.apply_simulation(pid, operator="panel-operator")
    return {name: wf.inspect(view.proposal_id).model_dump(mode="json")
            for name, view in (("pending_with_advisory", pending), ("rejected_then_denied", rejected),
                               ("applied_then_denied", applied))}


def _strip(value):
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


def test_panel_fixture_matches_real_workflow():
    """The control-room incident contract tests treat this fixture as real M4 output."""
    recorded = json.loads(PANEL_FIXTURE.read_text(encoding="utf-8"))
    assert _strip(recorded) == _strip(build_panel_fixture())


if __name__ == "__main__":
    PANEL_FIXTURE.write_text(json.dumps(build_panel_fixture(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote", PANEL_FIXTURE)
