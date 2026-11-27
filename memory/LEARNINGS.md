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


## 2026-11-25: notes from the storage packets (A–D)
- Even ONE suite at a time is close to the default limit: the 26-suite regression ended with mongod holding 895 open files (limit 1024 by default). Raise the limit before every run: `prlimit --pid $(pgrep -x mongod | head -n1) --nofile=65536:1048576`. It is lost when mongod restarts or the pod is new.
- `tests/ui_storage_wait_qa224.py` needs `/tmp/uibridge224/qa_variant.pdf`; nothing creates it. Make it after the bridge says READY: `python -c "import sys; sys.path.insert(0,'tests'); from cut_bridge207 import cut_pdf; open('/tmp/uibridge224/qa_variant.pdf','wb').write(cut_pdf('QAVAR', long=True))"`.
- A new API route without an entry in `tejas/route_contracts.py` (and, with a body, in `request_contracts.MODELS`) stops the server at startup.
- The Supabase bucket name comes from `FRONTEND_URL`. A fork with a new preview address gets a new, empty bucket.
- `/root/p2` (scratch logs, runner scripts) is outside the repo. The runner scripts are copied to `backend/tests/runners/`; the logs that matter go to `test_reports/`.
- Write a code review's result into a file as soon as it arrives; one answer was cut off by the tool and a "medium" point was lost for hours.


## 2026-11-27: the long chain aborted the preview MongoDB seven times (the builder's own miss)
- What happened: `tests/runners/n1_chain.sh` (54 suites, one at a time) was started without raising mongod's open-file limit. mongod aborted at 13:13, 13:14, 13:15, 13:19, 13:22, 13:23 and 13:24 UTC ("Too many open files") and supervisor restarted it each time within 2 seconds. The limit had fallen back to 1024 after a pod restart.
- Effect on the tests: `publish_progress_iso217` failed 4 of 5 inside that chain with "connection closed"; alone it passed 5/5 twice. Any other result of that first run is less trustworthy for the same reason, so the chain was run again with the limit raised (14:47–15:00 UTC): no abort, 1,918 checks, 1,898 pass, 20 fail, the 20 old lines only.
- The app's own preview database afterwards: students 2, sets 252, attempts 8, staff 1; `validate` passed on tejas_sets, tejas_attempts, tejas_phone_profiles, tejas_users, tejas_sessions. Nothing was lost.
- Fix: `tests/runners/solo.sh` (and its copy /root/p2/solo.sh) now raises the limit itself (`prlimit … --nofile=65536:1048576`) before it starts anything. Always start suites through solo.sh.
- Two throw-away databases are still there from older failing suites (`tejas_isolated_book170_19f082e9`, `tejas_isolated_window177_66e69d`). Not dropped: that needs the owner's word.

