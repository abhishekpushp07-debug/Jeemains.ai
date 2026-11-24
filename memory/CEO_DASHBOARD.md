# JEELIVE.AI — CEO Dashboard handoff

> For the agent building the **separate CEO dashboard project**. This document is self-contained: it tells you what the
> JEELIVE.AI app already exposes, what to track, where every number comes from, and how to build the dashboard without
> touching the app or the website. Give this file (and the website project's own handoff) to the new dashboard agent.

Written by the app-side agent, 23 Nov 2026. The app code lives in this repo under `/app/backend` (FastAPI) and
`/app/frontend` (Expo). The CEO dashboard is a **new, separate** project; it only *reads* from the two servers below.

---

## 0. The one thing to understand first — two servers, one student id

There are **two** backends, and they own different data:

| Data | Who owns it | How the dashboard reads it |
|---|---|---|
| **Signups, phone numbers, PIN, email, which exam** (the real "contacts") | the **jeelive.ai website** backend (canonical) | website's own CEO/export endpoint — **the website agent must build this** (spec in §4) |
| **App engagement**: who is active, streaks, coins, Rapid Fire, series play | the **app server** (this repo) | app CEO API (§2), already built |

Both servers identify a student by the **same `uid`** (the canonical website user id). So the dashboard **joins on `uid`**:
contact details from the website + engagement from the app = one row per student.

**Why the app cannot give you phone numbers:** for privacy the app never stores them. Friend-search keeps only an
**HMAC hash + the last 4 digits**. Out of 619 app profiles, only ~2 even have `phone_last4`. The authoritative contact
list (full numbers, for marketing) is the website's — read it from the website, join on `uid`.

---

## 1. Base URLs

- App server (live): `https://jeelive-mobile.emergent.host/api`  — if the app's live address changes, use `<new>/api`.
- App server (preview, while unpublished): the project's current preview URL + `/api`.
- Website backend: the jeelive.ai website's own API base (the website agent will give you this + the export endpoint).

All app CEO endpoints are **GET, read-only, no cookies**, returned with `Cache-Control: no-store`.

---

## 2. App CEO API (already built in this repo: `backend/ceo_api.py`)

### Auth
One shared secret, server-to-server. Send it on every call:

```
Authorization: Bearer <CEO_API_TOKEN>
```

- `CEO_API_TOKEN` is a backend secret set by the owner (already configured). Keep it on the **dashboard server only**,
  never in the dashboard's browser code.
- No token configured → `503`. Wrong/missing token → `401`. So the API is closed by default.

### `GET /api/ceo/overview`
Headline numbers for the app.

```json
{
  "generated_at": "2026-11-23T22:00:00+00:00",
  "app_users": 619,
  "active": { "today": 1, "last_7_days": 138, "last_30_days": 142 },
  "on_streak": 249,
  "rapid_fire_players": 141,
  "best_streak_seen": 4,
  "contacts": "Signup phone numbers are not on this app server. … join on `uid`."
}
```

- `app_users` = app profiles that exist (anyone who used a profile-creating feature).
- `active.*` = profiles whose last active day (`last_day`, IST) falls in that window → **DAU / WAU / MAU**.
- `on_streak` = profiles with a current streak > 0.
- `rapid_fire_players` = profiles that have played Rapid Fire at least once (a solo session, a duel or a rival game).

### `GET /api/ceo/users`
The app's student directory, most-recently-active first. Paginated.

Query: `page` (default 1), `limit` (default 100, max 500), `active_since=YYYY-MM-DD` (only users active on/after this
day), `q` (search name or player code).

```json
{
  "total": 619, "page": 1, "pages": 7, "limit": 100,
  "items": [
    { "uid": "cfcc3ac4-…", "name": "Aarav", "player_code": "PF37CC308",
      "coins": 1632, "diamonds": 149, "current_streak": 3, "best_streak": 3,
      "last_active": "2026-11-22", "phone_last4": null }
  ],
  "contacts": "… join on `uid`."
}
```

- Use `uid` as the join key to the website's contact export.
- `phone_last4` is almost always `null` here — **do not** rely on the app for contact numbers.

### Adding more app metrics later
`ceo_api.py` is small and read-only. If the CEO wants, say, a Rapid Fire leaderboard or coins-economy totals, add another
`GET /api/ceo/<thing>` that reads `rf_profiles` / `rf_cups` / `rf_duels` the same way. Keep every CEO route behind
`_auth()` and `Cache-Control: no-store`.

---

## 3. What to track, and where each number comes from

| Metric | Source | How |
|---|---|---|
| **Total signups** | website | website export: count of accounts |
| **Signups over time** (daily/weekly) | website | website export: group by `created_at` |
| **Signups by exam** (JEE / BITSAT / COMEDK) | website | website export: group by `exam` |
| **Contact list for marketing** (name + number) | website | website export, filtered by marketing consent |
| **DAU / WAU / MAU** | app | `GET /api/ceo/overview` → `active.*` |
| **Students on a learning streak** | app | `overview.on_streak`, per-user `current_streak` |
| **Rapid Fire players & matches** | app | `overview.rapid_fire_players`; extend `ceo_api.py` for match counts |
| **Coins / diamonds economy** | app | `GET /api/ceo/users` (sum `coins` / `diamonds`) |
| **Most engaged students** | app | `GET /api/ceo/users?active_since=…`, sort by streak/coins |
| **All India Series participation & scores** | website (series lives there) | the website's own owner numbers (per-day attempts, average, topper); the app server holds no series results |
| **Signup → active conversion** | join | website signups ⨝ app `active` on `uid` |
| **Retention (cohorts)** | join | website `created_at` cohort ⨝ app `last_active` |

Rule of thumb: **counts of people and their contacts → website; what those people did in the app → app CEO API.**

---

## 4. Website side the dashboard needs (give this to the website agent)

> **Check first:** the website agent has said it is already computing owner numbers on the website server (for example
> each All India day's average and topper). If the website already has its own CEO / owner API, **its own document is
> the truth for its paths and fields**; use the proposal below only for what is still missing. Whatever the paths are,
> the three things that must hold are the same: every row carries the canonical `uid`, the token is server-to-server
> only, and marketing consent travels with the contact.

The website owns the contacts, so the website must expose a small read-only export the dashboard can call
server-to-server. Proposed, mirroring the app's CEO API:

```
GET /api/ceo/signups?page=&limit=&since=YYYY-MM-DD      (website backend)
Authorization: Bearer <WEBSITE_CEO_TOKEN>               (a secret only the website + dashboard share)
```

Return one row per account, enough to market and to join to the app:

```json
{
  "total": 12840, "page": 1, "pages": 129,
  "items": [
    { "uid": "cfcc3ac4-…", "name": "Aarav Sharma", "phone": "+9170xxxxxxx",
      "email": null, "exam": "JEE Main", "state": "UP",
      "created_at": "2026-11-20T06:11:00Z", "last_login": "2026-11-23T04:02:00Z",
      "marketing_opt_in": true }
  ]
}
```

Plus a daily rollup for the signup chart:

```
GET /api/ceo/signups/daily?days=90   →  [ { "date": "2026-11-20", "signups": 410, "by_exam": { "JEE Main": 300, … } } ]
```

Rules the website agent must follow (same posture as the app):
- **`uid` must be the same canonical id the app uses** (so the dashboard can join). This is the single most important field.
- Read-only. Never return or accept a PIN or password. The token is server-to-server only, never in browser code.
- Respect **marketing consent**: expose `marketing_opt_in` and let the dashboard filter on it before any campaign.
- `Cache-Control: no-store`, `Referrer-Policy: no-referrer`; token compared in constant time; closed by default when unset.

---

## 5. How to build the CEO dashboard (shape, not prescriptive)

- A **server-side** app (so the two bearer tokens never reach the browser). The browser talks only to the dashboard's
  own backend; the dashboard backend calls the app CEO API and the website export.
- Pages: **Overview** (signups, DAU/WAU/MAU, streak count, exam split), **Students** (searchable table: name, number,
  exam, last active, streak, coins — number from website, engagement from app, joined on `uid`), **Marketing**
  (consented contacts export / WhatsApp list), **Growth** (signup & retention cohorts).
- Caching: both APIs are no-store and cheap; the dashboard can poll every few minutes and cache its own copy.
- **Never** write to either server from the dashboard. It is a read-only mirror.

---

## 6. Security & privacy (do not skip)

- Contact numbers are personal data. Keep them on the dashboard server, behind the owner's login; never ship them to the
  browser in bulk, never log them, never put a token in a URL.
- Only market to `marketing_opt_in = true` students. The app's own stance is explicit ("No OTP; phone ownership is not
  verified; your PIN protects sign-in") — honour the same care here.
- Both tokens (`CEO_API_TOKEN` for the app, `WEBSITE_CEO_TOKEN` for the website) are rotated by re-issuing the secret;
  the dashboard reads them from its own environment, never from code.

---

## 7. Quick test (once the app is published and you have the token)

```bash
TOKEN=…   # the CEO_API_TOKEN value
curl -s https://jeelive-mobile.emergent.host/api/ceo/overview -H "Authorization: Bearer $TOKEN"
curl -s "https://jeelive-mobile.emergent.host/api/ceo/users?limit=20&active_since=2026-11-01" -H "Authorization: Bearer $TOKEN"
```

No token → 503 (not configured) or 401 (missing/invalid). A valid token → JSON above.
The app CEO API answers on the **preview** URL immediately; on the **live** URL after the app project's next publish.
