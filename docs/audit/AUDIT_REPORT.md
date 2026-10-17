# Architecture and full-code compliance audit

**Verdict: DO NOT SIGN OFF for a student launch or 500,000-concurrent-user operation.**

This is an **audit, not a repair release**. The project has useful working practice components, but the audit found reproducible correctness defects, incomplete requirements, and unqualified infrastructure. Earlier “hardened”, “fenced”, or high test-pass claims must not be read as full compliance.

## 1. Scope, authority, and preservation

User instruction: audit the architecture and everything coded against the updated rules **before changing application code**.

- Authoritative source: all five supplied PDFs, **177 pages**; original URLs and SHA256 values remain in `../source_guides/manifest.json`.
- User overrides retained: **matte maroon**, and **phone-number-only student access without OTP/password**. These are deliberate product choices, not findings to “fix”. Staff access remains separately assessed.
- Initial source baseline: **97 application/configuration files, 29,382 lines**, in `source_baseline.json`. Four additional entry/build files were subsequently inventoried in `supplemental_source_inventory.json`.
- Reviewed custom backend modules, custom React pages/components/hooks, source/grade/report flows, configuration, dependencies, tests and existing claims. Shadcn primitives were reviewed at integration points, not formally verified line by line. An inventory is not a code-coverage measurement.
- No application-source, connection environment, infrastructure, credentials, published paper, answer, or report was repaired during this audit. Original-source SHA256 comparisons are recorded separately in `source_integrity_final.json`.
- Audit-created tests and documents are new artifacts. One rejected harness accidentally created four unreferenced test-only content packs outside its namespace; those exact records were identified and removed. See `harness_side_effect_inventory.json` and `harness_cleanup.json`. Subsequent corrected tests show unchanged main-collection counts and no remaining audit collections.

## 2. Evidence policy

| Evidence class | Meaning |
|---|---|
| R | Actual application function executed against isolated Mongo collections; dependencies outside the tested behavior mocked and disclosed |
| B | Actual built frontend exercised in a browser; controlled synthetic attempt responses are **MOCKED TEST DATA**, not a real student's attempt |
| H | Real application middleware with installed framework exercised in a local ASGI harness; not a public load or exploit test |
| S | Source/configuration inspection with file and line references |
| D | Dependency advisory scan; establishes a version match, not exploitability |
| N | Not implemented, not provisioned, or not verified; these are distinct from a reproduced runtime bug |

No overall “architecture percentage” or “500k readiness score” is assigned. A test that reproduces a bug has succeeded as an audit test; it does **not** mean the application passed its requirement.

Reports 24 and parts of 25 were rejected because tests copied logic, missed the intended sequence, or failed to patch the real collection object. Reports 27–29 also contain overclaims corrected in `EVIDENCE_LEDGER.md`. The validated records below take precedence over generic “100% passed” sections in subagent output.

## 3. Actual architecture, not the proposed one

```text
Browser React SPA
  -> one FastAPI application / API boundary
      -> shared MongoDB writer and shared identity/content/attempt stores
      -> in-process grade/report/extract/regrade execution limits
      -> existing private object-storage gateway
      -> local source/pack/crop caches
Platform cron -> periodic repair/dispatch of a bounded batch
```

Mongo's read-only `hello` response confirms **no replica-set name and no mongos** in this environment. A requested majority/journal write concern on standalone Mongo is not multi-AZ acknowledged-write durability.

The code is a **modular monolith**, not 20 independent live cells. File boundaries are useful, but they are not independent database writers, queue failure domains, workload identities, admission budgets, or outage boundaries.

PDF-05's 20 × 25,000-cell example, 35,000 live RPS baseline, 2× envelope, and separate pathological burst model are **planning inputs only**. There is no representative single-cell saturation result, distributed 500k run, AZ failover, quorum-loss test, or restore drill in this audit.

## 4. Reproduced application findings

Severity: **P1 = blocks release of the affected correctness/security capability**; **P2 = significant functional/UX correctness gap**. These are not CVSS scores. All findings remain **OPEN; no fixes applied**.

| ID | Severity | Finding and observed result | Code / guide | Evidence |
|---|---|---|---|---|
| A01 | P1 | **Retry-resume identifiers are not durable.** K1 creates retry R1; K2 resumes R1; after R1 completes, replaying the already-successful K2 creates a different R2. Ordinary start aliases do not solve this separate retry path. | `backend/tejas/attempts.py:388–430,471–490`; V5 p29 | R: report 26, real `retry()` |
| A02 | P1 | **Concurrent publication duplicates one version.** Two real publication calls succeed and create two archives for the same set/version. The revision guard is not advanced by publication, and no unique set/version archive constraint prevents this. | `content.py:565–633`; `db.py` indexes; V3 p20–21, V5 p17–20,29 | R: report 26, real `publish()` |
| A03 | P1 | **Reviewer edits silently lose updates.** Two real edits succeed; the later update overwrites the first. There is no client expected-revision condition on this edit mutation. | `content.py:472–521`; V3 p13–14,20; V5 p28–29 | R: report 26, real `edit_question()` |
| A04 | P1 | **Unknown audience values fail open.** Real `create_set()` accepts an invalid audience. `permitted()` then treats it as non-restricted, and the real detail handler allows access to a record made published inside the isolated fixture. Creation does not whitelist the enum even though updates validate it. This is not evidence that an existing private paper leaked publicly. | `content.py:40–53,84–98,159–172`; `attempts.py:114–119`; V3 p2–3; V5 p11–13 | R: report 26, real create/policy/detail handlers |
| A05 | P1 | **A freed worker lane does not drain waiting work.** With two grade jobs deliberately held running, a third dispatch remains queued. After both finish, it stays queued until another explicit dispatcher call. Result polling and the periodic cron can later recover it, but they are not a continuously serviced durable worker fleet. | `jobs.py:50–60,131–132,169–188`; `.emergent/crons.yml:2`; V5 p31,46,52 | R: report 26, real `run_job()` and event-held capacity |
| A06 | P1 | **Extraction fencing has a check/write race.** The real worker passes `require_lease`; its lease is replaced before its set update; the old worker still modifies the draft because the destination condition includes revision but not a fencing generation. A later job-completion check does not undo that content write. | `jobs.py:45–47,89–94`; V3 p14; V5 p10,40,50 | R: report 26, real worker and intercepted real collection write |
| S01 | P1 | **The JSON size guard is not an upload/form budget.** With the actual `JsonBodyLimits` middleware and installed Starlette parser, a 2,097,152-byte non-file multipart field is accepted by a local ASGI endpoint. The installed Starlette version also matches known multipart DoS advisories. A live outage/exploit was not attempted. | `http_limits.py:30`; `content.py:245–271`; `requirements.txt` Starlette 0.37.2; V5 p39–40,52 | H: corrected report 30; D: OSV |
| F02 | P2 | **Sign-out erases other profiles' pending drafts.** The logout action deletes every `tejas-draft-*` key, not just the current profile. Two scoped synthetic drafts were removed without an immediate loss confirmation. The privacy page does disclose that logout removes drafts; that disclosure does not resolve the cross-profile scope or interruption UX. | `frontend/src/lib/auth.js:11`; `features/Info.js:117–123`; V2 p17; V5 p41–42 | B: report 27; S: explicit key filter |
| F03 | P1 | **Typed answer-option mathematics displays raw markup.** A controlled Player fixture renders options such as `$x^2$` literally; option content is not passed through the math renderer. This concerns typed options, not source-image options. | `features/Player.js:253–295`; `components/QuestionContent.js`; V3 p5–7,22; V5 p42–43 | B: report 28, both required viewports |

### Additional code-level risks not promoted to reproduced runtime findings

- **F01 — malformed/null local draft recovery:** `useAttempt.js:45–57` accepts parsed `null`, then calls `Object.entries` without validating a record shape. The language expression throws, but the actual Player browser observations were inconsistent. Status: **NOT VERIFIED at UI level**, not “fixed”. Quarantine/recovery behavior needs a correct browser regression.
- **A04b — malformed audience expiry:** creation accepts a free-form expiry string; comparisons use strings. Updates parse dates. This adjacent creation-validation path needs an isolated date-boundary test before a separate runtime finding is claimed.
- **A05b — repair backlog fairness:** maintenance inspects bounded, unsorted first batches and is not a fleet dispatcher. Failed/unserved entries can consume the recovery window; high-volume starvation has not been load-tested.
- **A07 — hot-path CPU/source work:** every new attempt still reconstructs/hashes/compresses and upserts a question pack through `packs.seal`; staff source-view handlers parse PDF data synchronously. Limits and local caches reduce some work but do not prove event-loop or CPU isolation. This is source evidence, not a measured latency regression.
- **A08 — analytics zero denominator:** `scoring.py:103–119` returns zero for unavailable accuracy/percent/rate denominators, while V4 p5–6 requires null/unavailable for the corresponding undefined metric. Marks correctness and metric semantics are different requirements.

## 5. Security and dependency review

### Immediate audit-process incident — credential rotation required

A testing agent included an existing staff credential in report 27. The saved artifact was redacted; `credential_redaction.json` contains paths and actions, not the value. Prior tool-log output cannot be retracted.

**Required authorized action:** rotate the actual staff account credential and revoke relevant sessions. Merely changing a bootstrap environment value may not change an already-created account. **No credential or session revocation was performed during this audit.** This incident is separate from the application defects above; it is not proof of external account compromise.

### Dependencies

- `yarn audit`: **51 advisory records, 27 unique module/advisory pairs**; reported record severities: 21 high, 25 moderate, 5 low. Many concern the CRA/webpack build or development toolchain, not necessarily deployed browser execution.
- OSV query checked **12 selected installed Python packages**, not the entire environment. Starlette 0.37.2 matches multipart-form resource advisories. File-spooling, range-response and unrelated dependency advisories were not independently exploited.
- KaTeX 0.16.22 matched an advisory requiring pre-existing prototype pollution to bypass trust restrictions. No such pollution/XSS chain was demonstrated in this application.
- Local HS256 configuration, package presence, or an advisory count alone does not prove reachability of JWK/algorithm-confusion vulnerabilities. Runtime reachability must be triaged before risk claims or upgrades are declared verified.

### Third-party instrumentation and secrets boundaries

`frontend/public/index.html:64–133` initializes PostHog. The public browser showed `autocapture=true`, `capture_pageview=true`, `opt_out_capturing_by_default=false`, `disable_session_recording=false`. These flags establish configuration, **not proof that sensitive question content or credentials were exported**, nor proof that session recording is currently active server-side.

Protected study/staff surfaces need an explicit telemetry inventory, consent/minimization policy and production configuration review. “No advertising trackers” is not equivalent to “no product analytics”; the existing copy does not fully describe this instrumentation. Platform/editor scripts must be handled with the platform owner, not removed blindly during an audit.

Staff password/RBAC separation exists. Required SSO/MFA, payload-bound one-use step-up grants, independent approval, KMS/HSM signing, WORM/Object Lock, per-artifact-class workload identities and production key lifecycle are not implemented/provisioned.

## 6. Full requirement status

The detailed matrix is `REQUIREMENTS_MATRIX.md`; all 60 analytics entries are in `analytics_60_matrix.csv` and `.json`.

| Area | Status | Interpretation |
|---|---|---|
| Exact marks for currently supported custom MCQ/integer practice | PASS, scoped | Seven real scorer fixtures passed, including wrong-answer penalties, signed integers, equivalent key, dropped/award-only items and exact fractional marks. This is not approval of every official exam adapter. |
| Acknowledged save receipts / ordinary start aliases | PARTIAL | Useful atomic properties exist; the retry-resume path fails A01; no complete distributed command register/lease protocol. |
| Content pairing, private source handling and attempt snapshots | PARTIAL | Reviewed refs, hashes and private API gates exist; physical release classes, signed manifests and four-eyes protected activation do not. |
| Publication and reviewer integrity | FAIL | A02/A03/A06 block a claim of safe concurrent editorial operation. |
| Batch processing | PARTIAL / FAIL at required guarantees | Heavy grade/report work is off the request path, but A05/A06 and process sharing prevent a reliable isolated worker-fleet claim. |
| Phone-only student access / matte maroon | PASS, user override | Preserve these decisions; do not reintroduce OTP or the old blue palette as an audit fix. |
| Offline practice UX | PARTIAL | Pending draft recovery and countdown have useful behavior; logout loss, malformed-record recovery and a full offline-open capsule remain gaps. |
| Formula fidelity | FAIL for typed options | F03; unrelated source-image rendering is not the failing path. |
| Results / PDF snapshots | PARTIAL | Core score and complete-report paths exist, including separate correction versions. Full report/accessibility/analytics specification is not complete. |
| All 60 analyses | FAIL | Ten related analysis contracts have partial implementations; fifty were not found as metric calculations plus metric-specific unavailable-state contracts. No full analysis PASS is asserted. This is not a percentage score. |
| API contract-first boundary | PARTIAL | `/api` envelopes exist; AST inventory found 46 routes but only two explicit response models, with ten untyped dictionary-body handlers. Versioned envelopes are not a complete typed API. |
| Database/cells/durability | FAIL against the target architecture | One standalone writer; no independent cells, transactional distributed admission, generation fencing or multi-AZ durability proof. |
| 500k capacity, chaos, recovery and accessibility certification | NOT VERIFIED | No qualifying campaigns or certifications exist in this evidence set. |

## 7. Rulebook errors and claim corrections

See `RULEBOOK_ERRATA.md`. Most importantly:

1. **V4 p1 mandates all 60 analyses**, and V5 p64 repeats this. The internal rulebook's “at least 40 meaningful analyses” relaxes the actual specification without a user-approved override.
2. V2/V5 require an explicit draft/commit/admission/seal protocol. The implemented custom autosave policy is labelled honestly, but labelling does not make it compliant with that protocol.
3. A lease read before a write is not a write fence (A06). Separate semaphores are not independent worker fleets (A05).
4. Private objects plus hashes are not independently signed academic truth, independent approvals, or WORM retention.
5. High pass percentages in small test reports are neither comprehensive coverage nor capacity qualification. Some prior “passes” were no-op, malformed-input, copied-logic or selector errors.

## 8. UI and operational observations

- Public desktop1920×800 and mobile390×844 screenshots had no horizontal overflow; settled matte-maroon dark-mode controls were readable.
- Browser title remains **“Emergent | Fullstack App”** (`public/index.html:24`). Two measured mobile targets were below44px high: brand link40px and login42px. These are P2 polish/accessibility gaps, not evidence that the whole UI is broken.
- Native controls and literal style values remain throughout the custom UI. Shadcn adoption/tokenization is partial; duplicate test IDs occur in repeated components. No complete keyboard/screen-reader/zoom-device audit was completed.
- Current catalogue: **50 QA sets withdrawn; one original75-question paper in review, version1/revision3**. No approved student paper is published. This is an intentional approval gate, not a fixture-access defect to bypass.
- Frontend production build and Python compilation pass. Build success does not invalidate the correctness findings.

## 9. Remediation order — proposed only

### Immediate authorized security action
Rotate the exposed staff credential and revoke sessions; retain a redacted incident record. Review telemetry policy and prevent credentials from entering future test output.

### Gate1: correctness before publication or scale claims
Fix A01–A06 and S01; then address typed-option math and safe draft-discard scope. Each fix needs the exact failing regression converted into a passing requirement test, plus a new **testing-agent** verification report. Do not weaken permissions or substitute copied logic to get a green result.

### Gate2: academic truth and operator controls
Implement immutable publication identity/CAS/uniqueness, segregated approval, full typed contract families, staff step-up and signed release artifacts. Treat source parsing as hostile work in a physically isolated execution boundary.

### Gate3: per-cell architecture and durability
Select/provision the required writer and durability topology, transactional admission/command authority, generation fences, terminal drain rules, autonomous batch dispatch and reserved capacity. Reconcile the Mongo pilot with the guide's relational cell protocol through an explicit design/migration decision—not a silent equivalence claim.

### Gate4: complete product and evidence
Official year-pinned adapters, full60-analysis registry/calculations/unavailable states, all report/solution-release workflows, accessibility, source review. Then qualify one cell, test skew and failure, progress to distributed capacity and restore campaigns. Admit only a measured envelope.

**No remediation has been applied. Findings and acceptance tests are ready for review before implementation.**
