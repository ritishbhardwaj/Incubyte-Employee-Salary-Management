# Feature: Deterministic seed

## Intent

Reviewers and local machines must share the same 10,000-employee shape. Seed is an **explicit CLI**, never an application startup side effect.

## Command

```bash
python -m app.seed --employees 10000 --seed 42
```

- Ensures the HR user from `HR_EMAIL` / `HR_PASSWORD`.
- If employees already exist, exits 1 unless `--force` (deletes compensation then employees, then reseeds).
- Inserts in chunks of 500.
- Compensation `reason` is `Seed` so insights "recent changes" can exclude them.
- `created_by` is the HR user.

## Generator (`app/seed/generator.py`)

`random.Random(seed)` only. No Faker (non-deterministic versions).

- 10 countries with matching currencies and cities
- 8 departments
- Levels IC1–IC6 and M1–M4
- Status weighted toward ACTIVE, plus ON_LEAVE and TERMINATED
- Hire dates from 2014 onward
- Pay: USD level band × country multiplier × department multiplier × deterministic jitter, converted through the static FX table, rounded in local units (INR/JPY to thousands)

No gender or other unnecessary sensitive fields.

Identity comes from `app.core.org`: org short name `ESMINCUBYTE`, codes `ESMINCUBYTE-00001` … `ESMINCUBYTE-10000`, emails `{first}.{last}.{n}@esmincubyte.example`. The HR login default is `hr.manager@esmincubyte.example`.

The same `--seed` always yields the same emails and amounts (unit-tested).

## Why not startup seed

First request on FastAPI Cloud would block on 10k inserts, hide failures, and surprise production redeploys. `/ready` only checks connectivity and schema presence.
