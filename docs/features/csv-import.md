# Feature: CSV import

## Intent

The source problem is spreadsheet management. After create/adjust/insights/export were stable, import was added so HR can load a CSV with **row-level** validation. Invalid rows are never written. XLSX uploads are rejected (400).

## HTTP

`POST /api/v1/imports/employees`  
multipart field `file`  
Session + CSRF required.

Response:

```json
{
  "created": 1,
  "failed": [{"row": 3, "errors": ["annual_salary must be greater than zero"]}],
  "total_rows": 3
}
```

`row` is 1-based including the header (data starts at 2).

## Required columns

first_name, last_name, email, country, city, department, job_title, job_level, employment_status, hire_date, annual_salary, currency

Optional: employee_code, effective_from or compensation_effective_from, reason or compensation_reason. If `employee_code` is omitted, the next `ESMINCUBYTE-#####` code is assigned. Seeded and sample emails use `@esmincubyte.example`.

UTF-8 (BOM allowed). Missing header columns fail the whole file as row 1 (no data to write).

## Validation (per data row)

- Required fields non-empty
- Email unique in DB and in the file
- employee_code unique if provided
- status in ACTIVE / ON_LEAVE / TERMINATED
- job_level in the known set
- currency in the FX table
- annual_salary numeric and > 0
- dates ISO `YYYY-MM-DD`
- effective_from not in the future

A valid row is created with the same atomic employee+compensation path as the API. A failed insert after validation is reported and does not keep a half-written employee.

Good rows in the same file still commit. That avoids "one typo blocks 9,999 people" while never writing corrupt rows.

## UI

Import is available on the API (and can be wired to a file input later). The demo script emphasizes export; import is documented for reviewers hitting the endpoint or a future button.

## Code

`app/api/routers/imports.py` accepts the multipart file. `app/services/imports.py` parses UTF-8 CSV, validates each data row, and calls `create_employee` for good rows. `app/api/schemas/imports.py` is the result body.

## Tests

Mixed CSV: one created, negative salary and duplicate email fail, only the good email is listable. `.xlsx` filename rejected.
