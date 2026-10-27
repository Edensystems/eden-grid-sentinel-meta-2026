from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from eden.sentinel.schemas import (
    TelemetryEvent, ForecastPoint, RecommendationEvent,
    ApprovalEvent, ExecutionAuditEvent,
)

NOW = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


def telemetry(**overrides):
    values = dict(
        event_id="t-1", site_id="school-1", observed_at=NOW,
        source="simulated", solar_generation_kw=2.0,
        essential_demand_kw=1.0, flexible_demand_kw=0.5,
        battery_soc_fraction=0.42, battery_capacity_kwh=10.0,
    )
    values.update(overrides)
    return TelemetryEvent(**values)


def recommendation(**overrides):
    values = dict(
        recommendation_id="r-1", site_id="school-1", created_at=NOW,
        action="shift_flexible_load", shift_energy_kwh=1.0,
        reason="Protect critical loads",
    )
    values.update(overrides)
    return RecommendationEvent(**values)


def test_simulated_telemetry_is_explicitly_labeled():
    item = telemetry()
    assert item.source == "simulated"
    assert item.battery_soc_fraction == 0.42


@pytest.mark.parametrize("soc", [-0.01, 1.01])
def test_soc_outside_bounds_rejected(soc):
    with pytest.raises(ValidationError):
        telemetry(battery_soc_fraction=soc)


@pytest.mark.parametrize("field", ["solar_generation_kw", "essential_demand_kw", "flexible_demand_kw"])
def test_negative_power_rejected(field):
    with pytest.raises(ValidationError):
        telemetry(**{field: -1.0})


def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError):
        telemetry(observed_at=datetime(2026, 10, 27, 14))


def test_extra_fields_rejected():
    with pytest.raises(ValidationError):
        telemetry(unapproved_command="energize_relay")


def test_forecast_rejects_negative_power():
    with pytest.raises(ValidationError):
        ForecastPoint(timestamp=NOW, predicted_solar_kw=-0.1,
            predicted_essential_demand_kw=1, predicted_flexible_demand_kw=1)


def test_recommendation_requires_approval():
    assert recommendation().approval_required is True
    with pytest.raises(ValidationError):
        recommendation(approval_required=False)


def test_approval_requires_operator_identity():
    with pytest.raises(ValidationError):
        ApprovalEvent(approval_id="a-1", recommendation_id="r-1",
            operator_id="", decision="approved", decided_at=NOW)


def test_audit_cannot_claim_hardware_execution():
    with pytest.raises(ValidationError):
        ExecutionAuditEvent(audit_id="au-1", recommendation_id="r-1",
            approval_id="a-1", occurred_at=NOW, mode="hardware",
            status="applied", detail="would be unsafe")


def test_audit_simulation_valid():
    result = ExecutionAuditEvent(audit_id="au-1", recommendation_id="r-1",
        approval_id="a-1", occurred_at=NOW,
        status="applied", detail="sandbox simulation event")
    assert result.mode == "simulation"
