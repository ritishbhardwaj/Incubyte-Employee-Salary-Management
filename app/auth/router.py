from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_csrf
from app.auth.models import User
from app.auth.schemas import LoginRequest, UserOut
from app.auth.service import authenticate, create_session, revoke_session
from app.core.config import get_settings
from app.core.csrf import new_csrf_token
from app.core.db import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_session_cookies(response: Response, raw_session: str) -> None:
    settings = get_settings()
    max_age = settings.session_absolute_hours * 3600
    session_kw = {
        "max_age": max_age,
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        "path": "/",
    }
    response.set_cookie(settings.session_cookie_name, raw_session, **session_kw)
    csrf_kw = {**session_kw, "httponly": False}
    response.set_cookie(settings.csrf_cookie_name, new_csrf_token(), **csrf_kw)


def _clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = authenticate(db, payload.email, payload.password)
    raw = create_session(db, user)
    db.commit()
    _set_session_cookies(response, raw)
    return user


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> dict[str, str]:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        revoke_session(db, token)
        db.commit()
    _clear_session_cookies(response)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
