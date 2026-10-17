# Packet 1 — architecture/contract baseline v1

Status: application foundation under implementation; NOT a qualified 500,000-attempt platform. The ten-packet strategy remains binding. Explicit user decisions preserve matte maroon and phone-only students (no OTP/password); routine engineering choices proceed autonomously.

## Authority and implementation states

Five original PDFs are authoritative, subject to explicit user overrides and verified official-year evidence. Source page/block indexing is not atomic clause coverage. `coverage_manifest.json` must keep unreviewed source obligations visible and deny Packet 1 promotion until reviewed. The portable v1.0 PDF is a historical snapshot; do not rewrite it to imply future work was already completed.

Terms: IMPLEMENTED = code exists; TESTED = scoped executed artifact; PROVISIONED = actual infrastructure; QUALIFIED = measured matching workload/fault envelope. Contracts and a workload calculator do not imply provisioned capacity.

## Data ownership and access matrix

| Plane / authority | Writes | Permitted reads | Forbidden dependencies or actions | Implementation owner |
|---|---|---|---|---|
| Quarantine/source vault | Original bytes + hashes + source-role/rights receipt, append-only | Assigned extraction/reviewer workload only | No candidate access; no document-triggered fetch/execution; no in-place locked overwrite | P03/P04/P05 |
| Editorial/control | Draft branches, reviewed question-solution pairing, independent approvals, signed version/activation decisions | Academic authorized staff, build worker | Not an exam response writer; catalogue index cannot approve rights or answers | P03/P05 |
| Candidate delivery | Prebuilt candidate-only package/asset projections | Entitled student, exact pinned version/release | No original PDFs, hidden keys, source maps, unreleased solutions; authorize before cache hits | P05/P07 |
| Server-key | Exact approved keys, rational rules, canonical option mapping | Isolated grader and authorized reviewer | Never browser/source CDN; live API must not send key material | P03/P05/P06 |
| Live cell authority | One attempt home, reservation, generation, command+receipt, draft/commit, seal watermark, outbox | Cell-local session and grader snapshot readers | No source parsing, analytics scans, PDF generation, global transaction or unfenced dual writer | P02/P06 |
| Batch | Durable jobs, immutable candidate outputs, fenced output pointers | Pinned input snapshots and least-privilege objects | Broker/cache not acknowledgement truth; no cross-lane capacity theft | P04/P08/P09 |
| Analytics | Versioned materialized projections, cohort contributions, unavailable reasons | Results/reports/support under ownership and embargo | Cannot edit attempt truth or scan live writer per dashboard request | P08/P09 |
| Operations/evidence | Signed release evidence, bounded metrics, protected audit export | Named authorized operators | No secrets/phone/answers in metrics, logs or public health; no empty metrics reported healthy | P01/P10 + operators |

Current Mongo collections are legacy pilot authorities, not SQL live cells. Preserve legacy identifiers and attempt truth. Reference target is 20 independently qualified cells x at most 25,000 active attempts, with independent writers/HA and reserved terminal capacity. Actual engine/provider/version/regions, DB privileges, IAM, KMS, WORM and replication are operator dependencies. Do not invent provider selections or rewrite MONGO_URL.

## Source/rights/retention/release policy

- Source role enums: questions, solutions, key, combined. Source references use 1-based PDF pages and explicit coordinate systems; conversions are versioned, never inferred.
- Exact question-solution mapping and approved accessible text are independent from upload rights, publish rights and personal report rights. No test script is an academic approver.
- `source-private`, `candidate-safe`, `server-key`, `embargoed-solution` are separate classifications; a hash does not create an authorization or signature boundary.
- Locked versions create successors; author cannot independently approve their own protected change. Existing attempts pin source/package/profile/key/release versions.
- Retention/delete intervals and release/embargo rules must be approved in the decision register. Unknown retention is BLOCKED, never automatically purged. No destructive deletion job is introduced.
- Staff identity/MFA/grants are separate from phone-only student convenience identity. No verified-person cohort counts or recovery assurance is inferred from phone entry.

## Contract kernel

`backend/tejas/command_contracts.py` defines strict bounded immutable DTOs for future canonical command identity, receipts, exact rational marks and source references. They are executable reference schemas, NOT already wired into legacy save/start handlers and NOT a database transaction implementation.

Canonical format `tejas-command-json-v1`:
1. Accept a bounded object of null, boolean, signed 64-bit integer, valid Unicode string, array or object. Reject floats/NaN/Infinity, invalid Unicode, oversized keys/strings, excessive depth/items/bytes. No Unicode normalization or numeric coercion.
2. Sort object keys in Python Unicode codepoint order, UTF-8 encode JSON with no spaces and no ASCII escaping. This is a named application format, not claimed RFC 8785 conformance. Other languages must pass golden vectors before use.
3. Hash a versioned domain plus complete tenant/actor/operation/target/version/preconditions and body. Idempotency lookup scope includes tenant+actor+operation+target+request key; body fingerprint additionally includes version/preconditions. Changed intent conflicts within the same key scope; replay returns the stored immutable receipt.
4. Canonical hashes are integrity identifiers, not secret verifiers/signatures. Do not log the body, plain key, response values or raw identity.

New schemas use integer UTC milliseconds for absolute instants and monotonic milliseconds only for process-local duration measurement. Cross-host monotonic values must not be compared. Exact rational marks are reduced numerator/positive denominator, no binary floating-point scoring. Existing legacy float epoch-seconds are explicitly separate and unchanged.

## API catalogue and legacy compatibility

All routes remain under `/api`. Current runtime OpenAPI and generated policy inventory describe actual legacy routes; opaque dict bodies and responses remain labelled gaps. New canonical `/api/v1/student`, `/api/v1/admin`, `/api/v1/integrations` route families are PLANNED and must not be represented as functional aliases until implemented and tested in their owning packets. `GET /api/internal/capacity/profile` and `GET /api/internal/safety/status` are staff-authenticated, read-only, typed, no-store baseline endpoints.

Target per-operation contract: operationId, x-owner-policy, x-role-scope, x-workload-tier, x-idempotency-mode, body budget, strict input/output, typed errors, exact versions, permission boundary. Editable truth requires strong ETag and exact If-Match; missing precondition 428, stale version 412, reused key with changed intent 409. Long jobs accept 202 only after durable intent, with Location and Retry-After. Auth 401, forbidden 403, hidden/nonexistent owner resource 404, invalid schema 422, excess body 413, overload 429/503 with bounded retry guidance. These target conventions are not claims that all legacy routes enforce them yet.

## Immediate containment vs permanent repairs

Uploads, source parsing/preview, publication, extraction and regrading are held fail-closed in Packet 1. HTTP containment happens before form/body parsing. Function-level guards and worker dispatch checks prevent alternate direct paths from bypassing the hold. The hold is code-controlled, not a browser/env switch; later packets may lift an individual capability only with its original regression and protected-operation gates passing. Running work already past a guard is not retroactively fenced: P04 owns destination fencing.

Student entry, existing attempt saves/submissions/core grading/report access and staff read-only review stay available. Ordinary draft edits retain audited limitations (A03); content remains unpublished. Holding a capability is not fixing A02/A05/A06/S01, and does not rotate a leaked credential.

## Security incident / operator execution boundary

The persisted staff password hash lives in `tejas_users`; changing `ADMIN_PASSWORD` alone does not rotate an existing account because seed_owner only inserts missing users. Access and refresh validate a `tejas_sessions` record. Rotation must replace the persisted hash and invalidate all affected sessions, including sessions created by a racing login. A safe execution requires a temporary staff-auth issuance hold, zero in-flight issuance, persisted rotation, revocation and verification, then restoration. Do not delete student sessions. Never put passwords in shell args, environment dumps, screenshots or reports. Use a protected secret manager/operator terminal, audit only opaque operation identifiers/counts.

No rotation or session invalidation is executed by this baseline. It remains a P0 gate pending the previously required one-time authorization and operator-controlled secure credential handoff. Blocking publication reduces impact but does not close the incident.

## Observability, resource and cost schemas

Bounded metric label enums only: service, cell (configured finite allowlist), lane (live/grade/normal/batch/telemetry), operation (catalogue ID), outcome (accepted/rejected/error/held), deployment_version (bounded active versions). Never learner/attempt/request IDs, phone, URL query, answer or credential as metric labels. Logs allow only request correlation, catalogue operation, outcome and duration; sensitive payloads remain absent.

Capacity evidence must report API queues vs DB pool wait vs commit latency, backlog age, WAL/replication, rejection classes, offered/started/completed/dropped generator demand, full and predeclared critical-window histograms. Missing evidence is UNQUALIFIED.

Budget inventory requires measured unit throughput, utilization, actual quota/region/provider/version, per-lane pool/concurrency, approved cost currency/period/ceiling and named operator. Unset values stay null/BLOCKED; no guessed cloud bill or machine count. Optional exports/analytics may shed; admitted commits/seals must not be terminated to save cost.
