# Native app PIN update — publication handoff

Use this guide with the confirmed post-deployment PIN ZIP, not the older phone-only handoff.

Canonical API remains https://jeelive.ai/api. Keep all current user IDs, profiles, attempts, answers and results. Rapid Fire remains separate. Do not create a new database or re-register existing users to solve login failures. No payments or OTP are part of this update.

## Native screens to update

1. New student signup: phone + four-digit PIN + confirm PIN, POST /auth/phone/signup with phone,pin,confirm_pin.
2. Login: phone + four-digit PIN, POST /auth/phone with phone,pin. Preserve leading zeroes by treating PIN as a string. Do not log it.
3. Existing signed-in profile without PIN: GET /auth/session or /auth/me exposes pin_configured=false. Keep this session and account ID; show Set PIN. POST /auth/pin with that user's phone,new_pin,confirm_pin. Do not log out first or register a second profile.
4. Change PIN: same authenticated endpoint and form, only the current student's own phone. No OTP and no public forgot-PIN endpoint. Handle the fresh session cookies; old sessions on other devices become invalid after the change.
5. Legacy profile with no valid session and no PIN cannot be claimed using only a number. Show a clear unavailable-account/recovery message, not an automatic signup, PIN bypass or invented reset endpoint. Owner-approved recovery remains a separate decision.
6. Keep one secure cookie jar for JSON and protected question/solution images. GET /auth/session, single-flight /auth/refresh and session invalidation follow APP_INTEGRATION.md.
7. Respect429 Retry-After. Five-attempt short-window guard and20failed-check hourly budget apply. A successful login never erases the accumulated hourly failures. Do not retry automatically in a loop or downgrade to phone-only access.503 means temporary service trouble, not wrong PIN.

## Existing session / identity guarantees

The release does not bulk-sign-out or rewrite existing students. A still-valid legacy session has PIN version0 and can set its first PIN. Version changes invalidate prior cookies only when that student changes the PIN. Cookie strings can differ between browser and native; user.id and server-saved progress must match. Only server-acknowledged answers are shared across devices.

## Super Admin

The website /super-admin uses the existing owner staff login, with owner-only GET /api/admin/students. A student phone/PIN never grants admin rights. The directory exposes only id+phone, paginated50. Do not include owner credentials or student dumps in this handoff or native bundle.

## Acceptance evidence

The post-deployment ZIP must contain live-pin-verification.json and canonical-api-contract.json with live PIN routes confirmed. Real production signups and exam attempts are deliberately not created for QA. Real-auth end-to-end signup/PIN change/session revocation and two-session paper/save/result/solution flows were checked in disposable isolated databases, not on the actual Expo device. The app agent must verify actual native cookie persistence, same learner identity/result and original solution delivery on-device without resetting data.

The user explicitly requested backend PIN publication first, then this ZIP. Consequently old native NEW sign-ins require this app update; existing valid sessions should be preserved while implementing enrollment.
