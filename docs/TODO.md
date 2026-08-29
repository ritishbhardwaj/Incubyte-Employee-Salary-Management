# Future work

Essential follow-ups that did not belong in the MVP.

## Product

- [ ] Playwright (or similar) end-to-end path: login, filter, adjust, export.
- [ ] Optional all-or-nothing CSV import mode for legal "upload this file as a batch".
- [ ] CSV export of compensation history, not only current pay.
- [ ] Role-based access if a second persona appears (compensation partner vs HRBP). Still one org.
- [ ] Audit log of profile field changes (status, department) in addition to pay.
- [ ] Soft search with `pg_trgm` if name search feels slow on larger than 10k.

## Compensation

- [ ] Future-dated raises **only** with a worker or a nightly job that closes/opens rows in one transaction. Do not fake this in the request path.
- [ ] Optional "as-of" pay view (what was current on date D) using the ledger.
- [ ] Currency admin UI for the reference FX table (still snapshot on write).

## Platform

- [ ] Rotate the Neon role password if it was ever pasted into `.env.example`, committed, or shared in chat. Keep the live URL only in `.env`.
- [ ] Re-seed Neon with `--force` after the org rename so existing `employee_code` / email rows match `ESMINCUBYTE` (not leftover fictional codes).
- [ ] CI job that runs pytest + frontend tests + ruff + `npm run lint` on every push.
- [ ] Optional marked PostgreSQL test for `percentile_cont` against `DATABASE_URL_TEST`.
- [ ] FastAPI Cloud GitHub Action that builds `frontend/dist` then `fastapi deploy`.
- [ ] Connection metrics / slow-query logging on Neon.

## Explicitly never (unless the product changes)

- XLSX parsing.
- Gender or other unnecessary sensitive demographics.
- Payroll/tax/payslip engine.
- Auto-migrate or auto-seed on process start.
- Bearer JWT in `localStorage`.
