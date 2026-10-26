#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

## Iteration 30 — exam isolation, diagrams, weak revision, NEET portable bank
user_problem_statement: "Separate JEE/NEET leaderboards using arena exam selection; quick Biology diagram cards; one-tap most-missed chapter revision; save all existing NEET content independently for future NEETLIVE.AI."
backend:
  - task: "Exam-scoped content, rewards, ranking, history and matchmaking"
    implemented: true
    working: true
    file: "backend/server.py, backend/gamify.py, backend/duels.py, backend/exam_groups.py, backend/exam_migration.py"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "Exam pinned at play creation; separate indexed profile XP counters; backward-compatible defaults Biology=NEET, other old play=JEE. Legacy awarded XP reconstructed. Existing WS/capped event transport unchanged."
  - task: "Idempotent missed-card events and revision"
    implemented: true
    working: true
    file: "backend/revision.py"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "Completed solo/duel incorrect+timeouts count, skips/unseen excluded. Most-missed unresolved active cards grouped by chapter; correct replay clears. Repeat completion does not duplicate misses. Legacy activity backfilled."
  - task: "Independent NEET source and export bundle"
    implemented: true
    working: true
    file: "neetlive/content, neetlive/tools/export_bundle.py, neetlive/README.md"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "7585 cards = Physics 2610, Chemistry 2095, Biology 2880; 18 original diagrams replace text within 90-card caps. Independent IDs for NEET PC, stable old Biology IDs. ZIP manifest/checksums; no personal data/secrets in default content bundle. Optional explicit owner private export only outside repository."
frontend:
  - task: "Exam leaderboard, Biology diagrams, one-tap revision"
    implemented: true
    working: true
    file: "frontend/app/(tabs)/rapid.tsx, frontend/app/rapid/session.tsx, frontend/app/rapid/duel.tsx, frontend/src/components/ArenaLearning.tsx, frontend/src/components/ExamLeaderboard.tsx, frontend/src/components/BiologyDiagram.tsx"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: true
        comment: "Self-smoke at 390x844: pilot login, NEET toggle, diagram sprint 18 cards, SVG prompt, option feedback, return and NEET leaderboard PASS. Need complete play/revision, exam-switch cache isolation, 320px overflow, all 3 drawings and duel regression. tsc --noEmit passes."
test_plan:
  current_focus: ["Exam scoring/match isolation", "Revision idempotency and clearing", "Diagram correctness/rendering", "Portable NEET export", "Existing sprints/duels/WS regression"]
  stuck_tasks: []
  test_all: false
agent_communication:
  - agent: main
    message: "Read test_credentials.md. Main browser smoke passed; external URL from frontend env. Legacy unscoped catalog/cards returns canonical JEE + Biology, scoped exam=NEET includes independent PC copies; old raw DB total assertions must now filter exam. Please write iteration_30 tests/report. Do not invoke generation/audit scripts or reset DB."
  - agent: main
    message: "Iteration30 passed 10 new +13 regression cases. Follow-up16/16 includes rerun10 new +6 WS checks; 29 unique backend cases total. Mobile320/390 diagram+revision passed; main verified NEET invite/quick-match/complete/rematch/solo/start-another. See iteration_30_followup.md. User verification pending; no known blockers. Private data migration and physical-device/capacity tests not performed."

## Owner ZIP download follow-up
- User requested an actually downloadable NEET ZIP and explanation of independent backend/app/website copying.
- Added an owner-issued 256-bit expiring bearer capability, issued only by trusted-workspace CLI (`backend/tools/owner_download.py`). Only token SHA256 stored; 24h max, explicit expiry/revocation/type/content-hash validation, no HTTP mint endpoint, no learner-header authorization.
- `GET /api/owner-downloads/{token}` returns the fixed existing ZIP as attachment/no-store/nosniff/no-referrer. Exact bytes are checked and returned without path input or replacement race. Uvicorn access log token is redacted; upstream infrastructure logging is not controlled by this app.
- Needs backend tests: valid ZIP/header/hash, invalid/malformed/expired/revoked/type-mismatched/changed-hash grants denied, public mint unavailable, learner header cannot grant access, stored token digest only, CLI revocation and TTL index, no regressions to NEET catalog.
- Final verification:10/10 pass (`test_reports/pytest/iter31_owner_final.xml`). The first run's sole failure was exact Cache-Control equality; the edge keeps no-store and adds no-cache/must-revalidate. Corrected test to require no-store and disallow public/max-age rather than a specific ordering/string. Owner link to be issued only after this verification; no raw token stored in reports.

## Iteration32 — live website theme + direct JEE Main PYQ flow
- User: match changed jeelive.ai theme; replace JEE mocks with new PYQ/solutions. Chosen flow: Mains card -> PYQ -> direct full list, Start / Continue / Result+Re-attempt, minimal clicks; year+shift grouping.
- Implemented Figtree and verified live charcoal/red website tokens, new native brand/exam cards and hub, primary/semantic contrast fixes. BITSAT/COMEDK mocks and chapter practice retained. JEE old catalogue?kind=mocks redirects to /pyq.
- New /pyq list uses real existing student GET /pyq/jee-main through unchanged cookie-session proxy/native direct API. No demo or fabricated app data.
- One-tap start performs fresh server status check + existing preflight + persistent idempotent start key; retries preserve key, per-user/set single-flight. Continue reads exact saved attempt and NEVER starts a new one; sealed attempts route to result. List focus/pull refresh, visible per-row errors, dynamic year/shift filters.
- Supplied solutions retain source-image/question-ID mapping, zoom and answer-key-only honesty; supplied typed question/solution maths now renders with bundled native KaTeX, readable web fallback. No AI-generated replacement for uploaded solutions.
- IMPORTANT LIVE BLOCKER: live authenticated GET https://jeelive.ai/api/pyq/jee-main returnsHTTP200 total0/items[] (also through preview). Correct upstream/config confirmed by independent troubleshooting. Uploaded/staged admin state cannot be inspected; owner needs to check publication/student visibility. Do not mark real PYQ start/submit/solution mapping fully verified with this empty dataset.
- Main checks: tsc and JS lint passed. Preview390/320 confirms new home, Mains->PYQ direct two-tap route, actual0 empty state + refresh, no horizontal overflow. Initial screenshot selector typo was fixed to source testID home-tile-jee-main; app itself rendered correctly.
- Testing needed: test-only fixture scenarios for all button states, one-tap sequence, duplicate prevention, failed start same-key retry, new reattempt newkey, stale active->result no POST; navigation/filter/error/empty/narrow; existing result supplied image/typedmath/answerkey and RF/NEET regression. Keep fixtures isolated to tests, never seed or publish fake live PYQ data.
- Iteration32 report read;4/4 live backend checks passed and real UI navigation/layout/redirects/RF passed. Isolated fixture contract tests passed; main fixed grading hint/result-release logic and verified genuine new-key reattempt. Narrow Re-attempt label now single-line. Existing generic Header back-ID collision found during cleanup was removed for new hub/PYQ screens with explicit unique IDs. No fixture data shipped.
- Remaining P0 is EXTERNAL: real upstream PYQ list still0, so real-paper solve/submit/solution-mapping E2E remains pending publication/visibility by backend owner. Do not mark this as a fully verified real PYQ feature until live rows exist.

## Iteration33 — authoritative PYQ contract + source-environment investigation
- User provided latest public GitHub repo and authorized Go; wants actual website/app shared backend, not a duplicate question bank.
- Found and corrected REAL local frontend bug: blanket `live_enabled:false` checks incorrectly rejected ordinary PYQ practice. Source catalogue permission contract only uses this flag for import/chapter event content. Removed checks in `frontend/src/api/pyq.ts`; count/state/permission checks otherwise retained.
- Verified actual source-project API returns30 genuine papers/2250 questions and separate pilotUIDaac7961a-b3df-4c14-a422-c5c46ab022f4. Current jeelive.ai API returns0 and its known packagepaper IDs404, currentpilotUIDdb0c62b8-eeaf-41be-b8b1-05f5f34ac1d8. Separate identities/data; app URLs remain unchanged. Credentials notes updated for separated test contexts.
- Need regression test falseflag ordinaryPYQ remainsnew/startable and auth/preflight failures stillblock. Prefer real source-project API for academic end-to-end, without changing persistent appconfig or importing data. If temporary browser transport forwards to real sourceproject, explicitly report that it is isolated testing, not mainappswitch or fakeAPI.
- Three earlier manual website-browser trace attempts failed due harness assumptions (loginignoresnext, freshcontexts, authhome notlandinganchors), not duewebsiteauthfailure. Testing agent shouldinspectDOMcontrols afterlogin insideonescript andcaptureactualrequest; no guessedselectors orcacheadvice.
- Iteration33 real API suite3/3passed, includingfalseflagpractice,sourcequestions75,sourcequestionimage200,pre-submit solutionlock,save/resume,submit/results,re-attemptidempotency.
- Main follow-up isolated browser forwarded actualHTTP tosourceproject (notfabricatedresponses): rendered30realpapers inapp,Startwithfalseflag,answerSave/Continue sameID,submit,75questionresult,providedsolutionimages200/render/zoomat320,Re-attempt newID andoriginalresultpreserved. Test signedout/forwardingremoved; persistentappconfigsunchanged. Initialtestassert expectedrows,actualcontractquestions75; correctedtestonly, appalreadyhandledit.
- Codefix verified. Remainingcriticaldecision: retainjeelive.ai'sexistingidentity/history andsyncmissingpaperswithwebsite-owneraccess, or explicitlypointappatworking30-paperproject'sdifferentidentity/history. Never switchorimportsilently. Awaiting ownerconfirmation.
- Owner confirmed keeping currentjeelive.ai history and requested100%sharedbackend. NO preview switch. Live protected-import probe: anonymous401/learner403; currentPYQ0; websiteRFcatalog404. No writes performed. Secure owner credential collection needed for canonical PYQ sync; fullRFsharing requires website-side integration/migration and is not already complete.
- LATEST USER SCOPE OVERRIDE: shared backend is required EXCEPT Rapid Fire. Keep RF separate and do not treat RF404 on canonical website as a blocker. User asks for website-project handoff covering academiccontent/solutions, authidentity/history/results and exact design/card-theme parity. Handoffdocument updated accordingly.

## Iteration35 — complete native theme mapping + newly available canonical PYQs
user_confirmation: "Theme aur UI checks; Pehle PYQ availability check. Abhi confirm nahi. 100% same content except rapid fire."
frontend_theme:
  implemented: true
  working: NA
  needs_retesting: true
  files: ["frontend/src/theme.ts", "frontend/src/components/ExamTile.tsx", "frontend/src/components/ExamCardFinish.tsx", "frontend/src/components/ExamHub.tsx", "frontend/src/components/LearningTheme.tsx", "frontend/src/components/PyqPaperCard.tsx", "frontend/src/components/ui.tsx", "frontend/app/(tabs)/index.tsx", "frontend/app/(tabs)/tests.tsx", "frontend/app/result/[id].tsx"]
  status: "Owner CSS exam colours, native sheen/pause/reduced motion, responsive title wrapping, PYQ spacing, learning badges/top borders, maroon score, 5-colour result tabs. Fixed two pre-existing unfinished compile errors (Press accessibility props, unavailable navigation import). Academic/auth/RF data code unchanged. tsc + modified JS lint pass."
main_smoke:
  result: "PASS: real canonical pilot login, home exam colours, pause switch, JEE hub -> PYQ, 30 real papers, year filter, 390/320 preview."
  artifacts: ["theme-home-390.jpeg", "theme-jee-hub-390.jpeg", "theme-pyq-390.jpeg", "theme-pyq-320.jpeg"]
live_data:
  result: "Canonical GET /pyq/jee-main now returns30 real papers/[2026,2025]. Old external empty-list blocker no longer reproduced. NO source-project switch, import, fake responses or seed. Need real canonical E2E now."
test_plan_iter35:
  current_focus:
    - "Theme switch/animation, all3 exam hubs, responsive320/390; no clipped labels/overflow; My Tests library and all5 Results tabs"
    - "Canonical direct vs app proxy existing identity, all PYQ metadata, chapters/mocks/live catalogue parity, history/result/question/solution consistency"
    - "One actual new canonical PYQ on approved pilot: Start -> answer saved -> leave -> Continue same ID -> submit -> Result -> supplied solution images -> Re-attempt newID, old result preserved"
    - "Read-only Rapid Fire JEE/NEET catalogue/leaderboard and arena smoke; do NOT change RF data or migrate it"
  special_instructions: "Run first4 iteration34 parity tests; fifth has obsolete RF migration assertions, DO NOT treat missing canonicalRF as blocker. Existing pilot9000000001 in memory/test_credentials.md; keep canonical UID. New academic test attempts allowed ONLY on this approved pilot for E2E, log their IDs, never modify old attempts. No mocks/interception/source-environment redirects. No auth changes/OTP. Do not run opt-in RF mutation seed or external-source iteration33 tests."

iteration35_final:
  working: true
  needs_retesting: false
  backend: "9/9 parity tests passed, no skipped cases. See pytest/iter35_parity_final.xml. Includes new75-question result signatures and original question+solution image hashes."
  frontend: "Main real UI E2E passed: Start->source image->saved response->leave->Continue sameID->submit->result->supplied solution/zoom->Re-attempt newID->old result preserved->My Tests. Theme/3hubs/320+390/pause/accessible states and read-onlyRF NEET/JEE board/chapter checks passed."
  followup_fixes: "Test-only repeated logins fixed to session reuse;429 cooldown recovered with no auth policy changes. Corrected actual accessibility selected/checked forwarding and nested My Tests compare buttons. Follow-up verified no nested buttons or accidental compare navigation; final console only expected canceled request on navigation."
  final_report: "test_reports/iteration_35.json"
  artifacts: "test_reports/artifacts_iter35/followup/"
  live_state: "PYQ30 available; BITSAT50 mocks; COMEDK0 mocks in canonical website and app alike. No local replacements. RF separate by explicit scope."
  limitations: "Physical-device QA pending. Source equality verified for listed endpoint samples and75 question signatures, not a claim of every asset/device/signup path tested."