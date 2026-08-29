from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import resolve_session
from app.core.config import get_settings
from app.core.csrf import enforce_csrf
from app.core.db import get_db
from app.core.exceptions import UnauthorizedError


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise UnauthorizedError("Not authenticated")
    return resolve_session(db, token)


def require_csrf(request: Request) -> None:
    enforce_csrf(request)
