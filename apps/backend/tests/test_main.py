from fastapi.testclient import TestClient

from achiwave_backend.config import Settings
from achiwave_backend.main import create_app


def test_service_metadata() -> None:
    settings = Settings(_env_file=None, app_environment="test")

    with TestClient(create_app(settings)) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "achiwave-backend",
        "environment": "test",
        "status": "ok",
    }
