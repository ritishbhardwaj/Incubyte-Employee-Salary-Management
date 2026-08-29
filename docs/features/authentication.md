# Feature: Authentication

## Intent

Only the ACME HR Manager may see or change salary data. The app is a same-origin SPA. Credentials are not stored in JavaScript-accessible storage.

## Actors

One seeded user: `HR_EMAIL` / `HR_PASSWORD` (defaults in `.env.example`). Created by `python -m app.seed` via `ensure_hr_user`.

## HTTP

| Method | Path | Auth | CSRF | Notes |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | public | no | Bootstrap. Sets cookies. |
| POST | `/api/v1/auth/logout` | cookie optional | yes | Revokes if a session exists. |
| GET | `/api/v1/auth/me` | session | no | Current user. |

## Session model

Table `sessions`:

- `token_hash` = SHA-256 of a 32-byte urlsafe token (hex, 64 chars). The raw token is never stored.
- `expires_at` = login time + 12 hours (absolute).
- `last_seen_at` updated on each authenticated request. Idle limit is 4 hours.
- `revoked_at` set on logout. Resolve rejects revoked or expired rows.

Cookie `iesm_session`: HttpOnly, SameSite=Lax, Path=/, Secure when `ENVIRONMENT=production`.


Cookie `iesm_csrf`: **not** HttpOnly. The SPA reads it and sends `X-CSRF-Token` on mutations.

## CSRF / origin

Unsafe methods (POST, PATCH, PUT, DELETE) after login:

1. `Origin` must be present and listed in `ALLOWED_ORIGINS`.
2. `X-CSRF-Token` must match `iesm_csrf` (constant-time compare).

`http://testserver` is included so pytest TestClient can mutate. Vite origin `http://localhost:5173` must stay on the list. Production must add the FastAPI Cloud origin.

Login itself does not require CSRF (no prior cookie contract). Logout does.

## Passwords

bcrypt via the `bcrypt` package. Login returns 401 for unknown email or bad password with the same message.

## Frontend

`fetch(..., { credentials: "include" })`. Login page prefills the demo account. Failed login shows `ApiError` with status and detail. Empty fields fail client-side before the network.

## Tests

- Unit: token hash length, revoke, expiry.
- API: cookies set, 401 without session, logout, missing CSRF, bad Origin.
- UI: empty email/password validation.

## Out of scope

Multi-user RBAC, password reset, SSO, JWT access/refresh tokens, Remember-me longer than 12 hours.



These above things can come into the scope if we plan to extend our codebase and start serving it as a documented product handling the reql-sensitive data.
As when it comes to add the auth layers, it is always be fruitful to decide the plans beforehand.
