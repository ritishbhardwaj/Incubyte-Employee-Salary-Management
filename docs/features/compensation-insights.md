# Feature: Compensation insights

## Intent

HR must answer how ACME pays people without downloading 10,000 rows. All figures use **stored** `annual_salary_usd` on **current** rows (`effective_to IS NULL`) for **ACTIVE** employees unless noted.

## HTTP

All authenticated GET.

| Path | Result |
|---|---|
| `/api/v1/analytics/summary` | active_headcount, total_annual_payroll_usd, average, median, percentiles |
| `/api/v1/analytics/breakdowns` | country, department, job_level: headcount, total_usd, average_usd |
| `/api/v1/analytics/distribution` | Fixed USD buckets and counts |
| `/api/v1/analytics/recent-changes` | Latest ledger inserts excluding `reason = Seed` |

## Percentiles and dialect honesty

Production PostgreSQL uses `percentile_cont` in `app/analytics/pg_percentiles.py`.

SQLite tests (and any non-Postgres bind) return:

```json
"percentiles": {
  "p25": null, "p50": null, "p75": null, "p90": null,
  "dialect": "sqlite",
  "source": "postgresql_percentile_cont_only"
}
```

`median_salary_usd` is null in that case. The UI shows an em dash and a short note. Tests assert this instead of inventing a Python median.

Portable aggregates (count, sum, avg, group by, bucket case) are SQL on both dialects and are tested.

## Distribution buckets (USD)

0-40k, 40-60k, 60-80k, 80-100k, 100-130k, 130-160k, 160-200k, 200k+. Half-open except the last.

## UI

KPI cards, Recharts bar chart, breakdown tables, recent changes table.

## Out of scope

Gender pay gap, cost-of-living indexes, live FX restatement, OLAP cubes.
