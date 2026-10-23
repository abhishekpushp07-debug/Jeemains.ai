# JEELIVE.AI — Native Android Agent Handoff

Prepared: 2026-10-23. Revision: **1.1 — completeness cross-check update**. Type: **implementation handoff, not an APK or a finished Android project**.

## Android agent ko kya dena hai
Poora ZIP upload karo, phir `AGENT_PROMPT.md` ka text paste karo. Agent ko existing backend reuse karna hai; naya database, copied question bank ya website WebView wrapper nahi banana.

- Live API root: `https://jeelive.ai/api`
- Web reference: `https://jeelive.ai`
- Architecture: native Android client → HTTPS JSON/binary APIs → existing FastAPI backend → existing private MongoDB/storage. Android must never connect directly to MongoDB or object storage.
- Suggested native stack: Kotlin + Jetpack Compose, lifecycle-aware ViewModels, a single HTTP client/cookie jar, local per-account draft storage. Android agent stable supported versions choose kare; this kit does not claim an Android build has passed.
- API snapshot is fetched from the current **preview** schema. A deployment was already running during handoff; live/preview parity must be checked before release, without changing customer data.

## Pehle ye padho
1. `01_BACKEND_AND_AUTH.md`: cookie sessions, envelopes, Android compatibility, current login limitation.
2. `02_NATIVE_APP_BRIEF.md`: screens and feature parity.
3. `03_TEST_ENGINE_AND_SYNC.md`: hard parts—acknowledged autosave, retries, timer, submission, protected assets.
4. `04_DESIGN_AND_ASSETS.md`: supplied logo, compact diagonal ribbon, subject tabs, native accessibility.
5. `05_BUILD_PLAN_AND_ACCEPTANCE.md`: small independently testable implementation stages.
6. `06_KNOWN_GAPS_AND_RELEASE.md`: honest release blockers and work not done.
7. `api/ENDPOINTS.md`, `api/student-openapi.json`, `api/postman_collection.json`, `api/command-examples.json`.
8. `07_COVERAGE_CHECK.md`: feature-to-endpoint reconciliation, added guest/job routes and paused-route warning.
9. `reference/`: selected current web files for behavior/design reference, not a complete runnable web project.

## Important boundaries
- Current learner phone access is **unverified phone-only convenience access**, not OTP. Do not describe it as secure ownership verification. Resolve verified identity before a high-trust public launch.
- Cookie handling works for native HTTP clients; current server does **not** accept an Authorization Bearer token as a replacement for its cookies.
- This package contains no API secrets, passwords, login sessions, database dump, private PDFs, or student records. Example IDs are placeholders, not real records.
- Existing source questions/solutions must come through authorized APIs. Do not regenerate supplied solutions using AI.
- This is a student-first Android app. Existing owner/reviewer operations remain protected in web Content Studio; do not expose them to students or embed operator credentials in an APK. A native staff tool needs separate explicit scope.
- No live write, test signup, test attempt, production migration or deployment is authorized merely by receiving this kit.

## Replaceable release inputs
`[ANDROID_APPLICATION_ID]`, signing configuration, developer/publisher identity and any approved privacy/store-listing URLs must be supplied through the Android build/release workflow. No guessed package ID, signing key, legal claim or verified-identity promise is provided here.
