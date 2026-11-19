# JEELIVE.AI Native App — PRD

## Analysis 2.0 Phase 1–2 (19 Nov 2026) — DONE
- User: "Phase 1–2 shuru karo, asli test mein time ki sync pakki karo, exactly like jeelive.ai". Choices: keep app WHITE look (cards/charts website-style); yes one real QA practice test.
- Phase 1 verified on a real scripted attempt 9332443d-284c-4456-bf87-a4e506658971 (QA 7004186276): server per-question times, answer change, mark, revisit and 8 s background all matched within 1 s (src/analysis/timeCapture.ts + useAttempt.ts already wired; TS errors from the old handoff were already gone).
- Phase 2: website card language in light theme — Roboto Mono numbers (assets/website-2026-10-26/roboto-mono-latin-400/700, fonts.mono/monoRegular, T w="mono"), Tile with 4px coloured left edge + caps label, Block radius 20 + soft shadow, Overview "Aapka Score" card with big centred ring, 2x2 action buttons (stack icon-over-label under 360 px), Potential 2-col tiles, odd last tile full width, mono numbers in ledger/grids/Qs-by-Qs/Difficulty/bottom bar. iteration_106: all pass; 320 px label clip fixed after.
- Next (user order): Phase 3 comparative → Phase 4 solutions summary / Meri 3 seekh / PDF / share → Phase 5 small screens + real attempt → then login 401 fix.

## Rank + Mission website hand-off ZIP (19 Nov 2026) — DONE, link given to user
- User (Hinglish): ZIP for the website team, NO Rapid Fire, "seedha simple link", link valid 7 days, fresh screenshots, and "rank ka data / colleges alag se nahi likhna chahiye — tumhare server ko call karke bula le".
- So the pack ships NO data copies (no RANK/data, no rank_data, no CSV/JSON dumps, no test vectors, no "host it yourself" option). The website reads every number live from the app server through `CONNECT/backend_fastapi/jeelive_app_connect.py`. docs/05 §1 states the rule; README + START_HERE carry it.
- Build: `cd /app/backend && python ../handoff/build_pack.py` → `/app/handoff/JEELIVE_Rank_Mission_Website_Handoff.zip` (156 files, ~1.7 MB). Sources next to the script: `pack_root/*.md`, `docs/01..10*.md` (03–10 written this session), `connect/`, `shots/` (25 rank + 4 mission, retaken fresh 19 Nov, tab bar hidden so no Rapid Fire button). Script copies read-only server code (`server_reference/`), app UI code (Rapid Fire import rewritten to `shared/whatsapp.ts`, theme.ts stripped of the game palette, DreamCheer/routine/HomeDream left out), 22 rank API samples + 7 PDFs, masked Mission samples, filtered OpenAPI (28 paths), MANIFEST.json, then asserts: no Rapid Fire file/import, no data file, "Rapid Fire" words only in docs + Mission product copy.
- Link: issued with `python tools/owner_download.py issue --artifact rank-mission-handoff-zip --hours 168` (grant e1c45718-04a0-47b1-80ec-44e2326fabde, expires 2026-11-26 10:02 UTC). Served by `owner_downloads.py` on the preview URL. **Rebuilding the ZIP kills the link (SHA check) — re-issue a link after any rebuild.** Never write the bearer URL into files.
- Live server check (connect_check.py): ALL 21 CHECKS PASSED.
- Fork fix again: Metro cache had the old fork URL (share-card-stats…) → moved `.metro-cache` to /tmp/metro-cache-old-*, restarted expo.
- Next (user order): Analysis 2.0 Phases 1–5 → then login session 401 refresh fix.


## Deep audit round 2 (18 Nov 2026) — load test, real mock journey, cleanup (DONE)
- Report: `/app/memory/AUDIT_2026_06.md` section "Deep audit — round 2". Load: 1,000 users app mix 0 errors (p95 46 ms), 1,000 Rapid Fire matches 0 errors, mock proxy 1,000 users 0 errors (00:00 storm 1.4 s). Public preview URL: Cloudflare challenges one machine at 100 users (not our server).
- Fixed: `backend/client_ip.py` — student address = X-Forwarded-For entry 2 before the last (edge + balancer); used by login_guard (8 per number, 100 per address / 15 min), pin_reset, mission_links, website proxy header. Sweep closes archived-exam matches. Socket double-close guarded. Result "2 min 53 sec used". iOS ITSAppUsesNonExemptEncryption false.
- Tests: obsolete suites removed/updated; conftest skips ffmpeg tests without ffmpeg and Cup Night tests after 8 pm IST. 506 pass, 0 fail.
- New load tool `backend/tools/loadtest_app.py` (TEST-loadapp-* grants, `--cleanup`). Never edit files under backend/ during a load test: the preview backend runs with --reload and restarts.
- QA account: one more real attempt `0a7b71fc-648f-4d36-b5b6-c2b182b7c031` (JEE Main PYQ 21 Jan 2026 S2, 5/300, submitted). Do not start more.
- Open (needs owner/Emergent): images via CDN signed links (website), Cloudflare challenge exemption for /api/*, production servers (8-10 × 4 cores + Mongo 4-8 cores), share gate server-side, account deletion.

## Audit June 2026 (5 phases + DB audit) — report only, fixes waiting for approval
- Full findings + numbers: `/app/memory/AUDIT_2026_06.md` (reports iteration_97/98/99). User rule: full list first, then fixes that really hold at 1 lakh students in one mock.
- Built on user request during the audit: Home promo replaced by the Dream College Meter; meter = purple outside (header band + border + glow), deep black inside, rows royal blue/teal alternating with a diamond on every row; Rank tab Dream panel moved into a 6th tile DREAM COLLEGE (`rank-tool-dream`, dark violet metal jewel `violet`, accent `dream`), tiles 3 rows × 2. Result screen + Home wired to Dream; Rank tab missing import fixed.
- Load-test tools: backend/tools/fake_website.py, loadtest_mock.py, proto_proxy.py (benchmark only, not imported by server.py).
- QA account used ONE real attempt: 7f61a0ac-7c68-49ff-b59d-256a6f82ec87 (JEE Main PYQ 22 Jan 2025 S1, −2/300). Do not start more.

## Iteration94–96 — Rank tab: tool form colours, College predictor blood red, college button-cards, Edit pill
- Forms by tool (src/rank/accent.tsx, AccentContext around each pane): Rank predictor yellow, Percentile teal, Target lime, College predictor blood red (white text), Compare sky blue. Each form has a coloured frame, header band, chips, fields and main button. The chosen tile's border and glow use the same colour.
- College predictor tile is pure blood red: Metal jewel `blood` with `pure` (no graphite, no dark streaks or shade). The other tiles keep their graphite metal.
- Collapsed form (Summary) shows a filled glowing "Edit" pill (`<id>-edit`) and the hint "Doosra number dekhna hai?".
- College lists (JEE/COMEDK/BITSAT, src/rank/CollegeCard.tsx) show every college as a card: chance edge, medal, tags, 3 stat boxes and a "Cutoff dekho ›" CTA, plus a tap hint and a "Dekha" tag on opened cards. The first CTA breathes until a college has been opened once.
- Tests: iteration_94/95/96 all pass.

## Iteration93 — Share gate opens on return from WhatsApp + Share Card Stats
- User (Hinglish): result opens "WhatsApp khol kar wapas aane par; Max 3 sec"; then "Share Card Stats: Thank you, ki aapne itne log free education mein help kiya". Choices: a friend counts on opening the student's personal link; the thank-you also shows on the shared picture; "Make it very beautiful".
- Gate: `src/mission/share.ts` `watchReturn()` (AppState; web = visibilitychange). Shares to another app/tab (`away`) unlock only after the student comes back; if the app never leaves, it unlocks after 3 s. iOS sheet / navigator.share dismissed keeps it locked. The note shows under the button that was pressed. Leaving during the thank-you still unlocks.
- Backend `backend/mission_links.py`: GET `/api/rf/mission/me` (RF grant) returns {code, helped, week}. Public GET `/api/j/{code}` redirects (302) to https://jeelive.ai and counts +1 only when both the visitor cookie `jlv` and sha256(ip|ua) are new. Robots, scripts, unknown codes and an empty browser name are never counted; CUBOT phones are allowed. Collections `mission_links`, `mission_visits`.
- Frontend: `src/mission/stats.ts` (useMissionStats; the caption ends with the personal link `<BACKEND>/api/j/<code>`), `ImpactPanel.tsx` on the Mission tab (gold medal count-up, thank-you line, +K is hafte, next milestone track, zero state), and the MissionCard gold thank-you band (`mission-card-thanks`, also on the gate and in the shared PNG). Pull-to-refresh on the Mission tab. Spec: `/app/design_guidelines_mission_stats.md`.
- Tests: `test_reports/iteration_93.json` all pass; `backend/tests/test_iter93_mission_links.py` 19/19. QA account mission code VU6PE38 (helped 0). Native share paths need a real build.
- Next: Paper Ready note per series day, Match Link Stats, Rematch same group, Phase 3 One Server, NEET hand-over pack, APK size.

## Iteration84 — Rank tab: RANK PREDICTOR tile (first) + COLLEGE PREDICTOR tile
- User: rank predictor above college predictor; Home-style tiles; BITSAT left out. `src/rank/PredictorTiles.tsx`, `src/rank/RankPredictor.tsx` (JEE: marks, paper type, category, PwD -> percentile, CRL, category/PwD rank + all 3 paper types side by side; COMEDK: marks -> rank range + percentile + 3 analyses). POST /api/rank/estimate. "Is score se colleges dekho" hands the score to the College tool. Tests `tests/test_rank_estimate.py` (+ tester edges). Reports iteration_84, iteration_85.
- After testing: one query/result per exam (no cross-exam card), COMEDK handover seed cleared after use, rank tool stays mounted when the College tile is open, busy reset on exam switch, paper rows fit 320px (category and PwD rank on their own lines, non-breaking hyphen/dash).

## Iteration82 — Rank: COMEDK + round-wise ladder + sparkle silver / light blood red + JEE data recheck
- User order (Hinglish): COMEDK → round-wise cutoff → elegance → JEE data recheck. COMEDK: only GM (All India); marks OR rank input; marks→rank "pichhle saalon ke data se andaaza" as a range. College tap: closing rank of every round (R1 → last). Look: "Sparkle silver + halka blood red", "beautiful, perfect, elegant".
- Backend `rank_comedk.py` (POST /api/rank/comedk, /api/rank/comedk/college; meta.comedk in GET /api/rank/meta). Data `rank_data/comedk_2026.json` from official COMEDK 2026 Round 1–4 cut-off PDFs, 2025 final, 2026 seat & fee matrix (`tools/rank_data/build_comedk.py fetch|build <raw>`; every numeric PDF cell parsed: R1 1191, R2 181, R3 547, R4 368). 880 GM college-course rows, 148 colleges. Marks→rank = range across 3 public analyses (CollegeDekho 2026, Shiksha 2026, 2024–25 trend), log interpolation, median as mid. Seat closing = max over rounds; demand = min round closing. Tags as JEE (Safe/Likely/Borderline); rank input uses a 5% band for Borderline.
- Frontend: `src/rank/Comedk.tsx`, `ComedkSheet.tsx`, shared `Rounds.tsx` (RoundLadder + RoundTable, used by JEE CollegeSheet too). JEE college cells carry `mine`. MetalCard: blood-red glow + shimmer top edge + light blood-red badge/rule/№, sparkle-silver serif with twinkling SVG glints (reduce-motion safe; worklet check passes). Rank tab accents: blood red / silver (no blue except Likely tag). Design spec: `/app/design_guidelines.json`.
- JEE recheck: `tools/rank_data/verify_jee_data.py <raw>` after a fresh `build_rank_data.py fetch`: 58,382 in-scope official JoSAA/CSAB rows match exactly; rebuilt file identical (10,733 seats, 0 diffs). Out of scope by design: IITs/IISc (JEE Advanced), SPA (B.Arch), DASA quota.
- Fork note: Metro cache had the old backend URL again → moved `.metro-cache` to /tmp and restarted expo.
- Tests: `backend/tests/test_rank_comedk.py` (+ tester's `test_rank_comedk_extended.py`, `test_rank_iter83_fixes.py`, rank predictor/phase2) 80 pass. Reports `test_reports/iteration_82.json`, `iteration_83.json`.
- After testing: tapped branch always in the JEE sheet (NSUT/DTU outside top 10 fixed); JAC Upgrade/Spot = "JAC ne ye rank publish nahi ki"; ladder/table/line use one rule (andar = worst estimate inside, borderline = only part of the range; backend `rank_comedk.ladder_line`); chips show real reachable totals (`reach`); card number sized from window width (fits 320px), foot stacks < 360px.

## Iteration80-81 — JEELIVE.AI Rank (RANK tab): Phase 1 fixes + Phase 2 + fully dark luxury look
- User (Hinglish): Phase 2 incl. BITSAT (official page https://admissions.bits-pilani.ac.in/FD/BITSAT_cutOffs.html), rank card in the user's reference theme (dark brushed metal, silver serif, electric-blue hairline + tracked caps, № serial — "take it as the theme, do not copy"); then "elegance is missing — whole screen dark"; and NO shift picker ("next-year students won't match 2026 shift dates"; ask shift only after next year's paper data exists). Easy/Normal/Tough stays.
- Backend `rank_predictor.py` (/api/rank, public): college() blocks paths not open to the student (`blocked` + "Ye raasta aapke liye nahi: …", no green cells); CRL clamped to candidates; 50-item lists mix ≤20 Borderline / 15 Likely / 15 Safe ordered by demand; items carry `y25` (JoSAA 2025 final round, `rank_data/jee_main_2025_close.json.gz`, built by `tools/rank_data/build_trend_2025.py` from the official JoSAA archive) and `y26` (2026 JoSAA final); college sheet has a `2025 R6` column. `rank_bitsat.py` POST /api/rank/bitsat {score −130..390, campus, degree} from `rank_data/bitsat_cutoffs.json` (official 2022–2026 finals, 50 programs; Safe ≥ cutoff+10, Likely ≥ cutoff, Borderline cutoff−5..−1, near ≤20 below).
- Frontend `src/rank/`: `MetalCard.tsx` (Rank Card shell, gradients only, system serif), `ResultCard.tsx` (JEE card), `Bitsat.tsx` (BITSAT input/card/list with 5-year history), `shortlist.ts` (phone storage `rank.shortlist.v1`) + `ShortlistSheet.tsx`, `share.ts` (WhatsApp text via rapid/social `sendWhatsApp`). Whole tab dark: `rankColors` palette in `theme.ts` given through `PaletteContext` in `app/(tabs)/rank.tsx`; `DSheet` now follows the palette (other screens unchanged). Trend arrows: ▲ tough hua / ▼ aasaan hua on both exams.
- Tests: `backend/tests/test_rank_predictor.py`, `backend/tests/test_rank_phase2.py` (run with EXPO_BACKEND_URL set).
- Next: account deletion (store blocker), Rank Phase 3 (choice-filling list, live round tracker), match-link stats/preview card.


## Iteration79 — Installed app closed on the Cheer Squad show (ROOT CAUSE fixed)
- User (frustrated, English this time): "app is crashing when buying cheerleaders and in the rapid-fire section somewhere… The app should not crash."
- Root cause: `src/rapid/CheerSquad.tsx` — the banner's `carry` worklet (`useAnimatedStyle`) called `hand()`, an ordinary function. On a phone, worklets run on the UI thread and an ordinary function is a "remote function": calling it throws `[Worklets] Tried to synchronously call a Remote Function. Called "hand" on the UI Runtime` → fatal in a release build → the app closes. The browser has no separate UI thread, so web preview and every web test passed.
- Where it closed the app: (1) right after buying a squad (the new squad's show opens by itself), (2) Preview on `/rapid/squads`, (3) opening the profile of ANY player with a cup win (`player/[pid].tsx` mounts `<CheerSquad visible={false}>`, and the worklet runs even while hidden): own profile after a cup win, Champions Wall → CHEER, SEE MY CROWN, friends with a crown.
- Fix: `hand()` replaced by a plain number array `hands` (no function inside the worklet). Purchases made before the crash are safe: `squads.py` buy is atomic and a second buy answers 409 "You already have this squad".
- New guard: `cd /app/frontend && node scripts/check-worklets.js` — fails when any worklet (Reanimated hook callback, gesture callback, animation callback, `"worklet"` function) calls an ordinary function or a non-Reanimated import. Passes now (149 files); flags the old code. **Run it after touching any animation; web tests cannot see this class of crash.**
- Also audited (clean): every worklet closure in `app/` + `src/` (Entry, session swipe, StreakGem, juice, Art, arena, CrownCelebration, CheerBanner…), raw text outside `<Text>`, JS APIs missing on Hermes.
- Verified here: the plugin-compiled `carry` worklet run with phone-UI-thread rules throws before the fix and returns a style after it; web preview Preview → squad dances as before; arena web bundle rebuilt (7.6 MB). NOT verified on a phone (no native runtime here): user must Publish and make a new Android build, then try buy / Preview / a champion's profile.


## Iteration76 — One brand (JEELIVE.AI), website-driven exams/sections, browser arena (Phase 1 of "website + app = one")
- User-approved plan (Hinglish, plan mode): app renamed back to **JEELIVE.AI**; exams and sections come from the website; Rapid Fire opens in a browser for website students; a copy-paste note for the website project. Phases 2/3 (website SSO ticket, Rapid Fire on jeelive.ai's own address/server, NEET hand-over pack) are NOT built.
- **Name/logo:** `app.json` name JEELIVE.AI; `src/assets/brandLogo.ts` is now the website's original logo SVG (source SHA-256 4cec3778…faff2, only role/aria/title removed); splash PNG re-rendered from that SVG with the dark wordmark (same size 1132×452, same filename). All visible JEECIRCLE text replaced in app screens, `legal/content.json`, `legal_pages.py`, `rooms.py` link pages, WhatsApp/share texts. Package id, slug, scheme, icon and marketing videos unchanged. `tests/test_iter58_brand_legal.py` now expects JEELIVE.
- **Website content:** new `src/api/examCatalog.ts` (`useExams`, `useExam`, `cataloguePath`, `examIcon`, `cachedExamName`) reads the website's `GET /catalog/exams` and `GET /catalog/exams/{slug}` through the existing `/api/jl` proxy (no backend change). Home Practice grid, ExamHub rows and My Tests exam chips are built from it and re-read on focus, app foreground and pull-to-refresh. Built-in three exams are used only while loading or when the website can't be reached. A 404 for an exam = hidden → "not available" screen. Custom (owner-made) sections open `/catalogue?slug=&kind=&section=<slug>`.
  - Behaviour change: the old redirect of `jee-main` + `kind=mocks` to PYQ is removed, so a JEE Main "Mock Tests" section is reachable whenever the website lists it. PYQ stays first for JEE Main. No screen inside the app links to `jee-main&kind=mocks` unless the website lists that section.
  - Live website, observed in this session (read-only): 3 exams. BITSAT sections mocks/chapters; COMEDK sends no sections (app shows the two default boxes). JEE Main listed pyq/mocks(2 live)/chapters at 22:13 UTC and the app showed a "Mock Tests" row; by 22:28 UTC the website listed only pyq/chapters and answered 404 "This section is not available." for `kind=mocks`. Cause unknown (not changed from this project: only GET requests and sign-in/sign-out were sent). Do not assume either state; read the live list.
  - NOT exercised: a brand-new exam or an owner-created section (needs the owner panel). The request shape for a named section (`kind=mocks&section=<slug>`, website answers with that section's own layout) was inferred by probing the built-in sections only.
- **Browser arena:** `src/arenaMode.ts` (`ARENA`, `HOME_ROUTE`, `arenaAllows`) switches the web build to Rapid Fire only when it is served under `/api/arena`: 480 px column on a blood-red stage (window width clamped for `useWindowDimensions`), non-arena routes redirect to the lobby, arena bar Home → jeelive.ai, own profile has "Account & sign out", `BACKEND` = the page's own origin. `backend/arena_web.py` serves the static export from `backend/arena_web/` (hashed files cached a year, index no-cache, path-escape safe). Build with `/app/scripts/build_arena_web.sh` (sets `JEELIVE_ARENA_EXPORT=1` → `experiments.baseUrl=/api/arena` in `app.config.js`); **re-run it after any app screen change, then Publish.** `.easignore` keeps `backend/` out of EAS, so the APK does not grow (arena folder ≈7.6 MB on the server).
  - Same phone + PIN, same `X-JL-Sid` proxy sign-in and same `/api/rf/access` grant as the app: same ID, wallet, one player pool. No new auth code was written; the integration playbook's SSO ticket design is only described in the note for Phase 2.
  - Verified in preview only: `/api/arena` at 1280 px → sign-in → lobby (column 480 px, app tab bar absent). Live `https://jeelive-mobile.emergent.host/api/arena` returns 404 until the user Publishes.
- **Website note:** `/app/memory/WEBSITE_NOTE.md` (Rapid Fire button + link, name/logo rules, Phase 2 one-time 60 s ticket hand-off). Nothing in the website project was changed from here.
- User actions: Publish (arena goes live), then a new Android build (name, website exam list and the iteration75 connection fix arrive together).

## Iteration75 — Installed APK "Connection interrupted" ROOT CAUSE fixed
- Deployer RCA (`/app/deployer-agent-docs/RCA_780f04ff-...MD`): both `.easignore` files excluded `.env`, so EAS never got `frontend/.env` (where the pipeline writes the production EXPO_PUBLIC_BACKEND_URL) → `extra.backendUrl` undefined → fetch("undefined/api/...") failed on the phone. This was also the real cause of the iteration71 phone-login bug.
- Fix: `.env` exclusions removed from `/app/.easignore` and `/app/frontend/.easignore` (key/secret excludes kept). `client.ts` now says "This app build is missing its server address" if a build ever lacks it. User must re-Publish and generate a new Android build. NEVER exclude frontend/.env from EAS again.

## Iteration74 — 100k scale: many servers through the database + cheerleader shortfall
- User (Hinglish): "Pehle 100k scaling poori karo; Pehle diamonds se cheerleader" (both), servers joined through "Apne database se hi jodo" (no Redis), squad price "Har cheerleader ki alag keemat" (already: Gold 8 Red+2 Blue, Royal 6 Blue+2 Emerald, Legend 3 Emerald+2 Gold; Rookie opens on the first cup win), short of diamonds → "Kitne aur chahiye, wo batao".
- Backend: addressed live channel (`rf_duels.ws_nodes`, events `to`/`by.<node>`, capped 128 MB), one-trip answers (`quick_answer` pipeline update), cross-server spectator count `rf_watch`, inbox `poll_s` (8, 20 when busy), Mongo pool 40, cached collection objects (`Collections` in server.py), practice-rival runs cached. Squad 409 message now lists the exact shortfall. Details + numbers: `memory/SCALE.md`.
- Frontend: `ShortNote` in StoreParts ("NEED 3 more Ruby…", testIDs `squad-<id>-short`, `squad-buy-short`); InboxPoller polls every 25 s inside rapid/duel, session, watch and follows `poll_s`.
- Fix after testing (`test_reports/iteration_72.json`): squad buy no longer charges diamonds for a squad already opened by cup wins (409 'Tap USE'); price buttons 44 px; clearer shortfall a11y label. Tester file `tests/test_iter75_review.py` passes.
- Tests: `tests/test_iter74_multiserver.py` (4, two of them need RF_NODE_B), iter73/phase3/iter69 pass. Load: 3000 students on 3 workers (practice rivals and student vs student) with 0 errors. 100k itself needs production capacity (~50 app cores + a big MongoDB) — to arrange with Emergent support.

## Iteration72 — Security audit + simple Forgot PIN
- Security audit (read-only): CONDITIONAL PASS. SEC-001 session handle (X-JL-Sid jar) no TTL/rotation; SEC-002 4-digit PIN brute force via proxy (shared server IP). User chose "Abhi nahi" — not fixed yet. Positive: Set-Cookie never returned, server-priced atomic buys, server-derived RF identity, strict CORS.
- Forgot PIN (owner's explicit choice, no OTP, warned twice): `backend/pin_reset.py` POST `/api/account/forgot-pin` {phone,new_pin,confirm_pin} → owner login (env JEELIVE_OWNER_EMAIL/PASSWORD, in-process cookies) → `admin/students?q=` exact last-10-digit match → `auth/owner/student-pin-reset` with expected_pin_version. Throttle 5/h per number, 30/h per IP (rightmost X-Forwarded-For), log in Mongo `pin_resets`. `app/forgot-pin.tsx`: phone + new PIN + confirm → Set new PIN → auto sign-in → Home.
- Tested: `test_reports/iteration_71.json` (tester naming) — backend 10/10 (`tests/test_forgot_pin_iter72.py`), real reset of QA number to the SAME PIN 5524 → auto sign-in → Home, sign-out → sign-in OK. Fixed after: IP from rightmost XFF hop, guard missing pin_version (503 not 500), countdown in minutes, removed real-reset test file.

## Iteration71 — Phone login fix (all platforms through our server)
- Bug: installed Android app showed "Couldn't check your session…" + "Connection interrupted" on sign-in (preview + live); native fetch to https://jeelive.ai/api threw on the phone while the phone browser opened jeelive.ai. Deployer RCA: production backend healthy, no failing requests.
- Fix (user approved): `src/api/client.ts` BASE = `${EXPO_PUBLIC_BACKEND_URL}/api/jl` on every platform with X-JL-Sid (web AsyncStorage `jl_sid`; native SecureStore `jl_sid`, falls back to AsyncStorage if the Keychain write fails). Native cookie capture removed; `/api/rf/access` always X-JL-Sid + `{}`. `rf_access.py` still accepts old builds' `access_cookie` (kept for already-installed builds).
- Tested: `test_reports/iteration_70.json` — backend 10/10 (`tests/test_iter70_native_proxy_login.py`), web sign-in → Home, Rapid Fire, Store, reload persistence, sign-out → sign-in all pass. Native not runnable here: user must republish and install a new Android build.

## Deployment health check (after iteration70)
- First check FAILED: rf_feed TTL index auto-deleted feed rows; Redis (unsupported in production). Fixed: startup now drops the old `at_1` TTL index (rows kept, reads already show last 7 days); `metadata_cache.py` is memory-only (no redis import), redis/hiredis removed from requirements, `redis_runtime.py/.json`, Redis tests and the `jeelive-redis` supervisor program removed (backup conf at /tmp/jeelive-redis.conf.bak). Also deleted `frontend/eas.json` (pipeline makes its own; the apk-arm64 profile is gone) and `frontend/package-lock.json` (yarn only).
- Re-check: status WARN, no blockers. Remaining WARN: root .gitignore ignores .env (platform-managed, left as is). INFO: backend legal_pages.py reads frontend/src/legal/content.json at import (works in monorepo).

## Latest iteration70 — Stadium Cheer banner, diamond unlock, smaller Android bundle
- User (Hinglish): board "chamak nahi rha, baccho jaisa lag rha, sexy rugby match jaisa nahi"; chose "Diamonds se cheerleader kharidna" with rule "wins se apne aap level + diamonds se jaldi unlock"; and "APK size jaanch (<20MB)".
- `src/rapid/CheerBanner.tsx` (new): pro-stadium banner — satin cloth with cut corners + gloss, metallic trim, leaning metallic-foil CONGRATULATIONS! (SVG text, outline + shadow), glint sweep, glitter (10/13/15/18 by level), swaying fringe, halo pulsing on each count, spear-tip poles; corner stripes only when banner ≥210 px so the name always fits. Colours per level in theme `cheer` (1 crimson/gold, 2 black/gold, 3 sapphire/silver, 4 plum/rose-gold), `arena.glint`. Old bulbs/rainbow letters removed. Lead dancer now renders under the banner.
- Diamonds: backend `squads.py` buy/equip already existed. `/rapid/squads` Buy opens confirm sheet (`squad-buy-*`); after buying coin sfx, arena profile reload, the new squad dances at once. Store tab has a CHEER SQUADS card (`shop-squads`) → `/rapid/squads`; diamond wallet shows a skeleton while loading (no fake zeros).
- Size: removed unused optional dep `expo-symbols` (only expo-router's Android native-tabs converter required it; Android uses our own tab bar). Android export (no bytecode) JS 4.63 MB + assets 3.28 MB = **7.91 MB** (was 8.94 MB; 962 KB Material Symbols font gone). Signed APK still not built here — <20 MB unverified. Further option: subset MaterialDesignIcons.ttf (1.3 MB) — not done (icons also come from backend data).
- Testing: `test_reports/iteration_69.json` (tester naming) — backend 4/4 squads, all flows pass; 320 name-cut bug + medal gap + pom-pom overlap + store zeros fixed and re-verified by main at 320/390. Helper `/app/tests/iter70_qa_wallet.py` (backup/raise/restore QA diamonds); QA wallet restored to 7/4/1.
## Latest iteration64 — Cup Champion Showcase
- User choices: count ALL cup wins, real-player wins shown apart; list of past cup wins on the profile; crown next to names in leagues, Gang War and friend lists. "World best and perfect".
- Backend: `crown_of(p)` in `gamify.py` → `{"won", "real"}` or null, added to `social.card()` (all player cards), `/leaderboard`, `/league/friends`, `/league/gangwar`. `cups.finish` increments `cups_real` when 2+ real players. `/players/{pid}` returns `cups {won, real, played, recent[5]}`. One-time startup backfill `backfill_cup_crowns()` (marker `rf_meta._id=cup_crowns_v1`). Index rf_cups (champion, status, finished_ts).
- Frontend: `src/rapid/CupShowcase.tsx` (trophy hero, titles, 4 stat tiles, latest titles with BEAT N REAL / PRACTICE tags, gold/silver legend, own-profile CTA). `Crown`, `NameLine`, `crownText` in `parts.tsx` — gold crown = beat real players, silver = practice cups, ×N. Used in PersonRow, BoardRow + podium (Leagues), All India rows, player card. Gang tab Challenge button becomes icon-only < 360 px.
- Fixture seeds cup titles: Diya gold ×3, Aarav silver ×1, Kabir none; cleanup removes `fixture-cup-*` cups.
- Testing: `test_reports/iteration_64.json` all pass (backend 16/16 incl. new `tests/test_rf_cup_crowns.py`); minor polish then fixed (a11y labels include crown, Win % capped, podium testID, shorter win row, legend 11 px).

## iteration62/63 — Rapid Fire Phase 3 wired: multi-pick battleground, Knockout Cup, live watch, Badla lo, Friends League, Gang War board
- User (Hinglish) confirmed order; Badla choice = **"Pehle subject/chapter dobara chunein"** (choose battleground first, then same opponent gets the challenge). Asked for "Beautiful, powerful" / "World's best" Knockout UI.
- **Battleground** (`src/rapid/scope.ts`, `ScopeSheet.tsx`): up to 5 picks (whole subject or chapter), PCM Mixed, Quick Mix tiles, chapter tabs/search/tray, 6th pick warning. Lobby `SubjectChips` one row (icons hidden < 380 px, 44 px tall). Used by lobby, Play Friends, Cup hub, Gang War.
- **Knockout Cup** (`app/rapid/cup/index.tsx`, `cup/[cid].tsx`, backend `cups.py`): Open (40 s lobby, practice rivals fill) / Friends (host START, empty seats = BYE, invited list `invited_players` + WhatsApp remind, cancel confirm), 4/8/16, prizes strip, watch-by-code (max 100), seat progress bar, bracket that slides to the current round, champion panel, NEW CUP. Cup duel opened by link returns to its bracket.
- **Live watch** (`app/rapid/watch/[did].tsx`, `LiveStrip.tsx`): friends/gang mates/cup members, questions hidden, max 100 watchers.
- **Badla lo** (`useBadla` in `HeadToHead.tsx`, used by MatchResult, player profile, h2h sheet): opens `rf-badla-sheet` prefilled with the lost match's picks → `POST /api/rf/challenges {rematch_of, picks}` (backend `rooms.py` now honours new picks; without picks keeps old scope). h2h API + profile `head_to_head.last` include `picks`. 1 v 1 room: one open seat, label in header, "Badla lo! 🔥" title + `room-revenge` banner.
- **Boards** (`Leagues.tsx`, Trophy → Ranks: All India / Friends / Gang War): weekly Friends League with last-week podium claim; Gang War top 100 scorers. Gang form has Gang / Batch (200, open link) segment.
- Fork fix: Metro cache had the old backend URL baked in (CORS failure on login) — cache moved to `/tmp/metro-cache-old-*` and rebuilt. Do this again if a fork shows "Couldn't check your session".
- Fixture `tests/rf_social_fixture.py` now sweeps orphan `TEST-fixture-*` profiles when its state file is missing (an orphan run was removed). Cleaned after testing.
- Testing: `test_reports/iteration_62.json` and `iteration_63.json` — backend 15/15 (`test_rf_phase3.py`, `test_rf_phase3_live_api.py`, `test_rf_iter63_cup_invited_live.py`; run with `-o addopts=`), frontend ~95 % then the last low items fixed (room Remind label, watch-code error now inside the watch panel, duo seats centred, h2h date first, cup header shorter, bracket scroll left-aligned). QA learner history now has a few finished/cancelled cups and cancelled Badla rooms from testing.
- Pending: video ZIP check (user deferred), delete old `backend/tools/make_*` scripts before build (ask first), signed APK < 20 MB unverified, physical-device check.

## Latest iteration61 — Rapid Fire 2.0: Friend activity, Head-to-head history, Rival streak diamonds, Blood Red Arena
- User asks (Hinglish): "Rival ke streak diamonds; Head-to-head history; Friend Activity feed", full test + screenshots. Also: "rapid. maroon pr blue me mza nahin aaya, blood red with a shining ?" — read as: inside Rapid Fire the navy-blue cards on the maroon stage are out; make it blood red with a shine. **This colour reading is an assumption shown to the user with screenshots; adjust only `arena` tokens in `src/theme.ts` if they want it different.**
- Previous fork had written `FriendFeed.tsx`, `HeadToHead.tsx`, `RushTrack.tsx`, `StoreParts.tsx` but only imported them (player profile even crashed: `Face` not defined). This fork wired everything:
  - **Friend activity** (`FriendFeed` in Gang tab, under the three action tiles): last 7 days of the players you added — 1 v 1 / gang / group wins, win runs (3, 5, 10), Emerald/Gold/Kohinoor diamonds, level-ups, trophies. 3 rows + "See all (n)"; a row opens that player's profile. Hidden when you have no friends. API `GET /api/rf/feed` (collection `rf_feed`, written by `gamify.award`, TTL 14 days, never for `TEST*` uids).
  - **Head-to-head** (`HeadToHeadCard` on a player's profile): running score; tap opens a sheet with recent-form dots (W/L/T) and every 1 v 1 match (last 30); a row opens the match review. API `GET /api/rf/players/{pid}/h2h`.
  - **Rival streak diamonds**: `RivalGem` beside the rival's score in the live 1 v 1 strip (`duel-opp-streak`) and on each rival cell in 3–5 player matches, shown from 3 correct in a row. Practice rivals now get a fixed-per-match random sequence of right/wrong cards (`simulate_bot`, `random.Random(duel id)`), so they have real runs; before, their score was `round(n × acc)` and almost never reached 3 in a row. Holding the rival behind a student who is really playing is unchanged.
  - Player profile shows the portrait between Phoenix wings in the colour of the rarest diamond ever won (`WingedFace`, sized for 320 px).
  - **Diamond Rush** (`RushTrack` in Trophy → Rewards): diamonds won today move a track with 5 chests (1/3/6/10/15 → 25/50/80+freeze/120+Blue/200+Gold), `POST /api/rf/rush/claim`. Trophy badge and lobby Quests badge count ready quests + ready chests (`rewardsReady`).
  - **Diamond specials in the Store**: `DiamondWallet` panel, `PriceButton` (coins or diamonds), purchase sheet with diamond cost; diamond-priced avatars no longer show "Use · Free".
- **Sync fix (real bug found by testing):** the game profile is read by several mounted components (top strip, arena bar, tab body); a reload in one did not reach the others, so coins at the top stayed stale after claiming a chest/quest or buying. `ResourceCache.subscribe` + a subscription in `useCached` now give every screen showing the same key the fresh value as soon as any one of them loads it. Store purchases reload the profile.
- **Blood Red Arena** (`arena` + `rapidColors` in `src/theme.ts`, `ArenaBg`/`Panel` in `src/rapid/arena.tsx`): stage `#B0101E → #7C0913 → #45050C` with a hot glow at the top and a slow band of light (off with Reduce Motion and behind questions); cards are black-cherry glass (`#16070A`, ruby rim `#8E2231`, glossy top). No navy left in Rapid Fire. Teal buttons, gold titles, diamond colours, Home tab and the royal-blue dock diamond are unchanged.
- Testing: `test_reports/iteration_61.json` — backend 8/8 (`backend/tests/test_rf_iter61_new_apis.py` + `test_rf_social.py`; run with `-o addopts=`), frontend all flows pass at 390 and 320. Main agent then fixed and re-verified in the browser: coins 102 → 127 at the top after a Bronze chest, top diamonds 12 → 6 after buying Ruby Blaze, trophy badge 2 → 1, and the rival's streak diamond in a live Practice Rival match. `backend/tests/test_rf_duels_ws.py` is a stale pre-grant test (fails on auth, unrelated).
- QA data: `python tests/rf_social_fixture.py seed|cleanup` (three `TEST-fixture-*` friends, feed rows, four 1 v 1 matches, diamonds for the approved QA learner). **Cleaned up after testing** — the QA learner has no fake friends left. Two forfeited Practice Rival matches played during verification remain in that account's Rapid Fire history.
- Pending / next: user to confirm the blood-red look; video ZIP check ("baad mein bataunga"); Phase 3 (friends-only leaderboard + weekly friend leagues, Gang vs Gang leagues + batch groups, knockout tournaments + spectating); delete old `backend/tools/make_*` art scripts only after asking; signed APK < 20 MB still unverified; physical-device check of the new screens.



## Latest iteration60 + follow-up — CRED polish, Rank tab, 2×2 practice grid, tablet player, royal maroon / royal-blue glass
- User asks (Hinglish): fix all iter59 items; All India card "thoda better, kafi casual hai"; 4 practice tiles bigger in a 2×2 grid; replace JEE Main tab with Rank (feature to be built later); then tablet test screen. Follow-up: exam names in royal maroon matte so they show clearly; Rapid Fire dock button royal blue with a CRED-style glass look (ref: green "unclaimed reward" pill). Rapid Fire screens untouched.
- Home: HomeSeriesCard is onyx→ruby gradient + SVG radial red glow (explicit stopOpacity) + hairline sheen, live chip, 3-column facts strip (75 questions | 180 minutes | +4/−1), bigger ring, glowing red CTA. `ExamGrid` (HomeParts) replaces the rail: 2×2 tiles 168px (150 under 360px), exam names heavy royal maroon `custom_royalMaroon #7A1F35`, value muted. PromoBanner hides "200+" under 360px, CTA 44px. Footer watermark aria-hidden. ExamHub title is maroon too (ScreenHeader `titleColor`).
- Tabs: HOME, RANK (podium glyph), RAPID FIRE, MY TESTS, MISSION; `app/(tabs)/jee.tsx` deleted, `rank.tsx` is an honest "coming soon" placeholder (no fake ranks) with links to /live and My Tests → Completed. Rapid Fire dock button is now a royal-blue rhombus diamond (tall ♦ octahedron, many facets, sparkles, glow) with a small golden flame inside that flickers (user asked "rhombus, royal blue not sky blue"; before that: cube → clean round blue diamond) (`RapidGem` in tabs layout cross-fades `rapid-gem.webp` and `rapid-gem-flicker.webp`, two flame edits of the same rhombus (outline IoU 0.999), Reanimated loop, off under reduce-motion; 190×224 (artwork scaled 1.2× wide, 0.8× tall on user request; dock 48×56, 41×48 under 360px), ~15KB each, transparent; made with Gemini 3 Pro Image; alpha mask uses blue channel > 170 for royal blue; made with Gemini 3 Pro Image on black, alpha from the cyan outline silhouette + soft glow) rising out of the dock (66×60, 57×52 under 360px, scale 1.08 when focused); unfocused label light royal blue `custom_gemBlue #8FA8FF`. History: royal-blue glass capsule → winged ruby diamond → blue diamond (user requests). Labels 10.5px (10 under 360). iOS NativeTabs: rank trigger, red tint.
- iter59 fixes: contrast (pyq subtitle, /live skipped + lock icons, `custom_eyebrow` now #74747E ≈4.6:1), set-detail eyebrow wraps + internal source line hidden, black selection everywhere (chapter chips, solutions subject tabs, My Tests exam chips + divider, player options/integer input), score colours (negative red, zero ink, positive green; preparing amber), catalogue count spacing, web search focus outline removed (`noOutline`), DayMap hitSlop, white splash with dark wordmark (app.json splash bg #FFFFFF; adaptive icon unchanged).
- Player tablet layout: ≥600px centred 760px column/dock; ≥900px right side panel (360px) with legend + palette (`side-q-*`), Palette button hidden. Orientation stays portrait in app.json (Android 16 large screens may rotate anyway; layout adapts by width).
- Testing: iteration_60 frontend PASS for all items (player verified with a browser-only fake attempt; no academic writes). Follow-up legend truncation fixed; maroon/glass verified by screenshots 390/320.
- Pending: account deletion (ask user for PIN-backend repo — user said "kal mangna"); video ZIP check; signed APK <20MB; Rank feature design later.


## Latest iteration58 — teal instead of purple, red/black All India card, Result/Solutions theme, JEECIRCLE.AI rename
- User asked (Phase 1 review): light purple → teal everywhere; Home All India card back to red & black like before; Result + Solutions = colour/theme only (no function/content change); rename the app to jeecircle.ai everywhere.
- theme.ts: Maths subject, neon violet and epic rarity tokens are now teal; the upcoming pastel is teal and done is soft green (so the two stay distinct); marked-for-review is teal #0D9488 with ink #5EEAD4. Rapid Fire violet tokens are teal too; duel opponent score is amber and RF Maths is amber so they don't clash with the teal Physics colour; history loss is muted. Pill kind renamed purple→teal.
- HomeSeriesCard is back on the original ruby/onyx surface (ExamCardFinish live layers + shine, red CTA, website 100% AI badge gradient) with all the new content kept (ring, status accent dot, streak/skipped, CTA). The Live JEE Series tile is now dark with a red glow (pastel tone prop removed from ExamTile).
- Result screen: ScreenHeader, white-active pill tabs, red→black score card, dark stat tiles, dark solution card/rail/grid/reflection; AiSolution sections restyled. Logic and testIDs unchanged.
- Rename: new bundled SVG logo `src/assets/brandLogo.ts` (original emblem + tagline, "JeeCircle.ai" wordmark drawn from Figtree-800 as paths) — BrandMark no longer fetches the logo, so it draws instantly. Splash PNG regenerated (same filename). app.json name JEECIRCLE.AI; all user-visible JEELIVE text in app, legal content.json, backend legal_pages changed. Website/API domain links (jeelive.ai), package id, slug, storage paths, cache keys and marketing video files are intentionally unchanged.
- Bug fix: `useCached` re-requests (max 2 times) when a shared read is aborted by a central reset while the screen is still mounted. This fixes `/live` opened cold being stuck on the skeleton (tester reproduced 2/3; main verified cold /live 3/3 PASS).
- Env: `redis-server` disappears when the pod resets (apt packages don't persist); reinstalled via apt for the preview. The backend works without it.
- Testing: iteration_58 frontend PASS for every requested item (no purple left anywhere in the rendered UI; layout OK at 320/390). Low: 4 avatar images and the RF hero art still contain violet pixels (images, not theme).
- Pending: user to send the PIN-backend repo link for account deletion (they said yes); user to check the video ZIP download; signed APK <20MB still unverified.

## Latest iteration56 — compatible ZIP and standalone download page
- User exact: **“Direct toh aur doenload nahi ho rha zip.me shi format do ya kuch aise do jo ho doenload . Actually click krte hi preview khul ja rha app ka”**. Repeated delivery complaint; do not call resolved on their phone solely from server/browser tests.
- Confirmed existing public MP4 attachment responses and correct bytes/no redirect; app has no associated-domain/universal-link rules. **Actual chat/device interception cause unproven.** Troubleshooter again guessed WhatsApp/Telegram; support search stopped/unverified and found no documented actual chat attachment/alternate-host mechanism. Do not repeat that guess as fact or claim a native chat attachment was supplied.
- Created NEW plain, unencrypted `JEELIVE-Mobile-Videos-45s.zip`, **13,403,359bytes**, SHA256`8672f7bb38fcc47146c58ea01b4dfc8cc2de168cf465b84b3543a80cd3ff8c84`. Exactly2ASCIIrootZIP_STOREDfiles: `JEELIVE-Mobile-Vertical-45s.mp4` + `JEELIVE-Mobile-Landscape-45s.mp4`; bit-identical to prior verified720pbaselineH264/AAC files. Managed UUID upload/readback verified. All previous9assets including OLDmasterZIP unchanged; allowlist now10.
- New fixed public routes `/api/marketing/launch/launch-mobile-pack.zip` and short alias **`/api/marketing/videos.zip`**, both always file attachments, same hash/bytes/ranges/HEAD/304. User-facing **`/api/marketing/downloads`** is a standalone static download document outside Expo/router/login with real form ZIP button, individualMP4download links, exact13.4MBlabel and unzip instructions. CSP blocks scripts; no credentials, learner data or frontend/native app changes. Media remains outsideAPKbundle.
- Publishing: `python marketing/launch45/download_pack.py --publish --mobile`; optional flag preserves old defaultmasterZIP; idempotent early-return avoids duplicatePUT. Regular fullpublisher preserves mobileZIPentry. No publicupload or arbitraryfileproxy added.
- Main actual browser ZIPbutton download→complete13403359bytes→PKmagic/CRC/extract/memberSHA PASS. Independent **100/100scopedpytest PASS**,3/3actualbrowserdownloads ZIP+bothMP4 exactfilenames/bytes/SHA with pageunchanged,320/390nooverflow/min44pxtargets, bothPUBLICdownloaded/extractedvideosfullydecoded, original9records/masterZIPpreserved. Savedbrowserregressionpassed via browserrunner; backendPythonhasnoPlaywright, notanappruntimeissue. Report`test_reports/iteration_56.json`; browserproof`test_reports/artifacts_iter56/browser_results.json`.
- Main pinned testpreservationbaseline to9a22b91 ratherthanvolatileHEADsofutureworkspacecommitdoesn'tbreaktest. Earlier test-onlycontent-length/cloudflare-scriptassumptions corrected: GETmaychunkwithoutlength,HEADcorrect; edgeinjectedscriptsblockedbyCSP. Not productfailures.
- **P0 pending user confirmation:** finalreply must give FULLURL as copyablecodeblock, ask openinChrome/Safariaddressbar (notjusttapthechatpreviewlink), pressDownloadZIP,Files→Downloads→Extract→openMP4. No login. Ifstillopensapp, need screenshot/addressbar+actualbrowser to investigate; don'treissueidenticallinks/calluniversallyfixed. ExistingphysicalAndroidperformance/<20MBartifact/deferreddeletionbacklogunchanged.

## Latest iteration55 — session reliability, list refresh and compatible videos
- User confirmed **“Pehle logout aur list loading”** and **“World best banao na”**. Scope: verify/fix unexpected logout and slow mocks first, then phone-compatible MP4 delivery. No redesign, academic writes, PIN changes, new accounts or RF gameplay changes.
- Independent regression found FOUR real edge-case defects in inherited changes: GET/session and POST/refresh rotating concurrently; null/malformed refresh401 being treated as expiry; automatic ChangePIN POST replay; caller abort waiting for shared refresh. These were reproduced with isolated transport, NOT by revoking a live user's cookies.
- Fixed client rotation ordering (ordinary data reads stay parallel), successful session token revision, bounded refresh JSON-body parsing and verified denial classification; /auth/pin is non-replayable; aborted readers settle without cancelling another reader's renewal. Genuine expiry still clears private state once; cached profile never authenticates. Epoch/draft protections retained.
- Web proxy now orders rotating requests per SID within the CURRENT worker and merges only incoming cookie changes instead of overwriting newer whole jars. Weak locks are reclaimed and waits bounded. **Not distributed locking:** multiple web-proxy workers still require coordinated leases/shared jar-cache invalidation before a multiworker reliability claim. Native uses canonical API directly plus the client ordering, not these proxy locks.
- Lists: inherited 10s account-keyed catalogue/PYQ RAM freshness retained; matching cached key can paint immediately; manual refresh has accurate state; catalogue and MyTests check on refocus/foreground; bounded/memoized mock rows and catalogue pull-refresh added. Private MyTests counts always revalidate. Current server actions remain authoritative, originals/theme preserved. No claim of0ms rendering or world's-fastest app.
- **Verified:**23/23 new actual-module auth/cache/focus tests +7/7 iter49 regressions PASS; tsc/JS/Python lints PASS. Backend/media final **96/96 PASS** includes proxy race, no unsafe auth retries, published files/allowlist/ranges/downloads/full original+compatible decodes. Original failure report55 retained; followup `test_reports/iteration_55_main_followup.json` records corrections.
- Main REAL read-only phone preview: one successful existing-account login; BITSAT50 mocks, page2, search/clear resets page1, back/revisit; all3 MyTests tabs. Injected503 preserved10 visible completed rows and session; restored real API Retry200 recovered.320px no overflow. BITSAT visible-navigation samples462ms initial/468ms warm; agent's earlier PYQ247ms first/137ms warm with Home prefetch. **Browser samples, not Android measurements or benchmarks.** No attempts created/visited/answered/submitted; no PIN/wallet/history writes.
- Handoff video claim corrected: compatible MP4s existed only locally, old public links still delivered originals. Added verified UUID-managed-storage objects + fixed public routes **`/api/marketing/launch/vertical-mobile.mp4`** (7,032,763bytes) and **`landscape-mobile.mp4`** (6,370,296bytes). `?download=1` attachment. Both45s/30fps/720p/H264 constrained-baseline level3.1/yuv420p/AAC-LC44.1k/stereo/faststart and full decode pass. Originals and original ZIP are unchanged. No new ZIP needed to open mobile files; originals/webm remain available. All media stays OUTSIDE native bundle.
- Operator `marketing/launch45/publish_mobile.py --publish` verifies media and SHA readback, idempotently adds only these two entries; regular publisher preserves them.9 public assets now; no secret/learner media made public. Physical-phone playback remains unverified; baseline encoding is not a universal-compatibility guarantee.
- **P0:** physical Android expiry/background/network restoration, real list/image/solution timings via existing Account→Loading performance, phone MP4 playback. Canonical intermittent503/520 not eliminated by local fixes. **P1:** actual signedAPK<20,000,000bytes remains unverified; direct account deletion still owner-deferred pending matching PIN-backend source (do not re-ask until resumed). **P2:** RF Phase2/3 remain separate, unimplemented future work. Academic source/identity/history remain canonical; Rapid Fire intentionally companion-only.

## Latest iteration54 — “Download nahi ho rha” delivery fallback
- User reported download failure after launch-film links. Freshserverchecks foundvalidassets; user'sactualdevice/browser/errornotprovided. RCAguessedmessagingWebView, but thatisNOTestablished—don'tstateWhatsApp/Telegramorcodecascertaincause.
- Hardened explicitvideo`?download=1` links to **attachment+application/octet-stream+nosniff**, notinlinevideoplayback. DefaultMP4/WebMpreviewMIMEunchanged. Added **`/api/marketing/launch/launch-pack.zip`**:ALWAYSattachmentwithoutquery,application/zip,containsONLYtwooriginalMP4s(noqualitychange/privatefiles/loginrequirement).
- Bundle`JEELIVE-Launch-Videos-45s.zip`:15,097,795bytes,sha256`aceeaa6329a41e32109521acb6f9da1118c81b0816b1c27ab33577dbec339822`. ExactlysafeASCIIvertical/landscapefilenames;ZIP_STORED/deterministicdate/regularfiles,CRCandeachoriginalMP4SHAverified. NewmanagedUUIDobjectuploadedandreadbackverified;7publicassetsnow.
- New`marketing/launch45/download_pack.py`verifiedpack-onlypublisher(noffproberequirement);full`publish.py`alsorebuildspackonfuturemediaupdates. Existingmaster/preview/posterrecordsretained. `backend/marketing_media.py`fixedallowlist+downloadMIMEonly; nofrontendUI/nativepage/dependency/auth/datachanges. QA'stemporarybrowserDOManchorwasNOTaddedtotheapp.
- **58/58scopedregressionsPASS**, plusindependentactualbrowser`click+expect_download` **3/3ZIPandbothMP4s** complete withcorrectfilename/bytes/SHA. MainalsoactuallydownloadedZIPandverticalMP4andopenedarchive/checkedeachmember. Tests:`backend/tests/test_iter54_marketing_download_delivery.py`,report`test_reports/iteration_54.json`;existingiter53allowlisttestupdatedto7. Noauth/RF/PYQ/accountwrites.
- Preferreduserlink:currentEXPO_PUBLIC_BACKEND_URL+`/api/marketing/launch/launch-pack.zip`. UsercanextracttwoMP4sinFiles/Downloads; ifchatbrowserblocksfiledownloads,openlinkinsystembrowser. **Userdeviceconfirmationstillpending;donotclaimuniversalfixorrootcauseproof.** Ifstillfails,askforscreenshot/device/browser—notHARasfirststepfornontechnicalphoneuser. Noappinstall/PINneeded.

## Latest iteration53 — Actual45s launch films, both formats DELIVERED
- User exact: “Launch video banao sabse zyada focus 20 sec no pen challenge rapid fire and all india test series . Beautiful banana naki mechanical”; choices BOTH9:16Reel/ShortsAND16:9YouTube,45scinematic,Music+Hinglish(noVO),researchfirst.
- Research/reference review + artdirection, then ACTUAL rendered films—not justscript/storyboard/appUIrunner. Authoritative fact-checked creative:`marketing/launch45/BRIEF.md`. Generatedrootdesign_guidelines.json is an unapproved draft with unsupportedrank/coin/NTA/fourthexam/UIrunnerideas; those wereREJECTED, notimplemented, andmustNOToverrideappdesign/producttruth.
- Film:“Ab tumhari baari.”27sRapidFire/20secondno-penconcept,12sAllIndia,6soriginalbrandending. Dimensionalteal/rubybackdrops, kineticFigtree type, ring-colour-morphtransition, originalgameavatars/logo, readableHinglish, originalcomposedstereo music/no commercialsongcopied. Quizandduelarefeatureillustrations(notlearnerrecording), quizexplicitCONCEPTPREVIEW,Newtoncorrect, elapsedtimerhonest;nofakecoins/ranks/percentile/guaranteedmarks/newstoreavailabilityclaims.
- OriginalfrontendUI/theme/artwork/nativegradientfix/auth/game/data/dependenciesunchanged. Sources/renderedassetsalloutsidefrontendsoNOAPKbundlebloat. Backendonlynewread-onlymarketingrouterinclude/module+publicmanifest; no learner writes, no publicuploador arbitraryfileproxy.
- REALMP4masters: `vertical.mp4`1080x1920/7,724,316bytes; `landscape.mp4`1920x1080/7,373,179bytes. Both EXACT45.000s,30fps1350frames,H264yuv420p/AACstereo48k,faststart. IdenticalVP9/OpusWebMpreviews4,486,542/4,517,644bytes(~45.008s codec-tolerance),2JPEGposters. All8managedobjects(including2sourcebackdrops)uploadednewUUID+SHAreadbackverified; no secrets inlinks.
- Publicdelivery uses currentfrontend.envEXPO_PUBLIC_BACKEND_URL + `/api/marketing/launch/{vertical.mp4,landscape.mp4,vertical.webm,landscape.webm,poster-vertical.jpg,poster-landscape.jpg}`. `?download=1`forcesattachment;defaultinline. All6fixedallowlistedassetsGET/HEADonly; explicitbyte-rangesbecauseStarlette0.37.2. Lazydiskcache, SHAcheck, sanitized503, noAPIstudentauthneededbecauseONLYpublicowneradvertising.
- Currentworkinglinks base:`https://handoff-zip-hub--8kn8pvyh.preview.emergentagent.com` (useCURRENTpublicenvafterfork, notoldhardcodedhost). MP4downloadsplusWebMpreviewlinks delivered; objectpaths/metadata in`backend/marketing_manifest.json` and`marketing/launch45/published.json`. MP4/previewfiles/sourcecomposer in`marketing/launch45/output`andparentPythonmodules.
- **Verification:**67/67publicdelivery/mediaregressionsPASS(`backend/tests/test_iter53_marketing_media_public.py`,report`test_reports/iteration_53.json`). All6SHA/bytes/MIME/HEAD/GET/download/404allowlist, Rangeclosed/open/suffix/clamp/invalid/reversed/huge/multiple416,IfRange/ETag304/HEADnobody;ALL4videosfullyFFmpegdecodedwithout errors,1350frames/dimensions/codecs/durations/audio/faststart/postersvalid. RealbrowserWebMmobile390+wide playsandseekspass; maincapturedactualdecodedNewton11.9s/AllIndia31.5s frames. Independentvideo/audioqualityreviewpositive;27–29transitionpolished. Pythonlint/compilePASS. NoAPI/game/authwritesbytests.
- **Codecdiagnostic:**testbrowser`canPlayType(H264/AAC)`empty,MP4mediaerror4`DEMUXER_ERROR_NO_SUPPORTED_STREAMS`whileHTTP206/bodySHA/fullFFmpegdecodevalid. This isNOTcorruptMP4/failedAPI. WebMpreviewsplayunderSAMEproxyheaders. FirstRCAclaim“no-storeuniversallypreventsbuffering”wasfalse; NOCDN/env/supervisor/headerworkaroundapplied. UseWebMlinksforbrowserpreview,MP4fornormalplayers/socialuploads;physicalphoneMP4notclaimedtested.
- **P0 for thisrequest:**nonefoundinscope; completedfilmdelivery. OptionalP2:15steasercutandphysical-deviceMP4compatibilitycheck. ExistingAPPsignedAPK<20MB/nativeperformance/canonical503/520/deferredaccountdeletionremainseparateunchangedbacklog—notcertifiedbyfilmdelivery. NoEAS/cloudappbuild/socialpostingperformed.

## Latest iteration52 — All India native gradient colour correction
- User objected to white/black/red washout of AllIndia banner/CTA in screenshot, asking why colours changed. **Do not redesign/recolour it.** Last Home-copy removal did not modify SeriesBanner/theme/gradient (Git comparison confirmed).
- Root cause confirmed in installed react-native-svg native `extractGradient`: embedded stopColor RGBAalpha is discarded and replaced with stopOpacity (default1). Our CSS adapter passed RGBAcolour only, making transparentblack/softwhite opaque on native. Web SVG honoured embeddedalpha, hiding the defect in prior browser-onlychecks.
- Added small `src/gradientStop.ts` using ReactNative `processColor` to separateRGB and unsignedARGBalpha/255; WebsiteGradient memoizesconversion and forwards BOTHstopColor+stopOpacity. No theme/token/layout/shine/CTA/content/API/auth/dependencychanges. Originalpalette/artwork/sourcefiles hash-match7cd149d.
- Final **5/5 regressionsPASS** in `tests/iter52_native_svg_gradient_regression.cjs`: actualinstallednativeSVGextractor reproducesbefore255alpha and verifiesafter0/51/26; alphaformat/boundary/signedinteger/fallback; allownerbanner/shine/CTA/ribbontokens; actualReactcomponent render→nativeextractorpreservesEVERYoriginalARGB/offset/layerangle/order. NativeprocessColorboundary suppliedbyrealRNWebnormalizer; NOThardwareemulation. TSC/ESLintPASS.
- MainrealreadonlyPINPOST200→Home390/320screenshots: readableoriginaldarkruby/onyxbanner, redCTA, explicittransparent/softSVGstops, pause, explaineropen/close, Openhub→/livePASS. Noattempt/PIN/account/RFwrites. Screenshots`jeelive-series-opacity-390.jpeg`,`jeelive-series-opacity-320.jpeg`.
- TesterindependentUIattemptinconclusive: nohome/noentryerrorobserved; timestamp09:59logshaveGETauth/session200butNOcorrespondingPINPOST. Main09:54PINPOSTandseriesGETboth200plusactualauthenticatedflowPASS. Noauthbugestablished, noauthcodeweakened/changed, noadditionalcredentialretries. Originalreport52retainedwiththisfollowup.
- **PhysicalAndroidvisualconfirmationstillpending**; extractor+browserproofnotclaimedashardwaretest. Existingnativeartifact/size/canonicalavailability/deferreddeletionbacklogunchanged. `test_reports/iteration_52_main_followup.json` recordsfinalscope.

## Latest UI correction — remove boxed Home marketing copy
- User's annotated screenshot explicitly crosses out all promotional text below the logo and asks for an icon-led app, not a text-heavy landing page.
- Removed only `100% FREE · BUILT FOR YOUR NEXT STEP`, `Your exam.`, `Your next big step.`, supporting paragraph and `CHOOSE YOUR EXAM` from `frontend/app/(tabs)/index.tsx`; removed unused headline/title styles. No empty replacement spacer.
- Original target/diamond/rocket/crown artwork, four card labels/subtitles/badges/routes, logo/account, conditional continue/session notices, Rapid Fire, series and bottom navigation unchanged. Added `home-header`/`home-exam-grid` testIDs. No API/auth/data/dependency changes.
- Self-verified with approved real PIN sign-in and read-only UI: all five removed elements absent, original four images fully loaded, 390px and320px layout fits, JEE Main card navigation works. No new test accounts, academic attempts, answers or PIN edits. TypeScript and modified-file lint PASS.
- Screenshots `jeelive-home-clean-loaded-390.jpeg` and `jeelive-home-clean-loaded-320.jpeg`. Initial captures were taken during entrance animation; final captures waited for image-loading indicators to disappear and all ancestor opacity to reach1. This is mobile-sized preview evidence, not physical-device testing.

## Latest user-requested fresh deployment health check
- User explicitly requested Deployment Agent and a readiness health check. Agent invoked; no app code, secrets, repository tracking, supervisor command or user data changed. Expo restarted; Expo and backend RUNNING with no new Expo error output.
- Generic scanner again returned **FAIL**, solely demanding `.env` tracking and `--tunnel`. These are the same previously investigated false positives, not a new app defect. Scanner verdict is retained as FAIL; do not claim it returned PASS or commit secrets to appease it.
- Independent fresh read-only troubleshooting verified public Expo native manifest HTTP200, publicHTTPS launch asset, backend health HTTP200/statusok, injected public configuration and untrackedsecret.envfiles. Runtime infrastructure is healthy for these checks. This does NOT establish production capacity, physicalAndroid behavior, signing, cloud native build or all upstream API availability.
- No tunnel/config/secret changes are warranted by those findings. The diagnostic agent's broad “production-ready/fullyfunctional” phrasing is **not adopted**: signedAPK<20MB, physicalspeed, canonical503/520 reliability and explicitly deferred account deletion remain pending release gates. Report:`test_reports/deployment_health_followup.json`.

## Latest iteration51 — EAS filename fix + Android size analysis
- User approved **“Build fix, phir size jaanch”** and reiterated lightning-fast/under20MB target. Hindi/Hinglish communication. No unsupported world's-fastest/sub20MB claim.
- Deleted ONLY confirmed corrupt zero-byte frontend filename (basename hex `01b0d7404030b1444038`) with byte-safe unlink. No Git index/commit/reset command, app runtime/auth/data/native engine/dependency/artwork/env change.
- Added **Git-root `.easignore`** (official EAS docs require root, existing frontend-only rules insufficient). Standalone frontend package/assets/config/preinstall files included; backend/private notes/NEET archives/secret files/tests/dependencies/build outputs excluded. Frontend rules retained. ~69MiB local Metro cache excluded from source upload, NOT a claim of APK savings.
- Default release R8/minification/resource shrink/JScompression verified; AAB full device architectures unchanged. Existing optional ARM64APK profile retains arm64-v8a/legacycompressedlibraries. ExpoDoctor20/20, native introspection for both profiles, TSC/lint,24frontendregression cases and public390pxentry→privacy smoke PASS.
- Raw Android graph export: JS4,321,833 +74assets3,900,067 = **8,221,900bytes (8.222MB/7.841MiB)**. `--no-bytecode` used only for measurement on aarch64 host; production Hermes unchanged. This excludes native libraries/resources/Hermes/signing and is **NOT APK/AAB/install size**. SignedAPK target strictly<20,000,000bytes remains unverified.
- **Test/RCA correction:** initial report51 flagged deleted name in old Gitindex as archive blocker; read-onlyRCA incorrectly said EASalwayschecksoutHEAD. OfficialGitClient uses`--no-checkout`+working-treecopy when`requireCommit`notenabled(as here). Updated test follows actualNode`fs.cp`ignorefilter; FAILSonexistinginvalidnames, warns separatelyonoldindex. `.git`excludedfromstagedarchive. Real copy test caught new whitelist trailing-slash mismatch; fixed`!/frontend/`→`!/frontend`so directory includedbeforetraversal.
- Final localroot+frontendNodecopy/tar/gzip/extract tests PASS(202/201files), noinvalidstagednames, requiredinputsretained, secrets/excludedpathsabsent. **LOCAL simulation only**, notfullEAS execution. Priorindexstillcontainsdeletednameuntilnormalplatformsnapshot; latestdeletion+ignorefilesmustbecapturedbeforebuildingafreshcheckout. DoNOTrunGitwritesasaworkaround.
- References:`reference/ITER51_ANDROID_BUILD_INPUTS.md`, `frontend/tests/iter51_build_archive_regression.cjs`, original`test_reports/iteration_51.json`andcorrective`iteration_51_main_followup.json`. Original report's index-only criticalfailure is superseded by source-backed followup, nothidden.
- FinalgenericreadinessscannerstillreportsFAILonpreviouslyknownincorrect.envtracking/--tunnelrules despitepublicHTTPSmanifest+bundle200/correctsecretinjection. **DoNOTtrack.envsecretsorchangesupervisortomakegenericcheckerpass.** Independenttroubleshooterconfirmedpublicroutingworks; Pythonurllib403vsCurl200isrequest/probe-specific,notproofnativeappfailed. ScannerverdictretainedasFAIL/falsepositive-disputed,NOTrelabeledPASS. Source/archivechecksaboveareindependentverifiedevidence; fullsignedbuildreadinessstillunverified.
- **P0 remaining:** latestsourcefullcloudbuild+signedAPK/AAB+physicalAndroidcold/warmimage/solution/mathmeasurements. EASCLIdisabledhere; noJava/Gradle/AndroidSDK/device. No bypass or paidbuild attempted. UseexistingAccount→Loadingperformancediagnostics; don'tcallbrowsernumbersnativeproof.
- **P1:** canonical503/520stabilityremainsunresolved; PINdirectdeletionexplicitlydeferredbyowner(awaitmatchingPINsourceonlywhenuserresumes). **P2:** RFPhase2/3separatelyapprovedfuturework. NEETarchivedandalllearnerdatauntouched.

## Latest priority — API fetching speed + private Redis (2026-10-27)
User prioritized API speed/Redis before native size work; chose app-private Redis
and asked us to choose the technical setup. Implemented and measured; no
"world fastest" or APK-size guarantee.

- Private supervised UNIX-socket Redis,0700,no TCP/persistence,32MBLRU limit.
  Only public RF catalogue/card-page/selection metadata; NO auth/private academic
  responses/wallets/results. Mongo and canonical remain authoritative.
- Warm30-card selection changed from reading all2383 fullPhysicsdocs to cached
  selectionmetadata + indexed live30-card read, with retired/duplicate safeguards.
- Same benchmark: selection p50 **17.586→1.718ms (~10.2x)**; external publicRF
  catalogue **82.562→68.878ms**, card page **73.652→62.174ms** (~16%median gain).
  Cataloguep95 worsened280.234→324.782ms; internet/cold variability is not hidden.
- Pure ASGI auth guard preserves ownerbinding; HTTP/2 canonical pool/45skeepalive,
  original-image gzip bypass, boundedJSONcompression, timing/cacheheaders,
  explicit configured CORSorigins. No auth/writePOSTauto-retries.
- Shared appin-flight reads, accountreset cancellation, bounded64-entry/2MiB JSON
  accounting, oneprefetchlane, Home5→2speculativecalls. Publiccataloguefocus
  reusesfresh data while wallet/privatequeries revalidate. Nativecanonical
  transport and encryptedquestion-imagecache remain unchanged; no newfrontenddeps.
- Mainphone-sizecheck: onecatalogue+oneprofileGET atinitialRFmount; catalogue
  remainedone acrossshop/historynavigation; livewallet re-fetched. ActualQA
  game250→252Coinreward/result/shopverified. Fixturesremovedafterward.
- Finalbackend25passed/1data-dependentskip; clientcacheunits/TSC/lintpassed;
  trusted/foreignCORSchecks andRedis-outagefail-open passed. Protectedbaseline
  profiles/wallets/awards/NEET unchanged. See `memory/API_SPEED_REDIS.md`,
  `test_reports/api_speed_{before,after}.json`, iterations46/47.
- Architecture additions: `backend/{metadata_cache,redis_runtime,performance,
  cors_config}.py`, `redis_runtime.json`, supervisor template;
  `frontend/src/resourceCache.ts`. Private service must be provisioned again if
  runtime is recreated; backend safely falls back when Redis is unavailable.
- P0 remaining: physicalAndroidAPI/render/cache measurements; canonical502/503/
  first-fetch bottlenecks need upstreamtimings/logs, not stale privatecaching.
- P1: actualAPK/AAB measurement, under20MBtarget remainsunverified. Phase2/3
  game/content expansion remains separately approved future scope, not built now.


## Current release — Rapid Fire portrait refresh (2026-10-27)
This section supersedes historical Rapid Fire/auth descriptions below. Approved
scope is the FULL `/app/plan/plan.md` Phase 1, not a cosmetic-only preview.

### Implemented
- Original teal/royal-blue/purple energy lobby, graphite playing cards, managed
  original art (~31KB total), prominent actual Coins/progression, solo/quick-match/
  practice-rival modes, Challenge Friend + Join code and one-tap private history.
- Matching shop/avatars/leaderboard/reward/history surfaces; purchase confirmation,
  balance refresh and historical earned-reward labels. Same +1 score/2 Coins rules,
  original win/perfect bonuses; 30 cards and 20 seconds retained.
- Full AI-assisted reread of all 7,045 active JEE cards: 6,155 kept, 890 permanently
  rejected. No bulk rewriting. Fourteen scientific vector diagrams added to retained
  concepts. Answer-reference formulae appear only after answering/review.
- Approved RF-only cleanup: 209 solo sessions, 388 duels, 255 learning events and
  old JEE match/leaderboard statistics removed/reset. Also purged 4,041 older retired
  JEE card records. Source seeds cannot resurrect the newly rejected cards.
- Wallet/ownership/award and archived NEET fingerprints unchanged: 344 profiles,
  10,257 total Coins, 399 award records. QA data removed; fresh JEE history empty.
- RF HTTP and WS now use expiring opaque grants derived from VERIFIED canonical
  identity, not X-RF-User assertions. `/api/rf/access` verifies web X-JL-Sid or native
  access cookie against canonical `/auth/me`. Cookie is not persisted in the app;
  grant token stays in RAM, digest/15-minute expiry in Mongo. HTTP guard replaces
  any supplied UID; socket first JSON frame carries grant (not URL query).
- Existing academic/PYQ endpoints and native direct canonical transport remain;
  PIN credentials, original home artwork and charcoal/red theme unchanged.

### Architecture additions
- `frontend/src/rapid/{ui,Art,Lobby,RapidText,ScientificDiagram,Diagram}.tsx`
- `frontend/app/rapid/{history,leaderboard}.tsx` plus rebuilt `(tabs)/rapid.tsx`.
- `backend/rf_access.py`, `rapid_deck.py`; `branding.py` serves managed RF art.
- Offline operator scripts and hash-bound review decisions in `backend/rapidfire/`.
  One-time migration `rapid_portrait_2026_v1` is complete. Do not reset future matches.
- Detailed counts, preservation evidence and limitations: `memory/RAPID_FIRE_REVIEW.md`.

### Verified / backlog
- Verified: TypeScript/lints, canonical positive PIN-to-RF grant, API privacy/WS,
  complete 30-card duel/scoring/rewards, solo partial/idempotent rewards, shop/equip,
  real phone-size UI solo timeout/play-again, friend history, purchase and 360px diagram.
- Reports: iterations 42/43 plus `test_reports/iteration_44_self_verify.json`.
- P0 release validation: physical Android native bridge/typesetting/touch/performance.
  Web/browser evidence is not a native device test. Canonical intermittent 502/503
  availability remains outside this app; safe GET retries/bounded errors only.
- P1: measure actual Android build size (<20MB remains an unverified target), then
  real-device load/cache performance. No new dependencies, video or 3D engine added.
- P2: approved plan Phase 2/3 content/cosmetics/competition expansions await separate approval.


## Original problem
A native Android (Expo React Native) student app for JEELIVE.AI covering JEE Main, BITSAT and COMEDK, for a private pilot. It reuses the existing jeelive.ai backend without changing it and has every student feature from the website: exam hubs, mocks/chapters, a reliable test player, results, focused Solutions, My Tests, the 62-day All India series with streak, reflection and reports. It also adds a new Rapid Fire mode: 20-second formula/concept cards. Phone entry is unverified (no OTP). The Home screen has a 2×2 tile grid (JEE Main, Live JEE Series, BITSAT, COMEDK) in the user's exact supplied card design. The bottom bar has Home, Rapid Fire, a raised diamond LIVE button, My Tests and Mission. Mission explains the AI-made content (80-parameter PYQ analysis), says the app is free and asks students to share it. The user also asked for very fast loading and for 5 lakh concurrent students.

## Architecture
- Frontend: Expo Router, Figtree fonts and Material Design icons.
- Native: talks directly to `https://jeelive.ai/api` using a cookie session (`EXPO_PUBLIC_JEELIVE_API`).
- Web preview: goes through the FastAPI pass-through proxy `/api/jl/*`. Each session has its own cookie jar keyed by `X-JL-Sid`, and the shared client never stores cookies.
- Rapid Fire: our own FastAPI + Mongo (`/api/rf/*`). Cards live in `backend/rapidfire/cards/*.json` and auto-sync every 90 s.
- Fast start: the cached user loads instantly and the server is checked in the background. Screens show cached data first and refresh it (stale-while-revalidate, persisted).
- Study material: `/app/reference` and `/app/memory/STUDY_NOTES.md`.

## Implemented (2026-10-23)
- Entry with private-pilot and unverified-phone notices; signout offers Keep drafts / Discard drafts / Stay signed in.
- Home: 2×2 premium code-built tiles (src/components/ExamTile.tsx: glass 3D SVG icons, orbs/dots/tech-line patterns, HOT / 100% AI pills, 24px radius, shadow, press scale), Continue-attempt card, Rapid Fire entry, compact series banner (true 45° 100% AI ribbon, AI Astra credit, pale Score 200+ block), My Tests summary.
- Exam hub → catalogue: subject chips, search, pagination, Start/Resume/Result actions, honest empty states.
- Set detail: rules, marking, preflight, acknowledgement, idempotent start_key, save/unsave.
- Test player:
  - Saving: acknowledged autosave with per-user drafts, save states (Pending, Saving, Saved, Offline, Conflict) and conflict handling.
  - Timer: monotonic and anchored to server time.
  - Navigation: palette with icon+colour states, mark/clear, optional confidence.
  - Submission: BITSAT bonus lock, guarded exit, submit only after every save is acknowledged.
- Results:
  - States: grading (polling), job retry, embargo.
  - Tabs: Analysis, Progress, Confidence, Rank/BITSAT branches, Solutions.
  - Solutions: subject tabs → horizontal question rail → one question card, with filters, reflection, solution-open tracking and reporting.
- My Tests: In progress / Saved / Completed, status and exam chips, search, compare.
- Live hub: streak and cups, today's slot, 62-day calendar, archive, results.
- Rapid Fire:
  - Content: 4,100 JEE Main cards (50 per chapter, 100 for the 4 inorganic chapters), marked review_status `pilot_review_pending`.
  - Play: 10-card sessions, 20 s ring timer, tap to lock, swipe or buttons, timeout handling, exit sheet.
  - End: summary, missed-card review, repeat-missed, history.
- Mission page with Share.

## Iteration 3 (2026-10-23)
- Home tiles: exact supplied 3D artwork (upscaled crops) + HOT / 100% AI pills top-right, 24px radius, shadow, press scale.
- Rapid Fire: 30-card sessions (default); horizontal chapter chips.
- Rapid Fire Duels (backend/duels.py, app/rapid/duel.tsx): random matchmaking (only recently-active hosts), WhatsApp invite code + join, same 30 cards, answers hidden until finish, server-measured tie-break time, forfeit, invite expiry 30 min, history/record.
- Speed: network fetch starts in parallel with cache read; Home prefetches likely next screens; player prefetches next question image.

## Iteration 4 (2026-10-23)
- Bottom bar: Home · JEE Main · center diamond = RAPID FIRE arena · My Tests · Mission. Live series moved to /live (Home tile + banner).
- Auto-advance on option select (test player: only first answer of a question; Rapid Fire solo & duel); Next/Back kept.
- Rapid Fire game layer (backend/gamify.py): XP/levels, coins, daily IST streak, 9 badges, leaderboard, idempotent atomic rewards; reward panel with one-shot burst; combo counter; dark arena UI.
- Duels: forfeiting player can never win; rewards given to both players at settle; card ids/answers hidden until reveal.
- Public bank API for the website: GET /api/rf/cards?subject&chapter&page&limit (4,100 cards).

## Iteration 5 (2026-10-23)
- AI Rival fallback (POST /api/rf/duels/{id}/bot): 1000 rotating names, avatars and cosmetics; always labelled "AI RIVAL"; paces itself and always stays below the student; small practice reward only (no PvP win, quest or leaderboard credit).
- Duel UX: an on-card RIGHT +1 / WRONG verdict with a coloured border, a live scoreboard with avatars and lead text, an entry-effect intro with both avatars.
- Coin Shop (backend/shop.py, app/rapid/shop.tsx): streak freezes (auto-save one missed day), 4 avatar frames, 4 animated entry effects, 3 arena themes, 12 free avatars; earned coins only, no payments.
- Daily Quests (3/day, claim coins), freezes shown on the streak card, themed arena background.

## Iteration 6 (2026-06)
- Duels on a live WebSocket connection (/api/rf/duels/{id}/ws?u=uid): server pushes state after join/bot/answer/forfeit; one server-side ticker per duel (not per phone); 3 s polling fallback only while the socket is down. Card cache in memory; presence writes throttled to 3 s; GZip on API responses.
- Duel verdict fix (verdict tied to card index; no skip on early push); countdown clamped 5..1; AI Rival duels excluded from duel record.
- Card bank expanded to ~11,500 JEE Main cards (150 per chapter, 100 for the 4 inorganic chapters), still review pending.
- Scale note: multi-server WebSocket fan-out needs Redis pub/sub (not added yet).

## Iteration 7 (2026-06)
- 16 3D game-style hero avatars (Nano Banana, bundled webp in frontend/assets/avatars; generator backend/rapidfire/generate_avatars.py): 4 free, 12 paid by rarity (Rare 300-400, Epic 700-800, Legendary 1500-2000).
- 10 entry effects (added Cyclone, Meteor, Dragon, Phoenix, Galaxy, Black Hole) with particle bursts.
- Full-screen 3 s duel intro (EntryShow): you fly in, rival flies in, VS slam + flash + shake, FIGHT!; duel starts 4 s after match. Shop "Watch full duel intro" preview.
- Sound effects (expo-audio, offline-synthesised WAVs in frontend/assets/sfx; backend/rapidfire/make_sfx.py); respects silent switch, mixes with music.

## Iteration 8-11 deep audit (2026-06)
- Card bank second-pass AI verification (backend/rapidfire/verify_cards.py, idempotent): wrong keys fixed, "Both/All of these" cards rewritten/dropped, ambiguous cards + duplicates removed; sync deletes removed cards.
- All-skip runs earn nothing (no XP/coins/streak/quest/badge/counters). Reward has XP bar, coin balance, quest-ready nudge, full-screen level-up.
- Sounds + distinct haptics: correct, wrong, combo, tick (last 5 s), win, lose, level-up, coin.
- Wrong answers stay 2.4 s with full explanation; test player no auto-advance; confidence saveable after answering; set page start hint; 44 px targets; inline quest-claim errors; public /rf/cards hides answers; leaderboard hides TEST_; 15 s client timeout.
- Known gaps: Redis fan-out for multi-server WS, server-side anti-farm timing, resume label on set page, answer harvesting via many solo sessions.

## Iteration 12-14 (2026-06)
- Result > Solutions now fetches AI step-by-step solutions from the live backend (GET /attempts/{id}/ai-solutions): concept, given, steps, final answer + key check, shortcut, common mistakes, time tip, insight, difficulty. Native renders maths with KaTeX in a WebView (CDN); web preview uses a plain-text maths converter (plainMath). Pending items show "being prepared"; newly generated solutions appear automatically on next open.
- AssetImage clears stale images on question switch.

## Iteration 15 (2026-06)
- Offline maths: KaTeX bundled (katex npm, CSS + woff2 fonts inlined in src/katexCss.ts); AI solutions are typeset in JS (katex.renderToString) and shown in a WebView with no network.
- Multi-server duels: shared live channel = capped MongoDB collection rf_events tailed by every server process (no Redis needed). Any mutation calls notify(did): local push + event; other servers push to their sockets. Verified two uvicorn processes: cross-server update in ~6 ms.
- User declined: AI Doubt, Revision Notebook.

## Iteration 17-18 (2026-06)
- Rapid Fire hub redesigned (elegant): identity bar, streak + quests tiles (quests in a sheet), one hero Play card (subject segmented control, chapter picker sheet, START SOLO SPRINT), Duel tiles + join-code sheet, Leaderboard/Recent/Trophies switcher.
- Duel intro is now 4 s (timing-based, no springs); server start_at = now + 4.6 s; first card waits for the intro; opponent-left banner (view() exposes forfeit).
- Set page: one-tap Start (preflight runs silently; checkbox removed).
- Leaderboard cached 15 s (single-flight). Load: one preview worker ≈ 1.2–1.5k req/s on cached endpoints.

## Iteration 21 (2026-06)
- Rapid Fire hub = game lobby: arena-image stage (you vs bobbing "?" opponent, magenta VS pulse, LIVE 1v1 badge, subject switch, glowing chapter pill on the edge), huge PLAY (random match, rf-duel-random) with light sweep, Challenge friend + Join code outline buttons, then Solo Sprint row, streak/quests, tabs.
- ChapterSheet (full-height Modal): search across all subjects, subject tabs, Mixed hero card, "Jump back in" recent chapters, chapter rows with card counts.
- Quick match auto-seats an arena player after 5-7.5 s if no human joins; all "AI Rival" labels/buttons/copy removed per user ("student should never feel they are playing alone or AI"). API still has bot flag.
- Free "Neon Spark" entry (entry_spark, price 0) owned + auto-equipped for everyone (shop.owned_of/equipped_of). Store shows FREE.

## Iteration 22-25 (2026-06)
- Seated-opponent duels pay/count like normal duels; winner decided by score (forfeit = loss). Win bonus only with >=5 correct; all-skip duels give nothing. Opponent score is monotonic: natural pace when the student isn't really playing; when the student has >=5 correct it holds until overtaken, then ends 1-3 behind (per-match gap).
- Waiting screen reuses the arena stage (BattleHero); "Quick match instead" fixed (cancel + replace).

## Iteration 26-27 (2026-06)
- Whole app = luxury black + blood red (CRED vibe): theme.ts palette swapped (near-black surfaces, ivory text, blood-red brand, champagne-gold accents, graphite cards), new key brandText #FF5266 for red text/icons, always-dark scheme, StatusBar light, app.json userInterfaceStyle dark.
- Font: Plus Jakarta Sans 400-800 (assets/fonts/PlusJakartaSans-*.ttf, names Jakarta-*).
- Question palette: current ivory, answered green, marked red, answered+marked gold, pending amber, visited graphite, fresh dark. Logo on white plate with gold border. Rarity colours silver/ruby/gold.

## Backlog
- P1: Owner review of Rapid Fire cards; verify the user id on Rapid Fire endpoints server-side; native device QA (cookies, images, Expo Go).
- P1: Phase 2 — verified identity/OTP, account deletion, privacy.
- P2: Larger question images, richer confidence/progress charts, reduced-motion trophy animation.
- P2: Phase 3 — controlled public release.

## Iteration 16 (2026-06)
- Contrast polish: outcome badges use on* text colours (SKIPPED readable), trophy icons use neonAmber.
- Rapid Fire pool audit (backend/rapidfire/audit_cards.py, judge-only, no rewriting, cached in audit_cache.json): removed cards needing pen/paper; kept the most important 90 per chapter (120 cap for inorganic). JEE pool 11,086 → 7,045 (Physics 2610, Chemistry 2095, Maths 2340). Rejected cards in rapidfire/rejected/ (server retires them softly).
- NEET UG in Rapid Fire: JEE MAIN / NEET UG toggle on the arena; NEET = Physics + Chemistry (shared pool) + Biology (32 NCERT chapters × 90 = 2,880 new cards, generated → verified → audited). Biology allowed in solo sessions and duels; catalog returns `exams` map.

## Iteration 30 — exam leaderboards, Biology diagrams, weak revision, NEETLIVE handoff

### User requests / decisions
- Separate JEE and NEET leaderboards; grouping follows **the exam selected in the arena**, not a locked profile exam.
- Quick picture-based Biology cards for heart, nephron and flower parts, still 20 seconds and no pen.
- One-tap replay of most-missed chapter cards from the arena.
- Preserve all existing NEET content independently for a future NEETLIVE.AI native app and website; tell the owner the exact transfer location. No separate app/website requested to be built in this iteration.

### Implemented architecture (supersedes shared-pool notes above)
- NEET live source: **`/app/neetlive/content/cards/`** and `content/chapters.json`. Independent Physics/Chemistry copies have `neet-` IDs and provenance; existing Biology IDs stay compatible with saved sessions. The old `backend/rapidfire/cards/biology__*.json` files are legacy copies, no longer synced. JEE still reads non-Biology files in that directory.
- NEET bank: **7,585 active cards** — Physics 2,610; Chemistry 2,095; Biology 2,880. PC copies are from the curated shared bank, not a claim of a new expert-certified NEET syllabus. Future subjects can be added to the independent NEET catalogue; none were invented.
- 18 original, NCERT-concept-aligned vector diagram cards (6 heart, 6 nephron, 6 flower), replacing 6 text cards in each relevant Biology chapter to preserve the 90-card cap. Replaced text and rejected Biology content retained in `neetlive/archive/`. Original schematics, not official NCERT scans; owner/expert review still pending.
- Diagram definitions are self-contained JSON primitives rendered by native `react-native-svg` in `BiologyDiagram.tsx` (no external image dependency). Displayed in solo play, summary review, duels and duel review. NEET arena shortcut starts an 18-card picture sprint; normal Biology play can also sample these cards. Player content scrolls on small devices without hiding options.
- `exam` pinned at session/duel creation. Rewards atomically increment `rf_profiles.exam_stats.JEE` / `.NEET` alongside existing shared wallet/overall XP. Leaderboards are exam-scoped, cached with per-exam single-flight locks, stable UID tie-break, personal rank and top20. Shared coins/streak/overall level are explicitly labelled, not falsely split.
- Exam-specific random matchmaking, invite mismatch rejection, history and rematch/solo fallback. Existing capped `rf_events` WebSocket transport was NOT changed.
- `exam_migration.py`: restart-safe legacy activity classification (Biology→NEET, other old activity→JEE because original PC play did not record exam), legacy ranking rebuilt from saved reward ledger rather than guessing combined profile XP; learning history backfilled once.
- `revision.py`: unique `(uid,ref)` immutable learning events from completed sprints/duels, learner+exam index. Wrong/timeouts count; skips and unseen cards do not. Latest correct answer clears a card; cards retired from the bank are excluded. Chapters ordered by accumulated unresolved misses. One-tap replay loads <=30 hardest missed cards in the selected chapter; counts refresh on arena focus/manual refresh.
- Cache key rendering hardened to prevent briefly showing the previous exam/account on key changes. New UI uses established black/burgundy/gold theme and current Jakarta fonts; no theme migration.
- Card sync only clears catalog cache when data changes, and soft-retires cards from deleted/empty source files while retaining historical review data.

### APIs
- `GET /api/rf/catalog?exam=JEE|NEET`, `/cards?exam=...`, `/leaderboard?exam=...`, `/history?exam=...`, `/duels?exam=...`.
- `POST /api/rf/sessions`: optional `exam`, `diagram_only`, `revision`; subject/exam combinations validated. Completion derives correctness server-side and records learning idempotently.
- `GET /api/rf/revision?exam=...`: unresolved chapter counts and misses, no answer keys.
- Duel create/join carries exam; responses preserve exam. No-exam old clients retain backward-compatible defaults/canonical catalog.

### NEETLIVE handoff location / privacy
- Give future builder **`/app/neetlive/`** or **`/app/neetlive/exports/neetlive-content.zip`** (~1 MB). Includes 7,585 cards with keys/explanations, chapter list, diagrams, archives, SHA-256 manifest, READMEs and integration-reference snapshots.
- Refresh owner bundle: `python neetlive/tools/export_bundle.py`. The frontend/backend reference files are not a standalone runnable app.
- **Private learner progress remains in MongoDB**, scoped by `exam: "NEET"`; profiles expose NEET counters under `exam_stats.NEET`. It is NOT silently included in the content ZIP. Optional explicit owner-only `--private-output /secure/neet-transfer` exports NEET progress to a protected path OUTSIDE the repository. Cookies, phone numbers, auth tokens and shared wallet entitlements are excluded. This optional private migration command has not been exercised on a live transfer.
- No authentication changes. Existing private-pilot unverified phone access remains; verified identity is still a P1 requirement before public use.

### Verification
- Testing report `/app/test_reports/iteration_30.json`: new suite 10/10 plus prior NEET catalogue regression 13/13 passed. One stale DB-count assertion was corrected for intentional independent NEET PC copies.
- Follow-up: new suite rerun + 6 existing WebSocket membership/join/push/forfeit cases **16/16 passed** (`test_reports/pytest/iter30_final.xml`). **29 distinct backend cases verified in total**.
- Mobile preview at 390×844 and narrow320: exam switching without stale board data, all three diagram types, diagram feedback/completion/review, one-tap weak revision, no horizontal overflow. Follow-up UI: NEET invite→quick match→complete→fresh invite rematch→solo→start another, all preserving NEET.
- TypeScript `tsc --noEmit` and modified Python/JS lint pass. Duplicate cookie-policy invocation removed without changing behavior. Pilot-mutating UI seed helper now opt-in, not part of routine regressions.
- Not verified here: physical Android/iOS device QA; 500,000-concurrent-user capacity. No such scale claim is made.

### Current priorities
- P0: no known blocking defects in tested feature scope; user verification pending.
- P1: owner/subject-expert review of diagrams and independently forked NEET PC syllabus; physical-device QA; verified identity/OTP (separate future integration).
- P2: future standalone NEETLIVE app/site using this bundle; expand original Biology diagrams only after owner feedback; additional shop/avatar refinements.

## Iteration31 — owner-requested downloadable NEET ZIP
- User requested a clickable ZIP and asked how to copy the app/backend for a later separate NEET app/website.
- `backend/owner_downloads.py` adds GET `/api/owner-downloads/{token}`; only a256-bit trusted-workspace-generated grant can retrieve the fixed content ZIP. There is NO HTTP mint route and no use of unverified learner IDs for owner access.
- Operator CLI: `python backend/tools/owner_download.py issue` (24h max, configured backend URL), revoke by nonsecret `--grant-id`. Only token SHA256 stored in Mongo, TTL expiry plus explicit access-time expiry, revoked/type/hash checks; returns verified exact ZIP bytes as attachment. Changed ZIP bytes invalidate old grants.
- Application access logs redact bearer paths. No-store/nosniff/no-referrer headers applied. Upstream infrastructure logs cannot be controlled here; link possession grants download, so owner must not share it publicly. Raw bearer URLs must NOT be stored in PRD/source/test reports.
- `test_owner_download_iter31.py`: final10/10 passed; valid byte/hash/headers, denial cases, no public mint, CLI revoke, hash-only storage, TTL, logs, NEETcatalog unchanged. Initial exact header test was corrected because ingress's no-store/no-cache/must-revalidate still prohibits ALL cache storage.
- Download ZIP remains content+integration references, not a complete independent app/backend. Owned backend/frontend source can be copied separately; the external jeelive.ai exam/mock/attempt service source and live DB are not in this repo. Future NEET website and full standalone backend still need implementation.

## Iteration32 — current website theme + minimal-click JEE Main PYQ

### Explicit request / chosen flow
User: match the changed jeelive.ai theme, replace JEE mocks with PYQs and use uploaded solutions. Confirmed **year/shift listing**, specifically **Mains card -> PYQ -> immediate paper list** with Start for new, Continue for unfinished, Result+Re-attempt for completed. No intermediate set-detail or mandatory year/date drilldown.

### Implemented
- Verified public current website CSS and JS rather than guessing branding/contracts. Theme now uses Figtree400–800, surface#08080A, card#14141C, primary#D91222, readable accent#FF6974, brandSoft#280D13, brandLine#67202C, foreground#F8FAFC, muted#B0B0BF. Global semantic foreground selection fixes white-on-bright-subject/amber contrast.
- Native vector brand, matching red/charcoal home exam cards, refreshed exam hub/series and entry decoration; authentication logic unchanged. BITSAT/COMEDK mocks, chapters, existing history, live series, RF/NEET remain available.
- `frontend/app/pyq.tsx` + `src/api/pyq.ts` + `components/PyqPaperCard.tsx`: actual GET `/pyq/jee-main`, validated response, date/year/shift metadata from API, dynamic optional inline filters, no fabricated rows. Live/authenticated cache scoped to UID, focus/pull-to-refresh.
- JEE hub's Mock tests replaced by PYQ. Old `/catalogue?slug=jee-main&kind=mocks|pyq` links redirect to `/pyq`; other exam mock routes and chapter routes unchanged.
- New/re-attempt one-tap pipeline: recheck `/my/sets/{id}` active state, existing preflight, idempotent `/sets/{id}/start`, then player. Per-user/set single-flight and persisted JSON start intent keep the same key for uncertain retries; new acknowledged reattempt gets a new key. No history deletion.
- Continue reads the exact existing attempt and routes active to player, sealed/expired to result; never POSTs a new start. Results use latest_result_id/finished attempt only. Grading shows an explicit waiting hint and no premature new-start action; previous released result may remain available.
- Per-row errors/loading/disabled controls and 320px single-line Re-attempt button. New hub/PYQ Back testIDs unique to avoid hidden-stack selector collisions.
- Existing supplied solution/question image mapping remains keyed by question ID with authenticated asset fetching and zoom. New `MathText.tsx` uses bundled native KaTeX for supplied typed maths; web preview uses readable plain-math fallback. Answer-key-only and missing-worked-solution disclosures remain honest. No AI regeneration/replacement of uploaded solutions introduced.
- **Backend proxy and auth code were not changed**: the existing generic proxy already forwards the new endpoint. No env changes or new credentials.

### Critical external live-data blocker (P0)
As of2026-10-26, authenticated live **`https://jeelive.ai/api/pyq/jee-main` returns HTTP200 `{items:[],years:[],total:0}`**, both direct and through this app's proxy. Existing login and chapter histories work; correct API base confirmed in website JS and app config. Independent troubleshooting confirmed student catalogue emptiness.

This does NOT prove uploads failed or that no draft data exists. Admin/studio/database publication is not visible with the learner session. The jeelive.ai backend owner must check publication/association/student visibility of the intended full-length year/date/shift rows. Do NOT substitute chapter tests from `/sets?kind=pyq`; that undocumented filter may be ignored. No admin/studio data was changed.

**Real new PYQ start -> solve -> submit -> supplied-solution mapping cannot be called verified until live published rows exist.** The app is wired to display them on refresh/focus as soon as the student endpoint returns them.

### Verification
- `/app/test_reports/iteration_32.json`; new `/app/backend/tests/test_iter32_pyq_live.py`:4/4 live auth/proxy-contract/parity/RF-exam sanity checks passed.
- Real preview390/320: current theme, home->Mains->PYQ two taps, honest empty/refresh, BITSAT mocks, legacy redirects, chapters and RF regression passed.
- Isolated **test-only** network fixtures (NOT app/demo data) validated row actions, optional filters, Start request ordering, tap-spam suppression, same-key failed-start retry, Continue withoutPOST, schema errors. Main follow-up verified genuine Re-attempt creates a different key/new attempt, grading waiting hint, and narrow action labels. Fixtures removed; real catalogue returned0 afterward.
- TypeScript and modified JS/Python lint pass. Physical Android/iOS rendering of newly reused native maths wrapper has not been verified on-device.
- Source/contract notes: `/app/reference/PYQ_INTEGRATION.md`. Current website reference supersedes older Jakarta/black-burgundy-only styling notes.

### Current priorities
- P0: upstream student-visible year/shift PYQ publication/visibility, then real-paper end-to-end solution matching test.
- P1: physical-device maths/asset QA; existing verified-identity/OTP backlog remains separate.
- P2: future NEETLIVE independent app/site using `/app/neetlive/`; further changes only after owner feedback.

## Iteration33 — real PYQs found, code bug fixed, source alignment awaits owner
- User supplied freshly pushed publicrepo`abhishekpushp07-debug/Jeemains.ai` and then authorizedGo. Inspectedcommit`2e0c883da0c5c6ddfe7b008bfbfdeb7f5dbbc442`; bundlecontains30published/audienceall papers,2250questions andsource-backedsolutionmapping. Sourcecode/frontendroute matchtheapp'sroute.
- **Real local bug corrected:** `live_enabled:false` is normal for ordinaryPYQ practice; upstream onlyusesthisflag togateimport/chaptereventcontent. Removedbothblanketrejections in`frontend/src/api/pyq.ts`. Availabilitystillenforcedbyactualstudentcatalogue/detail/preflight/start. Empty state nowstates no papersreturnedforthisaccount, notglobalunpublished/dataabsentassumption.
- **Two verified separate identity/data sources:** currentappacademicAPI`https://jeelive.ai/api` returns0 forapprovedpilot; knownpackagepaperIDs404. Officialsourceproject`https://handoff-zip-hub--8kn8pvyh.preview.emergentagent.com/api` returns30/[2026,2025]. SamephonehasdifferentlearnerUIDs (memory/test_credentials.md). No remoteimport/reset, noappbackendbasechange, no duplicated bank inappMongoDB.
- Real API E2E3/3passed:75questions,sourcequestionimage200,solutionslockedbeforefinish,save/resume,submit/results,idempotentsamekey,newreattempt.
- Main REAL frontend E2E passedusingisolatedbrowserHTTP forwarding tosourceproject withdedicatedcookiejar (NO fabricatedpaper/solutionresponses):30paperlist; actualStartwithfalseflag;Save/Continue sameattempt;submit;75questionresult;providedsource-solutionimages200/render/zoom;Result+Re-attempt;newattemptIDandolderresultstillavailable. Screenschecked390and320. Testsignedoutandforwardingremoved; appstillusesoriginalconfiguredsource.
- Real UI resultID`167f8257-971f-41dc-a875-b8e57623188f`, reattempt`2d68b2bb-5ab7-4505-a2d6-6fb6027db43a`. These are approvedsourcepilotrecords, notproductionlearnerrecords.
- Testreport`test_reports/iteration_33.json`. Sourceintegrationpytestis nowexplicitoptin (`PYQ_RUN_SOURCE_INVESTIGATION=1`+`PYQ_SOURCE_API`) toavoidcreatingpilotattempts/routinelyassertingthetemporary0vs30mismatch.
- **P0 owner decision before permanent changes:** preservejeelive.ai'scurrentaccounts/history andsyncmissingpapersintothatsource(usingwebsite-owneraccess), OR explicitlychooseworking30-paperproject assharedacademicbackendacknowledgingdifferentaccounts/history. Do notsilentlyswitchappURLorpretend30papersarealreadyvisibleintheunchangedcurrentapp. No need forpaperre-upload; originaldataandcontractsareverified.

## Canonical-backend decision — owner confirmed
- User chose **“Maujooda jeelive.ai history rakho”** and explicitly requires website/app backend to be 100% shared for content, signup, results and other data.
- **Decision fixed: keep `https://jeelive.ai/api` as the canonical academic/identity source.** Do not switch to the source-project environment, create duplicate learner records, reset data, or mix account IDs. Existing accounts, attempts and results must remain intact.
- Source-specific integration playbook checked the public pinned auth/import implementation before requesting credentials. Existing production staff login: `POST /auth/login` with email/password; owner-only PYQ operations: `GET /studio/pyq-import/status`, `POST /studio/pyq-import/step`. Use only a server/operator cookie session, never add owner credentials or UI to the student app.
- Read-only live probes: owner-import status returns **401 anonymously and 403 for the approved learner**, confirming the protected route exists; learner PYQ catalogue remains0. No import/publish/write was invoked in these probes.
- Approved intended content operation: verify owner role, production host, package SHA/30 papers/2250 questions and import state first; then serial insert-only existing importer steps. Stop on package mismatch, identity conflicts or missing source assets. Never reset, overwrite an existing record, reupload papers, or copy a database. Verify original learner UID/history before and after.
- Secure-secret metadata check found **no saved website-owner credentials**. Request only `JEELIVE_OWNER_EMAIL` and `JEELIVE_OWNER_PASSWORD` into backend secret storage. Do not request MongoDB URI, signing secrets or keys in chat; do not write owner credentials into memory/test reports.
- **Full-sync gap still explicit:** current website `/api/rf/catalog` returns404; current app Rapid Fire data lives in its own companion backend. Owner credentials/PYQ import alone will NOT make Rapid Fire fully shared. Website-side RF code integration, canonical session authorization and a deliberate non-destructive migration of RF records are needed before claiming 100% shared backend. Preserve existing capped-collection/WebSocket internals; do not just repoint clients to missing endpoints.
- Pending: secure owner access for the production read-only status/preflight, then academic PYQ synchronization and cross-client history verification. Website-side RF integration remains a separate required work item, not falsely marked done.

## Owner access skipped — safe continuation
- User skipped the owner credential card. Respect the skip: no repeated secret request, no guessed login, no protected import or remote data change. Canonical source/history remain unchanged.
- Verified a password-sharing-free website-side path: website source exposes `/owner-login` and `/studio`, but there is no PYQ sync button in the inspected `Studio.js`. A real owner-only panel/operator action must be added/run in the existing website project; do not fabricate click instructions.
- Prepared `/app/reference/CANONICAL_BACKEND_HANDOFF.md` with exact canonical-source decision, existing insert-only PYQ API/manifest, protected owner-session approach, RF code/data migration and cross-client acceptance criteria. It contains no passwords, cookie values or learner export.
- Remaining blocks are explicit: canonical PYQ sync needs an owner-authorized action; 100% RF sharing needs website-side integration and a safe migration. Neither was executed by the app project.

## Latest scope clarification — Rapid Fire is explicitly EXCLUDED from shared backend
- User clarified the mission: academic content including solutions must match100%; all card/theme styles must match; website/app fetch the same backend APIs **except Rapid Fire**; signup/login identity and saved attempts/results must share canonical data.
- This overrides earlier full-RF-migration planning. **Do not migrate RF, repoint its endpoints, or count canonical RF404 as a blocker in the current scope.** Preserve the working companion Rapid Fire/NEET features.
- User requested a precise copy-paste task for their existing website-project chat, not further app changes or another credential request.
- `/app/reference/CANONICAL_BACKEND_HANDOFF.md` replaced with the clarified website-side task: canonical insert-only reviewed PYQ sync, identity/attempt/result parity, exact current design-token/asset/card-theme exports, API/session contract and verification evidence. No secrets required in chat.
- Iteration34 read-only cross-client checks passed5/5: canonical learner ID, catalogue parity, completed history and existing result signatures match through website direct API and app proxy. This does not prove new PYQs exist on canonical data (currently0) or automatic shared browser/native cookie state.
- Remaining work: canonical PYQ content visibility/import with owner authorization, then exact design-token/per-card asset parity and final real-paper test against the canonical source. RF is intentionally separate, not unfinished unification work.

## Iteration35 — native academic theme completion (verification in progress)
- User re-confirmed **100% same content except Rapid Fire**; proceed with PYQ availability check and website-style mapping/UI verification. Canonical origin, authentication, existing history and standalone RF remain unchanged.
- **Availability update:** canonical learner endpoint now serves30 genuine PYQ papers (2026/2025). No app-side import, admin action or backend switch performed. Old zero-papers observation is historical, not the current state.
- Finished academic exam palettes (JEE red `#B00000`, BITSAT orange `#FF9933`, COMEDK graphite `#101115`), native glass/sheens and pause/accessibility/reduced-motion support; fixed unfinished TS imports/props. Preserved requested2×2 mobile home grid and existing Live Series theme. Wrapped narrow titles.
- Applied website PYQ mobile20px padding,18px headings and24px CTA spacing; library active/completed/saved top borders and labelled badges, maroon score panel and five learning-colour result tabs. Exact academic tokens are scoped so RF semantic colours/ChapterSheet stay unchanged.
- Reference rationale: `reference/NATIVE_THEME_MAPPING.md`; source CSS not modified. Native layouts adapted to phone navigation, not claimed pixel-identical to desktop.
- Main smoke390/320: real login, exam colours, pause switch, JEE hub→PYQ30 papers and year filter passed. TypeScript and changed-JS lint passed. Full canonical real-paper E2E/parity and extended visual verification pending iteration35 report.
- P0: complete real canonical start/save/resume/submit/results/supplied-solutions/re-attempt and cross-client verification now data is available.
- P1: physical Android/iOS QA; verified identity/OTP remains a separate canonical-backend-coordinated feature. No new auth implemented.
- P2: RF shop/avatar refinements only after requested; independent NEETLIVE remains future work.

### Iteration35 final verification — supersedes pending notes above
- **Complete:** website academic token/style mapping and canonical real-paper E2E verified in390/320 mobile-sized Expo preview. Final report `test_reports/iteration_35.json`, screenshots `test_reports/artifacts_iter35/followup/`.
- **Canonical parity9/9 passed:** same existing learner identity;30 paper metadata; JEE/BITSAT/COMEDK catalogue samples; live series; newly completed result summary/75 question-answer-solution signatures; original question AND supplied solution binary hashes match direct website API and app proxy.
- **Real UI flow passed:** new PYQ Start, original question image, saved answer, leave, Continue exactID, submit, score/result, all5 tabs, supplied solution image+zoom, Re-attempt distinctID, old result preserved, both attempts in My Tests. IDs in `memory/test_credentials.md`. Exactly2 new academic QA attempts; no old attempts changed, no RF sessions/duels/migration.
- Additional fixes verified: shared Press forwards accessible selected/checked state; My Tests main open/compare controls are siblings (no nested button warnings or accidental navigation). Phone throttle was triggered by tester repeated setup logins, resolved via test-only reuse/cooldown; **no app/upstream auth changes**.
- **Old PYQ P0 blocker cleared:** canonical content is now visible. Current COMEDK mocks remain0 on both website/app; this is source catalogue availability, not divergent app content. Do not insert substitute rows.
- P0: no known unresolved defects in this tested iteration; user visual review pending. P1: physical Android/iOS cookies/math/images/safe-area QA; verified identity/OTP coordinated separately with canonical backend. P2 unchanged.
- Scope caveat: same-source architecture retained; does not claim exhaustive verification of every source asset, new-user signup, all website features, desktop/mobile pixel identity or physical devices.

## Iteration36 — new authoritative ZIP (in verification)
- User supplied full integration ZIP and confirmed **existing-record read-only comparison FIRST, then fresh pilot test**. Extracted to `reference/integration-2026-10-26`; original source is canonical `jeelive.ai/api`, download preview never used as API.
- IMPORTANT visual supersession: latest measured home palette is **JEE royal-blue/platinum, BITSAT bright amber, COMEDK teal, All India ruby/onyx**, not older red/orange/graphite handoff. Other pages remain black/crimson. Source JSON copied unchanged and consumed by theme/gradient adapter.
- Added original SVG logo managed-storage route (publicbranding only, no learner assets), original fonts/OFL licences and Lucide paths; native layered SVG gradients/aspect-ratio angle conversion;7s shine,pause/reducedmotion; source academicstatus colors and selectedtabs. Preserved native2×2 grid and RF base tokens/data/auth.
- Canonical contracts already largely match existing client/controller; no login/session/PIN code changed. **PIN client support NOT implemented/activated and no backend cutover**. Rate-hardening/recovery/native-cookie device validation stay rollout gates.
- Main baseline9/9 existing read-only parity passed; main390/320 real login/PYQ30/home/logo/hubs smoke passed; logo hash matches source; code checks pass. Need expanded packaged30IDs/2250 count and authorized fresh pilot E2E report36 before finish.
- Details/limitations: `reference/integration-2026-10-26/NATIVE_ADOPTION.md`. Physical-device/pixel parity not claimed; source solution image pipeline remains canonical/private, never uploaded to public branding storage.

### CRITICAL latest explicit visual preference — never replace original card artwork
- User interrupted iteration36: **"Bhai theme rkhna hai jeelive se lekin card ka icon kyu badal diye ? Screenshot diya hu"**. User screenshot: JEE red target/radar, Live Series blue diamond, BITSAT orange rocket, COMEDK black/gold crown.
- Preserve website/global JEELIVE black/crimson styling, Figtree, official logo etc BUT **the4 Home artwork images must stay original**. This overrides website4-card gradients/Lucide symbol replacement in the prior iteration36 notes. Do not repeat this mistake in future theme work.
- Restored `assets/images/tile-*.jpg` in image-top2×2 cards, sourced from managed storage with identical bundled offline fallback. Hash/byte match verified all4. Removed ExamGlyph. Kept ruby/onyx series banner; moved finish toggle to banner scope only.
- Main390/320 screenshot verification passed; icons visible/clickable, JEE->30PYQs. Final scoped regression and previously approved fresh pilot pending test agent.

### Iteration36 final — complete
- Original4artwork correction independently verified by testing agent: exact assetbytes, logo, all4routes, reducedmotion/banner-only finish,30 canonicalpapers matching owner evidenceIDs and2250question count. Main mobile390/320 and agent375 screenshots pass. Nativephysicaldevices not claimed.
- After read-only historical comparison, main completed **exactlyONE authorized fresh pilot** in real UI: Start→originalquestion→saved answer→independentcanonicalsession confirmation→leave→Continue sameID→submit→result→supplied originalsolution+zoom. Results/75question data and sampled question+solutionbinary hashes match websiteAPI vs appproxy. Old result/active answers+deadline unchanged. Private QA record in memory/test_credentials.md.
- Browserlaunch once crashed before executing app actions; diagnosed transient, recovered; no duplicatepilot created. Official evidence file is `evidence/canonical-pyq.json` (earlier `pyq-live-index.json` reference was our test-context typo).
- New publicbranding hostconfig changed to explicit `BRANDING_STORAGE_URL` env; no hardcoded host fallback, no changes to protectedenvironment/authsource. Final5/5 brandassets checks,TypeScript andPython/JS lints pass.
- Report `test_reports/iteration_36.json`; existing risks CORS/RFheaderidentity remain coordinated authbacklog (unchanged, not part of this visual correction and no RFmigration permitted). PIN support/cutover intentionally not implemented. P0 scope complete, uservisualreview pending; P1 physicaldevice and canonicalPIN coordination; P2 RF refinements only if requested.

## Iteration37 — NEET removed from live Rapid Fire, archive retained (testing)
- New explicit user request: removeNEETUG fromRapid Fire because separateZIP exists. Clarified **"Archive mein safe rakho"**: hide allNEET options/history fromapp; preserve storeddata/ZIP. This now authorizes targetedRF availability changes, superseding earlier blanketRF-untouched constraint ONLY for this removal.
- JEE-only lobby,3subjects; removedNEETtoggle andBiologydiagramshortcut. Histories/revision/leaderboard/APIcards defaultJEE. ExplicitNEET endpoints reject410; oldNEET sessions/duels get/complete/answer/cancel/bot/forfeit/join/WS guarded beforewrites. Cached/deeplinkNEET practice blockedclient-side too.
- Archive is **logical**, not a migration: existingNEET schema/cards/results/awards/learning/XP segment remain inDB unchanged; NEET contentfiles/ZIP untouched, excluded from livecontent sync. Existingsharedwallet/streak/level preserved. Neverdelete records.
- Baseline fingerprints `test_reports/iter37_archive_baseline.json`:8083NEETcards(includingretired),32sessions,11duels,10awards,8learningevents,1NEETprofilestats segment; separateZIP1055634bytes/SHA2569b51ca14f7f8e41fc81e3b56d1dcf4bb1a9d7df0db4438425335e39683143396.
- MainTypeScript/lints/API JEE7045/default3subjects/NEET410 pass; comprehensivepost-changearchive/JEEregression pending.
- **New externalP0 blocker:** canonicalwebsite auth nowrequiresPIN despite packagedguide sayingpreview-only. Phone-onlyapp login422 (18:39UTC; worked18:08). PublicOpenAPI confirmsrequiredphone+pin. No usableapprovedstoredsessions inlatest8checked. NativePINUI NOT implemented and noPIN/identity/sessionreset made here. FreshauthenticatedUI verification blocked. Do notclaimthis isRFbug orsilentlyregister/fallback/guessPIN. CoordinatePINclient/recovery withowner separately.

### Iteration37 final outcome
- **NEET-removal implementation complete; backend17/17PASS.** JEE7045-card catalogue/3subjects, solo30cards/idempotentrewards/history/revision, invitations/JEEanswer/cancel work. AllNEETlookup/create/replay/history/duelactions/websocketdeny beforewrites. DefaultsneverincludeNEET.
- **Archive preservation proven before+after:** fiveNEETcollections,1NEETprofileXPsegment andseparateZIP matchbaseline exactcounts/hashes. No recordsdeleted,moved,reset,retired;sharedwalletnotreset. Separateexport andsourcefilesremain safe.
- Tests `backend/tests/test_iter37_neet_archive_and_jee_regression.py`; report `test_reports/iteration_37.json`; finalXML `test_reports/pytest/iter37_neet_archive_final.xml`. Tests use onlyexactrun-createdTEST37recordsforJEE mutations andcleanthoseonly.
- Appsource/lints/TypeScript pass,NEETUGtoggle/Biologyshortcutremoved; liveauthenticatedUI validation **stillBLOCKED** byexternalPINcutover. P0next: coordinatepropernativePINlogin/enrollment/recovery withoutchangingIDs orassumingPIN. Do notclaim appfreshlogin works. Afterauthfix, recheckRapid UI (NEETabsent,JEE subjects/history,olddeeplinkarchive message). User's original4Home artwork preference unchanged.

## Iteration38 — canonical PIN auth support (implemented; live checks pending)
- Userconfirmedlivepush andrequestedlogin/signupPIN+ConfirmPIN/ChangePIN/ForgotPIN. Securetestphone/PINprovided via secretscard; use backend environmentnames only, neverpublishvalues. LatestPINLIVE ZIP URL was neverprovided; implement against **currentcanonicalOpenAPI + verifiedlivewebsitepolicy + previousdocumentedcontracts**, notinventednewZIPcontents. Saved schema /tmp/jeelive-live-openapi.json.
- Built phone+4digitPINlogin, explicitsignup, confirmation/localvalidation/leadingzeroes, show/hide, visible429cooldown,noautoretry/noPINpersistence. Samewebsiteidentity/API/cookies; nofallbackphoneonly/signup-on-failure.
- Added protectedChangePIN with registeredphone/newPIN/confirmPIN, currentserveridentityverification aftersuccess; Accountentryandclearsuccess/errorstates. Existingresults/drafts preserved; noRF/academicdata writes.
- ForgotPIN **guidance, not a publicreset**: canonicalhasnoreset/OTPendpoint. Usealready-signed-inAccount/ProfileChangePIN,otherwiseexistingofficialadmincontact; nofakeOTP,email,resetlinkorcontact. Officialwebsitebuttonfromconfiguredcanonicalorigin.
- Authbootstrap doesnotrendercachedprivateidentity beforeverification. Singleflightrefresh/oneretry forprotected401 incl/auth/pin/me; failed401 clearsuser/privateimagecache andretainssame-IDdrafts. Signed-outflag guardsagainstnativecookiesreloggingafterofflinelogout. Rootscreenoverlay protectsprivateviews whilevalidation; credentialscreenstack clearedonlogin/logout; accountprivateidentity neverinvented.
- PreservedFigtree/charcoalredthemeandoriginal4Homeartworks. Nativecookie transport unchanged; physicalAndroid/iOS persistence stillneedsdeviceQA. Noauthbackendmigration/DBchanges/RFchanges.
- MainTypeScript/lints pass;390login/signupmismatch/Forgot guidancepreviewpasses; fixedduplicateentryreturn withdismissTo. Needsecureapprovedaccountreadonlyliveflow+sessionrestore/historyandJEE-onlyRFUI regression. Newaccountcreation/PINchangewritesnotauthorizedonexistingtestaccount; testisolatedorreportlimit.

### Iteration38 current verification/blocker
- Tester plusmainpublicUIchecks passed390/320:PINmask/visibility/leadingzero,confirmmismatchbeforePOST,signup/login tabs,Forgotguidance+dismissTonoentryduplication,unauthprivategate. FullprojectESLint overchangedauthfiles andTypeScript PASS (introducedeffect/purity/textlinterrors fixed; unrelatedRF/pre-existinglintdebtuntouched).
- **Positive live login notyetverified:** securepair returns401directcanonical ANDproxy; oneattemptperchannel thenstop.7dependentbackendchecks skipped, notpassed. Checkedruntimeenvagreessavedconfig. Need ownersecurecardcorrectLIVEstudentphone/PIN; norecovery/reset/guess/newaccountmaybypass.
- Existingrecords/RFdata remainuntouched. No newauthprovider/backendAPIchanges. No approvedtestaccountPINchangeornewsignupperformed. LatestPINZIPnotprovided; currentlivecontractverified (only/auth/pin, noforgotreset).
- P0remaining:workingcredentials→authenticatedmobilelogin/sessionrestore/read-onlyidentity/history/PYQ/sourceimageparity→verifyJEE-onlyRapidUI. P1:physicaliOS/AndroidcookieQA; authorizeddisposablePINchange/signupsuccess tests. Currentimplementationreadybut **do not claimfullauthcompletion** untilpositiveverification.

## Iteration39 — smoother questions/solutions + subject navigation (implemented; testing next)
- UserprioritizedloadingbeforegivingworkingPIN. Explicitchoices **subjecttabs+questiongrid**, **readyaschecked/no30seccountdown**. Wantswholepaperbackgrounddownloadandresults/solutionswarmup. NoPINvalueschat;storedtestpairstillunverified401,noadditionalattempts.
- Foundapp-onlybottlenecks: prefetchnextfirstcroponly, noduplicate-requestcoalescing, unboundedbase64cache andsolutionsondemand; mixedsubjectpalette/globalNext. Changedsourcecode notcanonicalcontent.
- Built4slotprioritydedupqueue (reservevisiblequestion slot),48MiBmemorybudget/accountmemory-onlycache/Abort/logoutsafeguard/browserBlobURLs/nativeRAMdataURI, allpermittedcropsorderedbycurrent→subject→rest. Exactsourcebytes/croporder/version retained; 25secondtimeoutincludesbodyread,429manualcooldownrespect, failuresretry, visibleimageanswerblocking. No local/publicfileuploads/privateimagepersist.
- Player actualsubjecttabs rememberlastquestion, selectedsubjectgridresponsive44ptcells, positionlabel, NextwithinSubject+explicitNextsubject. Solutionssamecontrols withrealreleasedmetadata; backgroundpreload startsalreadyonAnalysisafter200release. Sealed202/embargoed/lockedbonusnotfetched;prefetchdoesn'trecordconsults.
- ReadySheet checksstoragewrite/read/delete+canonicalpreflightbeforeStartnow(noartificialwait);genericpapers+PYQnew/retry useit,existingContinueunchangedUUID/deadline. **Importantlimit:** canonicalimagesrequireattemptID,no prepare/activate endpoint. So allimagespreloadAFTER/startreturn+metadata; nofalsebeforeclockguarantee and noexamtimeextension.
- Tinyauthintegration: verifiedsameaccountdoesn'twipeassetcache;logout/switchpausesprivatequeue sohiddenroutecannotrefillit. RestPIN/UI/backend/RF untouched. PublicoriginalHomeartworksunchanged.
- LatestchangedcodeTypeScript/projectESLintPASS. Implementationdetails `reference/PLAYER_LOADING_CONTRACT.md`; testingpending. P0:isolatedqueue/navigationgates,thenworkingPINandowner-authorizedlivepaperflow/networktimings. P1canonicalprepare/activateiftruepreclockdownloadrequired;Android/iOSmemory/zoom/cookiedeviceQA.

### Iteration39 verification checkpoint — awaiting working securePIN
- Final **17/17 isolated tests PASS** in `frontend/tests/iter39_frontend_isolated_tests.cjs`; report `test_reports/iteration_39.json`. Tests use actualqueueclass and actualsubjectnavigationhook with **syntheticloader/statefixtures only**; NOT realnetworktimings or liveUIproof. No simulatedresponses/auth inproductapp.
- Covered75/150normalimages,sourcecroporder, dedup,priority/reservedslot, boundedparallelism/memory/pinnedLRU, clear/abort/lategeneration, pause/groupcancel, failures+429cooldown, immutable5unevensubjects/lastquestionmemory,44ptgridfit320–768,lockedbonus/202embargo/versiongates, storage/preflightreadiness/UUIDstartcontract.
- Hostedentrysmoke390/375PASS. StrictprojectESLintoverallchangedfiles andTypeScriptPASS. OldbadtestcredentialsNOTretried (securekeytimestampunchanged); publicPINloginUIremainsavailable butpositiveauthnotverified.
- **RemainingP0:** ownerupdatesworkingLIVEphone/PIN securely→readonlyaccount/history/sourceimageparity, authorizedpaperUI/actualnetworklatency measurement, solutionsprefetch+subjects+readiness and JEE-onlyRapid regression. Do notclaimbuttersmooth productionperformance withoutthesechecks. No forcedwait; totalpreclockdownloadstillblockedbycanonicalcontract ratherthanfaked.
- User skipped the iteration39 securecredentialupdate. Stop here without further login attempts or resetting/creating accounts. Implementation+17isolatedchecks available for review; **livePINauthentication/realpaperlatency and authenticatedplayer/solutions E2E remain unverified**. Resume liveQA only after user supplies workingcredentials securely; no repeated prompt needed now.

## Iteration40 — user correction: silent caching + direct start + Androidsize (testing)
- Usercomplaint75questionpaper78displaywasimagepieces,NOTextraquestions. Explicitly **remove imagecounts andloadingannouncements**, downloadASAPfromStart/Reattempttap; **Seedhatestkholo**, noReadySheet. SameforreleasedsolutionsafterSubmit. Persistprivateimagesonsamedevice. Also asksAPK<20MB.
- RemovedallAssetProgress/ReadyToStartUI; originalquestioncount/subjectgrid unchanged. PYQdetail+preflightparallel,POSTstart→warmmetadata/allimagesBEFOREcleanup/navigation;Playerconsumessameinflightdata. SubmitACK→warmresult;onlyreleased200solutionsenqueue. Responsemonotonicclockpreservesexactofficialdeadline, noearly/startpermission bypass.
- Newencrypteddevicecache/AAD256bitGCM: NativeExpoFiles+SecureStorekey, webIndexedDBnonextractableCryptoKey;256MiBboundedLRU,16MiBfilecap;48MiBRAM+6slotpriorityqueue scheduleswholepaperdespiteRAMeviction. Sameaccountreopenreuse, renewedmetadata/ETag/Rangefreshness, crossattemptcandidateonlyafternewpathauthcheck,sourcebytes/croporder/versionexact. Explicitlogout/accountswitchpurge;expiredsessiononlyciphertextretainedlocked untilsameaccountreauth. OS/quota/changedcontentmayredownload, neverabsolute“neveragain”.
- Proxyonlyaddedconditional/rangeheaderforwarding;noauthRFDB/canonicalURLchanges. Original4artworks/Figtree/RFassetsretained. Codec/cache failuresfallbackRAM notplaintext.
- AndroidreleaseR8/shrink/bundlecompressconfigured;defaultAAB(fullABI)+optionalARM64APKprofile;unusedRobotoMonoloadingremoved. NoactualAPK/AAB orAndroidtoolchain available. HostARM64cannotexecute x86Hermescompiler; rawAndroidJS/assetgraphexportvalidatedusing--no-bytecode(noenginechange). Registered8,160,615bytes(~7.78MiB) **NOTAPK**;<20MBtargetstillunverified. Web-static2.58MBhandoffZIPnotnativeassetmanifest;excludedfrombuildinputsnotdeleted.
- Details `reference/ITER40_SILENT_CACHE_AND_ANDROID_SIZE.md`. CurrentTS/strictchangedESLint/PythonPASS,cachetests/livepublicsmokepending. OldbadPINnotretried; nativephysicalperformance/encryptedFiles/cookierestart andrealpaperspeedstillpending. Do notclaimguaranteedinstant/zero-network/sub20APK.

## Iterations48–49 — latest authoritative status: deep native loading optimization
### Request and architecture
- User explicitly approved **investigate → fix → test**, emphasizing career importance and physicalAndroid/ExpoGo questions/solutions/cards still feeling slow after Redis. Speak Hindi/Hinglish. Do NOT call it world-best or instant without device measurements.
- Existing architecture remains Expo/ReactNative frontend, canonical JEELIVE academic/PIN/cookie API (native DIRECT configured canonicalURL, web via FastAPI `/api/jl` per-session proxy), MongoDB separate RF data and private Redis RF metadata cache. **Redis does not accelerate native academic image requests**. No website sync/auth-provider/DB migration, new dependency, public private-image upload, canonical write, artwork swap, or build-engine change.
- Approved PIN now works in real web login; prior37–40 badcredential notes are superseded by `/app/memory/test_credentials.md`. Never reset/guess/bypass PIN or create canonical accounts. NEET stays hidden/archived with original wallet/history preserved.

### Implemented local performance fixes
- `PrivateAssetQueue.ts`: per-path subscriptions instead of global image invalidations; `usePaperAssets` no longer subscribes Player/Result to every image completion. Memoized `AssetImage`, queue reprioritization on subject jump, current crops hard-pinned with neighbours soft-preferred; normal LRU eviction still frees space for foreground. Whole-paper preloading,6slots/reservedvisible capacity,48MiBRAM and source/grant/version/abort semantics preserved.
- Device cache uses read-priority serialized work with open/clear lifecycle barriers, so reads overtake queued background AES writes WITHOUT crossing an account boundary. Reused bounded SHA-ID promises; no plaintext persistent image fallback. Existing AES-GCM256MiB quota/16MiB image limit unchanged.
- Native image conversion avoids Blob/FileReader ArrayBuffer bridge roundtrip; exact bytes become base64 in bounded48KiB yielding chunks. PNG/JPEG/GIF/WebP headers supply dimensions before paint. Encoding completes before starting persistence packing. Unique opaque native memory-cache keys, stable image source objects and native-only next2/previous warm surfaces, max6crops/4MiBestimateddecode perwarmimage. Explicit `cachePolicy=memory`; rejected `Image.loadAsync`/`writeToCacheAsync` because loader/file paths lack required plaintext-disk guarantees.
- New stable `OfflineMath` native WebView shell bundles KaTeX CSS/fonts once, then sends revision-checked small RAM DOM updates; ResizeObserver/fonts-ready sizing, stale acknowledgement hiding, offline CSP and navigation allowlist. MathText plain/web path skips typesetting; memo RapidText; removed whole-card key remounts. RF expiry still checks100ms/20seconds but screen updates only each displayed second; ring animation uses native animated SVG. AI solution typesetter reuses the same shell.
- New **Account → Loading performance**: bounded device-session-only p50/p95 stage timings + cache counters; refresh/reset/share aggregate. No userIDs, URLs, questions, PINs, cookies or automatic uploads. Reset clears timings ONLY. It is a diagnostic, not a benchmark score or FPS measurement.
- Discovered JSON timeout ended at headers and was disabled by caller AbortSignal. `requestDeadline.ts` now bounds entire fetch+JSON body at32s including signal-composed cancellation and an explicit race if platform reader ignoresabort. Existing credential/session NO-autoretry,401refresh and cookie/session contracts preserved. ReadonlyGET retry backend policy left unchanged: **GETauth/session can rotate cookies, so is intentionally non-retryable**.
- My Tests no longer shows a false empty-history/start-first-attempt message on serverfailure; it shows saved-work-preserved/retry guidance. Comparison selection resets in tab/exam event rather than cascadingeffect.

### Verification and honest limits
- `frontend/tests/iter40_frontend_isolated_tests.cjs`12/12 +iter48 5/5 +iter49 7/7 PASS (24 frontendlogic cases). Includes real queue/cachegrant helpers, byte-for-byte base64/SHA, format headers, barrier ordering, fullJSONdeadline/callerabort/credentialnoretry. Synthetic75completion comparison recorded16globalnotifications vs2pathnotifications: **mechanical isolated callback count, NOT Android FPS or speedup**.
- Actual offline HTML browser harness verified revision updates, sizing and CSP block; not a nativeWebView device test. StrictTS and changed-fileESLint pass. Entry/home/MyTests/diagnostics screenshots at390/320; forced503bootstrap settles to editablePIN/retry (no infinite spinner reproduced).
- Existing real RF backend regression re-run:9PASS,1SKIP(no sparsechapter present). Isolated localQA UI with realRFAPI:30-card session, answerfeedback→Next, actual untouched-card timeout at20.4s→0 ring→auto-next,320px layout and partial finish summary PASS. Canonical auth ONLY intercepted inside this testbrowser; no production test-response code.
- TemporaryQAprofiles/grants/matches removed with exact-UIDhelper; baseline guard confirms344originalprofiles/coin total10257 and ownership/archive fingerprints unchanged. Temporary grant files deleted. No canonical academic POSTs sent; solution-open was intercepted503 in readonlybrowsercheck.
- Main approved realPINlogin succeeded repeatedly without retrying credentials in each testcontext; ownedcompleted list showed14total/12loaded. Subsequent realcalls produced external Cloudflare520/503; actualreleasedimage/zoom end-to-end and direct-vs-proxySHA parity **NOT completed this iteration**. Python directcanonical auth timedout; all3paritytests explicitlySKIPPED, notpasses. Repaired paritytest to discover currentaccount OWN completed IDs, removing historicalotheraccount IDs.
- No physicalAndroid/iOS device, nativeStore runtime profiling or signedAPK/AAB built here. **Physical speed and <20MB Android artifact target remain unverified**. No claim of totalP0resolution or world-bestperformance. No newpackage overhead.

### Next work / backlog
- **P0:** User device check on same paper:10questions forward/back, subjectjump, supplied/AI solutions; Account→Loadingperformance refresh/share aggregate. Verify cold vs same-session/native-cache repaint, encryptedstoreafterrestart, nativeOfflineMath fonts/updates, memory underlargecrops. Continue profiling with actual p50/p95 notwebnumbers.
- **P1:** canonicalwebsite intermittent503/520 and slowAI/image responses need upstream investigation/owner-side access; do not “fix” by retrying PIN/session or caching private/auth data inRedis. Re-run readonly parity oncehealthy. Then measure a realAndroidrelease artifact and optimize toward<20MB; do not confuse rawJS/assets with APKsize.
- **P2:** RF sparsechapter content/social expansion only afterloading/nativeverification. Preserveoriginal4homeartworks and existingcoins/academic data.
- Details: `reference/ITER49_NATIVE_LOADING.md`, test reports48/49 and mainfollowup in `test_result.md`.

## Latest deployment-readiness health check — PASS (check only)
- User explicitly requested deployment agent + health check. Final deploymentagent verdict **PASS** after investigating two contradictory template flags. No app publish, paidbuild, credentials/env changes, Gitwrites, supervisor command changes or private-record mutations performed.
- `.env`ignore flag was a falsepositive: platformSupport explicitly confirms runtimeSecretsManager injection, secret-bearing.envfiles MUSTremainuntracked/ignored. Never remove.envignores simply to satisfy the generic scanner.
- `--tunnel`flag was also inapplicable to existingmanagedHTTPSingress: current supervisorprovidesEXPO_PACKAGER_PROXY_URL andworkingMetrocommand. MainrealpublicGET with `Accept:application/expo+json` +`expo-platform:android` returned nativeSDK58manifest advertisingpublicHTTPS `/node_modules/expo-router/entry.bundle`, NOTlocalhost. SupervisorExpo/backend/jeelive-redis allRUNNING. Do not addredundantngrokorchangeprotectedframeworkhostconfig without actualroutingfailure.
- Finalagent compilation/envsyntax/CORS/runtimeURLconfig/supervisor/startupMongoDB checksPASS. NativeacademicAPI remains directconfiguredcanonical; webproxyusesconfiguredbackend. ValidRFaccess TTL isephemeral, notdestructiveacademicdata.
- **Readinessscope only:** externalcanonical503/520 risks remain; liveimageparity, physicalAndroidspeed andsigned<20MBartifactunverified. This check doesNOTcertify those or mean appwaspublished. Healthrecord:`test_reports/deployment_readiness.json`.

## Latest Play Store-specific readiness review — NOT READY (read-only)
- User requested `expo-playstore-readiness-review`. Exact namedskill was not callable/located; an equivalent manual source/config + officialpolicy review was performed, NOT a claim of namedskill execution. Support's broaderavailabilityresponse was explicitlyunverified. No appsource/dependencies/env/userdata/signing/build/publishchanges.
- Installed `expo config --type introspect` confirms Androidlabel/name=`frontend`, package`com.emergent.jeelivemobile.kt2g15`, selectedbluebuildericons and “Start building apps on emergent” splash. Correctreleasebranding needed; preserve4originalHomeartworks. Packageformatpresent, ownershipunverified—notautomaticallyinvalid.
- **Expo Doctor17/20PASS;3FAIL**: missingdirectpeer`expo-asset`requiredbyexpo-audio; duplicateexpo-file-systemroot58.0.11/nestedexpo58.0.10; patchalignmentrecommendations expo58.0.17→~58.0.19,font58.0.9→~58.0.10,image58.0.16→~58.0.17,router58.0.25→~58.0.26. Standalonebuildrisk evenifExpoGoworks; NOautomaticupgrade/downgradeperformed.
- **Policy blockers:** signupavailablebutnoin-appaccountdeletioninitiation; public https://jeelive.ai/privacy existsbutin-applinknotfound andpublicpolicy lacksprivacycontact/explicitdeletionrequestmechanism. Needauthorizeddeletionprocesscoveringcanonicalacademicidentity+linkedRFdata,owner-approvedpolicy/contact andfunctionalexternalwebresource. DoNOTdeleteexistingrecordsor inventendpoint/contact whilechecking.
- **Permissionreview:** introspectedcandidate(notbuiltfinal)manifestRECORD_AUDIO+FOREGROUND_SERVICE_MEDIA_PLAYBACK/defaultsfrombareexpo-audio;SYSTEM_ALERT_WINDOW;legacyREAD/WRITE_EXTERNAL_STORAGEmaxSdk32. AppaudioonlyshortbundledSFX,no recordingflowfound. Disableunneededpluginfeatures/reviewfinalmergedmanifestwhenfixauthorized;declaredpermissiondoesNOTproveaudiocollection.
- Custom.easignoreoverrides.gitignore,soarchiveexclusions/releaseenvmustbeverified;noactualsecretleakclaimed and.envmustremainignoredinGit. PriorinfrastructurehealthPASSisnotPlayStoreapproval.
- No signedAPK/AABfound;actualtargetAPI36percurrentofficialphone-submissionpolicy,64bit/16KBalignment/versionCode/signing/size/physicalQA andPlayConsoleforms/access/conditional12testers14days remainunverified.20MBisuserproducttarget,notgeneralPlaylimit. Earlierupstream503/520 remainsoperationalrisk.
- Detailedreport:`test_reports/play_store_readiness_review.md` andJSON. Next: userauthorizationfornativebuild/branding/permissionfixes; coordinateprivacy/deletionwithcanonicalowner; thenactualreleaseartifact/deviceandConsoleverification. No changeswereappliedduringreview.

## Iteration50 — latest implementation: local store blockers fixed, canonical deletion BLOCKED
### Explicit user choices
- User: “Toh kro ready bhai”, selected **PIN confirm karke direct deletion**, contact **Abhishek@billpe.com**, “World best”. No actual real-account deletion authorized; preserve existing learner records/coins/artworks. Communicate Hindi/Hinglish without claiming world-best/storeapproval/size evidence not measured.

### Implemented and verified
- SDK-compatible dependency changes via supported `yarn expo install` (directyarnaddwasblockedbycommandguard): Expo~58.0.19(actual58.0.20),font~58.0.10,image~58.0.17,router~58.0.26(actual.27),addedexpo-asset~58.0.18,alignedfile-system~58.0.12 andweb-browser~58.0.7. Missingpeer/duplicates/SDKpatchissues resolved. Latest **ExpoDoctor20/20PASS**, TypeScript andstrictchanged-fileESLintPASS. Transientexp.hostschema timeoutresolvedwithoutdisablingchecks.
- `app.json`displaynameJEELIVE.AI,newJEELIVEicons/adaptive+monochrome/splash/faviconfromEXACTapprovedoriginalSVG; package/slug/scheme unchanged. Operatorrasterizer `backend/tools/build_native_brand.py` verifiesSVGsourceSHA andpublishesnewUUID PNGstomanagedobjectstoragewithreadbackSHA.5assets196525bytes; nativebundledcopies+`backend/native_brand_manifest.json`; publicallowlisted `/api/brand/launch/{kind}.png`. FouroriginalHomeJPEGs/mainlogoSVG unchanged. PythonCairoSVGinstalledforoperatorrasterization;requirementsfreezeupdated,notanAndroiddependency.
- ExpoAudioexplicitlydisablesmicrophone/backgroundrecording/backgroundplayback; Androidblockedpermissions removeRECORD_AUDIO/overlays/legacyexternalstorage/FGS/media/micFGS. Introspection showsremove nodes/noAudioControlsService. ShortSFXlogicretained; actualrelease-manifest/hardwareproofstillneeded. SharedPress `.set` APIusedforReactcompiler-safeanimation;childlabel/title testIDsadded.
- `.easignore`excludesenv/keys/keystores/credentials/metadata/backendfromnativearchive;secretsremainignoredinGit. `app.config.js`exposesONLYconfiguredpublicbackend/canonicalURLsviaConstants.extra,preservingframeworkenv/main/metro. No secretvalue/endpoint hardcoding changes.
- Newnative `/privacy`, `/delete-account`, Entryfooter andAccountbuttons; contactexactuseremail. Sharedpubliccontent `frontend/src/legal/content.json` also backsGET `/api/legal/privacy`, `/delete-account`, `/information`; samefull-stacksourcefilepresentinbackendruntime. Eightpolicysectionscoverrealprocessing/devicecaches/RF/retention/contact andhonestlyunavailabledeletion. Nativepolicysnapshotreadableoffline; externalpagebuttonsresolveconfiguredHTTPSbackend;mailtoopenscomposeronly,neverautoemailorPINsend.
- Publicroutesentry/forgot-pin/privacy/delete-account remainusablewhilebootstrapPENDING;privateroutesremaincovereduntilready&&user. Entrykeyboardgoalsohas!readyguard. Focus-awareauto-redirect/late-loginhandlingdoesnotstealpolicypage;Privacyclickclearspin+confirm. IntegrationplaybookconsultedbeforeauthUIchanges. No credentialchanges/newcanonicalaccount/deletion.

### Verification / report corrections
- Testreport`iteration_50.json`:public/auth-gateUIpassed,backendlegal/brand15/16pass. MainRFregression9PASS/1SKIP(no sparsechapter) +existingfrontend40/48/49 suites24PASS. MainfreshapprovedPINlogin afterbuttonenabledreturnedHTTP200 andHome→Account→PrivacyPASS. Testingagent's “inconclusivelogin” wasforce-clickwhilebootstrapguardactive+5swait; no PINPOST inbackendlogs, notestablishedappauthbug. No workaround/authweakeningapplied.
- OneassertionSTILLFAILS:platformCloudflareinjectsscriptintoDELIVEREDHTML. OriginpureHTML,CSPdefaultnoneblocksedgeJS,fullpubliccontent200readable. AddedCache-Controlno-store,no-transform;edgeinjectionpersists. Support/troubleshooteranswerscontainedunverified/unsupportedpolicyclaims; **GooglePlaydoesNOTcategoricallyrequirescript-freeHTML** inofficialpolicyconsulted. DoNOTrepeat“anyscript=Playrejection”ordisablebot/CSPglobally. Testnotmarkedpassedorskipped. Platformrouteexclusionnotavailableinappcode;rootwarningdocumented.
- Original344profiles/10257coin sum/walletownership/NEETarchivefingerprintsunchanged bybaselineguard. No canonicalacademicPOSTs,userPINchanges,realaccountdeletionsorpublicuploads ofprivatequestions.

### Critical remaining dependency — ask owner for website backend source
- FreshreadonlyLIVE `JEELIVE_API/openapi.json` returned121paths; onlyDELETEsavedattempts/setstudio,NOaccountdeletion. `/tmp/jeelive_store_live_openapi.json`. No publicwebsitebackendrepoURLfoundinsuppliedhandoff. Do notguess/inventendpoint,useadminreset,orpretendRF-onlydeletioneraseswebsiteaccount.
- UserchoseDIRECTPINdeletion,notemailrequestalternative. Currentnative/publicdeletionpagesintentionallysayUNAVAILABLE,nocollectedPIN/confirmation/Deletebutton/falsesuccess. This isNOTa completeddeletionfeatureandappisNOTfullyPlayStoresubmission-ready.
- Needwebsitebackendproject/repository/sourceURL orverifiednewdeletioncontract. Requirementsin`reference/CANONICAL_ACCOUNT_DELETION_REQUIRED.md`:freshPIN/ownership/throttle/CSRF,idempotentcross-serviceoutcome,associateddatapurge/legitretention,grant/session/devicecleanup,trustedreceipt/coordination,outsideappentry,disposableisolatedtestsONLY.
- SignedAAB/APK,targetAPI/ABI/16KB/versionCode/signing/physicalAndroid/<20MB,PlayConsole declarations/access/testing andexternalcanonical503/520stabilitystillunverified. No paidbuild/actualpublishingdone. Nextmustnotcall“ready”withouttheseevidencegates.
- Latestfollowup:`test_reports/iteration_50_main_followup.json`. Priorread-onlyreviewreportishistorical;native/config/branding/privacyaccessgapsnowfixedbutdeletion/artifact/Consolegatesremain.

## Latest owner repository input — source compatibility BLOCKER, no backend edits
- Owner supplied `https://github.com/abhishekpushp07-debug/Jeemains.ai/settings` and explicitly said **“Safely backend me add krna kuch gadbadaye nahi .”** Repositoryrootpublic;settings404expected. Read-onlyclone `/tmp/jeelive-canonical-source`, maincommit`2e0c883da0c5c6ddfe7b008bfbfdeb7f5dbbc442` dated2026-10-26. NoGitpush/settingschanges/merges/livebackend replacement, no datastore/auth/accountmutations.
- Onlyotherremotehead `App` at`e25ec0fb35092c2e231518b37d73316b9f9feed9` ismobileExpo/proxycode, NOTwebsitePINbackend. Nootherheads/tags/PRheadrefs discovered.
- **Critical mismatch:** main`backend/tejas/phone.py` PhoneInputonlyphone andphone-onlyupsertsession; `request_contracts.py` PhonePayloadonlyphone/extra_forbid. FreshLIVEOpenAPIrequiresphone+PIN andhasphone/signup,pin,owner/student-pin-reset absentfromrepo. Noaccountdeleteendpoint. Do notguesspin_hash/algorithm/sessiongenerationfromOpenAPI.
- Read-onlytroubleshooterconfirmedmatchinglivePINsourceisnotinavailablebranches. WholemainbackendreplacementcouldbreakPINlogin; no destructivecodeaddedagainstoldsource. Neverrunclone startup/seeds/globalreset_student_data.py/credentialtools againstrealDB.
- Needowner'sLATESTwebsitebackendbranch/commit/sourceexport thatcontainsworkingPINimplementation. RepoURLhasbeenprovided; DONOTaskforitgenericallyagain orrequestGitHubtoken(theexistingrepoispublic). AskonlyforMISSINGcurrentPINsource. No assumptionwhichotherprojectholdsit.
- Sourceevidence:`reference/CANONICAL_SOURCE_COMPATIBILITY.md`;freshschema`/tmp/jeelive_latest_live_contract.json`. PreviousmobileDoctor20/20/fixes remain; directdeletionstillgatedoff. Mustpreserveworkingwebsite+mobilewhileobtainingcorrectsource.

## Latest user decision — website deletion work deferred
- When asked for the matching live PIN backend source, user replied **“In future”**, additionalinfo **“No”**. Respect this deferral: do not ask again or attempt destructive/backendauth changes unless user reopens this work and provides the missing source.
- Keep all verified native dependency/branding/permission/privacy/support/publicaccess improvements. No changes were made to the supplied canonical repository, running website accounts/data, login/PINs or repository settings.
- PIN-confirmed direct account deletion remains intentionally unavailable; neither the information page nor an email is a completed deletion flow. Do not label the app fully Play Store submission-ready.
- Future gates: matching website PIN source and verified cross-service deletion; actual signed AAB/APK/version/ABI/16KB/physical-device performance/<20MB evidence; Play Console requirements and canonical API reliability. Existing CDN edge-script assertion is documented with strict CSP and readable public policy; not an automatic Play-policy rejection.

## Phase 4 polish — Iterations 66–67 (2026-06)
- Crown Celebration now plays on EVERY Knockout Cup win (user choice). Backend cup view returns `title_no`, `first_title`, `my_crown`; `finish()` stores `title_no` on the cup. Modal: FIRST CROWN / CROWN #N, "Champion again!", GOLD/SILVER CROWN · N CUPS chip, scrolls on short phones, art colour follows the player's overall crown.
- Bug fixed: celebration only shows while the cup screen is focused and is marked seen only after the player closes it.
- Cup Night: 30 s lead-in before round 1; seated players can't start/join another cup in the last 15 min (409); after the draw `count` = seated, `missed` flag + night-missed panel for busy joiners.
- UI: Cup Night banner short kicker + 2-line countdown on small phones, moved to top of Knockout hub; duel wait shows a ticking countdown; entry-show white flash toned down; big/small button labels shrink below 360 px.
- Session flash on hard reload fixed (rapidAccess ignores empty uid, no shared failure).
- Tests: backend 14/14 (test_rf_phase3/phase4/iter65/iter66); frontend iteration 67 all pass.
- Backlog: cleanup of /app/backend/tools image scripts before build (APK < 20MB); video zip deep-link (deferred by user).

## Iteration 68 (2026-06) — Champions Wall, Cheer Squad, Crown Share, Cup Night reminder, cleanup
- Champions Wall in lobby (GET /api/rf/cups/champions): last/tonight's Cup Night real champions until next doors (7 pm). CHEER → champion profile with Cheer Squad (2 AI-generated cheerleaders dancing, swinging CONGRATULATIONS board, stage lights, confetti). Profile section renamed "Trophy Cabinet" with a "Cheer squad" replay button.
- Crown Share on crown celebration: 4:5 crown card + WhatsApp (native: view-shot + expo-sharing, Android caption copied; web: wa.me text).
- 7:55 pm Cup Night reminder: rf_notices kind cup_night (once per seat holder, expires after start), NightReminder banner; Later/OPEN/Cup Night screen dismiss; excluded from Gang list/badge.
- Cleanup: removed backend/tools image scripts, unused fonts/images. Redis: redis-server missing in pod (installed manually here); metadata cache L1 holds 30 s when Redis is down so speed holds.
- Tests: test_iter67_champions_reminder.py, test_iter68_wall_edges.py pass; frontend iteration 68 pass, follow-up fixes applied (tonight key, label fallback, caption, wa.me on web, solid share backdrop, Cheer fits 375x667, no web vibrate).

## Iteration77 — Deployment health check (Jun 2026)
- Deployment agent: WARN, no blockers. Lint cleaned (unknown eslint rule comments removed, duplicate import merged). Regression smoke passed (iteration_77).
- Open store/security warnings (not fixed, need owner decision): in-app account deletion disabled (Apple 5.1.1(v)); Forgot PIN has no OTP (user's choice) and needs JEELIVE_OWNER_EMAIL / JEELIVE_OWNER_PASSWORD in the deployed backend.

## Iteration78 — WhatsApp match links (Jun 2026)
- Play Friends → SHARE MATCH LINK creates a "Link Match" room (rooms.py `link:true`): anyone with the link takes one of 4 guest seats (host + 4), 3-minute room, starts on START / full / timer.
- Taking a seat from the link makes the guest and host friends at once (social.make_friends, notice `via:"link"`). Blocked players can't see the room; invite-only rooms unchanged.
- Public page /api/rf/c/{cid}: Open in the app, Play in your browser (/api/arena/rapid/room/{cid}), Get the app; WhatsApp preview text (og tags).
- Signed-out link visitors sign in and come straight back to the room (entry `next`). WhatsApp share uses api.whatsapp.com (emoji safe). Browser arena rebuilt.
- Tests: tests/test_iter77_match_link.py, tests/test_iter78_match_link_public.py, test_rf_social.py pass; frontend iteration_78 pass.

## Iterations 79–87 — JEELIVE.AI Rank tab (Jun 2026)
- Dark brushed-metal Rank tab (sparkle silver + light blood red). Tools as Home-style tiles (src/rank/ToolGrid.tsx): Rank predictor (JEE/COMEDK, BITSAT excluded), Percentile se rank (NEW), Target marks (NEW), College predictor (JEE JoSAA/CSAB/JAC, BITSAT, COMEDK GM only), College compare (NEW, full width). Tools stay mounted after first open so results survive switching.
- Percentile se rank: NTA percentile + category + PwD -> CRL range, category/PwD rank, marks for Tough/Normal/Easy; hands over to College predictor.
- Target marks: pick college (search by short/full name/city) -> per branch marks needed for 2026 closing rank (JEE per paper type and per round incl. CSAB/JAC; COMEDK range of 3 analyses + fee + GM seats; BITSAT official cutoffs + safe target).
- College compare: 2–3 saved colleges (any exam) side by side — final + round-wise closing (CSAB CRL marked), last year, seats (JoSAA seat matrix / COMEDK GM), fee (COMEDK; JEE/BITS note), chance tag; all columns fit the phone width.
- Backend: rank_predictor.py, rank_comedk.py, rank_bitsat.py, rank_tools.py (/api/rank/*: meta, predict, college, estimate, bitsat, comedk, comedk/college, percentile, target/jee, target/comedk, target/bitsat, colleges, compare). Data = static JSON in backend/rank_data (no app size increase; text only).
- Tested: iterations 82–87 pass (backend tests test_rank_*.py).
- Iteration 88: College predictor keeps each exam's answer (JEE / BITSAT / COMEDK) when switching. White A4 PDF export (server-made, reportlab; app size unchanged) on JEE/COMEDK/BITSAT lists (Top 50 + near), Target marks college, Compare + saved list, shortlist sheet. Web downloads; phone opens share sheet (WhatsApp / Files / Print). Endpoints POST /api/rank/pdf/{jee,comedk,bitsat,target/jee,target/comedk,target/bitsat,saved}.
- Iteration 89: PDF straight to WhatsApp ("PDF WhatsApp" next to every PDF button; Android build attaches the file in WhatsApp via react-native-share, iPhone/Expo Go use the share sheet, web shares/downloads + opens WhatsApp). All India day count now comes from the website (Series.total = 50, 9 Dec 2026 – 27 Jan 2027) everywhere; no hardcoded 62. Home's last block is a royal-blue share card (src/components/home/ShareCard.tsx, invite text src/shareApp.ts). Website AITS section has 0 published papers yet.
- Play Store readiness review (17 Nov 2026, report only, no code changes): /app/test_reports/play_store_readiness_review_2026-11-17.md — 1 blocker (no real account deletion), warnings: app.config.js drops WhatsApp manifestQueries, two lock files, 23 SDK patch mismatches, no "Report player", strong score claims.

## Iteration 90 — Build cleanup + Rank tab "Elite card" look (DONE)
- Build: only yarn.lock (no package-lock.json), corrupt zero-byte file removed, Expo SDK 58 versions aligned, `expo-doctor` 20/20, tsc clean.
- Rank page background: pure black (`custom_rankBg`).
- Top 5 tool tiles = Elite-style brushed metal cards, each its own colour (Rank predictor maroon, Percentile indigo/purple-blue, Target teal, College pink, Compare champagne gold) with a faceted SVG diamond in the corner (sparkles on the chosen tile). Files: `src/rank/Metal.tsx` (MetalFace), `src/rank/Diamond.tsx` (Diamond, DiamondLine, DiamondMark), `src/rank/ToolGrid.tsx`.
- Everything below the tiles stays simple (user: "niche simple rkho"): original black panels with red hairlines; the Rank Card is a quiet black metal card with a hairline diamond watermark and a small diamond mark by JEELIVE.AI (`src/rank/MetalCard.tsx`).
- List rows: gold/silver/bronze medal coins for 1-3 (`src/rank/Medal.tsx`), type + chance tags under the college name; PDF buttons wrap on phones.
- Rank features unchanged; no testID changed. Tested: iteration_90 (all features pass).

## Iteration 91 — Mission tab: one shareable "Creator's Letter" card (DONE)
- Watch-only Mission tab. User picked design 5 of 5 concepts shown in-app.
- Card (`src/mission/MissionCard.tsx`, 4:5, royal blue + gold, Hinglish): gold corner ribbon "100% MADE BY AI ASTRA", maker's quote, signature "Abhishek Pushp" + gold AP seal, 4 chips (PYQ DNA, Target 200+, Rapid Fire, Rank + College), footer "100% FREE · Please share karo · jeelive.ai".
- Red share buttons above and below the card: WhatsApp icon + "Please share karo" / "aur free education ko support karo". Plus "Doosre app mein share karo".
- Share (`src/mission/share.ts`): card PNG 1080×1350 + caption. Android build: straight into WhatsApp (shared helper `src/whatsappFile.ts`, also used by Rank PDF). iPhone: share sheet. Expo Go: share sheet + caption copied. Web: WhatsApp text with link.
- "Poori baat" list (6 points) + disclaimer (200+ is a target, not a guarantee).
- Tested: iteration_91 (all pass on web).

## Deployment health check (June 2026)
- Status: WARN, no blockers. Warnings: root .gitignore excludes .env files (fine if deploy copies the workspace); no in-app account deletion (App Store 5.1.1(v) risk, deferred by user); cups.py:325/421 load all rows at once; first-boot migration in exam_migration.py runs inside startup. Info: iOS ITSAppUsesNonExemptEncryption not set.
- Audit fixes (AUDIT_2026_06.md) approved and DONE (build minify/shrink off, DB safety, 1 lakh scale, Dream College per account).

## Iteration 100–101 — Dream College account sync hardened (DONE)
- Old phone dreams (dream.v1) now only fill free slots; the account's own dreams are never dropped (bug from iteration_100 fixed, verified in iteration_101).
- 3-way merge: the phone sends {dreams, base}; the server merges atomically (rev field), so a change on one device never wipes another device's dreams. Missing base = add only (older builds).
- Notices in the meter: refused save ("Ye badlav account mein save nahi hua...") and no room ("<college> nahi juda: account mein <exam> ke 5 ... pehle se hain").
- Sign-out sends pending changes first, then removes the phone copy (kept only if changes are still unsent).
- BITSAT 426-mark bonus paper keeps the real score (shown "/ 426"); shorter papers still scale up.
- Paper submit: waits for saves already on the way; auto-submit holds back up to ~40 s for answers unsent because of the network.
- Touch targets 44×44 (dream remove X, card DREAM button). Backend tests: 25 pass.
- Next for user: tap Publish to make a fresh Android build (APK/AAB) — the old build failed because of the minify setting.

## June 2026 — College/Branch Compare + Dream Progress Chart (DONE)
- "+ Add to Compare" button replaces the star on college cards; branch compare from "See branches".
- Dream Progress Chart (SVG line graph of full mocks vs dream targets) on Home Dream card, Rank Dream panel and Mock Result.
- ETA line wording follows the rounded speed shown on screen (fixed "Score ruka hai" at +0.5). Verified on Home with the QA account.
- Target reached: happy message "🎉 Target marks pahunch gaye! Ab har mock mein isse upar raho, seat pakki karo." and "Bilkul target par" when exactly on target.
- Next: user to Publish for a fresh APK.

## June 2026 — Dream Unlocked celebration (DONE)
- First time a full mock crosses a dream college target (once per dream college, on any device): Rapid Fire's Kohinoor Legends (level 4 Cheer Squad) run a 30 s, 64-count routine to their own 128 BPM cheer track, with beat chants, fireworks, stage lights and confetti cannons at the start, the drop and the finale.
- Banner "DREAM UNLOCKED!" + college name; card shows target, score, how far above, and other dreams unlocked by the same mock. Skip is always there while it plays; after 30 s: Continue + Phir se dekho.
- Opens on the Mock Result screen or on Home (only the focused screen; newest mock of the exam, at most 7 days old, dream picked before that mock). Celebrated dreams are saved with the account (`cheered`, POST /api/rf/dream/cheered).
- Track: backend/rf_art/sound/dream_cheer.m4a (made by backend/rapidfire/make_dream_cheer.py), downloaded from /api/rf/art/dream_cheer.m4a, so it adds nothing to the app size. Offline: the bundled Rookie Squad dances instead.
- QA fixture: backend/tests/dream_cheer_fixture.py seed|cleanup.

## June 2026 — Dream Share Card (DONE)
- WhatsApp share of a crossed dream: black-metal card (big serif college, branch, diamond, "TARGET CROSS · +N MARKS UPAR", mock score X/300, target, student name, mock title, estimate note) sent as a photo with caption "🎯 Dream unlocked! … Tum bhi apna dream set karo 👉 <student link>".
- From the end of the Dream Unlocked celebration (SHARE + Continue; replay moved to the top bar) and from every reached row of the Dream College Meter (Home, Rank Dream panel, Result) as "Dost ko dikhao".
- The card is drawn only while sharing (src/dream/DreamShare.tsx, useDreamShare), so nothing hidden keeps animating.
