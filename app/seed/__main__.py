from __future__ import annotations

import argparse
import sys

from sqlalchemy import func, select

from app.auth.service import ensure_hr_user, utcnow
from app.compensation.models import CompensationRecord
from app.core.config import get_settings
from app.core.db import get_engine, get_session_factory
from app.employees.models import Employee
from app.seed.generator import generate_employees


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed IncubyteESM with deterministic employees.")
    parser.add_argument("--employees", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Dangerous: delete existing employees and compensation, then reseed.",
    )
    args = parser.parse_args(argv)

    engine = get_engine()
    factory = get_session_factory()
    db = factory()
    try:
        existing = db.scalar(select(func.count()).select_from(Employee)) or 0
        if existing and not args.force:
            print(
                f"Refusing to seed: {existing} employees already exist. "
                "Pass --force to wipe employees and compensation first.",
                file=sys.stderr,
            )
            return 1
        if existing and args.force:
            from sqlalchemy import delete

            db.execute(delete(CompensationRecord))
            db.execute(delete(Employee))
            db.commit()

        hr = ensure_hr_user(db, get_settings())
        db.commit()

        rows = generate_employees(args.employees, args.seed)
        now = utcnow()
        chunk = 500
        for start in range(0, len(rows), chunk):
            batch = rows[start : start + chunk]
            employees = [
                Employee(
                    employee_code=row.employee_code,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    email=row.email,
                    country=row.country,
                    city=row.city,
                    department=row.department,
                    job_title=row.job_title,
                    job_level=row.job_level,
                    employment_status=row.employment_status,
                    hire_date=row.hire_date,
                    created_at=now,
                    updated_at=now,
                )
                for row in batch
            ]
            db.add_all(employees)
            db.flush()
            comps = [
                CompensationRecord(
                    employee_id=employee.id,
                    annual_salary=row.annual_salary,
                    currency=row.currency,
                    fx_rate_to_usd=row.fx_rate_to_usd,
                    annual_salary_usd=row.annual_salary_usd,
                    effective_from=row.hire_date,
                    effective_to=None,
                    reason="Seed",
                    created_at=now,
                    created_by=hr.id,
                )
                for employee, row in zip(employees, batch, strict=True)
            ]
            db.add_all(comps)
            db.commit()
            print(f"Inserted {min(start + chunk, len(rows))}/{len(rows)}")
        print(f"Seeded {len(rows)} employees with seed={args.seed}")
        return 0
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
