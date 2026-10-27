# Website source compatibility gate — no backend mutations performed

## Owner-provided repository
`https://github.com/abhishekpushp07-debug/Jeemains.ai/settings`

The settings page is not publicly accessible, but the repository itself is public and was successfully read without credentials. No GitHub token is needed to inspect this repository. No pushes, settings changes, branch merges or live-code replacements were made.

## Verified repository refs
- `main`: `2e0c883da0c5c6ddfe7b008bfbfdeb7f5dbbc442`, dated2026-10-26 12:19:40UTC.
- `App`: `e25ec0fb35092c2e231518b37d73316b9f9feed9`, dated2026-10-27 06:36:19UTC. This is the Expo mobile/proxy application, not the canonical website authentication source.
- Read-only remote enumeration found no other heads, tag refs or pull-request head refs.
- A sparse read-only working copy of `main` is at `/tmp/jeelive-canonical-source`; `App` was fetched for tree inspection, not merged or checked out over it.

## Confirmed incompatibility with the running website
Repository `backend/tejas/phone.py`:
- `PhoneInput` accepts only `phone`.
- `/api/auth/phone` upserts an unverified-phone profile and creates a session without a PIN.

Repository `backend/tejas/request_contracts.py`:
- `PhonePayload` accepts only `phone`; strict `extra='forbid'` rejects additional fields.

Fresh LIVE `JEELIVE_API/openapi.json`, inspected read-only on2026-10-27:
- `/api/auth/phone` requires **both phone and PIN**.
- Additional live routes exist: `/api/auth/phone/signup`, `/api/auth/pin`, `/api/auth/owner/student-pin-reset`.
- Corresponding PIN implementation is absent from the supplied repository's canonical backend. Exact hash field/algorithm cannot be determined from OpenAPI and MUST NOT be guessed.
- No canonical account-deletion operation is documented.

Evidence copy: `/tmp/jeelive_latest_live_contract.json`. Public health endpoint had no directly usable build/revision identifier in inspected top-level fields. No credentials, learner account writes or deletion calls were sent for these checks.

## Why work is paused at this gate
Applying the old phone-only backend over the running website could regress its working PIN login. Implementing destructive account deletion against guessed PIN/storage/session behavior would not satisfy the owner's explicit safety requirement. The mobile proxy cannot substitute local RF deletion for deletion of the external website account.

Do not execute `backend/tools/reset_student_data.py`, owner credential tools, seed scripts or legacy backend startup against any real database. Those are not safe substitutes for a verified per-user account deletion flow.

## Required next input
The current website backend source/branch/commit/export that actually contains its working PIN login. This might be unsaved changes in the website project or a different repository; those possibilities are NOT established facts. Obtain the source rather than inventing its location.

Once the matching source is available: get the auth integration guidance against that implementation, design fresh-PIN/ownership/idempotent cross-service deletion, implement additively, and test only isolated disposable data. Keep the currently working app and website unchanged until verified. No production account may be deleted merely to test the feature.