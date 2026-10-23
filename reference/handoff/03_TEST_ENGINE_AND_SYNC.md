# Test engine: implement these contracts before polishing screens

## 1. Start safely
1. Fetch catalogue/set availability and frozen-rule preview.
2. POST `/api/sets/{set_id}/preflight`, body `{ "preview": false, "test_response": "[LOCAL_DEVICE_CHECK]" }`. This writes a preflight marker, not an exam attempt; it is NOT a safe read-only test against production.
3. Create one random UUID start_key for this start intent, persist it before transmission. POST `/api/sets/{set_id}/start` with `{ "start_key": "[UUID_FOR_THIS_INTENT]", "device_checked": true, "preview": false }`.
4. Retry the same start intent with the SAME start_key after timeout. Never generate a new key just because a response was lost. Backend may resume an existing active/first live attempt.
5. Keep returned id, questions, status, server_now, deadline, rules, answers, visited and any bonus/competition state. Use the server's question IDs, not array indices.

## 2. Acknowledged autosave, not fire-and-forget
PUT `/api/attempts/{attempt_id}/answers/{question_id}`:
```json
{"value":"A","marked":false,"revision":1,"request_id":"[NEW_UUID_FOR_THIS_EDIT]"}
```
Optional confidence is a finite number0..1. Empty string clears a response. MCQ values are actual option keys; integer values are strings validated against the returned question/rules. Current runtime answer value limit is **30 characters**, even where a broader ingress schema advertises128—honor the stricter runtime model.

Persist draft first under `(user.id, attempt.id, question.id)`. Save revision must be the last acknowledged answer revision +1 (first is1). Keep an immutable in-flight command: question, value, marked, confidence, revision, request_id. Retry the exact command on network uncertainty. Changing payload under the same request_id causes409.

Response inner data includes `accepted`, `server_now`, `current_revision`, `duplicate` and possibly `command_state`. Accepted contains normalized_value, revision, request_id, accepted_at and optional server_seq. Clear a local draft only if the ACK corresponds to that exact pending command; an ACK for an older edit must not erase a newer draft. Serialize saves per question and reconcile revision from ACK/read before advancing later edits.

UI distinguishes: local/pending, sending, server-acknowledged, conflict, offline. Never claim “saved” on tap alone. A server ACK is not equivalent to a client write to Room. Do not alter marks or scores from local state.

409 after a concurrent device edit is not permission to bump revision automatically. Preserve the local draft, fetch the authoritative attempt and give a deliberate reconcile/discard choice. 409 after deadline/seal means late work cannot be scored. Runtime history budgets are finite; don't loop endlessly.

## 3. Visit is not an answer
POST `/api/attempts/{id}/visit` with `{ "question_id": "[QUESTION_UUID]" }` returns the actual `visited` list. Do NOT expect `{ok:true}` or wipe visited state when a malformed/missing response arrives. Visit doesn't mark the question answered or award score.

## 4. Native timer and process death
Server timestamps are Unix **seconds**. Anchor server_now to Android `elapsedRealtime()` when a response arrives; displayed remaining time is deadline minus anchored server time, not device wall clock. On resume/reconnect read current attempt and re-anchor. A deadline of0 means no deadline when the server uses that value.

Timer does not pause when app backgrounds, process dies, screen rotates or network drops. Local drafts can survive process death, but cannot extend the server deadline. When time reaches0, stop editing and ask server for authoritative state with bounded retry. Server sealing can happen on subsequent reads; do not assume GET attempt is side-effect-free when an active deadline has elapsed.

Before background/process death, persist pending intents. WorkManager may help bounded recovery but is not an exact deadline timer and must not submit after a server deadline pretending it was on time. Keep drafts separated between accounts; never resume another user's attempt by a cached ID.

## 5. Submit and grade are separate states
Flush all pending saves and wait for acknowledgements before manual submission. POST `/api/attempts/{id}/submit` with `{}`. Persist returned receipt before clearing pending state. A202 with grading_status queued/running is a **sealed submission awaiting grading**, not a failed submission.

GET `/api/attempts/{id}/results?score_version=original`:
- 202: grading in progress; use Retry-After/retry_after_ms with bounded jitter/lifecycle-aware polling.
- 200 with `status:embargoed`, release_at: wait for release; do not synthesize analysis/solutions.
- 200 completed results: render server ledger, rows, version metadata and analytics.
- 403 while active: solutions are not released.
On a lost submit response, reload attempt/results. Do not create a new attempt or declare zero score.

### Failed grading and job recovery
A results202 payload can contain job_id and grading_status. GET `/api/jobs/{job_id}` returns this user's permitted job state; this GET can dispatch queued/running background work, so it is NOT a harmless production test. Use only an ID supplied by the server, never synthesize grade IDs.

If grading_status/job status is failed, offer Retry grading: POST `/api/jobs/{job_id}/retry` with `{}`. The server returns done unchanged, retries a failed allowed job, or409 if already processing/a competing retry won. Then poll results with bounded backoff. Never retry an AI or safety-held content job to bypass a pause. Saved/sealed answers do not change when grading is retried.

### Optional existing report contract, not a new UI requirement
POST `/api/attempts/{id}/report` with score_version can return a report job only when source redistribution rights and release allow it. GET `/api/jobs/{job_id}/download` serves authenticated application/pdf only for an owned completed report after release. The current web result Download control is intentionally hidden; including these API contracts is not permission to restore that button or add a native export feature without approval.

## 6. Private source images and solutions
For each `asset_count`, fetch authenticated PNG bytes:
`GET /api/attempts/{id}/questions/{qid}/asset/question/{zero_based_index}`.
For released result rows, use `solution_asset_count` and `/asset/solution/{index}`. The image loader must share the same session cookies and refresh policy as the API client. Never place tokens in image URLs or fetch unauthenticated storage paths from q_refs/s_refs.

Source-image content may intentionally have empty text to avoid inaccurate extraction. Show original image with zoom and accessible text if supplied; do not replace it with generated OCR/AI text. Keep a white reading surface. Use account-scoped private caching, no public external-storage copies, and clear decoded assets on signout. Do not prefetch forbidden solution routes while exam is active.

On showing a released solution call POST `/api/attempts/{id}/questions/{qid}/solution-open` with `{}`. This tracks consultation; it does NOT generate an AI solution. Preserve error/retry state before confirming reflection's reviewed_solution flag.

Do not confuse consultation with legacy POST `/api/attempts/{id}/solutions/{qid}`: the latter currently returns410 for authenticated requests (AI generation paused). It appears in the route inventory for honesty, marked unavailable_http_410; Android must not offer a Generate button or repeatedly call it. GET of that legacy route can read an already-saved supplement after ownership/release checks. `/attempts/{id}/ai-solutions` exposes existing saved metadata, not a generation entitlement.

## 7. Reflection and reports
PUT `/api/attempts/{id}/reviews/{qid}` is a private, revisioned study record, separate from answers/ledger. Use a new immutable request_id for each intended change; score_version scopes review state. Categories: concept_gap, calculation, silly_mistake, time_pressure, misread, guess, other. Note <=500 characters. identified_error requires category; wrote_note requires text; reviewed_solution requires successful consultation; retry_planned is explicit. “Completed” means actions recorded, not demonstrated mastery.

POST `/api/attempts/{id}/questions/{qid}/report-wrong` accepts category question/key/solution/display, context attempt/results/solutions, note<=600. Reporting does not mutate the answer key or instantly change the score. Only show the server receipt.

## Reference warning
Current HTTP autosave is the deployed practice contract. Do NOT implement hypothetical SQL/live-cell writer-generation protocols from old planning files; those are not mounted native API routes. No client-side claim of unlimited concurrency, perfect offline scoring or proctoring.
