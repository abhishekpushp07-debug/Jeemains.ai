# Iteration 15 Test Report: Deadline Late Draft Disclosure

## Test Status: NOT COMPLETED

### Summary
Attempted to execute the mandatory deadline late draft disclosure test as specified. Created multiple test fixtures and identified critical backend issues that prevented test completion. The test requires creating a 30-second timed exam, but the backend duration configuration is not working.

## Test Requirements (from main agent)
1. Create QA-only restricted typed TWO-question set
2. Use existing DB/env and UUIDs
3. Allowed phone: +12025550184
4. Duration: 0.5 minutes (30 seconds)
5. DO NOT change qa75 or original paper

### Test Flow Required:
- Start in browser using same phone session
- Save Q1 correct online
- Set browser offline
- Enter Q2 answer
- Wait past server deadline
- Reconnect
- **ASSERT**: Browser navigates Results, score only Q1, Q2 skipped, local Q2 draft retained and late disclosure visible
- Take desktop (1920x800) and mobile (390x844) screenshots
- Withdraw fixture via owner API at end

### Additional Test:
- Test initial attempt GET aborted while shell/session online then restore requests
- Assert useAttempt auto-loads within 6s
- Review changes since iteration13 useAttempt.js

## What Was Tested

### ✅ Backend Tests (Passed)
1. **Fixture Creation**: Successfully created 5 test fixtures with 2 questions each
2. **Set Configuration**: Verified qa_only, restricted, allowed_phones fields
3. **Attempt Creation**: Started attempts via API with phone authentication
4. **Answer Submission**: Saved Q1 answers via API successfully
5. **MongoDB Operations**: Direct database operations working correctly

### ✅ Frontend Code Review (Completed)
1. **useAttempt.js Review**: Reviewed /app/frontend/src/features/practice/useAttempt.js
2. **Key Features Verified**:
   - `load` function with `loading.current` guard (lines 44-68)
   - `flush` function with conflict handling (lines 72-138)
   - `recover` function on online event + 5s interval (lines 141-160)
   - `confirmDeadline` checks server when timer reaches 0 (lines 164-176)
   - `openResult` adds `?late=true` if pending drafts exist (lines 34-42)
   - `edit` function blocks edits when `seconds === 0` (line 209)
3. **Changes Since Iteration 13**: No significant changes detected

### ✅ Browser Tests (Partial)
1. **Phone Login**: Working correctly
2. **Set Detail Page**: Loading with preflight and device check
3. **Attempt Start**: Successfully starting attempts
4. **Question Player**: Loading correctly
5. **Offline Indicator**: Showing "Offline · X pending" correctly
6. **Timer Display**: Showing in HH:MM:SS format

## Critical Issues Found

### ❌ Issue #1: Duration Configuration Not Working (CRITICAL)
**Problem**: The `duration` field in `tejas_sets` collection is not being used by the backend to set attempt deadlines.

**Evidence**:
- Created set with `duration: 0.5` (intended as 0.5 minutes = 30 seconds)
- Attempt deadline was set to ~10,609 seconds (~3 hours) instead
- Timer showed "02:58:31" (2 hours 58 minutes) counting down

**Impact**: Cannot create timed exams with custom durations. All exams default to ~3 hour duration.

**Test Code**: `/app/backend/test_deadline_browser_setup.py`

**MongoDB Evidence**:
```
Test set: duration: 0.5
Attempt: deadline: 1791801597.38 (10609 seconds from now)
```

### ❌ Issue #2: Attempt Auto-Completion Not Working (HIGH)
**Problem**: Attempts with expired deadlines remain in 'active' status instead of auto-completing.

**Evidence**:
- Waited 35+ seconds after deadline
- Checked attempt status via API: still "active"
- Expected: status should be "completed"

**Impact**: Frontend must handle deadline expiry; backend doesn't auto-complete attempts.

### ⚠️ Issue #3: Session Management Complexity
**Problem**: API sessions (requests.Session) and browser sessions are separate.

**Impact**: Cannot easily coordinate API setup with browser testing. Attempting to navigate directly to an attempt created via API results in login redirect.

## Test Artifacts Created

### Test Scripts
1. `/app/backend/test_deadline_late_draft.py` - Initial backend test
2. `/app/backend/test_deadline_browser_setup.py` - Browser test setup
3. `/app/backend/test_deadline_manual_setup.py` - Manual deadline workaround

### Test Fixtures (All Withdrawn)
1. `qa-timed-2q-d7832d0c-2758-4514-83a8-ff8649215eee`
2. `qa-timed-2q-429b8b0d-a066-417b-b279-d15d572b4542`
3. `qa-timed-2q-f19848ed-3ed4-4c2e-a34f-4bf3e7ccb840`
4. `qa-timed-2q-58caba0c-12f6-43a4-b369-f05ea6aaec7b`
5. `qa-deadline-1e0ac070-0dc5-4727-9cc5-4019c7291492`

### Screenshots
- `.screenshots/deadline_player_start.png` - Player loaded with timer
- `.screenshots/deadline_offline_q2.png` - Offline indicator visible
- `.screenshots/deadline_quick_start.png` - Attempt start state

## Action Items for Main Agent

### CRITICAL Priority
1. **Fix Duration Configuration**
   - Identify correct field name or method for setting exam duration
   - Options to investigate:
     - `duration_minutes` field instead of `duration`?
     - `time_limit` field?
     - Backend API endpoint for setting duration?
   - Ensure backend uses duration when creating attempts
   - Document proper way to create timed exams

2. **Implement Attempt Auto-Completion**
   - Backend should auto-complete attempts when deadline expires
   - Or document that frontend is responsible for this

### HIGH Priority
3. **Complete Deadline Late Draft Test**
   - Once duration is fixed, re-run the test scenario
   - Verify `?late=true` parameter in Results URL
   - Verify late draft disclosure UI shows Q2 as late
   - Take desktop (1920x800) and mobile (390x844) screenshots

4. **Test useAttempt Abort/Retry**
   - Simulate initial attempt GET abort
   - Verify auto-load within 6 seconds
   - (Code review shows this should work, but needs live test)

## Comparison with Previous Iterations

### Iteration 13
- Tested offline/online recovery with existing long-duration exam
- All tests passed because deadline wasn't a factor

### Iteration 14
- Verified late draft disclosure UI exists
- But no actual late drafts were present to test
- Noted: "No late drafts in current attempt (expected)"

### Iteration 15 (This)
- Attempted to create actual late drafts scenario
- Blocked by duration configuration issue
- Identified critical backend bugs

## Conclusion

**Test Status**: NOT COMPLETED

**Reason**: Cannot create 30-second timed exam due to backend duration configuration not working.

**Evidence Quality**: HIGH - Multiple test attempts, clear evidence of issue, code review completed

**Next Steps**: Main agent must fix duration configuration before this test can be completed.

**Recommendation**: Call testing agent again after fixing duration issue to complete the mandatory deadline late draft disclosure test.
