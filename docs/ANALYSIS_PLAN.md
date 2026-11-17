# JEELIVE.AI Analysis 2.0: plan only (nothing built yet)
Date: 2026-11-17. Website first. One server and one API for both the website and the app. No AI credits are used: every number comes from stored data.

## 0. What the code has today
- The Results page already has these tabs: Analysis, Progress, Confidence, Real-exam rank and Solutions. It also has peer %, the AIR scenario, the live-series rank card and the competition leaderboard.
- Each attempt already stores: final answers, the first answer and the server time it was saved, confidence, marked-for-review, the set of visited questions, and start/deadline/submit times.
- Not stored today: how long each question stayed on screen and the order of visits. So the Time, Attempt Quality and Question Journey sections can only start from the first mock after release. Old mocks still show every section that does not need time.
- Most questions have no difficulty tag. Some have Easy/Moderate/Hard from their solutions.

## 1. Screen map and navigation
- Top bar: Back, Download, Share, View Solutions.
- Sticky bottom bar (works on phone and desktop): a Personal / Comparative switch, then scrolling pills:
  1 Overview, 2 Performance, 3 Score Potential, 4 Attempt Quality, 5 Time, 6 Difficulty, 7 Question Journey, 8 Qs by Qs.
- Each section has its own link, for example `/results/{id}?a=time&mode=compare`. On phone you can swipe between sections, and the page remembers the last one you opened.
- Every number and every bar can be tapped. It opens the filtered list of questions, then that question's solution. Back returns to the same chart at the same scroll position.
- Progress, Confidence, Real-exam rank and Solutions stay as they are.

## 2. The rulebook (one versioned set of definitions, the same on website and app)
- **Time on a question** = total time it was on screen while the paper was running. The timer stops when the tab is hidden, the app goes to the background or the screen turns off. One stretch counts for at most 15 minutes. The label says "time on screen".
- **Par time (ideal time) for each question**
  1. If 30 or more students solved it correctly: the median time of those students, kept between 30 s and twice the paper average.
  2. Otherwise: the paper's average time per question × a type factor (MCQ 0.85, numerical 1.35), adjusted so the total is 90% of the paper's duration.
  - The screen always shows where the par time came from, for example "from 412 solvers" or "paper standard".
- **Attempt Quality**: every question gets exactly one tag, so the totals always add up to the number of questions.
  - Perfect: correct within 1.25× par
  - Slow-correct: correct but slower than 1.25× par (counted under Overtime)
  - Wasted (careless): wrong in less than 0.5× par
  - Concept gap: wrong between 0.5× and 1.5× par
  - Costly overtime: wrong after more than 1.5× par (counted under Overtime)
  - Confused: not answered, but more than 0.5× par spent on it
  - Smart skip: seen briefly and left
  - Not seen: never opened
  - The headline cards show Perfect, Wasted, Overtime, Confused and Concept gap. The rest appear in the details.
- **Difficulty**
  1. If 50 or more students attempted it on their first try: Easy when 65% or more got it right, Tough when under 35% did, otherwise Moderate.
  2. Otherwise: the paper or book tag.
  3. Otherwise: "Not rated", shown as its own row and never guessed.
  - For live papers, difficulty based on student results appears only after results are released.
- **Score Potential** (exact maths, with the questions listed behind each step)
  - a. Careless fix: each Wasted question earns the correct marks plus the negative mark back.
  - b. Negative guard: wrong answers on Tough questions that fewer than 25% of students solved. Skipping them saves the negative marks.
  - c. Time reinvest: minutes lost to Costly overtime and Confused, used instead on questions you didn't attempt (Easy first). Expected marks are worked out from your own accuracy at that difficulty.
  - Realistic target = current + a + b + half of c. Maximum = current + a + b + c. The predicted rank or percentile at that score comes from the existing cohort/AIR logic when that data exists.
- **Comparative mode**
  - Compare with the Topper, the Top 10% average, the class average, or any student picked from the leaderboard.
  - Only totals and averages of other students are shown, never their per-question answers.
  - It appears only after results are released. Class and top-10% averages need at least 10 finishers.
- **Per-question class stats**: % correct, % wrong and % skipped, average time, topper's time, and the most-chosen wrong option ("62% fell for C").

## 3. Sections
1. **Overview**: score ring, rank, percentile, attempted/correct/wrong/skipped, accuracy, time used, a card for each subject, and "3 things for your next mock" (ranked by marks at stake, worked out from your data with no AI). In Comparative mode: you vs topper vs average for each subject.
2. **Performance**: tabs for each subject. Score, accuracy, attempt rate, negative marks, MCQ vs numerical split, and a chapter table where tags exist. No strength label is shown when a chapter has fewer than 3 questions.
3. **Score Potential**: a step chart (current, +careless, +negative guard, +time reinvest, potential). Each step lists its exact questions. Also shows "At X marks, rank about Y".
4. **Attempt Quality**: definition cards, a subject × tag table and grouped bars. Tap a tag to see its questions. In Comparative mode: your Perfect % vs the topper's.
5. **Time**:
   - Time breakdown: subject, time, attempted, accuracy.
   - Subject chart with Time / Questions / Accuracy toggles.
   - Quality-of-time bar: time on correct, wrong and unanswered questions.
   - Time journey in 30-minute blocks (15-minute blocks for papers of 60 minutes or less): correct, wrong, answered.
   - Pace curve: how many questions were answered over time. This replaces Quizrr's misleading single line.
   - Slowest 5 questions.
   - In Comparative mode: your pace curve vs the topper's.
6. **Difficulty**: tabs for each subject plus All. An Easy/Moderate/Tough/Not rated × Correct/Wrong/Not attempted table showing x/N, with grouped bars. A "Leak" highlight shows Easy wrong + Easy skipped. In Comparative mode: your accuracy at each difficulty vs the average.
7. **Question Journey**: one chip per visit, grouped by time block. A badge shows which visit it was (2nd, 3rd…). An icon shows the quality tag, with a show/hide toggle. Other icons: marked for review, answer changed (B→C). Tap a chip to open the solution. A summary line reads: "Visited 47/75, went back 18 times, 6 questions seen 3+ times". There is also a note on the order you worked in (subject order and what the first 30 minutes produced).
8. **Qs by Qs**: a table on desktop and cards on phone. Columns: Q, subject, chapter, difficulty, your answer, correct answer, result, your time, par time, class % correct, tag. Filters: wrong, skipped, careless, overtime, confused, marked, changed answer. Each row opens its solution.

**Solutions header**:
- A strip of question chips coloured by status.
- Filters: All, Correct, Wrong, Skipped, Careless, Overtime, Confused, Marked.
- Subject tabs.
- One line for each question, for example: "Q17 · Physics · Moderate · You 3m40s · Par 2m10s · 41% right · Topper 1m50s · Most chose B". It also shows your journey on that question (seen 3 times, changed C→B).
- The existing navigator stays.

**Compare screen** (from the leaderboard's Compare button):
- You vs [name, rank]: score, rank and percentile.
- Marks, attempts, accuracy and time for each subject.
- Attempt Quality split and both pace curves.
- "Where the gap is biggest" by subject and by difficulty.
- Totals only. The other student's answers are never shown.

## 4. Download, share and easy access
- Download report: an A4 PDF of 6–8 pages, made on the server. It is saved for each attempt and answer-key version and opens on phones. File name: `JEELIVE_<paper>_<date>.pdf`.
- Optional Revision PDF: only wrong, skipped and careless questions, with solutions, for offline revision.
- Share: a scorecard image (score, rank, percentile, never the phone number) for WhatsApp.
- Speed: analysis is calculated once when the result is ready, so the page opens with a single request. Charts use the Recharts library that is already in the app. The last analysis you opened can still be viewed offline.
- Accessibility: right and wrong are marked with icons as well as colour, labelled numbers, large tap targets, works on 360 px screens.

## 5. Backend and data
- **A. Time capture in the Player**
  - Records each on-screen stretch {q, from, to}, answer changes {q, value, t} and marked toggles.
  - Saved in the existing offline draft store, so a refresh or crash does not lose it.
  - Sent along with the existing answer saves, so there are no extra requests during the rush. Whatever is left goes with submit. After an auto-submit, one flush is accepted for 10 minutes.
  - The server checks that times fall inside the paper window and are in order without overlaps, that question ids are known, that there are no more than 2,000 events, and that the total does not exceed elapsed time.
  - Stored in a separate `tejas_attempt_timeline` collection keyed by `attempt_id`, so attempt records stay small. Resending the same data has no effect.
- **B. Analysis engine**: one pure function `build_analysis(attempt, result, stats, rules)` that returns versioned JSON (`analysis_version: 1`). The result is saved and recalculated when the answer key or the class stats change.
- **C. Class stats job**: runs for each paper, in the background and off the request path. It works out per-question %, median times, chosen options and topper/top-10%/average totals. It refreshes after new finishes, at most every 10 minutes. For live series it runs only after results are released.
- **D. API** (website and app use the same calls; owner-only; release embargo respected; every route registered in the route/request contracts):
  - `GET /api/attempts/{id}/analysis?mode=personal|comparative&compare=topper|top10|average|user:{id}`
  - `GET /api/attempts/{id}/analysis/questions?filter=…`
  - `GET /api/attempts/{id}/analysis/report.pdf`
  - `GET /api/competitions/{id}/compare/{user}`
- **E. Old attempts**: every section works except Time, Attempt Quality and Journey. Those show "Starts from your next mock".

## 6. App packet (kept ready, handed over when asked)
`docs/app_packet/analysis/` will contain:
- an API guide with examples
- the analysis v1 JSON schema
- the rulebook
- a spec for each screen, with its states (loading, empty, locked, old attempt) and test ids
- the time-capture spec for the app player (same format)
- design tokens
- sample payloads
- a test checklist

## 7. Build order (each phase tested on its own)
1. Time capture, storage and validation, plus an isolated load test of answer saves carrying the extra time data.
2. Analysis engine, rulebook and class-stats job. Isolated database tests must cover: every tag, old attempts, dropped/bonus questions, numerical questions, ties and the live embargo.
3. Website: sticky bar and all 8 sections in Personal mode.
4. Comparative mode, the leaderboard Compare screen and the Solutions header.
5. PDF download, share image and, if approved, the Revision PDF.
6. App packet, full testing agent run and a 390 px check. Deploy only when the owner says "deploy".

## 8. Decisions for the owner
1. Par time: based on student results when enough exist (recommended), or always the paper standard.
2. Comparative: topper + top 10% + average + any leaderboard student (recommended), or averages only.
3. Revision PDF in phase 5: yes or no.
4. Section names: English as now (recommended), or Hinglish.
