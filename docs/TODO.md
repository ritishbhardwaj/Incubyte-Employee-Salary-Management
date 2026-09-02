# Future work

Essential follow-ups that did not belong in the MVP.

## Product

- [ ] Playwright (or similar) end-to-end path: login, filter, adjust, export.
- [ ] Optional all-or-nothing CSV import mode for legal "upload this file as a batch".
- [ ] CSV export of compensation history, not only current pay.
- [ ] Role-based access if a second persona appears (compensation partner vs HRBP). Still one org. Update `DATA_AND_ROLES_CYCLE.md` and `HTTP_SEQUENCE_FLOWS.md` in the same change.
- [ ] Audit log of profile field changes (status, department) in addition to pay.
- [ ] Soft search with `pg_trgm` if name search feels slow on larger than 10k.

## Compensation

- [ ] Future-dated raises **only** with a worker or a nightly job that closes/opens rows in one transaction. Do not fake this in the request path.
- [ ] Optional "as-of" pay view (what was current on date D) using the ledger.
- [ ] Currency admin UI for the reference FX table (still snapshot on write).

## Layout

- [ ] Keep `app/database/models.py` as the single models file. Do not split tables back into feature packages unless that file becomes unreadable.
- [ ] Keep `frontend/src/lib/api.js` as the only cookie/CSRF client. New screens should import it, not open a second `fetch` helper.
- [ ] After the flatten, smoke-check a FastAPI Cloud deploy: entrypoint stays `app.main:app`, `frontend/dist` still ships, `ALLOWED_ORIGINS` still includes the Cloud origin.

## Platform

- [ ] Rotate the Neon role password if it was ever pasted into `.env.example`, committed, or shared in chat. Keep the live URL only in `.env`.
- [x] Re-seed Neon with `--force` after the org rename so existing `employee_code` / email rows match `ESMINCUBYTE`.
- [ ] CI job that runs pytest + frontend tests + ruff + `npm run lint` on every push.
- [ ] Optional marked PostgreSQL test for `percentile_cont` against `DATABASE_URL_TEST`.
- [ ] `fastapi login`, `fastapi cloud link` to the existing IncubyteESM app, set Cloud env (including the Cloud origin in `ALLOWED_ORIGINS`), then `fastapi deploy`.
- [ ] FastAPI Cloud GitHub Action that builds `frontend/dist` then `fastapi deploy`.
- [ ] Connection metrics / slow-query logging on Neon.

## Explicitly never (unless the product changes)

- XLSX parsing.
- Gender or other unnecessary sensitive demographics.
- Payroll/tax/payslip engine.
- Auto-migrate or auto-seed on process start.
- Bearer JWT in `localStorage`.
