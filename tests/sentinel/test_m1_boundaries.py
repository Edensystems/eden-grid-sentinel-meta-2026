"""M1 time-boundary and API validation regression tests."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from eden.sentinel.api import app
from eden.sentinel.scenarios import build_scenario
from eden.sentinel.twin import SimulationRequest


def test_contiguous_intervals_cross_dst_by_elapsed_time():
    body = build_scenario('night_reserve').model_dump(mode='python')
    # The clock repeats 01:00 at the fall-back transition; elapsed time still increases.
    start = datetime(2026, 11, 1, 5, tzinfo=timezone.utc)
    for index, row in enumerate(body['intervals']):
        row['timestamp'] = (start + timedelta(hours=index)).astimezone(ZoneInfo('America/New_York'))
    assert len(SimulationRequest.model_validate(body).intervals) == 4
    body['intervals'][1]['timestamp'] = body['intervals'][0]['timestamp']
    with pytest.raises(ValidationError, match='contiguous'):
        SimulationRequest.model_validate(body)


@pytest.mark.parametrize('duration', [0, 121, 1.5])
def test_api_rejects_invalid_interval_duration(duration):
    body = build_scenario('night_reserve').model_dump(mode='json')
    body['intervals'][0]['duration_minutes'] = duration
    assert TestClient(app).post('/sim/run', json=body).status_code == 422


def test_api_rejects_excessive_horizon():
    body = build_scenario('night_reserve').model_dump(mode='json')
    body['intervals'] = body['intervals'][:1] * 337
    assert TestClient(app).post('/sim/run', json=body).status_code == 422
