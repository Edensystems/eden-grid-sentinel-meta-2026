"""M0 data contracts only. Business logic starts in later milestones.

Units: power in kW, energy in kWh, battery SOC as a fraction in [0,1].
Timestamp fields require timezone-aware ISO 8601 datetimes.
"""
from datetime import timezone
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True,
        str_strip_whitespace=True, allow_inf_nan=False,
    )

    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, value):
        # ConfigDict strips str fields; Literal[str] also needs normalization.
        return value.strip() if isinstance(value, str) else value


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

    @model_validator(mode="after")
    def require_increasing_timestamps(self):
        if any(
            a.timestamp.astimezone(timezone.utc) >= b.timestamp.astimezone(timezone.utc)
            for a, b in zip(self.points, self.points[1:])
        ):
            raise ValueError("forecast timestamps must be strictly increasing")
        return self


class RecommendationEvent(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"
    recommendation_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    created_at: AwareDatetime
    action: Literal["shift_flexible_load", "no_action"]
    shift_energy_kwh: float = Field(ge=0)
    reason: str = Field(min_length=1)
    approval_required: Literal[True] = True

    @model_validator(mode="after")
    def require_zero_energy_for_no_action(self):
        if self.action == "no_action" and self.shift_energy_kwh != 0:
            raise ValueError("no_action requires zero shift_energy_kwh")
        return self


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
