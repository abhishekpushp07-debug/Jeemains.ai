# Phase 2 of the 8-level backend plan (Levels 1–4) — 21/22 Nov 2026

## Level 1 — baseline speed + All India Daily re-check
- Baseline tools: `python tests/perf_rf_probe.py` (live preview server, TEST player, Server-Timing per call) and
  `python tools/db_audit.py queries` (whole app in-process on the 60k-player scratch DB `rf_audit_scratch`, MongoDB profiler:
  db trips per call, flagged reads). Saved runs: `test_reports/phase2_db_audit_before.txt` / `_after.txt`.
- All India Daily: `tests/test_rf_daily.py`, `test_rf_daily_pcm45.py`, `test_daily_board_ranks.py` played on fresh TEST players
  (their own QA board, never the real one) — see the regression run below.

## Level 2 — tidy
- Removed one-off probe scripts (tests/iter113_*.py ×4, iter115_load_probe.py, iter126_probe_attempt.py), unused constants
  (exam_groups.NEET_ROOT, scope.PCM, rank_predictor.INF), unused imports (tools), the dead "diagrams" mode branch, daily board's
  unused `limit` argument. Frontend scan: no unused files (the "Switch your arena exam" text is already gone).

## Level 3 — server.py split (795 → 146 lines; 144 routes, identical list before/after)
| file | what |
|---|---|
| database.py | Mongo connection (`db`, `client`), BaseDocument, now_iso, to_field/from_field, take_turn |
| jl_proxy.py | website proxy /api/jl/*, cookie jars, website_trouble (520 shield); `jl_proxy.http` = shared client |
| card_bank.py | Card model, card-file sync, /rf/catalog (`warm_catalog`) |
| sprints.py | solo sprints: /rf/sessions, /complete, /history, /sessions/{sid} |
| db_setup.py | indexes + migrations once per code version (`run_once`, SETUP_VERSION) |
| jobs.py | Cup Night tick loop, 5-minute sweep (`sweep(db, settle, cups)`) |
| shared_pass.py | SharedPass: quick pass waited for, slow pass in the background (boards) |
| server.py | only wiring: routers, middleware, startup (incl. `warm_up()`), shutdown |
- `rf_user()` now lives in rf_access.py. Tests/tools updated to the new module names (jl_proxy.*, card_bank.*, jobs.sweep, db_setup.*).

## Level 4 — faster database
- metadata_cache: stale-while-revalidate (a copy past its ttl answers for one more ttl while ONE reload runs behind; invalidation
  still forces a fresh read). Catalog, deal pools, /cards, weak-list card map.
- Startup `warm_up()`: deal pools of all 5 subjects, weak-list card map, catalog, XP ladder, Gang War standings.
- Weak lists (revision.py): incremental `card_marks` (after the first pass only rounds newer than the last one read are added;
  a late round → full pass, same answer — proven by `tools/db_audit.py check` "ALL THE SAME" and tests/test_phase2_speed.py);
  `live_cards()` map replaces per-call rf_cards lookups of thousands of ids.
- All India board + Gang War board on SharedPass (quick passes still waited for, so tests/small crowds see fresh numbers;
  ≥20 ms passes run in the background). Daily deck: one deal per process at a time (no midnight stampede).
- New index rf_cards {source_file, retired} (card sync retire query was a COLLSCAN).
- Numbers (perf_rf_probe, live preview server): new sprint 32.7 → 5.7 ms, new match 42.9 → 4.0 ms, first lobby daily 186 → 4.5 ms,
  history first 130 → 3.9 ms, revision first 105 → 5.8 ms; answers 0.7 ms. db_audit (60k players): calls ≥20 ms 9 → 6 and the
  ones left are first-ever reads of a 2,300-round player after a restart (one full pass ~70 ms, then incremental) or background work.
- Known limit: a player's very first weak-list look on a freshly started process reads their whole history once (O(rounds)).
