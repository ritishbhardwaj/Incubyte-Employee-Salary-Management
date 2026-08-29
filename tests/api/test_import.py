HEADER = (
    "first_name,last_name,email,country,city,department,job_title,"
    "job_level,employment_status,hire_date,annual_salary,currency"
)
CSV = f"""{HEADER}
Good,Row,good.row@esmincubyte.example,United States,Austin,Engineering,Engineer,IC2,ACTIVE,2022-01-01,90000,USD
Bad,Row,bad.row@esmincubyte.example,United States,Austin,Engineering,Engineer,IC2,ACTIVE,2022-01-01,-5,USD
Dup,Mail,good.row@esmincubyte.example,United States,Austin,Engineering,Engineer,IC2,ACTIVE,2022-01-01,90000,USD
"""


def test_import_reports_row_errors_and_writes_valid_rows(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/imports/employees",
        files={"file": ("people.csv", CSV, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 1
    assert body["total_rows"] == 3
    reasons = {item["row"]: item["errors"] for item in body["failed"]}
    assert 3 in reasons
    assert 4 in reasons
    listed = client.get("/api/v1/employees?q=good.row")
    assert listed.json()["total"] == 1


def test_import_rejects_xlsx(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/imports/employees",
        files={"file": ("people.xlsx", b"not-a-real-xlsx", "application/vnd.ms-excel")},
        headers=auth_headers,
    )
    assert response.status_code == 400
