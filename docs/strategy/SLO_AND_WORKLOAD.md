# Workload and measurable “no lagging” contract

**Status: proposed acceptance contract, not measured performance.** Packet01 freezes definitions and operator signoff; Packet10 produces qualification. Source guide numbers below are explicitly proposed by PDF-05, not vendor guarantees. Additional client/PDF budgets are separately labelled proposals.

## 1. Workload identities and boundaries

C=500,000 distinct admitted active attempts, T=10,800 steady-state seconds. Each has an independent actor/session, home cell, lease, adapter/package version, deterministic answer-state machine and expected receipt ledger. Idle users, cached duplicate operations and one identity reused500k times do not count.

| Stream | Formula | Global baseline |
|---|---|---:|
| Explicit commits | C/30s |16,666.7 requests/s |
| Dirty drafts | C×0.20/10s |10,000 requests/s |
| Lease renewal | C/60s |8,333.3 requests/s |
| **Live subtotal** | Sum above |**35,000 requests/s** |
| Optional telemetry batches | C/30s, isolated collector |16,666.7 requests/s |
| **Combined baseline** | Live+telemetry |**51,666.7 requests/s** |

In three hours:180million commits +108million drafts +90million lease renewals =378million live operations; telemetry adds180million batches. These are not378million distinct answers, nor a direct IOPS estimate. Measure transaction/row/index/outbox/WAL/replication amplification.

A25,000-attempt cell carries1,750 live requests/s plus833.3 telemetry batches/s. Qualify3,500 live requests/s at the2×mix without increasing its authorized concurrency to50,000.20full cells provide no empty spare cell.

## 2. Separate overlays and capacity envelopes

| Scenario | Required demand / measurement |
|---|---|
|2×normal throughput |70,000 live +33,333.3 telemetry =103,333.3 dynamic requests/s, **before** other overlays |
| Pathological draft case |100%dirty every5s →100,000drafts +16,666.7commits +8,333.3leases =125,000live/s; with baseline telemetry141,666.7/s. Separate test, not covered by2×normal |
| Start wave |500,000/120s =4,166.7starts/s; authentication, grants, preflight and content requests added explicitly |
| Submit wave |500,000/30s =16,666.7submissions/s; overlapping full baseline gives51,666.7live/s and68,333.3with telemetry, before retries/assets/other reads |
| Grade burst example |500,000×75/120s =312,500item evaluations/s. Recalculate for actual adapter mix, partial rules and expensive cases |
| Candidate delivery example |2MB×500,000 =1TB; over120s ≈8.333GB/s or66.667Gbit/s before overhead.2MB is a reference, not an assumption that image-heavy papers fit it |
| Report demand |All500k may request a complete report after grading/release. If within30s,16,666.7report requests/s **in addition** to other streams. Generation throughput, pages/s, bytes/s and storage/egress must be measured |
| Result/job polling |500k clients every10s would add50,000reads/s; every30s adds16,666.7reads/s.304responses still cost requests. Use bounded jitter/coalescing/materialized reads and include actual polling policy in the manifest |
| Renewals/reconnects |Independently measure retry amplification, expired asset/auth tokens, synchronized renewal cliffs, multi-tab churn and return-from-background traffic |
| Mixed traffic |Catalogue/search, staff operations, report reads, annotations, backups, telemetry and hostile/invalid traffic receive explicit quotas and measured overlays |

Do not double-count or omit headroom. Declare exactly which overlays are simultaneous and whether their rates already include retry factors. Content cache-hit ratios reduce origin demand, not viewer bandwidth or authorization obligations. Cold and warm campaigns are separate.

## 3. Guide-backed proposed acceptance targets

Source: PDF-05 p55,61–62. All are **targets awaiting qualification**.

| SLI | Proposed gate | Measurement boundary |
|---|---|---|
| Valid commit acknowledgement |p95≤300ms; p99≤1,000ms |In-region server ingress through queueing/validation/lock/DB durable commitment to acknowledgement. Not just handler CPU time or queue insertion |
| Durable submission receipt |p99≤2s under declared submit burst |Ingress to durable terminal receipt/seal-state acceptance; not PDF completion |
| Correct core grade readiness |p95≤60s; p99≤120s |Durable submission receipt to correct frozen core grade available. Includes grade queue wait and execution |
| Server errors |≤0.1%overall **and in each predeclared critical window** |Distinguish infrastructure/server errors, expected business rejections, admission denials and cancellations. Overload failures of valid admitted operations cannot be hidden as harmless429s |
| Integrity |Zero violations within covered failure envelope |No wrong grades, duplicate score effects, lost acknowledged commits, wrong version/canonical mapping or forbidden source/key release |
| Covered AZ loss RPO |0, only with verified synchronous durable persistence |Reconcile acknowledged receipts against recovered durable truth. No standalone/asynchronous shortcut |
| Regional disaster |RPO≤5min; RTO≤60min |Guide proposal; declare nonzero async-loss risk. RTO includes detection, exclusive writer fencing, restore, key/object validation, routing and authorized essential-API usability |

Freeze per-cell as well as global evaluation, the whole run, named start/submit/expiry/renewal windows and rolling windows (initial proposal5minutes). Never remove a failed window after observing results. Merge compatible latency histograms; do not average p99values across generators/cells. Publish tail latency and actor journey failures, not only HTTP success counts.

## 4. Additional proposed client/export budgets

These are planning proposals, **not numbers claimed from the PDFs**. Product/operator approval and representative measurements are required before they become exit criteria; if infeasible, make an explicit scope/SLO decision instead of claiming success.

| Experience | Initial proposed budget | Conditions / guardrails |
|---|---|---|
| Browser responsiveness |INP p75≤200ms; CLS≤0.1 |Agreed low/mid-range mobile and desktop profiles; real accessible mathematics and large-number inputs |
| Initial route experience |LCP p75≤2.5s on the agreed normal-mobile profile |Measure cold and warm separately; publish precise bandwidth/RTT/loss/CPU/cache definitions, not a vague “4G” label |
| Prefetched local question navigation |p95≤150ms; p99≤300ms |Only navigation not waiting for a required durable transition; never relabel server-dependent Save&Next as local-only |
| Student-observed save feedback |p95≤1.5s; p99≤3s on agreed normal connected profiles |Actual click→visible durable acknowledgement including network. Slow/offline profiles get truthful pending/recovery states, not a false saved badge |
| Complete PDF readiness |p95≤5min; p99≤15min from accepted export request |Includes queue wait/render/publish for the declared full paper mix and **all500k request** scenario. Grant/embargo may delay when export can lawfully be requested; do not start this clock only when a worker picks it up |
| Export/read traffic impact |Critical commit/receipt SLOs still pass |Grade, analytics and PDF workers/pools are separate; optional exports never steal answer-write resources |

A75-question example with100pages/report and500kexports produces50million pages. Finishing all within900s would require≈55,556pages/s; this is an illustrative sizing calculation, not the mathematical consequence of a p99target or a measured renderer capability. Benchmark reusable templates, personalization, storage and delivery before buying capacity. Publish actual achieved service, costs and shortfalls.

Proposed status polling must use server-directed backoff/jitter and a measured read budget; a minimum steady interval around30s is a starting proposal, not a hidden requirement that students see instant grades. Include initial result reads, manual checks and ready-to-visible delay explicitly. Optional persistent push channels require their own connection/authorization/failure proof; they are not free capacity.

## 5. Resource budgets and overload policy

Packet01/04 must freeze numeric per-schema/body/field/count/page/pixel/CPU/memory/concurrency/deadline budgets from a representative corpus. Initial upload guard proposals: one file/request,50MiBfile cap,52MiBtotal request cap,64KiBnon-file field cap and a small explicit field-count allowlist. Larger approved sources require a reviewed ingestion profile—not silently raised/unbounded limits. These are proposed limits, not a claim that current multipart enforcement works.

Reserve capacity by lane: **admitted commits/sealing first**, then lease/control essentials and core grading, then normal reads, then optional analytics/search/exports/telemetry. Drop/defer optional work explicitly; never drop a durable admitted command or display a cache write as saved. Missing telemetry becomes unavailable analytical evidence, not invented observations.

Admission depends on measured writer commit latency, pool wait, storage/WAL pressure, inflight work and pending registered commands—not API CPU alone. Stop new admissions before admitted attempts become unstable. Budget controls must never terminate admitted students to save money.

## 6. Node, database and failure sizing

For each service tier, with measured sustainable unit throughput μ and utilization factor u:

- Normal requirement: `n ≥ ceil(required_RPS / (μ × u))`.
- Separate30%equal-host-loss scenario: `floor(0.70 × n) × μ × u ≥ scenario_RPS`.
- Choose the maximum satisfying the declared scenarios; do not multiply blanket headroom twice. If μ was measured at the chosen utilization, use u=1.

Count physical host contention, database connection totals, storage/WAL/IOPS, standby capacity, object/KMS requests, network/NAT, LB/target limits, collector load and prewarming time. API-node survival is not DB-cell recovery. Twenty full cells do not magically absorb a lost cell's25kactive writers; restore/fence within that cell or use explicitly provisioned and tested migration capacity.

No machine counts or bill estimates are invented before benchmarks and dated provider quotes. Operators must reserve usable capacity/quotas ahead of the event; an autoscaling maximum or pending quota request is not readiness.

## 7. Exact qualification progression

Source: PDF-05 p58. Each stage needs reviewed evidence before promotion.

| Active actors | Minimum steady-state duration |
|---:|---:|
|1,000 |15minutes |
|10,000 |30minutes |
|50,000 |45minutes |
|100,000 |60minutes |
|250,000 |90minutes |
|500,000 |180minutes |

Additionally qualify a25kcell's baseline/2×mix and skew before fleet claims. This extra cell test does **not** replace the six stages. For final proof, all500k admitted attempts remain active throughout the180-minute steady period; warmup, preflight and admissions do not count. Use scheduled-start fixtures. Run submit/baseline overlap scenarios separately where necessary rather than terminating actors early and calling it a full180-minute active soak.

Three noninterchangeable tracks:
1. Stateful HTTP actors with independent expected response/receipt/grade ledgers.
2. Declared real-browser subset (guide example500–2,000) during saturation, with real devices/network profiles and accessibility interactions.
3. Measured connection/socket/handshake/churn inventory based on origin multiplexing.500kactors do not prove500kTLSsockets.

Arrival-rate generators must sustain offered load; report scheduled/started/completed/dropped operations and scheduler delay. An under-generated, interrupted or generator-saturated run FAILS. Cold, warm and fault scenarios retain separate results. Fault envelopes include lost replies, duplicate/out-of-order commands, expiry cliffs, stale writers, poison jobs, control-plane isolation, host/AZ loss, DBstall/quorum loss, cache/object/KMS failures, regional restore and telemetry overload.

## 8. Versioned run manifest and release decision

Record: source/image/SBOM/schema/config digests; exact DB/service versions; cell/resource/pool layout; actor ranges/seeds/exam mix; payload/asset sizes and cache states; intervals/dirty fractions/retry factors; official scheduling/cutoffs; browser/network profiles; connection inventory; SLO definitions/windows; fault scopes; evidence locations; cost/quotas; operators and approvals.

The final dossier includes per-actor reconciliation, histograms, pending/backlog age, WAL/replication/storage metrics, browser states, current key/package authorization, restore timelines and cost. No wrong grade or covered lost acknowledgement may be waived because latency looks good. Material code/schema/config/workload changes require requalification.

**Nothing in this document states that these targets have been achieved.**
