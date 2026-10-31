"""M3 synthetic fixture catalog, forecast evaluation and simulated scheduling."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from eden.sentinel.scenarios import build_scenario, scenario_names
from eden.sentinel.twin import (
    GridParameters, PowerInterval, SimulationRequest, SimulationResult,
    TwinModel, run_simulation,
)
from eden.sentinel.m3_forecast import ForecastEvaluation, previous_day_forecast
from eden.sentinel.m3_scheduler import SchedulingPolicy, SchedulingResult, schedule_flexible_load

# Independently defined synthetic prior-day reference profiles.
# No target-day power readings are used in prediction construction.
# Values are illustrative: NOT measured/weather-validated data.
HISTORICAL_PROFILES = {
    "cloudy_school_day": (
        [2.5, 2.7, 1.8, 0.8, 0.2, 0.1, 0.0],
        [1.2, 1.2, 1.2, 1.1, 1.1, 1.2, 1.2],
        [0.7, 0.8, 0.8, 0.6, 0.5, 0.3, 0.4],
    ),
    "night_reserve": (
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.1, 1.2, 1.3],
        [0.5, 0.5, 0.5, 0.5],
    ),
    "sunny_surplus": (
        [2.8, 3.0, 3.2, 2.9],
        [1.0, 0.9, 1.1, 1.0],
        [0.4, 0.5, 0.6, 0.5],
    ),
    "critical_priority_school": (
        [3.8, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.5, 0.0, 0.0, 0.0],
    ),
}


class RealizedComparison(TwinModel):
    data_mode: Literal["simulation"] = "simulation"
    baseline: SimulationResult
    scheduled: SimulationResult
    essential_unserved_reduction_kwh: float
    flexible_unserved_reduction_kwh: float
    battery_reserve_violations: int
    max_abs_bus_residual_kwh: float


class M3Evaluation(TwinModel):
    mode: Literal["simulation"] = "simulation"
    scenario: str
    forecast: ForecastEvaluation
    scheduling: SchedulingResult  # Forecast-based plan only
    realized: RealizedComparison  # Outcome on held-out synthetic solar


def available_scenarios() -> list[str]:
    return sorted(HISTORICAL_PROFILES)


def target_fixture(name: str) -> SimulationRequest:
    if name == "critical_priority_school":
        start = datetime(2026, 10, 28, 7, 0, tzinfo=timezone.utc)
        return SimulationRequest(
            grid=GridParameters(
                site_id="school-demo-001", battery_capacity_kwh=4.0,
                initial_soc_fraction=0.2, minimum_soc_fraction=0.2,
                max_charge_kw=3.0, max_discharge_kw=2.0,
                charge_efficiency=0.95, discharge_efficiency=0.9,
            ),
            intervals=[PowerInterval(
                timestamp=start + timedelta(hours=i), duration_minutes=60,
                solar_generation_kw=solar, essential_demand_kw=1.0,
                flexible_demand_kw=(1.5 if i == 0 else 0.0),
            ) for i, solar in enumerate([4.0, 0.0, 0.0, 0.0])],
        )
    if name not in scenario_names():
        raise ValueError("unknown synthetic scenario")
    return build_scenario(name)


def previous_day_fixture(name: str) -> SimulationRequest:
    """Create a historical fixture from independent, hard-coded synthetic arrays."""
    target = target_fixture(name)
    solar, essential, flexible = HISTORICAL_PROFILES[name]
    if len(solar) != len(target.intervals):
        raise AssertionError("historical fixture lengths must match")
    rows = [PowerInterval(
        timestamp=target.intervals[i].timestamp - timedelta(days=1),
        duration_minutes=target.intervals[i].duration_minutes,
        solar_generation_kw=solar[i],
        essential_demand_kw=essential[i],
        flexible_demand_kw=flexible[i],
    ) for i in range(len(solar))]
    return SimulationRequest(grid=target.grid, intervals=rows)


def evaluate_against_actual(
    name: str, reference: SimulationRequest, actual: SimulationRequest,
    policy: SchedulingPolicy | None = None,
) -> M3Evaluation:
    """Plan using forecast solar and *published demand timetable*; score on actual.

    Future actual solar values are used ONLY for retrospective MAE and final
    simulation, never when choosing the flexible scheduling moves.
    """
    forecast = previous_day_forecast(reference, actual)
    expected_rows = []
    for idx, row in enumerate(actual.intervals):
        data = row.model_dump()
        data["solar_generation_kw"] = forecast.forecasts[idx].solar_kw
        # Essential/flexible powers are treated as a known published timetable,
        # not measurements fetched from the future.
        expected_rows.append(PowerInterval.model_validate(data))
    expected_request = SimulationRequest(grid=actual.grid, intervals=expected_rows)
    plan = schedule_flexible_load(expected_request, policy)
    applied_rows = []
    for observed_row, planned_row in zip(actual.intervals,
                                         plan.scheduled_request.intervals):
        data = observed_row.model_dump()
        data["flexible_demand_kw"] = planned_row.flexible_demand_kw
        applied_rows.append(PowerInterval.model_validate(data))
    realized_request = SimulationRequest(grid=actual.grid, intervals=applied_rows)
    actual_baseline = run_simulation(actual)
    actual_scheduled = run_simulation(realized_request)
    observed, changed = actual_baseline.summary, actual_scheduled.summary
    realized = RealizedComparison(
        baseline=actual_baseline, scheduled=actual_scheduled,
        essential_unserved_reduction_kwh=(
            observed.unserved_essential_kwh - changed.unserved_essential_kwh
        ),
        flexible_unserved_reduction_kwh=(
            observed.unserved_flexible_kwh - changed.unserved_flexible_kwh
        ),
        battery_reserve_violations=changed.reserve_violations,
        max_abs_bus_residual_kwh=changed.max_abs_balance_residual_kwh,
    )
    return M3Evaluation(scenario=name, forecast=forecast,
                        scheduling=plan, realized=realized)


def evaluate_fixture(name: str, policy: SchedulingPolicy | None = None) -> M3Evaluation:
    target = target_fixture(name)
    historic = previous_day_fixture(name)
    return evaluate_against_actual(name, historic, target, policy)
