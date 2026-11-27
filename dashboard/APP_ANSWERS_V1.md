# JEELIVE.AI app → JLive Command (CEO dashboard): answers v1

Read-only answers from the app project, 28 Nov 2026 (IST). No app code or data was changed to write this.
The app CEO API was already in the repo (`backend/ceo_api.py`). The earlier handoff is `memory/CEO_DASHBOARD.md`.
Where the app could not check something, the answer says **unsure**.

Repo layout: `backend/` = FastAPI app server (all routes under `/api`), `frontend/` = Expo app (expo-router, `frontend/app/`).
Live app server: `https://jeelive-mobile.emergent.host/api`. The website (jeelive.ai) is a separate server. It owns
accounts, papers, timers and results. The app reaches it through its own proxy `/api/jl/{path}` (`backend/jl_proxy.py`).

---

## A. Identity

**1. Student id in `rf_profiles`.**
- The field is `rf_profiles.uid`.
- It is the **same id the website uses**: the website's `user.id`, as returned by the website's `GET /auth/me`.
- **How it is linked:** there is no app account. The student signs in to the website account (mobile number + 4-digit
  PIN) from inside the app. The app server never takes an id from the phone.
- **Code path:**
  1. The phone calls `POST /api/rf/access` (`backend/rf_access.py`, `make_access_router`, route `@router.post('/access')`,
     about lines 91–139).
  2. The server takes the student's website session (web: the access cookie saved for that browser in collection
     `jl_jars`; phone: the access cookie the phone sends).
  3. It calls the website's `GET {JEELIVE_API}/auth/me` and sets `uid = user['id']`.
  4. `social.remember_identity(db, uid, user)` (`backend/social.py`, about line 88) upserts `rf_profiles` `{uid}` with
     `pid`, `display_name`, `seen_ts`, plus `phone_hash` and `phone_last4` when the website sends a number.
  5. A 15-minute grant (only its SHA-256 is stored, in `rf_access`) is returned as `{token, user_id, expires_at}`.
  6. On every `/api/rf/*` request the access guard (`install_access_guard`, about lines 160–180) replaces any
     `X-RF-User` header the phone sent with the uid from the verified grant. Routes read it through `rf_user()`.
- **Website down:** a session the website verified in the last 6 hours keeps working from `rf_trust`
  (`TRUST_HOURS = 6`).

**2. Does the app have its own login/signup?**
- **No own accounts.** The login screens are the website's login shown inside the app:
  - `frontend/app/entry.tsx`: sign in / sign up.
  - `frontend/app/forgot-pin.tsx`
  - `frontend/app/change-pin.tsx`
  - `frontend/app/account.tsx`: sign out.
  - `frontend/app/delete-account.tsx`
- **Website endpoints, through `/api/jl/...`** (`frontend/src/auth.tsx`, `frontend/src/api/client.ts`):
  `POST /auth/phone` (sign in), `POST /auth/phone/signup`, `GET /auth/session`, `GET /auth/me`, `POST /auth/refresh`,
  `POST /auth/logout`, `POST /auth/pin`.
- **App-server endpoints:**
  - `POST /api/account/forgot-pin` (`backend/pin_reset.py`)
  - `POST /api/account/delete-request`, `GET /api/account/delete-request/{rid}` (`backend/account_deletion.py`)
  - `POST /api/rf/access`
- **When the uid is known on the device:**
  - Right after `POST /api/jl/auth/phone` or `/auth/phone/signup` answers with the user (`authenticate()` in
    `src/auth.tsx`).
  - On later starts, after `GET /api/jl/auth/session` returns `user.id` (`src/api/client.ts`, about line 246).
  - For Rapid Fire, the server-verified id comes back as `user_id` from `POST /api/rf/access`
    (`src/api/client.ts`, about line 394).

**3. Test accounts and real profile counts.** Read-only counts, taken 28 Nov 2026 about 01:40 IST with the CEO API on
the live server (preview in brackets).
- **Yes, they are test accounts.** `uid` starting `TEST-` / `TESTUSER`, or `name` starting `TEST_`, are made by this
  project's automated tests. The game code already leaves them out of the leaderboards (`uid` or `name` matching `^TEST`).
- **Live counts:**

| Profiles | Live (preview) |
|---|---|
| All `rf_profiles` | **640** (639) |
| Test by the rule above | **588** (562) |
| Ids in the website's UUID format | **4** (4) |
| Other ids (`qa`, `qa-`, `ms-`, `tester-`, `user-`) | **48** (73) |

- **Real (non-test) profiles today: 4.**
  - The 48 "other" ids are not in the website id format, and a real profile can only be made after a website sign-in
    (question 1). So they are almost certainly test fixtures too. Exactly which test made each one: **unsure**.
  - Recommended dashboard rule: count a profile as real only if `uid` is a UUID
    (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`) and the name does not start with `TEST`.
- **Update, 28 Nov 2026 (preview; live after the next app publish):** both CEO routes now count **real students
  only** with exactly that rule. The overview also returns `test_profiles_left_out`.
- **Before that update:**
  - `/api/ceo/overview` and `/api/ceo/users` did **not** filter test profiles. For example, live
    `app_users = 640`, `active.last_30_days = 155`, `rapid_fire_players = 155` all include test profiles.
  - Live and preview numbers are almost identical. The live database appears to hold the preview test data. Why: **unsure**.

## B. Screens and features

**4. Every expo-router screen (`frontend/app/`).**

Tabs, `(tabs)/` (ink-black bottom bar):

| File | What it is |
|---|---|
| `(tabs)/_layout.tsx` | the bottom bar: Home, Rank, Rapid Fire, My Tests, Mission |
| `(tabs)/index.tsx` | **Home**: greeting, All India Series card, practice tiles (JEE Main / BITSAT / COMEDK / Student Choice), Misfire card, Dream College Meter, Explore chips, Share card |
| `(tabs)/rank.tsx` | **Rank**: rank predictor, cut-off, target marks, college predictor, **college compare**, **PDF reports**, "Meri details" |
| `(tabs)/rapid.tsx` | **Rapid Fire** lobby with its own bar (Home, Trophy, Arena, Gang, Store): streak, coins, diamonds, quests, leagues, **leaderboards**, shop |
| `(tabs)/tests.tsx` | **My Tests**: Completed / In progress / Saved, with search |
| `(tabs)/mission.tsx` | **Our Mission**: the student's share link and how many friends it helped |

Website papers, series and analysis:

| File | What it is |
|---|---|
| `live.tsx` | **All India Series** hub (days, streak, "How it works") |
| `series-analysis.tsx` | AITS analysis: every series day attempted |
| `series-leaderboard.tsx` | AITS leaderboard (All India Rank per day, search "Naam ya Rank") |
| `series-share.tsx` | share pictures (Rank card, Streak card) |
| `exam/[slug].tsx` | one exam's hub (JEE Main / BITSAT / COMEDK) |
| `catalogue.tsx` | chapter-wise tests (subject chips × All / Class 11 / Class 12) |
| `pyq.tsx` | JEE Main PYQ papers |
| `set/[id].tsx` | one paper's page before starting (save / start) |
| `attempt/[id].tsx` | the paper player (answers, timer: website) |
| `result/[id].tsx` | result + analysis (Analysis, Progress, Confidence…, Solutions, report PDF) |
| `misfire/index.tsx`, `misfire/[id].tsx`, `misfire/solve.tsx` | Misfire: wrong/skipped questions, solve again |
| `choice/index.tsx`, `choice/pick.tsx`, `choice/questions.tsx`, `choice/tests.tsx` | Student Choice: pick chapters / questions |
| `matched/index.tsx`, `matched/[id].tsx` | Matched: JEE Main questions that matched ours (open without sign-in) |

Rapid Fire screens:

| File | What it is |
|---|---|
| `rapid/session.tsx` | **Solo Sprint** |
| `rapid/duel.tsx` | **1 v 1 / Quick Match / Practice Rival** (vs bot), and match review |
| `rapid/daily.tsx`, `rapid/daily-styles.tsx` | **All India Rapid** (daily) and its card styles |
| `rapid/challenge.tsx`, `rapid/room/[cid].tsx` | Play Friends (WhatsApp link, gang, up to 4) and a Match Room |
| `rapid/cup/index.tsx`, `rapid/cup/[cid].tsx`, `rapid/cup/night.tsx` | Cups and Cup Night |
| `rapid/gang/new.tsx`, `rapid/gang/[gid].tsx` | Gangs |
| `rapid/player/[pid].tsx` | a player's Rapid Fire **profile** |
| `rapid/squads.tsx` | Cheer Squads |
| `rapid/vault.tsx` | Diamond Vault |
| `rapid/watch/[did].tsx` | watch a live match |

Offline:

| File | What it is |
|---|---|
| `offline/index.tsx` | the screen that opens without internet |
| `offline/rapid.tsx` | an offline Solo Sprint |
| `offline/results.tsx`, `offline/result.tsx` | kept results |

Account and other screens:

| File | What it is |
|---|---|
| `entry.tsx` | sign in / sign up (there is no separate onboarding flow) |
| `account.tsx` | **profile and settings**: name, PIN, offline, privacy, delete, sign out (no separate Settings screen) |
| `change-pin.tsx`, `forgot-pin.tsx`, `delete-account.tsx` | PIN change, PIN help/reset, account deletion |
| `privacy.tsx` | privacy policy and support (open without sign-in) |
| `performance.tsx` | loading-speed check for this device |
| `index.tsx` | start redirect |
| `_layout.tsx` | root layout, fonts, sign-in gate |
| `+html.tsx` | web page wrapper |

Where the topics you named live:
- **Dream college:** Home card plus Rank. Server: `backend/dream.py`, `/api/rf/dream`.
- **Streak:** Rapid Fire (game streak) and All India Series (series streak, website).
- **Coins / diamonds:** Rapid Fire top strip, Store, Vault.

**5. Tests / attempts.**
- Tests live **only on the website**. The app starts and submits them on the website through the proxy:
  - `POST /api/jl/sets/{id}/start`
  - `/attempts/{id}/begin`
  - `/attempts/{id}/answers/{qid}`
  - `/attempts/{id}/submit`
  - `/attempts/{id}/analysis`
  - `/attempts/{id}/analysis/report.pdf`
  - `/attempts/{id}/leaderboard`
  - `/attempts/{id}/ai-solutions`
  - `/my/tests`
  - `/series/all-india-jee/*`
- The app server stores no paper attempts or results.
- The app's own "rounds" are Rapid Fire games (question 8), not tests.

**6. Search.**

| Where | What it searches |
|---|---|
| My Tests (`(tabs)/tests.tsx`) | "Search test names…", on the phone |
| Rapid Fire chapter picker (`src/rapid/ScopeSheet.tsx`) | "Search chapters…" |
| Misfire / Student Choice | "Chapter ka naam likho…" |
| AITS leaderboard (`series-leaderboard.tsx`) and the analysis leaderboard | "Naam ya Rank" |
| Rank | college search (`src/rank/CollegeSearch.tsx`) |
| Gangs | `GET /api/rf/gangs/search` |
| Friends | by code, `GET /api/rf/friends/code/{code}` |

**7. Leaderboards.**

| Leaderboard | Endpoint | Data |
|---|---|---|
| Rapid Fire XP (per exam) | `GET /api/rf/leaderboard?exam=` (`gamify.py`) | `rf_profiles.exam_stats.<exam>.xp`, top 20 + your rank, 15 s cache |
| All India Rapid (daily) | `GET /api/rf/daily/board?exam=&day=` (`daily.py`) | `rf_daily_plays` |
| Friends league (weekly + all time) | `GET /api/rf/league/friends` (`leagues.py`) | `rf_profiles.week_stats` + `rf_friends` |
| Gang war | `GET /api/rf/league/gangwar` (`leagues.py`) | `rf_duels` (Gang vs Gang) + `rf_gangs` |
| Cup champions | `GET /api/rf/cups/champions` (`cups.py`) | `rf_cups`, `rf_cup_nights` |
| AITS / paper leaderboard | website `GET /api/jl/attempts/{id}/leaderboard` | website data (not on the app server) |

## C. Backend events (server side)

**8. Where each is written.**

**Rapid Fire match completed:**
- **Solo Sprint:** `POST /api/rf/sessions/{sid}/complete`, `rf_complete` → `finish` (`backend/sprints.py`, about
  line 150). It sets `rf_sessions.status = "completed"`, `summary` and `completed_at`.
- **Offline round sent later:** `POST /api/rf/sessions/offline` (`rf_offline`) inserts into `rf_sessions` with
  `offline: true`.
- **1 v 1 / Quick Match / Rival / Gang / Cup:** `settle(d)` (`backend/duels.py`, about line 480) sets
  `rf_duels.status = "finished"`, `winner` and `finished_ts`. It is reached from `POST /api/rf/duels/{did}/answer`,
  `/forfeit`, `GET /api/rf/duels/{did}` and timeouts.
- **All India Rapid:** `POST /api/rf/daily/finish` (`backend/daily.py`, about line 338) updates `rf_daily_plays`.

**Streak awarded, coins / diamonds / XP:**
- All three match kinds above call `award()` in `backend/gamify.py` (about lines 214–325), which writes once per match
  through `pay_once()`.
- Streak: `rf_profiles` `$set streak, last_day` and `$max best_streak`. A Streak Freeze, when used, is written in the
  same function.
- Coins, diamonds and XP: `rf_profiles` `$inc coins`, `diamonds.<colour>` and `xp`.
- Each payout is recorded in `rf_awards` `{uid, ref, exam, ts, reward}`. `ref` is `solo:<sid>`, `duel:<did>` or the
  daily ref.
- **There is no separate wallet ledger.** Other wallet moves `$inc` `rf_profiles` directly:
  - `POST /api/rf/shop/buy`: spends coins (or diamonds for gem items).
  - `POST /api/rf/quests/claim`: coins.
  - `POST /api/rf/rush/claim`: coins, plus a diamond or a freeze on some steps.
  - `POST /api/rf/league/friends/claim`: weekly prize coins.
  - `POST /api/rf/squads/buy`: spends diamonds (`diamonds.<colour>` down, `diamonds_spent.<colour>` up).

**Rank / cut-off result served:**
- Endpoints: `POST /api/rank/predict`, `/estimate`, `/college`, `/bitsat`, `/comedk`, `/comedk/college`, `/cutoff`,
  and `GET /api/rank/cutoff/options` (`rank_predictor.py`, `rank_cutoff.py`).
- **Nothing is written to the database.** The answer is computed from files in `backend/rank_data`.

**PDF report generated:**
- Rank PDFs: `POST /api/rank/pdf/jee`, `/comedk`, `/bitsat`, `/target/jee`, `/target/comedk`, `/target/bitsat`,
  `/saved`, `/cutoff` (`backend/rank_pdf.py`). They are made in memory and **not stored**.
- The result-analysis PDF is made by the website (`/api/jl/attempts/{id}/analysis/report.pdf`).

**Mission completed:**
- There is **no "mission completed" event**. Mission is a share link.
- `GET /api/rf/mission/me` creates the student's row in `mission_links` `{uid, code, helped}`.
- When a new browser opens `/api/j/{code}` (`backend/mission_links.py`, `open_link`), `mission_visits` gets a row and
  `mission_links.helped` is increased by 1.

**Leaderboard update:**
- **Nothing is written.** Every board is read from the collections above when asked: the XP board has a 15 s cache,
  the rank ladder a short in-memory cache.

Other written data you may want:
- `rf_duels` (all matches)
- `rf_sessions` (sprints)
- `rf_daily_plays`
- `rf_learning_events` (`revision.py`, per card answered)
- `rf_dreams` (dream colleges + mock marks, `PUT /api/rf/dream/dreams`, `POST /api/rf/dream/mocks`)
- `rf_feed` (friend feed)

**9. Framework, secrets, httpx.**
- FastAPI **0.110.1** on Python **3.11.18**.
- Secrets are read from the environment:
  - `backend/database.py` loads `backend/.env` (`load_dotenv(ROOT_DIR / '.env')`) when the server starts.
  - Modules then read `os.environ` (for example `CEO_API_TOKEN` in `backend/ceo_api.py`, `JEELIVE_API` in `rf_access.py`).
  - On the hosting, saved secrets are given to the server as environment variables.
- **httpx 0.28.1 is installed** and is already used to call the website (`jl_transport.py`).

## D. App build

**10. Versions and how students run it.**
- Expo SDK **58** (`expo ~58.0.26`), `expo-router ~58.0.32`, React Native **0.88.1**.
- Package / bundle id: **`com.emergent.jeelivemobile.kt2g15`** (Android and iOS).
- Students use a **store build**, built and published with Emergent Publish. Expo Go is only for development.
- **Google Play:** the listing exists, "JEELIVE.AI: JEE & BITSAT - Apps on Google Play" (checked with a public GET,
  HTTP 200), at `https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15`.
- **App Store (iPhone):** **unsure / not known.** No App Store link is set in the app (`backend/app_switches.py`
  `STORES["ios"] = ""`).
- A browser copy of the app runs on the app server at `/api/arena`, only for friends who open a match link without the app.

**11. Packages.**
- `@react-native-async-storage/async-storage` **2.2.0**: installed.
- `expo-constants` **~58.0.16**: installed.

**12. Analytics, crash reporting, push.**
- **No** analytics or crash tools: no Firebase, Sentry, Amplitude, Mixpanel or PostHog in `package.json` or the code.
- **No push notifications:** `expo-notifications` is not installed.
- Only server-side owner tools exist: a health page `/api/owner/health` and owner alert emails (`health_alerts.py`).

**13. Deep links.**
- App scheme: **`frontend`** (`frontend/app.json` `expo.scheme`). Match-room links use it as `frontend://...`
  (`backend/rooms.py` `APP_SCHEME`).
- **No** universal links or Android App Links: no `associatedDomains` and no `intentFilters` in `app.json` or
  `app.config.js`.
- Shared links are https links to the app server:
  - `/api/rf/c/{cid}`: match room. Opens the app, else the browser copy.
  - `/api/rf/g/{gid}/{code}`: gang.
  - `/api/j/{code}`: mission, which counts a friend and then goes to the website.

## E. Contacts and consent

**14. Phone numbers and emails on the app server.**
- `rf_profiles.phone_hash` (keyed HMAC) and `rf_profiles.phone_last4`: only the last 4 digits, used for friend
  search. Only **2** profiles have them.
- `pin_resets.phone`: a SHA-256 of the number (plus a hashed IP), kept only for the 5-per-hour reset limit.
- `account_deletions.phone` and `name`: the **full number and name** while a deletion request is open, so the owner can
  find the website account. Marking the request done or cancelled removes them (`backend/owner_panel.py`,
  `$unset phone, name`).
- **Emails:** none for students. Only the owner's own addresses (`JEELIVE_OWNER_EMAIL`, `OWNER_ALERT_EMAIL`) are in
  server settings.
- **Marketing consent / opt-in: none stored** in the app (no consent field anywhere). The full contact list and any
  consent belong to the website.

**15. Settings > Privacy.**
- There is no separate Settings screen. **Account** (`app/account.tsx`) has a "Privacy" group with **"Privacy policy &
  support"**, which opens `app/privacy.tsx` (also open without sign-in). There is also "Delete account"
  (`app/delete-account.tsx`).
- There are **no privacy toggles** (no tracking or marketing switches), because the app has no tracking today.

## F. CEO API

**16. Current sort of `GET /api/ceo/users`.**
- `db.rf_profiles.find(query).sort("last_day", -1).skip(...).limit(...)` (`backend/ceo_api.py`, about line 99).
- It sorts by `last_day` descending **only**. There is **no `uid` tie-break**, so profiles with the same `last_day` can
  change order between pages.
- **Update, 28 Nov 2026 (preview; live after the next app publish):** it now sorts
  `.sort([("last_day", -1), ("uid", 1)])`, backed by a new index `rf_profiles [(last_day,-1),(uid,1)]`, so the order is
  stable.

**17. Live base URL and token.**
- **Confirmed:** `https://jeelive-mobile.emergent.host/api`.
- **`CEO_API_TOKEN` is set in production.**
  - Live `GET /api/ceo/overview` without a token answers **401**. It would be 503 if no token were set.
  - With the token it answers **200**, `app_users: 640`.
  - The app's secret list shows `CEO_API_TOKEN` saved for live and preview, with one shared value (last saved
    23 Nov 2026).
- The token value is not written here. The owner pastes it into the dashboard.
