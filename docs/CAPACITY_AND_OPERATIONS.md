# Capacity and operations — reference design, not provisioning

## Mounted runtime clarification — 2026-10-24
The worksheet below is the UNMOUNTED V5 reference design, retained for source traceability. It is not the current protocol. Current `/api/internal/capacity/profile` adds `mounted_runtime` without removing legacy fields.

Current web saves use one PUT per dirty question after debounce, durable revision/body-bound receipts, and server-side deadline checks. There are no separate remote draft, lease or telemetry heartbeat endpoints. A planning example with500000 active students, one save/30s,75visits/10800s,2crop requests/visit and10%save retries produces:16666.67save/s +3472.22visit/s +6944.44crop/s +1666.67retry/s =28750requests/s. These are assumptions, NOT measurements. Extra revisits, session reads, results, source misses and bursts must be added. An expiry wave retrying the small status endpoint every6s can demand83333.33requests/s; synchronized submission over30s adds16666.67submit/s. Real clients jitter/retry and the gate rejects excess503; rejection is not successful exam service.

Operational per-process defaults: Mongo pool32, pool wait2000ms, decoded pack cache32MiB, rendered crop cache48MiB, decoded pack ceiling16MiB; in-flight live32/read16/asset8/auth4/control4/probe2. Configure with existing TEJAS_* knobs only after measurement. These are not per-fleet quotas: multiply by workers and pods. Mongo client defaults retain majority+journal acknowledgements; production replica quorum/backups/failover still need verification.

`GET /api/health` is liveness; `GET /api/ready` checks database connectivity only. Staff-only `GET /api/internal/runtime/status` exposes bounded per-process admission/latency buckets/bytes/cache/job counters, without account/attempt/session identifiers. Polling different pods is NOT an aggregate metric; fleet telemetry requires an operator-owned collector.

Each grade drain handles at most16jobs by default; repeated events/15minute platform cron recover durable work. New terminal failed jobs do not permanently starve newer outbox entries. This does not establish continuous large-volume grading or a120second worst-case recovery guarantee. An independent durable worker fleet and measured drain capacity are prerequisites for the stated target.

Safe release: code-only redeploy existing binding; no preview DB clone, seed overwrite, content import or credential changes. New endpoint/ledger metadata are additive, legacy ledgers unchanged. Stop on any lost acknowledgement, grade mismatch, key leakage, incompatible source record or rising503/timeouts. Restore previous code using platform checkpoint controls, never rewrite students' truth to make tests pass.

## Measured PYQ device-check improvement — 2026-10-26
Isolated141 measured real21Jan2026S1 original18.3MB/197uniqueq+solutionrefs: old8.62scold/197sourceGETcalls/197PDFopens; batch4.45scold/1GET/1PDFopen withall197regionsrendered andbyte-identicalPNG. WarmAPIseconduser0.009s; fourconcurrentcoldusers4.51swall/onevalidation/fourseparateuserreceipts. Across10Janpapers4.11–4.63scold. StorageGETboundaryusedlocaloriginalbytes, so theseareCPU/applicationmeasurementsNOTproductionnetwork/FleetSLOs. Cacheholds256content-addressedvalidationproofs, neveraccountpermission orpreflightrevision. Auth,availability,filemembership and per-userreceipts still enforced. Failuresnotcached; hashes/refs/policychangesmiss. Post141validationlocksseparatedfromassetlocks; pendingtargetedretestwiththemeQA. No capacityqualification implied.



Authoritative workload: PDF05 pp3,46. No load certification is inferred from this preview.

## Editable worksheet
C=500000, T=10800s, dirty fraction=.20, commit interval=30s, draft interval=10s, lease interval=60s, telemetry interval=30s. R_commit=C/30=16666.7/s; R_draft=C*.20/10=10000/s; R_lease=C/60=8333.3/s. Live baseline=35000/s; telemetry=16666.7/s; total=51666.7/s. 2× headroom:70000 live+33333.3 telemetry=103333.3/s. Pathological100%dirty/5s=100000draft+25000commit/lease=125000live/s (141666.7with telemetry), independently tested, not covered by2×normal.

500000 starts/120s=4166.7/s;500000 submits/30s=16666.7/s. A2MB candidate pack×500000=1TB, over120s=8.333GB/s=66.667Gbit/s before overhead. Prefetch/cache assumptions must be reported, not hidden.20 equally loaded cells=>1750live/s/cell baseline,3500live/s/cell2×. Three-hour totals:180M commits+108M drafts+90M leases=378Mlive;180M telemetry=>558Mcombined. API RPS != transactions != row writes != IOPS; measure index/WAL/replication amplification.

## Reference topology / ownership
Edge static app and viewer authorization -> stable thin home-cell routing. Global control publishes signed permits/packages ahead of window. Each cell has independent transactional writer+failover-safe standby, bounded API/grade/admin pool budgets, isolated queues, admission and fencing authority. Live write route uses cell-local identity/entitlement material, no global synchronous allocator/analytics dependency. Analytics/report/extraction private batch plane with distinct workload identities and keys; source-private origin never exposed through candidate distribution.

Do not provision this by merely increasing replicas of the preview. Proposed20×25k is subject to measured per-cell saturation; lower admission until qualified. API replica pool sum + worker pools must stay below writer budget. Store measured limits, not guessed instance counts. Do not claim horizontal DB scaling from frontend autoscaling.

## Application knobs (configuration reference only; existing env unchanged)
Pool sizing/wait and pilot batch lane bounds belong in documented TEJAS_* environment settings. Default pilot values must stay conservative. Platform-managed15-minute maintenance is recovery only: not a production admission/expiry timer and not a worker fleet. Deadline acceptance is enforced synchronously on saves; receipt recovery does not extend time.

## Campaign before launch
Ramp gates:1k ->5k ->25k single cell ->multi-cell skew ->500k active, then2× workload envelope and independent pathological draft case. These are proposed stages, NOT executed counts. Use distributed isolated generators plus real-browser cohort for offline/mobile/storage behavior. Do not run full load against this shared preview.
Record git revision, package/profile hashes, workload parameters, topology, approved quotas, warm/cold cache state, p50/p95/p99 latency, errors, pool wait, commit latency, replication lag, queue oldest-age, sealed-but-ungraded age, bytes/IOPS and generator saturation. Select latency/error SLOs before qualification; changing SLOs after failure invalidates comparison.

Correctness oracles: zero lost acknowledged commitments, one durable terminal receipt, retries never double-apply, exact grade reconciliation, immutable historical reports, zero unreleased-key/other-account access. Distinguish dropped optional telemetry from lost required answers.

## Fault and recovery gates
- Drop response after commit; retry identical and altered body, including after newer command/deadline
- Crash between close and dispatch; outbox recovery, worker crash before/after result publish, stale lease worker must not win
- Lock waiting across deadline, duplicate starts/submits, writer takeover, out-of-order delivery and command sequence gaps
- DB writer stall/quorum loss; stop new admissions while preserving already admitted work; never downgrade ack durability
- One-cell overload/global allocator outage/asset source outage must not halt healthy admitted cells
- Worker poison/extraction saturation/report backlog, cold caches, platform cron duplicate/malformed auth, network flap
- AZ loss and fenced failover; regional restore at production-equivalent volume with manifest/receipt/outbox/KMS verification
- Roll back canary cell with backward-compatible schema, never rewrite frozen academic truth

Proposed regional RPO≤5min/RTO≤60min (PDF05p53) are unverified. Local RPO zero requires verified synchronous durable replication; majority/journaling on a single node is not multi-AZ proof. Vault retention, encrypted backups, retention/legal deletion, key recovery and restore concurrency require provider evidence.

## Operations stop conditions
On critical gate failure: halt new admissions to affected cell, preserve accepted commitments, isolate batch/telemetry first, publish accurate status, retain incident evidence, retest changed artifacts. Never relax source/key permissions or invent successful receipts to relieve load. Infrastructure, CI/CD, DB server and production deployment changes require operators outside this application session.
