# Backend and native transport contract

## What exists
FastAPI serves `/api/...`; React is a separate client. A native HTTP client can use the same endpoints. MongoDB and private source storage stay server-side. CORS is a browser policy, not a requirement to rewrite these APIs for Android.

Native requests normally send **no Origin header**. The current write fence rejects an explicitly supplied untrusted Origin; it does not reject a request merely because Origin is absent. Do not send `null`, `file://` or a fabricated origin. Do not weaken backend CORS/CSRF checks. HTTPS only; no permissive trust manager, disabled TLS validation or cleartext release configuration.

## Sessions: cookies, not bearer
- `POST /api/auth/phone` with `{ "phone": "[USER_ENTERED_PHONE]" }` is existing learner convenience access. It creates/opens an **unverified_phone** profile. No OTP is sent or checked. Indian national-format parsing is supported by the current backend; international numbers require their country code. Do not infer the user's country from this.
- `POST /api/auth/login` is the existing approved **staff** email/password login, not public student registration. `POST /api/auth/register` is closed; do not offer open signup.
- Successful sign-in returns user details and **Set-Cookie** headers. Cookies are `access_token` (15 minutes) and `refresh_token` (7 days), Secure, HttpOnly, SameSite=Lax, Path=/.
- Preserve both cookies in one trusted-host HTTPS cookie jar shared by JSON and binary image requests. Host-only cookies for jeelive.ai must not be copied to another domain. Redirects must not forward session credentials to untrusted hosts.
- Do not parse JWTs to grant roles or expose tokens in Compose state, URLs, logs, crash reports or analytics. Use server user data; server authorization is authoritative.
- Persist cookie material only in appropriately protected per-install storage using Android Keystore-backed protection; exclude it from backups and exported files. On logout clear the cookie jar and decoded image memory. Pending answer drafts require an explicit keep/discard choice and stay partitioned by the same user ID.
- `GET /api/auth/session` returns `{user: ...}` or `{user:null}`. It is useful for a cold start and can rotate cookies through the existing refresh cookie. Always process Set-Cookie responses, not only login responses.
- `GET /api/auth/me` returns the authenticated user or 401.
- On 401, single-flight `POST /api/auth/refresh` with `{}` and the refresh cookie, then retry the original request **once** with the original immutable body/request_id. Prevent concurrent refresh storms and infinite auth loops. If refresh fails, keep unacknowledged drafts safely and ask the user to sign in again.
- `POST /api/auth/logout` with `{}` invalidates the current session and clears cookies. Do not log out other devices by clearing arbitrary server sessions.
- `PATCH /api/auth/preferences` currently accepts only `JEE Main` or `BITSAT`; do not send COMEDK to this preference endpoint just because a COMEDK catalogue exists. COMEDK can still be browsed by its catalogue slug.

## JSON envelope and errors
The regular JSON response is:
```json
{"data":{"example":"payload"},"error":null,"meta":{"api_version":"1","request_id":"[SERVER_REQUEST_ID]"}}
```
Errors use:
```json
{"data":null,"error":{"code":"validation_error","message":"[SAFE_MESSAGE]"},"meta":{"api_version":"1","request_id":"[SERVER_REQUEST_ID]"}}
```
DTOs in OpenAPI describe the **inner data**, unless explicitly noted. Generated Retrofit DTOs must account for the envelope. Binary PNG/PDF responses are NOT JSON wrapped. Do not blindly unwrap binaries or double unwrap JSON. API v1 is metadata; URLs remain `/api`, not `/api/v1`.

Use exact JSON types; many writes forbid unknown keys and coercion. Most learner JSON write budgets are 4096 bytes, recorded as `x-body-limit-bytes`. Do not send nested duplicate keys, compressed JSON bodies, NaN/Infinity, or extra role/user/tenant fields. Use Content-Type: application/json. Server authorizes the user from its session, not a client-supplied user_id.

- 200/201: accepted/read success as specified.
- 202: still pending (not failure), especially submit/grading. Respect `Retry-After` and state fields.
- 400/422: fix input; don't retry unchanged.
- 401: one refresh attempt, then reauthenticate.
- 403/404: unavailable/forbidden; do not bypass by changing roles or identifiers.
- 409: conflict, closed attempt, embargo/state or stale revision. Preserve drafts, reload authoritative state and explain; do not blindly increment revision and overwrite newer work.
- 410: deliberately unavailable legacy AI-generation route; do not retry or expose a Generate action.
- 413/415: request budget/media error.
- 429/503: bounded retry with `Retry-After` and jitter, preserving the exact immutable save command. `capability_held` must NOT become a rapid retry loop.

## Native compatibility conclusion
No browser-only dependency prevents a native client from calling the current JSON/cookie/PNG APIs. Backend rewrite or direct DB access is unnecessary for a first native client. **This is source/schema compatibility analysis, not an emulator or real-device end-to-end certification.** Verified phone identity and release testing remain unresolved prerequisites.
