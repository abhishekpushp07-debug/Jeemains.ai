# Requirement-to-code compliance matrix

**Scope:** five supplied PDFs + explicit user overrides. This is not a release certificate. PASS means only the narrowly stated row is supported; PARTIAL means a useful subset exists; FAIL means required behavior is absent or contradicted; NOT VERIFIED means evidence is missing or the relevant infrastructure is outside visibility. See `AUDIT_REPORT.md` for reproduced findings and evidence classes.

## Product, frontend and session behavior

| ID | Requirement / source | Status | Current implementation / evidence |
|---|---|---|---|
| R01 | Latest matte-maroon override, replacing V1 blue palette | PASS, scoped | `App.css`, `index.css`, `ThemeToggle.js`; real light/dark screenshots at1920×800 and390×844. Not a full contrast certification |
| R02 | Latest phone-only student entry, no OTP/password | PASS, user override | `phone.py`, `Auth.js`; explicit unverified-profile disclosure. Do not flag the deliberate lack of verified phone ownership as an accidental bypass |
| R03 | Separate student/staff authorization, V1 p10; V5 p9,13 | PARTIAL | Staff password/RBAC exists and phone profiles cannot elevate through staff flow. SSO/MFA and protected step-up absent |
| R04 | Full official-year adapters and versioned rule provenance, V1 p9; V2 p2,24–25 | FAIL | `profiles.py` pins custom profiles; only JEE MCQ/integer and BITSAT MCQ practice are implemented, not complete official-year engines |
| R05 | WBJEE/COMEDK and full BITSAT phase semantics, V2 adapter chapters | FAIL | Not implemented; no multiselect/partial-credit adapter or bonus-phase irreversible transition. These are specification gaps, not broken implemented menu items |
| R06 | Explicit draft/commit and navigation semantics, V2 p13–14; V5 p29–31 | FAIL | `answers.py` treats acknowledged saves as scoring-eligible under custom autosave. No complete separate explicit commit register |
| R07 | Final accepted response is authoritative, V2 p18 | PASS, scoped | Seven actual scorer fixture baselines in report29; submitted local pending data is not substituted into frozen marks |
| R08 | Body-bound durable save retries, V5 p29 | PARTIAL | Answer receipts and ordinary start aliases exist; retry-resume fails A01. No complete mutation-wide operation catalogue |
| R09 | Monotonic sequencing / post-lock authoritative cutoff, V5 p10,29–31,50 | PARTIAL | Per-attempt response seq + single-document Mongo conditions exist; no relational lock-time authority/contiguous admission register/drain protocol proof |
| R10 | Per-attempt writer takeover fencing, V5 p7,10,50 | FAIL | Revision conflict handling is not a writer generation or explicit takeover lease |
| R11 | No structured key/solution fields in active-question responses, V3 p3; V5 p12 | PASS, scoped | `attempts.py:question_public` allowlists candidate fields and guards solution kind. This does not prove approved image crops contain no answer information |
| R12 | Offline acknowledged-vs-pending recovery, V2 p17; V5 p41–42 | PARTIAL | Local drafts, reconciliation and conflict UI exist; report28 shows client timer continues offline. Full reload/offline-open capsule and every malformed-storage case not verified |
| R13 | Safe local-draft lifecycle across profiles, V2 p17 | FAIL | F02: logout clears every profile's draft key without immediate discard confirmation. Privacy page documents logout removal but not a scoped preservation workflow |
| R14 | Defensive malformed storage recovery, V5 p41–42 | NOT VERIFIED | Parsed null reaches `Object.entries` in source. Conflicting browser probes prevent an actual UI pass/fail claim; language-only reproduction is insufficient |
| R15 | Server timer independent of analytics, V2 p16; V4 p8 | PARTIAL | Client timer uses server offset; API save guard and expiry exist. Full deadline/clock/lock failover qualification not performed |
| R16 | Durable submit receipt then async grading, V4 p1–2; V5 p31 | PARTIAL | Lightweight terminal update + grading marker +202pending UI exists; no full admitted-command watermark/drain protocol, and dispatcher/fencing defects remain |
| R17 | Accurate mathematical visual text, V3 p5–7,22 | FAIL | F03: typed MCQ options show raw LaTeX even though shared question math rendering exists |
| R18 | Complete accessibility/device/keyboard certification, V1 p12; V3 p22; V5 p42–43 | NOT VERIFIED | Label/focus/status patterns exist; no full assistive-tech/device-lab evidence. Main audit found two undersized mobile targets; PDF tagging is explicitly not claimed |
| R19 | Calm responsive navigation and honest UI states, V1 p4–8,11 | PARTIAL | Core routes and pending/error states exist; source-image/timed synthetic flows reviewed. Template browser title, mixed native controls, partial tokenization and repeated test IDs remain |

## Academic content, sourcing and protected publication

| ID | Requirement / source | Status | Current implementation / evidence |
|---|---|---|---|
| R20 | Source provenance, hashes and location-backed matching, V3 p1–8,16 | PARTIAL | Private upload metadata, hashes, q/s refs, crop checks and review flags exist. Full question-block/solution-block graph, cardinality forms, taxonomy and diff evidence are incomplete |
| R21 | Rights per audience/expiry fail closed, V3 p2–3; V5 p11–13 | FAIL | A04 invalid audience is accepted and fails open. Rights flags and restricted lists exist, but creation validation is inconsistent |
| R22 | Human semantic approval before public release, V3 p13–14,20 | PARTIAL | Approval flag + rights/accessibility checks exist; not independent role-separated approval or payload-bound attestations |
| R23 | Concurrent editorial revision integrity, V3 p13–14,20 | FAIL | A03 last-writer overwrites another reviewer edit without expected-revision conflict |
| R24 | One immutable academic publication identity per version, V5 p17–20,29 | FAIL | A02 concurrent publish produces duplicate same-version archives; archive uniqueness/atomic publication transition missing |
| R25 | Immutable attempt snapshots and grade lineage, V4 p2,21 | PARTIAL | Content-addressed packs and set-on-insert grade ledgers/correction variants exist; no signed lineage/WORM or complete semantic rule-bundle attestation |
| R26 | Four separately governed artifact classes, V3 p3; V5 p12,17–27 | FAIL | Source, candidate crops, server keys and embargoed solutions share application identity/compute path; release allowlists are not independent storage/workload boundaries |
| R27 | Cryptographically signed activation decisions and one-use grants, V5 p13–20,27 | FAIL | No full request/grant/result tuple, canonical payload digest, independent signing authority or consumed-grant tombstone workflow |
| R28 | Key custody, WORM/ObjectLock and storage policies, V5 p17–27 | NOT VERIFIED | No evidence of configured KMS/HSM custody or certified retention controls. Do not infer provider policy from a private object path |
| R29 | Hostile-document parser sandbox and budgets, V3 p7,23; V5 p39–40 | FAIL | Parsing occurs in live/shared deployment or threadpool. No production sandbox/network-denial/hard-kill isolation proof; S01 exposes a form-parser budget gap |
| R30 | Extraction output fencing, V5 p10,40,50 | FAIL | A06 check/write race lets a stale lease mutate the draft after authority changes |
| R31 | Original guide/source paper stays unapproved until reviewed | PASS, scoped | Read-only DB snapshot: original75-question paper remains review, v1/r3; all50QAsets remain withdrawn. No audit publication performed |
| R32 | Authorized immutable content distribution and prefetch, V5 p47 | PARTIAL | Authenticated cropped assets/local byte-bounded cache exist; no complete publish-time candidate pack + authorization-aware CDN distribution protocol |

## Backend, database, operations and security

| ID | Requirement / source | Status | Current implementation / evidence |
|---|---|---|---|
| R33 | Modular ownership and API boundary, V1 p15; V5 p2,28 | PARTIAL | Domain modules and `/api` router boundary exist, but shared DB/runtime reads cross domains; this is not isolated service/cell ownership |
| R34 | Full bounded typed API catalogue, V5 p28 | PARTIAL |46routes;2explicitresponsemodels;10dictbodyhandlers. Envelope version/requestID present; comprehensive typed input/output/error/idempotency conventions incomplete |
| R35 | Bounded JSON and ambiguous input rejection, V5 p28,52 | PASS, scoped | Actual JSON middleware caps1MiB/depth40 and rejects duplicate/nonfinite values; historical tests cover this. This row excludes forms/files |
| R36 | Multipart/form parsing limits, V5 p39–40,52 | FAIL | Corrected local ASGI report30 accepts2MiBnonfilefield with actual middleware; installed Starlette version has known relevant resource advisories |
| R37 | Credential security and privileged operations, V5 p9,13–16 | PARTIAL | Hashes, revocable sessions, staff throttle exist. MFA, one-use step-up, independent review and production secret lifecycle absent. Audit-process credential leak requires authorized rotation |
| R38 | Autonomous durable batch dispatch, V5 p31,46,52 | FAIL | A05 queue can remain idle after capacity frees; cron/poll-triggered dispatch is not a continuously serviced worker fleet |
| R39 | Idempotent output publication and worker write fences, V5 p10,40,52 | PARTIAL | Unique per-lease PDF path and job lease guards exist; extraction destination fence fails A06 |
| R40 | Batch/live CPU/memory/identity failure isolation, V5 p44–46 | FAIL | Per-process lanes share deployment/threadpool/runtime; no independent worker/resource/trust plane |
| R41 | Bounded DB connections and waiting, V5 p49,52 | PARTIAL | Configurable default32connections/2swait. No fleet-wide pool budget, reserved critical pools or measured saturation evidence |
| R42 | Slim hot-path queries and budgets, V5 p49–50 | PARTIAL | Visit/history projections improved; per-start pack canonicalization/compression/upsert and repeated authenticated asset reads remain |
| R43 | Independent home cells and stable routing, V5 p44–45 | FAIL | No cell router, home-cell authority or independently provisioned writers/failure domains in application implementation |
| R44 | Atomic admission reservations and capacity release, V5 p7,30,50–51 | FAIL | No owner-bound preissued reservation consumption/counter transaction/exactly-once capacity release |
| R45 | Multi-AZ acknowledged durability and fenced DB failover, V5 p49–50 | NOT VERIFIED | Current accessible Mongo topology is standalone. Majority+journal request does not prove replicated durability or regional recovery |
| R46 | Degradation order, reserved terminal capacity and quota classes, V5 p51–52 | FAIL | Local limits and Retry-After exist, not admission/deadline-pressure controls that protect already-admitted cells |
| R47 | Cache correctness and nonauthority, V5 p47,49 | PARTIAL | Byte-bounded caches and authorization before crop delivery exist; distribution-tier authorization/invalidation/isolation is unqualified |
| R48 | WAF, edge quotas and hostile mixed traffic, V5 p52,64–68 | NOT VERIFIED | In-app limits are not evidence of external WAF policies or mixed authorized/hostile load qualification |
| R49 | Observability, bounded labels and attributable receipts, V5 p56–58 | PARTIAL | Audit events/request IDs/operational timestamp exist; no complete exported cell metrics, SLO/error-budget suite or incident evidence pipeline |
| R50 | Backups, restores and disaster recovery, V5 p53–55,64–68 | NOT VERIFIED | No operator-supplied restore/failover artifacts, production-volume timings, key-recovery rehearsal or RPO/RTO proof |
| R51 |500k/2×/pathological workload qualification, V5 p3,46,48,64–68 | NOT VERIFIED | Capacity worksheet only; small8-way duplicate-command checks and isolated worker tests are not capacity qualification |
| R52 | Dependency/supply-chain gates, V5 p9,39,56–68 | FAIL | Current dependency scans report version-matched advisories; reachability/remediation not completed. No clean golden dependency gate demonstrated |
| R53 | Minimized telemetry and privacy policy, V4 p3–4; V5 p56 | PARTIAL | Explicit phone profile disclosure is good; public HTML enables product analytics/autocapture configuration needing reviewed production consent/minimization. No sensitive-export claim made |

## Results, analytics, reports and evidence governance

| ID | Requirement / source | Status | Current implementation / evidence |
|---|---|---|---|
| R54 | Exact arithmetic for supported scoring, V2 p18; V4 p2 | PASS, scoped | Actual scorer seven-case baseline passed. No claim of complete official adapter golden corpus |
| R55 | Regrade does not silently replace original score/report, V4 p2,21 | PARTIAL | Separate ledger/version objects and PDF paths exist; full independent release approval/correction-cohort policy incomplete |
| R56 | Complete matched-solution PDF, V3 p16,20; V4 p1,22 | PARTIAL | Full-report generator and access-controlled queued downloads exist, with historical real PDF checks. This audit did not repeat every75Q/render/accessibility variant or high-volume export campaign |
| R57 | All60analysis contracts and versioned unavailable states, V4 p1,5–16; V5 p63–64 | FAIL | `analytics_60_matrix.csv`:10related contracts partial,50notimplemented; no full PASS asserted. Internal40minimum is incorrect |
| R58 | Cohort definitions, privacy and sample thresholds, V4 p3–4,17–20 | FAIL | No full cohort snapshot/eligibility/suppression/percentile pipeline; absence of fake percentile claims is good but is not implementation |
| R59 | Question timing, confidence, revision/exposure evidence and action plans, V4 p8–16 | FAIL | No complete reconciled visibility ledger, confidence capture, canonical exposure/review history or7/30day planning engine |
| R60 | Test/golden/artifact registry sufficient for sign-off, V5 p57,64–68 | FAIL | Useful tests exist, but audit found copied simulations, no-op assertions, invalid selectors/encodings and scope leaks. Corrected narrow proofs do not replace the required complete evidence catalogue |
| R61 | Current build/compile health | PASS, scoped | Frontend production build and Python compile pass; services run. This does not imply semantic correctness or deployment capacity |
| R62 | No application fixes during this audit | PASS, scoped | Initial97sourcehashesunchanged; supplementaryfilesunchangedsincediscovery. Test-artifact leakage/cleanup and credential-report redaction disclosed separately |

See `RULEBOOK_ERRATA.md` for internal documentation corrections and `AUDIT_REPORT.md` §9 for the proposed remediation order. None of these findings has been repaired during this audit.
