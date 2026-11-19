# 02 · Connect guide

How the website calls the app server. Everything here was run against the live server while this pack was made.

## 1. Addresses

| Server | API root | Use |
|---|---|---|
| Live | `https://jeelive-mobile.emergent.host/api` | Always, unless you are testing unreleased app-server work |
| Development | `https://handoff-zip-hub--8kn8pvyh.preview.emergentagent.com/api` | Unreleased work only. It sleeps when idle and its address changes when the workspace is recreated |

Both serve the same code and data today and return identical numbers. All paths below are relative to the API root.

## 2. What needs sign-in

| Area | Paths | Sign-in |
|---|---|---|
| Rank | `/rank/*` (14 endpoints + 7 PDFs) | none: no account, no key, no cookie |
| Share link | `/j/{code}` | none: opened by a friend's browser |
| Mission stats | `/rf/mission/me` | a 15-minute pass |
| Dream college | `/rf/dream`, `/rf/dream/dreams`, `/rf/dream/mocks`, `/rf/dream/cheered` | a 15-minute pass |
| The pass | `/rf/access`, `/rf/access/revoke` | exchanges the website session for the pass |

## 3. Two ways to connect

Both read every number from the app server. The website never keeps its own copy of the data (`docs/05_RANK_DATA.md` §1).

| | A · Connector on the website backend | B · Browser calls the app server |
|---|---|---|
| What you add | `jeelive_app_connect.py` (one file) | nothing on the backend |
| Rank | yes | yes, only from an allowed origin |
| Mission, Dream college | yes | no (the session cookie is HttpOnly) |
| Works from preview / staging | yes | no |
| CORS | not involved | must be allowed per origin |
| Yearly data renewal | automatic (the app server's) | automatic |
| **Use it** | **Recommended. Start here.** | Only as a production shortcut for Rank |

The rest of this guide describes A, then gives the facts for B.

## 4. Way A: the connector

### 4.1 Mount it

```python
# website backend, next to the other routers
from jeelive_app_connect import router as jeelive_app_router, close as close_jeelive_app

api_router.include_router(jeelive_app_router)          # api_router has prefix "/api"
app.add_event_handler("shutdown", close_jeelive_app)
```

It needs `fastapi` and `httpx`. It adds these routes to the website's own origin:

| Website route | Forwards to (app server) | Notes |
|---|---|---|
| `GET /api/rank/meta`, `/colleges`, `/target/bitsat` | same path | kept in memory for 10 minutes; `Cache-Control: public, max-age=300` |
| `POST /api/rank/…` (11 JSON endpoints) | same path | status and JSON passed through word for word |
| `POST /api/rank/pdf/…` (7) | same path | `application/pdf` with the server's file name; 30 s limit |
| `GET /api/mission/me` | `/rf/mission/me` | adds `link`; `Cache-Control: no-store` |
| `GET /api/dream`, `PUT /api/dream/dreams`, `POST /api/dream/mocks`, `POST /api/dream/cheered` | `/rf/dream…` | signed-in |
| `GET /api/j/{code}` | redirect to `/j/{code}` | optional pretty share link (§8) |

Only the listed paths are forwarded. Anything else is a 404 at the website and never reaches the app server.

### 4.2 Settings

All optional (`CONNECT/.env.example`):

| Variable | Default | Meaning |
|---|---|---|
| `JEELIVE_APP_API` | the live API root | where the connector sends requests |
| `JEELIVE_SESSION_COOKIE` | `access_token` | the website cookie that holds the student's session |
| `JEELIVE_SHARE_LINK_BASE` | `<JEELIVE_APP_API>/j` | the start of a student's personal link |
| `JEELIVE_SITE_URL` | `https://jeelive.ai` | where a malformed share link lands |

### 4.3 The browser side

```ts
import { createJeeliveApp, JeeliveError } from "./jeeliveApp";

const app = createJeeliveApp();                      // baseUrl "/api"

try {
  const out = await app.rank.predict({ marks: 180, level: "normal", category: "GEN", female: false, pwd: false,
                                       state: "Bihar", branches: [], segment: "all", page: 1 });
} catch (e) {
  if (e instanceof JeeliveError) show(e.message);    // already a sentence for the student
}
```

## 5. Sign-in for Mission and Dream college

The app server never sees a phone number or PIN and never trusts a user id sent by a caller. It accepts one thing: a
session that the website itself confirms.

```
 Browser                 Website backend (connector)            App server                       Website /api/auth/me
    │  GET /api/mission/me        │                                  │                                   │
    │  Cookie: access_token=S     │                                  │                                   │
    ├────────────────────────────►│  POST /rf/access                 │                                   │
    │                             │  {"access_cookie": "S"}          │                                   │
    │                             ├─────────────────────────────────►│  GET /auth/me   Cookie: access_token=S
    │                             │                                  ├──────────────────────────────────►│
    │                             │                                  │◄──── {"data": {"id": "<student>"…}}│
    │                             │◄── {"token","user_id","expires_at"} (15 minutes)                     │
    │                             │  GET /rf/mission/me              │                                   │
    │                             │  Authorization: Bearer <token>   │                                   │
    │                             ├─────────────────────────────────►│                                   │
    │◄── {code, helped, week, link}◄──── {code, helped, week} ───────│                                   │
```

Details that matter:

- **`POST /rf/access`** body `{"access_cookie": "<value of the access_token cookie>"}` → `200 {"token", "user_id", "expires_at"}`.
  `expires_at` is ISO 8601 UTC, 15 minutes ahead. Missing, malformed or rejected cookie → `401 {"detail": "Your canonical session needs refreshing."}`.
  Website unreachable → `503 {"detail": "Could not verify your session. Please retry."}`.
- **Send the pass** as `Authorization: Bearer <token>` on every `/rf/…` call. No pass or an expired one → `401`.
- **The connector keeps the pass in memory**, keyed by a SHA-256 of the cookie, until one minute before it expires. On
  a `401` it asks for one new pass and retries once. It never writes the cookie or the pass to disk or to a log.
- **`POST /rf/access/revoke`** with the bearer header ends a pass early (use it at sign-out if you want). Always `200 {"ok": true}`.
- **What `/auth/me` must keep returning:** either `{"data": {"id": "..."}, "meta": {"api_version": ...}}` or a plain
  `{"id": "..."}`. The `id` is the student's permanent website id; the app server keys Mission and Dream data by it.
- Every signed-in answer carries `Cache-Control: no-store`.

If the website keeps its session somewhere other than a cookie named `access_token`, replace the one function
`session_cookie(request)` in the connector, or set `JEELIVE_SESSION_COOKIE`.

## 6. Errors and what to show

Every error is JSON with one key, `detail`.

| Status | `detail` | Meaning | Show |
|---|---|---|---|
| 422 | a **sentence**, e.g. `"Marks ya percentile mein se koi ek daalo."` | a rule of the tool was broken | the sentence, under the form |
| 422 | a **list** `[{"loc": ["body","marks"], "msg": "Input should be less than or equal to 300", …}]` | a field has the wrong type or range | your own field message; validate before sending so this never appears |
| 404 | `"College nahi mila."` | unknown institute number or college code | the sentence, with Retry |
| 401 | `"Please sign in again."` (connector) | no valid website session | your sign-in prompt |
| 413 | `"Request too large"` (connector) | body over 16 KB | should never happen |
| 503 | `"Rank abhi load nahi hua. Retry dabao."` (connector) | app server unreachable, slow or failing | the sentence, with a Retry button |

The browser client turns all of these into `JeeliveError(message, status)`; `message` is ready to display.

Client-side timeouts the app uses, and the client in this pack copies: 15 s for JSON, 30 s for a PDF. A timeout reads
"Network kamzor hai. Retry dabao."

## 7. Caching and load

- `GET /rank/meta`, `GET /rank/colleges`, `GET /rank/target/bitsat` change only when the app server is redeployed with
  new data. Fetch once per visit; the connector also keeps them for 10 minutes.
- `POST` answers depend only on the request body. You may memoise them in the page for the session. The server itself
  remembers the last 512 different forms.
- There is no rate limit on `/rank/*` today. Please keep it that way: call on "Show", not on every key press.
- Mission and Dream answers are per student: never cache them in a shared cache.

## 8. Share links: two choices

A student's link must end at the app server's counter, opened by the friend's own browser.

| Choice | The link students share | Setup |
|---|---|---|
| Direct (default) | `https://jeelive-mobile.emergent.host/api/j/AB2CDEF` | none |
| Website address | `https://jeelive.ai/api/j/AB2CDEF` | keep the connector's `/j/{code}` route; set `JEELIVE_SHARE_LINK_BASE=https://jeelive.ai/api/j` |

With the second choice the friend's browser makes two hops (website → app server → `https://jeelive.ai`). Both are
plain 302 redirects. Never fetch the counter from the website's server instead of redirecting: the counter would see
the server's address and count nobody (`docs/07_MISSION.md` §4).

Links already shared from the app keep working either way.

## 9. Prove the connection

```bash
python CONNECT/connect_check.py                                   # live app server, 21 checks
python CONNECT/connect_check.py --pdf                             # + the 7 PDFs
python CONNECT/connect_check.py https://<website>/api --website   # through the mounted connector

# with a signed-in student's session, the 3 signed-in checks run too
JEELIVE_ACCESS_COOKIE='<access_token cookie>' python CONNECT/connect_check.py https://<website>/api --website
```

If a check fails:

| You see | Cause | Fix |
|---|---|---|
| every check fails with a network error | wrong address, or the development server is asleep | use the live root; open the development app once to wake it |
| `HTTP 404` on `/rank/...` through the website | the connector is not mounted under `/api` | mount it on the router that has the `/api` prefix |
| `HTTP 401` on the signed-in checks | the cookie is not a live website session, or it expired | sign in again in a browser and copy the fresh cookie |
| `HTTP 503` on the signed-in checks | the app server could not reach the website's `/api/auth/me` | check the website is up; retry |

`CONNECT/curl_examples.sh` has every call as a single curl line. `CONNECT/openapi_rank_mission.json` describes the same
API for tools that read OpenAPI.

## 10. Way B: the browser calls the app server directly

Possible for Rank only.

- The app server allows cross-origin calls from a fixed list of origins. On the live server that list contains exactly
  `https://jeelive.ai`. A page on any other origin (a preview address, `www.`, `localhost`) fails the browser's
  pre-flight with HTTP 400.
- To add an origin, the app project adds it to its `CORS_ORIGINS` setting (comma-separated) and redeploys. Send the
  exact origin: scheme, host, and port if any.
- Use `createJeeliveApp({ baseUrl: "https://jeelive-mobile.emergent.host/api" })`. Call only `app.rank.*`.

## 11. Security notes

- All traffic is HTTPS. The connector validates the session cookie's shape before forwarding and whitelists paths.
- The session cookie crosses one extra hop (website backend → app server). The app server uses it for a single call to
  the website's `/api/auth/me` and does not store it.
- The pass is random (256 bits), stored on the app server only as a SHA-256, valid 15 minutes, and useless on the website.
- Rank is public by design: it reveals nothing that is not published by the counselling bodies.
- No secret of any kind is needed in the browser.
