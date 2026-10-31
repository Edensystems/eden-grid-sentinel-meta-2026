"""M3 regression tests: power balance, safety, forecast leakage and constraints."""
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from eden.sentinel.scenarios import build_scenario, scenario_names
from eden.sentinel.twin import PowerInterval, SimulationRequest, run_simulation
from eden.sentinel.m3_demo import evaluate_fixture, evaluate_against_actual, previous_day_fixture
from eden.sentinel.m3_forecast import previous_day_forecast
from eden.sentinel.m3_scheduler import SchedulingPolicy, schedule_flexible_load
from eden.sentinel.m3_routes import router


def test_solar_forecast_reproducible_and_no_target_leakage():
    target = build_scenario("cloudy_school_day")
    reference = previous_day_fixture("cloudy_school_day")
    first = previous_day_forecast(reference, target)
    second = previous_day_forecast(reference, target)
    assert first.model_dump_json() == second.model_dump_json()
    assert first.metrics.sample_count == len(target.intervals)
    # Forecast input is previous-day PV, not current actual generation.
    assert first.forecasts[0].solar_kw == pytest.approx(reference.intervals[0].solar_generation_kw)
    assert first.forecasts[0].solar_kw != target.intervals[0].solar_generation_kw
    assert first.metrics.solar_mae_kw > 0


def test_reference_must_precede_target_by_24h():
    target = build_scenario("night_reserve")
    with pytest.raises(ValueError, match="24 hours"):
        previous_day_forecast(target, target)


def test_reference_wrong_horizon_rejected():
    target = build_scenario("cloudy_school_day")
    ref = previous_day_fixture("night_reserve")
    ref = SimulationRequest(grid=ref.grid, intervals=ref.intervals[:-1])
    with pytest.raises(ValueError, match="horizon"):
        previous_day_forecast(ref, target)


def test_reference_mismatched_duration_rejected():
    target = build_scenario("night_reserve")
    ref = previous_day_fixture("cloudy_school_day")
    rows = ref.intervals.copy()
    # A 30-minute sample is valid as data but cannot align to the 60m target.
    rows[0] = PowerInterval.model_validate({**rows[0].model_dump(), 'duration_minutes':30})
    # contiguous check in request catches before predictor, which is also appropriate
    with pytest.raises(ValidationError):
        SimulationRequest(grid=ref.grid, intervals=rows)


def test_forecast_site_mismatch_rejected():
    target = build_scenario("night_reserve")
    ref = previous_day_fixture("night_reserve")
    grid = type(ref.grid).model_validate({**ref.grid.model_dump(), "site_id": "other-school"})
    with pytest.raises(ValueError, match="same site"):
        previous_day_forecast(SimulationRequest(grid=grid, intervals=ref.intervals), target)


@pytest.mark.parametrize("scenario", scenario_names())
def test_scheduler_conserves_load_and_reserve(scenario):
    base = build_scenario(scenario)
    result = schedule_flexible_load(base)
    s = result.summary
    assert result.mode == "simulation"
    assert result.scheduled.mode == "simulation"
    assert abs(s.workload_after_kwh - s.workload_before_kwh) < 1e-8
    assert s.reserve_violations == 0
    assert s.max_abs_balance_residual_kwh < 1e-8
    assert s.essential_unserved_scheduled_kwh <= s.essential_unserved_baseline_kwh + 1e-8
    if abs(s.essential_unserved_scheduled_kwh - s.essential_unserved_baseline_kwh) < 1e-8:
        assert s.flexible_unserved_scheduled_kwh <= s.flexible_unserved_baseline_kwh + 1e-8
    assert run_simulation(result.scheduled_request).model_dump_json() == result.scheduled.model_dump_json()
    assert result.scheduled_request.grid.site_id == base.grid.site_id
    for item in result.scheduled.intervals:
        assert item.soc_end_fraction >= base.grid.minimum_soc_fraction - 1e-8
        assert item.soc_end_fraction <= 1 + 1e-8
        assert item.battery_charge_input_kwh == 0 or item.battery_discharge_output_kwh == 0
        assert item.served_essential_kwh + item.unserved_essential_kwh == pytest.approx(item.essential_demand_kwh)
        assert item.served_flexible_kwh + item.unserved_flexible_kwh == pytest.approx(item.flexible_demand_kwh)


def test_local_search_repeatable():
    base = build_scenario("cloudy_school_day")
    policy = SchedulingPolicy(max_moves=12)
    first = schedule_flexible_load(base, policy)
    assert first.model_dump_json() == schedule_flexible_load(base, policy).model_dump_json()


def test_zero_budget_keeps_baseline():
    base = build_scenario("cloudy_school_day")
    result = schedule_flexible_load(base, SchedulingPolicy(max_moves=0))
    assert result.scheduled.model_dump_json() == result.baseline.model_dump_json()
    assert result.moves == []


def test_invalid_max_power_is_rejected():
    base = build_scenario("cloudy_school_day")
    with pytest.raises(ValueError, match="exceeds scheduling power cap"):
        schedule_flexible_load(base, SchedulingPolicy(flexible_power_cap_kw=0.1))


def test_shift_window_preserved():
    base = build_scenario("cloudy_school_day")
    result = schedule_flexible_load(base, SchedulingPolicy(
        flexible_power_cap_kw=1.5, first_shiftable_index=1,
        last_shiftable_index=3, max_moves=16,
    ))
    for i in (0, 4, 5, 6):
        assert result.scheduled_request.intervals[i].flexible_demand_kw == pytest.approx(
            base.intervals[i].flexible_demand_kw)


def test_bad_shift_window_rejected():
    with pytest.raises(ValueError, match="invalid scheduling window"):
        schedule_flexible_load(build_scenario("night_reserve"),
                               SchedulingPolicy(first_shiftable_index=9))


def test_rejects_nonfinite_policy():
    with pytest.raises(ValidationError):
        SchedulingPolicy(quantum_kwh=float("inf"))


def test_hard_full_service_infeasible():
    result = schedule_flexible_load(
        build_scenario("night_reserve"),
        SchedulingPolicy(require_full_service=True, max_moves=4),
    )
    assert result.status == "infeasible"
    assert result.summary.essential_unserved_scheduled_kwh > 0


def test_critical_load_scenario_shows_tradeoff():
    o = evaluate_fixture("critical_priority_school")
    assert o.realized.essential_unserved_reduction_kwh > 0.5
    assert o.realized.battery_reserve_violations == 0
    assert o.scheduling.summary.workload_before_kwh == pytest.approx(o.scheduling.summary.workload_after_kwh)


def test_evaluate_fixture_consistency():
    result = evaluate_fixture("cloudy_school_day", SchedulingPolicy(max_moves=4))
    assert result.mode == "simulation"
    assert result.forecast.metrics.solar_mae_kw >= 0
    assert result.realized.battery_reserve_violations == 0
    with pytest.raises(ValueError):
        evaluate_fixture("does-not-exist")


def test_read_only_api_routes():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    names = client.get("/m3/scenarios")
    assert names.status_code == 200
    assert "cloudy_school_day" in names.json()
    response = client.get("/m3/evaluate/cloudy_school_day")
    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "simulation"
    assert response.json()["realized"]["battery_reserve_violations"] == 0
    assert client.get("/m3/evaluate/nonexistent").status_code == 404
    assert client.get("/act").status_code == 404


def test_api_rejects_invalid_custom_policy():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.post("/m3/evaluate/cloudy_school_day", json={"max_moves":99999}).status_code == 422
    assert client.post("/m3/evaluate/cloudy_school_day", json={"flexible_power_cap_kw":0.1}).status_code == 422
    assert client.post("/m3/evaluate/nonexistent", json={}).status_code == 404


def test_no_simulator_demand_fields_modified_in_input():
    source = build_scenario("cloudy_school_day")
    before = source.model_dump_json()
    _ = schedule_flexible_load(source, SchedulingPolicy(max_moves=8))
    assert source.model_dump_json() == before


def test_plan_does_not_use_future_actual_solar():
    from eden.sentinel.m3_demo import target_fixture
    target = target_fixture("critical_priority_school")
    reference = previous_day_fixture("critical_priority_school")
    first = evaluate_against_actual("critical_priority_school", reference, target)
    altered = [PowerInterval.model_validate({**r.model_dump(),
        "solar_generation_kw": r.solar_generation_kw * 0.5}) for r in target.intervals]
    changed = SimulationRequest(grid=target.grid, intervals=altered)
    second = evaluate_against_actual("critical_priority_school", reference, changed)
    assert first.scheduling.scheduled_request.model_dump_json() == second.scheduling.scheduled_request.model_dump_json()
    assert first.realized.baseline.model_dump_json() != second.realized.baseline.model_dump_json()


def test_forecast_error_can_reduce_realized_critical_load_service():
    from eden.sentinel.m3_demo import target_fixture
    actual = target_fixture("critical_priority_school")
    reference = previous_day_fixture("critical_priority_school")
    rows = reference.intervals.copy()
    rows[0] = PowerInterval.model_validate({**rows[0].model_dump(), "solar_generation_kw": 3.4})
    poorly_forecast = SimulationRequest(grid=reference.grid, intervals=rows)
    outcome = evaluate_against_actual("critical_priority_school", poorly_forecast, actual)
    # We report the downside honestly instead of suppressing forecast error.
    assert outcome.realized.essential_unserved_reduction_kwh < 0
    assert outcome.realized.battery_reserve_violations == 0
