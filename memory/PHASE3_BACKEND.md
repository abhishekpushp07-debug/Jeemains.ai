# Phase 3 of the 8-level backend plan (Levels 5–8) — June 2026

User choices: "Poora Phase 3 ek saath, chhote safe steps mein"; App Health page = "Sirf backend link, app mein nahi"
(owner panel web page, same owner sign-in as the deletion panel); load test = "Preview pe chhota test, usse 50k ka andaza";
no extra small tasks. No screen or button changed for students; the same server addresses.

## Level 5 — speed engine
- `fast_json.py`: every plain-data answer is written by orjson (app default response class + FastAPI's `serialize_response`
  patched only for routes without a response model). A 30-card match view: 1.2 ms → 0.014 ms of CPU. Same JSON (tested:
  dates, int keys, models, sets, >64-bit ints fall back to the old path).
- `later.py`: work nobody waits for runs after the answer (friend-feed rows, a website session's once-a-day touch).
  Coins, answers and rewards are always written before the answer. Bounded (2,000 waiting, then inline); drained at shutdown.
- Match end: the players' rewards are written side by side (`asyncio.gather`), not one after another.
- Already in place from earlier work: pooled website connection (aiohttp, keep-alive), gzip ≥1 KB, warm pools/boards/XP ladder.
- Probe (preview, server time p50): sprint complete 9.6 → 3.3 ms, new sprint 7.2 → 4.2 ms, history 3.7 → 1.6 ms, match view 2.5 → 1.2 ms,
  answers 0.6 ms.

## Level 6 — live match engine for many copies
- `duels.close_all()` at shutdown: every phone on the stopping copy gets close code 1012 at once and reconnects (the app
  already reconnects with a random back-off and polls meanwhile); the copy leaves every match's `ws_nodes` in one write.
- Card bank: a file another copy already wrote is not written again (fresh read of `rf_meta.card_files` once per pass);
  files whose mtime+size did not change are not re-read (was 11 MB read + hashed every minute per copy).
- Jobs on one copy: sweep (`take_turn`), database setup (version turn), Cup Night draw (atomic status flips). Rewards once:
  `rf_awards` unique (uid, ref) + `paid_refs` in the same profile write.
- `tools/restart_drill.py` (two copies A/B on one DB, SIGTERM A mid-match): socket closed with **1012 after 0.07 s**, copy B
  saw all 15 answers, match finished on B, **reward paid exactly once**, `ws_nodes` left empty. PASSED.

## Level 7 — shields and eyes
- `website_shield.py` (per copy): ≥8 failures and ≥50% of the calls of the last 10 s (connection errors, time-outs,
  502/503/504/52x, answers slower than 10 s) → no call is sent for 5 s (doubling to 30 s), the proxy answers 503
  `website_unavailable` at once (plain line, app keeps work safe); then ONE probe; success closes it. `WebsiteDown` is an
  aiohttp.ClientError, so every existing `except UpstreamError` handles it.
- Rapid Fire keeps playing while the website is down: `/rf/access` writes `rf_trust` (hash of device handle or access
  cookie → uid, 6 h, TTL; erased with the account). Website down/5xx → a grant from that trust (`trusted: true`). Website
  401/403/4xx, unknown session, expired trust → no grant.
- Limits per player (in the RF guard, per copy): 20 calls/s, bursts of 120 → 429 `slow_down` (Retry-After 2).
- Crowd order: answers/sockets never wait; new matches wait (arena_gate); background looks (boards, feeds, history, live
  strip, other players' profiles) — while packed, at most 16 at once, the rest 503 arena_busy (Retry-After 10; the app keeps
  what it shows). Website calls no longer count toward "packed" (`inflight_web`), and above 3,000 waiting website calls per
  copy the proxy answers 503 at once (`JL_MAX_INFLIGHT`).
- `log_redact.py`: a filter on every log handler masks PINs, passwords, tokens, cookies, Bearer values and phone numbers
  (tracebacks too). 422 answers keep type/loc/msg only (before, Forgot PIN echoed the new PIN back).
- App Health page `/api/owner/health` (+ `/api/owner/health/data`, owner session cookie): students signed in, playing live,
  live matches, speed per part (answers / Rapid Fire / sign-in / website calls / whole app: calls, typical, p95, errors),
  website shield state + calls/failed/paused/p95, background jobs (last run, took, worked), each server copy (delay, working
  on, live players, packed, asked to wait), busiest addresses. Counts and timings only. Every copy writes `rf_health_nodes`
  every 5 s (TTL 2 min); a stopping copy deletes its own row at shutdown (`health_stats.leave`), a crashed one drops off
  after 16 s. Shared jobs in `rf_meta` `job:<name>`; a job's colour uses `late_s` (how long before its copy's report it
  last ran), so the 3-second Cup Night clock no longer turns amber between reports. Rows are named by the matched route
  pattern (`/api/rf/friends/code/{code}`); unrouted calls keep plain lower-case words only (letter-only codes never show).
  Signing out (`/api/jl/auth/logout`) also deletes that session's `rf_trust` row. Fits a 390 px phone (no wrapped
  numbers, Refresh + Sign out on one line, "No calls" rows). Dark owner style, green/amber/red, refresh 30 s.

## Level 8 — proof (preview container: 4 cores shared by load clients + server + mongod)
Rapid Fire, Practice Rival matches, 30 cards, 3 s per card, live socket + inbox poll per player (`tools/loadtest_rf.py`):
| run | players | answers/s | errors | answer p50 / p95 / p99 | server CPU | per 100 answers/s |
|---|---|---|---|---|---|---|
| 1 copy | 250 | 55.6 | 0 | 1.6 / 3.6 / 6.3 ms | 0.092 core | 0.165 core |
| 1 copy | 500 | 106.8 | 0 | 1.7 / 5.3 / 14.9 ms | 0.175 core | 0.164 core |
| 1 copy | 1,000 | 213.8 | 0 | 2.0 / 26.1 / 181 ms | 0.366 core | 0.171 core |
| 2 copies | 2,000 | 440.5 | 0 | 2.1 / 34.2 / 199 ms | 0.778 core | 0.177 core |
- Straight line: the CPU per answer stays the same from 250 to 2,000 players and from 1 to 2 copies.
- Before Phase 3 (SCALE.md, iteration74): 1,000 players took 0.56–0.62 core → now 0.366 core (~40% less CPU per player).
- Website SLOW drill (fake website, every call 15 s; 300 test-takers saving answers every ~1 s + 250 Rapid Fire players on
  the same copy): 302 calls waited (before the shield shut + probes), **12,859 answered at once (p95 1.9 ms)**, website calls
  waiting fell from 300 to ~1; Rapid Fire meanwhile: 250/250 finished, 0 errors, answer p95 4.4 ms; the copy was never "packed".
- Website DOWN drill (nothing listening): 8,714 paper loads in 30 s, all answered 503 at once (p95 1.0 ms), shield open.
- Soak (~12 min, 5 runs × 600 players = 3,000 different players, 90,000 answers, one copy): 0 errors in every run, answer
  p95 6.3 / 6.4 / 6.5 / 6.4 / 6.5 ms, CPU 22–23% of a core each run, memory 326 → 404 MB and flat in the last run
  (bounded per-player memories fill up, then stay). Hours-long soaks were not run on the preview.

## 50,000 students at once (estimate from the measured straight line, not a measured 50k crowd)
- 50,000 players × ~0.21 answers/s each (3 s think + card show) ≈ 10,700 answers/s → ~0.17 core per 100 answers/s → ~18
  cores busy for the app, ~27 with 50% headroom (e.g. 7–8 servers × 4 cores, 4 copies each).
- Database: mongod used ~0.5 core per 1,000 players here (writes + live channel) → ~25 cores at 50k; a dedicated MongoDB
  replica set sized for ~30–40k ops/s. Copies × 40 pool connections must stay inside its connection limit.
- Production copy count / database size are set by the hosting (Emergent, support@emergent.sh). The website's own login,
  tests and results capacity is in the website's hands; the shield protects our server and Rapid Fire from it.

## Tests
- `tests/test_phase3_engine.py` (14, scratch DB `<DB_NAME>_phase3_selftest`): JSON parity, shield states, nothing sent while
  shut, trust fallback (6 cases), player limit, crowd order, website calls ≠ packed, redaction (+traceback), 422 no echo,
  8 simultaneous payouts → paid once, card file written once across copies, health data adds copies up + no personal data.
- Full backend suite on the preview: 654 passed, 70 skipped, 1 failed = the route-count check (144 → 146, the two new App
  Health routes; updated).
- Tools: `tools/restart_drill.py` (new), `tools/loadtest_mock.py` now also reports failed-call latency.
