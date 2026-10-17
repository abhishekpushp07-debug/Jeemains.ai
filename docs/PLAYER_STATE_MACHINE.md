# Player state machine — active custom-practice profile

`not_visited -> visited_blank -> draft_pending -> acknowledged_answered`

- Any viewed question may be marked: `marked_blank` or `answered_and_marked`.
- Clearing a response creates a new revision containing an empty string; it is not saved until acknowledged.
- Mark state and answer state are independent. Submitted grading uses only the last accepted response, not the draft or colour in the palette.
- Drafts use `{value,marked,revision,request_id}` and remain in browser storage through refresh/offline. Same-request retries are idempotent; stale revisions conflict rather than silently overwrite another device.
- Numeric entry keeps the exact typed string. Policy normalizes whitespace, Unicode minus and leading zeros to an integer. Invalid noninteger drafts remain visible, are rejected and cannot be submitted silently.
- The countdown derives from a server timestamp plus monotonic browser elapsed time. Device wall-clock edits cannot change the deadline. At displayzero, the client asks the server for status; it never voluntarily submits early merely because localtimechanged.
- A server deadline rejects late saves independently of cron. Expiry/submission is an atomic status transition. Finalization freezes a ledger and permanent receipt. Duplicate submission returns that same receipt.
- Published missing source assets block preflight. A source image that fails in the player blocks that question’s answer controls until successfully retried.
- Current practice navigation is free. Official BITSAT bonus irreversible transition, section locks, WBJEE digitalOMR/multiple-correct and COMEDK officialmodes are not activated without a reviewedyearprofile.
- `completed_original -> correction_available` does not mutate originalresponses,originalledger ororiginalreport. Userselects a labellednewscoreversion; newPDF and matchedsolutionassets follow that selectedversion.

Phone-only access is intentionally unverified: anyoneentering thesamenumber can reopen thisprofile. Staffkeys/publishing use separatepasswordauth.
