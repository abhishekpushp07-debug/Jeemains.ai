# JEELIVE.AI — Hand-off for the next agent (written 26 Nov 2026, 19:30 IST)

> Read this first, then `memory/PRD.md` (newest section is at the END: "26 Nov 2026 (evening)"),
> `memory/REQUIRED_CHANGES_GUIDE.md` (the owner's Hindi to-do guide), `memory/test_credentials.md` (test rules + ids).
> `memory/HANDOFF_SUMMARY.md` is very old (Nov early days); do not plan from it.

---

## 0. The owner, the app, the rules

- **Owner** = non-technical, writes Hindi / Hinglish / English, often on a phone. Reply in plain words, his language.
  He hates surprises: explain first, get "yes", then code. When he says **"Just talk, don't code"**, do not edit anything.
- **App** = JEELIVE.AI: Expo SDK 58 (React Native, expo-router) in `/app/frontend`, FastAPI in `/app/backend`
  (port 8001, every route under `/api`), MongoDB (`MONGO_URL`, `DB_NAME` from `backend/.env`).
  Accounts, papers, attempts, results, Misfire, AITS all live on the **website jeelive.ai** (canonical API);
  the app's server proxies it at `/api/jl/<path>` → `https://jeelive.ai/api/<path>` (`backend/jl_proxy.py`).
  Rapid Fire (cards, duels, coins, All India Rapid, CEO dashboard, Matched shifts) lives on the app's own server.
- **The owner's six golden rules (26 Nov 2026, verbatim meaning):**
  1. Never break what is already built (90 % is done): be careful with code AND data.
  2. Work in small packets that don't interfere with each other.
  3. Aim for the fastest, most efficient, most capable platform.
  4. Small / slow Android phones: automatically drop gloss → animation → cheerleading so nothing lags
     (`src/analysis/smooth.ts` "Smooth Mode" calms the Shine; since 26 Nov late night its lowest level also rests the
     endless decoration and puts every celebration in its calm form: `useLowMotion` / `useStill` in `src/motion.tsx`.
     Proven in a browser only, NOT on a real slow phone — see the last PRD section and `tests/slow_phone_*.py`).
  5. Never crash, always fast.
  6. Don't rush; make it perfect.
- **Never:** touch `metro.config.js`, `.env` URLs/ports, `EXPO_PACKAGER_*`; overwrite existing files (use search_replace);
  hard-code colours outside `frontend/src/theme.ts`; run `rm -rf` yourself; paste credentials into chat or into docs
  that go to the website.
- **Rapid Fire:** owner said **"rapid fire में कुछ नहीं बदलना है"**. Do not change Rapid Fire code until he says what
  to change (REQUIRED_CHANGES_GUIDE बदलाव 3). Only its browser copy was rebuilt (no source change).
- **QA learner** (phone/PIN in `memory/test_credentials.md`) is **the owner's own real account on jeelive.ai**:
  read-only for academics. Never press Start/Resume/Submit on real papers; screenshot scripts must answer every
  write (`POST jl/attempts/...`) in the browser instead of sending it (see `handoff/feature_book/take_shots*.py`).
- Dates: today is **26 Nov 2026 (IST)**. AITS series starts **9 Dec 2026**. JEE Main first shift ≈ **Jan 2027**
  (Matched must be in students' phones before it).

---

## 1. Where things stand RIGHT NOW

| What | Preview (this pod) | Production (jeelive-mobile.emergent.host) | Students' phones |
| --- | --- | --- | --- |
| Student Choice on the real 81 chapters + chapter search | yes | yes (publish 26 Nov 05:33 UTC) | Android build versionCode 153 (26 Nov 06:19 UTC) |
| Matched pages + paper button | yes | yes | build 153 |
| Matched card on Home as soon as the FIRST shift is published + All India bar (`HomeSeriesBar`) under it | yes (commit f0f337b, 26 Nov 08:17) | **NO** (needs Publish) | needs new build |
| Student Choice "three-hour" sentence, 180-min cap of chapter-test ratio time | yes | **NO** | needs new build |
| **Student Choice colours** (today) | yes | **NO** | needs new build |
| **Made-paper make-up minutes add up** (today) | yes | **NO** | needs new build |
| **Browser Rapid Fire copy** (`/api/arena`) with All India Rapid "Misfires" tab (rebuilt today) | yes | **NO** — production still serves the 21 Nov copy | (browser only) |
| iOS build | — | — | **never built** |

- `expo-updates` is NOT in the app → installed phones only change with a new build.
- **Owner said (26 Nov, last message): "I will deploy later with a new agent."** So: do NOT publish on your own.
  When he asks: run the deployment health check if he wants, then deploy via `emergent__send_to_deployer`
  (intent deploy). Remind him: after Publish, Android + (first) iOS build from the Publish panel.
- Git: everything is committed by the platform (last commit 56414f2). Untracked: `frontend/package-lock.json`,
  `frontend/yarn.lock` (both dated 21 Nov; earlier deploys worked with them — see §4).

---

## 2. What I (this agent) did on 26 Nov 2026, in order

1. **Explained to the owner (no code):** what "browser Rapid Fire" is (the app's own web export at
   `/api/arena`, built by the app side on 15 Nov, last copy 21 Nov; NOT made by the website agent); that Misfire is
   ONE calculation — the website's (app only reads `/my/misfire…` and builds paper-wise lists from results);
   wrote the Hindi guide `memory/REQUIRED_CHANGES_GUIDE.md` (बदलाव 1–8, open decisions, website work, order).
2. **Owner approved** (a) Student Choice colours "maroon like the result page", colour only at the top, cards stay
   white; (b) book version 3 + Misfire checklist, final hand-off for the website agent; (c) no Rapid Fire code change;
   (d) "one account" (sign up on website → log in app, and vice versa) must be in the hand-off.
3. **Student Choice colours — DONE, tested:**
   - New `frontend/src/choice/looks.tsx`: `ChoiceHero` (dark-red Shine card, uses existing maroon tokens),
     `SubjectTabs` (glossy tabs via `GlossTabs`: Physics red, Chemistry amber, Maths teal), `subjectWash`.
   - Edited `frontend/app/choice/index.tsx` (hero card: "JEE MAIN · CHAPTER-WISE SAWAAL", title, facts in glass chips),
     `pick.tsx` (glossy tabs, ticked rows in subject colour), `tests.tsx` (hero with Ho gaye / Chal rahe / Baaki,
     testIDs `choice-tests-hero`, `choice-tests-done|running|left`; title 3 lines for 320 width),
     `questions.tsx` (tabs), `frontend/src/choice/parts.tsx` (badges Start red / Resume yellow / Result pink,
     unknown label → plain; StepBar red button, count 2 lines), `frontend/src/theme.ts` (new tokens
     `custom_tabRed*`, `custom_tabAmber*`, `custom_tabTeal*`, `custom_wash*`, `tabEdges.red/amber/teal` — added to `dark`;
     `light` starts with `...dark`, so it has them too).
   - `frontend/src/choice/api.ts`: new `splitMinutes` (largest-remainder) so a made paper's subject rows add up to
     its total (7 + 3 + 7 = 17, before 8 + 4 + 7). `TEST_MAX_MINUTES = 180` unchanged.
   - Checks: tsc 0, eslint clean (app + src), 76,076 split cases 0 bad, `tests/choice_colour_look.py` at 390 & 320
     (no sideways scroll), testing agent 64/64 (`test_reports/iteration_147.json`; it added `tests/t1_choice_colour_check.py`,
     `tests/t1_choice_bar_320.py`). NOT checked: a real phone, a slow Android phone.
4. **Browser Rapid Fire copy rebuilt** with `bash scripts/build_arena_web.sh` → `backend/arena_web/` (8.7 MB).
   No Rapid Fire source changed. ⚠ the script itself contains `rm -rf` of its own output folders.
5. **Website hand-off book v3 — DONE** (`/app/handoff/feature_book/`):
   - Parts: `00_start` (owner box in Hinglish, what's live, who does what, 24 "never get wrong" rules),
     `10/11/12_choice_*` (colours, make-up fix), `20/21/22_matched_*`, `30_reference` (addresses, sentences,
     testIDs, files, curl checks, decided + still-open points 1–8), NEW `40_misfire.md` (website's own; app computes
     only paper lists, `<attempt id>:<question id>` ids, marks lost; six checks for the website agent),
     NEW `50_rapid_fire.md` (app-owned; website only links to `…/api/arena`; card line corrected 15 → 20 seconds;
     website→arena sign-in ticket = written idea, not built), NEW `60_one_account.md` (all auth doors are the
     website's: `auth/phone`, `auth/phone/signup`, `auth/session`, `auth/refresh`, `auth/me`, `auth/pin`,
     `auth/logout`; forgot-PIN via app server `POST /api/account/forgot-pin`; student `id` never changes; account
     deletion is by hand on the website).
   - New pictures `shots/x01..x03` (Misfire), `r01_arena_laptop`, `a01_signin` via `take_shots_more.py`.
   - Build: `cd /app/handoff/feature_book && python3 build_book.py` (needs `pip install --target /tmp/mdlib markdown`
     if `/tmp/mdlib` is missing; shots need `QA_PHONE=… QA_PIN=…` env from test_credentials). Output: PDF 59 pages,
     `BOOK.md` (~30 k words, paste-able), ZIP `/app/handoff/JEELIVE_Student_Choice_and_Matched_Book.zip`.
     Its state table live-checks production `/api/arena` (compares the `entry-<hash>.js` name) and website
     `auth/session`.
   - Owner download links (PDF + ZIP) issued with `python3 backend/tools/owner_download.py issue --artifact
     choice-matched-book-pdf|choice-matched-book-zip --hours 168`; verified 200 + exact bytes; expire
     **3 Dec 2026 13:49 UTC**. Grants pin the file's sha256 → **any rebuild of the book needs new grants**.
     Never write grant URLs into files.
   - `memory/WEBSITE_NOTE.md`: "15-second" → "20-second" (cards are 20 s: `CARD_SECONDS = 20` in `backend/scope.py`).
6. **Deployment health check (read-only): WARN, no blocker.** See §4. Lint after it: clean.

---

## 3. What the next agent should do (priority order)

🔴 **A. When the owner says deploy/publish:** deploy (`emergent__send_to_deployer`, intent deploy). Afterwards confirm
   production: `/api/arena` entry file name equals `backend/arena_web/index.html`'s; Home Matched rule; Student
   Choice colours need the NEW Android build + first iOS build (owner does it from the Publish panel). Must be done
   before **9 Dec** (AITS) and long before the first JEE Main shift (Jan 2027).

🟡 **B. Health-check warnings — fix ONLY with owner's yes** (I offered, he hasn't answered):
   1. Two lockfiles (`package-lock.json` + `yarn.lock`, both untracked in git; `packageManager` = yarn 1.22.22).
      Deploys worked with both. Option: remove `package-lock.json`. Ask first.
   2. Slow first start: `backend/server.py` startup awaits `db_setup.run_once` (indexes, ~14 k card sync, migrations)
      before uvicorn listens → `/health` connection-refused during start. Option: run it in a background task.
      Touches startup → small packet, test carefully, ask first.
      **DONE 26 Nov late night (owner's yes), as a limit, not a background task:** `db_setup.run_before_serving`
      waits at most 30 s, then the setup goes on behind a server that answers. Measured: the setup takes 29 ms on
      the preview and a restart is unreachable for 0.9 s before and after, so nothing got faster; it only cannot hang
      any more. Not fully in the background on purpose (a fresh database needs the capped `rf_events` and the unique
      indexes before the first request). The health check may still warn about the wait; that is the reason.
   3. `.gitignore` `.env*`: platform default, nothing to do.
   4. Store review: needs a reviewer demo login (separate account, not the owner's QA learner); not in repo.

🟡 **C. Owner's open decisions** (book Part 3.8 + REQUIRED_CHANGES_GUIDE बदलाव 6) — code only after his answer:
   1. Max 3 h for MADE papers too? (ratio: 75 Maths Qs = 240 min). 2. Minimum time for a chapter test?
   3. Should a Matched paper ever count in the Dream College meter? 4. App's suggestions for made papers (new
   questions first in random mock, daily limit, cleaning never-started papers, no leaderboard).
   5. Matched `source` / `tag` wording. 6. Keep or hide the made-up sample Matched shifts on the PREVIEW.
   7. (question for website agent) `kind` of Student Choice / Matched papers in paper history → then add two
   Misfire paper-wise tabs (बदलाव 4). 8. Opening browser Rapid Fire from the website without typing PIN again
   (ticket idea in Part 5.4; not built).
   Also unanswered: (a) did he check the last publish on an installed app or Expo Go? (b) were the five
   24–25 Nov attempts on the QA learner started by him?

🟢 **D. Waiting on the website agent** (app cannot do these; the book tells them):
   Student Choice doors A `GET choice/bank` (pick/random switch), B (chapter questions without options),
   C `POST choice/papers` (max 75, never 90, +4/−1, Maths 3.2 / Physics 2.4 / Chemistry 1.6 min per question);
   81 chapter-test times by ratio, 180 min max (today every chapter test is 60 min); Matched public doors
   `GET matched`, `GET matched/<shift>`, one ordinary paper per shift, super-admin page, the matching machine
   (built nowhere yet); Misfire six checks (Part 4.4); "Rapid Fire" button/link on the website; one-account
   test with a TEST number (new app sign-up → jeelive.ai sign-in, and reverse; `auth/me` same `id`);
   pictures fast-load (`memory/APP_PICTURES_NEEDS.md`); CEO dashboard signups export.

🟢 **E. Never checked yet:** real phone (Student Choice, Matched, colours, keyboard, maths text, safe area); slow
   Android phone with the new shine; a real AITS day + Home AITS bar (from 9 Dec); a real Matched shift end-to-end;
   picture questions in the Student Choice question list (needs door B); an attempt longer than 180 min;
   BITSAT / COMEDK papers in Misfire (QA learner has none).

⚪ **F. Backlog:** Offline Solutions (`memory/OFFLINE_SOLUTIONS_PLAN.md`, not started); App Store / Play Store
   readiness review (skills `expo-appstore-readiness-review`, `expo-playstore-readiness-review`); Rapid Fire card
   teacher-review list; two small labels (`aria-checked` on count pills, `rf-history-empty`); All India Rapid
   "Misfires" number (counts every not-right card, e.g. 36, while never-reached cards are not listed — owner's
   decision pending); golden rule 4 for every animation/cheer (CheerSquad, CheerBanner, ChampionsWall,
   CupShowcase, DailyScenes, StoreTab, the crown celebration, the diamond flare, the reward panel, Dream Unlocked):
   since 26 Nov late night they follow the device-speed level too (`useLowMotion` / `useStill`), checked in a
   browser by `tests/slow_phone_{check,surfaces,dream,wins,smoke}.py`. STILL OPEN: the same on a real slow Android
   phone; and the browser copy `backend/arena_web/` was NOT rebuilt, it has the old celebrations (owner's yes first).

---

## 4. Deployment facts (for the deploy agent)

- Last successful deploy: `51e353c0`, 26 Nov 05:33–05:38 UTC (included commit 9c61bc4 of 25 Nov). Everything after
  that (commits f0f337b … 56414f2) is preview-only.
- Android versionCode 153 (26 Nov 06:19 UTC) = from that deploy. No iOS build ever.
- Health check today: WARN only (lockfiles, `.env*` in `.gitignore`, store demo login, slow first start).
  Disk 5.2 GB free; `backend/arena_web` 8.7 MB; `handoff/` 31 MB. `GET /health` 200 locally.
- Production read checks: `https://jeelive-mobile.emergent.host/api/arena` (200), `/api/matched`
  (was `matched:false`, no shifts), website `https://jeelive.ai/api/auth/session` (200, `user: null` signed out).

---

## 5. Key files map

- Student Choice: `frontend/app/choice/{index,pick,tests,questions}.tsx`, `frontend/src/choice/{api,search,store,parts,looks}.ts(x)`,
  backend `backend/choice.py` (`minutes_for`, `chapter_test_minutes`), notes `memory/WEBSITE_CHOICE_NOTE.md`.
- Matched: backend `matched_shifts` collection + `/api/matched*` routes, Home card + `HomeSeriesBar`
  (`frontend/app/(tabs)/index.tsx`), `memory/MATCHED_CONTRACT.md`, `memory/WEBSITE_MATCHED_NOTE.md`.
- Misfire: `frontend/app/misfire/{index,[id],solve}.tsx`, `frontend/src/misfire/*` (no own data).
- All India Rapid Misfires: `backend/daily.py` (`GET /api/rf/daily/misses`), `frontend/src/rapid/DailyMisses.tsx`.
- Browser Rapid Fire: `backend/arena_web/` (built), `backend/arena_web.py`, `scripts/build_arena_web.sh`.
- Accounts: `frontend/src/auth.tsx`, `frontend/src/api/client.ts`, `backend/jl_proxy.py`, `backend/rf_access.py`,
  `backend/login_guard.py`, `backend/account_deletion.py`, `backend/pin_reset.py`. Any auth change → call
  `integration_expert` FIRST.
- Looks: `frontend/src/theme.ts`, `src/components/GlossTabs.tsx`, `src/analysis/Shine.tsx`, `src/analysis/smooth.ts`.
- Owner downloads: `backend/owner_downloads.py`, `backend/tools/owner_download.py` (since 26 Nov night also
  `choice-matched-book-md` = `BOOK.md` as a forced file download; see the last PRD section).
- Website hand-offs: `handoff/feature_book/` (v3, current), `handoff/JEELIVE_CEO_Dashboard_Handoff*`,
  `handoff/JEELIVE_Rank_Mission_Website_Handoff*`, `memory/WEBSITE_AGENT_BRIEF.md`, `memory/WEBSITE_NOTE.md`.

## 6. Mistakes to avoid (seen before)

- Don't invent a Student Choice question bank: it is the website's JEE Main chapter-wise bank (canonical ids).
- Don't claim "live" without a deploy record; don't call a deploy failed without the deployer's evidence.
- Don't suggest "clear cache / hard refresh" as a fix.
- Dates: the earlier guide said "27 Nov" by mistake; today is 26 Nov.
- Rebuilding the book changes the file hash → old owner links stop (403/404). Re-issue grants.
- Chapter papers with 68+ questions never count in Dream College (`chapter`, `choice` kinds excluded).
