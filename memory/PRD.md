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

## Backlog
- P1: Owner review of Rapid Fire cards; verify the user id on Rapid Fire endpoints server-side; native device QA (cookies, images, Expo Go).
- P1: Phase 2 — verified identity/OTP, account deletion, privacy.
- P2: Larger question images, richer confidence/progress charts, reduced-motion trophy animation.
- P2: Phase 3 — controlled public release.
