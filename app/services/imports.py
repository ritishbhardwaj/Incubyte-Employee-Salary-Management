import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import IO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.compensation import CompensationCreate
from app.api.schemas.employees import EmployeeCreate
from app.database.models import JOB_LEVELS, Employee, EmploymentStatus, User
from app.fx import supported_currencies
from app.services.employees import create_employee

REQUIRED_COLUMNS = (
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
)


def import_employees_csv(db: Session, actor: User, file_obj: IO[str] | str) -> dict:
    stream = io.StringIO(file_obj) if isinstance(file_obj, str) else file_obj
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        return {
            "created": 0,
            "failed": [{"row": 1, "errors": ["CSV has no header row"]}],
            "total_rows": 0,
        }

    missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
    if missing:
        return {
            "created": 0,
            "failed": [{"row": 1, "errors": [f"Missing required columns: {', '.join(missing)}"]}],
            "total_rows": 0,
        }

    created = 0
    failed: list[dict] = []
    seen_emails: set[str] = set()
    seen_codes: set[str] = set()
    total = 0

    for index, raw in enumerate(reader, start=2):
        total += 1
        errors = _validate_row(db, raw, seen_emails, seen_codes)
        if errors:
            failed.append({"row": index, "errors": errors})
            continue
        payload = _to_payload(raw)
        try:
            create_employee(db, payload, actor)
            db.flush()
            created += 1
            seen_emails.add(str(payload.email).lower())
            if payload.employee_code:
                seen_codes.add(payload.employee_code)
        except Exception as exc:
            db.rollback()
            failed.append({"row": index, "errors": [str(getattr(exc, "detail", exc))]})

    db.commit()
    return {"created": created, "failed": failed, "total_rows": total}


def _validate_row(db: Session, raw: dict, seen_emails: set[str], seen_codes: set[str]) -> list[str]:
    errors: list[str] = []
    for col in REQUIRED_COLUMNS:
        if not (raw.get(col) or "").strip():
            errors.append(f"{col} is required")

    email = (raw.get("email") or "").strip().lower()
    if email:
        if email in seen_emails:
            errors.append("duplicate email in this file")
        elif db.scalar(select(Employee.id).where(Employee.email == email)):
            errors.append("email already exists")

    code = (raw.get("employee_code") or "").strip()
    if code:
        if code in seen_codes:
            errors.append("duplicate employee_code in this file")
        elif db.scalar(select(Employee.id).where(Employee.employee_code == code)):
            errors.append("employee_code already exists")

    status = (raw.get("employment_status") or "").strip()
    if status and status not in {item.value for item in EmploymentStatus}:
        errors.append("employment_status must be ACTIVE, ON_LEAVE, or TERMINATED")

    level = (raw.get("job_level") or "").strip()
    if level and level not in JOB_LEVELS:
        errors.append(f"job_level must be one of: {', '.join(JOB_LEVELS)}")

    currency = (raw.get("currency") or "").strip().upper()
    if currency and currency not in supported_currencies():
        errors.append(f"unsupported currency: {currency}")

    salary_raw = (raw.get("annual_salary") or "").strip()
    if salary_raw:
        try:
            if Decimal(salary_raw) <= 0:
                errors.append("annual_salary must be greater than zero")
        except InvalidOperation:
            errors.append("annual_salary must be a number")

    hire = (raw.get("hire_date") or "").strip()
    if hire:
        try:
            date.fromisoformat(hire)
        except ValueError:
            errors.append("hire_date must be YYYY-MM-DD")

    effective = (raw.get("effective_from") or raw.get("compensation_effective_from") or "").strip()
    if effective:
        try:
            start = date.fromisoformat(effective)
            if start > date.today():
                errors.append("effective_from cannot be in the future")
        except ValueError:
            errors.append("effective_from must be YYYY-MM-DD")
    return errors


def _to_payload(raw: dict) -> EmployeeCreate:
    effective = (raw.get("effective_from") or raw.get("compensation_effective_from") or "").strip()
    reason = (raw.get("reason") or raw.get("compensation_reason") or "Imported").strip() or "Imported"
    code = (raw.get("employee_code") or "").strip() or None
    return EmployeeCreate(
        first_name=raw["first_name"].strip(),
        last_name=raw["last_name"].strip(),
        email=raw["email"].strip(),
        country=raw["country"].strip(),
        city=raw["city"].strip(),
        department=raw["department"].strip(),
        job_title=raw["job_title"].strip(),
        job_level=raw["job_level"].strip(),
        employment_status=EmploymentStatus(raw["employment_status"].strip()),
        hire_date=date.fromisoformat(raw["hire_date"].strip()),
        employee_code=code,
        compensation=CompensationCreate(
            annual_salary=Decimal(raw["annual_salary"].strip()),
            currency=raw["currency"].strip().upper(),
            effective_from=date.fromisoformat(effective) if effective else None,
            reason=reason,
        ),
    )
