"""M3 constrained, deterministic local-search flexible-load scheduler.

Finds a locally improved schedule using the M1 simulator as the evaluation oracle;
NOT a mathematically proven global optimum. No effect outside returned simulated data.
"""
from typing import Literal

from pydantic import Field
from eden.sentinel.twin import (
    SimulationRequest, SimulationResult, PowerInterval, TwinModel, run_simulation,
)

EPS = 1e-8


class SchedulingPolicy(TwinModel):
    flexible_power_cap_kw: float = Field(default=1.5, ge=0)
    quantum_kwh: float = Field(default=0.1, gt=0, le=5)
    max_moves: int = Field(default=64, ge=0, le=250)
    first_shiftable_index: int = Field(default=0, ge=0)
    last_shiftable_index: int | None = Field(default=None, ge=0)
    # Full completion must be evaluated, not assumed or falsely called infeasible.
    require_full_service: bool = False


class LoadMovement(TwinModel):
    from_index: int = Field(ge=0)
    to_index: int = Field(ge=0)
    energy_kwh: float = Field(gt=0)


class SchedulingSummary(TwinModel):
    essential_unserved_baseline_kwh: float = Field(ge=0)
    essential_unserved_scheduled_kwh: float = Field(ge=0)
    flexible_unserved_baseline_kwh: float = Field(ge=0)
    flexible_unserved_scheduled_kwh: float = Field(ge=0)
    essential_unserved_reduction_kwh: float
    flexible_unserved_reduction_kwh: float
    workload_before_kwh: float = Field(ge=0)
    workload_after_kwh: float = Field(ge=0)
    energy_shifted_kwh: float = Field(ge=0)
    solar_curtailed_before_kwh: float = Field(ge=0)
    solar_curtailed_after_kwh: float = Field(ge=0)
    reserve_violations: int = Field(ge=0)
    max_abs_balance_residual_kwh: float = Field(ge=0)


class SchedulingResult(TwinModel):
    mode: Literal["simulation"] = "simulation"
    method: Literal["bounded_pairwise_local_search"] = "bounded_pairwise_local_search"
    status: Literal["feasible", "degraded", "not_fully_served", "infeasible"]
    explanation: str
    baseline: SimulationResult
    scheduled: SimulationResult
    scheduled_request: SimulationRequest
    moves: list[LoadMovement]
    summary: SchedulingSummary


def _make_schedule(original: SimulationRequest, energies: list[float]) -> SimulationRequest:
    rows = []
    for row, kwh in zip(original.intervals, energies):
        data = row.model_dump()
        data["flexible_demand_kw"] = max(0.0, kwh) / (row.duration_minutes / 60.0)
        rows.append(PowerInterval.model_validate(data))
    return SimulationRequest(grid=original.grid, intervals=rows)


def _grade(out: SimulationResult, original: list[float], energies: list[float]) -> tuple[float, ...]:
    """Lexicographic: essential served first, then flexible, then avoid changes."""
    s = out.summary
    moved = sum(abs(a - b) for a, b in zip(original, energies)) / 2
    # Round only numerical comparison; raw simulator outputs remain full precision.
    return (round(s.unserved_essential_kwh, 9),
            round(s.unserved_flexible_kwh, 9),
            round(moved, 9),
            round(s.curtailed_solar_kwh, 9))


def schedule_flexible_load(request: SimulationRequest, policy: SchedulingPolicy | None = None) -> SchedulingResult:
    policy = policy or SchedulingPolicy()
    n = len(request.intervals)
    if n > 24:
        raise ValueError("M3 local-search horizon limited to 24 intervals")
    first = policy.first_shiftable_index
    last = n - 1 if policy.last_shiftable_index is None else policy.last_shiftable_index
    if first > last or last >= n:
        raise ValueError("invalid scheduling window indices")
    original = [row.flexible_demand_kw * row.duration_minutes / 60 for row in request.intervals]
    capacity = [policy.flexible_power_cap_kw * row.duration_minutes / 60 for row in request.intervals]
    # A limit lower than already scheduled flexible load is a proof of infeasibility
    # under this request's fixed baseline. Do not silently discard work.
    if any(original[i] > capacity[i] + EPS for i in range(first, last + 1)):
        raise ValueError("baseline flexible demand exceeds scheduling power cap")
    baseline = run_simulation(request)
    current_energy = original.copy()
    current_result = baseline
    current_grade = _grade(baseline, original, original)
    moves: list[LoadMovement] = []

    for _ in range(policy.max_moves):
        candidate = None
        candidate_grade = current_grade
        for source in range(first, last + 1):
            if current_energy[source] <= EPS:
                continue
            for target in range(first, last + 1):
                if source == target:
                    continue
                shift = min(policy.quantum_kwh, current_energy[source],
                            capacity[target] - current_energy[target])
                if shift <= EPS:
                    continue
                trial = current_energy.copy()
                trial[source] -= shift
                trial[target] += shift
                candidate_request = _make_schedule(request, trial)
                candidate_output = run_simulation(candidate_request)
                grade = _grade(candidate_output, original, trial)
                if grade < candidate_grade:
                    candidate_grade = grade
                    candidate = (source, target, shift, trial, candidate_output)
        if candidate is None:
            break
        source, target, quantity, current_energy, current_result = candidate
        moves.append(LoadMovement(from_index=source, to_index=target, energy_kwh=quantity))
        current_grade = candidate_grade

    planned_request = _make_schedule(request, current_energy)
    scheduled = run_simulation(planned_request)  # re-evaluate final plan independently
    if abs(sum(original) - sum(current_energy)) > EPS:
        raise ArithmeticError("flexible workload energy was not preserved")
    if scheduled.summary.reserve_violations or scheduled.summary.max_abs_balance_residual_kwh > EPS:
        raise ArithmeticError("safety invariants failed")
    for i in range(first, last + 1):
        if current_energy[i] > capacity[i] + EPS:
            raise ArithmeticError("flexible power cap violated")
    for i in (*range(0, first), *range(last + 1, n)):
        if abs(current_energy[i] - original[i]) > EPS:
            raise ArithmeticError("load outside shift window changed")

    unfinished = (scheduled.summary.unserved_flexible_kwh > EPS or
                  scheduled.summary.unserved_essential_kwh > EPS)
    # Necessary physical upper bound on energy available to all loads.
    # Ignoring charge/discharge bottlenecks and conversion losses makes this an
    # optimistic bound; when it is inadequate, full service is provably impossible.
    solar_total = sum(row.solar_generation_kw * row.duration_minutes / 60
                      for row in request.intervals)
    demand_total = sum((row.essential_demand_kw + row.flexible_demand_kw)
                       * row.duration_minutes / 60 for row in request.intervals)
    initial_battery_deliverable = (
        request.grid.battery_capacity_kwh *
        (request.grid.initial_soc_fraction - request.grid.minimum_soc_fraction) *
        request.grid.discharge_efficiency
    )
    proven_shortfall = demand_total > solar_total + initial_battery_deliverable + EPS
    if policy.require_full_service and proven_shortfall:
        status = "infeasible"
    elif policy.require_full_service and unfinished:
        status = "not_fully_served"  # NOT proof of global infeasibility
    elif unfinished:
        status = "degraded"
    else:
        status = "feasible"

    sb, so = baseline.summary, scheduled.summary
    moved = sum(abs(a - b) for a, b in zip(original, current_energy)) / 2
    return SchedulingResult(
        status=status,
        explanation=(
            "Proven full-service infeasibility: even optimistic PV plus initially "
            "usable battery energy is less than total demand. No physical actions."
            if status == "infeasible" else
            "Constrained local-search best effort, not certified global optimum. "
            "Unserved loads, if any, remain explicit. No physical actions."
        ),
        baseline=baseline,
        scheduled=scheduled,
        scheduled_request=planned_request,
        moves=moves,
        summary=SchedulingSummary(
            essential_unserved_baseline_kwh=sb.unserved_essential_kwh,
            essential_unserved_scheduled_kwh=so.unserved_essential_kwh,
            flexible_unserved_baseline_kwh=sb.unserved_flexible_kwh,
            flexible_unserved_scheduled_kwh=so.unserved_flexible_kwh,
            essential_unserved_reduction_kwh=sb.unserved_essential_kwh - so.unserved_essential_kwh,
            flexible_unserved_reduction_kwh=sb.unserved_flexible_kwh - so.unserved_flexible_kwh,
            workload_before_kwh=sum(original), workload_after_kwh=sum(current_energy),
            energy_shifted_kwh=moved,
            solar_curtailed_before_kwh=sb.curtailed_solar_kwh,
            solar_curtailed_after_kwh=so.curtailed_solar_kwh,
            reserve_violations=so.reserve_violations,
            max_abs_balance_residual_kwh=so.max_abs_balance_residual_kwh,
        ),
    )
