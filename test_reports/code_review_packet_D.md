# Separate code review: Packet D (truthful storage badge)

Reviewed: worktree at commit `18a2ef5` (no app code changed after it). Read-only review; no test suite was run by the reviewer; no call to Supabase or Emergent.
Files: `backend/tejas/storage_health.py`, `backend/tejas_storage.py` (notes + storage checks), `backend/server.py` (lifespan, storage handlers), `backend/tejas/jobs.py` (wake + maintain), `backend/tejas/machine.py`, `backend/tejas/ceo.py`, route/request contracts, `StorageBadge.js`, `MachinePanel.js`, `UploadProgress.js`, `master.css`.

## Verdict
**NO BLOCKER.** Reviewer's status: "READY WITH FIXES". No critical, no high. One medium, three low.

## MEDIUM (not fixed)
Owner's Machine panel / storage badge can stay loading for a long time when a store is slow.
- Where: `storage_health.py` `health()` awaits `check()` (lines 438-447); `_check()` awaits `store.probe` (300-316); `machine.py:27` calls `health(fresh=False)`; `tejas_storage.py` `request()` uses a 120 s timeout, two tries for the health check.
- When: the owner opens the badge or Machine panel more than 60 s after the last check while Emergent (or Supabase) hangs. The request waits for the real check. Worst case for the Emergent leg: about 2 x 120 s.
- Effect: owner screens only. Uploads, jobs and students are not affected: the check runs in a worker thread, one server at a time (lease), and all waiting requests share one check.
- Reviewer's suggested fix: return the saved record at once and run the check behind, or bound the wait.
- Note for whoever fixes it: with no saved record yet (first check ever), an early answer would show Supabase as "bad". A fix must not create a false red line.

## LOW (not fixed)
1. `tejas_storage.EVENTS` is a deque of 200. If the database refuses writes for long and many notes arrive, the newest notes can be dropped (`storage_health.py` 166-168). Best-effort list.
2. `useStorageHealth` / `useMachineStatus` have no guard against an older answer arriving after a newer one; the badge can show an older snapshot for a moment.
3. `/admin/storage/retry` and `check()` give a plain 500 to the owner if the database fails inside `flush` / `wake_storage`.

## Checked and found correct
- Shared record: revision compare-and-swap, no lost update; errors and readings capped at 20; an older note does not overwrite a newer reading.
- Leases: one check and one big test at a time across servers; a dead holder's lease expires (120 s / 600 s).
- Watcher: catches every exception per round, sleeps 30 s, ends cleanly on shutdown; notes never raise; works when Supabase is not configured.
- Deletion safety: `_CHECK` is an anchored pattern; `_drop_checks` and `sweep_checks` refuse any other name; `sb_end_upload` checks host and path; `_removable` blocks other folders and `..`. A failed delete does not turn the badge red and is swept later.
- Load: admin polling cannot start a storm of checks; the 7 MiB test runs about once in 24 h, every 15 min only while the route is unproven, failed, or a PDF waits on it.
- Truth: a read-back mismatch is that file's fault (yellow, not red); Supabase away is red; a stuck file or a 10-minute wait forces yellow; no path found that shows green while a file is stuck.
- Access: all storage and machine routes are owner-only; contracts exist, so the server starts.
- Frontend: null-safe on partial data, timers and listeners cleaned up, double-click guarded, data-testid present.
- No change to student flows, verified PYQ or `LiveSeries.js`.
- `ruff check` clean on `storage_health.py` and `tejas_storage.py`.

## Could not be verified by reading
- Real timing of Supabase / Emergent under a hang.
- Merge and lease behaviour under two real servers (covered by suites `storage_badge236`, `storage_badge_edge237` inside one process).
