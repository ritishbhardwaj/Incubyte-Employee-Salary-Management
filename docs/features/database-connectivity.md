# Database connectivity

IncubyteESM talks to PostgreSQL through SQLAlchemy + psycopg. Production is Neon. Tests use in-memory SQLite and never open Neon.

## Configuration

| Setting | Source | Role |
|---|---|---|
| `DATABASE_URL` | `.env` only | Neon or local Postgres URL. `postgres://` is rewritten to `postgresql://`, then to `postgresql+psycopg://`. |
| `DATABASE_SSL_REQUIRE` | `.env`, default `true` | Forces `sslmode=require` on the driver. Also forced when the URL host contains `neon.tech`. |

Do not put a real Neon password in `.env.example` or in `Settings` defaults. Those files are committed. Keep the live URL in `.env` (gitignored).

## What `build_engine` adds on Postgres

1. **`sslmode=require`** when `DATABASE_SSL_REQUIRE` is true or the host is Neon.
2. **`connect_timeout=15`** so a dead route fails in seconds instead of hanging Alembic or seed.
3. **`hostaddr` = first IPv4 A record** when DNS has one. Neon publishes AAAA records. On many Windows machines those IPv6 addresses time out (black-hole). libpq tries IPv6 first, so `alembic upgrade head` looks frozen for 30–90 seconds even though IPv4 works in ~200ms. `hostaddr` pins TCP to IPv4; TLS SNI still uses the hostname.

Alembic `env.py` uses `build_engine()` so migrate, seed, and the API share the same SSL / timeout / IPv4 behavior.

## Operator checks

If migrate or seed hangs with no SQL output, the process is still opening a socket.

1. Confirm Neon compute is not paused (first wake can add 10–30s after TCP is up).
2. Confirm `.env` has `DATABASE_SSL_REQUIRE=true` and `sslmode=require` on the URL.
3. `channel_binding=require` is optional. It is not required for this app; leave it if Neon’s dashboard added it and connect succeeds.
4. Prefer the Neon **pooler** host (`…-pooler.…`) for many short connections (API). Direct compute host is fine for one-off migrate/seed.

## Out of scope

- Runtime `alembic upgrade` or seed on process start.
- Application-level retry storms against Neon.
- Custom CA bundles (Neon’s public CA is enough with `sslmode=require`).
