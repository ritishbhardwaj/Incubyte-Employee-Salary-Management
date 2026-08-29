from app.core.config import get_settings


def test_login_sets_http_only_session_cookie(client) -> None:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.hr_email, "password": settings.hr_password},
    )
    assert response.status_code == 200
    assert response.json()["email"] == settings.hr_email
    assert settings.session_cookie_name in response.cookies
    assert settings.csrf_cookie_name in response.cookies
    header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in header or "httponly" in header.lower()


def test_login_rejects_bad_password(client) -> None:
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.hr_email, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_me_requires_session(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_session(client, auth_headers) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200


def test_logout_revokes_and_requires_csrf(client, auth_headers) -> None:
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_mutation_without_csrf_is_forbidden(client, auth_headers) -> None:
    response = client.post("/api/v1/auth/logout", headers={"Origin": "http://testserver"})
    assert response.status_code == 403


def test_mutation_with_bad_origin_is_forbidden(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "https://evil.example", "X-CSRF-Token": auth_headers["X-CSRF-Token"]},
    )
    assert response.status_code == 403
