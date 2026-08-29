from datetime import date
from decimal import Decimal

from app.auth.service import get_user_by_email
from app.compensation.schemas import CompensationCreate
from app.compensation.service import (
    adjust_compensation,
    get_current_compensation,
    list_compensation_history,
)
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.employees.models import EmploymentStatus
from app.employees.schemas import EmployeeCreate
from app.employees.service import create_employee


def _create(db, email="pay.person@acme.example"):
    actor = get_user_by_email(db, get_settings().hr_email)
    payload = EmployeeCreate(
        first_name="Pay",
        last_name="Person",
        email=email,
        country="United States",
        city="Austin",
        department="Engineering",
        job_title="Engineer",
        job_level="IC3",
        employment_status=EmploymentStatus.ACTIVE,
        hire_date=date(2021, 3, 1),
        compensation=CompensationCreate(
            annual_salary=Decimal("120000"),
            currency="USD",
            effective_from=date(2021, 3, 1),
            reason="Initial compensation",
        ),
    )
    return create_employee(db, payload, actor), actor


def test_adjust_closes_current_and_inserts_new(db) -> None:
    employee, actor = _create(db)
    first = get_current_compensation(db, employee.id)
    assert first is not None
    first_id = first.id
    incoming = adjust_compensation(
        db,
        employee_id=employee.id,
        actor=actor,
        annual_salary=Decimal("130000"),
        currency="USD",
        effective_from=date(2024, 1, 1),
        reason="Market adjustment",
    )
    db.commit()
    current = get_current_compensation(db, employee.id)
    assert current is not None
    assert current.id == incoming.id
    assert current.annual_salary == Decimal("130000.00")
    closed = db.get(type(first), first_id)
    assert closed is not None
    assert closed.effective_to == date(2024, 1, 1)
    assert closed.annual_salary == Decimal("120000.00")
    history = list_compensation_history(db, employee.id)
    assert len(history) == 2


def test_rejects_future_effective_from(db) -> None:
    employee, actor = _create(db, email="future.person@acme.example")
    try:
        adjust_compensation(
            db,
            employee_id=employee.id,
            actor=actor,
            annual_salary=Decimal("140000"),
            currency="USD",
            effective_from=date(2099, 1, 1),
            reason="Too early",
        )
        raise AssertionError("future date should fail")
    except ValidationAppError:
        pass
