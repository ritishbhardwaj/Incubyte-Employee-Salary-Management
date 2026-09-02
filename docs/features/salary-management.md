# Feature: Compensation ledger

## Intent

Pay must be explainable years later. Overwriting a salary cell (or a column on `employees`) loses history. IncubyteESM stores an effective-dated ledger.

## Source of truth

Table `compensation_records` only. Employees have no salary fields.

| Column | Role |
|---|---|
| `annual_salary` | Local currency, `NUMERIC(14,2)` |
| `currency` | ISO code in the static FX table |
| `fx_rate_to_usd` | Rate used at write time, `NUMERIC(18,8)` |
| `annual_salary_usd` | Snapshot, `NUMERIC(14,2)` |
| `effective_from` / `effective_to` | Half-open `[from, to)`. Null `to` means current |
| `reason` | Required, max 500 |
| `created_by` | HR user id |
| `created_at` | Write timestamp |

Partial unique index: one row per employee where `effective_to IS NULL`.

## Rules

1. Money is `Decimal`. Never float.
2. FX comes from `app/fx.py`. Unsupported currency is 400.
3. `annual_salary` must be > 0.
4. `effective_from` cannot be in the future (MVP).
5. `effective_from` cannot be before hire date or before the current period start.
6. Adjust: in one transaction, set current `effective_to = new.effective_from`, insert new open row. Historical amounts are never UPDATEd except `effective_to`.
7. Same-day adjust is allowed (empty closed interval) so corrections still leave an immutable row.

## HTTP

| Method | Path | Behavior |
|---|---|---|
| POST | `/api/v1/employees` | Nested initial row (`reason` often "Initial compensation") |
| POST | `/api/v1/employees/{id}/compensation` | Adjust |
| GET | `/api/v1/employees/{id}/compensation` | History, newest first |

## UI

Adjust salary modal: amount, currency, date, reason. Client rejects empty reason and non-positive amount before the API. History table shows from/to/local/USD/reason.

## Code

| File | Role |
|---|---|
| `app/database/models.py` | `CompensationRecord` only. No salary columns on `Employee`. |
| `app/services/compensation.py` | Initial row, adjust (close + insert), current, history. |
| `app/api/routers/compensation.py` | `POST/GET .../compensation`. |
| `app/api/schemas/compensation.py` | Create, adjust, out. |
| `app/fx.py` | Static rates; snapshot stored on the row. |

## Tests

Unit: close + insert, reject future dates. API: history length 2 after adjust, closed amount unchanged, empty reason 422, future date 400. FX unit tests for USD identity and INR snapshot.

## Out of scope

Future-scheduled raises, bonuses, equity, payroll deductions, live FX.
