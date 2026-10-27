# Canonical website dependency — PIN-confirmed direct account deletion

## User-approved outcome
- PIN-confirmed **direct deletion**, not a request/email-only substitution.
- Official privacy contact: **Abhishek@billpe.com**.
- Delete the real linked JEELIVE website account and associated personal academic/app data; do not delete only RF data or clear device cache and call it complete.
- Feature implementation approval is NOT permission to delete the current learner or any existing real account in tests.

## Current verified blocker
On2026-10-27 the main agent fetched the LIVE canonical `JEELIVE_API/openapi.json` without credentials/mutations. It contained121paths. The only documented DELETE operations were `/api/my/tests/saved/{id}` and `/api/studio/all-india-jee/{set_id}`. Neither is account deletion. No account/self-user deletion contract was found.

Current source handoff also states the endpoint is not exposed. A public Git/project URL for the website backend was not found in the supplied handoff. The companion FastAPI app cannot safely erase external website records without an authorized canonical operation.

**Needed from owner:** the project/repository/source containing the running `jeelive.ai` account backend, or its newly implemented and verified account-deletion contract. Do not send keys/PINs in chat; any necessary credentials must use secure credential collection later. Do not invent a deletion endpoint or assume privileged database access exists.

## Required canonical-side behavior (requirements, NOT an existing API)
1. Establish the authenticated current account from the real canonical session. Require fresh PIN confirmation and explicit irreversible-action consent. Enforce ownership, PIN throttling and appropriate CSRF/origin protections; never trust a client-supplied UID.
2. Document which account records, private attempts/answers/reports/sessions and linked personal records are removed or irreversibly anonymized. Do not remove other learners' data or shared published content indiscriminately. Explain legitimate retention exceptions.
3. Provide a durable, idempotent operation/result so a timeout cannot become false success, and a retry after session revocation can determine the outcome without recreating the account.
4. Coordinate with linked companion RF data. The companion must receive trusted server-to-server confirmation/receipts bound to the verified UID, not a client boolean. Handle partial failures durably, revoke grants/sessions, and clear appropriate device data only after verified outcomes.
5. Provide a real external-browser route so users can initiate deletion outside the app with the same ownership/fresh-PIN checks. Do not email or log the PIN.
6. Exercise wrong-PIN, UID substitution, expired session, duplicate/retried request, upstream timeout, partial cleanup, logout/relogin and cross-account isolation on controlled disposable test data. Never delete the approved real test/learner account.

## What the companion app now does
- Privacy/support information is readable in-app before sign-in and at public `/api/legal/privacy`.
- `/delete-account` and `/api/legal/delete-account` truthfully show direct deletion unavailable; no PIN field, deletion action, success state or email-request fallback is presented.
- This is **not** a completed deletion feature or Google Play account-deletion compliance. Do not flip a capability flag or change the wording to 'deleted' without implementing and verifying the real cross-service operation.

## Separate remaining release evidence
SignedAAB/versionCode/targetAPI/64-bit/16KB alignment, physical-device UX, the user's<20MBartifact goal and Play Console declarations/test eligibility remain separate verification gates. ExpoDoctor20/20 is native project validation, not proof of those or store approval.