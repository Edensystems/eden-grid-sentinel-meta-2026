"""M4 Guardian and local workflow; no cloud, Meta, or electrical operations."""
from datetime import datetime, timedelta, timezone
import copy

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from eden.sentinel.api import app
from eden.sentinel.m3_demo import previous_day_fixture, target_fixture
from eden.sentinel.m3_scheduler import SchedulingPolicy, schedule_flexible_load
from eden.sentinel.m4_guardian import guard_schedule
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, WorkflowError
from eden.sentinel.m4_perception import build_sam_request, MAX_IMAGE_BYTES
from eden.sentinel.twin import PowerInterval, SimulationRequest

NOW = datetime(2026, 10, 31, 10, 0, tzinfo=timezone.utc)


def clock_holder():
    holder = [NOW]
    return holder, LocalApprovalWorkflow(clock=lambda: holder[0])


def make_forecast_plan():
    target = target_fixture("critical_priority_school")
    historic = previous_day_fixture("critical_priority_school")
    forecast = [PowerInterval.model_validate({**observed.model_dump(),
        "solar_generation_kw": earlier.solar_generation_kw})
        for observed, earlier in zip(target.intervals, historic.intervals)]
    original = SimulationRequest(grid=target.grid, intervals=forecast)
    policy = SchedulingPolicy()
    return schedule_flexible_load(original, policy), original, policy


def test_guardian_valid_forecast_plan():
    plan, original, policy = make_forecast_plan()
    verdict = guard_schedule(plan, original, policy)
    assert verdict.allowed
    assert verdict.mode == "simulation"
    assert verdict.predicted_reserve_violations == 0


def test_guardian_rejects_fabricated_metrics():
    plan, original, policy = make_forecast_plan()
    plan.scheduled.summary.unserved_essential_kwh += 1
    verdict = guard_schedule(plan, original, policy)
    assert not verdict.allowed
    assert "proposal does not match deterministic scheduler output" in verdict.reasons


def test_guardian_rejects_changed_flexible_plan():
    plan, original, policy = make_forecast_plan()
    plan.scheduled_request.intervals[0].flexible_demand_kw += 0.5
    assert not guard_schedule(plan, original, policy).allowed


def test_guardian_rejects_tampered_original():
    plan, original, policy = make_forecast_plan()
    original.intervals[0].solar_generation_kw += 3
    assert not guard_schedule(plan, original, policy).allowed


def test_guardian_rejects_tampered_policy():
    plan, original, policy = make_forecast_plan()
    policy.max_moves = 0
    assert not guard_schedule(plan, original, policy).allowed


def test_guardian_does_not_depend_on_future_measured_solar():
    plan, original, policy = make_forecast_plan()
    assert original.intervals[0].solar_generation_kw == 3.8
    assert target_fixture("critical_priority_school").intervals[0].solar_generation_kw == 4
    assert guard_schedule(plan, original, policy).allowed


def test_create_is_pending_and_does_not_expose_realized_outcome():
    _, service = clock_holder()
    view = service.create("critical_priority_school")
    assert view.status == "pending"
    assert view.guardian.allowed
    assert view.realized_essential_unserved_kwh is None
    assert view.realized_essential_reduction_kwh is None
    assert len(view.audit) == 1


def test_cannot_execute_pending_proposal():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    with pytest.raises(WorkflowError, match="execution_requires_approval"):
        service.apply_simulation(proposed.proposal_id, operator="person")


def test_operator_identity_required():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    with pytest.raises(WorkflowError, match="operator_identity_required"):
        service.decide(proposed.proposal_id, operator="   ", decision="approved")


def test_rejection_cannot_be_executed_or_reapproved():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    rejected = service.decide(proposed.proposal_id, operator="person", decision="rejected")
    assert rejected.status == "rejected"
    with pytest.raises(WorkflowError):
        service.apply_simulation(proposed.proposal_id, operator="person")
    with pytest.raises(WorkflowError):
        service.decide(proposed.proposal_id, operator="person", decision="approved")
    assert service.verify_audit(rejected.audit)


def test_expired_proposal_cannot_be_approved():
    holder, service = clock_holder()
    proposed = service.create("critical_priority_school")
    holder[0] += timedelta(minutes=16)
    with pytest.raises(WorkflowError):
        service.decide(proposed.proposal_id, operator="person", decision="approved")
    view = service.inspect(proposed.proposal_id)
    assert view.status == "expired"
    assert service.verify_audit(view.audit)


def test_approved_but_expired_cannot_execute():
    holder, service = clock_holder()
    proposed = service.create("critical_priority_school")
    service.decide(proposed.proposal_id, operator="person", decision="approved")
    holder[0] += timedelta(minutes=16)
    with pytest.raises(WorkflowError):
        service.apply_simulation(proposed.proposal_id, operator="person")


def test_cross_operator_application_denied():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    service.decide(proposed.proposal_id, operator="person-one", decision="approved")
    with pytest.raises(WorkflowError, match="approval_operator_mismatch"):
        service.apply_simulation(proposed.proposal_id, operator="person-two")


def test_approved_simulation_once_and_auditable():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    service.decide(proposed.proposal_id, operator="human", decision="approved")
    applied = service.apply_simulation(proposed.proposal_id, operator="human")
    assert applied.status == "applied"
    assert applied.realized_essential_reduction_kwh == pytest.approx(0.7175)
    assert [x.event for x in applied.audit] == ["proposed", "approved", "applied"]
    assert service.verify_audit(applied.audit)
    with pytest.raises(WorkflowError, match="execution_requires_approval"):
        service.apply_simulation(proposed.proposal_id, operator="human")


def test_audit_tampering_detected():
    _, service = clock_holder()
    proposed = service.create("night_reserve")
    updated = service.decide(proposed.proposal_id, operator="human", decision="rejected")
    changed = copy.deepcopy(updated.audit)
    changed[-1].note = "I changed this"
    assert not service.verify_audit(changed)


def test_snapshot_mutation_cannot_change_state():
    _, service = clock_holder()
    proposed = service.create("critical_priority_school")
    proposed.guardian.allowed = False
    proposed.audit[0].note = "changed"
    stored = service.inspect(proposed.proposal_id)
    assert stored.guardian.allowed
    assert stored.audit[0].note != "changed"


def test_unknown_scenario_and_proposal_rejected():
    _, service = clock_holder()
    with pytest.raises(WorkflowError, match="unknown_scenario"):
        service.create("bad-name")
    with pytest.raises(WorkflowError, match="proposal_not_found"):
        service.inspect("bad-id")


def test_no_op_scenario_never_claims_savings():
    _, service = clock_holder()
    proposed = service.create("sunny_surplus")
    assert proposed.forecast_shifted_kwh == 0
    service.decide(proposed.proposal_id, operator="human", decision="approved")
    applied = service.apply_simulation(proposed.proposal_id, operator="human")
    assert applied.realized_essential_reduction_kwh == pytest.approx(0)


def test_http_api_disabled_by_default(monkeypatch):
    monkeypatch.delenv("M4_ENABLE_LOCAL_API", raising=False)
    assert TestClient(app).post("/m4/proposals", json={"scenario":"critical_priority_school"}).status_code == 503


def test_http_api_denies_missing_or_wrong_token(monkeypatch):
    monkeypatch.setenv("M4_ENABLE_LOCAL_API", "1")
    monkeypatch.setenv("M4_OPERATOR_TOKEN", "not-a-real-credential-test-only-xxxxxxxx")
    monkeypatch.setenv("M4_OPERATOR_ID", "test-person")
    client = TestClient(app)
    assert client.post("/m4/proposals", json={"scenario":"sunny_surplus"}).status_code == 401
    assert client.post("/m4/proposals", json={"scenario":"sunny_surplus"},
                       headers={"Authorization":"Bearer wrong"}).status_code == 401


def test_http_operator_enforced_and_no_double_apply(monkeypatch):
    monkeypatch.setenv("M4_ENABLE_LOCAL_API", "1")
    monkeypatch.setenv("M4_OPERATOR_TOKEN", "not-a-real-credential-test-only-xxxxxxxx")
    monkeypatch.setenv("M4_OPERATOR_ID", "test-person")
    c = TestClient(app)
    headers = {"Authorization":"Bearer not-a-real-credential-test-only-xxxxxxxx"}
    create = c.post("/m4/proposals", json={"scenario":"critical_priority_school"},headers=headers)
    assert create.status_code == 200, create.text
    pid = create.json()["proposal_id"]
    assert c.post(f"/m4/proposals/{pid}/execute-simulation",headers=headers).status_code == 409
    approve = c.post(f"/m4/proposals/{pid}/decision", json={"decision":"approved"},headers=headers)
    assert approve.status_code == 200, approve.text
    assert approve.json()["approved_by"] == "test-person"
    apply = c.post(f"/m4/proposals/{pid}/execute-simulation",headers=headers)
    assert apply.status_code == 200, apply.text
    assert apply.json()["status"] == "applied"
    assert c.post(f"/m4/proposals/{pid}/execute-simulation",headers=headers).status_code == 409


def test_http_no_network_exposure(monkeypatch):
    monkeypatch.setenv("M4_ENABLE_LOCAL_API", "1")
    monkeypatch.setenv("M4_OPERATOR_TOKEN", "not-a-real-credential-test-only-xxxxxxxx")
    monkeypatch.setenv("M4_OPERATOR_ID", "test-person")
    from starlette.requests import Request
    scope = {"type":"http", "method":"GET", "path":"/m4/proposals/foo",
             "headers": [], "client": ("8.8.8.8", 3456), "server": ("127.0.0.1",8000),
             "scheme":"http", "http_version":"1.1"}
    from eden.sentinel.m4_routes import local_operator
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as err:
        local_operator(Request(scope), "Bearer not-a-real-credential-test-only-xxxxxxxx")
    assert err.value.status_code == 403


def test_sam_build_request_png_without_network_calls():
    fake_png = b"\x89PNG\r\n\x1a\n" + b"a" * 16
    req, meta = build_sam_request(fake_png, "solar panel")
    assert req["model"] == "sam-3.1"
    assert req["stream"] is True
    assert req["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,")
    assert meta.network_call_made is False
    assert meta.purpose == "equipment_inventory_only"


@pytest.mark.parametrize("img", [b"", b"abc", b"a" * (MAX_IMAGE_BYTES+1)])
def test_sam_rejects_invalid_image(img):
    with pytest.raises(ValueError):
        build_sam_request(img, "solar panel")


def test_sam_rejects_unapproved_concept():
    with pytest.raises(ValueError):
        build_sam_request(b"\xff\xd8\xffxxxx", "short circuit")


def test_cannot_replace_hardware_mode_in_proposal():
    _, system = clock_holder()
    item=system.create("night_reserve")
    with pytest.raises(ValidationError):
        item.mode = "hardware"


def test_approved_plan_tampering_fails_at_application():
    _, system = clock_holder()
    item = system.create("critical_priority_school")
    system.decide(item.proposal_id, operator="human", decision="approved")
    # Test a corrupted in-process record before the final guard pass.
    system.records[item.proposal_id].plan.scheduled_request.intervals[0].flexible_demand_kw += 0.1
    with pytest.raises(WorkflowError, match="guardian_rejected_plan"):
        system.apply_simulation(item.proposal_id, operator="human")
    assert system.inspect(item.proposal_id).status == "approved"


def test_invalid_decision_does_not_transition():
    _, system = clock_holder()
    item = system.create("critical_priority_school")
    with pytest.raises(WorkflowError, match="invalid_decision"):
        system.decide(item.proposal_id, operator="human", decision="not-an-approval")
    assert system.inspect(item.proposal_id).status == "pending"


def test_http_auth_does_not_trust_client_claimed_operator(monkeypatch):
    monkeypatch.setenv("M4_ENABLE_LOCAL_API", "1")
    monkeypatch.setenv("M4_OPERATOR_TOKEN", "not-a-real-credential-test-only-xxxxxxxx")
    monkeypatch.setenv("M4_OPERATOR_ID", "server-side-actor")
    client = TestClient(app)
    headers = {"Authorization": "Bearer not-a-real-credential-test-only-xxxxxxxx"}
    create = client.post("/m4/proposals", json={"scenario": "sunny_surplus"}, headers=headers)
    assert create.status_code == 200
    pid = create.json()["proposal_id"]
    decision = client.post(f"/m4/proposals/{pid}/decision", headers=headers,
                           json={"decision": "approved", "operator_id": "attacker"})
    assert decision.status_code == 422
    assert client.get(f"/m4/proposals/{pid}", headers=headers).json()["status"] == "pending"
