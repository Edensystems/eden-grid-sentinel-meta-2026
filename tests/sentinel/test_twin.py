"""M1 tests. The values are simulated fixtures, not field measurements."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from eden.sentinel.api import app
from eden.sentinel.scenarios import build_scenario, scenario_names
from eden.sentinel.twin import GridParameters, PowerInterval, SimulationRequest, run_simulation

T = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)


def cfg(**updates):
    params = dict(site_id="school", battery_capacity_kwh=10,
                  initial_soc_fraction=0.5, minimum_soc_fraction=0.2,
                  max_charge_kw=3, max_discharge_kw=3,
                  charge_efficiency=0.9, discharge_efficiency=0.8)
    params.update(updates)
    return GridParameters(**params)


def simulate(solar=0, essential=0, flexible=0, duration=60, **kwargs):
    request = SimulationRequest(
        grid=cfg(**kwargs),
        intervals=[PowerInterval(timestamp=T, duration_minutes=duration,
                                 solar_generation_kw=solar,
                                 essential_demand_kw=essential,
                                 flexible_demand_kw=flexible)])
    return run_simulation(request)


def test_solar_first():
    output = simulate(solar=2, essential=1, flexible=1).intervals[0]
    assert output.served_essential_kwh == 1
    assert output.served_flexible_kwh == 1
    assert output.battery_discharge_output_kwh == 0


def test_charge_efficiency():
    output = simulate(solar=4, essential=1).intervals[0]
    assert output.battery_charge_input_kwh == pytest.approx(3)
    assert output.soc_end_fraction == pytest.approx(.77)
    assert output.battery_conversion_loss_kwh == pytest.approx(.3)


def test_curtailment_with_charge_cap():
    output = simulate(solar=9, max_charge_kw=1).intervals[0]
    assert output.battery_charge_input_kwh == pytest.approx(1)
    assert output.solar_curtailed_kwh == pytest.approx(8)


def test_battery_full_charge_cap():
    output = simulate(solar=9, initial_soc_fraction=.99).intervals[0]
    assert output.soc_end_fraction == pytest.approx(1)
    assert output.solar_curtailed_kwh > 0


def test_essential_priority_when_supply_short():
    output = simulate(essential=4, flexible=4, max_discharge_kw=1).intervals[0]
    assert output.served_essential_kwh == pytest.approx(1)
    assert output.served_flexible_kwh == 0
    assert output.unserved_essential_kwh == pytest.approx(3)
    assert output.unserved_flexible_kwh == pytest.approx(4)


def test_discharge_efficiency():
    output = simulate(essential=1).intervals[0]
    assert output.battery_discharge_output_kwh == pytest.approx(1)
    assert output.soc_end_fraction == pytest.approx(.375)
    assert output.battery_conversion_loss_kwh == pytest.approx(.25)


def test_reserve_never_crossed():
    output = simulate(essential=100).intervals[0]
    assert output.soc_end_fraction == pytest.approx(.2)
    assert output.unserved_essential_kwh > 0


def test_partial_interval_respects_inverter_power():
    output = simulate(essential=10, max_discharge_kw=1, duration=30).intervals[0]
    assert output.battery_discharge_output_kwh == pytest.approx(.5)


@pytest.mark.parametrize('name', scenario_names())
def test_synthetic_scenarios_conserve_energy(name):
    request = build_scenario(name)
    result = run_simulation(request)
    assert result.mode == 'simulation'
    assert result.summary.reserve_violations == 0
    assert result.summary.max_abs_balance_residual_kwh < 1e-8
    for item in result.intervals:
        assert request.grid.minimum_soc_fraction - 1e-8 <= item.soc_end_fraction <= 1 + 1e-8
        assert item.served_essential_kwh + item.unserved_essential_kwh == pytest.approx(item.essential_demand_kwh)
        assert item.served_flexible_kwh + item.unserved_flexible_kwh == pytest.approx(item.flexible_demand_kwh)
        assert not (item.battery_charge_input_kwh > 1e-8 and item.battery_discharge_output_kwh > 1e-8)
        h = item.duration_minutes / 60
        assert item.battery_charge_input_kwh <= request.grid.max_charge_kw * h + 1e-8
        assert item.battery_discharge_output_kwh <= request.grid.max_discharge_kw * h + 1e-8
        stored_delta = request.grid.battery_capacity_kwh * (item.soc_end_fraction - item.soc_start_fraction)
        assert stored_delta == pytest.approx(
            item.battery_charge_input_kwh * request.grid.charge_efficiency
            - item.battery_discharge_output_kwh / request.grid.discharge_efficiency,
            abs=1e-8,
        )
        if item.unserved_essential_kwh > 1e-8:
            assert item.served_flexible_kwh == 0


@pytest.mark.parametrize('name', scenario_names())
def test_run_is_deterministic(name):
    request = build_scenario(name)
    original = request.model_dump_json()
    assert run_simulation(request).model_dump_json() == run_simulation(request).model_dump_json()
    assert request.model_dump_json() == original


def test_night_reserve_reaches_shortfall():
    output = run_simulation(build_scenario('night_reserve'))
    assert output.summary.unserved_essential_kwh > 0


def test_invalid_initial_soc_rejected():
    with pytest.raises(ValidationError):
        cfg(initial_soc_fraction=.1, minimum_soc_fraction=.2)


@pytest.mark.parametrize('invalid', [float('inf'), float('nan'), -1])
def test_bad_generation_rejected(invalid):
    with pytest.raises(ValidationError):
        PowerInterval(timestamp=T, duration_minutes=60, solar_generation_kw=invalid,
                      essential_demand_kw=0, flexible_demand_kw=0)


def test_naive_time_rejected():
    with pytest.raises(ValidationError):
        PowerInterval(timestamp=T.replace(tzinfo=None), duration_minutes=60,
                      solar_generation_kw=0, essential_demand_kw=0, flexible_demand_kw=0)


def test_discontinuous_intervals_rejected():
    row = PowerInterval(timestamp=T, duration_minutes=60, solar_generation_kw=0,
                        essential_demand_kw=0, flexible_demand_kw=0)
    with pytest.raises(ValidationError):
        SimulationRequest(grid=cfg(), intervals=[row, row.model_copy(update={'timestamp': T + timedelta(hours=2)})])


def test_api_scenarios_and_unknown_scenario():
    client = TestClient(app)
    assert 'cloudy_school_day' in client.get('/sim/scenarios').json()
    output = client.get('/sim/scenarios/cloudy_school_day')
    assert output.status_code == 200
    assert output.json()['mode'] == 'simulation'
    assert client.get('/sim/scenarios/none').status_code == 404


def test_api_custom_and_no_act_route():
    client = TestClient(app)
    body = build_scenario('night_reserve').model_dump(mode='json')
    response = client.post('/sim/run', json=body)
    assert response.status_code == 200
    assert response.json()['summary']['unserved_essential_kwh'] > 0
    assert client.post('/sim/run', json={}).status_code == 422
    assert client.get('/act').status_code == 404


def test_health_still_returns_simulation():
    client = TestClient(app)
    assert client.get('/health').json()['data_mode'] == 'simulation'
