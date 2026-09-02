from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import CompensationRecord, Employee, User  # noqa: F401
from app.database.session import Base, build_engine, get_db
from app.main import app
from app.services.auth import ensure_hr_user

ORIGIN = "http://testserver"


@pytest.fixture
def engine():
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    ensure_hr_user(session)
    session.commit()
    yield session
    session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.hr_email, "password": settings.hr_password},
    )
    assert response.status_code == 200, response.text
    csrf = response.cookies.get(settings.csrf_cookie_name)
    assert csrf
    return {"X-CSRF-Token": csrf, "Origin": ORIGIN}


def employee_payload(**overrides: object) -> dict:
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada.lovelace@esmincubyte.example",
        "country": "United Kingdom",
        "city": "London",
        "department": "Engineering",
        "job_title": "Software Engineer III",
        "job_level": "IC3",
        "employment_status": "ACTIVE",
        "hire_date": "2020-01-15",
        "compensation": {
            "annual_salary": "90000",
            "currency": "GBP",
            "effective_from": "2020-01-15",
            "reason": "Initial compensation",
        },
    }
    body.update(overrides)
    return body
