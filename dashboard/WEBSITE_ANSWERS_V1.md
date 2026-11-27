# WEBSITE_ANSWERS_V1 — jeelive.ai ↔ "JLive Command" (CEO dashboard)

Read-only inspection, 2026-11-28 (IST). No code, data or settings were changed. No key value is printed here.
How it was checked: repository files, the website's own public endpoints, the CEO API on https://jeelive.ai (GET only,
with the shared key; nothing written), public DNS/RDAP. The deployment tool could not see the production
deployment, so anything that needs direct production database access is marked **unsure**.
CEO API code: `backend/tejas/ceo.py`. Contract: `memory/CEO_DASHBOARD_HANDOFF_WEBSITE.md` section 9.

---

## A. CEO API IN PRODUCTION

### 1. Is ceo.py published? Is CEO_DASHBOARD_KEY set in production?
- **ceo.py is live on https://jeelive.ai, in its latest version.** With the key, all 12 endpoints answer 200 on production:
  `/summary /daily /funnel /retention /aits /content /health /alerts /students /students/{id} /contacts /events`.
  The last change to `ceo.py` (commit `56249b6`, 2026-11-25: `/health` → `storage.level`) is visible on production
  (`/health` returns `storage {alert, checked_at, level, mode}`).
- Whether every later non-CEO commit (repo HEAD `7f01db0`, 2026-11-27) is also published: **unsure** (no deploy history visible).
  The live bundle is `/static/js/main.8e48d0f3.js` and contains the tracking code (`jl.src`, `jl.vid`, `page_open`, `utm_campaign`).
- **CEO_DASHBOARD_KEY: yes, set in production.** Without a key production answers `401 "CEO key galat hai."`
  (if it were missing it would answer `503 "CEO dashboard ki key abhi set nahi hai…"`, `ceo.py` lines 23–25).
  Secrets list: live slot present, mode **shared** (same value in preview and live), updated 2026-11-23 22:36 UTC.

### 2. CEO_EXCLUDE_PHONES in production? How many numbers?
- **Yes.** Live slot present, mode **shared**, same update time as the preview value (2026-11-23 22:36 UTC).
- **1 number** (counted from the shared value; no value shown). Read in `ceo.py` `left_out()` lines 80–87.
  A 10-digit Indian number is matched as `+91XXXXXXXXXX`; anything else must match the stored E.164 exactly.

### 3. Do /students and /contacts LISTS exclude staff, TEST_ names and CEO_EXCLUDE_PHONES?
- **/students (list) — yes, same rule as the counts.** `match = {'id': {'$nin': out['students']}}` (`ceo.py` line 414).
  `total` and `items` both use it. Staff are never in this list anyway: staff live in `tejas_users`, students in
  `tejas_phone_profiles` (separate collections).
- **/students/{id} — yes.** An excluded student answers 404 (line 428).
- **/contacts (list) — yes, by the person who shared.** `match = {'user_id': {'$nin': out['all']}}` (line 455; `all` = excluded
  students + every staff id). Note: a row is NOT removed when the *friend's* number itself is in CEO_EXCLUDE_PHONES; only the
  sharer is checked. `already_student` / `student_id` ignore excluded students (line 462).
- **/events** also excludes left-out user ids (line 482), but anonymous (signed-out) visits are kept by browser id only,
  so the owner's own signed-out browsing can still be counted. Staff visits are never stored at all (`activity.py` line 26).
- The exclusion list is cached for 60 s (line 87), so a new TEST_ name or number takes up to 1 minute to drop out.

### 4. /students?sort=new — exact sort keys, tie-break?
- `sort=new` → `[('created_at', -1)]` only (`ceo.py` line 416). **No tie-break on id.**
- `sort=active` → `[('last_active_at', -1), ('last_seen_at', -1)]`. **No tie-break on id.**
- Paging is offset paging: `skip((page-1)*100).limit(100)` (line 417). **Not stable while new sign-ups arrive** — a new
  sign-up pushes every row down by one, so the next page repeats one row. The dashboard should de-duplicate by `id`
  (or re-read from page 1). `created_at` is epoch seconds with fractions (`time.time()`), so exact ties are rare but possible.

### 5. Production counts right now (read-only, via the CEO API, 2026-11-28 03:37 IST, after exclusions)
| Item | Production |
| --- | --- |
| Students total | **6** |
| Blocked | **0** |
| By signup_channel | **web 1, app 0, other 4** (+1 student with no `signup_channel` — an older profile; the 3 buckets sum to 5, not 6) |
| Attempts total | **7** (all 7 completed; `/daily` over 391 days and the `/students` per-student sums agree) |
| Contacts total (`tejas_invite_contacts`) | **0** (0 students shared) |
- These are the dashboard's numbers (staff, TEST_ names and the 1 excluded number left out). Raw totals including staff and
  the excluded number: **unsure** (no direct production database access).
- Note on "other" = 4: `signup_channel` is `web` only when the request carries `Sec-Fetch-*` or `Origin`, `app` only when the
  user-agent contains `httpx`/`okhttp`/`expo`, otherwise `other` (`backend/tejas/phone.py` `signup_origin()` lines 37–47).
  Why 4 sign-ups landed in `other` (e.g. app-server sign-ups with another user-agent, or scripts/tests): **unsure**.

### 6. Rate limits / caching on /api/ceo/v1; IP allow-list?
- **Server-side answer cache** (in-process memory, `ceo.py` `cached()` lines 65–73, max 200 entries, reset on restart):
  | Endpoint | Cache |
  | --- | --- |
  | `/summary`, `/health`, `/alerts` | 60 s |
  | `/daily`, `/events` | 120 s (per from/to) |
  | `/funnel`, `/aits` | 300 s |
  | `/retention`, `/content` | 600 s |
  | `/students`, `/students/{id}`, `/contacts` | **no answer cache** (live query each call; only the exclusion list is cached 60 s) |
- **Browser/proxy caching:** none. Production sends `Cache-Control: private, no-store` (set for every `/api/*` answer by
  `backend/server.py` `Protections`, lines 130–186).
- **Rate limit:** only for wrong keys — 20 wrong keys from one IP in a 10-minute slot → `429` for the rest of that slot
  (`ceo.py` lines 26–35). A correct key has **no limit**. Polling every 5 minutes is fine.
- **IP allow-list: none** in the code. Edge (Cloudflare) rules outside the repo: **unsure**.

---

## B. FRONTEND (for tracking)

### 7. Stack, router, every route → file
- React 19 (`react`, `react-dom` ^19.0.0), Create React App (`react-scripts` 5.0.1) via `@craco/craco` ^7.1.0,
  `react-router-dom` ^7.5.1 with `BrowserRouter` (clean paths, no `#`). Routes: `frontend/src/App.js` lines 153–237.
  Pages: `frontend/src/features/*.js`.

| Path | File | Note |
| --- | --- | --- |
| `/` | `features/Landing.js` | landing |
| `/login`, `/signup`, `/forgot-pin` | `features/Auth.js` | student phone + PIN |
| `/owner-login` | `features/Auth.js` (`staff`) | staff email + password |
| `/home` | `features/Home.js` | signed-in |
| `/exams` | `features/Exams.js` | |
| `/exams/:examSlug` | `features/ExamHub.js` | signed-in |
| `/exams/:examSlug/mocks` | `features/ExamSection.js` (`kind="mocks"`) | |
| `/exams/:examSlug/chapters` | `features/ExamSection.js` (`kind="chapters"`) | |
| `/exams/:examSlug/:sectionSlug` | `features/ExamSection.js` | |
| `/exams/:examSlug/results` | `features/ExamHistory.js` | exam results history |
| `/exams/jee-main/pyq` | `features/PyqCatalogue.js` | PYQ |
| `/sets/:id` | `features/SetDetail.js` | paper / set page |
| `/attempts/:id` | `features/Player.js` (via `PlayerRoute`) | test player (no header/footer) |
| `/results/:id` | `features/Results.js` | result + analysis (`components/results/ResultsAnalyticsWorkspace`, `components/analysis/AnalysisWorkspace`) |
| `/series/all-india-jee` | `features/LiveSeries.js` | AITS hub; the 50 days are shown here (no separate "day" route; a day's paper opens at `/sets/:id` → `/attempts/:id`) |
| `/series/all-india-jee/analysis` and `/series/all-india-jee/analysis/:attemptId` | `features/SeriesAnalysis.js` | AITS analysis |
| `/series/:seriesId` | `features/SeriesPage.js` | other exams' series |
| `/profile` | `features/Profile.js` | "My Tests" lives here |
| `/my-tests` | redirect → `/profile` | |
| `/misfire` | `features/Misfire.js` | |
| `/rank` | `features/Rank.js` | open without login |
| `/mission` | `features/Mission.js` | signed-in |
| `/saved-drafts` | `features/SavedDrafts.js` | |
| `/book-series`, `/book-series/:id` | `features/BookSeries.js` | |
| `/competitions`, `/competitions/:id`, `/competitions/:id/compare/:key` | `features/Competitions.js`, `features/Compare.js` | |
| `/preview/s/:token` | `features/SectionPreview.js` | |
| `/privacy`, `/accessibility` | `features/Info.js` | |
| `/super-admin/*`, `/studio…` | `features/admin/AdminWorkspace.js`, `features/ChapterBookStudio.js`, `features/StudioImport.js` | staff only |
| `*` | inline "This page isn't here" in `App.js` | |

### 8. Where the student id becomes known; where sign-out happens
- **Single place: `frontend/src/lib/auth.js` `AuthProvider`.** The id is `user.id` from `useAuth()`.
- **After sign-in / sign-up / forgot-PIN:** `frontend/src/features/Auth.js` `submit()` lines 37–63 —
  `const u = await postWhenFree(path, body); setUser(u);` → `lib/auth.js` `setUser` (line 12).
- **On page reload:** `lib/auth.js` `useEffect` lines 13–16 — `api('/auth/session')` → `commitUser(data.user)`.
- Every identity change also calls `resetPrivateResources(id)` (lines 12, 14, 25) — a natural single hook point.
- **Sign-out:** `lib/auth.js` `logout()` lines 18–26 (`POST /auth/logout`, then `commitUser(null)`), triggered by
  `frontend/src/components/Shared.js` line 54 `signOut()`. Other implicit sign-outs (e.g. an expired session): **unsure**.

### 9. Existing POST /api/events — who sends what today
- Sender: `frontend/src/lib/track.js` `track(name, props)` (fetch, `keepalive`, never blocks). Receiver: `backend/tejas/activity.py`.
  Allowed names: `backend/tejas/request_contracts.py` line 389.

| Event | Sent from | Props |
| --- | --- | --- |
| `page_open` | `App.js` line 144 `trackPage(loc.pathname)` on every route change; page names from `lib/track.js` lines 6–9 | `page`: landing, home, rank, mission, aits_analysis, aits, my_tests, misfire, result, test, paper, pyq, exams, competitions, books, profile, signup, login |
| `rank_tool_open` | `features/Rank.js` line 52 | `tool` |
| `mission_share` | `features/Mission.js` line 15 (share button) | — |
| `contacts_pick` | `components/mission/ContactInvite.js` line 32 | — |
| `pdf_download` | **nobody** — accepted by the backend, but no page sends it today | — |
- Paths not in the map (super-admin, studio, saved-drafts, privacy, preview) send nothing. A repeat of the same path within
  2 s is dropped. Server: staff not stored, 120 events per person per 10 min, kept 400 days (`activity.py` lines 13–30).

### 10. Content-Security-Policy / security headers; would the dashboard script be blocked?
- **There is no Content-Security-Policy** on jeelive.ai — not in the live HTML response headers, not as a `<meta>` in
  `frontend/public/index.html`, not in the backend. So there is no `script-src` and no `connect-src`.
- **Loading a script from https://student-radar-5.emergent.host and POSTing to it would NOT be blocked by jeelive.ai.**
  The only condition is on the dashboard side: its server must answer CORS for `https://jeelive.ai` (or the page uses
  `navigator.sendBeacon` / a "simple" `text/plain` POST, which needs no preflight).
- Headers seen on the live HTML (`server: cloudflare`): `strict-transport-security`, `x-frame-options: SAMEORIGIN`,
  `x-content-type-options: nosniff`, `referrer-policy`, `x-xss-protection`, `expect-ct`. These come from the hosting edge, not
  from this repo (exact place outside the repo: **unsure**).
- `/api/*` headers are set in `backend/server.py` `Protections` lines 130–186: `X-Content-Type-Options`, `Referrer-Policy`,
  `Cache-Control: private, no-store`, `X-Robots-Tag: noindex, nofollow`, `X-Frame-Options: DENY`, `Permissions-Policy`.
  The same class rejects cross-origin writes to jeelive.ai's own API (`403 origin_denied`), and CORS allows only
  `FRONTEND_URL` + `CORS_ORIGINS` (wildcard ignored, `backend/tejas/origins.py`). This matters only if a browser on another
  site tried to write to jeelive.ai's API.

### 11. Google Analytics / gtag / pixels? Where is the head template?
- **No Google Analytics, gtag, Tag Manager, Meta pixel, Clarity or Hotjar** — not in `public/index.html`, not in `src/`,
  not in the live HTML.
- **PostHog is present:** `frontend/public/index.html` lines 64–134, `posthog.init("phc_…", { api_host:
  "https://us.i.posthog.com", person_profiles: "identified_only", session_recording: {...} })`. The app code never calls
  `posthog.identify` or `capture` (no use in `src/`). It looks like the platform template's snippet.
- Also loaded: `https://assets.emergent.sh/scripts/emergent-main.js` (line 26); inside an iframe only, `debug-monitor.js`
  and the Tailwind CDN (lines 30–49).
- Head template: **`frontend/public/index.html`**.

---

## C. SIGN-UP SOURCE, MISSION, CONSENT

### 12. signup_source — what is captured, how long, first-touch?
- Captured by `frontend/src/lib/track.js` `captureSource()` (lines 38–50), called once on app start (`App.js` line 143):
  - `utm_source`, `utm_medium`, `utm_campaign` (only if they match `^[A-Za-z0-9 ._+-]{1,80}$`)
  - `referrer` = hostname of `document.referrer` when it is another site
  - `landing` = first path (no query string)
  - **Not captured:** `utm_content`, `utm_term`, `ref`, any Mission code, gclid/fbclid.
- Kept in `localStorage` key **`jl.src`** with **no expiry** (until the browser storage is cleared). It is not removed after sign-up.
- **Strict first-touch per browser:** if `jl.src` exists, nothing is captured again — even if the first visit had no UTM
  (it stores `{landing: …}` or `{}`), later campaign links on that browser are ignored.
- Sent once at sign-up: `features/Auth.js` line 45 `...withSource()` → `POST /api/auth/phone/signup` `{source}` →
  `backend/tejas/request_contracts.py` `SignupSource` (lines 64–75) → `backend/tejas/phone.py` `signup_origin()` →
  `tejas_phone_profiles.signup_source`. Production today: 1 of 6 students has a `signup_source`.
- Whether the app server sends a `source` for app sign-ups: **unsure**.

### 13. Mission link → where does the friend land on the website? Is the code kept?
- Website route `GET /api/j/{code}` (`backend/tejas/app_connect.py` lines 233–236):
  a valid code (`^[A-Za-z2-9]{7}$`) → `302` to the APP server `{JEELIVE_APP_API}/j/{CODE}`; anything else → `302` to
  `https://jeelive.ai` (`JEELIVE_SITE_URL`). Checked live: an invalid code goes to `https://jeelive.ai`.
  This hop sends `Referrer-Policy: no-referrer`.
- Where the APP server then sends the friend (which website URL, with which parameters): **unsure** — that is app-server
  code, not in this repo, and it was not called (to avoid counting a fake click).
- **The code is not kept at sign-up.** `captureSource()` keeps only utm_source/medium/campaign, referrer host and the
  landing path (no query string). The events schema has a `props.ref` field, but nothing sends it today.

### 14. Marketing consent (WhatsApp / SMS / calls / email)?
- **No opt-in of any kind exists today** for WhatsApp, SMS, calls or email.
- What exists: (a) a privacy line under the sign-up/sign-in form (`features/Auth.js` lines 203–210) and a `consent_at`
  time stamped at sign-up (`backend/tejas/phone.py` line 168) — storage/privacy acknowledgement, not marketing;
  (b) `consent: 'student_picked_contact_picker_v1'` on friend contacts (`backend/tejas/contacts.py` line 14) — about
  saving the friends a student picked, not about messaging the student.
- Where a per-channel opt-in could be added:
  - Sign-up form: `frontend/src/features/Auth.js` (the `signup` branch of the form, lines 112–192); backend body
    `PhoneSignupPayload` in `backend/tejas/request_contracts.py` (lines 73–75) and `signup()` in `backend/tejas/phone.py` (lines 158–173).
  - Profile: `frontend/src/features/Profile.js` (header block lines 35–36, which already holds `components/DisplayName.js`
    and `components/ChangePin.js`). **There is no separate settings page.**

### 15. Do students ever give an email?
- **No.** Students use mobile number + 4-digit PIN only (`features/Auth.js`). `PhoneProfile` has no email field
  (`backend/tejas/phone.py` lines 20–34). The only email field is the **staff** login (`Auth.js` lines 115–123, `LoginPayload`).
  Preview database: 0 student profiles with an email field.

---

## D. DATA RULES

### 16. AITS dates, times, "today's day"
- **Production (public endpoints, read-only):** `GET https://jeelive.ai/api/series` (reads the `tejas_series` document) →
  `first_date 2026-12-09`, `last_date 2027-01-27`, `total 50`, `open_time 00:01`, `last_start 20:59`.
  `GET /api/series/all-india-jee` → day 1 opens 2026-12-09 00:01, last start 20:59, closes 23:59, archive from 00:00 next day (IST).
- Code: `backend/tejas/live_series.py` lines 13–17 (`SERIES_ID 'all-india-jee-2026-27'`, `FIRST = date(2026,12,9)`,
  `TOTAL = 50`) and line 25 (`JEE_TIMES`). The `tejas_series` document is seeded from the same values
  (`backend/tejas/series_admin.py` lines 18–19, 53–55) and the built-in JEE series cannot change its dates/times (line 284–285 → 409).
- **"Today's day":** IST calendar date. Student pages use the database clock (`canonical.database_now()` = MongoDB
  `hello.localTime`) → `datetime.fromtimestamp(t, Asia/Kolkata).date()`. The CEO API uses the server clock (`db.now()` =
  `time.time()`) → IST date, and day number = `(today − 2026-12-09).days + 1` (`ceo.py` line 136).
  State per day (`live_series.phase()`): upcoming → live (until last start) → start_closed → ended → archive.
- A live day counts when the `series_live` paper is submitted on the same IST day (`ceo.py` line 109).
- ⚠ Production `/aits` today: `stage prelaunch`, **`papers_ready 0`**, `next_day_without_paper 2026-12-09`.

### 17. Staff accounts: how many? Any staff with a student profile?
- Production count: **unsure** (the CEO API does not expose staff; no direct production database access).
- Preview: **1** staff account (role `owner`).
- Staff (`tejas_users`, email + password) and students (`tejas_phone_profiles`, phone + PIN) are separate collections with
  separate ids. Preview: 0 overlaps. Production: **unsure** — a staff member who also signed up with their own phone would be
  counted as a student unless that number is in CEO_EXCLUDE_PHONES or the name starts with `TEST_`.

### 18. Account deletion
- **Students cannot delete their account today** — no route and no button.
- Owner **block** (`backend/tejas/students.py` lines 58, 72–73): sets `blocked_at`; the profile, attempts and contacts
  stay; sign-in is refused. CEO API: still counted in `students.total`, also in `students.blocked`, and `blocked: true` in lists.
- The only hard delete is the owner's QA tool `POST /api/admin/qa/test-accounts/remove` (`backend/tejas/qa_cleanup.py`):
  phone prefix + "signed up after" time, dry run by default, confirm text required. It deletes the profiles, their attempts,
  `tejas_events`, `tejas_invite_contacts` and 12 other per-student collections. Because the CEO API computes everything live,
  such students simply disappear: counts drop (also in past `/daily` rows) and `/students/{id}` answers 404.
- Privacy page (`features/Info.js` ~lines 118 and 138): no fixed automatic deletion period.

### 19. Preview vs production — different databases?
- **Yes, different.** Preview uses the pod's own MongoDB (`mongodb://localhost:27017`, `DB_NAME test_database`).
  Production `MONGO_URL` / `DB_NAME` are platform-managed (values not visible). Evidence: production CEO API = 6 students,
  preview CEO API = 1 student.
- **Yes, the CEO API on preview reads preview data only.** The same key works on both (shared secret).
- The preview address changes with each fork (now `jlive-ceo-inspect--0x57uoje.preview.emergentagent.com`); the dashboard
  should use only `https://jeelive.ai/api/ceo/v1`.

---

## E. DOMAIN

### 20. Who manages jeelive.ai's DNS?
- **Outside Emergent, at GoDaddy.** Nameservers `ns05.domaincontrol.com` / `ns06.domaincontrol.com` (GoDaddy DNS),
  SOA `dns.jomax.net`; registrar (RDAP): **GoDaddy.com, LLC**.
- The A records (`172.66.2.113`, `162.159.142.117`) point to Cloudflare addresses (`server: cloudflare`) — the hosting
  edge in front of the Emergent deployment.
