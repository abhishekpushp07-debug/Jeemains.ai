# JEELIVE.AI — Play Store readiness review

**Verdict: NOT READY for store submission.**

Reviewed on 2026-10-27. Read-only review: no source/config/dependency changes, account operations, signed builds, store uploads or publishing. The requested `expo-playstore-readiness-review` was not exposed as an available callable skill and no matching local skill definition was located; this is an equivalent manual review, NOT a claim that the named skill ran. Platform Support's availability response was explicitly unverified; do not infer platform-wide capability from this report.

The preceding infrastructure/deployment health **PASS** is a different check. It does not certify Google Play policy compliance or standalone Android build readiness.

## Checks actually performed

- Read `app.json`, `app.config.js`, `eas.json`, `.easignore`, `package.json`, account/signup/help screens, audio implementation and solution reporting UI.
- Ran installed `expo config --type introspect --json` without generating an Android project or modifying app configuration. Inspected candidate manifest, resource strings, permissions and release optimization properties.
- Ran installed `expo-doctor`: **17/20 checks passed; 3 failed**.
- Inspected current launcher/adaptive icon and splash artwork. Searched for privacy/deletion UI and local APK/AAB artifacts.
- Read public `https://jeelive.ai/privacy` and current official Google Play/Android/Expo documentation.
- Did NOT access Play Console, inspect a signed release artifact, test a standalone APK on a phone, create/delete an account or submit academic data.

## Confirmed blockers / required remediation

### P0 — Standalone native dependency readiness

`expo-doctor` reported:

1. **Missing required direct peer dependency `expo-asset`**, required by `expo-audio`. Expo Go success does not prove standalone native availability; the doctor explicitly warns of possible crashes outside Expo Go.
2. **Duplicate native module `expo-file-system`**: root `58.0.11`, nested under `expo` `58.0.10`. Resolve the dependency graph using the installed SDK's compatible versions, then repeat native validation.
3. SDK patch alignment failures:

| Package | Installed | Doctor recommendation |
|---|---|---|
| expo | 58.0.17 | ~58.0.19 |
| expo-font | 58.0.9 | ~58.0.10 |
| expo-image | 58.0.16 | ~58.0.17 |
| expo-router | 58.0.25 | ~58.0.26 |

Evidence: `frontend/package.json:14-60` and actual doctor output. These are actionable native-readiness risks, not proof an unbuilt APK has already crashed. Align within SDK58, add its compatible required peer, deduplicate, rerun doctor and build/test the actual release. Do not downgrade the SDK or hide failures through doctor exclusions.

### P0 — Account deletion is not implemented/discoverable in the app

The app permits account creation (`frontend/app/entry.tsx:23-31,45-61`). Account UI offers PIN help/change, diagnostics and sign-out, but no account-deletion initiation (`frontend/app/account.tsx:40-48`). The public privacy page supplies no explicit deletion mechanism or deletion-request URL.

Google Play's user-data policy requires a readily discoverable deletion initiation route **inside the app and outside the app** when account creation is supported. Sign-out, discarding drafts, clearing a cache or deactivating an account is not account deletion.

Required remediation: design an authenticated deletion/request process plus a functional public web resource, covering both canonical JEELIVE account/academic data and linked RF profiles/history/grants/device data. Document legitimate retention exceptions and deletion handling. Canonical deletion support was NOT established by this review; do not invent an API or erase existing learner records to test it. Implement only with explicit authorization and appropriate backend support.

### P0 — In-app privacy access and policy details incomplete

The public page **exists** at `https://jeelive.ai/privacy`; it must not be reported as missing. It identifies JEELIVE and describes normalized phone numbers, hashed PINs, sessions, attempts/results and report records.

However:
- No privacy-policy link/text was found in the inspected app entry/account/navigation source. The diagnostics-only privacy sentence is not an app privacy policy.
- The public policy reviewed did not provide a privacy contact or explicit deletion-request mechanism.
- RF-linked profile/activity data, processors/sharing and retention/deletion handling need an accurate review before completing Data safety. Do not claim that data is sent to an AI provider simply because a key/dependency exists; map actual processing.

Add a working in-app policy link and complete the policy/Play Console declarations consistently with the real website and companion backend. The user's identity/contact details must come from the owner, not invented sample legal information.

## Other release issues

### P1 — Template launcher identity and splash still selected

- Resolved `name`, `slug` and `scheme` are `frontend`; resolved Android `app_name` is also `frontend`.
- `assets/images/icon.png` and `adaptive-icon.png` display the blue builder `e` logo, not JEELIVE branding.
- Selected splash artwork says **“Start building apps on emergent”**.
- Android package `com.emergent.jeelivemobile.kt2g15` is syntactically present. Ownership/availability/existing listing linkage is unverified; it is not automatically invalid because of its namespace.

Evidence: `frontend/app.json:3-19,29-34`, actual config introspection, direct asset inspection.

Before release, replace only launcher/splash presentation with approved JEELIVE assets and app name. Preserve the user's explicitly requested four original Home exam artworks. Confirm package identity before the first store upload; do not arbitrarily rename it or change deep-link schemes.

### P1 — Permission surface exceeds demonstrated features

The introspected candidate manifest contains:
- `RECORD_AUDIO`
- `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_MEDIA_PLAYBACK`
- `SYSTEM_ALERT_WINDOW`
- `READ_EXTERNAL_STORAGE` / `WRITE_EXTERNAL_STORAGE` (both constrained to maxSdkVersion32)
- Internet, vibration and audio settings permissions.

The inspected app audio code (`src/sfx.ts`) only plays bundled short game effects; no microphone recording flow was found. The bare `expo-audio` plugin defaults `recordAudioAndroid=true` and `enableBackgroundPlayback=true` (`node_modules/expo-audio/plugin/src/withAudio.ts:41-47,68-83`), explaining those declarations.

For the current feature set, explicitly disable recording/background playback defaults that are not needed, review overlay/legacy storage permission necessity, and inspect the **final release merged manifest**. Do not remove permissions blindly if another legitimate feature needs them. Permission declaration alone does NOT prove microphone/photos are collected and must not be copied as a false Data safety declaration. Introspection is not the final built-manifest proof.

### P1 — Build archive and release environment need verification

`frontend/.easignore` has exclusions for tests/logs/handoff ZIPs but does not mirror the repository's secret-file ignore rules. Expo documents that `.easignore`, when present, replaces `.gitignore` for EAS uploads.

This review did not generate/inspect an EAS upload archive, so **no secret exposure is claimed**. Check archive scope and exclusions before a build; keep actual secret-bearing `.env` files out of Git and unwanted credentials/test files out of build uploads. Do not repeat the earlier false recommendation to unignore secrets. Verify the release bundle's stable backend URL rather than assuming a preview URL changes inside an already-built binary.

### P1 — External API reliability remains a release risk

Earlier verified work in this session observed intermittent canonical `jeelive.ai` 503/520 responses affecting session/history/images/AI solutions. This review did not re-submit credentials or run new academic writes. Existing error recovery is useful, but store reviewers need reliable access to the primary learning flows. Resolve the upstream instability and run a complete standalone release smoke test. Do not autoretry PIN submissions or cookie-rotating `/auth/session` as a workaround.

## Release evidence still missing / not assessable from this repository

| Check | Status / requirement |
|---|---|
| Signed release AAB and signing identity | No local APK/AAB found; signing may be managed remotely, so absence of a keystore in source is NOT a defect. Need actual release artifact evidence. |
| Target API | Current official phone-app submission requirement consulted is Android16/API36 from31Aug2026, subject to applicable explicitly granted extensions. Introspection has no compiled uses-sdk target; SDK58 alone is not artifact proof. |
| 64-bit and16KB native compatibility | Verify all native libraries/ABI delivery and ELF/ZIP alignment on the actual release artifact and suitable device/emulator. Modern RN alone does not prove every dependency passes. Check current official policy/Console enforcement rather than relying on an old deadline. |
| Version code | `version=1.0.0` and local version source exist; Expo may supply initial defaults. Verify actual versionCode and increase it for updates. Missing explicit autoIncrement is not itself a first-release blocker. |
| User's under20MB target | Unmeasured. AAB size, APK size and device download/install size are different.20MB is this product's target, not a general Google Play submission limit. |
| Native UX | No signed-app physical-device verification of startup, keyboard, PIN/session restore, image/solution loading, zoom, background/foreground transitions, RF/reconnect, offline failure or memory stability. Earlier mobile-web tests are not a substitute. |
| Play Console declarations | Data safety, ads/no-ads, target audience, IARC content rating, privacy/deletion URLs, app access instructions, contact details and store assets not verifiable without Console evidence. |
| Reviewer access | Supply a stable, non-personal reviewer account/instructions through the appropriate Console fields. Do not publish the current learner's phone/PIN in documentation. |
| Closed testing | If this is a personal developer account created after13Nov2023, the official policy consulted requires12 continuously opted-in testers for14 days before applying for production access. Account type/creation date is unknown; this is conditional, not a universal blocker. |
| Target age/content rights | Confirm truthful intended age groups and rights to distribute papers/diagrams/artwork; do not infer a Families declaration or official exam-body affiliation. |

## Positive findings

- `eas.json` includes a store-distribution `app-bundle` profile. The ARM64-only APK profile is internal distribution, not presented as the Play release.
- R8/minification, resource shrinking and bundle compression are enabled in release configuration.
- SDK58 package graph is identifiable and doctor passes17 checks; fix the remaining native checks before treating standalone support as verified.
- App data/API routing uses configured HTTPS endpoints. Earlier public Android manifest advertised a public HTTPS bundle URL, not localhost; infrastructure health is separate from store acceptance.
- AI solutions are disclosed as AI-generated and keep the official key/score distinct. The app already has an in-app question/solution reporting UI (`app/result/[id].tsx:251-275`). Verify AI-reporting policy scope/moderation handling if content generation expands; do not assume a generic chatbot policy failure for displayed pre-generated educational solutions.
- No ad or real-money billing SDK was found in the inspected direct dependencies; RF coins appear to be earned in-app. Final declarations must reflect actual behavior and any backend/SDK changes, not this limited dependency observation.

## Recommended order

1. Resolve SDK-compatible native peer/duplicate/patch issues and rerun doctor.
2. Correct launcher/splash identity and unnecessary native permission defaults; inspect final release manifest.
3. Add in-app privacy access and establish an authorized, real account-deletion/request process covering both backends; complete owner-approved policy/contact details.
4. Validate build archive/release environment and canonical API stability.
5. Produce a signed release AAB, verify API/ABI/16KB/version/signing/size, and test the standalone app on real Android hardware.
6. Complete applicable Play Console forms/reviewer access/testing requirements and then reassess submission readiness.

No fixes were applied during this review. Account deletion, identity/signing choices, legal text and production operations need the appropriate authorization/information rather than silent implementation.

## Official references consulted

- Google Play user data/privacy/deletion: https://support.google.com/googleplay/android-developer/answer/10144311?hl=en
- Account deletion requirements: https://support.google.com/googleplay/android-developer/answer/13327111?hl=en
- Target API requirements: https://support.google.com/googleplay/android-developer/answer/11926878?hl=en
- Android16KB page-size guidance: https://developer.android.com/guide/practices/page-sizes
- Play permissions policy: https://support.google.com/googleplay/android-developer/answer/9888170?hl=en
- Data safety: https://support.google.com/googleplay/android-developer/answer/10787469
- New personal-account testing: https://support.google.com/googleplay/android-developer/answer/14151465
- App/listing setup: https://support.google.com/googleplay/android-developer/answer/9859152?hl=en
- AI-generated content scope: https://support.google.com/googleplay/android-developer/answer/13985936?hl=en
- Expo EAS ignore rules: https://docs.expo.dev/build-reference/easignore/
- Current public JEELIVE policy: https://jeelive.ai/privacy