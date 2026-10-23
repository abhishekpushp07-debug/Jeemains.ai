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

## Backlog
- P1: Owner review of Rapid Fire cards; verify the user id on Rapid Fire endpoints server-side; native device QA (cookies, images, Expo Go).
- P1: Phase 2 — verified identity/OTP, account deletion, privacy.
- P2: Larger question images, richer confidence/progress charts, reduced-motion trophy animation.
- P2: Phase 3 — controlled public release.
