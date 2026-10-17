# Tejas: exactly 10 implementation packets

**Status: STRATEGY ONLY — proposed for approval. No packet implementation has started.**

## The contract

Build for **500,000 concurrently active exam attempts**, not registered users or idle connections. Preserve **matte maroon**, accessible light/dark modes, and **phone-number-only student entry without OTP/password**. Strengthen staff security separately. A phone profile is not verified human identity; do not claim proctored identity assurance or verified-person cohort counts under this choice.

Authority: all five supplied PDFs (177 pages), their verified source manifest, explicit user overrides, and the audit. The internal “40 analyses minimum” is wrong: **all 60 analysis contracts are required**. Current app/source state remains unchanged; original75-question paper is review-only and QA sets remain withdrawn.

**No launch/capacity claim while any required correctness, security, recovery or load gate is failed or unqualified.** “No lagging” means passing `SLO_AND_WORKLOAD.md`, not promising zero delay on every network or through unbounded disasters.

### Architecture we will build and qualify

- **Edge:** static frontend and authorized candidate-asset distribution; viewer authorization before protected cache hits; no source/key distribution.
- **Control/trust:** separate identity, entitlements, signed academic decisions, staff grants, catalogue and admission preparation. Admitted writes must not synchronously depend on a global allocator or analytics service.
- **Live cells:** reference layout20 independently qualified cells × at most25,000 active attempts, each with independent transactional writer/HA boundary, bounded API pools, local authority, outbox and reserved terminal capacity.20pods/databases sharing one writer do not qualify.
- **Batch/analytics:** autonomous, isolated extraction, grading, report, regrade and aggregation execution. Redis/caches/queues are not the source of acknowledged response truth.
- **Operations:** protected evidence, metrics, quotas, keys, backup/restore, incident control, deployment manifests and release decisions.

The reference live authority is **PostgreSQL with a specifically verified synchronous durability/failover configuration** because the guide specifies relational lock-time semantics. Final managed service, engine version, regions and sizing require operator selection and proof. Mongo may remain a segregated legacy/archive store during migration, not an assumed equivalent live-cell authority. Do not rewrite historical attempt truth or invent a cross-store transaction.

### Execution discipline

1. The packets below are dependency ordered. Each has implementation deliverables and explicit exit evidence. An implementation gate is not a500k qualification gate.
2. Packet01 first freezes atomic requirements/contracts and isolates existing red regressions. Their permanent owners are named below; containment is not called a fix.
3. Every later fix must pass its original failing sequence through a **new testing-agent report** plus regression checks. Tests must call real implementation; fixtures/mocks are labelled; a test reproducing a bug does not close it.
4. No production/student traffic uses an affected capability until its defect gates close. No automatic publication or simulated academic approval.
5. Observability, security, migration and cost evidence are added from the start, not postponed to Packet10.
6. Application engineers own code/contracts/tests. Authorized cloud/SRE/DBA/security operators own provisioning, DB-server configuration, IaC, CI/CD, SSL, capacity reservations and production deployments. Those infrastructure actions are outside this builder session's operational scope.
7. Existing preview `REACT_APP_BACKEND_URL` and `MONGO_URL` must not be rewritten. Future provider configuration is additive and operator-managed. All application APIs remain under `/api`; guide `/v1`/internal routes receive explicit compatible aliases, not broken ingress paths.

## Packet 01 — Authoritative Rules, Safety & Regression Baseline

**Depends on:** strategy approval. **Owners:** product/academic owner, application lead, QA, security operator.

**Build/deliver**
- Atomize every MUST/acceptance clause in the five PDFs into versioned requirements with owner, API/data contract, dependency, acceptance test and evidence location. The62audit rows and page index are starting coverage, not proof of complete atomic traceability.
- Correct rulebook errata; preserve all60analyses, all13operational WP gates and all12OPS-R release blockers. Freeze workload, SLO measurement endpoints, critical windows, supported device/network profiles and failure envelope.
- Publish the contract-first API/permission catalogue: strict input/output DTOs, field allowlists, canonical body hashing, typed errors, idempotency scope, ETags/If-Match, status/Location/Retry-After, payload budgets, UTC/monotonic clock units and exact marks.
- Establish repository/domain boundaries, real-function regression fixtures, independent expected ledgers, source integrity/SBOM baselines, secret-safe test output, isolated test data access and a requirement→test→artifact registry. Test repositories must fail closed if pointed at production namespaces.
- With explicit operator authorization, rotate the exposed persisted staff credential and revoke affected sessions. Merely updating a bootstrap environment value is insufficient. Contain unsafe upload/publication/job paths while their owning packets repair them; no public exam launch.
- Freeze source/role/retention/solution-release policies and the decision register in `QUALIFICATION_AND_HANDOFF.md`. Define cost/quotas and minimal metric schemas now.

**Interfaces/artifacts:** versioned OpenAPI/operation catalogue, data ownership map, requirement registry, workload/SLO manifest, regression corpus, incident record, release-blocker register.

**Exit gate:** owner-approved contracts and failure scope; zero orphan mandatory clauses in the detailed registry; all current findings have a red regression or explicitly unverified reproduction task; safe test isolation and credential containment evidence. **No defect is marked fixed merely because its test exists.**

## Packet 02 — Database & Live-Cell Foundation

**Depends on:**01. **Owners:** application/data engineers; DBA/SRE/cloud operators for provisioning.

**Build/deliver**
- Provision/design one nonproduction reference cell and separate control/trust stores, then define reproducible fleet topology. Verify exact primary/standby acknowledgement and failover semantics; never silently downgrade durability when a standby disappears.
- Define UUID identities and constraints for reservations, attempt ownership, writer generations, command log/receipts, committed responses, drafts, phase transitions, submission receipts, grade inputs and transactional outbox. Control data owns source/version/review/grant/decision records; analytics owns derived snapshots only.
- Use SQL uniqueness/CAS/locks for truth, append-only version/history records, time/hash partitioning justified by query patterns, bounded connection pools/wait, appropriate indexes, archival/retention and measured WAL/fsync/IOPS/vacuum/storage budgets. Pool totals across replicas/workers must fit a fleet DB budget.
- Build cell-routing/admission primitives and signed home-cell routing metadata. Pre-distribute pinned schemas/authorized versions and verification material; critical writes avoid global user/catalogue lookups. Freeze specific authority/freshness behavior during control-plane outages.
- Migrate safely: map legacy UUIDs, pack hashes, versions, source refs and receipts; reconcile counts/checksums/scores; shadow-read/grade; expand before contracting schemas. Existing attempts stay on one authoritative backend until safely drained. No unfenced dual writers or blind dual-write migration.
- Establish protected telemetry, backup/key/object inventories, restore environment and signed release/IaC requirements with operators. Add cache and analytics stores only as nonauthoritative dependencies.

**Interfaces/artifacts:** repository interfaces, SQL schemas/migrations, data-class/retention map, HA/failover contract, migration/rollback evidence, per-cell connection and storage budgets, operator topology manifest.

**Exit gate:** schema/constraint and migration golden tests pass; canary data platform and operational ownership exist; selected durability semantics and controlled failover tests are recorded. **This is not yet a25k-cell or500k qualification.**

## Packet 03 — Identity, Permissions & Locked Trust

**Depends on:**01–02. **Owners:** application/security engineers, identity/KMS operators, academic/legal owners.

**Build/deliver**
- Keep student phone-only entry, revocable secure sessions and profile disclosure. Bind authorization to tenant/profile/attempt/version; define abuse controls that work behind shared mobile NAT without blocking legitimate cohorts. Do not claim verified phone ownership or official candidate identity.
- Implement staff SSO/MFA, least-privilege capabilities, distinct author/reviewer/publisher/support/operator roles, session revocation and audited break-glass. Source/code/configuration/role-grant changes are protected operations too; “owner” is not a permanent bypass.
- Implement the guide's privileged step-up/PIN policy using protected credentials—not a shared PIN copied from the PDF. Issue one-use grants bound to actor, tenant, session assurance, resource/action, parent version, canonical diff/reason hashes and nonce; atomically consume with the protected operation.
- Separate encryption, signing and secrets purposes. Create canonical request/grant/result and manifest schemas, managed signing/verification, key rotation/survival, monotonic activation generations, independent approvals, supersession/revocation/correction lineage and current-authority checks. A valid historical signature is not proof that a release is still authorized.
- Establish separate workload identities for quarantine, extraction, draft editing, publication, scoring, delivery, signing and audit export. Viewer authorization and release/rights checks precede cache access. Define normal withdrawal versus emergency revocation for admitted attempts.
- Resolve privacy/retention/age-consent obligations, product telemetry opt-in/minimization, support access, exports/deletion and backup expiry. Under unverified phone entry, irreversible recovery/deletion policies require explicit approval; do not secretly add student passwords/OTP.

**Interfaces/artifacts:** permission matrix; identity/session/grant APIs; protected operation catalogue; signing/verifier services; key/retention/revocation runbooks; privacy and telemetry inventory.

**Exit gate:** cross-role/tenant/version access tests, expired/replayed/altered grant tests, independent approval tests and key-rotation/revocation tests pass; secrets never appear in fixtures/reports; student entry remains phone-only. Provider-backed controls must be real before a production gate passes.

## Packet 04 — Durable Workers & Safe Processing

**Depends on:**01–03. **Owners:** backend/processing engineers; queue/compute/security operators.

**Build/deliver**
- Replace browser/cron-dependent dispatch with autonomous managed queue delivery and dedicated workers. Use cell/control outboxes, bounded inflight work, fair scheduling, backpressure, retry budgets, delayed retry, dead letters, poison isolation and clear operator recovery. Recurring repair/cleanup uses the platform-managed scheduler; it is not the primary grader dispatcher.
- Isolate grade, extraction/OCR, rendering, reports, regrade and analytics CPU/memory/connection/identity pools. Define per-tenant/cell/operation budgets; optional work cannot take admitted answer-write capacity.
- Close **A05**: queued work drains when capacity becomes free without polling or maintenance intervention; failed early entries cannot starve later work.
- Close **A06** at the destination: generation/token and required lease validity participate in the authoritative output transaction/CAS. Checking a lease in a different store before writing is not fencing. Immutable artifact candidates may exist, but only the currently authorized generation can publish the pointer.
- Close **S01** and triage dependency advisories: enforce total request, file, field, count and concurrency limits before expensive multipart parsing. Quarantine untrusted PDFs, sniff actual types, reject active/embedded content, and run parsers with restricted network/credentials/filesystem, bounded expanded resources and hard kill/retry limits.
- Implement job schemas and handlers' integration boundaries. Grade logic is completed in06, analytics in08, final reports in09; a generic worker fixture does not certify those later handlers.

**Interfaces/artifacts:** durable job APIs/receipts, outbox relay/consumers, destination fence protocol, sandbox profiles, resource/cost budgets, queue health/age metrics and recovery tools.

**Exit gate:** original A05/A06/S01 regressions pass independently; worker-kill/lost-ack/duplicate/lease-handoff/poison/budget tests preserve truth and autonomous progress. No synchronous PDF/OCR work remains in interactive handlers. Physical isolation requires operator proof, not just process semaphores.

## Packet 05 — Content Sourcing, Catalogue & Publication

**Depends on:**01–04. **Owners:** content/backend engineers; named academic reviewers/publishers and rights owner.

**Build/deliver**
- Build quarantine→extraction→review→locked truth→delivery pipelines for raw questions, solutions, separately supplied keys and combined papers. Record original bytes/hashes, rights evidence, source role, 1-based/0-based page conversion, anchors, language, OCR confidence and processing provenance. PDF/AI text is untrusted data, never execution instructions or approval.
- Implement question/solution/stimulus blocks, taxonomy, exact pairing cardinalities, duplicate detection, anomaly/key adjudication, formula/diagram review, accessible text, locality-aware previews and review diffs. Shared passages and multipart solutions retain stable identities.
- Close **A03** through expected-revision edits; close **A02** through one atomic publication transition and unique version identity; close **A04/A04b** through enum/date/schema validation and fail-closed rights/audience/expiry checks on every path.
- Separate `source-private`, `candidate-safe`, `server-key` and `embargoed-solution` artifacts physically/by workload authority. Pre-render/build them once at approved publication; do not parse source PDFs or repack full papers on every student start or image request (**A07**).
- Produce signed versioned manifests tying content, key, adapter, response schema, rendering, locale and decision lineage. Keep source numbers separate from student slots. Freeze canonical/display option mappings; do not shuffle source-image options unless the approved rendering supports it safely.
- Deliver usable staff review/approval/publish/withdraw/correct/revoke/regrade workflows, publish blockers and source-authoritative diagnostics. Catalogue/search indexes are replaceable discovery projections, never grading truth.

**Interfaces/artifacts:** source/content/version APIs, editorial ETags, reviewer/publisher decisions, immutable manifests, safe asset builder, rights/audience and solution-release policies, approved source corpus.

**Exit gate:** independent A02/A03/A04 regressions and mixed-paper/pairing/LaTeX/diagram/locale/rights/security tests pass; concurrent operations cannot lose work or duplicate versions. The original75-question paper is not published until actual academic, accessibility and rights approvals are supplied.

## Packet 06 — Exam Engines, Durable Sessions & Exact Scoring

**Depends on:**01–05. **Owners:** session/scoring engineers and academic adapter owner.

**Build/deliver**
- Implement year/source-pinned **JEE Main, BITSAT, WBJEE and COMEDK** adapters from verified official material: sections, navigation, question counts/types, timers/accommodations, numeric syntax, multiselect/partial rules, bonus/invalid-item policy and BITSAT irreversible bonus transitions. Unsupported years stay unavailable; custom practice remains clearly separate.
- Atomically consume a signed owner-bound reservation, create one attempt/receipt and charge capacity. Freeze home cell, package, adapter, key, locale/display mappings and timing policy. Release capacity exactly once on terminal transitions; unconsumed reservation expiry cannot release an active slot.
- Close **A01** across ordinary starts, resumes and mistake retries: every successful operation key binds its complete canonical intent and durable outcome, including later replay after closure. Changed bodies/targets conflict; old receipts never overwrite newer accepted state.
- Implement explicit draft versus committed response semantics, all-or-nothing commit batches, single-writer generations, takeover, sequence/response-version rules and idempotent clears/review/phase changes. Return “saved” only after the engine's durable commitment—not cache or broker acceptance.
- At the attempt's fenced authority, acquire serialization lock then sample fresh authoritative time. Persist the complete admitted command and receipt; enforce the cutoff, seal the admitted watermark, drain/classify eligible work, and grade only the final committed snapshot. HTTP arrival time or local device timestamps do not establish deadline eligibility.
- Produce immutable exact-rational item/attempt ledgers asynchronously, with one score effect per attempt/key version. Preserve old grades, explicit approved correction versions and incident exceptions. Support reads/reporting must distinguish RECEIVED, APPLIED, SEALED, GRADING and READY.

**Interfaces/artifacts:** admission/start/lease/draft/commit/resume/submit/status/result contracts; command/receipt schemas; adapter registry; independent golden corpus; incident exception and regrade policy.

**Exit gate:** lost replies, committed-A/draft-B, clears, duplicate/no-change commands, stale writers, lock waits crossing cutoff, simultaneous submit/expiry, bonus transitions and reservation release all pass real-function/integration tests. Grade ledgers exactly reconcile. Cell-isolation/capacity qualification remains10.

## Packet 07 — Frontend, Offline Recovery & Edge Experience

**Depends on:**01–06. **Owners:** frontend/accessibility engineers; CDN/edge/privacy operators.

**Build/deliver**
- Complete the matte-maroon landing, catalogue, phone entry, practice home, instructions/preflight, exam workspace, history, staff console, support/privacy and error/empty/loading flows. Use consistent design tokens/Shadcn patterns, unique test IDs, keyboard/screen-reader semantics, safe focus and44px mobile targets; fix template branding.
- Close **F03** with one safe math renderer for typed stems/options/solutions and accessible equivalents. Validate long integers, locale changes, shared passages and image-heavy questions on supported devices; never trade content fidelity for speed.
- Build a versioned offline capsule using suitable durable browser storage: candidate-safe assets, pinned schema/mappings, local drafts and reconciliation metadata, never answer keys/unreleased solutions. Verify/quarantine malformed/null/old records (**F01**) and explicitly scope discard/logout actions with pending-loss confirmation (**F02**).
- Enforce multi-tab leadership/writer-generation UX, precise pending/saved/conflict/expired states, bounded buffers and explicit recovery after refresh, backgrounding, auth refresh, slow responses and lost acknowledgement. Timer truth remains server-owned and offline time does not pause it.
- Prefetch verified immutable candidate assets only when question-release policy permits. Scheduled exams may prefetch encrypted candidate packages with capacity-tested time-gated access. Renew asset/session authority without synchronized expiry cliffs; never extend the attempt clock merely because a link expires.
- Apply route splitting, current-question virtualization, bounded caches and main-thread budgets. Jitter/coalesce retries and status polling; count all304s, renewals and reads as workload. Capture versioned visibility/confidence/revision/review events needed for08 without making optional telemetry a write dependency.
- Deliver source-authoritative staff/support diagnostics, bookmarks/notes and accessible review interactions through their proper normal/queued lanes; never allow a stale index to authorize or change grades.

**Interfaces/artifacts:** student/staff route map, component/state-machine contracts, storage migration/recovery protocol, edge authorization and caching rules, client event schema, browser performance profiles.

**Exit gate:** actual desktop/mobile/tablet/keyboard/slow-network tests close F01/F02/F03 or keep them explicitly blocked; no silent draft loss or false “saved”; candidate/key separation and scoped cached access hold. Additional client budgets are in the SLO document and require approval.

## Packet 08 — All 60 Analyses, Cohorts & Study Plans

**Depends on:**01–07. **Owners:** analytics/data/frontend engineers; academic/privacy owners.

**Build/deliver**
- Implement **A01–A60**, not40cards: exact definition/version, inputs, denominator, evidence thresholds, output, interpretation, supporting-question drill-through and actionable next step for each metric. Close **A08**: unavailable evidence/zero denominators yield null with reasons, not invented zeroes.
- Build versioned visibility reconciliation, confidence/calibration, answer-revision impact, exposure, taxonomy, timing, longitudinal comparability, confirmed error causes and review histories. Observed visible time cannot exceed valid server elapsed time; missing observations remain explicitly missing.
- Stream authoritative grade/outbox events to isolated analytics stores; use idempotent contributions/retractions, preaggregated exact score histograms and materialized snapshots. No heavy cohort scans or joins on live attempt writers.
- Pin cohort eligibility to paper/item/key/adapter/mode/accommodation/exposure/time-window rules. Apply distinct-profile deduplication, minimum sample/privacy rules and complementary suppression. Use the guide's applicable thresholds, including privacy groups≥10 and percentile evidence≥100 where specified; distinguish privacy adequacy from statistical sufficiency.
- Preserve ties and fractional marks; never label platform percentiles as official ranks. Unverified phone profiles are not verified people; disclose cohort assurance and anti-abuse limitations.
- Deliver all results insight views plus reproducible7-day/30-day plans, prerequisite coverage, fresh review checks, notes/bookmarks/error notebook integration and honest evidence-specific unavailable states.

**Interfaces/artifacts:**60-entry feature/metric registry, versioned event/data contracts, golden datasets, cohort eligibility/suppression registry, materialized read APIs, study-plan/review APIs, regrade/replay reconciliation.

**Exit gate:** **60/60** positive applicable golden cases and missing/invalid-evidence cases pass; every ID has an implemented calculation, not a permanently unavailable placeholder. Duplicate/reordered/replayed/regraded events do not double-count; privacy and snapshot consistency pass. Full500k analytics isolation is qualified in10.

## Packet 09 — Results, Released Solutions & PDF Reports

**Depends on:**01–08. **Owners:** results/report/frontend engineers; publication/privacy operators.

**Build/deliver**
- Bind UI, question review, subject/topic/time/cohort insights, correction comparisons, study actions and exports to the same immutable grade/content/metric/cohort snapshot identities. Paginate detailed review; never recompute from current editable keys.
- Release solutions only when both attempt policy and the signed release/rights policy allow it. In scheduled/shared papers, submission alone must not bypass embargo. An interim receipt/score view is not falsely labelled a complete solutions report.
- Build full source-faithful PDFs including every attempted/eligible question in the student's actual order, their response, key/marks and exactly matched approved solution, with version/provenance/incident metadata and defined accessibility/readability standards. UI filters do not silently remove questions from a complete export.
- Reuse reviewed rendering/templates, cache immutable snapshots, single-flight duplicate jobs and publish fenced immutable report pointers. Preserve original report bytes after correction; generate clearly labelled successor exports.
- Provide authorized version-specific downloads through scalable delivery rather than loading every large PDF through API memory. Test expired/revoked tokens, range/retry behavior, cross-profile isolation and cache authorization. Protect solution-consultation/exposure telemetry feedingA56–A60.
- Treat **all500k students requesting reports** as a workload scenario, not an assumed10%subset. Separate API receipt latency, grade readiness, PDF generation wait and download bandwidth. Show honest progress/retry states while isolated export workers run.

**Interfaces/artifacts:** immutable result/report snapshot contract, released-solution APIs, queued report/status/download APIs, safe delivery manifests, source-render parity corpus, export throughput/cost worksheet.

**Exit gate:** complete question–solution pairing, screen/export parity, embargo/access/grade-version tests and real75-question/full-length/large-render PDF cases pass. Proposed export budgets require measured capacity; missed PDF SLOs cannot be hidden behind fast job-creation responses.

## Packet 10 — Full-Scale Qualification, Recovery & Operations

**Depends on:**01–09. **Owners:** QA/performance engineers, SRE/DBA/security operators, academic/product signatories.

**Build/deliver**
- Freeze the actual deployment/image/dependency/schema/package/adapter versions, resources, quotas, cost approvals, workload and failure scopes. Use dedicated nonproduction test capacity; never unleash500k traffic on this shared preview.
- Execute the guide's exact six stages: **1k/15min →10k/30min →50k/45min →100k/60min →250k/90min →500k/180min**. Warmup/admission is outside the final180-minute proof. Qualify the individual25k-cell envelope additionally; do not substitute it for these stages.
- Use independently reconciled stateful HTTP actors, a declared real-browser subset (guide example500–2,000) and separate observed-topology connection/churn tests. Arrival-rate demand must not fall when the service slows; fail saturated generators, dropped scheduled traffic and averaged localp99s.
- Test baseline,2×normal mix, pathological drafts, starts/submissions overlapping baseline, cold/warm assets, renewal/reconnect storms, status polling, all-report demand, hot-cell skew and platform quotas. Prewarm known waves; test30%API host loss and AZ/database/cell/control/queue outages separately.
- Verify exact accepted payload/sequence reconciliation, grades, destination fences, source/key safety, privacy and snapshot parity. Test alerts/collector failure with bounded labels; optional telemetry loss cannot masquerade as healthy monitoring.
- Run database/AZ failover, corruption and regional restoration at representative volume, including usable keys, manifests, receipts/outboxes, routing and writer fencing. Record actualRPO/RTO and affected windows; never claim zero regional loss for asynchronous replication.
- Complete signed IaC/image/SBOM/release artifacts and backward-compatible canary/rollback rehearsal with operators. Keep active pinned attempts compatible; drain before removing old schemas/leases. Publish cost/admission ledgers, support/incident runbooks and an operator-owned readiness decision.
- Retain **WP01–WP13 in order** and every **OPS-R01–OPS-R12** gate as internal checkpoints; these do not add top-level packets. See `QUALIFICATION_AND_HANDOFF.md`.

**Interfaces/artifacts:** signed run dossier, raw histograms/actor reconciliation, browser/connection evidence, fault/restore reports, quota/cost exports, release manifest, blocker register, incident/support playbooks, operator readiness APIs.

**Exit gate:** all mandatory gates PASS for the exact declared deployment and workload, including500kdistinct active attempts for180minutes, SLOs and covered-failure integrity. Any FAIL or UNQUALIFIED blocks the capacity claim. Only then may an authorized operator approve a staged production launch.

## Cross-packet closure rules

- API, data, security, privacy, performance, migration/rollback and observability checklists apply to **every** packet.
- Each packet produces versioned design/contracts, implementation artifacts, exact tests, independent verification and known limitations. No source change inherits an old qualification automatically.
- Full requirement completion requires both its owning packet and its qualification packet to pass. A provisioned DB, a queue demo or60empty cards is not compliance.
- Coverage is in `coverage_manifest.json` and `COVERAGE_MATRIX.md`:62audit requirements, every named finding/risk/erratum,60analyses,177source pages,13WP checkpoints and12release gates. Packet01 expands page-level ownership into atomic clauses before implementation.
- No timeline, node count or cloud bill is invented here. Operator quotes, representative benchmarks and decisions determine capacity and schedule. These10packets are unequal gated milestones, not a promise that10short coding steps produce500k readiness.
