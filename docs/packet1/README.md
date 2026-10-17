> **Latest checkpoint:** read [CONTINUATION_STATUS.md](CONTINUATION_STATUS.md) first. It supersedes the earlier counts below: 49 executable ingress contracts, 143 passing tests plus 6 OPEN regressions repeated three times, 2 source pages / 38 blocks / 65 exact-span obligations, staff generation fencing, and unresolved dependency findings. Packet 1 and 500k qualification remain blocked. Earlier testing-agent scope violations and replacement evidence are explicitly recorded there.


# Packet 1 — implemented foundation and remaining exit work

**Status: IN PROGRESS; exit BLOCKED. 500,000 active-attempt capacity: UNQUALIFIED.**

This update is actual application code plus bounded evidence, not completion of Packet 1 or the ten-packet plan. Routine implementation is authorized; student phone-only entry and matte-maroon design remain unchanged.

## Delivered and verified

- Strict versioned reference command/receipt/source/candidate schemas; scoped intent hashing, bounded JSON, nested command immutability, exact rational marks and explicit UTC-millisecond fields. These are not silently wired into legacy exam handlers or misrepresented as durable SQL transactions.
- Exact workload calculator: 500,000 active attempts imply 16,666.67 commits/s + 10,000 drafts/s + 8,333.33 leases/s = **35,000 live requests/s**; 16,666.67 telemetry/s yields **51,666.67 total/s** before overlays. Start/submit waves, per-cell rates, three-hour volumes, pathological traffic and staged SLO definitions are explicit. These are equations, not measured throughput.
- Staff-only typed `GET /api/internal/capacity/profile` and `GET /api/internal/safety/status`, with 401/403 boundaries, no-store responses and explicit unqualified state.
- Fail-closed holds on new PDF uploads, staff source previews, publication, extraction and regrade. Upload rejection occurs before reading/parsing request bodies. Direct protected functions, enqueue/retry paths and dispatch obey the hold. Held queued jobs retain their exact durable intent without consuming a lease. Existing normal grade/report lanes are not held.
- Original five source identities verified; all **177 pages / 3,299 text blocks** indexed. **45 selected obligations + 60 analysis feature obligations**, all **13 WP / 12 OPS-R gates**, current OpenAPI inventory and schema files are available. All source pages still require complete atomic-clause review; indexing does not prove zero orphans.
- Legacy rulebook's incorrect 40-analysis minimum corrected: all **60 analyses** are mandatory.

## Evidence, not a greenwashed pass rate

Independent final report: `/app/test_reports/iteration_37.json`. Three fresh-process runs each produced **71 passed + 6 strict expected failures; zero unexpected failures/errors**. Six RED cases prove current defects remain OPEN: A01 retry aliases (P06), A02 publication archives/A03 same-question edits/A04 audience (P05), A05 queue drain/A06 destination fencing (P04).

Every RED case raises a specific `OpenInvariant` only at the known final violated condition; unrelated setup exceptions/timeouts fail normally. A02/A03 use deterministic same-preimage barriers. A06 changes the real lease after `require_lease` and immediately before the real destination write. A05 pauses the real grader and joins its task during cleanup. No historical defect is closed by a hold or xfail.

The independent small scoring oracle is hand-calculated, synthetic practice only, not official JEE/BITSAT certification. The preserved-flow test exercises actual phone login, preflight, attempt start, answer save, replayed acknowledgement, resume, submit receipt replay and core results in an isolated database.

**MOCKED in tests only:** A06 parser output and object-storage bytes. Concurrency barriers/paused grader and capability bypasses are scoped test controls, not production behavior. All database cases use real Mongo under an exact UUID-only namespace. Outbound HTTP is blocked. No real staff credential is used, no pilot database is mutated by this suite, and cleanup errors are never swallowed.

The initial testing-agent reports 34–36 are superseded: they included incomplete execution or weak/incorrect harness assertions. Do not reuse their pass percentages. Report37 also has generic percentage fields and conflates owner packet codes with priority labels; use the explicit counts, OPEN statuses and original audit priorities instead. The report's broad zero-critical-bugs label is NOT a security clearance: credential rotation and historical P1 findings remain open.

Frontend build passed. Main-agent desktop 1920x800 and mobile 390x844 screenshots show the preserved maroon landing page with no horizontal overflow; login remains phone-only. Browser smoke is not full frontend regression, real-device performance or a load test.

## Still required for Packet 1 exit

1. Complete source-by-source atomic MUST-clause review, zero-orphan mapping and owner approval. The current registry is a partial reviewed subset with an explicit review queue, not the promised final coverage proof.
2. Complete all target route-family schemas, per-operation ownership/roles/preconditions/errors, retention/deletion and decision-register approvals. Existing generated legacy metadata is inferred inventory, NOT proof of enforcement or a frozen production contract.
3. Port and verify the remaining audit reproductions (including A04b/A05b/A07/A08, S01 original bounded upload failure, F01–F03); existing historical evidence remains open. The new upload hold is not a sandbox or a patched multipart stack.
4. Finish actual dependency/advisory/license triage and signed release SBOM/evidence. `dependency_baseline.json` is an unsigned installed-package/lock inventory only. Legacy Starlette/FastAPI parser handling remains scheduled for P04 remediation.
5. Execute authorized persisted staff credential rotation and race-safe session revocation, with secure replacement handoff. This has NOT happened. Changing the bootstrap environment password alone would not rotate the persisted account.
6. Finalize named owner/operator approval of device/network/region/quota/cost profiles and SLO decisions. No PostgreSQL cells, worker fleet, IAM/KMS/WORM, broker infrastructure or load generators have been provisioned here.

Do not advance to Packet 2 or announce Packet 1 complete while these exit requirements remain unresolved. Later permanent repairs retain their original packet owners. Tests/holds do not replace those repairs.

## Reproduction and files

- Run only `python -m pytest /app/tests/packet1 -q --tb=short`, in a fresh process, not historical audit scripts against the preview.
- Rebuild inventories: `python /app/docs/packet1/build_baseline.py`; it reads source PDFs/lockfiles and current public OpenAPI, not the application database. Coverage status remains BLOCKED by design.
- Authority: `BOUNDARIES_AND_CONTRACTS.md`, `READINESS.json`, `coverage_manifest.json`, `COVERAGE_MATRIX.md`.
- Evidence: `evidence/` retained logs, collected node IDs, build/compile evidence and file hashes. This evidence bundle is unsigned and not a release qualification manifest.
- Original v1.0 portable strategy PDF remains a historical pre-implementation snapshot; current plan and this handoff supersede its old NOT STARTED status for Packet 1 only.
