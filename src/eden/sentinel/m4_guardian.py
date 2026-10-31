"""Deterministic M4 Guardian. Validates M3 plans; never issues device commands.

A plan may originate from untrusted agents, so recompute an independently
validated M3 schedule and its M1 physics, rather than trusting claimed metrics.
Checks only forecast-time information; held-out observations are not consulted.
"""
from typing import Literal

from pydantic import Field

from eden.sentinel.twin import TwinModel, SimulationRequest, run_simulation
from eden.sentinel.m3_scheduler import SchedulingPolicy, SchedulingResult, schedule_flexible_load

EPS = 1e-8


class GuardianVerdict(TwinModel):
    mode: Literal["simulation"] = "simulation"
    allowed: bool
    reasons: list[str]
    warnings: list[str]
    forecast_essential_unserved_before_kwh: float = Field(ge=0)
    forecast_essential_unserved_after_kwh: float = Field(ge=0)
    predicted_reserve_violations: int = Field(ge=0)


def guard_schedule(plan: SchedulingResult, original_request: SimulationRequest, policy: SchedulingPolicy) -> GuardianVerdict:
    """Fail closed on any inconsistency. This is a simulation-only permission."""
    reasons: list[str] = []
    warnings: list[str] = []
    baseline = plan.baseline.summary
    forecast_after = plan.scheduled.summary
    try:
        expected = schedule_flexible_load(original_request, policy)
    except Exception as exc:
        reasons.append("schedule cannot be independently validated: " + type(exc).__name__)
    else:
        if plan.model_dump(mode="json") != expected.model_dump(mode="json"):
            reasons.append("proposal does not match deterministic scheduler output")
    try:
        rerun = run_simulation(plan.scheduled_request)
        if rerun.model_dump(mode="json") != plan.scheduled.model_dump(mode="json"):
            reasons.append("reported simulation differs from recomputed physics")
    except Exception as exc:
        reasons.append("physics re-evaluation failed: " + type(exc).__name__)

    if plan.mode != "simulation" or plan.scheduled.mode != "simulation":
        reasons.append("non-simulation mode is forbidden")
    if forecast_after.reserve_violations or forecast_after.max_abs_balance_residual_kwh > EPS:
        reasons.append("battery reserve or energy balance invalid")
    if forecast_after.unserved_essential_kwh > baseline.unserved_essential_kwh + EPS:
        reasons.append("planned essential load service worsens")
    if forecast_after.unserved_essential_kwh > EPS:
        warnings.append("forecast indicates some essential load will remain unserved")
    if forecast_after.unserved_flexible_kwh > baseline.unserved_flexible_kwh + EPS:
        warnings.append("plan increases flexible-load shortfall")
    if not plan.moves:
        warnings.append("schedule proposes no changes")
    return GuardianVerdict(
        allowed=not reasons, reasons=reasons, warnings=warnings,
        forecast_essential_unserved_before_kwh=baseline.unserved_essential_kwh,
        forecast_essential_unserved_after_kwh=forecast_after.unserved_essential_kwh,
        predicted_reserve_violations=forecast_after.reserve_violations,
    )
