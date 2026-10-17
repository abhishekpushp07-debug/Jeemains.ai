# Qualification, operator handoff and decision register

This is an appendix to the **exactly10top-level packets** in `TEN_PACKET_STRATEGY.md`, not additional packets. No infrastructure, cloud purchase, external message, credential rotation, deployment or application change is authorized by this strategy document alone.

## 1. Roles and responsibility split

| Owner | Responsibility |
|---|---|
| Product owner |Scope/SLO/failure-envelope approval, student phone-only trade-offs, launch decision and disclosed limitations |
| Academic owner + independent reviewers |Official-year evidence, source rights, exact pairing, taxonomy, accessible content, anomaly/key policy and independent publish/correction approval |
| Application engineers |Domain boundaries, typed APIs, repository interfaces/migrations, session/scoring/content/UI/analytics/report logic, instrumentation and isolated regression tests |
| QA/performance engineers |Independent expected ledgers, real-function regressions, honest mock labels, generator/browser/connection evidence and complete acceptance coverage |
| Cloud/SRE/DBA operators |Actual DB/server/network/worker/CDN/WAF/KMS/backup provisioning; quotas/prewarming; IaC/CI/CD/SSL; production deployment, failover and restore operations |
| Security/privacy owner |Staff assurance, grants/key custody, audit/retention/legal policy, telemetry minimization, incident response and exposed-credential rotation |

The builder must not quietly administer infrastructure, change existing environment connection values or perform production deployment. Missing operator capacity/credentials/evidence is an explicit dependency, not an application implementation success.

## 2. Decisions to freeze before their dependent packet

| Decision | Required before | Required evidence / constraint |
|---|---|---|
| D01 scope, exact SLOs and covered failure modes |01exit |Guide-backed targets plus approved extra client/PDF targets; no silent weaker substitutes |
| D02 cloud/provider, region/data residency and accountable operators |02start |Current official support/limits, latency/legal needs, dated quotes, access responsibilities |
| D03 exact PostgreSQL HA/replication/failover variant and migration policy |02exit |Durable acknowledgement semantics, standby/read/failover behavior, writer fencing, rollback and legacy protection. No generic “Multi-AZ” promise |
| D04 staff identity/MFA, managed signing/secrets and PIN policy |03start |Provider selection, secure credential channels and lifecycle. No credentials in reports or code |
| D05 academic authority, official years, paper rights, independent reviewers and release/embargo rules |05/06start |Verified current primary sources and actual human approvals; unsupported years unavailable |
| D06 resource budget, quotas, per-cell specification and synthetic-test spend |02/10 |Operator approval, usable quota reservations, provider limits, measured unit curves—not guessed node counts |
| D07 device/network/browser and export-demand profiles |01exit,07/09freeze |Exact bandwidth/RTT/loss/CPU/cache definitions; full500kexport scenario acknowledged |
| D08 privacy/consent, retention, source PIIdetection and product telemetry |03exit |Legal/operator-approved matrix; privacy-managed learner records separate from locked academic artifacts; review PostHog configuration with platform owner |
| D09 writer takeover, account recovery and irreversible deletion under phone-only access |03/06exit |No implicit verified-person promise; student login stays phone-only; destructive support actions need an approved assurance policy |
| D10 outage fairness/remedy, regional loss disclosure and incident authority |06/10 |Auditable approved exceptions; no silent deadline rewrite or invented restored answers |
| D11 credential containment |01 |Authorized persisted-account rotation and relevant session revocation; the audit's redaction is not credential rotation |

Service/model/library versions must be verified against current provider guidance before integration, with proper playbooks and credentials collected securely. No provider keys are requested or used merely to write this strategy.

## 3. Preserve all13operational work packages inside the10packets

PDF-05 p65–66 names13**sequential operational gates**. Build prerequisites in the owning packets, then retain formal WP01→WP13 verification/signoff order in the qualification dossier. This preserves the guide without creating13top-level implementation packets. Release artifacts must be generated/pinned before tests; WP12 verifies the **same tested artifacts**, not newly rebuilt untested images.

All example routes below are contract examples to map under `/api` (e.g. `/api/v1/...`, `/api/internal/...`) with explicit legacy aliases. Internal operations are operator-authenticated and not student-accessible.

| Gate | Deliverable / check | Artifact builders | Formal verification |
|---|---|---|---|
| WP01 |Workload/SLO manifest; internal capacity profile; arithmetic/time boundaries |01,02 |10, before traffic qualification |
| WP02 |Independent actors, adapters/options, expected response/grade fixtures; starts |01,05,06 |10 |
| WP03 |Durable commit tests; lost ack, clears, duplicates; accepted-payload reconciliation |02,06 |10 |
| WP04 |Distributed generators/run status; actor partitions/offered load/scheduling capacity |01,10 |10 |
| WP05 |Start/submit/cold-cache/expiry overlap and recoverable receipts |06,07,09,10 |10 |
| WP06 |Nonproduction fault suite; AZ/DB/queue/control outages and receipt reconciliation |02,03,04,06,10 |10 |
| WP07 |Dashboards/collector health/alarms; bounded cardinality and collection overhead |01–09 |10 |
| WP08 |Restore/failover; usableKMS/packages, exclusivewriterfence, rational rescore, actualRPO/RTO |02,03,06,09,10 |10 |
| WP09 |Cost/admission ledger; quota/budget controls protect admitted students |01,02,04,06,10 |10 |
| WP10 |A01–A60registry, versioned reports, unavailable states, embargoes/cohort revisions, no hot analytical scans |05,07,08,09 |10 |
| WP11 |Staff/support source-authoritative diagnostics and cell-aware receipt APIs; stale-index tests |03,05,06,07,09 |10 |
| WP12 |Operator-reviewedIaC; signed images by digest/SBOM; compatible migrations/rollback |01–09 plus operators |10, matching already-tested digest/config |
| WP13 |Six-stage dossier/blocker register;500k/180minute evidence and named operator signoff |All10packets |10, last |

## 4. Keep all12production-blocking gates

Source: PDF-05 p67–68. Every gate has a named operator, artifact references and retest triggers; **FAIL or UNQUALIFIED blocks the capacity/release claim**.

| Gate | Pass condition |
|---|---|
| OPS-R01 |500,000distinct active actor ledgers for180steady minutes, not idle users |
| OPS-R02 |Intended offered demand; unsaturated generators; correct public-edge path; merged histograms; no hidden dropped traffic |
| OPS-R03 |Zero wrong grades, duplicate score effects or committed-A/draft-B violations; every accepted payload reconciled |
| OPS-R04 |Covered crash/AZ failures preserve acknowledged truth beyond volatile caches/queues |
| OPS-R05 |Start, submit, cold-cache, expiry and reconnect windows meet declared gates, not just a global average |
| OPS-R06 |Exclusive writer fences, usable keys and validated restored version truth; no split brain |
| OPS-R07 |Measured regionalRPO/RTO with explicit asynchronous-loss scope and reconciliation before grade release |
| OPS-R08 |Report/cohort/grade snapshot consistency, embargo enforcement and no duplicate contributions |
| OPS-R09 |Bounded metric labels, complete durable receipt evidence, working alerts and collector-health truth |
| OPS-R10 |Qualified reservations, approved quotas/test costs and budget controls that do not terminate admitted students |
| OPS-R11 |Signed digests/SBOM/reviewedIaC and compatible rollout/rollback; no ungated production source changes |
| OPS-R12 |Auditable incident exceptions and source-authoritative support; no silent time rewrites or stale-index grading |

## 5. Audit findings and permanent closure owners

All remain **OPEN** until implementation and independent verification. Packet01 captures the exact regressions and applies only explicitly authorized containment.

| Finding | Primary repair packet | Required proof |
|---|---:|---|
| A01 retry-resume key reuse |06 |K1→R1;K2resumesR1;closeR1;K2replayreturnsR1;changedintentconflicts |
| A02 same-version publication race |05 |Concurrentpublish yields one transition/archive identity; replay outcome stable |
| A03 reviewer lost update |05 |Staleexpectedrevisionconflicts and preserves first edit, including different-question edits |
| A04 audience fail-open; A04b expiry validation |05 |Unknown/invalid/audience/date failsclosed on creation/update/read; validrestricted behavior preserved |
| A05 idle queue; A05b recovery fairness |04 |Queued work drains without polling; poisoned/failed head entries cannot starve later work |
| A06 stale extraction writer |04, integrated05 |Leasechangeaftercheck/beforewrite cannot publish; destinationauthorityenforced |
| S01 multipart/resource gap |04 |Actualmultipart(nonfile/file/count/total)limits enforce before expensive work; legitimateuploadswork |
| F01 malformed local state (unverified) |07 |ActualPlayerbrowsernull/primitives/malformedrecordrecovery; not just a language expression |
| F02 logout draft scope |07 |Explicit current-profile discard; no silent other-profile loss; pending warning/recovery |
| F03 typed option math |07 |Safe correct math/accessibility on all supported viewports and hostilemarkupfixtures |
| A07 live-path parsing/packing work |04/05 |Publishedassets/packagesreused; no sourceparse/repack on live start/read path; measured event-loop budget |
| A08 zero-denominator metrics |08 |Null+typedunavailable reason where defined; positive/missing evidence goldens |
| Exposed audit credential |01 operator |Actual persisted credential/sessionrotation proof; no secret values in output |
| Dependency advisories |01 triage;04/07 closure |Current advisories/SBOM, exploitability/risk decision, compatible fixes and regression tests; no unreviewed critical exploitable path at release |
| Undisclosed/unreviewed instrumentation |03 policy +07 integration |Approved privacy/consent/minimization and platform-supported configuration; protectedcontent excluded |
| Template title, touch targets, inconsistent controls/testIDs |07 |Approved branding,44px targets, keyboard/screen-reader checks, stable unique IDs |
| Harness isolation and false pass claims |01; enforcedeverypacket |Real implementation calls, fail-closed isolated repositories, independentoracles, scopedproof, credential-safeartifacts |

## 6. Evidence package required for every packet

- Approved source clauses and explicit accepted overrides; no orphan requirements or hidden deferred fixes
- Input/output, permission, data-owner, versioning, concurrency and idempotency contracts
- Implementation and dependency digests, migration/backward-compatibility and rollback plan
- Golden inputs, independent expected outcomes, negative tests and real-function/browser/integration evidence; clear **MOCKED TEST DATA** labels where appropriate
- Original failing audit regression plus **testing-agent** verification for every repaired issue
- Performance/resource/cost evidence appropriate to the packet; no scope inflation into500k claims
- Privacy/security/dependency checks, observability and operator runbook; no raw credentials or unnecessary student data
- PASS/FAIL/UNQUALIFIED status, unresolved blockers, owner and explicit promotion decision

Infrastructure, cloud accounts, quota approvals, cost funding, identity/KMS selections, independent academic reviewers and a representative corpus cannot be replaced by code or a screenshot. If any prerequisite is unavailable, mark the corresponding gate blocked rather than calling the packet fully delivered.
