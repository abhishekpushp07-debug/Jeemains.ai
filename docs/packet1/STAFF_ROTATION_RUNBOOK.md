# Staff credential incident — protected operator execution

**Status: tooling verified with synthetic accounts; live incident NOT closed.**

The persisted staff password is in `tejas_users`. Changing only the bootstrap environment password does not rotate an existing account. Phone-only student sessions are a different identity plane and must not be revoked by this operation.

## Preconditions

1. Establish authorized operator access and a protected replacement-secret handoff channel. Do not use chat, a JSON test report, shell arguments, shell history, screenshots or source control for the secret.
2. Verify **every serving login/access/refresh node** runs the generation-fencing build. Drain old auth code before applying. If this cannot be established, do not pass the fenced-deployment confirmation. A single preview response does not attest an entire fleet.
3. Verify the exact staff account UUID and current credential generation through the protected operator channel. Generation zero includes legacy accounts where the field is absent. Unknown/malformed generations fail closed and need explicit investigation.
4. Arrange an approved replacement secret, control-plane audit and bootstrap-secret update. Ensure operator recovery if the process loses its response after the database commit.

## Dry-run (no mutation)

`python /app/backend/tools/rotate_staff_credential.py --account-id <staff-uuid> --expected-generation <integer>`

It emits only opaque account/generation information. Do not replace placeholders with credentials. It must not prompt for a secret, call the rotator or change a record.

## Explicit apply in a protected interactive terminal

Add all three flags: `--apply --confirm-revoke --confirm-fenced-deployment`.

The tool requests the replacement twice without echo. It accepts no password argument or piped secret. The target must still be owner/reviewer at the expected generation. A majority+journal acknowledged single-document CAS changes the stored hash, increments generation and records a server UTC timestamp plus operation UUID. Concurrent attempts at the same expected generation cannot both win.

All prior staff sessions become logically unusable through generation checks. Deleting old rows is secondary cleanup; a delayed pre-rotation session insert cannot restore access. Valid new-generation sessions and phone sessions are preserved. The CLI does not clear an independent `staff_auth_held` flag.

The receipt contains no password/hash/token/email/phone. `physical_cleanup=RETRY_REQUIRED` means the credential fence committed but row cleanup needs retry; it is not a reason to blindly reapply the old expected generation. Likewise a lost network reply does not prove no commit: inspect the operation UUID/generation safely before retrying.

## Verify and record

- Old access and refresh sessions fail; old secret fails; replacement sign-in succeeds.
- A deliberately delayed old-generation login/session cannot be used after rotation.
- Phone-only student entry and existing student sessions continue unchanged.
- Record the tested build digest, opaque operation receipt, affected-generation counts and protected audit location, never the secret.
- Update the protected bootstrap secret separately; prevent snapshots/restores from silently reintroducing the exposed credential. Regional restore/credential-epoch reconciliation remains an operator/P03/P10 gate, not proven by this local rotation primitive.

Do not mark the incident or Packet 1 exit complete until actual authorized execution and verification evidence exist. Neither the CLI's presence nor passing isolated tests closes the live incident.
