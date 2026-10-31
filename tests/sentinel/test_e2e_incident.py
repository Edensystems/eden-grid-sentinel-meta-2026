"""M4.5 end-to-end incident: M3 forecast -> Muse advisory -> Guardian ->
human reject -> fresh approval -> simulated execution -> audited comparison.

Fully offline: fake Muse client, synthetic fixtures, in-memory twin only.
"""
import json
from types import SimpleNamespace as NS

import pytest

from eden.sentinel.m3_demo import evaluate_fixture, target_fixture, previous_day_fixture
from eden.sentinel.m3_scheduler import SchedulingPolicy, schedule_flexible_load
from eden.sentinel.m4_guardian import guard_schedule
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, WorkflowError
from eden.sentinel.muse import ModelProtocolError, assess_m3_scenario
from eden.sentinel.twin import PowerInterval, SimulationRequest, run_simulation

SCENARIO = "critical_priority_school"


def _initial(name="get_m3_evaluation", scenario=SCENARIO):
    args = json.dumps({"scenario_name": scenario})
    call = NS(id="call_1", function=NS(name=name, arguments=args))
    return NS(choices=[NS(finish_reason="tool_calls",
                          message=NS(tool_calls=[call], content=None))])


def _finish(scenario=SCENARIO):
    payload = {
        "scenario_name": scenario, "data_mode": "simulation",
        "risk_level": "high",
        "headline": "Synthetic solar shortfall threatens essential load",
        "explanation": "Forecast scheduling reduces essential shortfall at a flexible-load cost.",
        "suggested_next_step": "Guardian-check the plan and seek explicit operator approval.",
        "requires_human_approval": True,
    }
    return NS(choices=[NS(finish_reason="stop",
                          message=NS(tool_calls=None, content=json.dumps(payload)))])


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer


def test_m3_tool_is_strictly_allowlisted():
    client = FakeClient([_initial(name="energize_relay"), _finish()])
    with pytest.raises(ModelProtocolError):
        assess_m3_scenario(client, SCENARIO)
    assert len(client.calls) == 1  # no second request after a rejected tool


def test_m3_advisory_evidence_is_local_and_forecast_only():
    client = FakeClient([_initial(), _finish()])
    advisory = assess_m3_scenario(client, SCENARIO)
    assert advisory.kind == "advisory_only"
    assert advisory.evidence.source == "m3_deterministic_forecast_scheduler"
    assert advisory.evidence.energy_shifted_kwh == pytest.approx(1.1)
    # Evidence sent to the model carries forecast/planned values, no realized outcome.
    tool_payload = json.loads(client.calls[1]["messages"][-1]["content"])
    assert "realized" not in json.dumps(tool_payload).lower()


def test_complete_offline_incident():
    # 1-3. Predicted shortfall, unchanged baseline, forecast-based plan.
    evaluation = evaluate_fixture(SCENARIO)
    baseline_realized = evaluation.realized.baseline.summary
    assert baseline_realized.unserved_essential_kwh == pytest.approx(1.7175)
    assert evaluation.scheduling.summary.energy_shifted_kwh == pytest.approx(1.1)

    # 4. AI assessment via fake client (no billable call).
    advisory = assess_m3_scenario(FakeClient([_initial(), _finish()]), SCENARIO)

    # 5. Guardian denies a tampered plan.
    target = target_fixture(SCENARIO)
    historic = previous_day_fixture(SCENARIO)
    rows = [PowerInterval.model_validate({**o.model_dump(),
            "solar_generation_kw": h.solar_generation_kw})
            for o, h in zip(target.intervals, historic.intervals)]
    original = SimulationRequest(grid=target.grid, intervals=rows)
    policy = SchedulingPolicy()
    plan = schedule_flexible_load(original, policy)
    assert guard_schedule(plan, original, policy).allowed
    plan.scheduled_request.intervals[0].flexible_demand_kw += 0.5
    denied = guard_schedule(plan, original, policy)
    assert not denied.allowed and denied.reasons

    workflow = LocalApprovalWorkflow()

    # 6. First proposal (with advisory attached) is explicitly rejected.
    first = workflow.create(SCENARIO, advisory=advisory)
    assert first.status == "pending"
    assert first.advisory_headline and first.advisory_risk_level == "high"
    assert first.guardian.allowed
    rejected = workflow.decide(first.proposal_id, operator="operator-a",
                               decision="rejected")
    assert rejected.status == "rejected"
    with pytest.raises(WorkflowError):
        workflow.apply_simulation(first.proposal_id, operator="operator-a")

    # 7-8. Fresh proposal, explicit approval, simulation-only application.
    second = workflow.create(SCENARIO, advisory=advisory)
    assert second.proposal_id != first.proposal_id
    workflow.decide(second.proposal_id, operator="operator-a", decision="approved")
    applied = workflow.apply_simulation(second.proposal_id, operator="operator-a")
    assert applied.status == "applied"

    # 9. Complete audit trace verifies.
    assert [e.event for e in applied.audit] == ["proposed", "approved", "applied"]
    assert workflow.verify_audit(applied.audit)
    assert [e.event for e in rejected.audit] == ["proposed", "rejected"]

    # 10. Realized outcome compared with unchanged-operation baseline.
    assert applied.realized_essential_unserved_kwh == pytest.approx(1.0)
    assert applied.realized_essential_reduction_kwh == pytest.approx(0.7175)
    actual_baseline = run_simulation(target_fixture(SCENARIO)).summary
    assert applied.realized_essential_unserved_kwh < actual_baseline.unserved_essential_kwh
    # Trade-off is explicit, not hidden: flexible service is sacrificed.
    assert applied.realized_flexible_unserved_kwh == pytest.approx(0.877)


def test_advisory_for_wrong_scenario_cannot_attach():
    advisory = assess_m3_scenario(FakeClient([_initial(), _finish()]), SCENARIO)
    workflow = LocalApprovalWorkflow()
    with pytest.raises(WorkflowError, match="advisory_scenario_mismatch"):
        workflow.create("sunny_surplus", advisory=advisory)
