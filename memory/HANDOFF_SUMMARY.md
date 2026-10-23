# JEELIVE.AI — Handoff Summary (for next agent)

**Language:** User Hindi/Hinglish mein baat karta hai — reply bhi friendly Hinglish mein do.
**User ka goal:** "World best" premium app (Unacademy/PhysicsWallah level), fast, 5 lakh concurrent users tak scale ho sake.

## Product
Native Android app (Expo React Native + FastAPI + MongoDB) for JEE Main, BITSAT, COMEDK students.
- Exam Hubs (premium glassmorphism 3D tiles, har exam ka apna colour theme) — `frontend/src/components/ExamTile.tsx`. **In tiles ko mat badlo** (user ne "cartoon" version reject kiya tha).
- Test Player, Results/Solutions, My Tests, All India Series.
- Tabs: Home, Live JEE, Rapid Fire (center diamond button), Tests, Mission — `frontend/app/(tabs)/_layout.tsx`.
- **Rapid Fire arena** (gamified):
  - 30-card sessions, auto-advance (no Next button) — `frontend/app/rapid/session.tsx`
  - Multiplayer duels with matchmaking; agar human na mile to AI bot (ladki ke naam, user se thoda kam score) — `backend/duels.py`, `frontend/app/rapid/duel.tsx`
  - Live real-time scores dono players ke duel screen pe
  - XP, coins, streaks, badges — `backend/gamify.py`
  - Coin Shop: streak freeze, animated avatars, items — `backend/shop.py`, `frontend/app/rapid/shop.tsx`, `frontend/src/components/Entry.tsx`

## Key APIs
- `POST /api/rf/duels/queue`, `POST /api/rf/duels/{did}/answer`, `GET /api/rf/duels/{did}` (polling)
- `GET /api/rf/shop/profile`, `POST /api/rf/shop/buy`

## DB collections
- `rf_cards` {id, subject, chapter, prompt, options, answer, explanation}
- `rf_sessions` {id, type, status, players, card_ids, current_index, start_at}
- `rf_profiles` {uid, xp, coins, streak, badges, inventory, equipped}

## Auth
Abhi unverified phone entry (pilot). Phase 2 = OTP verified login (integration_expert se karna).

## Testing
4 testing iterations done (`test_reports/iteration_1..4.json`). Backend pytest: `backend/tests/test_rf_duels.py`, `test_rf_shop_bot.py`. Iteration 4 ke duel UI bugs (live score readability, avatar overlap) fix kiye gaye, **visual verify pending**.

## User ka confirmed NEXT PLAN (latest ask_human answers)
1. 🔴 Duel screen verify (live score + avatars) + poori app ki speed improve (frontend rendering + backend API response times).
2. 🔴 Duels ko polling (1s setInterval) se hata ke **real-time live connection (WebSocket)** pe shift karo — 5 lakh users scale ke liye.
3. 🟡 Rapid Fire question bank bharo — har chapter ke 120-180 concept questions (inorganic ~100), strictly JEE Mains syllabus (`backend/rapidfire/generate_cards.py`).
4. 🟢 Baad mein: OTP verified login.

## Rules
- metro.config.js aur .env URLs mat chhedo.
- Colors `frontend/src/theme.ts` se.
- Detailed PRD: `memory/PRD.md`, notes: `memory/STUDY_NOTES.md`, creds: `memory/test_credentials.md`.
