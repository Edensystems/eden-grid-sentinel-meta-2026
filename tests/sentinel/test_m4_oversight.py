"""M4 oversight regressions: informed approval, denied-attempt audit,
plan/input/policy binding and truncation detection."""
import threading

import pytest

from eden.sentinel.m3_scheduler import schedule_flexible_load
from eden.sentinel.m4_guardian import guard_schedule
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, WorkflowError

SCENARIO = "critical_priority_school"


def test_operator_sees_exact_planned_intervals_and_tradeoff():
    service = LocalApprovalWorkflow()
    view = service.create(SCENARIO)
    rec = service.records[view.proposal_id]
    assert len(view.planned_intervals) == len(rec.plan.scheduled_request.intervals)
    for shown, planned, original in zip(view.planned_intervals,
                                        rec.plan.scheduled_request.intervals,
                                        rec.original.intervals):
        assert shown.planned_flexible_kw == planned.flexible_demand_kw
        assert shown.original_flexible_kw == original.flexible_demand_kw
        assert shown.forecast_solar_kw == original.solar_generation_kw
    moved = sum(abs(i.planned_flexible_kw - i.original_flexible_kw) * i.duration_minutes / 60
                for i in view.planned_intervals) / 2
    assert moved == pytest.approx(view.forecast_shifted_kwh)
    assert view.forecast_essential_unserved_planned_kwh < view.forecast_essential_unserved_baseline_kwh
    assert view.forecast_flexible_unserved_planned_kwh > view.forecast_flexible_unserved_baseline_kwh
    assert f"plan_sha256={view.plan_sha256}" in view.audit[0].note


def test_denied_attempts_are_hash_chained():
    service = LocalApprovalWorkflow()
    view = service.create(SCENARIO)
    with pytest.raises(WorkflowError):
        service.apply_simulation(view.proposal_id, operator="op-a")
    service.decide(view.proposal_id, operator="op-a", decision="approved")
    with pytest.raises(WorkflowError, match="approval_operator_mismatch"):
        service.apply_simulation(view.proposal_id, operator="op-b")
    events = service.inspect(view.proposal_id).audit
    assert [(e.event, e.actor, e.note) for e in events if e.event == "denied"] == [
        ("denied", "op-a", "execution_requires_approval"),
        ("denied", "op-b", "approval_operator_mismatch"),
    ]
    assert service.verify_audit(events)


def test_concurrent_losers_are_audited():
    service = LocalApprovalWorkflow()
    view = service.create(SCENARIO)
    service.decide(view.proposal_id, operator="op-a", decision="approved")
    outcomes = []

    def race():
        try:
            service.apply_simulation(view.proposal_id, operator="op-a")
            outcomes.append("applied")
        except WorkflowError as exc:
            outcomes.append(exc.code)

    threads = [threading.Thread(target=race) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    events = service.inspect(view.proposal_id).audit
    assert outcomes.count("applied") == 1
    assert sum(e.event == "applied" for e in events) == 1
    assert sum(e.event == "denied" for e in events) == 7
    assert service.verify_audit(events)


def test_coherent_tampering_of_plan_input_and_policy_is_blocked():
    """Guardian re-derives from stored input, so editing input+policy+plan together
    could pass it; the creation-time digest must still refuse execution."""
    service = LocalApprovalWorkflow()
    view = service.create(SCENARIO)
    service.decide(view.proposal_id, operator="op-a", decision="approved")
    rec = service.records[view.proposal_id]
    rec.policy = rec.policy.model_copy(update={"max_moves": 3})
    rec.plan = schedule_flexible_load(rec.original, rec.policy)
    assert guard_schedule(rec.plan, rec.original, rec.policy).allowed  # Guardian alone is fooled
    with pytest.raises(WorkflowError, match="plan_digest_mismatch"):
        service.apply_simulation(view.proposal_id, operator="op-a")
    assert service.inspect(view.proposal_id).audit[-1].note == "plan_digest_mismatch"


def test_truncation_detected_with_retained_head():
    service = LocalApprovalWorkflow()
    view = service.create(SCENARIO)
    service.decide(view.proposal_id, operator="op-a", decision="approved")
    applied = service.apply_simulation(view.proposal_id, operator="op-a")
    head = applied.audit_head_hash
    assert service.verify_audit(applied.audit, expected_head=head)
    truncated = applied.audit[:-1]
    assert service.verify_audit(truncated)  # chain alone cannot see a dropped tail
    assert not service.verify_audit(truncated, expected_head=head)
    assert not service.verify_audit([], expected_head=head)
