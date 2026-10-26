# JEELIVE website ↔ native app: current integration handoff

## Latest owner requirements — supersede earlier RF migration plans
1. Website/app academic content must match100%, including supplied solutions.
2. Use the same design system: fonts, colours, card treatments, gradients, borders, shadows and original assets, adapted to native mobile layout.
3. Use the same canonical academic API/backend **EXCEPT Rapid Fire**, which is explicitly allowed to remain separate. Do not migrate RF or treat canonical `/api/rf/catalog`404 as a blocker for this scope.
4. Signup/login identity, saved attempts and results must be shared in the website backend. Independent device/browser session tokens are normal; they must resolve to the same learner/account and saved records.

## Canonical decision
Keep `https://jeelive.ai/api` and its existing accounts, learner IDs, attempts and result history. Do not redirect the app to a different source-project database, reset the database, or duplicate students/questions in the companion database.

## Verified facts
- App native academics use `EXPO_PUBLIC_JEELIVE_API`; browser preview uses per-user `/api/jl` proxy to `JEELIVE_API`. Both currently target the canonical site.
- Iteration34 read-only tests passed5/5: direct website API and app proxy return the same approved learner ID, PYQ/chapter catalogue data, completed history and one completed result's score/question/solution reference signatures.
- Canonical learner PYQ catalogue currently returns0; separate source-project API returns30 real papers/2250 questions. Same test phone has different UIDs on these sources. GitHub content/package existence alone does not synchronize their live databases.
- Repository inspected: `abhishekpushp07-debug/Jeemains.ai`, commit `2e0c883da0c5c6ddfe7b008bfbfdeb7f5dbbc442`. Reviewed PYQ package SHA256 `7ecfd145c0a8b2d8203c57778e8f8d41198b525174c8c2335a88b035b1803493`.
- The native app's wrong `live_enabled:false` rejection for ordinary PYQs was fixed. Actual30-paper UI, start/save/resume/submit,75-question results, original source-solution images and re-attempt preserving earlier results passed using isolated forwarding to the real source-project API. This was testing, not a permanent source switch.

## Required work in the existing website project

### A. Make reviewed content available in the canonical running backend
- Diagnose and align the canonical data/visibility using the actual student route `GET /api/pyq/jee-main`, not only an owner view or code/package count.
- Reuse existing owner-only `GET /api/studio/pyq-import/status` and `POST /api/studio/pyq-import/step`; do not build a duplicate importer or relabel chapter tests as full-paper PYQs.
- Before writes, authenticate through the existing owner flow, verify the intended host/package/count/hash, source availability and current import state. Stop for package mismatch, missing files or conflicts.
- Use serial, bounded, insert-only steps with existing locks/idempotency. No reset, delete, overwrite, reupload or new database. Preserve source review exclusions and existing learner/attempt/result identifiers.
- Owner credentials were not shared with the app project. Use the website project's normal protected owner session/secure workflow; never request credentials in chat or add them to the student app.
- Website `/owner-login` and `/studio` exist. The inspected `Studio.js` has no PYQ sync button, so do not give nonexistent-button instructions. If necessary, add a genuine owner-only panel using the existing API/session and protected importer; reviewers/students must remain forbidden server-side.

### B. Confirm cross-client identity and academic progress
- Same approved account must resolve to the same canonical learner ID through website and app.
- Website/app catalogues must return identical paper IDs and metadata.
- Save an answer on one client, continue the exact same attempt on the other, and verify it persists. Continue must not create a new attempt.
- After submission, both clients must return the same result ID, score, answers and supplied solution references. Source solutions remain unavailable before submission.
- Re-attempt creates a new attempt without replacing old results; uncertain retries reuse their start key.
- Describe cookie/token/session expiry and refresh behavior for web and native. Do not promise automatic browser-to-phone cookie sharing; use the same authenticated account with device-appropriate sessions.

### C. Export the actual current design system
Commit a usable `design-tokens.json` plus original logo/icon/card assets and a per-card theme mapping. Include exact colours, font files/families/weights, backgrounds/gradients, borders, radii, shadows, selected/pressed/disabled states and answer-status colours. Include mobile-width reference screenshots. Use the final running website styles, not stale token drafts or guessed colours.

## Deliverables to return to the app project
- Confirmed canonical API base and a sanitized integration contract (`APP_INTEGRATION.md`): catalogue/start/autosave/resume/submit/result/source-solution routes, auth/session rules, idempotency and safe response samples.
- Verified canonical student PYQ count and a few paper IDs, plus evidence of a completed paper's matching supplied solution assets (no full student-data dump).
- Design tokens, per-card theme/asset mapping, original assets and current mobile reference screenshots, committed to the provided repo.
- No owner password, cookie, API secret, signing key or private student export in chat/GitHub.

## Current status
Existing academic identity/history/results parity is verified. Canonical PYQ data alignment and exact latest per-card design parity still require website-project work/exports. Owner-protected sync was not executed from the app project. **Rapid Fire remains intentionally separate by the latest explicit user decision.**