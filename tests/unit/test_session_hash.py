from datetime import UTC, datetime, timedelta

from app.database.models import Session
from app.exceptions import UnauthorizedError
from app.services.auth import create_session, hash_session_token, resolve_session, revoke_session


def test_hash_is_sha256_hex() -> None:
    digest = hash_session_token("secret-token")
    assert len(digest) == 64
    assert digest != "secret-token"


def test_revoked_session_is_rejected(db) -> None:
    from app.config import get_settings
    from app.services.auth import get_user_by_email

    user = get_user_by_email(db, get_settings().hr_email)
    raw = create_session(db, user)
    db.commit()
    revoke_session(db, raw)
    db.commit()
    try:
        resolve_session(db, raw)
        raise AssertionError("revoked session should fail")
    except UnauthorizedError:
        pass


def test_expired_session_is_rejected(db) -> None:
    from app.config import get_settings
    from app.services.auth import get_user_by_email

    user = get_user_by_email(db, get_settings().hr_email)
    raw = create_session(db, user)
    row = db.query(Session).one()
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    try:
        resolve_session(db, raw)
        raise AssertionError("expired session should fail")
    except UnauthorizedError:
        pass
