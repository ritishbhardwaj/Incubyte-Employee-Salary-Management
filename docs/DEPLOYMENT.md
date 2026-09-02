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

Two ways to view the UI:

**Same process as Cloud (what you deploy):** build the SPA, then open the API origin. `/` is the React app, not Swagger.

```bash
npm --prefix frontend run build
fastapi dev
```

Open `http://127.0.0.1:8000/`. You should see the IncubyteESM login page. `/docs` is still the API docs. `/api/v1/*`, `/health`, and `/ready` stay on the same host.

**Split origin while coding the UI:** Vite on `:5173` proxies `/api` to `:8000`.

```bash
fastapi dev
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Rebuild `frontend/dist` before any Cloud deploy; Cloud does not run `npm run build`.

## FastAPI Cloud

The Cloud process is the same as local `:8000`: FastAPI serves `/api/v1/*` and `app.frontend("/")` serves `frontend/dist`. The homepage of the Cloud URL is the SPA, not Swagger.

This repo is meant to deploy onto the existing Cloud app named **IncubyteESM**.

1. Log in and link that app (once):

```bash
fastapi login
fastapi cloud link
```

Pick the existing **IncubyteESM** app. That writes `.fastapicloud/` (gitignored).

2. Set Cloud env (dashboard or `fastapi cloud env set`). Same Neon URL already migrated and seeded is fine.

| Variable | Value |
|---|---|
| `DATABASE_URL` | Neon URL (`sslmode=require`) |
| `DATABASE_SSL_REQUIRE` | `true` |
| `HR_EMAIL` / `HR_PASSWORD` | Seeded HR account |
| `ENVIRONMENT` | `production` (Secure cookies on HTTPS) |
| `ALLOWED_ORIGINS` | Local origins **plus** the Cloud origin, e.g. `https://incubyteesm.fastapicloud.dev` |

Same-origin POSTs from the SPA this process serves are allowed even if the Cloud env omit `ALLOWED_ORIGINS`. Still set the Cloud origin so Vite-style extra hosts and docs stay accurate.

Without a matching origin, login works but later POST/PATCH (logout, adjust pay, import) get 403.

3. Build the frontend **before** every deploy. Cloud does not run `npm run build`. Production refuses to start if `frontend/dist` is missing.

```bash
npm --prefix frontend run build
fastapi deploy
```

`frontend/dist` is gitignored. `.fastapicloudignore` un-ignores `frontend/dist/` so the built SPA is uploaded.

4. Open the Cloud URL at `/`. You should see the same login page as `http://127.0.0.1:8000/`. `/docs` remains API docs.

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
