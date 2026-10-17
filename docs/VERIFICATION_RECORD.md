# Tejas architecture hardening — verification record

## Delivered scope
Rulebook aligned to all5PDFs; explicit latest-user overrides:matte maroon, phone-only student convenience profiles. Source manifest includes each supplied PDF SHA256/URL/page count. Application hardening includes durable answer/start retry identities, atomic seal/outbox + async grading, bounded pilot job lanes/retries/fencing, private derivative cache, slim queries/pool budgets, bounded JSON, atomic staff rate limits, typed critical responses and resilient pending/retry UI. Full infrastructure/specification NOT complete.

## Executed evidence
- `test_reports/v5_final_backend.log`:27/27 API checks; includes8-way duplicate saves/starts, same-key altered-body conflicts, old receipt replay, no premature solution delivery, asynchronous submit/results and report job behavior
- `test_reports/iteration_19.json`:4scoped fault tests (dispatch gap, crash before dispatch, failing job attempt budget, done-report pointer preservation); these simulate application boundaries, not real infrastructure failures
- `test_reports/v5_json_limits_final.log`:6/6guards; duplicate keys, nonfinite numbers, >1MiB, >40nesting, normal requests, actual429RetryAfter
- `test_reports/iteration_21.json`:same-browser login/preflight/player, offline/reconnect, initialGETabort recovery, responsive light/dark; no public-fixture bypass
- `test_reports/iteration_22.json`:actual confirm-submit,202pending-grade→final, real downloaded PDF, failedreport→explicitretry→download; Studio read-only load check
- Main browser20261012_094650:result3/12 + realPDF download; both1920×800 and390×844 overflow[]
- Main browser20261012_094751:waited400ms for theme transition; darkheadericons computed readable palette; bothviewports overflow[]
- `test_reports/v5_frontend_build.log`:production frontend build succeeds without React hook warnings
- Python compile passes; backend/frontend services running
- `test_reports/qa_withdrawal.json`:50positively identified QA sets soft-withdrawn, **original75-question paper unchanged and stillreview**; attempts/ledgers/files/reportobjects retained
- `test_reports/v5_post_cleanup_final.log`:14/14 rechecked after fixing lax test assertions; catalogues contain no QA, former allowlisted student cannot preflight withdrawn paper, atomic8staffattempts→5×401+3×429, oversizedrevision422
- `test_reports/additional_verification.json`:existing student-owned attempt/report200, different profile404. "Owner" here means owner of the student attempt, NOT privileged staff

## Caveats, not hidden passes
Tests use synthetic/restricted QA content, real application APIs and controlled network/worker faults. No production API integrations are mocked. Some earlier test reports overstated code review as execution; use runbook/raw outputs to interpret evidence. Four fault tests currently execute in separate test processes because the harness binds Motor to its importing loop. Some guard paths remain review-only. The original75Q full100-page PDF was tested earlier; new job scheduling was then tested with small fixtures, not500kfull reports.

## Remaining blockers
StandaloneMongo singledeployment is not20independent cells. No distributed admission/writer-generation authority, relational lock-time acceptance/drain register, multi-AZ durability proof, independent workerfleet, parser sandbox, staffMFA/transactiongrants, KMS-signed activation/ObjectLock, privateCDN, regionalrestore drill or500kloadcampaign.40–60meaningful analytics are not complete. Existing acknowledged autosave is a custompractice policy, not the specification's official explicitcommit simulation.

Therefore: **hardened practice pilot; NOT500kqualified, NOT full-specification-complete, NOT production-capacity-certified.**
