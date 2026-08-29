from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import utcnow
from app.compensation.models import CompensationRecord
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.fx import to_usd
from app.employees.models import Employee


def get_current_compensation(db: Session, employee_id: UUID) -> CompensationRecord | None:
    return db.scalar(
        select(CompensationRecord).where(
            CompensationRecord.employee_id == employee_id,
            CompensationRecord.effective_to.is_(None),
        )
    )


def list_compensation_history(db: Session, employee_id: UUID) -> list[CompensationRecord]:
    return list(
        db.scalars(
            select(CompensationRecord)
            .where(CompensationRecord.employee_id == employee_id)
            .order_by(
                CompensationRecord.effective_from.desc(),
                CompensationRecord.created_at.desc(),
            )
        ).all()
    )


def create_initial_compensation(
    db: Session,
    *,
    employee: Employee,
    actor: User,
    annual_salary: Decimal,
    currency: str,
    effective_from: date | None,
    reason: str,
) -> CompensationRecord:
    start = effective_from or date.today()
    _validate_effective_from(start, hire_date=employee.hire_date, previous_from=None)
    rate, usd = to_usd(annual_salary, currency)
    record = CompensationRecord(
        employee_id=employee.id,
        annual_salary=annual_salary,
        currency=currency.upper(),
        fx_rate_to_usd=rate,
        annual_salary_usd=usd,
        effective_from=start,
        effective_to=None,
        reason=reason.strip(),
        created_at=utcnow(),
        created_by=actor.id,
    )
    db.add(record)
    db.flush()
    return record


def adjust_compensation(
    db: Session,
    *,
    employee_id: UUID,
    actor: User,
    annual_salary: Decimal,
    currency: str | None,
    effective_from: date | None,
    reason: str,
) -> CompensationRecord:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")
    current = get_current_compensation(db, employee_id)
    if current is None:
        raise ValidationAppError("Employee has no current compensation to adjust")

    start = effective_from or date.today()
    _validate_effective_from(
        start, hire_date=employee.hire_date, previous_from=current.effective_from
    )
    if start < current.effective_from:
        raise ValidationAppError("effective_from cannot precede the current period start")

    code = (currency or current.currency).upper()
    rate, usd = to_usd(annual_salary, code)

    # Half-open [effective_from, effective_to). Same-day adjustments keep the
    # previous amounts as an immutable row even if the closed interval is empty.
    current.effective_to = start
    incoming = CompensationRecord(
        employee_id=employee.id,
        annual_salary=annual_salary,
        currency=code,
        fx_rate_to_usd=rate,
        annual_salary_usd=usd,
        effective_from=start,
        effective_to=None,
        reason=reason.strip(),
        created_at=utcnow(),
        created_by=actor.id,
    )
    db.add(incoming)
    db.flush()
    return incoming


def _validate_effective_from(start: date, *, hire_date: date, previous_from: date | None) -> None:
    today = date.today()
    if start > today:
        raise ValidationAppError("effective_from cannot be in the future")
    if start < hire_date:
        raise ValidationAppError("effective_from cannot be before the hire date")
    if previous_from is not None and start < previous_from:
        raise ValidationAppError("effective_from cannot precede the current period start")
