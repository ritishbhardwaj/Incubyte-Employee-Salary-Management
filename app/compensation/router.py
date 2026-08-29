from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_csrf
from app.auth.models import User
from app.compensation.schemas import CompensationAdjust, CompensationOut
from app.compensation.service import adjust_compensation, list_compensation_history
from app.core.db import get_db
from app.employees.service import get_employee

router = APIRouter(prefix="/api/v1/employees", tags=["compensation"])


@router.post("/{employee_id}/compensation", response_model=CompensationOut)
def adjust_compensation_endpoint(
    employee_id: UUID,
    payload: CompensationAdjust,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
) -> object:
    record = adjust_compensation(
        db,
        employee_id=employee_id,
        actor=user,
        annual_salary=payload.annual_salary,
        currency=payload.currency,
        effective_from=payload.effective_from,
        reason=payload.reason,
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/{employee_id}/compensation", response_model=list[CompensationOut])
def list_compensation_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list:
    get_employee(db, employee_id)
    return list_compensation_history(db, employee_id)
