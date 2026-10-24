# Backend integrity and capacity audit — 2026-10-24

## Authorized scope
User requested the deepest backend/data/API/canonical-truth audit and implementation toward500,000 concurrent students; explicitly approved deploying compatible fixes after testing. Interpret target as500,000 simultaneously active examinations, not500,000 registered users. Preserve current production DB/data, existing cookie APIs and supplied content. No paid provisioning, destructive migration, real-user load test or secret rotation without a separate safe operator action.

## Execution plan and independently testable gates
1. Inspect mounted API/data flow, immutable packs, single-document answer commands, seal/grade recovery, authorization, bounded resources and existing deployment assumptions. Reproduce suspected correctness/performance faults with isolated fakes or a separate test DB only. Do not execute legacy tests that seed the configured customer DB.
2. Fix canonical-time and ownership-before-hydration paths, preserve retries/receipts and rule/bonus boundaries. Verify skewed app clocks, concurrent saves/submit, old replay/new late commands, foreign IDs and legacy attempts.
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
- Some ownership checks happen after expensive pack hydration.
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

Status: AUDIT AND IMPLEMENTATION IN PROGRESS. Subsequent evidence/results will be appended after testing.
