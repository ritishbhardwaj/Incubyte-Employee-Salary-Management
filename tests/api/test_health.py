from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.db import build_engine, get_db
from app.main import app


def test_health_does_not_need_database(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_ok_when_migrated(client) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_503_when_schema_missing() -> None:
    engine = build_engine("sqlite://")
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as raw:
        response = raw.get("/ready")
    app.dependency_overrides.clear()
    engine.dispose()
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
