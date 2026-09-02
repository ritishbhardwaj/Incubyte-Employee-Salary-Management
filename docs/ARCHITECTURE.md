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
FastAPI  ---- JSON /api/v1 ---->  routers -> services
    |                                |
    +-- static SPA                   +-- SQLAlchemy sessions
                                     v
                                Neon Postgres
```

Local development splits the origin on purpose: Vite on `:5173` proxies `/api`, `/health`, and `/ready` to FastAPI on `:8000` so cookies stay first-party from the browser's point of view.

## Layout

The backend is a small FastAPI app, not a feature-package forest. Layers are only **router -> service -> SQLAlchemy**. There is no repository or unit-of-work wrapper.

```
app/
  main.py                 FastAPI app: /health, /ready, AppError handler, SPA mount
  config.py               Settings from .env
  org.py                  ESMINCUBYTE name, email domain, employee-code prefix
  fx.py                   Static FX table + to_usd
  exceptions.py           AppError and HTTP-mapped subclasses
  pagination.py           page / page_size helpers
  seed.py                 CLI: python -m app.seed
  api/
    router.py             master_router (includes every area router)
    dependencies.py       get_current_user, require_csrf
    routers/              one file per HTTP area
    schemas/              Pydantic request/response models
  core/
    security.py           bcrypt, session SHA-256, CSRF / Origin
  database/
    models.py             ALL tables in one file
    session.py            engine, get_db, Neon IPv4 / SSL / timeout
  services/               business logic, one file per area
```

| Module | Responsibility |
|---|---|
| `app.main` | Create the FastAPI app. Include `master_router`. Mount `frontend/dist`. |
| `app.config` | `Settings` / `get_settings()`. |
| `app.org` | Org identity: `ESMINCUBYTE` codes and `@esmincubyte.example` emails. |
| `app.fx` | Static FX map. Snapshot at write. Changing this file does not rewrite history. |
| `app.exceptions` | Domain errors turned into JSON `{detail}` by the app handler. |
| `app.core.security` | Passwords, `hash_session_token`, CSRF header vs cookie, Origin allowlist. |
| `app.database.models` | `User`, `Session`, `Employee`, `CompensationRecord`, `EmploymentStatus`, `JOB_LEVELS`. |
| `app.database.session` | Engine, `get_db`, `build_engine` (SSL, 15s timeout, IPv4 `hostaddr`). |
| `app.api.router` | `master_router` — the only include from `main.py`. |
| `app.api.routers.*` | HTTP only. No SQL. Auth, employees, compensation, analytics, exports, imports. |
| `app.api.schemas.*` | Request and response shapes. |
| `app.services.*` | Transactions, ledger rules, directory queries, CSV, insights. Percentiles: `pg_percentiles.py`. |
| `app.seed` | Deterministic generator + CLI. Never runs on process start. |

`app.main:app` is the FastAPI Cloud entrypoint (`[tool.fastapi] entrypoint`).

Frontend follows the same idea: `frontend/src/lib/api.js` (cookie + CSRF `fetch`) and `frontend/src/lib/org.js` (display name + demo email). Pages and components stay under `pages/` and `components/` because this SPA has those screens.

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

Vite + React 18 + JavaScript + Mantine + Recharts. `frontend/src/lib/api.js` uses `fetch` with `credentials: "include"` and sends `X-CSRF-Token` from the `iesm_csrf` cookie on mutations. No token is stored in `localStorage`.

`app.frontend("/", directory="frontend/dist", fallback="index.html")` is mounted when the Vite build exists. Then `GET /` is the SPA (login / insights), not Swagger. `/docs` stays at `/docs`. API routes win over the SPA fallback. Production (`ENVIRONMENT=production`) refuses to start if `frontend/dist` is missing so Cloud cannot ship an API-only homepage.
