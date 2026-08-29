# Feature: CSV export

## Intent

HR still needs a spreadsheet *exit*. Export is a report, not the system of record. XLSX is out of scope.

## HTTP

`GET /api/v1/exports/employees.csv`

Same filters as the directory: `q`, `country`, `department`, `job_level`, `status`, `sort`.

Authenticated. Safe method: no CSRF.

`Content-Type: text/csv`  
`Content-Disposition: attachment; filename="incubyteesm-employees.csv"`

## Columns

employee_code, first_name, last_name, email, country, city, department, job_title, job_level, employment_status, hire_date, annual_salary, currency, fx_rate_to_usd, annual_salary_usd, compensation_effective_from, compensation_reason

Pay columns come from the **current** compensation row.

The export is unpaginated for the filter. For a full 10k unfiltered dump that is acceptable for an HR download; the list API stays paginated.

## UI

Employees page Export CSV uses the **applied** filter, not the unapplied form fields.

## Tests

Two employees, filter Engineering, CSV has a header and one data row, Sales absent.
