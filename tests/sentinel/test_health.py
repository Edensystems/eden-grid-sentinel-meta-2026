from fastapi.testclient import TestClient
from eden.sentinel.api import app


def test_health_ok():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "service": "eden-grid-sentinel",
        "phase": "M0", "data_mode": "simulation",
    }


def test_only_system_route_and_docs_exist():
    paths = set(TestClient(app).get("/openapi.json").json()["paths"])
    assert paths == {"/health"}