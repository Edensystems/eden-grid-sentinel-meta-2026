"""Fixed synthetic solar-school scenarios. Never represent as field measurements."""
from datetime import datetime, timedelta, timezone
from eden.sentinel.twin import GridParameters, PowerInterval, SimulationRequest

START = datetime(2026, 10, 28, 7, 0, tzinfo=timezone.utc)
PROFILES = {
    "cloudy_school_day": (
        [2.8, 3.1, 1.4, 0.6, 0.0, 0.0, 0.0],
        [1.2] * 7,
        [0.8, 1.0, 0.6, 0.6, 0.5, 0.3, 0.3],
        dict(battery_capacity_kwh=5.0, initial_soc_fraction=0.55,
             minimum_soc_fraction=0.2, max_charge_kw=2.0,
             max_discharge_kw=2.0, charge_efficiency=0.94,
             discharge_efficiency=0.9),
    ),
    "night_reserve": (
        [0.0] * 4, [1.2] * 4, [0.5] * 4,
        dict(battery_capacity_kwh=2.0, initial_soc_fraction=0.6,
             minimum_soc_fraction=0.2, max_charge_kw=1.0,
             max_discharge_kw=1.0, charge_efficiency=0.95,
             discharge_efficiency=0.9),
    ),
    "sunny_surplus": (
        [3.0] * 4, [1.0] * 4, [0.5] * 4,
        dict(battery_capacity_kwh=4.0, initial_soc_fraction=0.5,
             minimum_soc_fraction=0.2, max_charge_kw=1.0,
             max_discharge_kw=1.0, charge_efficiency=0.95,
             discharge_efficiency=0.9),
    ),
}


def scenario_names() -> list[str]:
    return sorted(PROFILES)


def build_scenario(name: str) -> SimulationRequest:
    if name not in PROFILES:
        raise KeyError(name)
    solar, essential, flexible, battery = PROFILES[name]
    return SimulationRequest(
        grid=GridParameters(site_id="school-demo-001", **battery),
        intervals=[PowerInterval(
            timestamp=START + timedelta(hours=i), duration_minutes=60,
            solar_generation_kw=pv, essential_demand_kw=critical,
            flexible_demand_kw=optional,
        ) for i, (pv, critical, optional) in
            enumerate(zip(solar, essential, flexible))],
    )
