# Trade-offs

## Session cookies instead of Bearer JWT

Salary data is sensitive. A token in `localStorage` is easy to steal with XSS. IncubyteESM is a same-origin HR SPA, so an HttpOnly session cookie is the better default.

Cost: CSRF must be handled. We use Origin allowlisting plus a double-submit `iesm_csrf` cookie on POST/PATCH/PUT/DELETE.

We did not implement refresh-token rotation or device lists. One HR user does not need that complexity.

## Compensation ledger instead of salary columns on employees

Duplicating `employees.annual_salary` and `salary_events.old/new` creates two sources of truth. The ledger is slower to query for "current pay" (join on `effective_to IS NULL`) but history cannot drift.

Half-open intervals `[from, to)` allow same-day adjustments: the previous row can close on the same date it opened and still keep the old amounts.

## No future-dated compensation

Without a worker, "become current at midnight" races with timezones and two-current-row bugs. MVP rejects `effective_from` in the future. Scheduled raises are a TODO if a worker is ever added.

## Static FX snapshots, not a live API

Live rates add outages and make yesterday's payroll unexplained. Each record stores the rate used. Changing `app/fx.py` later does not rewrite history. Rates will drift from the market; that is accepted.

## No migrate/seed on startup

Hidden 10k inserts on boot are slow, surprising, and unsafe on FastAPI Cloud. Ops stay explicit: `alembic upgrade head`, `python -m app.seed`. `/ready` tells you the schema is missing.

Cost: first deploy is two extra commands. That is the correct cost.

## SQLite tests vs PostgreSQL production

The default suite uses in-memory SQLite so it stays fast and deterministic without Neon.

`percentile_cont` is PostgreSQL-only (`app/analytics/pg_percentiles.py`). On SQLite, percentiles are returned as null with `source=postgresql_percentile_cont_only`. Tests assert that honesty instead of computing a Python median and pretending the dialects match.

Count, sum, and average are portable SQL and are tested.

## CSV instead of XLSX

The problem is Excel. CSV is the overlap that every spreadsheet tool speaks, without a binary parser. XLSX is out of scope.

Import writes only valid rows and returns row-level errors. It does not all-or-nothing the file: one bad row must not block 9,999 good ones, and it must not write the bad row.

## Sync SQLAlchemy, small pool

One FastAPI Cloud worker. Async + a large pool would multiply connections against Neon for no gain. `pool_size=5`, `pool_pre_ping=True`, SSL for Neon hosts.

## Mantine + Recharts instead of a paid data grid

10k rows are never sent to the browser. A simple table plus server pagination is enough. Charts are Recharts, not a second analytics stack.
