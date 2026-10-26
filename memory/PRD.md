# JEELIVE.AI Native App — PRD

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
- **Two verified separate identity/data sources:** currentappacademicAPI`https://jeelive.ai/api` returns0 forapprovedpilot; knownpackagepaperIDs404. Officialsourceproject`https://campus-search-debug.preview.emergentagent.com/api` returns30/[2026,2025]. SamephonehasdifferentlearnerUIDs (memory/test_credentials.md). No remoteimport/reset, noappbackendbasechange, no duplicated bank inappMongoDB.
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
