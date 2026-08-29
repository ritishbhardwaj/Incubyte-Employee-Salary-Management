from tests.conftest import employee_payload


def _seed_pay(client, auth_headers) -> None:
    people = [
        employee_payload(
            email="one@esmincubyte.example",
            first_name="One",
            country="United States",
            department="Engineering",
            job_level="IC3",
            hire_date="2019-01-01",
            compensation={
                "annual_salary": "100000",
                "currency": "USD",
                "effective_from": "2020-01-01",
                "reason": "Initial compensation",
            },
        ),
        employee_payload(
            email="two@esmincubyte.example",
            first_name="Two",
            country="India",
            department="Engineering",
            job_level="IC2",
            hire_date="2019-01-01",
            compensation={
                "annual_salary": "2000000",
                "currency": "INR",
                "effective_from": "2020-01-01",
                "reason": "Initial compensation",
            },
        ),
        employee_payload(
            email="gone@esmincubyte.example",
            first_name="Gone",
            employment_status="TERMINATED",
            hire_date="2019-01-01",
            compensation={
                "annual_salary": "300000",
                "currency": "USD",
                "effective_from": "2020-01-01",
                "reason": "Initial compensation",
            },
        ),
    ]
    for payload in people:
        assert (
            client.post("/api/v1/employees", json=payload, headers=auth_headers).status_code == 201
        )


def test_summary_portable_aggregates(client, auth_headers) -> None:
    _seed_pay(client, auth_headers)
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["active_headcount"] == 2
    # 100000 USD + 2000000 INR * 0.012 = 24000 -> 124000
    assert body["total_annual_payroll_usd"] == "124000.00"
    assert body["average_salary_usd"] == "62000.00"
    # SQLite does not run percentile_cont. Do not assert a fake median.
    assert body["percentiles"]["dialect"] == "sqlite"
    assert body["percentiles"]["source"] == "postgresql_percentile_cont_only"
    assert body["percentiles"]["p50"] is None


def test_breakdowns_and_distribution(client, auth_headers) -> None:
    _seed_pay(client, auth_headers)
    breakdowns = client.get("/api/v1/analytics/breakdowns").json()
    countries = {row["key"]: row["headcount"] for row in breakdowns["country"]}
    assert countries["United States"] == 1
    assert countries["India"] == 1

    buckets = client.get("/api/v1/analytics/distribution").json()
    counted = {row["label"]: row["headcount"] for row in buckets}
    assert counted["0-40k"] == 1
    assert counted["100-130k"] == 1


def test_recent_changes_excludes_seed_reason(client, auth_headers) -> None:
    created = client.post("/api/v1/employees", json=employee_payload(), headers=auth_headers)
    employee_id = created.json()["id"]
    client.post(
        f"/api/v1/employees/{employee_id}/compensation",
        json={"annual_salary": "95000", "reason": "Promotion", "effective_from": "2024-01-01"},
        headers=auth_headers,
    )
    changes = client.get("/api/v1/analytics/recent-changes").json()
    assert changes
    assert all(item["reason"] != "Seed" for item in changes)
    assert any(item["reason"] == "Promotion" for item in changes)
