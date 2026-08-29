from tests.conftest import employee_payload


def test_employees_require_auth(client) -> None:
    response = client.get("/api/v1/employees")
    assert response.status_code == 401


def test_create_list_get_patch_employee(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["employee_code"].startswith("ACME-")
    assert body["current_compensation"]["currency"] == "GBP"
    assert body["current_compensation"]["annual_salary_usd"]
    employee_id = body["id"]

    listed = client.get("/api/v1/employees?q=Ada")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == employee_id

    fetched = client.get(f"/api/v1/employees/{employee_id}")
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "ada.lovelace@acme.example"

    patched = client.patch(
        f"/api/v1/employees/{employee_id}",
        json={"employment_status": "ON_LEAVE", "city": "Manchester"},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["employment_status"] == "ON_LEAVE"
    assert patched.json()["city"] == "Manchester"
    assert patched.json()["current_compensation"]["annual_salary"] == "90000.00"


def test_duplicate_email_conflicts(client, auth_headers) -> None:
    first = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    assert second.status_code == 409


def test_pagination_and_filter(client, auth_headers) -> None:
    for i in range(3):
        payload = employee_payload(
            email=f"eng{i}@acme.example",
            department="Engineering",
            first_name=f"Eng{i}",
        )
        assert (
            client.post("/api/v1/employees", json=payload, headers=auth_headers).status_code == 201
        )
    payload = employee_payload(
        email="sales@acme.example",
        department="Sales",
        first_name="Sal",
        last_name="Person",
    )
    assert client.post("/api/v1/employees", json=payload, headers=auth_headers).status_code == 201

    page = client.get("/api/v1/employees?department=Engineering&page=1&page_size=2")
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 2


def test_no_hard_delete_route(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    employee_id = created.json()["id"]
    deleted = client.delete(f"/api/v1/employees/{employee_id}", headers=auth_headers)
    assert deleted.status_code == 405
