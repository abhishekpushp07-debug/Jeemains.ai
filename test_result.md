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