"""M5 staging ASGI gateway is GET-only, simulation-only and free of M4 routes."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
from eden.sentinel.m5_readonly import app

client = TestClient(app)


def test_preview_health_declares_read_only():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == dict(status='ok', service='eden-grid-sentinel',
                                   phase='M5_PREVIEW', data_mode='simulation',
                                   control_mode='read_only')


def test_preview_only_exposes_allowlisted_get_routes():
    schema = client.get('/openapi.json').json()
    assert set(schema['paths']) == {'/health', '/m3/scenarios', '/m3/evaluate/{scenario}'}
    assert all(set(operations) == {'get'} for operations in schema['paths'].values())
    for route in ('/m4/proposals', '/act', '/pubsub/act', '/sim/run'):
        assert client.post(route, json={}).status_code == 404
    assert client.post('/m3/evaluate/cloudy_school_day', json={}).status_code == 405


def test_preview_produces_real_comparison_without_side_effects():
    names = client.get('/m3/scenarios').json()
    assert 'cloudy_school_day' in names
    for name in names:
        payload = client.get(f'/m3/evaluate/{name}').json()
        assert payload['mode'] == 'simulation'
        assert payload['scenario'] == name
        assert payload['forecast']['method'] == 'previous_day_analogue'
        assert payload['realized']['battery_reserve_violations'] == 0
        assert payload['realized']['max_abs_bus_residual_kwh'] < 1e-8
        assert client.get(f'/m3/evaluate/{name}').json() == payload


def test_unknown_preview_scenario_returns_404():
    assert client.get('/m3/evaluate/not-real').status_code == 404


def _assert_same_payload(live, recorded, path):
    """Exact structure, strings and ints; floats to 1e-9 because Python 3.12's
    compensated float sum() differs from 3.11 in the last bit (~1e-15 kWh)."""
    if isinstance(recorded, dict):
        assert isinstance(live, dict) and live.keys() == recorded.keys(), path
        for key in recorded:
            _assert_same_payload(live[key], recorded[key], f'{path}.{key}')
    elif isinstance(recorded, list):
        assert isinstance(live, list) and len(live) == len(recorded), path
        for index, (a, b) in enumerate(zip(live, recorded)):
            _assert_same_payload(a, b, f'{path}[{index}]')
    elif isinstance(recorded, float) and not isinstance(recorded, bool):
        assert isinstance(live, (int, float)) and abs(live - recorded) <= 1e-9, path
    else:
        assert live == recorded and type(live) is type(recorded), path


def test_frontend_contract_fixture_matches_live_backend():
    """The control-room contract tests use this fixture as 'real M3 output'; keep it honest."""
    fixture_path = (Path(__file__).resolve().parents[2] / 'apps' / 'control-room'
                    / 'tests' / 'fixtures' / 'synthetic_m3_results.json')
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    assert sorted(fixture) == sorted(client.get('/m3/scenarios').json())
    for name, recorded in fixture.items():
        _assert_same_payload(client.get(f'/m3/evaluate/{name}').json(), recorded, name)
