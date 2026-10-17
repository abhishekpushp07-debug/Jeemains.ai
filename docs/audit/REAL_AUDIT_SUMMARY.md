# Real Backend Audit Test Results

## Executive Summary

Completed comprehensive audit testing using **REAL application functions** with isolated temporary collections. Successfully confirmed **4 out of 6** critical vulnerabilities through actual function calls, not simulations.

**Test Approach:**
- Created ONE pytest suite: `/app/docs/audit/tests/test_real_backend_audit.py`
- Used `unittest.mock.patch` to bind collections to UUID-suffixed temp MongoDB collections
- Called EXACT application functions (attempts.retry, content.publish, content.edit_question, etc.)
- No main DB mutations, no server imports/startup, no live publish, no env changes
- Restored in finally and dropped ONLY own collections

**Previous Tests Superseded:**
- `/app/docs/audit/tests/a01_retry_idempotency.py` - INVALID (simulated logic, never called retry())
- `/app/docs/audit/tests/a02_concurrent_publication.py` - INVALID (copied logic, added $inc revision not in app)
- `/app/docs/audit/tests/a03_lost_updates.py` - INVALID (copied logic)
- `/app/docs/audit/tests/a04_audience_fails_open.py` - PARTIAL (tested permitted() but not full flow)
- `/app/docs/audit/tests/a05_lane_overflow.py` - INVALID (copied lane check logic)
- `/app/docs/audit/tests/a06_extraction_fencing.py` - INVALID (copied logic)

---

## Test Results

### ✓ A01: Retry Idempotency Violation - CONFIRMED

**Location:** `attempts.py` lines 411-415

**Test Method:**
1. Called REAL `attempts.retry(parent_id, {start_key: K1}, user)` → Created R1
2. Called REAL `attempts.retry(parent_id, {start_key: K2}, user)` WHILE R1 ACTIVE → Returned R1 (correct)
3. Completed R1 in temp collection
4. Called REAL `attempts.retry(parent_id, {start_key: K2}, user)` AFTER R1 COMPLETE → Created R2 (BUG)

**Expected:** K2 should return R1 (idempotency preserved)
**Actual:** K2 created NEW retry R2 (idempotency violation)

**Root Cause:**
- Lines 411-415 return existing ID without calling `bind_start_alias`
- After completion, new start_key creates duplicate retry
- K2 was NEVER bound to R1, so after completion it's treated as new request

**Impact:** Users can create multiple retry attempts for same parent, violating idempotency guarantee

**Evidence:**
```
✓ K1 created R1: 5d00c2e6-1251-48b4-a94f-45ce346ec57e
✓ K2 while active returned R1: 5d00c2e6-1251-48b4-a94f-45ce346ec57e
✓ R1 completed
✓ K2 after complete created R2: 86af99c7-6700-468d-bc02-991e4f1c0200
✓ K2 NOT bound to R1 (confirms bug)
```

---

### ✓ A02: Concurrent Publication Race - CONFIRMED

**Location:** `content.py` lines 612-623

**Test Method:**
1. Created draft set at revision 5
2. Launched 2 concurrent calls to REAL `content.publish(set_id, {confirm: true}, user)`
3. Both calls completed successfully
4. Checked version rows and final set state

**Expected:** One publish succeeds, one fails with 409 (revision guard)
**Actual:** BOTH publishes succeeded, creating 2 version rows with same version number

**Root Cause:**
- Line 612-614: `insert_one()` to tejas_versions BEFORE CAS
- Lines 615-623: CAS with revision guard
- Both threads insert version rows before either CAS completes
- Revision guard at line 616 failed to prevent race (both read same revision)

**Impact:** Database contains duplicate version rows, revision guard ineffective

**Evidence:**
```
✓ Both publish() calls completed
  Result 1: {'ok': True, 'version': 1}
  Result 2: {'ok': True, 'version': 1}
✓ Version rows created: 2
✓ Final set version: 1
✓ BUG CONFIRMED: Both publishes succeeded (revision guard failed)
```

**Note:** Previous test incorrectly added `$inc revision` in version insert. Actual code does NOT increment revision there.

---

### ✓ A03: Lost Updates in Concurrent Editing - CONFIRMED

**Location:** `content.py` lines 473-516

**Test Method:**
1. Created set with question at revision 10
2. Launched 2 concurrent calls to REAL `content.edit_question()`:
   - Editor 1: Changed `text` field
   - Editor 2: Changed `topic` field
3. Both calls completed successfully
4. Checked final question state

**Expected:** Both changes preserved OR one edit fails with 409
**Actual:** Editor 1's text change LOST, only Editor 2's topic change persisted

**Root Cause:**
- Line 473: Read full set (no revision guard on read)
- Lines 498-511: Merge changes into old question object
- Lines 514-516: Update with `$inc revision` but no revision guard on read
- Last-write-wins: Editor 2 overwrites Editor 1's changes

**Impact:** Editor changes silently lost when multiple editors work on same question

**Evidence:**
```
✓ Editor 1 changed text
✓ Editor 2 changed topic
✓ Final text: 'Original question text' (LOST Editor 1's change)
✓ Final topic: 'Editor 2 changed the topic' (Has Editor 2's change)
```

---

### ✓ A04: Unknown Audience Fails Open - CONFIRMED

**Location:** `content.py` lines 29 (SetInput), 84-98 (permitted)

**Test Method:**
1. Tested REAL `permitted()` function with `audience='private-typo'` → Returned True
2. Tested REAL `SetInput` validation with `audience='private-typo'` → Accepted
3. Called REAL `content.create_set()` with invalid audience → Succeeded
4. Verified set persisted with invalid audience

**Expected:** Validation rejects unknown audience, permitted() fails closed
**Actual:** Unknown audience passes validation, permitted() returns True (fails open)

**Root Cause:**
- Line 29: `SetInput.audience` is plain `str`, not enum/Literal
- Lines 84-98: `permitted()` only checks `audience == 'restricted'`
- Line 98: Returns True for ALL other cases (fails open)
- No validation in create_set or update_set

**Impact:** Invalid audience values pass validation and permit unauthorized access

**Evidence:**
```
✓ audience='private-typo': permitted() = True
✓ SetInput accepted audience='private-typo'
✓ create_set() succeeded with invalid audience
✓ Set persisted with audience='private-typo'
```

---

### ✗ A05: Lane Overflow No Drain - NOT REPRODUCED

**Location:** `jobs.py` lines 59-60

**Test Method:**
1. Attempted to call REAL `jobs.run_job()` to fill grade lane (limit=2)
2. Created 2 grade jobs and ran them
3. Created overflow job and attempted to run

**Expected:** Lane fills, overflow job queued, no auto-retry after capacity frees
**Actual:** Jobs completed too fast, lane never filled

**Issue:** Test requires long-running jobs to demonstrate overflow. Mock jobs complete instantly, preventing race condition reproduction.

**Note:** Bug is real (confirmed by code review), but requires blocking operations to reproduce in test.

---

### ✗ A06: Extraction Destination Fencing Gap - NOT REPRODUCED

**Location:** `jobs.py` lines 89-91

**Test Method:**
1. Attempted to call REAL `jobs.run_job()` for extraction
2. Tried to inject lease replacement between `require_lease()` and destination write
3. Job completed successfully

**Expected:** Stale worker writes to destination despite lease replacement
**Actual:** Job completed too fast, race condition not reproduced

**Issue:** Test requires precise timing to inject lease replacement between require_lease() check and sets.update_one() call. Race window too small to reproduce reliably.

**Note:** Bug is real (confirmed by code review), but requires controlled timing to reproduce in test.

---

## Test Execution Details

**Test Suite:** `/app/docs/audit/tests/test_real_backend_audit.py`

**Isolation Strategy:**
- Temp collections with UUID suffix: `audit_attempts_ebe25243`, `audit_sets_ebe25243`, etc.
- Patched module-level collections using `unittest.mock.patch`
- Mocked side-effect functions: `audit()`, `seal_profile()`, `validate_refs()`, `freeze_ledger()`
- Restored originals in finally block
- Dropped ONLY temp collections (no main DB mutations)

**Functions Called (REAL, not simulated):**
- `tejas.attempts.retry()` - A01
- `tejas.content.publish()` - A02
- `tejas.content.edit_question()` - A03
- `tejas.content.create_set()` - A04
- `tejas.content.permitted()` - A04
- `tejas.jobs.run_job()` - A05, A06 (attempted)

**Mocking Strategy:**
- Collections: Patched to temp collections
- Audit: No-op (AsyncMock)
- Seal profile: No-op (AsyncMock)
- Validate refs: No-op (AsyncMock)
- Freeze ledger: Returns synthetic ledger (AsyncMock)
- Build questions: Returns synthetic questions (AsyncMock)

**No Mocking (Real Code Executed):**
- Retry idempotency logic
- Publish CAS logic
- Edit question merge logic
- Permitted() access control logic
- Job lane overflow logic
- Extraction lease logic

---

## Comparison with Previous Tests

| Test | Previous Approach | New Approach | Result |
|------|------------------|--------------|--------|
| A01 | Simulated DB queries, NEVER called retry() | Called REAL retry() 3 times | ✓ CONFIRMED |
| A02 | Copied publish logic, added $inc revision | Called REAL publish() concurrently | ✓ CONFIRMED |
| A03 | Copied edit logic | Called REAL edit_question() concurrently | ✓ CONFIRMED |
| A04 | Tested permitted() only | Called REAL create_set() + permitted() | ✓ CONFIRMED |
| A05 | Copied lane check logic | Called REAL run_job() | ✗ NOT REPRODUCED |
| A06 | Copied extraction logic | Called REAL run_job() with injection | ✗ NOT REPRODUCED |

**Key Improvements:**
- A01: Previous test NEVER called retry() while active - invalid proof
- A02: Previous test added $inc revision not in actual code - invalid simulation
- A03: Previous test copied merge logic - now uses real function
- A04: Previous test only checked permitted() - now tests full flow
- A05: Previous test simulated lane tracking - now uses real _active dict
- A06: Previous test simulated lease check - now uses real require_lease()

---

## Recommendations

### Immediate Actions (Main Agent)

1. **A01 - Retry Idempotency:**
   - Add `bind_start_alias()` call at line 415 before returning existing ID
   - Ensure K2 is bound to R1 even when returning early

2. **A02 - Concurrent Publication:**
   - Move version insert AFTER successful CAS
   - OR use transaction to make insert+CAS atomic
   - OR add unique constraint on (set_id, version)

3. **A03 - Lost Updates:**
   - Add revision guard on read: `{"id": id, "revision": s["revision"]}`
   - Use CAS pattern: read revision, update with revision guard
   - OR use field-level updates instead of full document replacement

4. **A04 - Audience Fails Open:**
   - Change SetInput.audience to `Literal["all", "restricted"]`
   - Change permitted() to fail closed: `return s.get("audience") == "all"`
   - Add validation in create_set and update_set

### Future Testing

5. **A05 - Lane Overflow:**
   - Requires blocking job execution to demonstrate overflow
   - Consider integration test with actual long-running jobs
   - OR mock job execution to block until signal

6. **A06 - Extraction Fencing:**
   - Requires precise timing control
   - Consider using asyncio.Event to control execution order
   - OR add lease guard to destination write: `{"id": set_id, "revision": r, "lease": j["lease"]}`

---

## Conclusion

Successfully created and executed real backend audit tests using actual application functions. **4 out of 6 critical vulnerabilities confirmed** through proper function calls with isolated temp collections.

**Previous audit tests (a01-a06.py) are INVALID** and superseded by `test_real_backend_audit.py`.

**No fixes applied** - this is audit only. Main agent should review findings and implement fixes.

**Test artifacts:**
- Test suite: `/app/docs/audit/tests/test_real_backend_audit.py`
- Test report: `/app/test_reports/iteration_25_real_audit.json`
- This summary: `/app/docs/audit/REAL_AUDIT_SUMMARY.md`
