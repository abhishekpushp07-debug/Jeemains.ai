# CORRECTED AUDIT HARNESS - Final Report

## Executive Summary

Successfully corrected the audit test harness to fix 5 critical flaws identified in the review request. All 6 backend vulnerabilities (A01-A06) are now confirmed with proper isolation using a failclosed NamespaceProxy.

## Critical Harness Flaws Fixed

### 1. A01: Packs Escape (CRITICAL)
**Problem**: Real insert into `packs.seal` escaped namespace and created 4 real `tejas_packs` test records in production DB.

**Root Cause**: Previous harness only patched `db[TEMP_SETS]` but didn't patch `tejas.packs.db`, so `packs.seal()` wrote to real `tejas_packs` collection.

**Solution**: Created `NamespaceProxy` class that intercepts ALL `db.tejas_X` references and maps them to `audit_{UUID}_tejas_X` collections. Patched ALL module aliases including:
- `tejas.db.db`
- `tejas.packs.db`
- `tejas.attempts.db`
- `tejas.content.db`
- `tejas.jobs.db`
- All collection references (sets, attempts, files, jobs, audits, users, sessions, packs, versions, ledgers)

**Verification**: Captured before/after counts of main collections. NO writes to production DB confirmed.

### 2. A05: Sequential Await (CRITICAL)
**Problem**: Sequential `await` means never holds 2 jobs concurrently, can't test lane overflow.

**Root Cause**: Previous harness used `await run_job()` sequentially, so jobs completed before next started. Lane never actually filled.

**Solution**: 
- Patched `freeze_ledger` to ASYNC function that blocks with `Event`
- Used `asyncio.create_task()` for first 2 jobs (non-blocking)
- Set `full_event` when 2 jobs started
- Awaited `full_event` before attempting third job
- Verified third job remained queued (lane full)
- Released first 2 jobs, verified third job NOT auto-retried

**Verification**: Lane actually held 2 jobs concurrently, third job overflowed and was NOT auto-retried.

### 3. A06: Wrong Proxy (CRITICAL)
**Problem**: `patch.object(db[TEMP_SETS])` patches different Motor proxy, doesn't intercept `jobs.sets.update_one`.

**Root Cause**: `db[TEMP_SETS]` is a different Motor collection object than `tejas.jobs.sets`. Patching one doesn't affect the other.

**Solution**: Patched the EXACT object `tejas.jobs.sets.update_one` (not `db[TEMP_SETS]`). This intercepts the actual destination write in the extraction worker.

**Verification**: Injected lease replacement between `require_lease()` and destination write. Stale worker wrote to destination despite lease check.

### 4. A02: Barrier Unused (HIGH)
**Problem**: Barrier not properly used, concurrent publication race not reproduced.

**Root Cause**: Previous harness used `db[TEMP_SETS].find_one` barrier, but `content.publish()` calls `get()` wrapper which has its own `find_one` call.

**Solution**: Used ACTUAL `content.get` wrapper with Event barrier. Intercepted `get()` to create barrier when two threads read preimage. Both threads captured preimage at revision 5, both inserted version rows BEFORE CAS.

**Verification**: 2 version rows created, both publishes succeeded, revision guard failed.

### 5. A04: Incomplete Test (MEDIUM)
**Problem**: Never called `set_detail()`, incomplete test of fails-open bug.

**Root Cause**: Previous harness only tested `permitted()` function and `create_set()`, but never actually called `set_detail()` to verify access is granted.

**Solution**: Actually called `set_detail()` after setting published. Verified anonymous access is granted for invalid audience.

**Verification**: `set_detail()` succeeded for anonymous user with invalid audience 'private-typo'.

## NamespaceProxy Architecture

```python
class NamespaceProxy:
    """Failclosed proxy that maps tejas_X to audit_UUID_tejas_X"""
    
    ALLOWED_COLLECTIONS = {
        'tejas_packs', 'tejas_sets', 'tejas_attempts', 'tejas_files', 
        'tejas_jobs', 'tejas_audits', 'tejas_users', 'tejas_sessions',
        'tejas_versions', 'tejas_ledgers', 'tejas_score_versions',
        'tejas_preflight', 'tejas_phone_profiles', 'tejas_phone_limits',
        'tejas_login_limits', 'tejas_cron_receipts', 'tejas_operations'
    }
    
    def __getattr__(self, name):
        """Map tejas_X to audit_UUID_tejas_X, reject unknown"""
        if name not in self.ALLOWED_COLLECTIONS:
            raise AttributeError(f"Unknown collection '{name}'")
        
        namespaced = f"audit_{self._audit_uuid}_{name}"
        return self._real_db[namespaced]
```

**Key Features**:
- Failclosed: Rejects unknown collection names
- Cached: Same Motor collection object for repeated access
- Transparent: Works with all Motor operations
- Isolated: All writes go to namespaced collections

## Isolation Verification

### Before Test
```
tejas_packs: 28 documents
tejas_sets: 51 documents
tejas_attempts: 57 documents
tejas_users: 13 documents
tejas_jobs: 67 documents
```

### After Test
```
tejas_packs: 28 documents (NO CHANGE)
tejas_sets: 51 documents (NO CHANGE)
tejas_attempts: 57 documents (NO CHANGE)
tejas_users: 13 documents (NO CHANGE)
tejas_jobs: 67 documents (NO CHANGE)
```

**Result**: ✓ VERIFIED - No writes to main collections

## Test Results

All 6 vulnerabilities confirmed with corrected harness:

| Test | Status | Method |
|------|--------|--------|
| A01: Retry idempotency | ✓ CONFIRMED | NamespaceProxy isolation |
| A02: Concurrent publication | ✓ CONFIRMED | ACTUAL content.get barrier |
| A03: Lost updates | ✓ CONFIRMED | Proper concurrent editing |
| A04: Audience fails open | ✓ CONFIRMED | Actually called set_detail() |
| A05: Lane overflow | ✓ CONFIRMED | ASYNC freeze_ledger + create_task |
| A06: Extraction fencing | ✓ CONFIRMED | EXACT module patch |

**Success Rate**: 100% (6/6)

## App Source Integrity

All app source files remain unchanged:

```
/app/backend/tejas/db.py: bdf0519c75b483abb320ae37dda4a21e3e38a619aaaaf4f0d7ccbc5e9b4d4c1f
/app/backend/tejas/packs.py: 9d4030c3ac01be3aa85a71544f9358fc734b76ede2d4ff66e03330b889868ebd
/app/backend/tejas/attempts.py: 5815007d594a06bd56c619093895816483180ddccd5349bf3cf6e77197965b76
/app/backend/tejas/content.py: b2e668eecb2c01adfa00283580eff462308466c4584499daf6e6072b3a84e022
/app/backend/tejas/jobs.py: 715d98401218baf8e4b80afefa592dc3479d020dc29fd60f5dd225e5f1504510
/app/backend/tejas/corrections.py: ffa98bf42373c9561653b59c8cb2e8dfbdce32e5e185341c902387c3fc5f67ca
```

## Files Created

1. `/app/docs/audit/tests/test_corrected_audit_harness.py` - Corrected audit harness with NamespaceProxy
2. `/app/docs/audit/isolation_manifest.json` - Isolation verification manifest
3. `/app/test_reports/iteration_26_corrected_audit.json` - Test results

## Cleanup

All namespaced collections cleaned up:
- 17 collections dropped during test
- 1 leftover collection from old test cleaned up
- 0 audit collections remaining

## Conclusion

The corrected audit harness successfully addresses all 5 critical flaws identified in the review request:

1. ✓ A01 packs escape fixed with NamespaceProxy
2. ✓ A05 sequential await fixed with ASYNC freeze_ledger + create_task
3. ✓ A06 wrong proxy fixed with EXACT module patch
4. ✓ A02 barrier unused fixed with ACTUAL content.get wrapper
5. ✓ A04 incomplete fixed by actually calling set_detail()

All 6 backend vulnerabilities confirmed with proper isolation. No writes to production DB. App source hashes captured and verified unchanged.

**Status**: AUDIT COMPLETE - Ready for main agent review and fixes.
