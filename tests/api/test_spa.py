from fastapi.testclient import TestClient

from app.main import FRONTEND_DIST, app


def test_root_is_the_spa_not_openapi() -> None:
    if not FRONTEND_DIST.is_dir():
        return
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<title>IncubyteESM</title>" in response.text
    assert "openapi" not in response.text.lower()
