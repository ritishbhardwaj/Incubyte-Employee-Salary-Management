from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db
from app.exports.service import export_employees_csv

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.get("/employees.csv")
def export_employees(
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    job_level: str | None = None,
    status: str | None = None,
    sort: str = "employee_code",
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Response:
    body = export_employees_csv(
        db,
        q=q,
        country=country,
        department=department,
        job_level=job_level,
        status=status,
        sort=sort,
    )
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="incubyteesm-employees.csv"'},
    )
