from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import enforce_csrf
from app.database.models import User
from app.database.session import get_db
from app.exceptions import UnauthorizedError
from app.services.auth import resolve_session


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise UnauthorizedError("Not authenticated")
    return resolve_session(db, token)


def require_csrf(request: Request) -> None:
    enforce_csrf(request)
