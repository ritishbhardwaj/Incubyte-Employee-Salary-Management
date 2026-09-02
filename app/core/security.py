"""Passwords, session token hashing, and CSRF / Origin checks."""

import hashlib
import hmac
import secrets
from urllib.parse import urlparse

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


def normalize_origin(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().rstrip("/")


def origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return None


def effective_origin(request: Request) -> str | None:
    print(request.headers.get("referer"))
    print(origin_from_referer(request.headers.get("referer")))
    print(normalize_origin(request.headers.get("origin")))
    print(normalize_origin(origin_from_referer(request.headers.get("referer"))))
    return normalize_origin(request.headers.get("origin")) or origin_from_referer(
        request.headers.get("referer")
    )


def public_origin(request: Request) -> str | None:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    proto = proto.split(",")[0].strip()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return None
    host = host.split(",")[0].strip()
    return normalize_origin(f"{proto}://{host}")


def origin_is_allowed(
    origin: str | None,
    allowed: list[str] | None = None,
    *,
    same_origin: str | None = None,
) -> bool:
    origin = normalize_origin(origin)
    if origin is None:
        return False
    allowed = allowed if allowed is not None else get_settings().origin_list()
    allowed_norm = {normalize_origin(item) for item in allowed if item}
    if origin in allowed_norm:
        return True
    same = normalize_origin(same_origin)
    return same is not None and origin == same


def enforce_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    settings = get_settings()
    origin = effective_origin(request)
    if not origin_is_allowed(origin, settings.origin_list(), same_origin=public_origin(request)):
        raise ForbiddenError("Invalid or missing Origin")
    header = request.headers.get("x-csrf-token")
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not tokens_match(header, cookie):
        raise ForbiddenError("CSRF validation failed")
