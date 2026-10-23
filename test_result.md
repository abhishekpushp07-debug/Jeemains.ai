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

user_problem_statement: "Latest explicit scope: Sirf remaining automatic work pause karein. Pause automatic mock/chapter solving and legacy work without deleting saved AI/owner solutions. No new manual Solve controls, source baseline UI, checkpoint 02 or redesign authorised in this slice."
backend:
  - task: "Automatic AI pause and preservation"
    implemented: true
    working: true
    file: "backend/tejas/mock_solutions.py, ai_solutions.py, jobs.py, smart_imports.py; backend/server.py; tools/solution_worker.py"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: NA
        agent: main
        comment: "Removed lifecycle spawn/keeper; code-enforced pause guards discovery, claim, direct solve, worker, spawn, keeper, legacy ensure/process, queue creation/retry/drain. Maintenance excludes AI; imports do not solve/requeue; review confirmation only records review. Legacy worker terminated. CLI --pause-pending converted 1161 failed records to paused; 5939 ready retained. Pre-pause hashes in test_reports/automatic_ai_pause_baseline.json."
frontend:
  - task: "Honest paused AI status copy"
    implemented: true
    working: true
    file: "frontend/src/components/studio/AiReviewPanel.js, MockBookPanel.js; components/results/AiSolution.js"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: NA
        agent: main
        comment: "Existing panels show paused not retrying/auto-solving; review help no longer promises re-solve; missing solution does not promise forthcoming generation. No new controls/layout."
metadata:
  created_by: main_agent
  version: "1.0"
  test_sequence: 1
  run_ui: true
test_plan:
  current_focus:
    - "Zero automatic solving on legacy discovery, startup/restart, idle, import reconcile, review-confirm, student and cron/retry paths"
    - "Pause is idempotent; jobs and payloads preserved; compare source/test and ready solution hashes to baseline"
    - "Existing 50 mocks and 94 chapters; saved solution read path and auth boundaries"
    - "Paused state copy in Studio/results at desktop and mobile"
  stuck_tasks: []
  test_all: false
  test_priority: high_first
agent_communication:
  - agent: main
    message: "Testing must make ZERO live LLM calls and no paid integrations. Use isolated fixture docs and mocked model boundary for trigger tests. Do not change real question keys/reviews or attempts. Keep baseline content hashes unchanged. Credentials exist in memory/test_credentials.md; never hardcode/print them. Do not run stale iteration95 test that expects automatic solving. Current baseline has no student attempts. Test startup with isolated client/index/seed mocks, not by launching an extra uvicorn. No scheduler edits."

  - agent: main
    message: "Iteration 96: 16/16 tests pass, hashes preserved, no worker after 75s, desktop/mobile Studio passes. Follow-up fixed progress label to 'Full mocks' and inline-flex icon alignment. Narrow retest needed for this label/layout only; source extraction is outside solving-pause scope and unchanged. Final report/PRD must keep this limitation."


# Current feature implementation (supersedes the pause-only test focus above)
user_problem_statement: "Owner selected one-click per-test Solve for missing explanations with owner/saved AI preservation. Also add small one-line Report as wrong on every question while attempting, after result and in solutions; simplify/focus tests/results/solutions navigation."
current_features:
  - "Owner POST /api/studio/sets/{id}/solve with request_id only; GET /solve progress and /studio/solve-tests selector. Separate tejas_manual_solves + tejas_solution_requests. Durable exact consent, content identity and request idempotency; worker --manual lock drains only owner-click jobs. Existing automatic pipeline remains paused. Maintenance recovers only existing manual consent. Daily quota, owner revocation, in-flight content/solution CAS and no score/key changes."
  - "POST attempt question /report-wrong, GET attempt /question-reports; unique receipt per attempt/question; foreign ownership404, locked bonus404, active key/solution reporting403. Staff /studio/question-reports paginated list/review, no changes to keys/score."
  - "Manual Solve selector in Studio and test editor/chapter inspection; Report as wrong provider/strip in Player + result question list + explanation; Analysis/Solutions tabs, direct question picker/prevnext, retained filters/selected query, preserved catalogue/history back state, explicit leave-test warning."
current_testing_instructions:
  - "Use current credentials memory/test_credentials.md, do not print/hardcode. Preview external URL from frontend/.env."
  - "MAX ONE real model call, on a disposable tiny typed one-question test via explicit owner POST. Do NOT click Solve on an existing mock/chapter or generate bulk work. All concurrency/error/cancel/owner edit tests must MOCK model boundary in-process, no lasting mock API."
  - "Full API auth matrix, repeated clicks/report dedupe, protected existing AI/text/image solutions, worker source-change race, no automatic enqueue, normal start/save/submit/result navigation/report flows. Use synthetic QA fixtures, clean only those fixtures. Existing144 sets11800Q/5939 ready AI and1161 paused automatic docs must be preserved."
  - "Desktop1920x800/mobile390x844 screenshots of new meaningful states, no horizontal overflow. Feature reports /app/test_reports/iteration_98.json onward."


final_verification:
  iteration_100: "19/19 manual/report +16/16 automatic-pause tests pass. Desktop1920x800/mobile390x844 all requested checks pass; zero overflow. Livegpt-6-astra success independently verified in99, no model calls in100/101."
  iteration_101: "Two final copy improvements (manualbuttonlabel and bonus singular/plural/minus) passed source-logic checks/compilation; no additional browser run. Iteration100 remains visual evidence."
  preservation: "All temporary fixtures/jobs/requests/reports/attemptpacks cleaned. Baseline hashes identical:144sets,11800questions,53files,5939savedAI,1161legacy paused. No user credentials changed; currentowner remains the previously explicitconfiguredaccount, not aplaceholder."
  remaining: "No current feature blocker. Source-gap baseline/fullMyTests/other roadmap checkpoints still require approval; do not proceed automatically or deploy. Initial providerfailurecause notconfirmed; laterexplicitretry succeeded unchangedmodel/keyconfiguration."


# Latest feature batch (supersedes prior manual-solve testing scope)
latest_user_choices:
  - "5-colour beautiful segmented Results + direct Solutions navigation"
  - "Verified historical rank range only; missing usable dataset => explicit unavailable, no fictional AIR/cutoff conversions"
  - "Comparable full mocks journey; last5 mocks weighted accuracy as confidence"
  - "Complete Profile MyTests with ongoing/saved/completed, private filters/history/reports, same-paper comparison"
  - "Repeated question reports grouped/prioritised; colourful large direct examhome boxes"
latest_test_instructions:
  - "ZERO live LLM/provider calls. No credentialchanges or deployment. Audit findings remainunresolved; do not expose secrets in reports/tests."
  - "Backend new modules learning_progress.py,my_tests.py,historical_rank.py; packs insertsprogress_family; reports grouping APIs; strict contracts registered."
  - "Synthetic completed fullmock fixtures MUST have real count/shape (JEE75, BITS130+12, COMEDK180), compatible rules and original summary; toy5Q papers intentionally excluded. Use varied attempts to verify weighted last5, notmean percentages, as-of cutoff, otheruser exclusion, mixedformats rejected, missingdata/zeroanswers honest."
  - "Saved paper add/repeat/remove causesnoattempt and requires currentallowedpublication; unavailablebookmarks retained; active originaltimer/answers preserved; expirednoresume; embargo hidesmarks; compareforeign404/mismatch409."
  - "Groupingpriority distinctprofiles beforetotalreports; retakesoneprofilecountonce; version/sourcehashsplit; staff403boundaries; reviewaudit no keychange."
  - "Browser views desktop1920x800/mobile390x844 with populated progress/profile/compare/reportgroups. Inspecthorizontaloverflow and fix anyregressions. Preserve144sets,5939savedAI,1161pausedauto. All testfixtures cleaned."


iteration102_followup:
  status: "12/12 new +19/19 regression passed; populated desktop/mobile functional flows pass; content preserved; zeroLLM calls."
  reproduced_typography: "Roboto Mono alreadyinstalled/imported. Browser: fonts.checktrue; gauge strong40px but nestedspan12px; confidence strong26px but nestedspan12px. Rootcause broadspan CSS on previewwrappers, notmissingfonts. Fixed captionclasses/inheritance; added700weight only."
  fixes: "Numericinheritance, brightcardeyebrows, freepillalignment, chooseexamlabel, namedchartaxes, rankbodyfont, cohortthreshold, comparisonheadings/dates, Calendar datefilters, singularcopy, clearcompare ontab/exam change, missingreceiptget, indexedgroupdetails, batchedsavedflags."
  fixtures: "ExistingQAseed /tmp/jr_ui_state.json prefixTEST_JR_f8d69ed0; realattempts72290088-a1b0-4c04-8e62-96c370647516,298ee986-0da3-4260-ac6d-2b9ea5e90b68,0dd5c054-8b7a-4f1c-93aa-5d6fbe05f2fd. Cleanup required via backend/tests/seed_ui_journey.py cleanup after retest."

iteration103_followup:
  verification: "37/38backendtests: journey12/12,manual19/19,regressions6/7. Allnewvisual/highpriority fixespassed desktop1920x800/mobile390x844 incl typographyrootcause, charts, genuinepopovers, savedbatch0N+1, indexedgroupdetails."
  final_fixes: "Explicitnullsource_hash normalized toempty byfieldvalidator (previously500); numeric_ruleemptybulletguard; shorter examcorner; legendpadding;44pxcalendarday/navtargets+8pxcollisionpadding;Cleardateserroraction; legacyaccuracyderived fromsamecorrect/attemptedformula; nicer cohort copy/en-INreportdates; uniquegroupdetailtestids; QAcohortjobcleanup. Allpendingverification, nofinishuntiltestingagentpasses."


# Streak delivery — 2026-10-23 (approved, pending QA)
streak_delivery:
  request_verbatim: "Daily Streaks: Incorporate a 62-day completion streak to help students maintain consistency throughout the test series. proper animation ke sath banana beautifulcup running etc"
  scope: "Read-only private /series/all-india-jee/streak, current/best/completed counts, actual62dayrecord, runningSVGtrack, earned7/15/30/45/62consecutive-daycups, once-per-user/browsermilestonecelebration, pause/reducedmotion, compacthomecardandfullhub. No extrasocial/AI/auth/cron integration."
  rules: "Finalized series_live attempts only; same scheduledISTday00:01–23:59 and <=servernow. Auto-timeout finalizedsubmission counts; active-expiredneedsconfirmresult first. Archivedpractice/retries/preview/others excluded. Deduplicate byday. Todayunfinishedretainsyesterdaystreakuntilmidnight. Best/earnedcupsdurablefromattemptrecords; afterseriesendingstreakpreserved."
  tests_needed: "Use existing isolated ASGI harness; no customerDB writes. Dateboundaries/prelaunch/zero/7day/grace/missed/reset/archive/dedup/foreign/same-dayvalidation/pending/62complete, GETauth/privacy/no mutation, no answer/score leakage duringembargo. Frontendactualsavedattempts,test-onlyclock/auth fixtures; desktop1920x800/mobile390x844, runner/trophyanimations,pause/reducedmotion, lockedandearnedcups,once-onlycelebrationperuser,error/retry,daylinksandpersonalcompactcard."
  files: "backend/tejas/series_streak.py;frontend/src/components/SeriesStreak.js;series-streak.css;LiveSeries.js;LiveSeriesBanner.js;registeredserver/contracts. Reuses indexed attempts; no scheduledbackendwork is required."

# Current delivery — 2026-10-23 (approved; pending QA)
current_delivery:
  requirements: "Hide result PDF buttons; solutions before feedback; light-only exams/results; sky-blue secondary accent; historical approximate rank ranges; All India JEE Mains flagship, 62 daily slots Dec1-Jan31 IST, cutoff20:59:00, archive and dedicated private results/analytics/solutions. Owner uploads using existing importer. No auto AI."
  backend: "live_series.py schedule/owner assignment/history; attempts.py derives live/archive modes server-side, deterministic live id, cutoff, embargo and deadline; content/catalog schedule guards; learning_progress segregated series families; historical_rank exact cited secondary-table ranges, no formulas/scaling."
  frontend: "LiveSeriesBanner, LiveSeries hub and owner SeriesSchedulePanel; Results reorder; ReportButton temporarily null for all callers; root exam-light tokens include portal controls and preserve user dark preference; blue theme."
  mandatory_tests:
    - "DO NOT write to the configured customer database. Use isolated in-memory/ASGI or dedicated test database via monkeypatched module handles, never change MONGO_URL/DB_NAME. Do not run old seed scripts on real data. Browser fixtures may bridge to isolated ASGI transport; clearly distinguish fixture testing from real API."
    - "Date boundaries beforeDec1,00:00,00:01,20:59:00 accepted,20:59:01 denied new start,resume after cutoff,23:59 release,00:00 nextday archive,Jan31/Feb1,62 slots. Concurrent duplicate live start. Direct /sets/id/start cannot bypass. Future content hidden; withdrawn/unavailable fail closed."
    - "Owner/reviewer/student/anonymous assignment matrix; duplicate date rejection, revision CAS, invalid paper/date/reassign after opening rejection; archive separated from live; private history pagination; no answers/keys in schedule."
    - "Ranks exact source rows for JEE2026 and COMEDK2025; BITSAT unavailable; JEE source gaps269/270 and malformed20-29 unavailable, overlap291/292 enclosing range; incompatible duration/rules/subjects/type/max and retry/correction rejected; embargo/private ownership."
    - "Desktop1920x800 and mobile390x844: banner/modal/hub all tabs/studio schedule; real populated Results with source crops and AI math under stored+OS dark; solutions above reflection; no PDF controls; theme preference restored after leaving; no overflow."
    - "No model calls, no credentials changed, no production calls. Preserve 144 existing sets, source content and real learner attempts. Test existing mocks rules/navigation/bonus regression with isolated fixtures."
  known_limits: "Owner must supply/publish/assign the62 papers; no invented JEE papers. 80-factor/60+ wording is explicitly a proposed approach/target, not verified prediction. Audit remediation and capacity testing remain separate. Source ranges are secondary estimates, not official observed ranks."
  qa_status_2026_10_23: "Verified:iteration10771/71backend,iteration10810/10finalfrontendchecks. Privateimport/live/archive/sourceimages+savedAI/mobileflowsverified in isolatedDB with TESTONLYPNG/auth/clockbridge. Customerdataunchanged,bridgesstopped,exacttestDBremoved. Correcthome32pxselector andlegacyAIcardmissingfields verified;nomodelclaiminUI. Remaining:APIdefaultmodelmetadata notret tested/normalized;optionalSourcezoomUX unchanged;security/capacitybacklogseparate.62actualJEEpapersawaitowneruploadandassignment."

final_iteration104:
  passed: "39/39 backend (12journey,19manual/report,8targeted), allrequesteddesktop/mobile/touch/keyboard flows. Sourcehashnull list/group/priorities/review bugverifiedfixed. No frontendissues, action_items empty."
  preservation: "144sets11800Q5939ready1161paused unchanged; QAfixtures/jobs/cohorts cleaned. Genuine non-QA learner attempt was preserved. Do NOT reset or delete realactivity to match oldzero-attemptbaseline."
  known_limits: "No verified marks-rank dataset: numeric real-exam rank UNAVAILABLE, no mocked estimates. Audit remediation pending. No production deployment. No providercalls during latestfeaturebatch."
  handoff: "Feature requestcomplete. No furtherselftests/screenshotsneeded pertestingagent. Reviewednewtargetedtestandcleanupdiff; nextworkrequiresuserapproval."

