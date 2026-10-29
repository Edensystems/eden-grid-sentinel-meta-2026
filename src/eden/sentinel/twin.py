"""M1 pure, deterministic solar-battery digital twin (synthetic only).

Units: power kW, energy kWh, state of charge in [0,1]. No hardware/cloud I/O.
"""
from datetime import timedelta, timezone
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from eden.sentinel.schemas import StrictSchema


class TwinModel(StrictSchema):
    """Use the same validation rules as the remediated M0 contracts."""


class GridParameters(TwinModel):
    site_id: str = Field(min_length=1)
    battery_capacity_kwh: float = Field(gt=0)
    initial_soc_fraction: float = Field(ge=0, le=1)
    minimum_soc_fraction: float = Field(ge=0, le=1)
    max_charge_kw: float = Field(ge=0)
    max_discharge_kw: float = Field(ge=0)
    charge_efficiency: float = Field(gt=0, le=1)
    discharge_efficiency: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def reserve_is_valid(self):
        if self.initial_soc_fraction < self.minimum_soc_fraction:
            raise ValueError("initial battery SOC must be at or above minimum SOC")
        return self


class PowerInterval(TwinModel):
    timestamp: AwareDatetime
    duration_minutes: int = Field(gt=0, le=120)
    solar_generation_kw: float = Field(ge=0)
    essential_demand_kw: float = Field(ge=0)
    flexible_demand_kw: float = Field(ge=0)


class SimulationRequest(TwinModel):
    schema_version: Literal["1.0"] = "1.0"
    grid: GridParameters
    intervals: list[PowerInterval] = Field(min_length=1, max_length=336)

    @model_validator(mode="after")
    def contiguous_intervals(self):
        for previous, current in zip(self.intervals, self.intervals[1:]):
            expected = previous.timestamp.astimezone(timezone.utc) + timedelta(minutes=previous.duration_minutes)
            if current.timestamp.astimezone(timezone.utc) != expected:
                raise ValueError("interval timestamps must be contiguous and chronological")
        return self


class IntervalResult(TwinModel):
    timestamp: AwareDatetime
    duration_minutes: int
    solar_generation_kwh: float
    essential_demand_kwh: float
    flexible_demand_kwh: float
    served_essential_kwh: float
    served_flexible_kwh: float
    unserved_essential_kwh: float
    unserved_flexible_kwh: float
    battery_charge_input_kwh: float
    battery_discharge_output_kwh: float
    battery_conversion_loss_kwh: float
    solar_curtailed_kwh: float
    soc_start_fraction: float
    soc_end_fraction: float
    energy_balance_residual_kwh: float


class SimulationSummary(TwinModel):
    generated_solar_kwh: float
    essential_demand_kwh: float
    flexible_demand_kwh: float
    served_essential_kwh: float
    served_flexible_kwh: float
    unserved_essential_kwh: float
    unserved_flexible_kwh: float
    charged_input_kwh: float
    discharged_output_kwh: float
    battery_conversion_loss_kwh: float
    curtailed_solar_kwh: float
    reserve_violations: int
    max_abs_balance_residual_kwh: float
    final_soc_fraction: float


class SimulationResult(TwinModel):
    mode: Literal["simulation"] = "simulation"
    policy: Literal["essential_first_baseline"] = "essential_first_baseline"
    site_id: str
    intervals: list[IntervalResult]
    summary: SimulationSummary


def run_simulation(request: SimulationRequest) -> SimulationResult:
    """Serve essential then flexible loads; solar first, battery second.

    The policy is deliberately NOT optimization. All requests are independent.
    """
    cfg = request.grid
    stored_kwh = cfg.battery_capacity_kwh * cfg.initial_soc_fraction
    reserve_kwh = cfg.battery_capacity_kwh * cfg.minimum_soc_fraction
    output: list[IntervalResult] = []
    epsilon = 1e-8

    for row in request.intervals:
        h = row.duration_minutes / 60.0
        pv = row.solar_generation_kw * h
        essential = row.essential_demand_kw * h
        flexible = row.flexible_demand_kw * h
        initial_stored = stored_kwh

        pv_essential = min(essential, pv)
        pv_flexible = min(flexible, pv - pv_essential)
        remaining_essential = essential - pv_essential
        remaining_flexible = flexible - pv_flexible

        max_battery_output = min(
            max(0.0, stored_kwh - reserve_kwh) * cfg.discharge_efficiency,
            cfg.max_discharge_kw * h,
        )
        battery_essential = min(remaining_essential, max_battery_output)
        battery_flexible = min(remaining_flexible, max_battery_output - battery_essential)
        battery_output = battery_essential + battery_flexible
        stored_kwh -= battery_output / cfg.discharge_efficiency
        served_essential = pv_essential + battery_essential
        served_flexible = pv_flexible + battery_flexible

        excess_pv = pv - pv_essential - pv_flexible
        free_capacity = max(0.0, cfg.battery_capacity_kwh - stored_kwh)
        charge_input = min(
            excess_pv, cfg.max_charge_kw * h,
            free_capacity / cfg.charge_efficiency,
        )
        stored_kwh += charge_input * cfg.charge_efficiency
        curtailed = excess_pv - charge_input

        battery_loss = (
            charge_input * (1 - cfg.charge_efficiency)
            + battery_output * (1 / cfg.discharge_efficiency - 1)
        )
        residual = (pv + battery_output - served_essential
                    - served_flexible - charge_input - curtailed)
        storage_expected = (initial_stored + charge_input * cfg.charge_efficiency
                            - battery_output / cfg.discharge_efficiency)
        if not reserve_kwh - epsilon <= stored_kwh <= cfg.battery_capacity_kwh + epsilon:
            raise ArithmeticError("battery SOC invariant violated")
        if abs(residual) > epsilon or abs(stored_kwh - storage_expected) > epsilon:
            raise ArithmeticError("energy conservation invariant violated")
        if charge_input > epsilon and battery_output > epsilon:
            raise ArithmeticError("simultaneous battery charge and discharge")

        output.append(IntervalResult(
            timestamp=row.timestamp, duration_minutes=row.duration_minutes,
            solar_generation_kwh=pv, essential_demand_kwh=essential,
            flexible_demand_kwh=flexible,
            served_essential_kwh=served_essential, served_flexible_kwh=served_flexible,
            unserved_essential_kwh=max(0.0, essential - served_essential),
            unserved_flexible_kwh=max(0.0, flexible - served_flexible),
            battery_charge_input_kwh=charge_input,
            battery_discharge_output_kwh=battery_output,
            battery_conversion_loss_kwh=battery_loss,
            solar_curtailed_kwh=curtailed,
            soc_start_fraction=initial_stored / cfg.battery_capacity_kwh,
            soc_end_fraction=stored_kwh / cfg.battery_capacity_kwh,
            energy_balance_residual_kwh=residual,
        ))

    def total(name: str) -> float:
        return sum(getattr(item, name) for item in output)

    summary = SimulationSummary(
        generated_solar_kwh=total("solar_generation_kwh"),
        essential_demand_kwh=total("essential_demand_kwh"),
        flexible_demand_kwh=total("flexible_demand_kwh"),
        served_essential_kwh=total("served_essential_kwh"),
        served_flexible_kwh=total("served_flexible_kwh"),
        unserved_essential_kwh=total("unserved_essential_kwh"),
        unserved_flexible_kwh=total("unserved_flexible_kwh"),
        charged_input_kwh=total("battery_charge_input_kwh"),
        discharged_output_kwh=total("battery_discharge_output_kwh"),
        battery_conversion_loss_kwh=total("battery_conversion_loss_kwh"),
        curtailed_solar_kwh=total("solar_curtailed_kwh"),
        reserve_violations=sum(item.soc_end_fraction < cfg.minimum_soc_fraction - epsilon
                               for item in output),
        max_abs_balance_residual_kwh=max(abs(item.energy_balance_residual_kwh)
                                         for item in output),
        final_soc_fraction=output[-1].soc_end_fraction,
    )
    return SimulationResult(site_id=cfg.site_id, intervals=output, summary=summary)
