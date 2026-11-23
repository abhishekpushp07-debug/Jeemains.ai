# JEELIVE.AI — Production object-storage state report (read-only)

Deployment: campus-search-debug (jeelive.ai / www.jeelive.ai)
Live run: `2f69138a-496d-4aab-83df-b7aaa9ebe714` (type=redeploy, completed 2026-11-22T09:51:55Z)
DB read: `pdf-engine-v2-test_database`
Snapshot taken: ~2026-11-23T07:57Z

## Headline
**No active object-storage failure in production.** Emergent private-storage health is green, Supabase is carrying all new writes, and there is NO evidence of any `Private storage unavailable`, `Supabase …`, or `vault_unavailable` event in the observable window. The one failed book and the 7 failed jobs are caused by a **409 book-lock contention** ("This book changed or is processing a batch"), NOT by storage.

---

## 1. Backend logs — storage error texts

**Tooling limitation:** the log backend only returns up to the last **1440 minutes (24h)**; a full 7-day history is NOT available through this agent. The figures below cover the last 24h of the active run.

- `Private storage unavailable` (any NNN, PUT or GET): **0**
- `Private storage initialization unavailable`: **0**
- `Private storage connection interrupted`: **0**
- `Private storage could not complete`: **0**
- `Supabase did not save the file`: **0**
- `Supabase connection failed`: **0**
- `Supabase file unavailable`: **0**
- `Supabase big-file upload`: **0**
- `Supabase bucket`: **0**
- API error code `vault_unavailable` (HTTP 503): **0**
- Emergent objstore PUT/GET answering 500: **none observed**

HTTP status histogram over the 24h window (non-health traffic): `200 × 98`, `401 × 7`, **zero 5xx (no 500/502/503/504)**.
`GET /api/admin/storage/health` is returning **200** consistently (401 only when the caller is unauthenticated) → storage health endpoint is green.

The only errors in the window (3) are a single repeating background-job traceback:
`fastapi.exceptions.HTTPException: 409: This book changed or is processing a batch. Reload and retry; saved work is retained.` at `backend/tejas/book_store.py:72 lock_book` ← `book_worker.py:132 step` ← `jobs.py:97 run_job` (`Background job failed (kind=book_step)`). This is lock contention, not storage.

## 2. Production env key NAMES (names only; values never read)
Present (non-empty):
- `SUPABASE_URL` ✓
- `SUPABASE_SECRET_KEY` ✓
- `EMERGENT_LLM_KEY` ✓
- `INTEGRATION_PROXY_URL` ✓
- `WEBHOOK_CRON_SECRET` ✓

Present but EMPTY:
- `MEDIA_CDN_URL` (exists, value is blank)

ABSENT (key name not present in the active run's secrets at all):
- `SUPABASE_BUCKET` ✗
- `PICTURE_PILOT_PHONES` ✗

Note: Supabase writes are clearly succeeding (22,377 files on `sb://`), so if a bucket is required it is being supplied by a code default rather than this env key — confirm intent.

## 3. MongoDB read-only counts

(a) `tejas_files` by path prefix:
- `sb://…` (Supabase): **22,377**
- not `sb://` (Emergent storage): **716**
- (identical to the 22 Nov report → no drift; no new Emergent-storage fallbacks since)

(b) `tejas_books` by state (8 docs total):
- published: **3**
- attention_needed: **3**
- ready: **1**
- failed: **1**
  - title: "Chemistry chapter-wise (boxed) — engine test"
  - message (first 200): "Processing interrupted. Retry resumes the saved pages without uploading again."
  - updated_at: 1795276563.52 (~2026-11-21 ~15:56 UTC)
  - → message is a processing-interrupt/retry notice, NOT a storage error.

(c) `tejas_book_mocks` publish_hold:
- docs with a NON-EMPTY `publish_hold`: **0**
- (205 docs have `publish_hold: ""` — empty string placeholder = no hold; distinct values = `[""]`)
- → nothing is on publish hold.

(d) `tejas_jobs` status=failed, last 7 days: **7**, all `kind=book_step`:
- 6 × error "Processing could not finish. Your originals and saved answers are safe. Retry after the cause is resolved."
- 1 × error "Worker recovery budget exhausted. Saved data is safe; retry after resolving the cause."
- created_at span ≈ 1795301474 → 1795307671 (~2026-11-21 23:00 → 2026-11-22 00:34 UTC)
- → consistent with the 409 lock-contention traceback above; none reference Supabase/Emergent storage.

(e) `tejas_operations` id="maintenance": `last_run` = 1795420171.33 (~2026-11-23 07:49 UTC, ~8 min before snapshot) → maintenance loop is running normally.

## 4. Live build + source files
- Live run id: `2f69138a-496d-4aab-83df-b7aaa9ebe714`, completed **2026-11-22T09:51:55Z** (redeploy, image sha256:4b814e1f…).
- `backend/tejas/machine.py`: **MISSING** (not in deployed source)
- `backend/tejas/png_small.py`: **MISSING** (not in deployed source)
- (`backend/tejas/` exists with ~130 other modules incl. book_store.py, book_worker.py, storage_health.py; neither file found anywhere under backend/.)

## 5. Pod restarts / OOM / 5xx (last window)
- Active-run pods (2 replicas): `restart_count = 0` on both, both Running/Ready, state running. `kill_findings`: none. No OOMKilled, no CrashLoopBackOff, no evictions.
- 5xx over the 24h window: **0** (histogram = 200/401 only).
- 7-day caveat: pod events + logs only reach back ~24h and only cover the current active run (promoted 2026-11-22 09:51Z). Days before that ran under separate runs (redeploys 21/20/19 Nov) and cannot be re-inspected here.

---

## Conclusion
Emergent object-storage PUT/GET is **not** returning 500 in production within the observable 24h window, the storage-health endpoint is green, and Supabase is absorbing all new writes. **No book, mock, or job is currently stuck because of object storage.** The single failed book and the 7 failed `book_step` jobs are a **409 "book changed / processing a batch" lock-contention** condition — they are retryable and their saved data is intact.

### Things for the user/E1 to confirm (not storage faults)
- `SUPABASE_BUCKET` and `PICTURE_PILOT_PHONES` key names are absent, `MEDIA_CDN_URL` is empty — confirm these are intended (Supabase writes work regardless).
- `backend/tejas/machine.py` and `backend/tejas/png_small.py` are absent from the live build — if they are expected, E1 must add them and redeploy.
- The 1 failed book + failed jobs can be retried; recurring 409 lock-contention under concurrent book processing may warrant a code review of the lock/retry path in `book_store.py`/`book_worker.py` if it keeps recurring.
