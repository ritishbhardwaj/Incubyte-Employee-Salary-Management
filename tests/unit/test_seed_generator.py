from app.org import EMAIL_DOMAIN, EMPLOYEE_CODE_PREFIX, format_employee_code
from app.seed import generate_employees


def test_seed_uses_org_identity() -> None:
    row = generate_employees(1, 42)[0]
    assert row.employee_code == format_employee_code(1)
    assert row.employee_code.startswith(f"{EMPLOYEE_CODE_PREFIX}-")
    assert row.email.endswith(f"@{EMAIL_DOMAIN}")


def test_seed_is_deterministic() -> None:
    first = generate_employees(25, 42)
    second = generate_employees(25, 42)
    assert [row.email for row in first] == [row.email for row in second]
    assert [row.annual_salary for row in first] == [row.annual_salary for row in second]


def test_seed_uses_country_level_bands() -> None:
    rows = generate_employees(2000, 42)
    india = [r.annual_salary_usd for r in rows if r.country == "India"]
    united_states = [r.annual_salary_usd for r in rows if r.country == "United States"]
    assert india and united_states
    india_avg = sum(india) / len(india)
    us_avg = sum(united_states) / len(united_states)
    assert india_avg < us_avg
