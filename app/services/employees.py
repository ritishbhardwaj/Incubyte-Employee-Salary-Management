from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.api.schemas.employees import EmployeeCreate, EmployeePatch
from app.database.models import JOB_LEVELS, CompensationRecord, Employee, EmploymentStatus, User
from app.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.org import EMPLOYEE_CODE_PREFIX, format_employee_code
from app.pagination import clamp_page, offset_for
from app.services.auth import utcnow
from app.services.compensation import (
    create_initial_compensation,
    get_current_compensation,
    list_compensation_history,
)

SORT_FIELDS = {
    "employee_code": Employee.employee_code,
    "name": Employee.last_name,
    "hire_date": Employee.hire_date,
    "department": Employee.department,
    "salary_usd": CompensationRecord.annual_salary_usd,
}


def _validate_level(job_level: str) -> str:
    if job_level not in JOB_LEVELS:
        raise ValidationAppError(f"job_level must be one of: {', '.join(JOB_LEVELS)}")
    return job_level


def _next_employee_code(db: Session) -> str:
    codes = db.scalars(
        select(Employee.employee_code).where(Employee.employee_code.like(f"{EMPLOYEE_CODE_PREFIX}-%"))
    ).all()
    highest = 0
    for code in codes:
        suffix = code.split("-", 1)[-1]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return format_employee_code(highest + 1)


def create_employee(db: Session, payload: EmployeeCreate, actor: User) -> Employee:
    _validate_level(payload.job_level)
    email = str(payload.email).lower()
    if db.scalar(select(Employee.id).where(Employee.email == email)):
        raise ConflictError("An employee with this email already exists")
    code = payload.employee_code.strip() if payload.employee_code else _next_employee_code(db)
    if db.scalar(select(Employee.id).where(Employee.employee_code == code)):
        raise ConflictError("An employee with this employee_code already exists")

    now = utcnow()
    employee = Employee(
        employee_code=code,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        country=payload.country.strip(),
        city=payload.city.strip(),
        department=payload.department.strip(),
        job_title=payload.job_title.strip(),
        job_level=payload.job_level,
        employment_status=payload.employment_status.value,
        hire_date=payload.hire_date,
        created_at=now,
        updated_at=now,
    )
    db.add(employee)
    db.flush()
    create_initial_compensation(
        db,
        employee=employee,
        actor=actor,
        annual_salary=payload.compensation.annual_salary,
        currency=payload.compensation.currency,
        effective_from=payload.compensation.effective_from,
        reason=payload.compensation.reason or "Initial compensation",
    )
    db.flush()
    return employee


def get_employee(db: Session, employee_id: UUID) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee


def patch_employee(db: Session, employee_id: UUID, payload: EmployeePatch) -> Employee:
    employee = get_employee(db, employee_id)
    data = payload.model_dump(exclude_unset=True)
    if "job_level" in data and data["job_level"] is not None:
        data["job_level"] = _validate_level(data["job_level"])
    if "email" in data and data["email"] is not None:
        email = str(data["email"]).lower()
        other = db.scalar(
            select(Employee.id).where(Employee.email == email, Employee.id != employee.id)
        )
        if other:
            raise ConflictError("An employee with this email already exists")
        data["email"] = email
    if "employment_status" in data and data["employment_status"] is not None:
        data["employment_status"] = data["employment_status"].value
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(employee, key, value)
    employee.updated_at = utcnow()
    db.flush()
    return employee


def _base_list_query(
    *,
    q: str | None,
    country: str | None,
    department: str | None,
    job_level: str | None,
    status: str | None,
) -> Select:
    current = aliased(CompensationRecord)
    stmt = select(Employee, current).outerjoin(
        current,
        (current.employee_id == Employee.id) & (current.effective_to.is_(None)),
    )
    if q:
        term = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Employee.first_name).like(term),
                func.lower(Employee.last_name).like(term),
                func.lower(Employee.email).like(term),
                func.lower(Employee.employee_code).like(term),
            )
        )
    if country:
        stmt = stmt.where(Employee.country == country)
    if department:
        stmt = stmt.where(Employee.department == department)
    if job_level:
        stmt = stmt.where(Employee.job_level == job_level)
    if status:
        try:
            EmploymentStatus(status)
        except ValueError as exc:
            raise ValidationAppError("Invalid employment status") from exc
        stmt = stmt.where(Employee.employment_status == status)
    return stmt


def list_employees(
    db: Session,
    *,
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    job_level: str | None = None,
    status: str | None = None,
    sort: str = "employee_code",
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[tuple[Employee, CompensationRecord | None]], int, int, int]:
    page, page_size = clamp_page(page, page_size)
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    if key not in SORT_FIELDS:
        raise ValidationAppError(f"sort must be one of: {', '.join(SORT_FIELDS)}")

    stmt = _base_list_query(
        q=q, country=country, department=department, job_level=job_level, status=status
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order_col = SORT_FIELDS[key]
    stmt = stmt.order_by(order_col.desc() if descending else order_col.asc())
    stmt = stmt.offset(offset_for(page, page_size)).limit(page_size)
    rows = list(db.execute(stmt).all())
    return rows, int(total), page, page_size


def filter_options(db: Session) -> dict[str, list[str]]:
    countries = list(db.scalars(select(Employee.country).distinct().order_by(Employee.country)).all())
    departments = list(
        db.scalars(select(Employee.department).distinct().order_by(Employee.department)).all()
    )
    levels = list(db.scalars(select(Employee.job_level).distinct().order_by(Employee.job_level)).all())
    return {
        "countries": countries,
        "departments": departments,
        "job_levels": levels,
        "statuses": [item.value for item in EmploymentStatus],
    }


def employee_to_list_item(employee: Employee, current: CompensationRecord | None) -> dict:
    current_out = None
    if current is not None:
        current_out = {
            "annual_salary": current.annual_salary,
            "currency": current.currency,
            "fx_rate_to_usd": current.fx_rate_to_usd,
            "annual_salary_usd": current.annual_salary_usd,
            "effective_from": current.effective_from,
            "reason": current.reason,
        }
    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "country": employee.country,
        "city": employee.city,
        "department": employee.department,
        "job_title": employee.job_title,
        "job_level": employee.job_level,
        "employment_status": employee.employment_status,
        "hire_date": employee.hire_date,
        "current_compensation": current_out,
    }


def employee_to_detail(db: Session, employee: Employee) -> dict:
    current = get_current_compensation(db, employee.id)
    payload = employee_to_list_item(employee, current)
    payload["created_at"] = employee.created_at
    payload["updated_at"] = employee.updated_at
    payload["compensation_history"] = list_compensation_history(db, employee.id)
    return payload


def apply_employee_filters(
    db: Session,
    *,
    q: str | None,
    country: str | None,
    department: str | None,
    job_level: str | None,
    status: str | None,
    sort: str = "employee_code",
) -> list[tuple[Employee, CompensationRecord | None]]:
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    if key not in SORT_FIELDS:
        raise ValidationAppError(f"sort must be one of: {', '.join(SORT_FIELDS)}")
    stmt = _base_list_query(
        q=q, country=country, department=department, job_level=job_level, status=status
    )
    order_col = SORT_FIELDS[key]
    stmt = stmt.order_by(order_col.desc() if descending else order_col.asc())
    return list(db.execute(stmt).all())
