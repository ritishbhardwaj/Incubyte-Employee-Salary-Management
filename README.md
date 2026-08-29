# IncubyteESM

Employee salary management for ESMINCUBYTE's HR Manager. FastAPI + React (JavaScript) + Neon PostgreSQL, served as one FastAPI Cloud app.

This is not a payroll engine. It is a same-origin web app to manage people and pay, and to answer how the organization pays — without Excel as the system of record.

## What you get

- Session login (HttpOnly cookie + CSRF). No JWT in the browser.
- Employee create / list / get / patch. No hard deletes.
- Compensation ledger: current pay is the open `compensation_records` row.
- Insights in USD (headcount, payroll, average, median/percentiles on Postgres, breakdowns, distribution, recent changes).
- Filtered CSV export. Validated CSV import. No XLSX.
- Deterministic seed: `python -m app.seed --employees 10000 --seed 42`

## Local run

```bash
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install fastapi[standard] sqlalchemy psycopg[binary] pydantic-settings email-validator alembic bcrypt pytest httpx ruff
copy .env.example .env
# set DATABASE_URL to local Postgres or Neon
alembic upgrade head
python -m app.seed --employees 10000 --seed 42
fastapi dev
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Open `http://localhost:5173`.

Default HR login (from `.env.example`):

- Email: `hr.manager@esmincubyte.example`
- Password: `ChangeMeNow!`

Startup does **not** migrate or seed. Those stay operational commands.

## Tests

```bash
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check app tests
cd frontend && npm test && npm run lint
```

Backend tests use SQLite fixtures. PostgreSQL `percentile_cont` is isolated and documented; SQLite tests do not fake it.

## Deploy

Build the SPA, then deploy the FastAPI app (it serves `frontend/dist`):

```bash
npm --prefix frontend run build
fastapi deploy
```

See [Docs/DEPLOYMENT.md](Docs/DEPLOYMENT.md). Put Neon credentials in `.env` / FastAPI Cloud secrets, never in git.

## Docs

Start with [Docs/REQUIREMENTS.md](Docs/REQUIREMENTS.md). Architecture, trade-offs, AI use, feature notes, demo script, and future work live under `Docs/`.
