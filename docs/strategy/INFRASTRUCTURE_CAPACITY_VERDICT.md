# Infrastructure and capacity verdict — 17 October 2026

## Verdict: UNQUALIFIED_500K
The visible preview is a development environment, not a proven 500k exam platform. It is **not suitable as the sole production topology** for that requirement. No claim is made about platform infrastructure outside this container, autoscaling policies, quotas, load-balancer fleets, or production regions that are not visible here.

## Read-only observations
| Observation | Evidence / implication |
|---|---|
| CPU quota | cgroup `cpu.max`: 200000 /100000 =2 CPU |
| Memory cap | cgroup `memory.max`:8589934592 bytes =8GiB |
| Colocation | supervisor shows API, frontend development server, MongoDB and preview proxy in this environment |
| MongoDB topology | `hello` shows writable standalone; no replica-set name or router; no replicated failover proof |
| DB pool | Application has bounded pool/wait configuration; bounds prevent unbounded waiting but do not manufacture throughput |
| Durable semantics | majority+journal write concern is requested; standalone journal acknowledgement does not establish multi-AZ durability |
| Work queues | Bounded pilot-level workers; source rendering/report generation require separate measured budgets |
| Frontend server | CRA development server is not the desired production asset-serving tier; residual security advisories exist |

No Kubernetes/Docker/server configuration, database administration, SSL, CI/CD or production deployment changes were performed.

## Implemented low-risk application improvements
- Studio book polling uses a minimal projection, cutting measured BSON transfer by97.1% across94 chapters (5,793,146 ->167,977 bytes).
- Catalogue returns newest practice attempt per visible chapter via indexed per-set aggregation. Old arbitrary200-row history cap could hide another chapter's active attempt.
- Preflight source checks deduplicate exact repeated regions inside one request; authorization and all unique-source validation still run, without a shared cache.
- Inline source display uses one original-image fetch, not hidden-image plus canvas duplicate requests.

## What was actually measured
Latest `test_reports/capacity_catalog_smoke.json` is40 HTTP requests against public chapter catalogue, at a global start-rate <=5rps and at most4workers, all successful. p95=107.89ms and p99=229.38ms, measured client-to-preview including network/ingress. Percentiles use nearest rank across completed successes AND failures/timeouts. No survivor-only metric. With only40 samples, p99 is effectively the maximum and is not a tail-latency qualification.

This is NOT:
- 40 simultaneous students or500k browsers;
- authenticated autosave throughput;
- a saturation/maximum capacity result;
- a submit or grading-burst test;
- an AZ failure, failover, restore or lost-acknowledgement test.

Do not extrapolate replicas linearly from this smoke. The existing capacity calculator remains planning-only and qualified_active_attempts remains unset.

## Workload grounding for current 50-question/60-minute product
Arithmetic, not measurements:
- 500,000 students x50 answer events /3600s =6,944 answer events/s if uniformly spread and answered once.
- Each visited question may also cause a server visit request; marked/changed/cleared responses add traffic. Saves are debounced350ms on edit, not an unconditional30s server write.
- Starts over120s:4,167 starts/s plus preflight/auth/source requests.
- Submissions over30s:16,667 submissions/s, followed by grading/results/report demand.
- Source image demand can approach25million question image reads across a complete session; actual byte size, browser caching, revisits, cold rendering, network and authorization cost need measurement.
- Existing generic SLO workload equations include other proposed lease/telemetry schedules; those must not be mislabeled as measurements of this exact UI.

## Required qualification path (operator-owned infrastructure; not provisioned here)
1. Freeze representative topology/budgets and build a production asset tier. Keep question/key assets private and authorization-correct; never use public CDN URLs for protected keys.
2. Separate stateless admission/save/submit handling from source rendering, reports and analytics workers. Bound queues and preserve accepted-write receipts under saturation.
3. Establish measured replicated database durability, indexes/partitioning, connection budgets, backup and tested restoration. Sharding/cells need workload evidence, not arbitrary replica counts.
4. Run distinct-user stateful staged campaigns on dedicated infrastructure:1k,10k,50k,100k,250k,500k; actual auth, starts, edits, offline reconnect, idempotent retries, submit, grade and report behavior.
5. Include synchronized bursts, long soak, cold/warm assets, stale browser revisions, worker loss, primary/AZ failure and restoration. Track p95/p99, offered vs admitted load,429/503, lost acknowledgements, cross-user leaks, grading correctness and queue age.
6. Reconcile every acknowledged save to immutable final grade; zero lost acknowledged answers, duplicate effects or pre-submit key leaks. Use SLO_AND_WORKLOAD.md as the acceptance source, not the small public-catalogue smoke.

## Current harness safeguards
`tests/load/catalog_smoke.py`: default40/max100 total requests;1..4workers; finite1..5rps global budget; only fixed public catalogue GET endpoints;10s request timeout;110s total wall bound; raw HTTP status/errors/Retry-After retained; malformed budgets rejected; incomplete/errors fail exit code; no authentication credentials. This is a safe replay tool, not the still-unbuilt full stateful500k campaign.
