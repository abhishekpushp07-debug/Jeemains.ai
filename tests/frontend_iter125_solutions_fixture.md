# Iteration 125 – Solutions navigator fixture recipe (TEST-ONLY, not shipped)

Used via browser_automation (Playwright `page.route("**/api/**")`), no real backend writes.

- `/api/auth/session` GET -> `{"user":{"id":"u_fixture","role":"student"}}` (fake session, script-only)
- `/api/attempts/att1/results` GET -> fixture result:
  - questions: `{id:"q{n}", number:n, subject, outcome(correct|incorrect|skipped|dropped|bonus), marked, bonus,
    type:"mcq", options, response, answer, accepted_answers, marks, marks_exact, reason_code, key_version,
    solution_kind:"supplied_worked", render_mode:"text", text:"FIXTURE stem n", solution:"FIXTURE worked solution n", solution_number:n}`
  - JEE: 75 Q (Physics 1-25, Chemistry 26-50, Mathematics 51-75; Q74 dropped, Q75 bonus, n%7 marked)
  - BITSAT: 130 Q (Physics 1-40, Chemistry 41-80, English Proficiency 81-95, Logical Reasoning 96-115, Mathematics 116-130) + 12 bonus (131-142, bonus:true), summary.sections + main_block + bonus_block
  - Chapter: 50 Q Mathematics
  - summary needs: score, maximum, percentage, correct, incorrect, skipped, attempt_rate, attempted, eligible_count, accuracy, penalties, total_seconds, subjects{name:{score,correct,attempted,count}}, topics{}
  - review: `{states:{}, categories:["Concept","Calculation"] (STRINGS, objects crash), assigned:["q1"]}`
  - analytics: null, or `{metrics:[{metric_id:A04|A05|A41|A42|A43|A45,name,state,reason,unit,sample_size,question_ids:[],value}], available_count, note}`
- `/api/attempts/att1/question-reports` GET -> `[]` (MUST be an array, object crashes QuestionReportsProvider)
- Everything else GET -> 404; every non-GET fulfilled locally (solution-open can be forced 500/503 to test retry button).
