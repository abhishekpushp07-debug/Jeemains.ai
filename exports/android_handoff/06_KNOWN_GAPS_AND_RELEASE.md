# Known gaps and boundaries — do not hide these

## Existing functionality vs native release readiness
The backend exposes JSON and authenticated binary APIs reusable by Android. This package documents that compatibility; **it does not contain a native client already built/tested**, nor a guarantee that every API is currently usable for every account.

1. **Unverified phone ownership.** Current `/auth/phone` is number-only convenience access, not OTP. A native app must not label it verified/secure identity. Verified learner identity is a prerequisite for a high-trust public launch. Changing auth is separate approved backend/integration work, not something to fake in the client.
2. **Cookie-only current transport.** Android must implement correct cookie refresh and asset authentication. There is no current bearer-token replacement route. A mobile-specific auth API can be added only as separately reviewed work if needed; a backend rewrite is not required simply because the client is native.
3. **Some administrative content operations are deliberately held.** Upload/parse/extract/publish/regrade routes can return503 capability_held, and internal capability guards can apply too. Do not bypass safety gates, enable upload shortcuts or claim every web administration flow works. Existing published learner practice is a separate path.
4. **Actual Android integration untested.** No emulator, real-device APK, image library cookie propagation, Room migration, OS background restriction or Play Store test was completed while creating this handoff. Stage9 of the plan is mandatory.
5. **Schema vs live image.** Packaged OpenAPI is sourced from preview; do not assume an asynchronous live deployment already includes every newest endpoint/UI revision. Confirm target environment and contract non-destructively before integration.
6. **Future scalable-live-cell documents are not deployed endpoint contracts.** Do not invent SQL authority, writer leases, generic command envelopes or 500k concurrency guarantees. Use the mounted API described here. Load/capacity certification is separate.
7. **No new native-only integrations.** Push notification registration, verified Android App Links, social login, offline full-PDF library, payment subscriptions and device proctoring are not promised by this kit. Don't fabricate support endpoints.
8. **Store/legal release work remains.** Choose/confirm `[ANDROID_APPLICATION_ID]`, publisher/signing, legitimate privacy/deletion/support flows, permissions and data-safety declarations. Account deletion needs an actual approved server workflow if required by distribution policy; a local logout is not account deletion. Do not invent legal URLs.
9. **No secret transfer.** Use a secure credential channel for an authorized QA account/environment when genuinely needed. No operator password, refresh cookie, Mongo URI, provider key or signing key belongs in this ZIP or an APK.

## What was checked for this handoff
Source/API/schema mapping, strict request contracts, session mechanism and source-asset routes were inspected. The final export validation records archive integrity, allowlisted files, resolvable schemas, no credential-bearing files and actual ZIP download. These checks are NOT proof that native Android end-to-end flows work.
