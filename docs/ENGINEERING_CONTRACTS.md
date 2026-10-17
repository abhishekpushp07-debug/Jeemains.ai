# Engineering contracts — Tejas

The binding rules are now in **[RULEBOOK_ARCHITECTURE_V5.md](RULEBOOK_ARCHITECTURE_V5.md)**, traced to all five supplied PDFs. See **[GAP_MATRIX_PDF_TO_CODE.md](GAP_MATRIX_PDF_TO_CODE.md)** for actual implementation status and **[CAPACITY_AND_OPERATIONS.md](CAPACITY_AND_OPERATIONS.md)** for the unprovisioned reference topology and qualification gates.

## Actual application boundaries
| Module | Owns | Must not do |
|---|---|---|
| `auth.py`, `phone.py` | Revocable sessions, student convenience profiles, staff passwords/RBAC | Imply phone ownership verification or grant staff rights to phone profiles |
| `catalog.py` | Bounded discovery metadata, audience filters | Deliver source PDFs, keys or solutions |
| `content.py`, `derivatives.py` | Private source provenance, review/rights gates, authorized cached crops | Treat cache as authorization; publish unreviewed extraction |
| `packs.py`, `profiles.py` | Immutable content-addressed attempt packs/profile versions | Claim hashes are signatures/WORM locks; substitute edited truth into historical attempt |
| `answers.py`, `idempotency.py` | Atomic acknowledged custom-practice saves, durable payload-bound receipts, server sequence, start aliases | Drop accepted history or equate autosave with official explicit-commit protocol |
| `attempts.py` | Ownership, clock fences, atomic terminal seal/outbox, read orchestration | Run grade computation on submit; hydrate packs for visits/history |
| `jobs.py`, `runtime.py` | Durable job intents, bounded pilot lanes/retries, lease checks, outbox recovery | Claim in-process limits are independent fleets; reset successful report output |
| `scoring.py`, `corrections.py` | Exact immutable grade ledger, labelled successor corrections | Overwrite original grade/report during regrade |
| `reports.py`, `tejas_core.py` | Full same-version PDF composition in batch work | Filter exports to current visible UI subset or expose solutions before policy allows |
| `http_limits.py`, `contracts.py` | JSON input budgets, v1 response envelopes | Log raw credentials/answers; accept ambiguous duplicate JSON fields |

## Current API conventions
All app routes begin `/api`. Actual schema: `/api/openapi.json`. Success envelopes contain `data` and `meta.api_version`; error envelopes expose stable user-facing messages, not tracebacks. Explicit newly typed DTOs cover answer save/receipt, start, visit and submission. Legacy staff/result dictionaries are not yet a complete contract-first schema catalogue.

Save acknowledgement includes accepted revision, server timestamp, sequence and current revision. Identical replay retrieves its original receipt even after newer saves; a changed body conflicts. `PUT /api/attempts/{id}/answers/{qid}` currently makes an accepted response scoring-eligible under the custom-practice policy.

`POST /api/attempts/{id}/submit` returns the durable terminal receipt; `202` means grading pending, not unsubmitted. Results may return `202` with `status=grading`, receipt, job state and Retry-After. They return final score only after a frozen ledger exists. Report requests reject pre-grade use; failed report jobs require explicit retry, successful report objects retain their original pointer.

## Current storage/durability limits
- UUID business IDs and UTC/epoch timestamps. Existing immutable pack keys are SHA256 identities, not question UUIDs.
- Mongo client: default32 connections, bounded2s pool wait, majority+journal request. Actual preview topology is **standalone**, not replicated multi-AZ storage. No acknowledged-write failover guarantee was demonstrated.
- Receipt count is capped per attempt (default10,000, config upper12,000) to keep a single document bounded; exhausted history is explicit, never silently pruned. Start resume aliases bounded1,024.
- Pilot job defaults: grade2,report1,extract1,regrade1, three attempts, 900s leases. Limits are per process. Parser/report work still shares one deployment/thread runtime; physical CPU/memory/network separation and hard-kill sandboxes remain pending.
- Setting `TEJAS_INLINE_JOBS=false` intentionally stops in-process execution; **no external worker adapter/fleet is supplied or provisioned**. Do not flip this in production without an implemented and tested consumer.
- Existing platform cron recovery is15-minute best effort, not a low-latency batch fleet. Deadline save rejection does not depend on cron timing.

## Privacy/source limitations
Question and solution fields are allowlisted by policy; attempt packs still combine private truth server-side. Object storage uses one existing application identity. Separate source/candidate/key/solution workload identities, KMS, signed manifests, authorized CDN distribution and Object Lock are release blockers.

## Capacity statement
This is a hardened, tested **practice pilot**. PDF05's20×25k cells,35kliveRPSbaseline and2×headroom are sizing proposals. No 500k concurrency load or distributed fault campaign was run. Do not call the system production-ready for that scale.
