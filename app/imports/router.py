from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_csrf
from app.auth.models import User
from app.core.db import get_db
from app.core.exceptions import ValidationAppError
from app.imports.schemas import ImportResult
from app.imports.service import import_employees_csv

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


@router.post("/employees", response_model=ImportResult)
def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
) -> dict:
    filename = (file.filename or "").lower()
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        raise ValidationAppError("XLSX is out of scope. Upload a CSV file.")
    raw = file.file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationAppError("File must be UTF-8 CSV") from exc
    return import_employees_csv(db, user, text)
