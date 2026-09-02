from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import Settings, get_settings
from app.core.security import hash_password, hash_session_token, verify_password
from app.database.models import Session, User
from app.exceptions import UnauthorizedError


def utcnow() -> datetime:
    return datetime.now(UTC)


def get_user_by_email(db: DbSession, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def ensure_hr_user(db: DbSession, settings: Settings | None = None) -> User:
    settings = settings or get_settings()
    target = settings.hr_email.lower()
    existing = get_user_by_email(db, target)
    if existing:
        return existing
    users = list(db.scalars(select(User)).all())
    if len(users) == 1:
        users[0].email = target
        users[0].password_hash = hash_password(settings.hr_password)
        db.flush()
        return users[0]
    user = User(
        email=target,
        password_hash=hash_password(settings.hr_password),
        created_at=utcnow(),
    )
    db.add(user)
    db.flush()
    return user


def authenticate(db: DbSession, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    return user


def create_session(db: DbSession, user: User, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    raw = secrets.token_urlsafe(32)
    now = utcnow()
    row = Session(
        user_id=user.id,
        token_hash=hash_session_token(raw),
        created_at=now,
        expires_at=now + timedelta(hours=settings.session_absolute_hours),
        last_seen_at=now,
        revoked_at=None,
    )
    db.add(row)
    db.flush()
    return raw


def resolve_session(db: DbSession, raw_token: str, settings: Settings | None = None) -> User:
    settings = settings or get_settings()
    now = utcnow()
    row = db.scalar(select(Session).where(Session.token_hash == hash_session_token(raw_token)))
    if row is None or row.revoked_at is not None:
        raise UnauthorizedError("Not authenticated")
    expires_at = _aware(row.expires_at)
    last_seen = _aware(row.last_seen_at)
    if expires_at <= now:
        raise UnauthorizedError("Session expired")
    idle_limit = last_seen + timedelta(hours=settings.session_idle_hours)
    if idle_limit <= now:
        raise UnauthorizedError("Session expired")
    row.last_seen_at = now
    db.flush()
    user = db.get(User, row.user_id)
    if user is None:
        raise UnauthorizedError("Not authenticated")
    return user


def revoke_session(db: DbSession, raw_token: str) -> None:
    row = db.scalar(select(Session).where(Session.token_hash == hash_session_token(raw_token)))
    if row is None or row.revoked_at is not None:
        return
    row.revoked_at = utcnow()
    db.flush()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
