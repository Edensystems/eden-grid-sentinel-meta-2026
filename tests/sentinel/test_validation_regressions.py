"""Regression coverage for M0 contract validation, with no external services."""
from datetime import timedelta, timezone

import pytest
from pydantic import ValidationError

from eden.sentinel.schemas import (
    ApprovalEvent, ExecutionAuditEvent, ForecastEvent, ForecastPoint,
)
from test_schemas import NOW, recommendation, telemetry


def point(**overrides):
    values = dict(timestamp=NOW, predicted_solar_kw=1,
                  predicted_essential_demand_kw=1, predicted_flexible_demand_kw=0)
    return ForecastPoint(**(values | overrides))


def forecast(points):
    return ForecastEvent(event_id="f-1", site_id="school-1", created_at=NOW,
                         source="modeled", points=points)


@pytest.mark.parametrize("factory,fields", [
    (telemetry, ["event_id", "site_id"]),
    (recommendation, ["recommendation_id", "site_id", "reason"]),
    (lambda **kw: ForecastEvent(**(dict(event_id="f", site_id="s", created_at=NOW,
                                      source="modeled", points=[point()]) | kw)),
     ["event_id", "site_id"]),
    (lambda **kw: ApprovalEvent(**(dict(approval_id="a", recommendation_id="r",
                                       operator_id="operator", decision="approved", decided_at=NOW) | kw)),
     ["approval_id", "recommendation_id", "operator_id"]),
    (lambda **kw: ExecutionAuditEvent(**(dict(audit_id="a", recommendation_id="r",
        approval_id="p", occurred_at=NOW, status="applied", detail="simulation") | kw)),
     ["audit_id", "recommendation_id", "approval_id", "detail"]),
])
def test_strings_trimmed_and_blank_rejected(factory, fields):
    for field in fields:
        assert getattr(factory(**{field: " \tvalue\n "}), field) == "value"
        with pytest.raises(ValidationError):
            factory(**{field: " \t\r\n "})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("factory,field", [
    (telemetry, field) for field in (
        "solar_generation_kw", "essential_demand_kw", "flexible_demand_kw",
        "battery_soc_fraction", "battery_capacity_kwh")
] + [(point, field) for field in (
    "predicted_solar_kw", "predicted_essential_demand_kw", "predicted_flexible_demand_kw")
] + [(recommendation, "shift_energy_kwh")])
def test_all_float_fields_reject_nonfinite(factory, field, value):
    with pytest.raises(ValidationError):
        factory(**{field: value})
    item = factory()
    with pytest.raises(ValidationError):
        setattr(item, field, value)


def test_no_action_requires_zero_energy():
    assert recommendation(action="no_action", shift_energy_kwh=0).shift_energy_kwh == 0
    with pytest.raises(ValidationError, match="no_action requires zero"):
        recommendation(action="no_action", shift_energy_kwh=0.1)
    with pytest.raises(ValidationError, match="no_action requires zero"):
        recommendation().action = "no_action"
    item = recommendation(action="no_action", shift_energy_kwh=0)
    with pytest.raises(ValidationError, match="no_action requires zero"):
        item.shift_energy_kwh = 1


def test_literal_strings_are_trimmed_before_validation():
    assert telemetry(source=" simulated ", schema_version=" 1.0 ").source == "simulated"
    assert recommendation(action=" no_action ", shift_energy_kwh=0).action == "no_action"


@pytest.mark.parametrize("offset", [0, -1])
def test_forecasts_reject_duplicate_or_descending_times(offset):
    with pytest.raises(ValidationError, match="strictly increasing"):
        forecast([point(), point(timestamp=NOW + timedelta(hours=offset))])


def test_forecast_order_compares_instants_across_timezones():
    same_instant = NOW.astimezone(timezone(timedelta(hours=3)))
    with pytest.raises(ValidationError, match="strictly increasing"):
        forecast([point(), point(timestamp=same_instant)])
    item = forecast([point(), point(timestamp=same_instant + timedelta(hours=1))])
    assert len(item.points) == 2
    with pytest.raises(ValidationError, match="strictly increasing"):
        item.points = [point(), point()]


def test_forecast_requires_at_least_one_point():
    with pytest.raises(ValidationError):
        forecast([])
