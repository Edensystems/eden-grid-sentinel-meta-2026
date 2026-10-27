"""M0 data contracts only. Business logic starts in later milestones.

Units: power in kW, energy in kWh, battery SOC as a fraction in [0,1].
Timestamp fields require timezone-aware ISO 8601 datetimes.
"""
from datetime import datetime
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class HealthResponse(StrictSchema):
    status: Literal["ok"]
    service: Literal["eden-grid-sentinel"]
    phase: Literal["M0"]
    data_mode: Literal["simulation"]


class TelemetryEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    observed_at: AwareDatetime
    source: Literal["simulated", "measured"]
    solar_generation_kw: float = Field(ge=0)
    essential_demand_kw: float = Field(ge=0)
    flexible_demand_kw: float = Field(ge=0)
    battery_soc_fraction: float = Field(ge=0, le=1)
    battery_capacity_kwh: float = Field(gt=0)


class ForecastPoint(StrictSchema):
    timestamp: AwareDatetime
    predicted_solar_kw: float = Field(ge=0)
    predicted_essential_demand_kw: float = Field(ge=0)
    predicted_flexible_demand_kw: float = Field(ge=0)


class ForecastEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    created_at: AwareDatetime
    source: Literal["simulated", "measured", "modeled"]
    points: list[ForecastPoint] = Field(min_length=1)


class RecommendationEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    recommendation_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    created_at: AwareDatetime
    action: Literal["shift_flexible_load", "no_action"]
    shift_energy_kwh: float = Field(ge=0)
    reason: str = Field(min_length=1)
    approval_required: Literal[True] = True


class ApprovalEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    approval_id: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    decision: Literal["approved", "rejected"]
    decided_at: AwareDatetime


class ExecutionAuditEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    audit_id: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)
    approval_id: str = Field(min_length=1)
    occurred_at: AwareDatetime
    mode: Literal["simulation"] = "simulation"
    status: Literal["applied", "rejected", "failed"]
    detail: str = Field(min_length=1)
