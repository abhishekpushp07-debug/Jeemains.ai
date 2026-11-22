# RCA — jeelive.ai AITS re-read ("Mock 1 still 150 questions / 500 to fix")

READ-ONLY diagnosis. Nothing was modified, re-enqueued, reprocessed, published, or deleted.

## Verdict
The deployment succeeded and is serving, READER_VERSION=6 is live, and the automatic re-read **IS running and progressing right now**. The suspected cause — a stale finished `book_step` job blocking the re-read via DuplicateKeyError — is **DISPROVEN**. The Super Admin still shows the old "150 questions / 500 to fix" numbers simply because the two 3803-page books are only ~24–26% through the re-read; the mock question counts and `blocking_issues` do not regenerate until a book finishes reading → matching → rebuild/publish.

---

## 1. Deployment — completed and serving
- Active run: `2f69138a-496d-4aab-83df-b7aaa9ebe714`, type=redeploy, status=success.
- Created 2026-11-22T09:46:12Z, completed **2026-11-22T09:51:55Z**.
- Image: `customers-app-2@sha256:4b814e1f181701636fb6775cda29353919ee3e79a67e3bef55a5789d503209cc`.
- Live URL GET / → **200** (frontend served via Cloudflare/R2).

### Deployed source (sha256, read from the active run's pulled source at /app/scratch/backend/tejas/)
- `book_reader.py`  = `2671148024f36bae4c92aeb9a0d7fb0f5cc0aca592000e501181b18acf6df652`
- `book_publish.py` = `1d79f228da349ac3970758fb537822569ac5f24aa877a303130a123ff7a32dcb`
- `book_worker.py`  = `37624e2d6dce96ff0e63e548ec494c866fc16c11aea15a0019305704029cc813`
- READER_VERSION line (book_reader.py): line 6 → `READER_VERSION=6`

> NOTE on hashes: the deployed `book_reader.py` prefix is `2671…`, which does **not** match the preview hash prefix you quoted (`4e1e…`). The functional fix is confirmed present (READER_VERSION=6 and v6 behavior is live), so this is most likely a stale/partial preview reference on your side — but please reconcile which source `4e1e…` came from. No preview hashes were provided for `book_publish.py` / `book_worker.py`, so those were not compared.

---

## 2. tejas_books (latest snapshot; values were visibly climbing between reads)
Book `9799c544-bf43-5482-8237-5440a0c2567c` ("aits 1 to 25"):
- state=`reading`, removed=`false`, paused=`false`
- revision: `114` → `118` (incrementing)
- payload.reader_version=`6`  ✅ (new version)
- payload.read_pages: `800` → `1000`  (pages=`3803`)
- payload.message: "Read 1000 of 3803 pages. Unclear content remains private."
- payload.metrics.blocking_issues=`12500` (stale pre-v6 metric — recomputed only at publish phase)
- updated_at=`1795342420` (seconds-fresh)

Book `a06a5fa1-0c61-5e9c-9278-d0fb1638a820` ("26 to 50"):
- state=`reading`, removed=`false`, paused=`false`
- revision: `114` → `116`
- payload.reader_version=`6`  ✅
- payload.read_pages: `800` → `900`  (pages=`3803`)
- payload.message: "Read 900 of 3803 pages. Unclear content remains private."
- payload.metrics.blocking_issues=`12500`
- updated_at=`1795342398`

(Both documents are keyed by `_id` = the book id; filtering by a field named `id` returns 0.)
`tejas_book_pages` count for 9799c544 = **1000**, exactly matching read_pages — confirming genuine forward progress, not a loop.

---

## 3. tejas_jobs — kind=book_step for the two ids
The DuplicateKey hypothesis does not apply. `jobs.enqueue` builds the job id as `book_step-<book_id>:<revision>`, and `book.revision` increments on every step, so each re-enqueue gets a **new, non-colliding** id. There is no stale finished job sitting on the current revision.

Observed (newest first), all with error="" :
- 9799c544 `:114` → status `queued` (created 1795342176)
- 9799c544 `:112` `:110` `:108` `:106` `:104` → status `done`, message "Book batch saved."
- a06a5fa1 `:114` → status `queued` (created 1795342179)
- a06a5fa1 `:112` `:110` `:108` `:106` `:104` → status `done`, message "Book batch saved."

All completed jobs: attempts=1, error="", next_run_at=0, message "Book batch saved." No failed/errored/stuck jobs for either id. Each done job spawns the next revision — the chain is live.

---

## 4. Worker / maintenance loop — running
- Jobs for multiple books are actively running/queued/done with created_at up to the moment of investigation (e.g. 1795342179, then 1795342398/…420 on the next read). Other books also mid-flight: `4e23420a…:137` (running), `3a704ed9…:142` (running).
- Backend logs filtered for `Book step failed|recover|book_step|reader` over the last 120 min (Loki): **0 lines** — no "Book step failed", no recover errors since the deploy.

---

## Root cause
Working as designed, just **in progress**. After deploy, `jobs.py` maintenance → `book_worker.recover()` matched both books (`reader_version != READER_VERSION`), reset `read_pages=0`, set `reader_version=6`, and re-enqueued them. `read_batch` reads PAGES_PER_STEP=100 pages per `book_step` and re-enqueues while `read_pages < pages`. Both books are 3803 pages and currently only ~900–1000 pages in, state=`reading`. The mock-level "150 questions / 500 to fix" and `blocking_issues=12500` are computed in the later matching/rebuild/publish phase (`book.state` → matching → publish_batch), which hasn't been reached yet, so Super Admin still shows the pre-fix numbers.

No deployment defect, no code defect, no stale-job block.

## Suggested action
- **Wait and monitor.** read_pages is climbing (~100 pages / ~40s per book, worker shared across several books). Re-check Super Admin → JEE Main → AITS once both books leave `state=reading` and reach `ready`/`published`; the question counts and fix-needed totals regenerate then.
- Throughput note (not a fault): 2× 3803-page books plus other books share one worker, so a full re-read + republish takes time. If faster turnaround matters, that is a throughput/capacity consideration, not a bug.
- Reconcile the `book_reader.py` hash difference noted in section 1 (deployed `2671…` vs quoted preview `4e1e…`) to be sure you're comparing the intended source — functionally v6 is confirmed deployed and active.
