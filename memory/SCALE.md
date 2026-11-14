# Rapid Fire crowd scale — how it works and what was measured (iteration74)

## Design (many servers, one arena, database only — no Redis)
- Any number of server processes/pods share MongoDB. Nothing a match needs lives only in one process.
- Live channel `rf_events` (capped, 128 MB / 500k docs). Each match lists the servers holding its sockets in `rf_duels.ws_nodes`
  (added atomically when the first socket of that match opens on a server, removed when the last one closes).
  A change is addressed only to those servers (`to` + `by.<node>`); each server tails only events addressed to it
  (projection returns only its own match ids). A match whose sockets are all on the server that changed it sends nothing.
  Traffic grows with changes, not changes x servers.
- Answers: one round trip (`quick_answer`): pipeline update measures answer time on the database from the player's last answer,
  guards (status, time window, order, forfeit) in the filter; anything unusual falls back to the full path. `/api/health/load`
  shows `answers_quick` / `answers_full`.
- Spectators: `rf_watch` (TTL 60 s) shared by all servers for the count and the 100-watcher limit; only matches with a recent
  `watched_ts` cost a count query.
- Session cookie rotation: Mongo lease (`jl_locks`), Cup Night draw: atomic status flips — both already multi-server safe.
- Crowd control per process (`load_guard.py`): new matches wait (503 `arena_busy`, app shows "Kuch second ruko") when the
  event loop lags; inbox answers `poll_s` 20 instead of 8 when busy; the app polls the inbox every 25 s during a live match.
- Mongo pool 40 per process (env `MONGO_MAX_POOL`) so many processes stay inside the database connection limit.

## Measured here (4-core container shared by load clients + servers + mongod; CPU-throttled ~63 s per run)
| run | players | answers/s | errors | backend CPU | mongod CPU |
|---|---|---|---|---|---|
| 1 worker, practice rivals, before | 1000 | 237 | 0 | 0.62 core | – |
| 1 worker, practice rivals, after | 1000 | 237 | 0 | 0.56 core | – |
| 3 workers, practice rivals | 3000 | 597 | 0 | 1.4 cores | – |
| 3 workers, student vs student | 3000 | 547 | 0 | 1.04 cores | 0.45 core |
Answer p50 2-3 ms. Tail latency in this container comes from CPU throttling of the shared 4-core quota.

## Rough sizing for 100,000 students playing at once (estimate, not measured)
- App: ~2,900 players per core → ~35 cores busy, ~50 with headroom (e.g. 12-13 servers x 4 cores, 4 workers each).
- Database: ~30k answer writes/s + cross-server reads + inbox → a dedicated MongoDB replica set sized for ~80-100k ops/s
  (roughly 15-20 cores). Must be arranged with the hosting provider (Emergent support: support@emergent.sh).
- Load test: `python tools/loadtest_rf.py --players N --procs P --think 3 --ramp 40 [--pairs] --base http://127.0.0.1:PORT/api/rf`,
  then `--cleanup`. Multi-worker test server: `uvicorn server:app --port 8002 --workers 3` (kill it afterwards).
  Local mongod allows only ~819 connections (soft file limit 1024): keep test servers few.
- Tests: `RF_NODE_B=http://127.0.0.1:8002 python -m pytest tests/test_iter74_multiserver.py -q -o addopts=`.
