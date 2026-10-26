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

## Iteration36 — owner ZIP authoritative adoption
user_request: "ZIP integration source, canonical https://jeelive.ai/api only; preview URL download-only; RF untouched; preserve existing IDs/history; no PIN cutover. Existing pilot records compare karo, uske baad pilot test bi."
status: "Implemented; main smoke PASS; extended testing pending."
source: "reference/integration-2026-10-26/APP_INTEGRATION.md + design-tokens.json; adoption details NATIVE_ADOPTION.md."
changes: "Source-driven layered home blue/platinum,amber,teal,ruby/onyx; original managed-storage logo; exact font files/licences/icon paths; academic dark status states; black/crimson hubs; real-only series schedule placeholders. Root RF tokens, auth, API routing unchanged."
verification_so_far: "Before pilot writes,9/9 current canonical parity checks passed(-n0). Original logo GET200, bytes/hash match supplied SVG. tsc/lints passed. Real existing learner home/PYQ30, mobile390/320, all4gradients, pause switch, other-page dark hub passed. No new pilot writes yet."
test_next:
  - "First read-only compare existing identity/history/result/resume to canonical;30 packaged paperIDs & sum2250. Do not open old attempt in player (visit writes); readAPI only."
  - "Then user-approved fresh pilot UI scenario on untouched paper; at most2 new attempts including full reattempt. Old7completed + existing active attempt must stay unchanged. Two independent canonical sessions compare saved state/results/source assets; test stale revision rejection only on NEW test."
  - "Compare token layers/source fonts/logo; selected/disabled/reducedmotion;320/390; private source white/unfiltered; original-source assets order; RF read-only smoke."
  - "Use phone9000000001 approved existing pilot from memory/test_credentials.md, never source-project account. Login once per session, run-n0, stop on429/Retry-After. Never seed RF, create new accounts, call PIN endpoints, swap envs or log cookie/identity/answer dumps."

iteration36_user_correction:
  priority: "P0: restore original card artwork. User explicitly rejected replacing target/diamond/rocket/crown with website SVG symbols. Keep JEELIVE theme elsewhere."
  implemented: true
  main_verified: "Exact4 original JPG files hosted via public managed storage and byte-compared. Restored image-top2×2 layout/dark text panels; no colour filters. Removed ExamGlyph. tsc/JS+Python lints PASS. Screenshots390/320 show correct4 artworks; JEE->PYQ30 navigation passes."
  testing_agent_scope: "Verify correction first, all4 destinations and320/390, then existing-record read-only comparison and previously authorized ONE fresh pilot. Do NOT change original icons again even if ZIP tokens differ. Live banner keeps source ruby/onyx."

iteration36_final:
  working: true
  needs_retesting: false
  result: "PASS: original4artworks, byte/hash identity, managed logo, all4destinations,30paper/2250questions, reducedmotion/banner-only switch. Tests11read-only passed; partial optin script intentionally not used. Main fulfilled user's earlier fresh-pilot approval via ONE actual UI flow (notanotheraccount), full result/solution and existing record preservation checks passed."
  assets_configuration: "Backendbranding endpoint now uses explicit BRANDING_STORAGE_URL only; no module fallbackhost. Backend restarted; final5/5 publicassets hash tests pass. No academic auth/RF changes."
  fresh_pilot: "Completed. Minimal ID stored memory/test_credentials.md, no newpublicidentity/answer dumps. Source sample75questions/results equal; sampled originalquestion+solution imagehashes equal direct/proxy."
  transient_harness_issue: "Chromium SIGSEGV before first launch script did not create anattempt; troubleshoot confirmed transient, one retry succeeded."
  context_correction: "Owner evidence filename is evidence/canonical-pyq.json, not pyq-live-index.json. It exists and30IDs/sum2250 match."
  remaining_scope: "PhysicaldeviceQA and previewPIN rollout/authhardening are separate backlog, no cutover. User must never again have original4cardartworks replaced during globaltheme work."

## Iteration37 — remove NEET from this Rapid Fire app, preserve archive
user_request: "Neet ug hata do bhai rapid se wo toh tumne alag zip rkha na bna kr"; choice: "Archive mein safe rakho".
implemented:
  - "JEE-only lobby (Physics,Chemistry,Maths), no NEET toggle/Biology shortcut; leaderboard/recent/revision scopedJEE. Shared coins/XP/streak not reset. Home original4artworks and globaltheme unchanged."
  - "Backend central active-exam boundary: default lists areJEE-only; explicitNEET gets410. Guards block NEET creation, repeat-request reuse, review/completion, invitation joining, duelmutations/settlement andWebSocket access before writes. Oldrecords retain original schemas/data."
  - "NEET bank excluded from live periodic sync; files/ZIP/records not deleted, retired or moved. Logicalarchive: inaccessible in current learner APIs, preserved forowner."
preservation_baseline: "test_reports/iter37_archive_baseline.json includes NEET rf_cards8083(allinclretired),sessions32,duels11,awards10,learning_events8,oneprofileNEETsegment and ZIPhash9b51ca14..."
main_checks: "tsc and changedJS/Pythonlints pass. RFcatalog default JEE/7045cards/3subjects; NEET410. ZIP exists1055634bytes and ziptestpasses beforeedits. Need AFTERhash equality and JEEregression tests."
external_auth_blocker:
  - "Canonical POST/auth/phone was200at18:08; nowphone-only422at18:39. Public /api/openapi.json nowrequiresphone+pin, verified byintegrationexpert+troubleshooter. This is externalPINcutover, notourRFchanges."
  - "No usable approvedexisting session among8newest nonemptyjl_jars checked withGETauth/me. Never guessPIN, reset/createaccount or fakeauth. No auth/canonicalURL changes made."
  - "Main screenshot loads entry but cannotfreshlogin. Authenticated frontendlive verification currentlyBLOCKED. BackendRF X-RF-User testcontract remains operational; isolatedtests notequivalenttoliveUI."
test_scope:
  - "Verify exactarchive baselinecounts/hashes using actualbackend.env MONGO_URL+DB_NAME; doNOTinfer0NEETdocs from APIavailability. They MUST remain8083."
  - "TestJEEcatalog/cards/history/revision/leaderboard, transientQA-onlysolo/duel flows. No canonicalacademic writes, no realpilotwallet changes."
  - "AttemptNEETquery/create/legacyBiology/archivedrepeat/get/complete/dueljoin/get/actions/websocket; assertreject andnoarchivechanges. Never deleteorreset existingNEETrecords."
  - "Frontend noNEETtoggle/Biology shortcut; archiveddeeplinkstops beforePOST; checkTypeScript and isolatedcomponent/staticproof ifcannotauthenticate. ReportliveUIblocked honestly."

iteration37_final:
  implemented: true
  backend_working: true
  backend_tests: "Final17/17PASS/no skips, pytest/iter37_neet_archive_final.xml. Initialagent14/14; main tightenedJEEduelanswer to200 and added explicitNEETcreation/default-history/finalpost-testhash checks."
  archive_preserved: "Exactall5NEETcollection counts/hashes, NEETprofilestats segment andZIP bytes/hash unchanged aftereveryrequest. No archiveretire/delete/move; original schema retained andliveNEETsyncdisabled."
  frontend_status: "JEE-only source/typechecking passes; noNEETselector/Biologyshortcut, archiveddeep-link guard. LiveauthenticatedUI retestpending: canonicalPINnowrequired, appphone-only422, no validapprovedsession. No claim ofliveUIpass."
  needs_retesting: true
  next_scope: "Owner-coordinatednativePINclient/recovery; onceauthenticationworks, verifyliveRapidUI. Do notmodifyauthorresetaccounts justtofinishNEETremoval."

## Iteration38 — live PIN auth client implementation (testing)
user_scope: "Live PIN pushed; update app login/signupConfirmPIN/PINchange/ForgotPIN. CanonicalAPIonly,existingaccounts/resultspreserved,RFuntouched. User suppliedsecuretestPHONE/PIN then 'Keys added, please continue.'"
implementation:
  - "PINlogin and explicitsignup tabs,4ASCII-digit stringvalidation, leadingzeroes preserved, confirm mismatchbeforePOST; maskedPIN/visibilitytoggle; noPINstorage/logging. Real canonical endpoints, nophonefallback."
  - "New signed-in change-pin route confirms ownmobile,newPIN/confirm; respects other-sessionrevocation, verifies sameauth/meID aftersuccessfulchange; no accountreset. Account buttons, new PINhelp route."
  - "ForgotPIN is honest guidance: liveOpenAPIonly/auth/pin, noforgot/reset/OTP. Existing signed-insession→ChangePIN; otherwise existingofficialadmincontact. Noinventedrecoveryendpoint/contact ormessage-send."
  - "Authbootstrap only trusts canonical/session, no cached-profileauth. Expired401 clearprivateuser/cache, preserveaccountdrafts; logout guardpreventsofflinecookieauto-login; refreshsingleflight+oneretry, explicit429countdown, noautomaticPINretries."
  - "Same nativecanonicalcookie transport and webper-SIDproxy, Constantsconfigfallback; no serverauth/RFcode, brand/cardicons or DBedits. Physicalnativecookiepersistence stillunverified."
main_checks: "tsc+JSbatchlints pass.390login/signup mismatch andForgot guidance screenshotspass; foundrepeatedentry stack onhelpreturn, fixedtodismissTo; no livePINsubmitted yet bymain."
testing_scope:
  - "Use securebackendJEELIVE_TEST_PHONE/PIN withoutprinting. Loginoncepersession, readonlycompare directcanonical vs appproxyID/history/PYQ30/sourceimages ifexistingresult. No guessedPIN, noreset/signup/changePIN on approvedaccount. Stopifcredentialsrejected."
  - "Validate webUIlogin→home→reloadpersist→AccountChangePINform+localmismatch/noPOST→help→logout→privatedeep-linkblocked→relogin. TestpreviousiterationJEEonlyRFUIreadonly (NEETabsent). DoNOTstartRFsession/changeavatarwallet."
  - "Isolatedunit/contracttests fornew-signup+PINchangerequestshapes/malformed4digits/leading0; don'tlabelisolatedpositiveasliveproduction. Signupsuccess/PINchangeidentity-revocation NOTauthorizedonrealaccount."
  - "Rate/offline/refreshprivate-cache behaviour canbeisolatedtransportharness; nofakeprodAPIorappdemo. Reportactual vsisolated scopeandany untestedpositivewrites honestly."

iteration38_current_status:
  implementation: "PINscreens and canonicalrequest wiring ready; authenticatedverificationBLOCKED."
  verification: "Public390/320Login/SignupPINmask/leading0/localconfirmation/Forgotguidance/oneentrybackroute/privateauthgate PASS. Changedauthfiles strictprojecteslint andtsc PASS aftermainfixed6lintissues."
  blocker: "Suppliedsecurephone/PIN got401directcanonical andproxy, oneattemptperchannel. No retryguessing/reset/registration.7dependentbackendcases correctlySKIPPED, NOTpassed. Runtimeenvmatches savedsecrets. RequestsecureworkingLIVEcredentials."
  report: "test_reports/iteration_38.json"
  risks: "No publicForgotPINresetAPI; guidanceonly. Positive signup/PINchangewrites notauthorizedoncurrentaccount. Nativephysicalcookiepersistencenottested."

## Iteration39 — subjectnavigation + aggressive private image preload (implemented, verificationpending)
user_choices: "Subject tabs + question grid; Ready hote hi start. Questions download ho jane chiye background me as soon as possible taki navigation butter smooth ho."
changes: "Priority4-slotdedupqueue/48MiBmemorybudget; all permitted crops backgroundload,current/subject priority; no disk/publiccache; blobURLsforweb/nativeRAMdataURI; activeaccountscope,cancel+purge/logout,retry429respect. Player subjecttabs/subjectgrid/lastquestionmemory/Nextsubject, visibleimagegatesanswers. Results allreleasedquestion+solutionpreloadduringAnalysis, versionedsourcepaths,responsivegrid. ReusedpreflightReadySheet(no30s), no/startuntilStartnow, ContinueexistingID."
source_truth: "reference/PLAYER_LOADING_CONTRACT.md. NO pre-startimage endpoint exists;preflightnotdownload. Can'tpromiseallpaperbeforeclockwithoutcanonicalprepare/activate. Start_keyremainsUUIDnotPIN. Noauthfallback/staffassetuse/RFchanges."
checks_so_far: "Latest tsc+fullESLint overchangedfiles PASS; generallintPASS. Needunit/isolatedtests. LivePINstoredpairpreviously401,userpausedkeyupdate; DONOTretrybadcredentials. SecurecorrectPINneededforlivepaint/networktimings andJEEUI."

iteration39_verification:
  implementation: "ReadyforliveQA; noAPI/content/timer/RFbackendchange."
  tested: "Final17/17isolatedunit/contracttests PASS; actualqueueclassandnavhook testedwithsyntheticloader/statefixtures. Includes75/150normalimages simulated,dedup,reservedslot,48MiBbound,pinnedLRU,abort/latecomplete/pause/groupcancel,429retry,croporder,subjectmemory/fiveunevengroups/gridfit,bonus/release/versiongates,readinesspreflight/startUUID."
  live_smoke: "Hosted390main/375agent appentryrenders,noerrors. No authenticatedfixtureoroldcredentialretry."
  static: "Strictprojecteslint allchangedfiles + tsc PASS afterfinalfollow-up."
  pending: "UpdatedsecureworkingLIVEphone/PIN needed. Liveplayernavigation/sourcequestionmetadata/actuallatency/solutionwarmup E2E unverified. Localhostcross-originCORS isexistingnonrequiredtestorigin issue,hostedworks."
  user_action: "User skipped securecredentialupdate afteriteration39 implementation. No more credential attempts; safehandoffwithliveverificationpending."