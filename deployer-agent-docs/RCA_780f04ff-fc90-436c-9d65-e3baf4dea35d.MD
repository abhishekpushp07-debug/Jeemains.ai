# RCA — jeelive-mobile Android APK cannot reach backend ("Connection interrupted")

## Symptom
Installed Android APK (built today after the latest Publish) shows "Couldn't check your session" on launch; every request (sign-in, Forgot PIN) fails with the generic "Connection interrupted" error. Production backend is healthy from outside (`/api/health/load` 200, `/api/account/forgot-pin` 422 on bad input, `/api/jl/auth/session` answers). The failure is therefore on the device, before any HTTP request leaves the phone.

## Root cause (CONFIRMED)
The app learns its backend address ONLY from a build-time env var that lives in `frontend/.env`, and `.easignore` strips that file from the EAS upload — so on the EAS build worker `EXPO_PUBLIC_BACKEND_URL` is undefined and the shipped app has `extra.backendUrl === undefined`.

Chain of evidence:

1. **The only injection mechanism is the `.env` file.** The Android Cloud Build step (`android_eas`) injects the production backend URL by a `sed` rewrite of `frontend/.env`:
   ```
   if [ -f .env ] && [ -n "$PREVIEW_DOMAIN" ] && [ -n "$BACKEND_URL" ]; then
     sed -i "s|https://[^/]*preview[^/]*\.${ESCAPED_DOMAIN}|${BACKEND_URL}|g" .env ...
   fi
   ```
   There is NO EAS server-side env var fallback. The same build log explicitly prints:
   `No environment variables with visibility "Plain text" and "Sensitive" found for the "production" environment on EAS.`
   So `EXPO_PUBLIC_BACKEND_URL` / `EXPO_PUBLIC_JEELIVE_API` can only reach the bundle via the uploaded `.env`.

2. **`.easignore` removes `.env` from the EAS upload.** `eas build` compresses project files and uploads them to the EAS Build worker (where Metro evaluates `app.config.js` and inlines `EXPO_PUBLIC_*`). EAS honours `.easignore`. Both ignore files exclude the env file:
   - `/app/frontend/.easignore` lines 12–17: `.env`, `.env.*`, `*.env`, `**/.env`, `**/.env.*`, `**/*.env`
   - `/app/.easignore`: `.env`, `.env.*`, `*.env` (pattern without leading slash also matches `frontend/.env`)
   With no VCS (`EAS_NO_VCS=1`, `git rev-parse` fails in the log), EAS uses the frontend dir as project root and applies `frontend/.easignore`. Either file alone is enough to strip it.

3. **With no `.env`, the config resolves to undefined — verified in the eph sandbox** against this exact run's source:
   ```
   WITHOUT .env -> extra.backendUrl= undefined   jeeliveApi= undefined
   client.ts BASE would be   = undefined/api/jl
   forgot-pin URL would be   = undefined/api/account/forgot-pin
   WITH .env present -> extra.backendUrl= "https://jeelive-mobile.emergent.host"
   ```
   `frontend/app.config.js` sets `extra.backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL` (undefined when `.env` is absent). `frontend/src/api/client.ts` does `BACKEND = extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL` → both undefined → `BASE = "undefined/api/jl"`. `fetch("undefined/api/...")` on React Native throws immediately (no valid URL), which `client.ts` catches and rethrows as `ApiError("Connection interrupted...")` / the session check surfaces "Couldn't check your session". This reproduces the reported symptom exactly.

## Answers to the four questions
1. **How the URL is provided:** solely by rewriting `frontend/.env` in Cloud Build (sed), then relying on that `.env` being uploaded to EAS. No EAS Plain/Sensitive env vars exist (per build log).
2. **Does the embedded config show backendUrl empty/undefined:** The Cloud Build log does not print the resolved `extra` (final config resolution + Metro inlining happen on the EAS worker `31ab4e75-...`, whose logs live on expo.dev and are not reachable from here, so I did NOT directly observe it). I verified the equivalent resolution in the sandbox: without `.env`, `extra.backendUrl` / `extra.jeeliveApi` are `undefined`. Inference + code-level verification, not direct EAS-worker-log observation.
3. **Does `.easignore` excluding `.env` break injection:** YES — this is the root cause. The sed-sanitised `.env` is excluded from the EAS archive, so `EXPO_PUBLIC_BACKEND_URL` never reaches the bundler.
4. **Did the backend see requests from the phone ~02:43 IST (≈21:13 UTC):** No phone requests are expected, because the device builds `undefined/api/...` and `fetch` fails locally before any request leaves the phone. I could NOT corroborate this from server logs: inbound HTTP access logs are not shipped to the available log store — even the user's own external test calls to `/api/account/forgot-pin` and `/api/health/load` (which returned 422/200) do not appear in the backend logs over a 4h window. So log-absence is not usable as proof either way; the device-side code path is the conclusive evidence. (Note: the APK the user tested was from the successful Android build at 20:41 UTC / 02:11 IST; the newest Android build `31ab4e75` started 21:12 UTC and was still running — but all of these builds share the identical defect.)

## Scope
This also affects the EAS **OTA update** publish during deploy (`eas update` respects the same `.easignore`), so the OTA-delivered JS bundle has the same undefined `backendUrl`. The defect is not specific to the APK.

## Fix (Source — frontend)
Stop `.easignore` from stripping the env file that carries `EXPO_PUBLIC_*`. The values in `frontend/.env` are public-by-design (baked into the client bundle) and the preview URL is rewritten to production by the pipeline's sed before upload, so shipping it is safe. Keep all signing/secret excludes (`*.pem *.key *.jks *.keystore *.p8 *.p12 credentials.json token.json`).

Apply to BOTH files:

- `/app/frontend/.easignore`: remove the lines `.env`, `.env.*`, `*.env`, `**/.env`, `**/.env.*`, `**/*.env`.
- `/app/.easignore`: remove the lines `.env`, `.env.*`, `*.env`.

(If you prefer to keep excluding arbitrary env files, instead append a negation AFTER the exclude block — `!.env` in `frontend/.easignore` and `!/frontend/.env` in the root `.easignore`. Removal is more robust; negation interacts awkwardly with the `**/.env` patterns.)

After the edit, re-trigger the deploy (to re-publish the OTA bundle) and re-run "Generate build" for Android/iOS. Verify the new APK by confirming `Constants.expoConfig.extra.backendUrl === "https://jeelive-mobile.emergent.host"` and that launch no longer shows "Couldn't check your session".
