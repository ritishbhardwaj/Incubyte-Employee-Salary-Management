# IncubyteESM — data flow cycle and roles cycle

Companion **time-ordered** HTTP diagrams: [`HTTP_SEQUENCE_FLOWS.md`](HTTP_SEQUENCE_FLOWS.md).

This document is the end-to-end map of **who** can do **what**, and **how data moves** from the browser into Neon and back out as screens, CSV, and insights.

V1 has **one application role**. Employees are **records**, not logins. Pay never lives on the employee row.

---

## 1. Roles cycle (who exists, what they can do)

### 1.1 Application identities (can sign in)

| Identity | Stored in | How created | What they can do in V1 |
|---|---|---|---|
| **HR Manager** | `users` | `python -m app.seed` via `ensure_hr_user` using `HR_EMAIL` / `HR_PASSWORD` | Everything the UI exposes: read insights and the directory, create/patch people, adjust pay, import/export CSV, log out |
| *(no other login)* | — | — | There is no HR Admin, HRBP, Finance, Manager, or employee self-service user |

There is no `role` column. Authorization is: **valid session ⇒ full HR access**. Invalid or missing session ⇒ 401 on `/api/v1/*` except login.

```
                    seed CLI
                       |
                       v
                 users (1 row)
                       |
              login (email + password)
                       |
                       v
              sessions (hashed token)
                       |
         +-------------+-------------+
         |                           |
    reads (cookie)            mutations (cookie
                               + CSRF + Origin)
         |                           |
         v                           v
    GET APIs                    POST / PATCH
```

**HR session lifecycle**

1. **Provision** — seed (or a later login against an already-created user) ensures one bcrypt-hashed row in `users`.
2. **Authenticate** — `POST /api/v1/auth/login` verifies bcrypt password, inserts a `sessions` row, sets cookies.
3. **Hold** — browser keeps `iesm_session` (HttpOnly) and `iesm_csrf` (readable). Absolute cap 12 hours. Idle cap 4 hours (`last_seen_at` refreshed on authenticated requests).
4. **Act** — SPA `fetch` uses `credentials: "include"`. GETs need the session cookie. POST/PATCH/PUT/DELETE also need `Origin` on `ALLOWED_ORIGINS` and `X-CSRF-Token` matching `iesm_csrf`.
5. **End** — `POST /api/v1/auth/logout` sets `revoked_at` and clears both cookies. A revoked or expired session cannot be reused.

Login does **not** require CSRF (there is no prior cookie contract). Logout **does**.

### 1.2 People in the org (cannot sign in)

These are rows on `employees`. They never get a password. The HR Manager is not an employee record unless someone creates one.

| Employment status | Meaning in V1 | Hard delete | In Insights (org pay) |
|---|---|---|---|
| `ACTIVE` | Currently employed and in payroll-style reporting | Never | **Yes** — current compensation only |
| `ON_LEAVE` | Still on the books, not in org-pay KPIs | Never | No |
| `TERMINATED` | Left; history kept | Never | No |

Status cycle (HR only, via create / PATCH / CSV import):

```
            create (default ACTIVE)
                    |
                    v
              +-- ACTIVE <--+
              |             |
              |  PATCH /    |  PATCH /
              |  import     |  import
              v             |
          ON_LEAVE ---------+
              |
              v
          TERMINATED -----> (stays; no DELETE endpoint)
```

There is no `DELETE /api/v1/employees/{id}` (405). Termination is a status change, not a wipe.

### 1.3 What is explicitly not a role in V1

- Approver / Finance sign-off before pay becomes current
- Manager seeing only their team
- Read-only dashboard user
- Employee viewing their own salary
- Multi-tenant orgs

Those would be a **new roles cycle** (new `users` rows + permission checks). Until then, one login owns the whole ledger.

---

## 2. Data stores (what is true where)

```
employees                          compensation_records
---------                          --------------------
identity + job + status            THE ONLY PLACE PAY LIVES
employee_code (ESMINCUBYTE-#####)  annual_salary, currency
email (lowercased, unique)         fx_rate_to_usd          (snapshot at write)
hire_date, country, city           annual_salary_usd       (snapshot at write)
department, title, level           effective_from / effective_to
NO salary columns                  reason, created_by (users.id)
                                   current row: effective_to IS NULL
```

Supporting tables: `users`, `sessions`. FX rates are **not** a table; they are the static map in `app/fx.py`.

**Current pay** = the unique open ledger row (`effective_to IS NULL`). Intervals are half-open `[effective_from, effective_to)`.

---

## 3. Request cycle (every interactive action)

Same process in production: FastAPI serves the SPA from `frontend/dist` at `/` and JSON under `/api/v1`.

```
HR browser
    |  GET /  → index.html (React)
    |  GET /assets/* → JS/CSS
    |  fetch /api/v1/...  (same origin, cookies)
    v
FastAPI  (router → service → SQLAlchemy)
    v
Neon PostgreSQL
```

Layering never skips the service: **router → service → SQLAlchemy**. No queues, no workers, no extra frontend host.

| Kind | Auth | CSRF + Origin | Examples |
|---|---|---|---|
| Public | none | no | `POST /login`, `GET /health` |
| Liveness of schema | none (DB ping) | no | `GET /ready` (503 if down or unmigrated) |
| Authenticated read | session cookie | no | me, list, get, history, insights, CSV export |
| Authenticated write | session cookie | **yes** | create, patch, adjust, import, logout |

---

## 4. Data flow cycles (product paths)

### 4.0 Bootstrap (ops, not HTTP)

Startup **never** migrates or seeds.

```
alembic upgrade head     →  users, sessions, employees, compensation_records
python -m app.seed       →  HR user + 10,000 employees + one open ledger row each
                            (reason = "Seed"; insights "recent changes" exclude these)
```

Seed is deterministic (`--seed 42`). Codes `ESMINCUBYTE-00001`… emails `@esmincubyte.example`.

### 4.1 Session cycle

```
SPA /login
  POST /api/v1/auth/login  { email, password }
       → bcrypt verify
       → INSERT sessions
       → Set-Cookie iesm_session, iesm_csrf
SPA GET /api/v1/auth/me     → current user or 401 → redirect /login
…work…
SPA POST /api/v1/auth/logout
       → sessions.revoked_at = now
       → clear cookies
```

### 4.2 Hire / create cycle (identity + first pay, one transaction)

Spreadsheets mixed person and salary on one row. V1 does not.

```
HR fills add-employee (profile + initial compensation)
  POST /api/v1/employees   [session + CSRF]
       → validate level, unique email/code, salary > 0, currency in FX table
       → effective_from ≤ today and ≥ hire_date
       → INSERT employees
       → INSERT compensation_records (open row, snapshots USD)
       → 201
Directory / detail / insights can now see that person
```

If `employee_code` is omitted, the next `ESMINCUBYTE-#####` is allocated.

A failed compensation insert does not leave an employee without pay: create is atomic.

### 4.3 Directory cycle (read, never 10k at once)

```
Employees page filters
  GET /api/v1/meta/filters          → distinct countries, depts, levels + status enum
  GET /api/v1/employees?q=&country=&…&page=&page_size=
       → join current compensation (effective_to IS NULL)
       → { items, total, page, page_size }
```

Search `q` matches first name, last name, email, employee_code (case-insensitive). Sort: code, name, hire_date, department, `salary_usd`.

### 4.4 Profile cycle (not salary)

```
Detail page PATCH
  PATCH /api/v1/employees/{id}   [session + CSRF]
       → city, department, title, level, status, hire_date, …
       → NOT annual_salary
```

Changing status (e.g. ACTIVE → TERMINATED) does **not** close the compensation row. The person drops out of Insights because analytics filter `employment_status = ACTIVE` **and** current pay. History remains.

### 4.5 Pay adjustment cycle (the ledger)

History is explainable because amounts on old rows are never rewritten (except `effective_to`).

```
HR: amount, currency, effective_from, reason (required)
  POST /api/v1/employees/{id}/compensation   [session + CSRF]
       1. Load current open row
       2. Reject future effective_from; reject before hire or before current period start
       3. Snapshot FX → annual_salary_usd
       4. In one transaction:
            current.effective_to = new.effective_from
            INSERT new open row (effective_to NULL, created_by = HR user)
  GET  /api/v1/employees/{id}/compensation
       → history newest first
```

Same-day adjust is allowed (empty closed interval) so a correction still leaves an immutable row.

```
time ---->

  [===== open row A =====)
                         [===== open row B =====)     after adjust
  A.effective_to = B.effective_from
  A.annual_salary unchanged forever
```

### 4.6 Insights cycle (org pay, no Excel dump)

All figures use **stored** `annual_salary_usd` on **current** rows for **ACTIVE** employees (unless the endpoint says otherwise).

```
Insights page
  GET /api/v1/analytics/summary        → headcount, total payroll USD, avg, median, percentiles
  GET /api/v1/analytics/breakdowns     → country / department / job_level
  GET /api/v1/analytics/distribution   → fixed USD buckets
  GET /api/v1/analytics/recent-changes → latest ledger inserts, excluding reason = "Seed"
```

Median / percentiles use Postgres `percentile_cont`. SQLite tests return nulls plus an honest dialect flag — they do not fake a Python median.

Changing FX in `fx.py` later **does not rewrite history**. Old rows keep their snapshot.

### 4.7 Spreadsheet cycle (exit and re-entry, not the system of record)

**Export (GET, session only)**

```
Employees page current filters
  GET /api/v1/exports/employees.csv?...
       → same filter as the directory
       → current pay columns
       → attachment incubyteesm-employees.csv
```

**Import (POST, session + CSRF)**

```
CSV file (UTF-8)
  POST /api/v1/imports/employees
       → each data row validated
       → good rows: same atomic create as the API
       → bad rows: returned with 1-based row numbers; never written
       → XLSX filename → 400
```

Valid rows in a mixed file still commit. One typo does not block the rest; corrupt rows never land.

### 4.8 Readiness cycle (ops)

```
GET /health  → process is up (no DB)
GET /ready   → SELECT 1 + required tables present
               else 503 (unmigrated or unreachable)
```

---

## 5. One picture: hire → pay → report → leave

```
                    HR Manager (users + session)
                               |
         +---------------------+---------------------+
         |                     |                     |
         v                     v                     v
   CREATE employee      ADJUST compensation     PATCH status
   + first ledger row   close A, insert B       TERMINATED
         |                     |                     |
         v                     v                     v
   employees            compensation_records    still in DB
   (ACTIVE)             (open row B)            (not in Insights)
         |                     |
         +----------+----------+
                    |
                    v
            Insights / CSV export
            (ACTIVE + open row only)
```

---

## 6. Money cycle (Decimal, snapshot FX)

1. HR submits local `annual_salary` + `currency`.
2. Service looks up `fx_rate_to_usd` in `app/fx.py` (not an HTTP FX API).
3. `annual_salary_usd` is computed and **stored**.
4. Insights and directory `salary_usd` sort **read the stored number**.
5. Historical rows keep the rate from the day they were written.

Unsupported currency → 400. Salary ≤ 0 → rejected. Types are `Decimal` / `NUMERIC`, never float.

---

## 7. What this cycle is not

| Not in V1 | Why it would change this document |
|---|---|
| Payroll run / tax / payslip | New data stores and a different “pay cycle” |
| Future-dated raise that becomes current at midnight | Needs a worker; V1 forbids `effective_from` in the future |
| Second approver | New role + pending vs current ledger states |
| Live FX restatement | Insights would recompute instead of reading snapshots |
| Employee login | `users` would attach to `employees`; data-access boundaries |

Until those exist, the cycle above is the whole product: **one HR login, people as records, pay as an append-only ledger, insights as SQL over current ACTIVE USD snapshots.**

---

## 8. Where to read more

| Topic | File |
|---|---|
| HTTP sequences | `HTTP_SEQUENCE_FLOWS.md` |
| Product contract | `Docs/REQUIREMENTS.md` |
| Package map | `Docs/ARCHITECTURE.md` |
| Auth cookies / CSRF | `Docs/features/authentication.md` |
| Directory API | `Docs/features/employee-directory.md` |
| Ledger rules | `Docs/features/salary-management.md` |
| Insights SQL | `Docs/features/compensation-insights.md` |
| CSV in/out | `Docs/features/csv-import.md`, `Docs/features/csv-export.md` |
| Seed | `Docs/features/seeding.md` |
