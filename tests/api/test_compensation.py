from tests.conftest import employee_payload


def test_adjust_compensation_keeps_history(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    employee_id = created.json()["id"]
    original = created.json()["current_compensation"]["annual_salary"]

    adjusted = client.post(
        f"/api/v1/employees/{employee_id}/compensation",
        json={
            "annual_salary": "110000",
            "currency": "GBP",
            "effective_from": "2024-06-01",
            "reason": "Promotion",
        },
        headers=auth_headers,
    )
    assert adjusted.status_code == 200, adjusted.text
    assert adjusted.json()["annual_salary"] == "110000.00"
    assert adjusted.json()["effective_to"] is None

    history = client.get(f"/api/v1/employees/{employee_id}/compensation")
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) == 2
    current = next(item for item in rows if item["effective_to"] is None)
    closed = next(item for item in rows if item["effective_to"] is not None)
    assert current["annual_salary"] == "110000.00"
    assert closed["annual_salary"] == original
    assert closed["effective_to"] == "2024-06-01"


def test_adjust_requires_reason(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    employee_id = created.json()["id"]
    response = client.post(
        f"/api/v1/employees/{employee_id}/compensation",
        json={"annual_salary": "110000", "reason": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_future_effective_from_rejected(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    employee_id = created.json()["id"]
    response = client.post(
        f"/api/v1/employees/{employee_id}/compensation",
        json={
            "annual_salary": "110000",
            "effective_from": "2099-01-01",
            "reason": "Scheduled raise",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
