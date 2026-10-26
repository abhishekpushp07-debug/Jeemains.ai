# RCA — jeelive.ai /exams/jee-main/pyq empty (run 0e4feee4)

## Problem statement
Live page https://jeelive.ai/exams/jee-main/pyq renders empty. Expected: 30 date-wise JEE Main PYQ papers (2250 questions). Actual: nothing. Requested action: execute the already-approved additive PYQ import into the EXISTING production DB using the deployed importer, idempotently, preserving all existing data.

## Confirmed root cause (read-only evidence)
Inspected the ACTIVE run's production DB `campus-search-debug-test_database` via read-only mongo_query:
- `tejas_sets` total = **222** (matches the known baseline; intact).
- `distinct(exam)` = `["BITSAT","JEE Main"]`.
- `count(exam="JEE Main")` = **78**, but `count(year != "")` across all sets = **0** — every set has `year:""`.
- `tejas_smart_papers` count = **0**.
- Sampled JEE Main sets are chapter-wise practice (`profile_mode:"practice"`, `status:"published"`, titles like "Kinematics"/"Laws of Motion"), i.e. NOT date-wise PYQ papers.

Conclusion: the page is empty because **zero date-wise PYQ documents exist in production**. The 30-paper / 2250-question approved bundle was never imported or published. No existing data is missing or corrupted — the gap is purely the un-imported PYQ content.

## Why the Deployer Agent did NOT perform the import
This is a production DATA MUTATION, and no tool in the deployment toolset can perform it:
- `mongo_query` is strictly read-only (find/count/distinct/list_*). Writes are impossible by design.
- There is no tool to invoke the deployed `/api/studio/pyq-import/step` endpoint, nor any tool to open an authenticated owner session against the live app.
- The ephemeral sandbox (`spawn_eph_pod`) injects NO app secrets and cannot reach the live DB or third-party APIs, so it cannot run the real importer against production.
- `resume_pipeline` only re-fires a deploy of the built image — and a redeploy is explicitly out of scope (preview PIN/student-directory code is UNTESTED and must not ship).

So the import must be executed by the OWNER/USER operating the already-deployed importer against production with their owner-authorized session/credentials — outside this agent's capability.

## Required executor & guardrails (for whoever runs the import)
- Executor: the app owner, via the already-deployed importer (`/api/studio/pyq-import/step` or equivalent validated importer logic) with the production-configured owner identity/credentials — NOT preview/guessed credentials.
- Source: `backend/resources/jee_pyq.json.gz` + manifest (30 approved papers, 2250 Qs, 90 records = 30 files / 30 versions / 30 sets). Incomplete 23-Jan-2025 S1 stays BLOCKED.
- Re-verify all 30 private original PDF hashes via the importer before publishing; stop on any hash/content conflict (importer is idempotent / resumable / lease-fenced).
- Preserve everything: 222 existing sets, all users / phone_profiles / attempts / credentials / old content. Do NOT reset / delete / migrate / overwrite / change secrets / run any student-reset.
- Record pre-existing academic-content hashes/counts; after import, compare EXCLUDING the new bundle IDs to prove nothing else changed.
- Acceptance: 30 published PYQ papers, 2250 questions, authenticated catalogue returns 30 date-wise papers, sample original question/solution delivery verified via READ-ONLY checks (no test-attempt / student creation). Close ONLY the operational auth session opened for the import.
- Do NOT redeploy: untested preview PIN/student-directory code must not be shipped by this operation.

## Current verified state (post-check, nothing changed by this agent)
- 222 sets intact; 0 PYQ (0 sets with a year; 0 smart_papers). Baseline recorded for post-import comparison.
