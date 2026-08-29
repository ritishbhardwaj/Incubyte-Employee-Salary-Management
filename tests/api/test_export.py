from tests.conftest import employee_payload


def test_csv_export_uses_filters(client, auth_headers) -> None:
    client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    client.post(
        "/api/v1/employees",
        json=employee_payload(
            email="other@esmincubyte.example",
            first_name="Other",
            department="Sales",
        ),
        headers=auth_headers,
    )
    response = client.get("/api/v1/exports/employees.csv?department=Engineering")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    lines = response.text.strip().splitlines()
    assert lines[0].startswith("employee_code")
    assert len(lines) == 2
    assert "Engineering" in lines[1]
    assert "Sales" not in response.text
