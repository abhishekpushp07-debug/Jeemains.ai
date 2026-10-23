# Small, independently testable Android build plan

Use dedicated isolated fixtures first. Do not run test writes against jeelive.ai. Each step ends with demonstrated checks; do not claim completed based only on generated code.

1. **Transport + session foundation.** Implement environment-configured HTTPS root, envelope/error decoder, protected cookie jar shared with images, single-flight refresh and cancellation. Test with a local fake HTTP server: Set-Cookie rotation, cold-start restore, concurrent401s, failed refresh, binary PNG vs JSON503, untrusted redirect and safe logs.
2. **Persistent answer command queue.** Implement per-user/attempt/question drafts, immutable request IDs, ACK correlation, revision conflict state. Test offline edit/process kill/relaunch, lost ACK then identical retry, rapid consecutive edits, old ACK arriving late, another-device conflict and account switch. Verify no local “saved” badge without server ACK.
3. **Authoritative timer + sealing state machine.** Implement server/elapsedRealtime anchor and lifecycle reload. Test wall-clock tampering, rotation/background/time passing offline, deadline0, deadline expiry, lost submit response,202 grading and embargo. No late drafts become scored answers.
4. **Catalogue + preflight + start.** Build exam destinations, subject/search/pagination and set instructions. With isolated API fixtures, test missing/published/restricted papers, failed preflight, repeated start_key, resume existing attempt and stale availability. Include chapter rules from API rather than constants.
5. **Native test player.** Compose MCQ/integer controls, source-image zoom, palette/subjects, mark/clear/confidence, save status and exit/submit dialogs. Test75-question JEE,130-question BITSAT plus gated bonus,50-question Mathematics chapter, long formulas/images, all navigation states and a long interruption. Correct visited endpoint response is a list, not just ok:true.
6. **Results and study review.** Build analysis/progress/confidence/rank/solutions. Verify grading/embargo placeholders, subjecttabs→horizontalrail→onecard, last question reachable, empty outcome filter, deep-link/back restoration, score-version switch retains selection, original supplied source image, consultation failure/retry, report receipt and reflection revision conflict. Never expose solutions early.
7. **My Tests + series.** Saved/in-progress/completed, compare, return-state restoration; server-driven All India schedule/streak. Test prelaunch/live/start-closed/ended, missing-paper slots, midnight/server refresh, trophy/reduced motion and no client-only completion streak increments.
8. **Visual/device qualification.** Check smallest supported phone, current phones, tablet/landscape, font scale, TalkBack, dark/light, process death, airplane mode and slow/flapping network. Verify diagonal ribbon never collides; no cluttered duplicate hero text; image reading remains crisp. Include native accessibility tests, not just web screenshots.
9. **Explicitly authorized integration + release.** Obtain dedicated QA identity/environment securely. Integrate and verify real cookie refresh, saves, binary assets, regrades/version selection, deadlines and private-data isolation there. Resolve phone verification/release gaps. Only then produce source project, reproducible debug APK and build instructions. Signing and Play Store publication require separate release inputs/approval.

## Required delivery from Android agent
- Native Android source project and versioned build instructions.
- Debug APK only if actually compiled and installed/tested.
- Environment setup with API origin but no embedded secrets.
- Automated tests for queue/session/timer/release semantics and screen regression evidence.
- Honest list of remaining backend/device/release gaps; no invented OTP, notifications, payments, proctoring or AI generation integrations.
- No production data migration. No replacing or resetting the current backend.
