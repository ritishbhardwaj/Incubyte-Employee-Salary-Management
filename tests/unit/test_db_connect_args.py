import socket

from app.core.db import (
    CONNECT_TIMEOUT_SECONDS,
    normalize_database_url,
    postgres_connect_args,
    prefer_ipv4_hostaddr,
)


def test_normalize_adds_psycopg_driver() -> None:
    assert (
        normalize_database_url("postgresql://u:p@localhost/db")
        == "postgresql+psycopg://u:p@localhost/db"
    )


def test_prefer_ipv4_returns_a_record(monkeypatch) -> None:
    def fake_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        assert family == socket.AF_INET
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 5432))]

    monkeypatch.setattr("app.core.db.socket.getaddrinfo", fake_getaddrinfo)
    assert prefer_ipv4_hostaddr("example.neon.tech") == "203.0.113.10"


def test_prefer_ipv4_none_when_dns_fails(monkeypatch) -> None:
    def fake_getaddrinfo(*_args, **_kwargs):
        raise socket.gaierror("no A record")

    monkeypatch.setattr("app.core.db.socket.getaddrinfo", fake_getaddrinfo)
    assert prefer_ipv4_hostaddr("missing.example") is None


def test_postgres_connect_args_ssl_timeout_and_hostaddr(monkeypatch) -> None:
    monkeypatch.setattr("app.core.db.prefer_ipv4_hostaddr", lambda _host: "198.51.100.20")
    args = postgres_connect_args(
        "postgresql+psycopg://u:p@ep-demo.neon.tech/neondb",
        ssl_require=True,
    )
    assert args["sslmode"] == "require"
    assert args["connect_timeout"] == CONNECT_TIMEOUT_SECONDS
    assert args["hostaddr"] == "198.51.100.20"


def test_postgres_connect_args_ssl_from_neon_host_without_flag(monkeypatch) -> None:
    monkeypatch.setattr("app.core.db.prefer_ipv4_hostaddr", lambda _host: None)
    args = postgres_connect_args(
        "postgresql+psycopg://u:p@ep-demo.neon.tech/neondb",
        ssl_require=False,
    )
    assert args["sslmode"] == "require"
    assert "hostaddr" not in args
