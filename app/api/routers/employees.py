from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_csrf
from app.api.schemas.employees import (
    EmployeeCreate,
    EmployeeDetail,
    EmployeeListResponse,
    EmployeePatch,
    FilterOptions,
)
from app.database.models import User
from app.database.session import get_db
from app.services.employees import (
    create_employee,
    employee_to_detail,
    employee_to_list_item,
    filter_options,
    get_employee,
    list_employees,
    patch_employee,
)

router = APIRouter(prefix="/api/v1", tags=["employees"])


@router.post("/employees", response_model=EmployeeDetail, status_code=201)
def create_employee_endpoint(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
) -> dict:
    employee = create_employee(db, payload, user)
    db.commit()
    db.refresh(employee)
    return employee_to_detail(db, employee)


@router.get("/employees", response_model=EmployeeListResponse)
def list_employees_endpoint(
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    job_level: str | None = None,
    status: str | None = None,
    sort: str = "employee_code",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    rows, total, page, page_size = list_employees(
        db,
        q=q,
        country=country,
        department=department,
        job_level=job_level,
        status=status,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [employee_to_list_item(emp, comp) for emp, comp in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/employees/{employee_id}", response_model=EmployeeDetail)
def get_employee_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    employee = get_employee(db, employee_id)
    return employee_to_detail(db, employee)


@router.patch("/employees/{employee_id}", response_model=EmployeeDetail)
def patch_employee_endpoint(
    employee_id: UUID,
    payload: EmployeePatch,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
) -> dict:
    employee = patch_employee(db, employee_id, payload)
    db.commit()
    db.refresh(employee)
    return employee_to_detail(db, employee)


@router.get("/meta/filters", response_model=FilterOptions)
def meta_filters(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return filter_options(db)
