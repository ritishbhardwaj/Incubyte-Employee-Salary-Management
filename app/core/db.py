from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

REQUIRED_TABLES = ("users", "sessions", "employees", "compensation_records")


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def build_engine(
    url: str, *, ssl_require: bool = False, pool_size: int = 5, max_overflow: int = 0
) -> Engine:
    url = normalize_database_url(url)
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        kwargs: dict = {"connect_args": connect_args}
        if ":memory:" in url or url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)

    connect_args: dict = {}
    if ssl_require or "neon.tech" in url:
        connect_args["sslmode"] = "require"
    return create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = build_engine(
            settings.database_url,
            ssl_require=settings.database_ssl_require,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def reset_engine() -> None:
    """Test helper: drop the cached engine so the next call rebuilds it."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def database_is_ready(engine: Engine | None = None) -> bool:
    """Liveness of the socket is not enough: schema must already be migrated."""
    engine = engine or get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        tables = set(inspect(engine).get_table_names())
    except Exception:
        return False
    return all(name in tables for name in REQUIRED_TABLES)
