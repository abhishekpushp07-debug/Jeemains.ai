# JEELIVE CEO Dashboard: full brief from the WEBSITE project

Written 2026-11-23, updated 2026-11-23: the website's CEO API is NOW BUILT (section 9 is the exact contract; it replaces the
plans in 5.2 and 7). Give this whole file to the new agent together with:
1. the website GitHub repo (this project, React + FastAPI + MongoDB),
2. the app GitHub repo (branch `App`, Expo app + its own FastAPI server),
3. the app team's own version of this brief.

The dashboard itself is NOT built in the website project. This file says what the website has, what to track, how to
read it safely, and which small additions the website still needs (section 7). Nothing here is invented: where the
website does not record something today, it says "NOT RECORDED TODAY".

---------------------------------------------------------------------------------------------------------------------

## 0. Ground rules for the new agent (read first)

1. The dashboard is READ-ONLY for both products. It never writes to the website or app database, never signs a
   student in, never resets a PIN, never blocks anyone. If the CEO wants an action, link to the owner screen of that product.
2. Day boundaries are India time (Asia/Kolkata, UTC+05:30). Every "today", "daily", "week" in this brief is IST.
   The website stores time as Unix seconds (float, UTC) in most fields. Convert with +19800 seconds before bucketing by day.
3. One student = one website user id (`tejas_phone_profiles.id`, a UUID). The app stores the same id as
   `website_user_id`. Use this id to join the two products. Never use the phone number as a join key in the dashboard.
4. Phone numbers: the OWNER decided (2026-11-23) that the dashboard gets FULL student numbers and the full numbers of friends a
   student picked in Mission. They come only from the key-protected API in section 9. Show them only on CEO-only pages behind the
   allow-list sign-in, never in logs, alerts, URLs or exported files you do not need. PINs, session ids, cookies, signed picture
   links and answers are never sent.
5. Exclude from every student metric:
   - staff accounts (`tejas_users`, roles `owner` / `reviewer`). They are a different collection, so they never appear in
     `tejas_phone_profiles`, but staff attempts exist in `tejas_attempts` (filter by `user_id` not in staff ids),
   - test accounts (keep an editable exclude list in the dashboard; start with ids whose name starts with `TEST_` and the
     owner's own test number, which the owner will give you),
   - blocked students only where the metric says so (`blocked_at` set).
6. Preview and production are different databases. The dashboard must read PRODUCTION (jeelive.ai). Never point it at a preview.
7. Every number on screen needs a tooltip with its exact definition (copy from section 4).

---------------------------------------------------------------------------------------------------------------------

## 1. The two products and how they connect

| | Website (this repo) | App (other repo, branch `App`) |
| --- | --- | --- |
| Live at | https://jeelive.ai | JEELIVE.AI mobile app + its server |
| Owns | Student identity (mobile number + PIN), tests, attempts, scores, analysis, AITS 50-day series, content studio, pictures | Rank predictor, Mission, Dream college, Rapid Fire, cups, leagues, gangs, duels, squads, shop, daily, sprints, account deletion requests |
| Sign-in | `POST /api/auth/phone/signup`, `POST /api/auth/phone` (sign in), cookie `access_token` | Uses the WEBSITE session: it forwards the website cookie and stores `website_user_id` |
| Database | MongoDB, collections `tejas_*` | Its own MongoDB (see app brief) |

Connection details that matter for the dashboard:
- The website forwards Rank / Mission / Dream calls to the app server (`backend/tejas/app_connect.py`, env `JEELIVE_APP_API`).
  So Rank/Mission/Dream numbers live ONLY on the app server. Read them from the app, not from the website.
- `GET /api/dream` on the website first sends the student's released full mocks to the app server, so the app's Dream
  meter also counts website mocks. Do not add website mocks to the app's Dream numbers again (double count).
- A student who signs up on the website and later opens the app is ONE person (same website user id).
  "Signed up on app vs website" is recorded from 2026-11-23 (`signup_channel`, section 9). Older students have no value.

---------------------------------------------------------------------------------------------------------------------

## 2. What the website has built (and what data each part leaves behind)

| Area | What students / staff can do | Where the data is |
| --- | --- | --- |
| Student sign-up / sign-in | Mobile number + PIN, forgot PIN, change PIN | `tejas_phone_profiles`, `tejas_sessions`, `tejas_phone_limits` |
| Staff sign-in | Owner and reviewers with password | `tejas_users`, `tejas_sessions`, `tejas_login_limits` |
| Owner student directory | Search students, block / unblock, reset PIN, remove display name | `tejas_phone_profiles.blocked_at`, `tejas_audits` |
| Catalogue | Exams, sections, papers (sets) | `tejas_catalog_exams`, `tejas_catalog_sections`, `tejas_sets` |
| Content studio | Import PDFs / Excel / books, chapter books, mock books, PYQs, cut pictures, publish | `tejas_imports`, `tejas_smart_imports`, `tejas_smart_papers`, `tejas_books`, `tejas_book_pages`, `tejas_book_mocks`, `tejas_chapter_books`, `tejas_files`, `tejas_jobs` |
| Taking a test | Start, answer, mark for review, submit, auto-submit at deadline | `tejas_attempts` (one row per attempt), `tejas_attempt_timeline` (per-question time + answer changes) |
| Scoring | Marks, accuracy, attempt rate, score versions after key corrections | `tejas_attempts.summary`, `tejas_score_versions`, `tejas_ledgers` |
| Result + analysis | Result page, analysis workspace, analysis PDF, solutions | `tejas_analysis`, `tejas_attempts.solution_opened`, `review_solution_opened` |
| Rank among students | Cohort rank per paper, AIR scenario | `tejas_cohorts`, `tejas_cohort_entries`, `tejas_cohort_snapshots` |
| All India Test Series (AITS) | 50 days, full syllabus, one paper per day, live 12:01 AM to 11:59 PM IST; later days can be practised | `tejas_series` (schedule), `tejas_sets.series_id/series_date`, `tejas_attempts.mode = 'series_live'` |
| Streak | Current streak, best streak, skipped days, cups at 7/15/30/45/50 days | computed from attempts (`backend/tejas/series_streak.py`) |
| Mistake retry ("misfire") | Retry wrong questions until done | `tejas_misfires` |
| Saved tests / my tests / compare | Save papers, compare attempts | `tejas_saved_tests` |
| Report a wrong question | Student reports, staff review | `tejas_question_reports` |
| AI solutions (Astra) | AI-written solutions with a daily limit | `tejas_ai_solutions`, `tejas_ai_daily` (calls used per UTC day), `tejas_ai_limits`, `tejas_solution_requests` |
| Storage | New files in Supabase; old files still read from Emergent; owner copy tool | `tejas_files`, `tejas_content_transfers`, storage health at `/api/admin/storage/*` |
| Audit log | Owner / staff actions | `tejas_audits` (`action`, `actor`, `at`, `resource`, `detail`) |

There are NO payments, plans or subscriptions on the website. Revenue is NOT RECORDED on the website. If the app has a shop, its brief covers it.

---------------------------------------------------------------------------------------------------------------------

## 3. Data map: exact fields the dashboard needs

### 3.1 `tejas_phone_profiles` (one row per student)
| Field | Meaning |
| --- | --- |
| `id` | Website user id (UUID). THE join key. |
| `phone` | E.164 (`+91...`). Personal data, never leave the product unmasked. |
| `name` / `display_name` | Name shown to the student (may be empty or `Learner`). |
| `exam` | Default `JEE Main`. |
| `created_at` | Sign-up time (Unix seconds). |
| `consent_at` | When they accepted terms (same as sign-up today). |
| `last_seen_at` | Last SIGN-IN time (set at sign-up and sign-in). It is NOT "last active". |
| `pin_version` | Goes up on every PIN change / reset. |
| `blocked_at` | Set when the owner blocked the student. |
| `signup_channel` | NEW 2026-11-23: `web` (website browser), `app` (the JEELIVE app's server signed them up), `other`. Missing on older rows. |
| `signup_device` | NEW: `android` / `ios` / `desktop` for web sign-ups, else same as channel. |
| `signup_source` | NEW: `{utm_source, utm_medium, utm_campaign, referrer (site name only), landing (first page path)}` from the student's first visit. |
| `last_active_at` | NEW: last signed-in request, written at most once per 10 minutes. This is the real "last active". |

### 3.2 `tejas_attempts` (one row per test attempt)
| Field | Meaning |
| --- | --- |
| `id`, `user_id`, `set_id`, `title`, `exam` | Who took what |
| `mode` | `practice`, `series_live` (AITS on its live day), `series_practice` (an AITS day taken after its day) |
| `test_kind` | `mock` (full paper), `chapter`, `pyq` |
| `series_id`, `series_date` | Set for AITS attempts (`series_date` = `YYYY-MM-DD`, the AITS day) |
| `status` | `active` (running), `completed`; deleted papers show as deleted |
| `started_at`, `submitted_at`, `deadline` | Unix seconds |
| `reason` | Why it ended (student submit or time up) |
| `summary` | After grading: `score`, `maximum`, `correct`, `incorrect`, `skipped`, `accuracy`, `attempt_rate`, `penalties`, `total_seconds` |
| `grading_status` | `ready`, `queued`, `failed` (failed = ops alert) |
| `parent_attempt` | Set for retakes; exclude from "first attempt" metrics |
| `solution_opened`, `review_solution_opened` | Question ids whose solution the student opened |
| `count` | Number of questions |

### 3.3 Others
- `tejas_attempt_timeline`: per attempt, events `v` (time on a question), `a` (answer changed), `m` (mark for review). Use for "time per question", never for headline counts.
- `tejas_cohort_entries`: one row per ranked attempt (`cohort_id`, `user_id`, `score`, `maximum`, `submitted_at`).
- `tejas_sets`: `status` (`published`, `draft`...), `exam`, `test_kind`, `series_id`, `series_date`, `catalog_section_id`.
- `tejas_series`: AITS schedule: `first_date`, `days` (50), `open_time`, `close_time`.
- `tejas_question_reports`: wrong-question reports and review state.
- `tejas_ai_daily`: `{id: 'YYYY-MM-DD' (UTC), used}`. Daily limit is in AI settings (`daily_call_limit`, default 300).
- `tejas_jobs`: background work (`kind`, `status`: `queued` / `running` / `failed` / done, `error`).
- `tejas_audits`: owner actions such as `owner_student_blocked`, `owner_student_unblocked`, `owner_student_pin_reset`, `student_directory_read`, `student_display_name_removed`.

---------------------------------------------------------------------------------------------------------------------

## 4. What to track: metric catalogue (website side)

Every metric: name, exact definition, source, and a trap to avoid. "Student" = not staff, not in the exclude list.

### A. Growth
| # | Metric | Definition | Source |
| --- | --- | --- | --- |
| A1 | New sign-ups (today / 7d / 30d) | count of profiles with `created_at` in the IST period | profiles |
| A2 | Total students | count of profiles (show blocked separately) | profiles |
| A3 | Sign-ups by hour of day (IST) | histogram of `created_at` | profiles |
| A4 | Sign-ups by exam | group by `exam` | profiles |
| A5 | Sign-up source (web / app / campaign) | `signup_channel`, `signup_source.utm_*` (from 2026-11-23) | profiles |
| A6 | Friends invited from contacts | rows in `tejas_invite_contacts`; "joined after invite" = a profile with that phone created after the pick | contacts |

### B. Activation (did the new student actually start?)
| # | Metric | Definition |
| --- | --- | --- |
| B1 | Started a test within 24h | sign-ups whose first `started_at` <= `created_at + 86400` / sign-ups of that day |
| B2 | Finished a test within 24h | same with first `submitted_at` |
| B3 | Opened analysis / a solution on first test | first completed attempt has a non-empty `solution_opened` (analysis opens are NOT RECORDED TODAY) |
| B4 | Time to first test | median of (first `started_at` - `created_at`) |
| B5 | Signed up but never started | profiles with no attempt at all (list for follow-up, masked) |
Trap: use the first attempt by `started_at`; ignore `parent_attempt` rows.

### C. Engagement and retention
| # | Metric | Definition |
| --- | --- | --- |
| C1 | Active test-takers DAU / WAU / MAU | distinct `user_id` with an attempt `started_at` OR `submitted_at` in the period |
| C2 | Stickiness | DAU / MAU |
| C3 | Sign-in active (secondary) | distinct profiles with `last_seen_at` in the period. Label it "signed in", NOT "active" |
| C4 | Retention cohort grid | rows = sign-up week (IST); columns = week 0..12; cell = % of that cohort with an attempt in that week |
| C5 | Tests per active student | completed attempts / C1 |
| C6 | Returning vs new active | active students who signed up before the period vs in the period |
| C7 | Churn risk list | students active in the last 30 days with no attempt in the last 7 (masked list) |
Trap: `last_seen_at` only changes on sign-in. A student who stays signed in for a week looks "inactive". Use attempts for activity.

### D. Tests and learning
| # | Metric | Definition |
| --- | --- | --- |
| D1 | Attempts started / completed per day | by `started_at` / `submitted_at` |
| D2 | Completion rate | completed / started, per `test_kind` and `mode` |
| D3 | Abandoned | `status = active` and `deadline` passed (should be near 0, the server auto-submits) |
| D4 | Average score % | mean of `summary.score / summary.maximum` for completed full mocks (`test_kind = mock`) |
| D5 | Accuracy and attempt rate | mean of `summary.accuracy`, `summary.attempt_rate` (accuracy can be null when nothing was attempted) |
| D6 | Score distribution | buckets of score % (0-10, 10-20, ... ) for mocks |
| D7 | Solutions opened per completed attempt | mean length of `solution_opened` |
| D8 | Most attempted papers | top `set_id` by completed attempts, with title |
| D9 | Mix | share of attempts by `test_kind` (mock / chapter / pyq) and `mode` |
| D10 | Student improvement | per student, score % of last 3 mocks vs first 3 mocks (only students with 6+ mocks) |
Trap: after an answer-key correction a new score version exists. For headline marks use the score the student sees (`summary`), and show "re-scored attempts" as a separate count from `tejas_score_versions`.

### E. AITS (All India Test Series, 50 days)
| # | Metric | Definition |
| --- | --- | --- |
| E1 | Live participants per day | distinct `user_id` with `mode = series_live` and `series_date = D` |
| E2 | Live completion rate | completed / started for that day |
| E3 | Late practice | attempts with `mode = series_practice` per AITS day |
| E4 | Average / top marks per day | from `summary` of completed live attempts of day D (also median) |
| E5 | Students on a streak | students whose current streak (consecutive live days completed, up to today) is >= 1, 7, 15, 30, 45 |
| E6 | Drop-off curve | for day N, % of day-1 live participants who also finished day N live |
| E7 | Skipped days | students who did day N-1 live but missed day N |
| E8 | Papers ready | AITS days with a published paper vs 50; next empty day (from `tejas_sets.series_date`) |
Rules: the live window is 12:01 AM to 11:59 PM IST of `series_date`. A day counts for the streak only when the LIVE attempt was completed. First AITS day: read `tejas_series.first_date` (currently 9 Dec), never hard-code.

### F. Content supply
| # | Metric | Definition |
| --- | --- | --- |
| F1 | Published papers | `tejas_sets` with `status = published`, by exam and `test_kind` |
| F2 | Questions available | sum of question counts of published papers |
| F3 | Content in progress | imports / books not yet published, jobs queued |
| F4 | New papers this week | published in the period (use the publish audit or `created_at` if present) |

### G. Quality and support
| # | Metric | Definition |
| --- | --- | --- |
| G1 | Wrong-question reports | new / open / resolved from `tejas_question_reports` |
| G2 | Papers with most reports | top papers by open reports |
| G3 | PIN resets | count per day (`pin_version` going up and audit `owner_student_pin_reset`) |
| G4 | Blocked students | count with `blocked_at`, plus block / unblock actions from `tejas_audits` |

### H. AI usage and cost
| # | Metric | Definition |
| --- | --- | --- |
| H1 | AI calls used today vs limit | `tejas_ai_daily.used` for today's UTC date vs `daily_call_limit` |
| H2 | AI calls per day (90 days) | `tejas_ai_daily` keeps 90 days |
| H3 | AI solutions made | count of `tejas_ai_solutions` per day |
Money per AI call is NOT RECORDED on the website. If the CEO wants Rs per day, store a "price per call" setting in the dashboard and label it "estimate".

### I. Reliability (show as green / amber / red tiles)
| # | Metric | Definition |
| --- | --- | --- |
| I1 | Grading failures | attempts with `grading_status = failed` (any > 0 = red) |
| I2 | Grading waiting | completed attempts with `grading_status` not `ready` for more than 5 minutes |
| I3 | Failed background jobs | `tejas_jobs` with `status = failed`, by `kind` |
| I4 | Storage | which store new files go to, Supabase health, files still only in Emergent (owner endpoint `/api/admin/storage/*`) |
| I5 | API up | the dashboard pings a public website endpoint every minute (for example `GET /api/series/all-india-jee`) and records time + status |

---------------------------------------------------------------------------------------------------------------------

## 5. How the dashboard should get the data (recommended design)

### 5.1 Do not connect to the production database directly
The production database of jeelive.ai is managed by Emergent. Whether an outside project can even reach it is NOT CHECKED, and a
direct connection would expose every phone number. So the recommended way is a small, read-only metrics API inside each product.

### 5.2 Metrics API in each product (website side BUILT, see section 9 for the exact contract; this was the plan)
- Prefix: `GET /api/ceo/v1/...` on jeelive.ai (and the same idea on the app server).
- Auth: header `X-CEO-Key: <long random secret>`, stored as a secret on both sides. The website checks it with a constant-time
  compare. No cookie, no student session. Wrong key -> 401. Optional: allow-list the dashboard server's IP.
- Every answer: `Cache-Control: no-store`, counts only, no phone numbers, ids only where the endpoint says so.
- Times in the answer are ISO 8601 with `+05:30`; days are `YYYY-MM-DD` IST.
- Each endpoint takes `from` and `to` (IST dates, max 400 days) and answers within 2 seconds (precompute if needed).

Endpoints the website should offer:
| Endpoint | Returns |
| --- | --- |
| `/api/ceo/v1/summary` | totals now: students, blocked, sign-ups today/7d/30d, active today/7d/30d, attempts today, AITS today |
| `/api/ceo/v1/daily?from&to` | one row per IST day: sign_ups, active_test_takers, attempts_started, attempts_completed, mocks_completed, avg_mock_score_pct, ai_calls, reports_new |
| `/api/ceo/v1/funnel?from&to` | for sign-ups in range: signed_up, started_24h, completed_24h, completed_7d, second_test_7d |
| `/api/ceo/v1/retention?weeks=12` | cohort grid: sign-up week, size, active % in week 0..12 |
| `/api/ceo/v1/aits` | per AITS day: date, paper_ready, live_started, live_completed, practice_completed, avg_marks, median_marks, top_marks, max_marks; plus streak buckets |
| `/api/ceo/v1/content` | published papers by exam / kind, questions available, AITS days ready, imports in progress |
| `/api/ceo/v1/health` | grading_failed, grading_waiting, jobs_failed by kind, storage state, server time |
| `/api/ceo/v1/students?page&q` | masked list for drill-down: id, masked phone, name, sign-up date, last attempt date, attempts, AITS streak, blocked |
| `/api/ceo/v1/students/{id}` | one student: timeline of attempts (date, paper, mode, score %), streak, reports made. No answers, no PIN, no sessions |

### 5.3 Inside the dashboard project
- Its own backend pulls each endpoint every 10 minutes (summary, health) and once per hour (daily, funnel, retention, aits),
  and stores snapshots in its own database: `daily_facts(product, day, metric, value)`, `snapshots(product, at, json)`.
  The screens read only the dashboard's own database, so a slow product never slows the dashboard.
- Joins across products by `website_user_id` happen in the dashboard's database, only on aggregated or masked rows.
- If a product endpoint fails: keep showing the last good value with "as of <time>" in amber. Never show 0 for "unknown".
- Sign-in to the dashboard: Emergent-managed sign-in with an allow-list of the CEO's email(s). No open sign-up.

### 5.4 Screens
1. Overview: sign-ups today, active test-takers today / 7d, attempts completed today, AITS live participants today,
   AITS streak holders, health tiles. Small 30-day trend under each number.
2. Growth: sign-ups per day (bar), cumulative students (line), sign-ups by hour, by exam, by source (when built).
3. Funnel: signed up -> started test -> finished test -> second test in 7 days, for a chosen sign-up range.
4. Retention: weekly cohort grid with colour scale.
5. Tests: attempts per day by kind, completion rate, score distribution, most attempted papers, solutions opened.
6. AITS: day-by-day table for all 50 days, drop-off curve, streak buckets, papers ready vs missing (red if tomorrow has no paper).
7. Content: published papers and questions, AITS days ready, reports per paper.
8. App (from the app brief): Rank, Mission, Dream, Rapid Fire, leagues, etc.
9. Students: masked search, one-student timeline (website + app joined by user id).
10. Health and alerts: grading, jobs, storage, API up, and a list of alerts.

### 5.5 Alerts (send to the CEO by email or WhatsApp, decided in the dashboard project)
- Tomorrow's AITS day has no published paper (check at 6 PM IST).
- Any grading failure, or grading waiting more than 15 minutes.
- Website API down for 3 checks in a row.
- Sign-ups today less than 50% of the 7-day average by 9 PM IST.
- AI calls used above 80% of the daily limit.
- New files going to the wrong store / Supabase unhealthy (from the storage endpoint).

---------------------------------------------------------------------------------------------------------------------

## 6. Traps (seen in this codebase)

1. `last_seen_at` = last sign-in, not last activity. Use attempts.
2. Times are Unix seconds in UTC; buckets must be IST. `tejas_ai_daily.id` is a UTC date (the only UTC-day field here).
3. Staff take tests too. Exclude staff `user_id`s from attempts.
4. `parent_attempt` rows are retakes. Exclude them from first-test and live metrics.
5. AITS: `series_live` vs `series_practice`. Only `series_live` counts for live participation and streaks.
6. A completed attempt can still be `grading_status = queued` for a short time: its `summary` may be missing. Do not count it as 0 marks.
7. Score versions: after a key correction, marks can change. Re-pull at least 7 days back every night.
8. Deleted papers keep their attempts; show them under "deleted paper", do not drop them from counts.
9. Rank / Mission / Dream are on the app server. Mocks from the website are already counted inside the app's Dream meter.
10. Never log or store signed picture links, cookies or PINs in the dashboard.

---------------------------------------------------------------------------------------------------------------------

## 7. What the WEBSITE still has to add

UPDATE 2026-11-23: items 1, 2, 3 and a smaller version of 4 are BUILT (see section 9). Still not built: the full event list in
item 4 (today only `page_open`, `rank_tool_open`, `mission_share`, `contacts_pick`, `pdf_download` exist) and item 5 (the
endpoints compute live with a 1-10 minute cache instead). Original list kept for reference:

1. The `/api/ceo/v1/*` endpoints from section 5.2, protected by `CEO_DASHBOARD_KEY`.
2. Sign-up source on `tejas_phone_profiles`: `signup_channel` (`web` / `app`), `signup_referrer`, `utm_source`, `utm_medium`,
   `utm_campaign`, `signup_device` (`android` / `ios` / `desktop` / `mobile_web`). Captured once at sign-up, never changed.
3. Real "last active": `last_active_at` on the profile, updated at most once per 10 minutes when a signed-in request arrives.
4. A small event log `tejas_events` (kept 400 days), one row per event: `{id, user_id, name, at, props}` with only these names:
   `signup`, `signin`, `test_start`, `test_submit`, `result_open`, `analysis_open`, `solution_open`, `aits_hub_open`,
   `aits_day_open`, `misfire_retry`, `report_wrong`, `ai_solution_request`, `pdf_download`, `pin_reset`.
   `props` holds ids and small enums only (paper id, mode, test kind), never answers or phone numbers.
5. A nightly job that writes `tejas_daily_facts` (one row per IST day and metric) so the endpoints answer fast.
6. Tests for each endpoint on a throw-away database: wrong key 401, no phone numbers in any answer, IST day boundaries, staff excluded.

---------------------------------------------------------------------------------------------------------------------

## 8. Build plan for the new dashboard agent

1. Read this file, the app brief and both repos. Write down any field the app brief names differently.
2. Build the dashboard backend with a FAKE data source first (fixtures shaped exactly like section 9), and all screens on it.
3. Add the CEO allow-list sign-in.
4. When the website and app endpoints exist, switch the data source per product with a setting; keep the fake one for tests.
5. Check every number against a hand count for one IST day (pick a quiet day, count in the product's owner screens).
6. Add alerts last.
Acceptance: every tile has a definition tooltip, phone numbers appear only on CEO-only pages, a product outage shows amber "as of" values,
IST day totals match the hand count.

---------------------------------------------------------------------------------------------------------------------

## 9. BUILT: the website CEO API (exact contract, 2026-11-23)

Code: `backend/tejas/ceo.py` (read-only), `backend/tejas/contacts.py`, `backend/tejas/activity.py`. Tested on a throw-away
database with hand-counted numbers (`backend/tests/ceo_bridge228.py`). Preview only until the website is published.

### 9.1 Connecting
- Base: `https://jeelive.ai/api/ceo/v1` (after publish). Every call is `GET` with header `X-CEO-Key: <key>`.
- The key is the website secret `CEO_DASHBOARD_KEY` (at least 24 characters). The owner types the same value into the website
  secrets and into the dashboard's own secrets. Never put it in browser code; only the dashboard's SERVER calls this API.
- Optional website secret `CEO_EXCLUDE_PHONES` = comma list of the owner's own test numbers (`9876543210,9123456780`).
- Answers: `{"data": {...}, "error": null, "meta": {"api_version": "1", "request_id": "..."}}`. Read `data`.
- Errors: no key set on the website -> 503; wrong key -> 401; 20 wrong keys from one IP in 10 minutes -> 429 for that window;
  bad date -> 422. `Cache-Control: no-store` on every answer.
- The website keeps each answer for 1 to 10 minutes, so polling more often gives the same numbers. Suggested polling: summary,
  alerts, health every 5 min; daily, events every 30 min; funnel, retention, aits, content every hour; students/contacts on demand.
- Days are India time. Times are ISO with `+05:30`. `from`/`to` are `YYYY-MM-DD`, at most 400 days, default the last 30 days.
- Left out of every count: staff accounts, students whose name starts with `TEST_`, and `CEO_EXCLUDE_PHONES`.

### 9.2 Endpoints
| Endpoint | Returns |
| --- | --- |
| `/summary` | `students {total, blocked, by_signup_channel {web, app, other}}`, `signups`, `active_test_takers`, `active_on_site` (from `last_active_at`), `signed_in` (from `last_seen_at`), each as `{today, last_7_days, last_30_days}`; `attempts_today {started, completed}`; `aits_today {date, day, live_started, live_completed}` or null outside the 50 days; `contacts {students_who_shared, total, today}`; `ai_calls_today_utc` |
| `/daily?from&to` | `rows[]`: `date, signups, signups_web, signups_app, active_test_takers, attempts_started, attempts_completed, mocks_completed, avg_mock_score_pct, aits_live_completed, contacts_shared, reports_new, ai_calls_utc` |
| `/funnel?from&to` | for sign-ups in the range: `signed_up, started_in_24h, completed_in_24h, completed_in_7d, second_test_in_7d, never_started, median_minutes_to_first_test` |
| `/retention?weeks=12` (2-26) | `cohorts[]`: `week_start` (Monday), `size`, `active_pct[]` (week 0..n, % who started a test that week; null when size 0) |
| `/aits` | `stage` (prelaunch / live / finished), `papers_ready`, `next_day_without_paper`, `streak_now_at_least {1,7,15,30,45,50}`, `best_streak_at_least {...}`, `days[]` (50): `day, date, paper {id,title,status}, paper_ready`, and for days up to today `live_started, live_completed, practice_completed, max_marks, avg_marks, median_marks, top_marks, day1_people_still_here_pct` |
| `/content` | `published[] {exam, test_kind, papers, questions}`, `papers_total`, `questions_total`, `published_last_7_days`, `aits_days_ready`, `jobs_waiting[]`, `question_reports {status: count}` |
| `/health` | `server_time, grading_failed, grading_waiting_over_5_min, jobs_failed[] {kind, count, last_at, last_error}, storage {mode, checked_at, alert} or null, index_problems` |
| `/alerts` | `level` (green / amber / red) and `alerts[] {code, level, title (Hinglish, ready to send), value}`. Codes: `aits_tomorrow_no_paper` (red after 6 PM IST), `grading_failed`, `grading_waiting` (over 15 min), `storage`, `jobs_failed_24h`, `ai_near_limit` (80%+ of the daily limit), `signups_low` (after 9 PM IST, today under half the 7-day average, only once there are 14+ sign-ups a week) |
| `/students?page&q&sort` | 100 per page, `sort=new` (sign-up) or `active`; `q` = part of a number or a name. Items: `id, phone (full), name, exam, signed_up_at, signup_channel, signup_device, signup_source, last_signin_at, last_active_at, blocked, attempts, completed, last_attempt_at, contacts_shared` |
| `/students/{id}` | the same fields plus `aits {live_days_done, current_streak, best_streak}`, `tests[]` (latest 300: `id, title, exam, mode, test_kind, status, started_at, submitted_at, series_date, retake, score, maximum, accuracy`), `contacts[] {name, phone, shared_at}`, `usage_last_90_days[] {name, page, tool, count}`. Unknown id -> 404 |
| `/contacts?page&q` | friends students picked, newest first, 100 per page, `q` = part of a number. Items: `name, phone (full), shared_at, shared_by {id, phone, name}, already_student, joined_after_share, student_id` |
| `/events?from&to` | `daily[] {date, name, count, people}` and `top[] {name, page, tool, count}` (people = signed-in students plus anonymous visitors by a random browser id) |

### 9.3 Mission "Contacts se dost chuno" (where `/contacts` numbers come from)
- On the Mission page, a phone browser that supports the Contact Picker (Android Chrome) shows "Contacts se dost chuno". The
  student taps it, the phone's own contact list opens, and ONLY the people the student ticks are sent. Nothing is read silently;
  other browsers (iPhone, laptop) simply do not show the button.
- The consent line is shown right under the button. Saved per student: `{id, user_id, phone (E.164), name, at, consent}` in
  `tejas_invite_contacts`, one row per student + number, at most 500 per student. Invalid numbers and the student's own number are skipped.
- Each saved friend gets a WhatsApp "Bhejo" button with the student's own Mission link, and a remove button (removing deletes that row).
- Student API (signed-in student only, their own rows only): `GET /api/mission/contacts`, `POST /api/mission/contacts`
  `{contacts: [{name, tel: [..]}]}` (max 100 per call), `DELETE /api/mission/contacts/{id}`.

### 9.4 Usage events and sign-up source
- `POST /api/events` `{name, vid?, props? {page, tool, ref}}` from the website's own pages: `page_open` (page names such as
  home, rank, mission, aits, aits_analysis, result, test, paper, my_tests, misfire, pyq, exams, profile, landing, login, signup),
  `rank_tool_open` (tool), `mission_share`, `contacts_pick`. Staff visits are not kept, 120 events per person per 10 min, kept 400 days.
- The first visit stores campaign words (`utm_source/medium/campaign`), the sending site and the first page in the browser; the
  sign-up sends them once and they land in `signup_source`.

### 9.5 Still on the app side
Rank (Cut off, Meri details, six tools), Mission counts, Dream, Rapid Fire: read them from the APP server's own CEO API (app
brief). The website only counts how often a Rank tool tab is opened (`rank_tool_open`).
