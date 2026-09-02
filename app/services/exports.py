import csv
import io

from sqlalchemy.orm import Session

from app.services.employees import apply_employee_filters

CSV_HEADERS = [
    "employee_code",
    "first_name",
    "last_name",
    "email",
    "country",
    "city",
    "department",
    "job_title",
    "job_level",
    "employment_status",
    "hire_date",
    "annual_salary",
    "currency",
    "fx_rate_to_usd",
    "annual_salary_usd",
    "compensation_effective_from",
    "compensation_reason",
]


def export_employees_csv(
    db: Session,
    *,
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    job_level: str | None = None,
    status: str | None = None,
    sort: str = "employee_code",
) -> str:
    rows = apply_employee_filters(
        db,
        q=q,
        country=country,
        department=department,
        job_level=job_level,
        status=status,
        sort=sort,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for employee, current in rows:
        writer.writerow(
            [
                employee.employee_code,
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.country,
                employee.city,
                employee.department,
                employee.job_title,
                employee.job_level,
                employee.employment_status,
                employee.hire_date.isoformat(),
                current.annual_salary if current else "",
                current.currency if current else "",
                current.fx_rate_to_usd if current else "",
                current.annual_salary_usd if current else "",
                current.effective_from.isoformat() if current else "",
                current.reason if current else "",
            ]
        )
    return buffer.getvalue()
