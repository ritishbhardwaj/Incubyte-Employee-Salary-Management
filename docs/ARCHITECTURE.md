# IncubyteESM architecture

## Shape

IncubyteESM is a **modular monolith** in one OS process:

- FastAPI serves `/health`, `/ready`, `/api/v1/*`, and (when built) the React SPA from `frontend/dist`.
- Neon PostgreSQL is the system of record.
- There are no workers, queues, or extra frontend hosts.

```
HR browser
    |  same origin in production (FastAPI Cloud)
    v
FastAPI  ---- JSON /api/v1 ---->  feature packages
    |                                |
    +-- static SPA                   +-- SQLAlchemy sessions
                                     v
                                Neon Postgres
```

Local development splits the origin on purpose: Vite on `:5173` proxies `/api`, `/health`, and `/ready` to FastAPI on `:8000` so cookies stay first-party from the browser's point of view.

## Packages

Layers are only **router -> service -> SQLAlchemy**. There is no repository or unit-of-work wrapper.

| Package | Responsibility |
|---|---|
| `app.core` | Settings, engine, FX table, CSRF helpers, pagination, domain errors |
| `app.auth` | Users, hashed sessions, login/logout/me, current-user dependency |
| `app.employees` | Employee identity and directory queries |
| `app.compensation` | Effective-dated pay ledger |
| `app.analytics` | SQL insights; PostgreSQL percentiles isolated in `pg_percentiles.py` |
| `app.exports` | Filtered CSV |
| `app.imports` | Validated CSV with row-level errors |
| `app.seed` | CLI-only deterministic generator |

`app.main:app` is the FastAPI Cloud entrypoint (`[tool.fastapi] entrypoint`).

## Persistence

**Employees have no salary columns.** Pay exists only on `compensation_records`.

- Current compensation: `effective_to IS NULL` (partial unique index per employee).
- Intervals are half-open `[effective_from, effective_to)`.
- An adjustment sets `effective_to` on the open row and inserts a new open row in one transaction.
- Each row stores local amount, currency, `fx_rate_to_usd`, and `annual_salary_usd` at write time.

Sessions store `sha256(raw_token)` only. The raw token is the HttpOnly cookie `iesm_session`.

Alembic owns schema. Application startup never runs migrations or seed.

## Auth

1. `POST /api/v1/auth/login` verifies bcrypt password, inserts a `sessions` row, sets `iesm_session` (HttpOnly, SameSite=Lax, Secure in production) and `iesm_csrf` (readable).
2. Authenticated reads send the session cookie automatically.
3. Mutations also send `X-CSRF-Token` matching `iesm_csrf` and an Origin on the allowlist.
4. Absolute lifetime 12 hours; idle timeout 4 hours via `last_seen_at`.
5. Logout sets `revoked_at` and clears both cookies.

## API surface

Public: `GET /health`, `GET /ready`, `POST /api/v1/auth/login`, static frontend.

Everything else under `/api/v1` requires a valid session. `/ready` is 503 if the database is down **or** required tables are missing (unmigrated).

## Frontend

Vite + React 18 + JavaScript + Mantine + Recharts. `fetch` uses `credentials: "include"`. No token is stored in `localStorage`.

In production `app.frontend("/", directory="frontend/dist", fallback="index.html")` is mounted only if `frontend/dist` exists, so `fastapi dev` still works before `npm run build`.
