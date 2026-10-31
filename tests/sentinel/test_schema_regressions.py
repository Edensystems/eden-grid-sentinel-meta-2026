"""M0 typed event-schema gap regression coverage."""
from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from eden.sentinel.schemas import ApprovalEvent, ForecastEvent, ForecastPoint, RecommendationEvent

T = datetime(2026, 10, 28, tzinfo=timezone.utc)


def test_blank_operator_rejected():
    with pytest.raises(ValidationError):
        ApprovalEvent(approval_id='a', recommendation_id='r', operator_id='   ',
                      decision='approved', decided_at=T)


def test_no_action_with_shift_rejected():
    with pytest.raises(ValidationError):
        RecommendationEvent(recommendation_id='r', site_id='s', created_at=T,
                            action='no_action', shift_energy_kwh=5, reason='none')


def test_valid_no_action():
    obj = RecommendationEvent(recommendation_id='r', site_id='s', created_at=T,
                              action='no_action', shift_energy_kwh=0, reason='none')
    assert obj.shift_energy_kwh == 0


def test_forecast_times_must_increase():
    row = ForecastPoint(timestamp=T, predicted_solar_kw=0,
                        predicted_essential_demand_kw=0, predicted_flexible_demand_kw=0)
    for next_time in (T, T - timedelta(minutes=1)):
        with pytest.raises(ValidationError):
            ForecastEvent(event_id='f', site_id='s', created_at=T,
                          source='simulated', points=[row, row.model_copy(update={'timestamp': next_time})])


def test_infinite_forecast_rejected():
    with pytest.raises(ValidationError):
        ForecastPoint(timestamp=T, predicted_solar_kw=float('inf'),
                      predicted_essential_demand_kw=0, predicted_flexible_demand_kw=0)
