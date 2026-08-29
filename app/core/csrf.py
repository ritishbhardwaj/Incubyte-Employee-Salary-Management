import hmac
import secrets

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def tokens_match(header_token: str | None, cookie_token: str | None) -> bool:
    if not header_token or not cookie_token:
        return False
    return hmac.compare_digest(header_token, cookie_token)


def origin_is_allowed(origin: str | None, allowed: list[str] | None = None) -> bool:
    if origin is None:
        return False
    allowed = allowed if allowed is not None else get_settings().origin_list()
    return origin in allowed


def enforce_csrf(request: Request) -> None:
    """Reject unsafe methods that fail Origin allowlist or double-submit CSRF."""
    if request.method in SAFE_METHODS:
        return
    settings = get_settings()
    origin = request.headers.get("origin")
    if not origin_is_allowed(origin, settings.origin_list()):
        raise ForbiddenError("Invalid or missing Origin")
    header = request.headers.get("x-csrf-token")
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not tokens_match(header, cookie):
        raise ForbiddenError("CSRF validation failed")
