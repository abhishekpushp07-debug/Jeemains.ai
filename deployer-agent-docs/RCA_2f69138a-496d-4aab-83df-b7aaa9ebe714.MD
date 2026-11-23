# JEELIVE.AI Production Read-Only Audit (strictly read-only; nothing was changed)

Deployment: campus-search-debug (jeelive.ai / www.jeelive.ai, both verified). Frontend: Cloudflare. Tier: tier_4. DB read: `pdf-engine-v2-test_database`. "Now" reference ≈ 2026-11-22 14:0x UTC (unix ~1795356300).

## 1) BUILD / VERSIONS  — KEY FINDING: production runs reader v6, NOT v7
- Serving run: `2f69138a-496d-4aab-83df-b7aaa9ebe714`, type=redeploy, status=success, completed **2026-11-22T09:51:55Z** (created 09:46:12Z). Image `...customers-app-2@sha256:4b814e1f181701636fb6775cda29353919ee3e79a67e3bef55a5789d503209cc`.
- Deployed source (read from this run's pulled source in sandbox):
  - `backend/tejas/book_reader.py` → **READER_VERSION = 6**  (preview = 7 → v7 is NOT deployed)
  - `backend/tejas/book_cutter.py` → **CUT_VERSION = 3**  (matches preview)
- Consequence vs. the stated fix: v6 already clears AITS false-blockages (confirmed below: AITS blocking_issues 0 and 1). The v7 fix for **BITSAT chapter-wise** is NOT in production, so the two BITSAT chapter-wise books (Logical Reasoning, Chemistry) still carry large blocking counts.

## 2) BOOKS — owner abhishek@billpe.com (owner_id edc17534-b756-4b0b-9734-7e1f9a9d3b97; tejas_users _id 6ad3c6d2a40660b01a447aac, role owner)
All four target books: reader_version=6, read_pages == pages (reading finished), paused=false, archived=absent/false, removed=false, plan all "list"/"bookmarks" as noted, destination.defaults present.

### AITS JEE Main — "aits 1 to 25"  (9799c544)
- state=**ready**, reader_version 6, read_pages 3803 / pages 3803, updated ~213 min ago.
- payload.message: "Clean mocks are isolated from held content. Review the book map and Attention Needed queue."
- plan_source: (absent — AITS list layout). destination.defaults: minutes 180, correct 4, wrong -1. metrics.blocking_issues: **0**.
- mocks: 25 total → **ready 25**, held/published/scheduled 0. total questions = 25×75 = **1875**. sum len(issues) ≈ 0 (ready mocks carry no issues; book blocking_issues=0).

### AITS JEE Main — "26 to 50"  (a06a5fa1)
- state=**attention_needed**, reader_version 6, read_pages 3803 / 3803, updated ~212 min ago.
- message same as above. plan_source absent. destination.defaults: minutes 180, correct 4, wrong -1. metrics.blocking_issues: **1**.
- mocks: 25 total → **ready 24, held 1**. total questions = 25×75 = **1875**. sum len(issues) = **1**.
  - The single held mock `3bd70c9e` (75 Q) carries exactly 1 issue: "Page 2938: Q46: crop boundary crosses text or a diagram; adjust the region." → pattern "Page N: QN: crop boundary crosses text or a diagram; adjust the region." ×1.

### BITSAT chapter-wise — "logicalreasoning" (9983c518)
- state=**attention_needed**, reader_version 6, read_pages 1119 / 1119, updated ~191 min ago.
- message same. plan_source **bookmarks**. destination.defaults: minutes 60, correct 3, wrong -1. metrics.blocking_issues: **3532**.
- mocks: 18 total → **held 18** (ready/published/scheduled 0). total questions = 18×50 = **900**.
- sum len(issues): not fully enumerated line-by-line (volume), book aggregate metrics.blocking_issues = **3532**.
- distinct issue PATTERNS (digits→N) present:
  1. "Questions QN: missing or conflicting supplied key."
  2. "Questions QN: incomplete options or key does not match printed labels."
  3. "Questions QN: original key region required."
  4. "Questions QN: original solution expected but not captured; attach its regions."
  5. "Questions QN: ambiguous worked-solution start/continuations."
  6. "Page N, QN: source region needs review."
  7. "Page N: Bare solution numbers may be numbered steps; confirm anchors."
  (patterns 1–5 dominate — one line per flagged question; 6–7 are sparse page-level notes.)

### BITSAT chapter-wise — "chemistry" (69f7ecde)
- state=**attention_needed**, reader_version 6, read_pages 2167 / 2167, updated ~173 min ago.
- payload.message: "Clean mocks are isolated from held content. Review the book map and Attention Needed queue." plan_source **bookmarks**. destination.defaults: minutes 60, correct 3, wrong -1. metrics.blocking_issues: **4905**.
- mocks: 32 total → **published 7, held 25** (ready/scheduled 0). total questions = 7×50 + 24×50 + 1 = **1551**.
- sum len(issues): not fully enumerated line-by-line; book aggregate metrics.blocking_issues = **4905**.
- distinct issue PATTERNS (digits→N), 8 present:
  1. "Questions QN: missing or conflicting supplied key."
  2. "Questions QN: incomplete options or key does not match printed labels."
  3. "Questions QN: original key region required."
  4. "Questions QN: original solution expected but not captured; attach its regions."
  5. "Questions QN: response type is unresolved."
  6. "Key/solution has no matching question: ('questions', 'questions', N)"
  7. "Page N: QN: confirm response type, options and continuation."
  8. "Printed optional/rounding/multiple-answer instructions cannot be converted to attempt-all or exact integers."

### "Confirm printed examination rules" issue
- **0 mocks** carry an issue starting "Confirm printed examination rules" — across every one of the four books AND the entire tejas_book_mocks collection.

### Sample held mocks (2 per book with issues)
Chemistry (69f7ecde):
- `5b8bbfd0` — chapter "08 Solutions". rules present=YES; rules.expected_questions=1; rules.note="Default time and marks of this mock type; the PDF prints none."; questions (cut_summary.total)=1; pages.question len=1, pages.key len=0, pages.solution len=49 (plus instructions len=17). First 5 issues: ["Page 476: Q1: confirm response type, options and continuation.", "Questions Q1: missing or conflicting supplied key.", "Questions Q1: response type is unresolved.", "Questions Q1: original solution expected but not captured; attach its regions.", "Questions Q1: original key region required."]
- `354fbcfc` — chapter "09 Chemical Equilibrium". rules present=YES; expected_questions=50; note=same; questions=50; pages.question len=50, pages.key len=0, pages.solution len=0 (instructions len=19). First 5 issues: ["Questions Q1: missing or conflicting supplied key.", "Questions Q1: incomplete options or key does not match printed labels.", "Questions Q1: original solution expected but not captured; attach its regions.", "Questions Q1: original key region required.", "Questions Q2: missing or conflicting supplied key."]

Logical Reasoning (9983c518):
- `984ee5aa` — chapter "01 Analogy". rules present=YES; expected_questions=50; note=same; questions=50; pages.question len=50, pages.key len=0, pages.solution len=10 (instructions len=2). First 5 issues: ["Questions Q1: ambiguous worked-solution start/continuations.", "Questions Q1: missing or conflicting supplied key.", "Questions Q1: incomplete options or key does not match printed labels.", "Questions Q2: ambiguous worked-solution start/continuations.", "Questions Q2: missing or conflicting supplied key."]
- `a3fc965b` — chapter "02 Classification (Odd One Out)". rules present=YES; expected_questions=50; note=same; questions=50; pages.question len=50, pages.key len=0, pages.solution len=10 (instructions len=2). First 5 issues: same five-pattern opening as above.

### Other non-removed, non-archived books of this owner (id prefix, title, state)
- 3a704ed9 — "physics chapterwise" — published (reader_version 6)
- 4e23420a — "mathematics chapterwise" — published (reader_version 6)
- e38ad688 — "chemistry chapterwise" — published (reader_version **5**)
(Owner also has 1 archived book: eed94a04 "Chemistry chapter-wise (boxed) — engine test", state=failed, archived=true — excluded.)

### Stuck books & book_step jobs
- Books in state received/reading/matching older than 15 min: **NONE** (0 books in those states collection-wide). The four audit books are ready/attention_needed with reading complete.
- Open/queued/failed book_step jobs for the four audit books: **NONE** (0). (tejas_jobs has only statuses done/failed; no queued/running/open exist at all.)

## 3) STORAGE
- Backend logs, last 24h (log tool caps lookback at 1440 min / 24h; 24–48h window not readable beyond that):
  - "Private storage unavailable": **0**
  - "StorageError": **0**
  - "storage" lines with HTTP 500: **0**
  - Only storage-related lines are `GET /api/admin/storage/health` → 200 (×26) and 401 (×2, unauthenticated probes). Most recent such line is a 200 OK on /api/admin/storage/health (no error line exists to report a time for).
- Secrets present (names only): **SUPABASE_URL = present (non-empty)**, **SUPABASE_SECRET_KEY = present (non-empty)**.
- tejas_files: path starts "sb://" = **22377**; not "sb://" = **716** (total 23093).
- Mocks whose issues/publish_hold mention storage/sb/supabase/upload: **0**.

## 4) SCHEDULED WORK
- tejas_operations {id:'maintenance'} (doc _id 6ada57d8...): last_run ≈ **just ran (<1 min ago)**; counters expired=0, graded=0, outbox_checked=0, recovered_jobs=0.
- POST /api/cron/maintenance in last 24h: **17 calls, all HTTP 200** (no non-200).
- tejas_jobs by (kind,status): statuses present are only done/failed. **queued=0, running=0** (none exist) → oldest-queued age = N/A. **failed=7, all kind=book_step** (cohort/grade have 0 failed). Failed jobs (all attempts=3):
  - e38ad688:64 — "Worker recovery budget exhausted. Saved data is safe; retry after resolving the cause." (oldest, ~15.3h ago)
  - 3a704ed9:70, 3a704ed9:72 — "Processing could not finish. Your originals and saved answers are safe. Retry after the cause is resolved."
  - 4e23420a:72, :73, :74, :75 — same "Processing could not finish…" text.
  - NB: none of these 7 belong to the four audit books; they're on the published physics/math/old-chemistry books.
- tejas_operations {id:'integrity'} (doc _id 6af89392...): report.needs_attention = **0**; last_run 1795293272.9 → **~17.5 h ago** (trigger nightly); all 20 checks state=ok, found/fixed/left=0, no index_problems, no missing_safeguards.

## 5) SIZE (counts only)
- tejas_phone_profiles: **6**
- tejas_users by role: **owner = 1** (only role present; total 1)
- tejas_sets by status: **published = 119** (only status present)
- tejas_books by state: attention_needed **3**, failed **1**, published **3**, ready **1** (total 8)
- tejas_book_mocks by state: held **44**, published **89**, ready **72** (total 205)
- tejas_attempts by status: **completed = 12** (only status present)
- tejas_audits total: **8667**
- tejas_sessions total: **82**
- Failed index-build lines in startup logs ("was not built"): **0 found** (within readable 24h window).

## 6) HEALTH
- Live URL probe https://campus-search-debug.emergent.host/ → **200**, 507 ms, serves real JEELIVE.AI app (title "JEELIVE.AI — 100% Free Exam Practice").
- Pods (current serving run): **2 replicas, both Running + Ready, restart_count=0, no OOMKilled, no kills** (kill_findings empty; started 2026-11-22T09:50:58Z). Note: pod-event history is readable ~24h and only for the current run's pods; prior runs' pods no longer exist, so a full 48h cross-run OOM history is not available — but current pods show zero restarts/OOM.
- 5xx responses in last 24h grouped by path: **0** (no 5xx lines at all).
- Distinct tracebacks in last 24h: **1** — first line "Traceback (most recent call last):" resolving to `fastapi.exceptions.HTTPException: 409: This book changed or is processing a batch. Reload and retry; saved work is retained.` This is a benign 409 concurrency guard, not a 5xx/crash.

## BOTTOM LINE (answers the stated concern)
- Production does **NOT** run reader v7 — it serves **v6** (and cutter v3). The v7 source exists only in preview.
- All four books finished re-reading under v6 (read_pages == pages). AITS is effectively clean under v6 (blocking_issues 0 and 1). The two **BITSAT chapter-wise** books are still blocked because v7 (their fix) isn't deployed: Logical Reasoning blocking_issues = **3532** (18 held mocks), Chemistry = **4905** (25 held mocks; 7 published). Current fix counts will not drop for these two until v7 is deployed and the books are re-read.
