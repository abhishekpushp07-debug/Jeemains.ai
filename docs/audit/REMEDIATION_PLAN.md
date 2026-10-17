# Remediation backlog — proposed, not applied

User approval is required before changing application behavior. Every bug fix must be verified by a new **testing-agent** report against its exact original failing sequence; inspection/curl alone cannot close it.

## Immediate security action (authorized operator/account owner)
- Rotate the staff credential exposed in audit output and revoke affected sessions. Confirm the persisted account credential changed, not just a bootstrap environment variable. Keep only a redacted incident record
- Review tester credential handling and protected-surface telemetry configuration. Do not disable required platform tooling or rotate secrets silently during an audit

## Gate 1 — correctness and resource safety

| Finding | Required behavior | Regression that must pass |
|---|---|---|
| A01 retry idempotency | Every successful retry/resume key binds actor+operation+parent+version/body to one durable outcome | K1→R1; K2 resumesR1; finishR1; K2 replay returnsR1; changedbodyconflicts; concurrentduplicate does not createR2 |
| A02 publish race | One transition/immutable version identity; guard advances atomically; archive uniqueness enforced | Barrier two publish calls on one snapshot: exactly one transition, one version archive; retry semantics explicit; no overwritten approval/truth |
| A03 review lost update | Client expected revision or equivalent editor concurrency token; no blind last-write-wins | Two editors readr; saveAaccepted; saveBconflicts with actionable currentrevision; A's content preserved |
| A04 audience | Strict accepted values/date schema at creation and update; unknown values deny access | Invalidaudience rejected; legacyinvalidaudience neverpublic; malformed/expiredrights reject; validrestricted/all behavior preserved |
| A05 dispatcher | Accepted durable job serviced without browser polling; overflow stays durable and fairly drains | Holdfullcapacity; enqueueN+1; freeaslot; jobstarts withoutstatusrequest/cronintervention; poison and failedoutbox entries do not starve laterwork |
| A06 extraction fence | Authority token/generation enforced at the destination write or equivalent atomic boundary | Replaceleaseaftercheck/beforewrite; oldworker cannot mutate content; currentworker can; editorCAS preserved |
| S01 multipart budgets | Version-qualified parser + total/field/file/count/concurrency limits before expensive work | Correctmultipartcontenttype; oversizednonfileparts reject within bounded resources before route work; file-spooling separately tested; legitimatePDFupload remains usable |
| F03 math options | Shared safe math rendering for typed option content, consistent with question/solution policy | LaTeX fractions/powers render as math in bothviewports, accessibleequivalent exists, hostilemarkup remains inert |
| F02 draft lifecycle | Explicit scoped cleanup/discard policy and immediate pending-loss warning | Otherprofiledrafts retained unless explicitly authorized todiscard; currentpendingdrafts reconciled/exported/confirmed beforeloss |
| F01 local corruption | Validate local record shape and recover safely fromnull/primitives/malformedentries | ActualPlayerbrowser replay (not language expression) shows recoverablestate, no fatalpage, no silentloss of validneighbor drafts |

Also add zero-denominator metric semantics, creation-expiry tests, query-budget and mutable-response-schema coverage. Do not label missing official protocol features as solved by fixing these pilot defects.

## Gate 2 — academic/control-plane safety
- Protected operation catalogue with full typed inputs/outputs, body digest/idempotency scope, status/header/error rules and exact authorization capabilities
- Immutable publication/version identity, review invalidation/diffs, taxonomy and pairing-cardinality provenance
- Independent author/reviewer/publisher decisions, staff MFA and payload-bound one-use step-up grants
- Signed activation/supersession/revocation/regrade lineage, managed key custody, physically separated source/candidate/key/embargoed artifacts, verified retention controls
- Isolated PDF parsing/extraction and publishing pipelines with hard resource/network budgets

## Gate 3 — real scale architecture
- Explicit platform/database decision and provisioned isolated live cell; migrate transactional admission, writer generation, commit register, cutoff/seal/drain and durable receipts without changing old attempt truth
- Authenticated home-cell routing and independent control/trust/identity outage behavior for admitted attempts
- Autonomous workers and aggregate pipelines in independent failure/resource domains; live receipt capacity reserved from batch/analytics traffic
- Authorization-aware distribution, tenant quotas, cache inventory, observability and backup/key/object recovery inventory
- Qualify one cell first. Publish measured limits, then multi-cell skew/fault behavior; never infer500k readiness from replica count or a2×normal workload alone

## Gate 4 — complete product specification and qualification
- Official-year JEE/BITSAT and remaining required adapters, including their explicit protocol and bonus/partial rules
- All60metric IDs with versioned definitions/evidence/unavailable states, golden datasets, privacy suppression, question drill-throughs and study-action workflows
- Full offline/recovery, accessibility/device coverage, matched-source rendering and export corpus
- Distributed mixed-workload campaign, cold-cache/prefetch bandwidth, reconnect/start/submit surges, queue poison, DBstall/quorum/AZ loss, operator failover and production-equivalent restore drills

Deliverables per change: reviewed design/contract, exact failing test, implementation diff, independent passing test report, updated risk/matrix row. Only then may a finding change from OPEN to VERIFIED FIXED.
