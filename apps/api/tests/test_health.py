from fastapi.testclient import TestClient

from lucia_api.main import app


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
