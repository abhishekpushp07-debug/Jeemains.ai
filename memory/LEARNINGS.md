# Learnings (read before running tests)

## 2026-11-20: parallel isolated test databases crash the preview MongoDB
- What happened (this session, main agent's own mistake): 9 copies of `tests/cut_probe208.py` were started at once. Each makes its own `tejas_isolated_book170_<hex>` database (about 46 collections plus all indexes). The preview mongod has a soft limit of 1024 open files; it hit the limit (WiredTiger error 24, "Too many open files") and aborted. Supervisor log: 5 aborts, at 18:21:05, 18:21:18 and 18:22:20 UTC (during the parallel probes) and at 18:24:29 and 18:24:35 UTC (during a follow-up diagnostic script that ran `collStats` on every collection of 11 databases). The same abort is in the log for the earlier session too (2026-11-19 17:25, 2026-11-20 15:40 and 15:42).
- App data (`test_database`) was checked afterwards: users 1, sets 252, attempts 8, files 164; `validate` passed on tejas_sets and tejas_attempts; no unfinished jobs; /api/health and /api/ready 200.
- Rules:
  1. Never run more than 2 harness databases at the same time (one bridge + one suite).
  2. Stop harness scripts with SIGINT (`kill -INT <pid>`), not `pkill`/SIGTERM: only then does their `finally` drop their database.
  3. Do not walk every collection of every database (collStats, listIndexes in a loop): each one opens files.
  4. To test the cutter on many pages use `tests/cut_scan209.py`: it calls the page reader and the cutter directly on the PDF, needs no database and uses all CPU cores.
- Mitigation applied to the running process only: `prlimit --pid <mongod> --nofile=65536:1048576` (soft limit raised inside the existing hard limit; no config file changed). It is lost when mongod restarts, so apply it again before any harness run after a pod restart.
- Cleanup done: the 8 databases created by that run were dropped by exact name after checking each held only probe fixtures. Two older leftovers were NOT touched because this session did not create them: `tejas_isolated_book170_436fa878` (files made 14:58 UTC, no books, no users) and `tejas_isolated_book170_50fcbf47` (files made 15:41 UTC, no books, one harness user). They look like harness databases orphaned by the earlier aborts; they only cost open files.
