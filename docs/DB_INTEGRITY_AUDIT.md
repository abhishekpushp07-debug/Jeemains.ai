# JEELIVE.AI database integrity audit (read-only)

Date: 2026-11-17. Database: MongoDB (one database, `tejas_*` collections). Nothing was changed, repaired or migrated. No personal data appears here.

Evidence used:
- **Code:** every write path traced in `backend/tejas/*.py`.
- **Isolated copy:** one sign-up burst on a throwaway database, measured.
- **Production:** read-only counts requested from the deployer. The production section below is filled in when those counts arrive. Until then, every production item is marked **PENDING**.

## 1. Structure and relationships

MongoDB has no foreign keys. Links between collections are kept by the code and checked every night by `integrity.py` (19 checks, counts only).

| Area | Collection | Identity / unique rules (from `db.py`) | Points to |
|---|---|---|---|
| Students | `tejas_phone_profiles` | `id` unique, `phone` unique (E.164 after `normalize_phone`) | — |
| Staff | `tejas_users` | `id` unique, `email` unique | — |
| Sign-in | `tejas_sessions` | `id` unique, TTL on `expires_at` | `user_id` → profile or staff |
| Tests | `tejas_sets` | `id` unique, `(series_id, series_date)` unique when a day is set | `book_import_id`, `chapter_book_id` |
| Question packs | `tejas_packs` | content-addressed `_id` (shared by many attempts) | — |
| Attempts | `tejas_attempts` | `id` unique; `(user_id, start_key)` unique; `(user_id, start_request_keys)` unique; one **active** per `(user_id, set_id, mode)` | `user_id`, `set_id`, `pack_id`, `parent_attempt` |
| Frozen score | `tejas_ledgers` | `id` unique (= attempt id) | attempt |
| Score corrections | `tejas_score_versions` | `id` unique | attempt, pack |
| Peer comparison | `tejas_cohort_entries` | `(cohort_id, user_id)` unique | attempt, cohort |
| Saved / preflight | `tejas_saved_tests`, `tejas_preflight` | `(user_id, set_id)` unique | user, set |
| Reports / reviews | `tejas_question_reports`, `tejas_reviews` | indexes only, not unique | attempt, set |
| Background work | `tejas_jobs` | `id` unique, built from the work key (`grade-<attempt>`), so the same work cannot be queued twice | attempt / set |
| Book pipeline | `tejas_books` → `tejas_book_parts` / `tejas_book_pages` (unique `(book_id, number)`) / `tejas_book_mocks` | mocks `(book_id, order)` **not unique** | book, set |
| Limits | `tejas_phone_limits`, `tejas_login_limits`, `tejas_ai_limits` | TTL on `expires_at` | — |

How a mock test writes data:
1. **Sign in:** a session row is created.
2. **Start:** one attempt row. A live exam uses a fixed attempt id per exam and student, so a second start returns the same attempt.
3. **Answer saves:** one compare-and-set update per answer. It checks the answer revision, a receipt per request id, and the deadline in database time.
4. **Submit:** one compare-and-set that turns the attempt from active to completed, with `grading_status = queued` as an outbox.
5. **Grade job:** writes the frozen ledger once (`$setOnInsert`), then copies the summary onto the attempt.
6. **Peer entry:** upserted after grading.

**No multi-document transactions are used anywhere** (0 uses of `start_session` / `with_transaction`). Safety comes from:
- single-document compare-and-set updates
- idempotent upserts
- unique indexes
- the outbox plus the nightly repair

## 2. Confirmed problems (with evidence)

### C1 — Sign-in and sign-up are turned away under a rush (HIGH)
- **What goes wrong:** 20 students signing up in the same second on one server: 16 got `503 This service is busy`.
  - Measured on an isolated copy on 2026-11-17 with `tools/load_live.py`.
  - The Login, Sign-up and Forgot PIN screens show that message and stop. The student must tap again. Only answer saves and report polling retry by themselves (`useAttempt.js`, `ReportButton.js`).
- **Why:** the admission gate lets only **4 sign-in requests at a time per server** (`runtime.py INFLIGHT_LIMITS auth=4`). Each one does a bcrypt PIN check.
- **Impact:** on exam morning a large share of students and app users see "busy" on the first tap.
- **Fix:**
  - Retry automatically on 503/429 on the three auth screens, honouring `Retry-After` with jitter (website), and tell the app agent to do the same.
  - Raise `TEJAS_INFLIGHT_AUTH` once the servers have more CPU.
- **Test:** a burst of 50 parallel sign-ups must end with 50 signed-in students and no error shown on screen.

### C2 — Staff practice attempts are counted in students' peer rank and percentile (MEDIUM, production count PENDING)
- **What goes wrong:** when the owner or a reviewer takes a test in practice mode, their score enters the "compared with N students" statistics. This shifts student rank and percentile, and staff often score full marks while checking keys.
- **Why:** `cohorts.record()` filters on `mode == 'practice'` only. It never checks whether the attempt belongs to a student (`competition_ranked` does check, line 295 of `attempts.py`).
- **Fix:**
  - Skip staff in `record()`.
  - One-time clean-up: delete cohort entries whose `user_id` is a `tejas_users` id, and mark those cohorts dirty so they rebuild.
- **Test:** an owner practice attempt never creates a cohort entry, and a student's rank is unchanged by it.

### C3 — A deploy can take the whole site down if one index cannot be built (MEDIUM)
- **What goes wrong:** the server builds about 70 indexes on every start (`server.py lifespan → indexes()`). If a unique index meets duplicate data, or an index is redefined with different options, `create_index` raises, startup fails, and every server stays down.
- **Why:** index creation is a hard part of startup, not a separate migration step.
- **Fix:**
  - Build each index inside try/except, log it and report it in the nightly check, and only stop startup for the few indexes that protect money-like data (attempt identity, ledger).
  - Before adding a new unique index, check the data for duplicates first.
- **Test:** start the app against a copy that holds one duplicate and confirm the API still starts and reports the index problem.

### C4 — Steps that can half-finish (LOW)

| Operation | Steps | If it stops midway | Self-heals? |
|---|---|---|---|
| Library permanent delete (`library.delete_sets`) | flag attempts → delete saved/solutions/versions → flag mocks → delete tests → drop sources | tests still archived, some saved rows gone | Yes: running Delete again finishes it |
| Series settings change (`series_admin.update_config`) | loops over tests and mocks, test update **without revision check** (line 305) | a paper assigned at the same moment can be overwritten | No: owner re-checks the calendar |
| Grading | ledger frozen → summary on attempt | attempt shows "scoring" | Yes: nightly `waiting_for_score` repair |
| PIN change | new hash → new session → old sessions deleted | old sessions remain but are refused (`pin_version` fence) | Yes |

**Fix for the series one:** add the same `revision` compare-and-set that `assign_written` already uses.

### C5 — Two clocks (LOW)
- **What goes wrong:** some times may be off from each other by however far a server clock drifts from the database clock.
- **Why:**
  - **Database time:** start, submit, deadline and answer saves.
  - **Server time:** `time.time()` is used for retry `started_at`, `created_at` on profiles, audits, the live paper guard and cohort `updated_at`.
- **Impact:** small drift can make "submitted before start" or the live paper guard off by that drift.
- **Fix:** use database time (`EPOCH_NOW` / `clocked_one`) for retry start and the live paper guard.

### C6 — Student rows carry two different ids (LOW)
- **What:** sign-up stores `_id = uuid()` and `id = uuid()` as two different values (`phone.py` line 100).
- **Impact:** none today, because every reader uses `id`. Any future tool that reads `_id` gets a different id.
- **Fix:** set `_id = id` for new rows. Old rows are fine.

### C7 — Some student data can never be removed (LOW, by design today)
- **What:** there is no way to delete a student account and its attempts, except the private operator script `tools/reset_student_data.py`.
- **Now in preview (not live):** an owner-only removal for test accounts, `POST /api/admin/qa/test-accounts/remove`.
  - It only touches numbers with a given test prefix that signed up after a given time.
  - It does a dry run first and needs a typed confirmation.

## 3. Checked and found safe (code evidence)

- **Two starts of the same test at once:** the unique "one active per student and test" index, plus a fixed id for live exams. The loser reads the winner's attempt.
- **Two saves of the same answer at once:** revision compare-and-set and a receipt per request id. A repeated save returns the first receipt. A changed body with the same id is refused (409).
- **Saves after time is up:** refused using database time, with no grace on the server.
- **Two submits at once:** `active → completed` compare-and-set. The second one reads the sealed attempt.
- **Two grade jobs at once:** the job id is unique per attempt, the worker holds a lease, and the ledger is written only once (`$setOnInsert`).
- **One student counted twice in peer stats:** `(cohort_id, user_id)` unique, with the earliest attempt kept.
- **Two accounts on one number:** unique `phone` after normalising. Sign-up handles the duplicate-key race (409).
- **Wrong-PIN counters under parallel tries:** the slot is reserved before the PIN check and given back after success. Counters use an atomic upsert and expire by TTL.
- **Rules enforced only in the browser:** none found for exams. Answer type and options, bonus section lock, deadline, the PIN format and the live paper guard are all checked on the server.
- **Money:** no payments or balances exist. Scores are stored exactly as fraction strings (`score_exact`), with a float copy only for sorting.
- **Soft delete:**
  - tests: Library (`archived`), then a typed permanent delete that keeps score lines (`set_deleted`)
  - book mocks: flagged `deleted`
  - ledgers: never deleted

## 4. Production numbers — PENDING

These counts were requested read-only and are not in yet:
- duplicates, orphans and stuck jobs
- timestamp types
- index list compared with the code
- unused collections and sizes

This section is filled in when they arrive. Until then nothing here is claimed about live data.

## 5. Fix order (after approval, one deploy)

| # | Fix | Safe migration |
|---|---|---|
| 1 | C1 auto-retry on sign-in screens; app told the same | code only |
| 2 | C2 staff out of peer stats | code + one-time delete of staff cohort entries, dirty flag; dry-run count first |
| 3 | C3 index build cannot block startup | code only |
| 4 | C4 series revision check | code only |
| 5 | C5 database time for retry/guard | code only |
| 6 | C6 `_id = id` for new students | code only, old rows untouched |

## 6. Tests to keep these from coming back

- Burst sign-up and sign-in (50 parallel): all end signed in. First-try 503s are counted and shown.
- Two parallel starts, saves and submits on one attempt: one attempt, one ledger, receipts identical.
- Staff practice attempt: no cohort entry.
- Startup with one duplicate row: the API starts and the index problem is reported.
- Series settings change while assigning: no lost assignment.
- Nightly integrity check: every count is 0 after the load test and after clean-up.
