"""Passwords, session token hashing, and CSRF / Origin checks."""

import hashlib
import hmac
import secrets

import bcrypt
from fastapi import Request

from app.config import get_settings
from app.exceptions import ForbiddenError

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


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
