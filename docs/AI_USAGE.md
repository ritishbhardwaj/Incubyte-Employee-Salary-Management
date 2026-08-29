# How AI was used

This assessment expects intentional AI use with human judgment. Work was done in Cursor (Grok 4.6) against a written plan, not a one-shot "build me an HRIS" prompt.

## What the model was asked to do

1. Turn the Incubyte brief into a product-shaped plan (persona, in-scope, explicit non-goals).
2. Revise that plan when architecture constraints changed (cookie sessions, compensation ledger, no startup seed, `/api/v1`, CSV, feature packages).
3. Implement the plan stage by stage: requirements first, then backend, tests, seed, React UI, docs.
4. Keep commits user-owned: suggest messages, do not run `git commit`.

## Prompts / instructions that mattered

- The original assessment text (goal, 10k employees, artifacts, incremental history).
- Stack choices: FastAPI, React JavaScript, Neon later via `.env`, FastAPI Cloud serving the SPA.
- Auth: no browser-stored Bearer JWT; hashed opaque session + HttpOnly cookie + CSRF.
- Pay: `compensation_records` as the only source of truth; close + insert atomically.
- Ops: do not migrate or seed on startup.
- Tests: fast, deterministic, SQLite allowed if PostgreSQL-only SQL is isolated.
- Frontend tests only for login validation, filters, salary adjustment validation, and API error rendering.

## What was reviewed and rejected

- JWT in `localStorage` (first draft). Replaced after the revised plan.
- `employees.annual_salary` plus `salary_events` (duplicated truth). Replaced by the ledger.
- Alembic + 10k seed on FastAPI startup. Rejected as an operational surprise.
- Live FX API. Rejected for reliability and auditability.
- XLSX parsing. Rejected as out of scope.
- Repository / unit-of-work layers. Rejected as pattern theater.
- Computing median in Python on SQLite and treating it as the production path. Rejected; percentiles stay PostgreSQL-only.
- Seeding gender. Rejected as unnecessary sensitive data.
- Auto-committing from the agent. The user commits.

## Quality bar the human still owns

- Read the requirements page before trusting the code.
- Run `pytest` and `frontend` tests after pulling.
- Confirm Neon `DATABASE_URL` is never committed.
- Walk the demo script on a migrated, seeded database before recording video.
- Incremental git history is created by the human using the suggested messages, not by a single dump commit.

AI accelerated scaffolding, docs, and test writing. Design decisions (cookie auth, ledger, no startup mutations, dialect honesty) were specified in the plan and checked in the resulting code.
