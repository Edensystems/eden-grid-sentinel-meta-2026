"""Reproducible, offline M6 evaluation evidence for the EDEN synthetic microgrid.

No credentials, network/model calls, cloud writes or hardware access. The default
uses a deterministic fake-client for Muse Spark protocol verification; the fake
response is explicitly NOT evidence of a live model call. Live evidence is
provided separately in docs/hackathon/M2_LIVE_SMOKE_2026-10-31.json.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
from types import SimpleNamespace as NS
from typing import Any

from eden.sentinel.m3_demo import (available_scenarios, evaluate_fixture,
                                   previous_day_fixture, target_fixture)
from eden.sentinel.m3_scheduler import SchedulingPolicy, schedule_flexible_load
from eden.sentinel.m4_guardian import guard_schedule
from eden.sentinel.m4_workflow import LocalApprovalWorkflow, WorkflowError
from eden.sentinel.m5_readonly import app as preview_app
from eden.sentinel.twin import PowerInterval, SimulationRequest

SCENARIO = "critical_priority_school"


def _canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _stable_number(n: float) -> float:
    """Suppress harmless platform last-bit float noise without hiding 1e-6 shifts."""
    return round(float(n), 9)


def _fake_muse_advisory(scenario: str):
    """Exercise the real M2 adapter with a fake transport, not a provider request."""
    from eden.sentinel.muse import assess_m3_scenario

    class DeterministicFakeClient:
        def __init__(self):
            self.calls = []
            self.chat = NS(completions=NS(create=self.create))

        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                tool_call = NS(id="m6_mock_call_1", function=NS(
                    name="get_m3_evaluation", arguments=json.dumps({"scenario_name":scenario}),
                ))
                return NS(choices=[NS(finish_reason="tool_calls",
                                      message=NS(tool_calls=[tool_call], content=None))])
            if len(self.calls) == 2:
                payload = {
                    "scenario_name":scenario,
                    "data_mode":"simulation",
                    "risk_level":"high",
                    "headline":"Synthetic shortage detected in a school microgrid",
                    "explanation":"Forecast-informed load shifting may protect essential school loads while reducing flexible load service. Synthetic data only.",
                    "suggested_next_step":"Request independent Guardian validation and explicit operator authorization; do not control equipment.",
                    "requires_human_approval":True,
                }
                return NS(choices=[NS(finish_reason="stop",
                                      message=NS(tool_calls=None, content=json.dumps(payload)))])
            raise AssertionError("Exceeded M6 fake client request cap")

    fake = DeterministicFakeClient()
    result = assess_m3_scenario(fake, scenario)
    assert len(fake.calls) == 2
    assert result.mode == "simulation" and result.kind == "advisory_only"
    assert result.evidence.scenario_name == scenario
    assert result.assessment.requires_human_approval is True
    # No realized target-day outcome may enter model tool evidence.
    tool_output = _canonical(fake.calls[1]["messages"][-1])
    assert "realized" not in tool_output.lower()
    return result


def _audit_valid(workflow: LocalApprovalWorkflow, view) -> bool:
    if hasattr(view, "audit_head_hash"):
        return bool(workflow.verify_audit(view.audit, expected_head=view.audit_head_hash))
    return bool(workflow.verify_audit(view.audit))  # Historical M4 staged fallback


def _scenario_metrics(name: str) -> dict[str, Any]:
    e = evaluate_fixture(name)
    e_again = evaluate_fixture(name)
    if e.model_dump_json() != e_again.model_dump_json():
        raise AssertionError(f"Nondeterministic M3 scenario: {name}")
    realized = e.realized
    base, scheduled = realized.baseline.summary, realized.scheduled.summary
    if scheduled.reserve_violations or realized.max_abs_bus_residual_kwh > 1e-8:
        raise AssertionError(f"Simulation safety invariant violated: {name}")
    if abs(realized.essential_unserved_reduction_kwh -
           (base.unserved_essential_kwh - scheduled.unserved_essential_kwh)) > 1e-8:
        raise AssertionError("Inconsistent essential-load comparison")
    if abs(realized.flexible_unserved_reduction_kwh -
           (base.unserved_flexible_kwh - scheduled.unserved_flexible_kwh)) > 1e-8:
        raise AssertionError("Inconsistent flexible-load comparison")
    return {
        "scenario": name,
        "data_mode": "simulation",
        "method": e.forecast.method,
        "solar_mae_kw": _stable_number(e.forecast.metrics.solar_mae_kw),
        "essential_baseline_unserved_kwh": _stable_number(base.unserved_essential_kwh),
        "essential_scheduled_unserved_kwh": _stable_number(scheduled.unserved_essential_kwh),
        "essential_unserved_reduction_kwh": _stable_number(realized.essential_unserved_reduction_kwh),
        "flexible_baseline_unserved_kwh": _stable_number(base.unserved_flexible_kwh),
        "flexible_scheduled_unserved_kwh": _stable_number(scheduled.unserved_flexible_kwh),
        "flexible_unserved_reduction_kwh": _stable_number(realized.flexible_unserved_reduction_kwh),
        "energy_shifted_kwh": _stable_number(e.scheduling.summary.energy_shifted_kwh),
        "final_soc_fraction": _stable_number(scheduled.final_soc_fraction),
        "reserve_violations": scheduled.reserve_violations,
        "max_abs_bus_residual_kwh": _stable_number(realized.max_abs_bus_residual_kwh),
        "scheduler_method": e.scheduling.method,
        "scheduler_status": e.scheduling.status,
    }


def _tampered_plan_denied() -> bool:
    """Guardian must refuse a forecast plan edited after scheduling."""
    target, historic = target_fixture(SCENARIO), previous_day_fixture(SCENARIO)
    rows = [PowerInterval.model_validate({**o.model_dump(),
            "solar_generation_kw": h.solar_generation_kw})
            for o, h in zip(target.intervals, historic.intervals)]
    original = SimulationRequest(grid=target.grid, intervals=rows)
    policy = SchedulingPolicy()
    plan = schedule_flexible_load(original, policy)
    if not guard_schedule(plan, original, policy).allowed:
        raise AssertionError("Guardian rejected the untampered deterministic plan")
    plan.scheduled_request.intervals[0].flexible_demand_kw += 0.5
    verdict = guard_schedule(plan, original, policy)
    return not verdict.allowed and bool(verdict.reasons)


def _incident(*, use_mock_muse: bool) -> dict[str, Any]:
    advisory = _fake_muse_advisory(SCENARIO) if use_mock_muse else None
    if not _tampered_plan_denied():
        raise AssertionError("Guardian accepted a tampered plan")
    workflow = LocalApprovalWorkflow(clock=lambda: datetime(2026, 11, 3, 12, 0,
                                                           tzinfo=timezone.utc))
    first = workflow.create(SCENARIO, advisory=advisory) if use_mock_muse else workflow.create(SCENARIO)
    workflow.decide(first.proposal_id, operator="m6-demo-operator", decision="rejected")
    rejected_blocked = False
    try:
        workflow.apply_simulation(first.proposal_id, operator="m6-demo-operator")
    except WorkflowError:
        rejected_blocked = True
    if not rejected_blocked:
        raise AssertionError("Rejected proposal unexpectedly executed")
    # Re-read after the refusal so the verified chain includes the denied event.
    rejected = workflow.inspect(first.proposal_id)
    approved = workflow.create(SCENARIO, advisory=advisory) if use_mock_muse else workflow.create(SCENARIO)
    workflow.decide(approved.proposal_id, operator="m6-demo-operator", decision="approved")
    workflow.apply_simulation(approved.proposal_id, operator="m6-demo-operator")
    replay_blocked = False
    try:
        workflow.apply_simulation(approved.proposal_id, operator="m6-demo-operator")
    except WorkflowError:
        replay_blocked = True
    if not replay_blocked:
        raise AssertionError("Repeated proposal application unexpectedly succeeded")
    applied = workflow.inspect(approved.proposal_id)
    if not _audit_valid(workflow, applied) or not _audit_valid(workflow, rejected):
        raise AssertionError("Audit chain integrity failed")
    if rejected.audit[-1].event != "denied" or applied.audit[-1].event != "denied":
        raise AssertionError("Refused execution attempts were not audited")
    comparison = evaluate_fixture(SCENARIO)
    if abs(applied.realized_essential_unserved_kwh -
           comparison.realized.scheduled.summary.unserved_essential_kwh) > 1e-8:
        raise AssertionError("M4 realized outcome differs from M3 scenario")
    return {
        "scenario":SCENARIO,
        "data_mode":"simulation",
        "model_step":"deterministic_fake_client" if use_mock_muse else "not_exercised_staged_fallback",
        "tampered_plan_denied_by_guardian":True,
        "proposal_rejection_enforced":rejected_blocked,
        "single_application_enforced":replay_blocked,
        "guardian_approved_plan":bool(applied.guardian.allowed),
        "audit_chain_verified":True,
        "rejected_event_types":[event.event for event in rejected.audit],
        "approved_event_types":[event.event for event in applied.audit],
        "realized_essential_unserved_kwh":_stable_number(applied.realized_essential_unserved_kwh),
        "realized_flexible_unserved_kwh":_stable_number(applied.realized_flexible_unserved_kwh),
        "realized_essential_reduction_kwh":_stable_number(applied.realized_essential_reduction_kwh),
        "operator_auth":"local_demonstration_only",
        "audit_storage":"volatile_in_memory",
    }


def generate_evidence(*, use_mock_muse: bool = True) -> dict[str, Any]:
    expected_paths = {"/health", "/m3/scenarios", "/m3/evaluate/{scenario}"}
    routes = {path for path in preview_app.openapi()["paths"]}
    if routes != expected_paths:
        raise AssertionError(f"Unexpected M5 preview paths: {sorted(routes)}")
    for path, methods in preview_app.openapi()["paths"].items():
        if set(methods) != {"get"}:
            raise AssertionError(f"Read-only endpoint has non-GET method: {path}")
    scenarios = [_scenario_metrics(name) for name in available_scenarios()]
    incident = _incident(use_mock_muse=use_mock_muse)
    core = {
        "evidence_version":"1.0",
        "project":"EDEN Grid Sentinel",
        "data_mode":"simulation",
        "validation":"offline_deterministic",
        "meta_inference":"FAKE_CLIENT_ONLY" if use_mock_muse else "NOT_EXERCISED",
        "m5_preview_mode":"read_only",
        "scenarios":scenarios,
        "incident":incident,
    }
    return {"sha256_canonical":sha256(_canonical(core).encode()).hexdigest(), **core}


def write_evidence(out_dir: Path, data: dict[str, Any]):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/"m6_evidence.json").write_text(
        json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    lines=[
        "# EDEN Grid Sentinel — M6 Offline Verification",
        "",
        ("**Data classification:** Synthetic simulation; deterministic fake model transport, not a live Meta request."
         if data["meta_inference"] == "FAKE_CLIENT_ONLY"
         else "**Data classification:** Synthetic simulation; M2 transport not exercised in this staged fallback."),
        "",
        "**Reproducibility fingerprint:** `"+data["sha256_canonical"]+"`",
        "",
        "| Scenario | Essential unmet baseline → schedule (kWh) | Flexible unmet baseline → schedule (kWh) | Reserve violations |",
        "|---|---:|---:|---:|",
    ]
    for x in data["scenarios"]:
        lines.append(f'| {x["scenario"]} | {x["essential_baseline_unserved_kwh"]:.4f} → {x["essential_scheduled_unserved_kwh"]:.4f} | {x["flexible_baseline_unserved_kwh"]:.4f} → {x["flexible_scheduled_unserved_kwh"]:.4f} | {x["reserve_violations"]} |')
    lines += ["", "## Incident gate checks", "",
              f'- Guardian denied tampered plan: {data["incident"]["tampered_plan_denied_by_guardian"]}',
              f'- Human rejection enforced: {data["incident"]["proposal_rejection_enforced"]}',
              f'- Repeat application denied: {data["incident"]["single_application_enforced"]}',
              f'- Guardian accepted validated plan: {data["incident"]["guardian_approved_plan"]}',
              f'- In-memory audit chain verified: {data["incident"]["audit_chain_verified"]}',
              "", "## Limitations", "",
              "- The output is an **offline synthetic** benchmark, not measured site data or proof of energy savings.",
              ("- M2 advice here uses deterministic fake transport, not a live provider request. The separate 2026-10-31 live smoke is documented in the repository."
               if data["meta_inference"] == "FAKE_CLIENT_ONLY" else
               "- M2 advice was NOT exercised in this staged fallback; the final M6 candidate must use the default full integration mode."),
              "- M4 audit is in-memory and single-process; it is not a production authorization service.",
              "- This report does not certify cloud staging, official rules eligibility, or the visual browser walkthrough.",
              ""]
    (out_dir/"m6_evidence.md").write_text("\n".join(lines),encoding="utf-8")


def main() -> int:
    p=argparse.ArgumentParser(description="M6 offline evidence generator (no API calls or secrets)")
    p.add_argument("--out-dir",default="artifacts/m6")
    p.add_argument("--staged-baseline-only",action="store_true",
                   help="Local historical patch verification only; disables M2 mock protocol and labels it as NOT_EXERCISED")
    args=p.parse_args()
    data=generate_evidence(use_mock_muse=not args.staged_baseline_only)
    output=Path(args.out_dir)
    write_evidence(output,data)
    print("M6 offline evidence validated; scenario_count="+str(len(data["scenarios"])))
    print("meta_step="+data["meta_inference"]+"; M5_api=read_only")
    print("fingerprint="+data["sha256_canonical"])
    print("wrote="+str(output/"m6_evidence.json"))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
