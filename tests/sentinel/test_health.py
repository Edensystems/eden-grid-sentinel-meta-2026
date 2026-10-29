from fastapi.testclient import TestClient
from eden.sentinel.api import app


def test_health_ok():
    result = TestClient(app).get('/health')
    assert result.status_code == 200
    assert result.json() == {
        'status': 'ok', 'service': 'eden-grid-sentinel',
        'phase': 'M0', 'data_mode': 'simulation',
    }


def test_m1_routes_are_simulation_only():
    paths = set(TestClient(app).get('/openapi.json').json()['paths'])
    assert paths == {'/health', '/sim/scenarios', '/sim/scenarios/{name}', '/sim/run'}
    assert not any('act' in path or 'control' in path for path in paths)
