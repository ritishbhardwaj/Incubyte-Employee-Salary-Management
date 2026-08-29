# Feature: Employee management

## Intent

HR manages people, not just a read-only list. Spreadsheets mixed identity and pay in one row. IncubyteESM separates them: this feature is identity and employment status. Pay is [salary-management.md](salary-management.md).

## Status

`ACTIVE`, `ON_LEAVE`, `TERMINATED`. Employees are never hard-deleted. There is no `DELETE /api/v1/employees/{id}` (405).

## HTTP

All require a session. Mutations require CSRF.

| Method | Path | Behavior |
|---|---|---|
| POST | `/api/v1/employees` | Create employee + initial compensation in one transaction. 201. |
| GET | `/api/v1/employees` | Search, filter, sort, paginate. Join current compensation. |
| GET | `/api/v1/employees/{id}` | Profile, current pay, full history. |
| PATCH | `/api/v1/employees/{id}` | Identity / org / status / hire_date. **Not salary.** |
| GET | `/api/v1/meta/filters` | Distinct countries, departments, levels, plus status enum. |

### List query parameters

- `q` — case-insensitive match on first name, last name, email, employee_code
- `country`, `department`, `job_level`, `status`
- `sort` — `employee_code` (default), `name`, `hire_date`, `department`, `salary_usd`. Prefix `-` for descending
- `page` (1-based), `page_size` (1-100, default 25)

Response: `{ items, total, page, page_size }`. The UI never receives 10,000 rows at once.

### Create body

Employee fields plus nested `compensation`: `annual_salary`, `currency`, optional `effective_from` (defaults today, cannot be future or before hire), `reason` (default "Initial compensation").

`employee_code` is optional. If omitted, the next `ACME-00001` style code is generated.

Emails are stored lowercased. Duplicate email or code is 409.

Job levels: `IC1`–`IC6`, `M1`–`M4`.

## Indexes

`employee_code`, `email`, `country`, `department`, `job_level`, `employment_status`.

## UI

Employees page: filters, paginated table, CSV export of the **applied** filter, add-employee modal (atomic initial pay).

Detail page: profile patch (city, department, title, level, status) and compensation panel.

## Tests

Create / list / get / patch; duplicate email; pagination; 401 without session; DELETE is 405.

## Out of scope

Org-chart, manager hierarchy, document attachments, bulk status changes without CSV import.
