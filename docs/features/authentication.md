# Feature: Authentication

## Intent

Only the ESMINCUBYTE HR Manager may see or change salary data. The app is a same-origin SPA. Credentials are not stored in JavaScript-accessible storage.

## Code

| File | Role |
|---|---|
| `app/api/routers/auth.py` | `POST /login`, `POST /logout`, `GET /me`. Sets/clears cookies. |
| `app/api/dependencies.py` | `get_current_user`, `require_csrf`. |
| `app/api/schemas/auth.py` | Login body and user out. |
| `app/services/auth.py` | Authenticate, create/resolve/revoke session, ensure HR user. |
| `app/core/security.py` | bcrypt, SHA-256 of session token, CSRF + Origin checks. |
| `app/database/models.py` | `User` and `Session` tables. |
| `frontend/src/lib/api.js` | `credentials: "include"` and `X-CSRF-Token` from `iesm_csrf`. |

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

1. `Origin` (or, if Origin is absent, the origin of `Referer`) must match this process (same host, including `X-Forwarded-Host` behind FastAPI Cloud) **or** be listed in `ALLOWED_ORIGINS`.
2. `X-CSRF-Token` must match `iesm_csrf` (constant-time compare).

Same-origin is allowed even when Cloud env never set `ALLOWED_ORIGINS`. That is why local logout worked (`http://127.0.0.1:8000` was on the default list) while [production](https://incubyteesm.fastapicloud.dev/) returned 403 `Invalid or missing Origin` until this check existed. Vite `http://localhost:5173` is a *different* origin from the API and must stay on the list. `http://testserver` is for pytest.

Login itself does not require CSRF (no prior cookie contract). Logout does.

## Passwords

bcrypt via the `bcrypt` package. Login returns 401 for unknown email or bad password with the same message.

## Frontend

`fetch(..., { credentials: "include" })`. Login page prefills the demo account. Failed login shows `ApiError` with status and detail. Empty fields fail client-side before the network.

The header **Log out** button (`AppLayout`) POSTs `/api/v1/auth/logout` with the CSRF header, then sets React user state to `null` so routes bounce to `/login`. If that POST fails, the catch keeps local state logged in (the server session is still valid) so the page does not look logged out while the cookie still works. Logout cookie deletes use the same `Path` / `SameSite` / `Secure` / `HttpOnly` flags as login so browsers actually drop them in production.

## Tests

- Unit: token hash length, revoke, expiry.
- API: cookies set, 401 without session, logout revokes and clears cookies, old cookie replay 401, missing CSRF, bad Origin.
- UI: empty email/password validation; Log out calls `api.logout` then `onLogout`.

## Out of scope

Multi-user RBAC, password reset, SSO, JWT access/refresh tokens, Remember-me longer than 12 hours.



These above things can come into the scope if we plan to extend our codebase and start serving it as a documented product handling the reql-sensitive data.
As when it comes to add the auth layers, it is always be fruitful to decide the plans beforehand.
