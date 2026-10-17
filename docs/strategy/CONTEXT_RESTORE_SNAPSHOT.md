# Context restore — read before implementation

**Snapshot v1.0: strategy reference, not an implementation or capacity certificate.**

## Latest user decision

The user approved reading the strategy/audit/rulebook and implementing **Packet 1 only**. Their immediate priority is: “Give me first 10 packets pdf so that whenever you forget i will send you back”. This export is delivered before Packet 1 application changes.

- **All 10 implementation packets: NOT STARTED at this snapshot.** Packet 1 is approved to begin after this PDF is delivered; no packet exit gate has passed.
- Student entry must remain **phone-number only, without OTP/password**. It is not verified phone ownership or verified candidate identity.
- The UI must remain **matte maroon (#5C0025)**. Strengthen staff authentication separately.
- Investigate the exposed staff credential safely; obtain **separate user confirmation before rotating the persisted credential or invalidating staff sessions**. No rotation/revocation happened during this export.
- Do not claim support for **500,000 concurrently active exam attempts** until all required qualification gates pass for the declared deployment.

## How to resume in a later session

1. Read this handoff, the complete 10 packets, workload contract and qualification appendix. Treat them as a versioned snapshot, not evidence that code was implemented.
2. Re-read the current repository plan and compare source hashes in this PDF against current documents. Newer verified evidence and explicit user decisions supersede this snapshot; do not revert completed work blindly.
3. Review the audit, errata and current runtime. Follow Packet 1's actual scope: authoritative requirements, API/data contracts, safe regression baseline, authorized containment and evidence registries.
4. Keep permanent defect repairs in their assigned packets: A05/A06/S01 in 04; A02/A03/A04 in 05; A01 in 06; F01/F02/F03 in 07. Do not call a failing reproduction a fix.
5. Confirm critical security operations separately, run independent tests for any code changes, and update the plan/handoff after each packet.

## Repository and runtime boundaries

- Backend: FastAPI, domain modules under `/app/backend/tejas/`.
- Frontend: React, Shadcn and Tailwind under `/app/frontend/src/`.
- Database: current pilot MongoDB; the audit describes a shared standalone writer, not independent live cells.
- Strategy: `/app/docs/strategy/TEN_PACKET_STRATEGY.md`, `SLO_AND_WORKLOAD.md`, `QUALIFICATION_AND_HANDOFF.md`.
- Audit: `/app/docs/audit/AUDIT_REPORT.md`, `REQUIREMENTS_MATRIX.md`, `RULEBOOK_ERRATA.md`.
- Rulebook: `/app/docs/RULEBOOK_ARCHITECTURE_V5.md`; read with errata. Its legacy “40 analyses” statement is wrong: **all 60 are required**.
- All application APIs remain under `/api`. Never rewrite the existing `REACT_APP_BACKEND_URL` or `MONGO_URL` values.
- Infrastructure provisioning, DB administration, SSL, CI/CD and production deployments require authorized operators, not silent builder changes.

## Evidence limitations and known gaps

The existing strategy still says “proposed for approval” because its original text is preserved. The latest user decision above approves Packet 1 sequencing; it does **not** sign off provider choices, exact proposed SLOs, budgets, academic publication or production readiness.

The strategy references `coverage_manifest.json` and `COVERAGE_MATRIX.md`, but those files were **not found in the current docs inventory**. They are not supplied as verified coverage. Packet 1 must resolve that gap and expand the 62 audit rows into atomic mandatory-clause traceability. Page counts and an inventory are not proof of complete requirements coverage.

Existing audit observations and test counts are historical, not re-run during this PDF export. Services were running at export preparation; that check is not functional or load qualification. The original paper remains unapproved according to the audit; do not publish it to make testing easier.

This PDF includes the full three strategy documents, full audit and errata, the 62-row requirements matrix, the 60-analysis status inventory, and source identities/hashes. The original five specification PDFs (177 pages) are **not embedded or reproduced**. Keep them with this reference when complete clause-level authority is needed. No raw test reports, source-document credentials, private URLs or live secrets are included.

## Status to carry forward

- Working practice MVP and matte-maroon/phone-only choices exist; correctness and security gaps remain open as documented.
- Leaked staff credential: **rotation/revocation still pending**.
- Independent worker fleet, PostgreSQL live cells, full analytics and load/fault/restore qualification: **not delivered by this document**.
- Next development action: **execute Packet 1 only**, after delivery of this reference.
