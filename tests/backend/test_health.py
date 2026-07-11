from fastapi.testclient import TestClient

from packstudio.api.app import app


def test_health_endpoint_reports_ready_service() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "packstudio"}
