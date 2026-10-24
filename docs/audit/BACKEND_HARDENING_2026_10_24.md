# Backend integrity and capacity audit — 2026-10-24

## Authorized scope
User requested the deepest backend/data/API/canonical-truth audit and implementation toward500,000 concurrent students; explicitly approved deploying compatible fixes after testing. Interpret target as500,000 simultaneously active examinations, not500,000 registered users. Preserve current production DB/data, existing cookie APIs and supplied content. No paid provisioning, destructive migration, real-user load test or secret rotation without a separate safe operator action.

## Execution plan and independently testable gates
1. Inspect mounted API/data flow, immutable packs, single-document answer commands, seal/grade recovery, authorization, bounded resources and existing deployment assumptions. Reproduce suspected correctness/performance faults with isolated fakes or a separate test DB only. Do not execute legacy tests that seed the configured customer DB.
2. Fix canonical-time paths and preserve already-correct ownership-before-hydration, retries/receipts and rule/bonus boundaries. Verify skewed app clocks, concurrent saves/submit, old replay/new late commands, foreign IDs and legacy attempts.
3. Improve immutable content reads/caching and integrity verification without caching authorization. Verify hash corruption fails, cold-load coalescing, eviction/mutation isolation, selected-question lookup, no answer-key leakage and unchanged source bytes.
4. Add per-worker workload admission and bounded telemetry, safe transient-DB error mapping, and bounded worker recovery. Verify overload rejection before DB access, separate live/asset/control lanes, counter cleanup on disconnect/error, no PII metrics, poison job/backlog behavior and existing cron protection.
5. Add frozen-ledger source commitment and deterministic validation for new ledgers only; preserve old immutable ledgers. Verify same snapshot/same proof, input drift detection, exact score/marking, repeated grading and ambiguous retry.
6. Replace misleading capacity metadata with an explicit model of actually mounted client traffic, per-worker resources and unqualified infrastructure assumptions. Provide a non-production load/fault qualification plan and real local measurements, never a500k claim based on arithmetic.
7. Run isolated backend fault, auth, regression and limited synthetic workload tests; a browser smoke/regression confirms existing student UI still works. Review every open functional defect. Deploy compatible changes only after passing checks, using the existing deployment/binding/secrets, then perform safe read-only live checks.

## Confirmed protections to preserve
- Answer CAS already uses Mongo `$$NOW`, per-question revision, durable body-bound receipt, atomic sequence and first-answer tracking. Do not replace with cache-only acknowledgement.
- Question packs already content-address and verify SHA on cold load; original ledgers use insert-once semantics.
- Start/retry request aliases are durably bound; some route catalogue warnings are stale and require evidence-based correction.
- Browser recovery timer does NOT reload the full attempt every5seconds once loaded; it retries only dirty outbox work. Earlier polling hypothesis is ruled out, so no unnecessary polling endpoint/frontend rewrite.
- Source rendering is authorized, but many callers hydrate the full question pack just to inspect one question. PDF byte verification and cold-request/cache costs need tightening.
- Backend has bounded pool/body sizes and per-kind job concurrency, but no front-door per-workload in-flight admission budget.
- Global capacity calculator describes hypothetical commit/draft/lease traffic not fully mounted runtime behavior; it is explicitly unqualified and must remain so.

## Risks requiring reproduction / fixes
- Ownership-before-hydration hypothesis RULED OUT by iteration134: user-scoped queries already precede pack reads. Preserve this invariant on the new lightweight routes.
- App-clock early expiry/finalization checks can disagree with database-clock save admission; validate with skew injection.
- PDF crop path does not compare source bytes with a declared source SHA, unlike rendered-PNG path.
- Pack JSON is decoded in full for each hydrated request; potential cold-start amplification/cache mutation hazards must be measured.
- Admission-free bursts can queue at pool/thread boundaries and starve live saving behind heavy reads/assets/control work.
- A drain call can process up to4096 jobs in a request background lifecycle;15minute crash-recovery cadence is not a120second grading guarantee.
- New ledger provenance can be explicit without rewriting older frozen truth; legacy provenance stays honestly unqualified.
- Distributed login limiter first-upsert races must not bypass limits or cause avoidable500s.
- Test suite contains legacy fixtures that contact configured customer APIs/DB; those are unsafe to run and are not accepted validation evidence.

## Release blockers outside this change's authorization/budget
- Student phone ownership remains unverified; no OTP provider/account was authorized. Do not claim public high-trust identity assurance.
- Prior tracked staff credentials require controlled rotation/session invalidation if still exposed; never guess/rotate a sleeping user's password or reveal it in a report.
- Replica/shard topology, independent failure domains, actual worker/CDN capacity, network quotas, edge trusted-client-IP policy and500k distributed load/failover tests remain unprovisioned/unverified.
- No claim of world-best, multi-AZ durability or measured500k service until objective SLO and integrity evidence exists.

Status: IMPLEMENTED, AWAITING REGRESSION AND COMPATIBLE REDEPLOY.

Iteration137: all73prior fault/regression cases and71series cases passed; browser error arrival-order and pending drafts passed at desktop/mobile. Added28window cases exposed only four ordinary-competition catalogue metadata inconsistencies (future/expired papers listed but every detail/start correctly denied); no question leak. Catalogue now applies the same optional start/end database-time clauses for all scheduled papers, preventing dead-end links; the dedicated competition schedule endpoint is unchanged. No changes to cosmetic footer/button wrapping or studio-only time labels.


Iteration136 follow-up: all135regressions passed,22/23new cases passed plus71series tests; final new fault reproduced early non-series private-paper starts under app-clock skew. `permitted` now requires explicit authoritative time, with all callers updated; preflight timestamps and list/detail/window/date-expiry filters agree with database time. Cron rejects unauthenticated calls before parsing their body. Deadline-check failures use a separate browser error state so save conflicts survive either arrival order. Awaiting final targeted verification.


## First regression evidence and follow-up
Iteration135:49/50 new isolated tests passed, with one reproduced remaining early-score release in exam-navigation history under app-clock skew. Additional isolated auth/CORS and content-transfer/streak regressions passed. Corrective changes cover all identified sibling score/solution/history gates with database time, including My Tests, series history, saved AI, review/report and competition leaderboard. This is a correctness/privacy fix, not a visual redesign. Remaining harmless schedule metadata timestamps are not represented as timer authority.

Measured local fixtures:32 concurrent cold100-question pack loads now1DB read/1decode (30ms) versus32/32 (43ms) before. Warm full defensive copies were19.9ms versus prior9ms JSON copies: not a universal speedup; selected-question reads avoid copying a full pack. A status reply was303bytes versus90192bytes full attempt;32status calls took32.1ms. Full-read concurrency deliberately rejected16/32 with503 at lane limit16; overload rejection is not capacity success. Only a small local fixture, not500000users.

Nonunique `job_lane_fifo(kind,status,created_at)` index added after isolated explain showed blocking queue-sort under the old delayed-job index; no existing index dropped. Job output message is literal, not a pipeline expression. Cron malformed envelope returns400 and header-only run-id follows the documented contract. Grade read already excludes command_receipts/response_schema; a tester suggestion claiming otherwise was source-checked and ruled out.



Credential hygiene: removed historical plaintext staff-password literals from the identified legacy test and current credential notes; that unsafe live-data test is now retired/skipped. Active accounts/secrets/sessions were not changed. Repository history and other archived artifacts are not certified clean; controlled rotation/session invalidation remains mandatory.

## Implementation and explicit boundaries — 2026-10-24
- Fault baseline134 reproduced premature expiry on five paths when the application clock led MongoDB by3600seconds; `finalize(time_limit)` itself now requires database expiry. Answer/visit/bonus/owned/history use MongoDB time; new starts derive timer time from a database read. Old stored deadlines are never rewritten.
- Additive owner-scoped `/api/attempts/{id}/status` returns only timer/seal metadata. The browser uses it for deadline confirmation instead of loading an entire exam. No extra periodic poll was introduced.
- Bounded decoded pack LRU, coalesced cold loads, decompression bound, digest/schema/count checks, per-question lookup and defensive copies. Assets retain user/question/score-version scope, embargo, and locked-bonus denial. PDFs with declared hashes are verified before first rendering; legacy missing hashes remain explicitly unqualified.
- New ledgers record sealed source commitments (attempt/user/pack/sequence/answers/rules/profile/version); source drift fails closed. Historical ledgers without commitments remain byte-for-byte unchanged and are not retroactively certified. This detects source drift, not a malicious operator able to rewrite both source and proof.
- Separate process-local live/read/asset/auth/control/probe admission budgets return503+Retry-After before expensive work. Bounded no-PII counters and cache/job metrics are staff-only. Readiness pings MongoDB; liveness stays lightweight. None measures fleet capacity.
- Job claim/lease/retry decisions use database time; release-triggered drains are bounded to16jobs by default. Terminal failed grading no longer blocks every subsequent outbox scan. Existing15minute platform recovery stays unchanged; no new scheduler or paid queue.
- Concurrent auth limit initialization retries DuplicateKeyError once without upsert, fail-closed if no counter exists. Cookie/phone identity and configured owner are unchanged; no plaintext password is needed in new tests.
- Capacity profile preserves the old reference fields for compatibility, explicitly labels them UNMOUNTED_V5_DESIGN, and adds equations for current answer/visit/asset/deadline traffic. No fake remote-draft/lease heartbeat is described as mounted.

## Data/query/packaging audit
MongoDB remains canonical; no SQL/Redis migration or shadow write store was added. Existing unique id/user-start/active-attempt indexes enforce identities and replay aliases; user/time history, job kind/status, expiry/status, ledgers and score-version indexes already exist. Validate query plans on isolated data. Every additive route is in the executable startup contract catalogue and OpenAPI. Do not run legacy tests against customer DBs. Index/pool tuning and shard keys require production volume, topology and explain evidence, not guesses.

## Required qualification evidence (not obtained by code changes)
Ramped isolated load campaign1k/10k/50k/100k/250k/500k with approved budget and production-equivalent data/replication; three-hour soak, simultaneous starts/deadlines/submits, offline retries, cold assets, DB stall/failover, kill-after-seal-before-enqueue, stale worker, restore drill, exact ack/ledger reconciliation, p95/p99 and saturation/queue-age/egress. Proposed SLOs remain targets until measured. No live load generation is authorized.

