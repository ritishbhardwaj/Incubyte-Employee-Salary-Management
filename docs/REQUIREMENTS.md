# IncubyteESM - Requirements

**Product:** IncubyteESM (Incubyte Employee Salary Management)
**Customer:** ACME (fictional org in this assessment)
**Primary user:** HR Manager
**Scale:** ~10,000 employees across multiple countries
**Problem:** Salary data lives in spreadsheets. That is slow, error-prone, and cannot answer how the org pays people without manual pivot work.

This page is the product contract written before application code. It states what we will build, what we will not build, and why.

---

## Goal

Give the HR Manager a same-origin web application to:

1. Manage people - create, find, update, and retain employee records (no hard deletes).
2. Manage pay - record current and historical compensation as an explainable ledger, not a cell that gets overwritten.
3. Understand pay - answer org-level questions in a single reporting currency (USD) using server-side analytics, not Excel dumps of 10,000 rows.

Success is a working end-to-end product (API + UI + PostgreSQL), not a prototype of every HRIS module.

---

## Scope

### In scope

| Capability | HR outcome |
|---|---|
| Session login / logout | Only the HR user can see or change salary data. |
| Employee management | Add people, search/filter/sort/page a large directory, update role/location/status. |
| Compensation ledger | Record initial pay with the employee; later adjust pay with a required reason; see history. |
| Compensation insights | Active headcount, total annual payroll (USD), average, median, percentiles, breakdowns by country / department / level, salary distribution, recent changes. |
| CSV export | Download the filtered directory plus current compensation (spreadsheet exit, not the system of record). |
| Deterministic seed | Reproduce 10,000 believable employees locally and in review environments. |
| Operational honesty | Schema changes and seeding are explicit commands, not hidden startup side effects. |

Employment status is ACTIVE, ON_LEAVE, or TERMINATED. Terminated people remain in the database.

Pay is stored in local currency plus a snapshot of the FX rate and the computed USD amount at write time. Insights use those stored USD figures so history stays explainable if reference rates later change.

### Deliberately out of scope

| Left out | Reason |
|---|---|
| Payroll runs, tax, statutory deductions, payslips | Different product. ACME asked to manage salary data and understand pay, not to become a payroll engine. |
| Multi-role RBAC, approval chains, employee self-service | One persona (HR Manager). Extra roles would dilute the assessment without changing the core design. |
| Live FX APIs | External rates add failure modes and rewrite risk. A static reference table plus per-record snapshots is enough and auditable. |
| XLSX import/export | Spreadsheet interop is valuable; XLSX parsing is a large, buggy surface. CSV covers the Excel workflow. |
| Gender or other unnecessary sensitive demographics | Easy to get ethically and legally wrong; not required to answer how ACME pays. |
| Background workers / queues | FastAPI Cloud is one process. Nothing in the MVP requires async jobs. |
| Future-scheduled compensation | Becoming current at midnight without a worker creates gaps or two current rows. MVP only accepts effective_from on or before today. |
| Auto-migrate or auto-seed on process start | Startup must not mutate schema or insert 10,000 rows. Ops stay explicit: alembic upgrade head, python -m app.seed. |
| Browser-stored Bearer JWT | Salary data is sensitive. Tokens in localStorage are easier to steal via XSS. Same-origin cookie sessions fit an internal HR SPA. |

CSV import is a planned follow-on after create / adjust / insights / export are stable. When added, every row is validated and failures are returned per row. Invalid rows are never written.

---

## Product rules (non-negotiable)

- One source of truth for pay: compensation_records, not a salary column copied onto employees.
- Current pay is the open row (effective_to IS NULL). An adjustment closes that row and inserts a new one in one transaction. Historical amounts, currencies, and FX snapshots are never overwritten.
- Intervals are half-open [effective_from, effective_to).
- Money is decimal, never floating point.
- Lists never return 10,000 rows. Server-side pagination (page size capped).
- Analytics are SQL over current compensation, not Python scans of the full table in the request path (PostgreSQL percentiles are dialect-specific and documented as such).
- All sensitive APIs require the authenticated HR session. Health/readiness and login are public.

---

## Experience (UI)

A single React application served from the same FastAPI process in production:

1. Sign in (demo HR credentials visible for the assessment).
2. Insights - how we pay in one screen.
3. Employees - search, filter, page, export CSV of the current filter.
4. Employee detail - profile edits, compensation history, adjust pay (reason required).

---

## Deployment and data

- Backend: FastAPI (Python), feature packages, Router then Service then SQLAlchemy.
- Frontend: React + JavaScript, Mantine, Recharts.
- Database: Neon PostgreSQL. Credentials live in .env / host secrets, never in git.
- Ship: one FastAPI Cloud app serves /api/v1/* and the built SPA. No extra frontend host, no workers.

---

## Acceptance

The product is done enough to submit when an HR Manager can log in, inspect org-wide pay, find people in a 10,000-row directory, create or update an employee, adjust compensation and see immutable history, export a filtered CSV, and when tests cover those rules without requiring a live Neon instance.
