# Test runbook and evidence interpretation

Use environment-provided frontend/backend URLs and database names. Never print credentials. All QA sources stay restricted; never publish the supplied original paper to unblock a test.

## Browser selectors (verified against current code)
- Phone input: `student-login-phone-input`; Continue: `student-login-continue-button`
- Preflight: `device-test-answer`, `preflight-run-check`, `preflight-check-success`, `preflight-acknowledge` (Shadcn role=checkbox), `set-preflight-start-button`
- Player: `player-option-1` (option identifier varies), `player-numerical-input`, `player-next`, `player-save-state-indicator`, `player-submit-button`
- Confirmation: `confirm-accept` (**not** confirm-action)
- Results: `results-grading-pending`, `submission-receipt`, `grading-status`, `grading-retry`, `grading-back-home`, `results-score-total`, `results-download-report-button`
- Original/corrected: `score-version-original`, `score-version-{key_version}`; late-draft notice: `late-draft-notice`
- Theme: `theme-toggle`; drawer: `mobile-menu-button`

Keep login and navigation in the SAME browser context. After Continue, wait for `/home`; hard navigation then bootstraps `/api/auth/session` before `/api/my/sets/{id}`. A fresh context is not authenticated. Never treat a correct restricted-public404 as a publish-permission bug. Main and iteration21 confirmed hard navigation/session persistence.

A modal drawer intentionally blocks background controls: close it before clicking the header toggle. Wait400ms for theme/drawer animations before contrast/overflow checks. Only screenshot viewports1920×800 and390×844. Inspect actual rendered pending/final states, not just code.

## Scripts / evidence
- `backend/test_v5_architecture.py`:27 API checks; latest actual stdout `test_reports/v5_final_backend.log`. Includes8 concurrent identical saves and8 starts. This is a small correctness test, NOT a load certification. Some history/visit checks accept terminal-state conflicts, not performance evidence.
- `backend/tests/run_fault_tests.sh`: four scoped fault/recovery tests; each runs in a separate process due Motor event-loop binding in the test harness. This limitation is not fixed by production config. `iteration_19.json` records execution. Enqueue gap is an application-boundary simulation; no machine/AZ was actually crashed.
- `iteration_20.json`: four actual JSON rejection tests and regular request test passed. Its fixture and drawer conclusions were invalidated by main reproduction and iteration21. Invalid-schema422 does not test throttling429.
- `iteration_21.json`: actual offline/reconnect and initial-fetch network-abort recovery; desktop/mobile light/dark and historical PDF download. Do not adopt its generic production-readiness claim.
- `iteration_22.json`: actual confirm submission, new report download, failed-report explicit retry, real202 queue-pending UI→grade and read-only Studio check. Retry cross-parent guard in that report was CODE REVIEW ONLY, not executed proof.
- Main screenshot session20261012_094650: authenticated result3/12, actual PDF download, desktop/mobile overflow[]; session20261012_094751: settled dark icon contrast verified, both viewports overflow[].

Runtime APIs are real, not mocks. Tests use temporary synthetic/restricted QA data and controlled network/worker/queue fault injections. Such injections are not evidence of regional resilience. Withdraw QA sets after testing; preserve attempts/reports as evidence. The original75-question source remains review-only until human academic/accessibility approval.

## Continuing safely
Run test fixture provisioning only in an explicitly authorized test environment. Source config from dotenv; mark fixtures at top-level `qa_only`, never inside answers. Track exact IDs and archive via the owner withdrawal API. Do not edit .env or weaken audience/rights gates to make a test pass. Do not run distributed saturation traffic against this shared preview.


Eight one-off or obsolete pre-async-grading/deadline helpers are preserved as non-executable `.py.txt` evidence under `test_reports/archived_helpers/`; they must not be collected as current tests or rerun to recreate published fixtures. Current CLI runners require environment configuration with no hardcoded URL/database fallback. The final cleanup runner was tightened to inspect `data.items` instead of treating an unrecognized shape as an empty list, use valid-length save IDs, require revision422, and require exactly5×401 +3×429 on the8-request throttle check.
