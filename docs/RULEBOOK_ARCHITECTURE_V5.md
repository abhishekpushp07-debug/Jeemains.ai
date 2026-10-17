# Tejas — binding engineering rulebook

Status: prioritized application hardening implemented and tested; **NOT qualified for 500,000 concurrent exams**. The full infrastructure and five-PDF specification remain incomplete; see the gap matrix and verification record.
Source pack: five supplied PDFs, byte hashes, original URLs and page counts in `source_guides/manifest.json`. Extracted text accompanies each file; references below use PDF page numbers. Record evidence, never replace a failed gate with a claim.

## 1. Precedence and non-negotiables
- Verified official-year evidence outranks examples; only an approved versioned exam profile may claim official behavior (V1 pp1,26; V2 pp2,24–25). Current custom practice is NOT full official simulation.
- Latest user decisions supersede older visual/login guidance: **matte maroon**, phone-number-only student entry, no OTP/password. Phone entry is a convenience profile lookup, NOT verified ownership; anyone knowing the same phone can enter that profile. Never elevate such a session to staff. Staff password authentication remains separate; required SSO/MFA and transaction step-up are NOT implemented.
- `/api` is the platform routing boundary. Current v1 JSON envelope uses `meta.api_version=1`; `/api/openapi.json` is actual generated schema. Do not introduce bare `/v1` paths that bypass ingress. A full pinned contract + operation policy catalogue is still required (V5 p28).
- UUID business identities; UTC time. No raw credentials, student answers, tokens, PINs, private source text or signed URLs in logs. Protected content authorization happens before any cache lookup.
- Persist drafts as pending until acknowledged. Under current explicit **custom autosave practice policy**, acknowledged saves are scoring-eligible. Do NOT label this the V2/V5 official explicit-commit protocol. No silent policy change for existing attempts.

## 2. Five planes, not a renamed monolith (V5 pp2,44–45)
1. **Edge**: static frontend, WAF, authorized private candidate-safe assets; thin route to stable attempt home.
2. **Control + trust**: identity, entitlement, signed activation decisions, admission permits; isolated source vault and locked truth.
3. **Live cells**: propose 20 independently qualified cells × 25,000 attempts. Each needs its OWN writer, HA arrangement, bounded pools, queues, reserved terminal capacity and dashboards. Twenty pods sharing one writer is not twenty cells.
4. **Batch**: isolated OCR/extraction, grading, versioned analytics, reports. OCR cannot consume live response-write or grade capacity.
5. **Operations**: identity/KMS, observability, audits, backups, restore, incident controls.

The preview is ONE FastAPI/Mongo deployment with in-process bounded pilot job execution. Per-domain files and semaphores are code boundaries, not independent failure domains. Existing-attempt writes currently still depend on this database for session checks. Do not claim control-plane outage independence.

## 3. Acceptance, idempotency and terminal truth (V2 pp13–18; V5 pp7,10,29–31,49–50)
- Scope every mutation key to actor + operation + target + version/preconditions; hash the complete canonical body. Identical retry returns original durable outcome, even after newer saves or expiry. Changed body conflicts. Validation failures before acceptance do not reserve a key.
- Current practice implementation uses Mongo single-document conditional updates to atomically persist accepted response, command receipt and monotonically increasing sequence. Preserve compact historical receipts for the attempt lifetime. This is NOT proof of PostgreSQL lock-time semantics or multi-AZ acknowledged durability.
- Close must atomically stop future saves, retain the accepted sequence watermark and create an embedded durable grading outbox marker. Retry never restarts the clock or changes the sealed answers. A crash between close and job enqueue must be repairable from that marker.
- Submit acknowledgement confirms a sealed submission, not a computed grade. Return `202` for durable pending grading with receipt, Location and Retry-After. UI says Submitted/Preparing results; no invented zero score. PDF and analytics failures cannot undo accepted answers.
- Production reference: attempt-scoped fenced authority; acquire lock, then sample fresh authoritative time (`clock_timestamp`, not transaction-start `now`); append authenticated full commands and advance contiguous sequence atomically; seal/drain watermark before FINAL. Pre-cutoff HTTP arrival is not acceptance. Writer takeover must persist generation and fence old writers. These reference requirements are still unimplemented; Mongo `$$NOW` CAS is not asserted equivalent under lock waiting/failover.
- Admission reservation consumption, attempt creation, receipt and slot counters must be one transaction. Capacity release exactly once. Never reroute active writers as ordinary load balancing. Current preview does not implement this distributed admission protocol.

## 4. Source and content contract (V3 pp1–23; V5 pp11–27)
- Keep four distinct artifact/release classes: `source-private`, `candidate-safe`, `server-key`, `embargoed-solution`. Never send a combined source PDF or hidden key to an active client. Current allowlisted payloads enforce API withholding, but separate workload identities/storage encryption boundaries are NOT provisioned.
- Preserve source bytes, SHA256, owner, source role, rights evidence, source anchors and approved pairing. Question numbers are local to paper/section, not global IDs. Existing crop coordinates use human 1-based pages; any zero-based ingestion format must convert explicitly.
- Untrusted PDF/OCR text is data, not instructions. Reject active features, embedded payloads and oversized decoded resources; no document-directed fetching. Bound job pages, pixels, memory, attempts, deadlines and per-tenant concurrency; run full parsers in isolated production compute. Current PDF validation is not a sandbox.
- Academic approval, rights/audience/expiry, reviewed accessible content and exact question–solution matching are independent publish gates. AI extraction never grants approval. Original guide PDFs are specifications, not automatically publishable exam content.
- Locked truth is append-only; edits create successor versions, invalidate affected approvals, retain historical manifests and report lineage. Activate via payload-bound, independently approved, signed decisions. Current hashes/version snapshots are not a KMS signature or WORM retention lock.
- Separate author/reviewer/publisher responsibilities. No single generic admin capability should bypass these. Staff MFA + scoped one-use transaction grants must precede production activation; never embed a default PIN in code or documentation as a live credential.

## 5. Hot-path/resource contract (V5 pp46–52)
- No PDF parsing, report generation, regrade or analytics inside live mutation handlers. Lightweight seal first, durable outbox, separate batch execution.
- Visits/history query compact projections, not question/key packs. Bounded pages; no unbounded scans on live paths. Catalogue searches are capped, but unindexed regex search needs measured scale replacement.
- Bound database connections AND pool waiting across the whole fleet. A per-process cap multiplied by autoscaling is not a fleet budget. Keep DB commit/replication latency distinct from API health.
- Default acknowledged writes must not silently degrade durability. Majority/journal configuration is an application request, not evidence of multi-AZ replication or RPO zero on standalone Mongo.
- Private immutable caches are rebuildable, byte-bounded and nonauthoritative. Cache key includes immutable source digest, crop, render version and release class. Always authorize caller first. Local cache is not a distributed CDN.
- Separate job lanes; atomic leases, fenced completions, immutable per-lease outputs, bounded attempts, visible failure. Bulk work cannot silently reset successful jobs. No unbounded application timer/worker loop; existing platform cron is a recovery safety net, not a low-latency 500k dispatcher.
- Exponential retry with jitter + Retry-After. Client queues coalesce unsent practice edits by question, retain pending drafts and stop automatic mutation on conflict. Do not falsely acknowledge rejected/late data. Deadline polling must not become a synchronized 1-second storm.

## 6. Analytics and exports (V4 pp1–4,19–23)
- Immutable exact grade ledger feeds results and PDF. Use rational arithmetic until display. Approved correction makes a separate grade/report, never overwrites original bytes.
- **All 60 numbered analyses are mandatory**, with typed informative unavailable states when evidence is missing (V4 p1; V5 p64). There is no 40-analysis minimum substitute. Current limited metrics are not 60 completed contracts/views. Mark missing evidence; never fabricate percentile/rank, timing or cohort values.
- Cohort identity pins paper/profile/key/mode/timing/exposure/date-window. Privacy minimum proposed 10 distinct learners is NOT percentile evidence minimum 100; suppress complementary cells too.
- Versioned materialized reports/aggregates built asynchronously; no repeated analytical joins on live writer. Released solutions only; every export uses same grade/version as screen.

## 7. Security and operations gates (V5 pp13–22,28,53–68)
- Server ownership + field allowlists together, secure revocable cookies, CSRF/origin protection, scoped staff permissions. Password-only staff is a pilot control, not guide-compliant MFA.
- Secrets/KMS and content source vault are different systems. No raw secrets in manifests. Object-store credential access is not least-privilege identity separation.
- Separate live/grade/telemetry metrics with bounded labels; no user/attempt IDs as metric labels. Structured request correlation with sanitized logs. Health != readiness != tested capacity.
- Restore full receipt/outbox/version/object inventory with keys. Rehearse failover, quorum loss, AZ loss, regional restore, queue poison, source outage, cell saturation and schema rollback. Proposed regional RPO≤5min/RTO≤60min are goals, not current guarantees.
- No production capacity claim until workload, fault, durability, privacy and content gates have dated reproducible evidence.

## 8. Release evidence vocabulary
`IMPLEMENTED` means code exists; `TESTED` means executed evidence attached; `PROVISIONED` means infrastructure actually exists; `QUALIFIED` means workload/fault evidence matches a claimed envelope. None implies the next. See gap matrix and capacity model for actual status.
