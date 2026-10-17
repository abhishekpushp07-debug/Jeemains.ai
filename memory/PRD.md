# jeemains.ai (Campus 2 / Witcircle) — PRD

## Original problem statement (approved plan, verbatim summary of owner's words)
jeemains.ai is a free web app where students practise for JEE Main, BITSAT and COMEDK with timed chapter-wise and full mock tests, instant results and downloadable PDF reports. Continue the existing app from GitHub (abhishekpushp07-debug/Witcircle): first fix the error that stops the app from running, then add 50 BITSAT full mock tests from the uploaded PDF "Tejas200_BITSAT_50_Full_Mocks_Combined.pdf" (1,284 pages). Each mock: 130 main + 12 bonus questions, section split/order from the PDF, +3/−1/0 for both, 180 minutes total (bonus shares timer). Bonus appears only after all 130 main are answered; clear warning that 130 answers lock; after entering bonus main answers locked. Answer keys only from the PDF. Problem mocks stay private and are listed in Studio with reasons. Results/PDF show total, section-wise, bonus, correct/wrong/unanswered and per-question student vs correct answer. Keep existing 94 BITSAT chapter tests, maroon #5C0025, Figtree/Roboto Mono. Phase 2: upload-to-live for PDF/Word/Excel, OpenAI gpt-6-astra step-by-step solutions labelled "AI generated", owner password change. Phase 3: rank/percentile (≥100 attempts), per-question stats, charts, JEE Main/COMEDK content, mistake practice, bookmarks, 2026 rank estimate only with verified table.

## Architecture
React (CRA/craco, Shadcn) + FastAPI (`backend/server.py`, modules in `backend/tejas/`) + MongoDB. Emergent object storage for private source PDFs (crops rendered server-side). Route-contract startup check (`tejas/route_contracts.py`) — every new API route must be registered there.
- Full mocks: `tejas/mock_parser.py` (PyMuPDF region parser + 2 independent key readers), `tools/import_bitsat_mocks.py` (idempotent importer; per-mock PDF in storage), `tejas/mock_books.py` (GET /api/studio/mock-books), `POST /api/attempts/{id}/bonus` (attempts.py), bonus gating in answers.py, section/bonus scoring in scoring.py, report lines in reports.py.
- Chapter tests restore: `tools/restore_chapter_books.py` (rebuilds the 94 tests with original IDs/window from `data/chapter50`).
- Frontend: Player bonus gate (`components/player/BonusGate.js`), `MockSectionScores.js`, Studio `MockBookPanel.js`, `full-mocks.css`.

## User personas
- Students (phone-only login) practising BITSAT/JEE/COMEDK on mobile/desktop.
- Owner/staff using the Content Studio (email + password).

## Core requirements (static)
Free access; phone-only student login; exam hubs (Mock Tests / Chapter-wise / Results); source-image questions with Fit/zoom/pan; offline answer recovery; server timer + auto-submit; instant results and PDF report; honest labels (no invented ranks/solutions).

## What's been implemented
- 2026-10-17: Imported repo; app starts (env configured, deps installed, poppler/LibreOffice installed). Restored the 94 live BITSAT chapter tests (30/32/32, 4,700 Q, original IDs, end 17 Oct 2027).
- 2026-10-17: 50 BITSAT full mocks imported — all 50 passed checks (130+12, sections P30/C30/E10/LR20/M40, 142/142 keys agreeing across two readings, A–D readable, no overlaps) → 50 live, 0 held, live until 17 Oct 2027. Bonus gate/lock (server-enforced), section-wise + bonus results and PDF, Studio mock status panel, results "Bonus section" filter. Testing agent iteration_93: backend 13/13, all requested UI flows pass.
- 2026-10-17 (iteration 3): AI solutions moved fully owner-side. The worker (12 lanes) scans every 30 s for every question in draft/review/published sets (new uploads first, then live mocks, then live chapter tests; 11,800 total). It saves the result as a `questions.$.ai_solution` tag (solution, key, refs hash, agrees, review). Students only read tags (GET /api/attempts/{id}/ai-solutions, about 0.1 s); the legacy student-triggered AI route now returns 410. A key or source-region edit triggers a fresh solve, and lost tags are restored from the queue. Disagreeing solutions are hidden from students until review. Studio "AI Answer Review" panel: GET /api/studio/ai-review, POST /api/studio/ai-review/{set}/{q} (key_confirmed → re-solve with the verified key, key_wrong → shown with a correction note, reopen), plus a crop image route. Testing agent iteration_95 passed; its HIGH issue (the images) is fixed.
- 2026-10-17 (iteration 2): Owner password set to the user's choice (tools/set_owner_password.py; sessions ended). Result analysis: live rank/percentile/average/median/top among all students (cohorts.py MIN_SAMPLE=1, early-sample label under 100), score-distribution, section you-vs-avg-vs-top, outcome donut, 142-question heat map, per-question "X of Y who attempted solved it", 25-point deep insights (frontend lib/deepInsights.js, data-driven). AI ten-mark solutions: gpt-6-astra (Emergent key) pre-generates for every live full-mock question in a separate worker process (tools/solution_worker.py, spawned at backend start, file lock, 8 lanes, lease/retry, auto-queues any newly live full mock every 2 min); shown as "AI generated" on results + in the PDF (plain-text math). Testing agent iteration_94 found a PDF failure on AI LaTeX, which is now fixed (PDF tested: 289 pages).

## Prioritized backlog
- P0 (Phase 2): automatic PDF/Word/Excel upload-to-live with issue list; Studio controls for the AI solution worker (pause/retry) and review of AI-vs-key disagreements.
- P1 (Phase 3): cohort rank/percentile (≥100 comparable attempts), per-question right/wrong/skip and option split, score distribution & subject charts.
- P2: JEE Main/COMEDK papers, mistake-practice mode, bookmarks, verified 2026 rank estimate.

## Next tasks
- Owner to change password; then Phase 2 upload-to-live + AI solutions.
