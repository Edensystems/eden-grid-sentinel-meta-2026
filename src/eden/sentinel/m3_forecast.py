"""M3: deterministic previous-day analogue forecast, explicitly non-ML.

No target telemetry is inspected while creating predictions; actual target observations
are used only AFTER forecasting for offline evaluation and error metrics.
"""
from datetime import timedelta, timezone
from typing import Literal

from pydantic import AwareDatetime, Field
from eden.sentinel.twin import SimulationRequest, TwinModel


class ForecastStep(TwinModel):
    timestamp: AwareDatetime
    solar_kw: float = Field(ge=0)
    essential_kw: float = Field(ge=0)
    flexible_kw: float = Field(ge=0)


class ForecastMetrics(TwinModel):
    solar_mae_kw: float = Field(ge=0)
    essential_mae_kw: float = Field(ge=0)
    flexible_mae_kw: float = Field(ge=0)
    sample_count: int = Field(ge=1)


class ForecastEvaluation(TwinModel):
    data_mode: Literal["simulation"] = "simulation"
    method: Literal["previous_day_analogue"] = "previous_day_analogue"
    description: str
    forecasts: list[ForecastStep]
    metrics: ForecastMetrics


def previous_day_forecast(reference: SimulationRequest, target: SimulationRequest) -> ForecastEvaluation:
    """Predict using previous-day same-index power; score against held-out synthetic target.

    Caller must supply reference and target from separate, contiguous date windows.
    Strict UTC 24-hour separation for every timestamp prevents same-day lookahead.
    """
    if reference.grid.site_id != target.grid.site_id:
        raise ValueError("reference and target must refer to the same site")
    if len(reference.intervals) != len(target.intervals):
        raise ValueError("reference and target must have identical horizon length")
    preds: list[ForecastStep] = []
    solar_err = critical_err = flexible_err = 0.0
    for historical, observed in zip(reference.intervals, target.intervals):
        delta = observed.timestamp.astimezone(timezone.utc) - historical.timestamp.astimezone(timezone.utc)
        if delta != timedelta(days=1):
            raise ValueError("each historical reference sample must be exactly 24 hours earlier")
        if historical.duration_minutes != observed.duration_minutes:
            raise ValueError("reference and target intervals must have equal durations")
        preds.append(ForecastStep(
            timestamp=observed.timestamp, solar_kw=historical.solar_generation_kw,
            essential_kw=historical.essential_demand_kw,
            flexible_kw=historical.flexible_demand_kw,
        ))
        solar_err += abs(historical.solar_generation_kw - observed.solar_generation_kw)
        critical_err += abs(historical.essential_demand_kw - observed.essential_demand_kw)
        flexible_err += abs(historical.flexible_demand_kw - observed.flexible_demand_kw)
    n = len(preds)
    return ForecastEvaluation(
        description="Naive prior-day synthetic analogue, not a learned or weather-aware model; scoring is held-out and retrospective.",
        forecasts=preds,
        metrics=ForecastMetrics(solar_mae_kw=solar_err / n,
                                essential_mae_kw=critical_err / n,
                                flexible_mae_kw=flexible_err / n,
                                sample_count=n),
    )
