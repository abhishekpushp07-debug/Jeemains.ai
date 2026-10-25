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
