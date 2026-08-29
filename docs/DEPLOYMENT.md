# Deployment

IncubyteESM is one process. FastAPI Cloud runs the API and, after you build the SPA, serves `frontend/dist`.

## Prerequisites

- Python 3.12
- Node.js 20+
- A PostgreSQL database (Neon recommended)
- FastAPI Cloud CLI (`fastapi` from `fastapi[standard]`)

## Environment

Copy `.env.example` to `.env`. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon or local Postgres. `postgresql://` is normalized to `postgresql+psycopg://`. |
| `DATABASE_SSL_REQUIRE` | `true` for Neon (and most hosted Postgres). Local Postgres can be `false`. |
| `HR_EMAIL` / `HR_PASSWORD` | Seeded HR account (seed CLI). |
| `ALLOWED_ORIGINS` | Origins allowed on cookie-authenticated mutations. Include the FastAPI Cloud URL. |
| `ENVIRONMENT` | `production` turns on Secure cookies. |

FastAPI Cloud can inject `DATABASE_URL` via its Neon integration.

## First-time database (explicit)

Startup will **not** do this.

```bash
alembic upgrade head
python -m app.seed --employees 10000 --seed 42
```

If employees already exist, seed refuses unless you pass `--force` (deletes employees and compensation).

On Windows, Neon’s IPv6 addresses often time out. The engine pins TCP to IPv4 (`hostaddr`) and uses a 15s connect timeout so `alembic upgrade head` does not sit silent for a minute. Details: `Docs/features/database-connectivity.md`.

## Local

```bash
fastapi dev
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Health: `GET /health`. Readiness: `GET /ready` (503 until migrated).

## FastAPI Cloud

1. Set secrets: `DATABASE_URL`, `HR_EMAIL`, `HR_PASSWORD`, `ALLOWED_ORIGINS`, `ENVIRONMENT=production`.
2. Add your Cloud hostname to `ALLOWED_ORIGINS`.
3. Build the frontend **before** deploy. Cloud does not run `npm run build`.

```bash
npm --prefix frontend run build
fastapi deploy
```

`frontend/dist` is gitignored. `.fastapicloudignore` contains `!frontend/dist/` so the built SPA is uploaded anyway.

4. SSH/CLI is not required for migrate if you can run Alembic against the same `DATABASE_URL` from your laptop:

```bash
alembic upgrade head
python -m app.seed --employees 10000 --seed 42
```

5. Confirm `GET /ready` returns 200, then sign in.

## What not to do

- Do not add startup hooks that call `alembic upgrade` or insert 10,000 rows.
- Do not commit Neon passwords.
- Do not deploy without rebuilding `frontend/dist` if the UI changed.
