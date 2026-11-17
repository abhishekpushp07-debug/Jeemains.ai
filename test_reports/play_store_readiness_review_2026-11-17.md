# Play Store Readiness Report (17 Nov 2026)

Verdict: 1 blocker, 5 warnings, 7 manual checks — account deletion is the only hard stop found; the rest are config hygiene and Play Console steps.

## Risk register

| Severity | Finding | Policy | Evidence | Fix |
| -------- | ------- | ------ | -------- | --- |
| Blocker | Account: users can sign up but cannot delete their account in the app or on the web | Play account deletion (User Data) | `app/entry.tsx` signup mode; `app/delete-account.tsx` + `src/legal/content.json` deletion.enabled=false, "Direct deletion is not available yet"; live `/api/legal/delete-account` shows the same | Add a real deletion flow (in-app + web URL) that removes the website account, results and Rapid Fire data |
| Warning | Build: `app.config.js` replaces the whole `expo-build-properties` config, so app.json's WhatsApp `manifestQueries` are dropped | Broken Functionality | `expo config --type introspect`: queries only has https VIEW; resolved plugin has no manifestQueries | Merge config in `app.config.js` instead of replacing it (otherwise "PDF WhatsApp" always falls back to the share sheet on Android 11+) |
| Warning | Build: two lock files (yarn.lock + package-lock.json); packageManager is yarn | Build stability | `npx expo-doctor`: "Multiple lock files detected" | Delete `frontend/package-lock.json` |
| Warning | Build: 23 packages behind SDK 58 patch versions | Build stability | `npx expo-doctor`: "packages match versions required by installed Expo SDK" failed | Run `npx expo install --check` and rebuild |
| Warning | UGC: player profiles can be blocked but not reported | Play User-Generated Content | `app/rapid/player/[pid].tsx` has Block only; gangs have Report (`gang-report`) + name blocklist (`backend/gangs.py`) | Add "Report player" next to Block, with a stated review commitment |
| Warning | Content: strong claims ("score 200+ with AI", "200+ marks of questions should feel familiar", "world best") | Deceptive Behavior / misleading claims | Home promo, `src/components/home/ShareCard.tsx`, `src/shareApp.ts` | Keep the "practice target, not a guarantee" lines visible; avoid any wording that sounds like a promised score |
| Manual | Data safety form | Play Data safety | Collected: phone number, hashed PIN, name, test attempts/results, Rapid Fire profile/games/friends, session IDs. Rank inputs sent to server for PDFs, not stored. No ads, analytics or crash SDKs found | Fill Data safety to match; confirm with the website team whether any user data goes to an AI provider |
| Manual | Privacy policy URL in Console | Play User Data | In-app links on Entry, Account and `/privacy`; public `https://jeelive-mobile.emergent.host/api/legal/privacy` = 200 | Enter this URL in Play Console; check the text matches real data use |
| Manual | Target API 36 on the built .aab | Play target API | RN 0.88 defaults: targetSdk 36, compileSdk 37 | Confirm in the built .aab |
| Manual | 16 KB page size on the built .aab | Play 16 KB page size | Expo SDK 58 / RN 0.88 native libs; new dep react-native-share is Java-only | Check alignment in Play Console / bundletool |
| Manual | App access for reviewers | Play App access | Everything behind phone + PIN login | Make a separate reviewer account; put phone + PIN in Console → App access (not a real student's) |
| Manual | Closed testing gate | New personal accounts | Account type unknown | If personal account created after 13 Nov 2023: 12 testers for 14 days before production |
| Manual | Content rating + target audience | IARC / Target audience | Students (likely 16+); Rapid Fire multiplayer, gangs, friend codes | Answer IARC "users interact" = yes; choose 13+ / 16+ honestly |

Technical compliance — no issues found in the checks run for: placeholder text, localhost/http URLs, console.log (0), root ErrorBoundary (present), web-wrapper (WebView only renders offline math).
Policy — no issues found for: permissions (final list INTERNET, VIBRATE, MODIFY_AUDIO_SETTINGS; mic/storage/overlay/foreground-service blocked), media permissions (none), AD_ID (no ad SDK), foreground services (none), billing (coins/diamonds earned in-game, "No real money"), NTA affiliation disclaimer (present on Mission + series explainer).

## Detailed findings

### [BLOCKER] No working account deletion — Play account deletion
- What we saw: sign-up exists; the Delete account screen and its public web page both say deletion is not available and show no delete action.
- Why it's a risk: since 2024 Play rejects apps that allow account creation without in-app deletion plus a web deletion link.
- How to fix: the website backend needs an authenticated delete operation (or a real request queue processed within a stated time). Then add a PIN-confirmed "Delete my account" in the app and the same request on `/api/legal/delete-account`, covering the website account, results and Rapid Fire profile/data.
- How to verify: create a test account, delete it, confirm login fails and data is gone; put the web URL in Data safety.

### [WARNING] WhatsApp queries dropped by app.config.js
- What we saw: `app.config.js` maps the `expo-build-properties` plugin to a new object, discarding the `manifestQueries` set in app.json.
- Why it's a risk: Android 11+ hides WhatsApp from the app, so the direct "PDF WhatsApp" attach silently falls back to the share sheet.
- How to fix: spread the existing plugin options (`{ ...opts, android: { ...opts.android, enableMinify... } }`).
- How to verify: `npx expo config --type introspect` shows `com.whatsapp` under queries; on a device, the WhatsApp button opens WhatsApp with the file.

## Reviewer experience checklist
- Install & launch — pass (needs .aab device test)
- First-run clarity — pass
- Permission prompts shown in context — N/A (no runtime permissions)
- Core feature reachable — at-risk: needs a reviewer login in App access
- Purchase / restore path — N/A
- Support & legal links resolve — pass (privacy 200; deletion page loads but offers no deletion)
- Empty & offline states — pass (error/retry boxes; verify on device)

## Not verified here
- Real-device testing of the release build; Play pre-launch report
- Final target API, 16 KB alignment and versionCode on the built .aab
- Play Console forms: Data safety, content rating / IARC, target audience, App access, ads declaration
- Closed-testing status and developer account type
- Whether the website backend sends personal data to any AI provider
- Listing metadata, app name / icon (out of scope)

---

This skill report is guidance, not a guarantee of approval. It reflects only the checks listed above against the code as inspected. Play policies change often and reviewer enforcement varies.
