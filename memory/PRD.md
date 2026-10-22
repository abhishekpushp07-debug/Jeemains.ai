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
- 2026-10-18: Worker speed fix. Root cause: after a pod restart the worker process died and nothing respawned it (about 5 h with no progress), and every call leaked an HTTP session (asyncio.run per call). Fixes: the backend keeper respawns the worker every 60 s (file lock keeps one copy); the worker watchdog exits if stalled for 15 min or RSS > 1.5 GB; one persistent event loop per thread (no leaks); a 240 s hard timeout per call; 16 lanes. Scope is now full mocks only (owner request); the 4,700 chapter queue entries were removed. Rate is about 55 per minute.
- 2026-10-17 (iteration 2): Owner password set to the user's choice (tools/set_owner_password.py; sessions ended). Result analysis: live rank/percentile/average/median/top among all students (cohorts.py MIN_SAMPLE=1, early-sample label under 100), score-distribution, section you-vs-avg-vs-top, outcome donut, 142-question heat map, per-question "X of Y who attempted solved it", 25-point deep insights (frontend lib/deepInsights.js, data-driven). AI ten-mark solutions: gpt-6-astra (Emergent key) pre-generates for every live full-mock question in a separate worker process (tools/solution_worker.py, spawned at backend start, file lock, 8 lanes, lease/retry, auto-queues any newly live full mock every 2 min); shown as "AI generated" on results + in the PDF (plain-text math). Testing agent iteration_94 found a PDF failure on AI LaTeX, which is now fixed (PDF tested: 289 pages).

## Latest approved roadmap and delivery boundary
The owner approved “Familiar Exams, Clear Results aur 5-Lakh Capacity Roadmap”: original-PDF display, canonical source/version provenance, light-only exam-specific screens, navigation, segmented Analysis/Solutions/Real-exam Comparison, optional feedback below analysis, complete My Tests, evidence-backed historical rank context, and future measured capacity. Maroon #5C0025, Figtree/Roboto Mono, current authentication, all content/rules and separate retakes are preserved. 2027 official interfaces only after verified release; otherwise identify actual verified reference year and adaptations. No invented rank datasets, scale claims or official affiliations.

There are exactly 25 owner-approved checkpoints in three major phases; one checkpoint at a time, stop for approval. MVP is 01–09; 10–25 are roadmap only. Private S3 + CloudFront is proposed, not provisioned. Paid infrastructure, load/capacity spend and production release require separate approval. Android-compatible APIs are roadmap scope, not an Android app. Full-mock window through 17 October 2027 and 94 chapter/50 mock contents/rules remain protected.

**Latest authorised scope:** The owner now requested the remaining per-test Manual Solve feature and selected **“Ek click mein shuru karein”** (no confirmation modal). Additional explicit request: **“Every question in test while attempting , after result , and in solutions should have a small one line section of report as wrong. Also navigation of trsts , results, solutions should be simplified and focussed.”** Implement one-click owner-only missing-solution generation, question issue reporting with Studio triage, and focused existing Tests/Results/Analysis/Solutions navigation. Do not execute unrelated source-reconciliation, full My Tests/rank or capacity checkpoints, paid infrastructure or deployment.

### Current work in progress — manual Solve, question reports, focused navigation
- New `tejas/manual_solutions.py`: separate durable explicit request/queue; existing auto pause remains True. Only owner POST materialises selected-test eligible jobs; GET/student/upload/publish paths never enqueue. Explicit request receipts, deterministic per-question content IDs, bounded single-process manual drain, owner/consent rechecks, CAS owner/source protection, quota enforcement and saved labelled tags. Existing maintenance only recovers previously owner-consented jobs, no library discovery.
- New `tejas/question_reports.py`: private per-attempt/question idempotent receipts, no key/solution data returned, locked bonus/release checks; staff-only paginated triage, audited status changes, no regrade.
- Frontend one-click Solve selector/panels; compact Report as wrong across attempt/results/solutions; Analysis/Solutions navigation with report download, filter/selected question query state, exam destination links, context-preserving return and explicit leave confirmation.
- Verification in progress: iteration98 identified None guards/mobile styling; iteration99 confirmed live gpt-6-astra generation on one explicitly requested isolated question (1,249 tokens), saved tag and student AI-generated display. Initial live call had a generic provider failure; non-generative model catalogue returned200 and exact model present; retry succeeded with unchanged provider/model/key configuration. Cause of initial failure remains unconfirmed; no IP-allowlist claim. Safe error classification logs enums/status/parameter names only, never provider bodies or secrets.
- Iteration100: **19/19 manual/report +16/16 automatic-pause regression tests passed** in separate serial pytest processes. Final UI verified at1920x800 and390x844, 0 horizontal overflow: working filter active pills, all144 long dropdown options fit, inline reporting acknowledgement, number-labelled supplied explanations and no empty card on AI-only questions, genuine disabled Nothing to solve button, and dynamic bonus rules. Report/AI/student access, idempotency, owner-source edit races, secure error redaction and unchanged source keys tested.
- Existing144 tests/11,800 questions/53 source records/5,939 savedAI/1,161 pausedautomatic records unchanged by preservation hashes. Temporary test sets/attempts/reports/manual requests/jobs/cohorts/packs/ledgers cleaned, 0 manual pending jobs left. Tests use MOCKED model calls for race/error cases; application APIs are real and live gpt-6-astra success was separately verified in iteration99. No production release or paid infrastructure setup. Final optional label/plural copy polish awaits narrow verification.


## Current implementation — automatic AI pause (2026-10-22 preview run)
- Supersedes all historical automatic-generation requirements above. The automatic worker was suspended and terminated. Backend lifespan no longer starts a worker or keeper. Code-enforced `AI_SOLVING_PAUSED=True` gates legacy discovery, claim, solve, worker/keeper/spawn, legacy ensure/process, generic enqueue/retry/run/drain. Scheduled maintenance ignores AI jobs, retains grading/report work; cron schedule/auth unchanged.
- `tools/solution_worker.py` now exits with a pause notice. Explicit administrative `--pause-pending` idempotently retains unfinished jobs as paused with previous state/time/reason, removing only lease/retry metadata. 1,161 failed automatic full-mock jobs paused; 5,939 ready solution documents/tags preserved; 7,100 total full-mock questions. No chapter solution jobs existed at pause. No deletion of jobs, solutions, source files, tests or student work.
- AI Answer Review confirmation records review only; no automatic re-solve. Smart-import reconciliation stops at `solving_paused`; retries no longer requeue solution jobs. Existing smart source extraction is NOT globally disabled: it is a separate import operation, may use AI, and remains subject to existing safety holds. This is a solving pause, not a blanket ban on every AI-assisted import feature.
- Existing Studio panels state that automatic generation is paused and show retained job counts; progress is explicitly labelled full mocks. Missing student explanations no longer promise automatic preparation. Saved explanations remain readable; disagreeing explanations still follow review gating. No new Solve button or resume-generation control added.
- Preservation baseline: `test_reports/automatic_ai_pause_baseline.json` stores only hashes/counts, not contents/credentials. 144 test sets (50 mocks + 94 chapters), 11,800 questions, 53 source file records and 5,939 ready solution payloads unchanged by hash. Current preview had **zero attempts before this work**; this is not independent evidence about production attempt history or remote source-byte integrity.
- Verification: `test_reports/iteration_96.json`; 16/16 regression checks (12 synthetic/in-process + 4 external-URL API tests), 75-second idle observation, hot-reload/no-spawn plus isolated lifespan check. No new AI queue work; pause is idempotent; review/read auth boundaries intact. Studio verified at 1920x800 and 390x844, no horizontal overflow. ZERO live model calls; model boundaries MOCKED in tests only. Student solution states checked via API, not full results-page UI. Final progress-label/alignment follow-up passed in `test_reports/iteration_97.json`: explicitly labelled full-mock count, aligned icon, desktop/mobile without visible horizontal overflow; no additional model calls or content changes.
- Regression files: `backend/tests/test_ai_pause.py` and `backend/tests/pause_baseline_check.py`; run pause suite serially with `-n0 -p no:asyncio`. Historical `test_ai_tags_review.py` has stale auto-solve/full-library assumptions and embedded credentials; do not run it as current acceptance evidence. No auth credential changed; test phone 9900000196 documented.
- No production deployment, CDN/storage setup, capacity exercise or automatic next-checkpoint execution performed. Full checkpoint 01 is **not complete**.

## Prioritized roadmap — approval required
### P0 / Major Phase 1 — MVP, checkpoints 01–09
01. Preservation, source baseline and owner AI control — pause slice delivered; source-traceability gaps/status summary and per-test explicit Solve (eligible missing solutions only, idempotent, owner-solution protection) remain pending approval
02. Navigation foundation — discovery, My Tests/Profile entry points, context-preserving back and deliberate active-exam exit
03. Light-only exam workspace — entire workspace independent of account/device theme, readable original images, accessible mobile controls and save states
04. JEE Main familiarity mode — verified NTA actions/legend/reference year; no invented 2027 parity
05. BITSAT familiarity mode — verified guidance/adaptation, preserve 130+12 eligibility, warning/lock, shared 180 minutes and +3/−1/0
06. COMEDK familiarity mode — verified familiarity reference distinguished from actual paper rules
07. Results redesign — Analysis/Solutions/Real-exam Comparison, grouped 25 insights/charts, retained question/filter context, optional feedback immediately below analysis, full-attempt PDF unaffected
08. Complete My Tests — In progress/Saved/Completed; original-deadline resume, searchable history/reports, save without attempt, comparable-version attempt comparison
09. Historical same-score comparison — usable approved sources and compatible scoring only; separate cohort rank; honest unavailable states until datasets verified

### P1 / Major Phase 2 — roadmap only, checkpoints 10–17
10. Complete canonical source/version records, reconciled gaps and original attempt scoring basis
11. Crop/readability validation and reading/zoom image variants; ordinary complete-view 25–60 KB target subordinate to mathematical clarity
12. Durable private storage and protected direct CDN delivery; short-lived links, immutable shared caches, separate paid approval
13. Shared documented/versioned web and future Android API contracts
14. Durable saving and weak-network recovery; acknowledged vs pending state, monotonic/conflict-safe saves
15. Authoritative deadlines, bonus and repeat-safe final submission
16. Complete publication and auditable corrections/regrades without silently changing ongoing papers
17. Results integrity and heavy-work isolation (reports, analytics, imports, manual AI)

### P2 / Major Phase 3 — roadmap only, checkpoints 18–25
18. Database, memory and connection capacity evidence and bounded caches
19. Independent scaling and start/finish/reconnect burst planning
20. Privacy and abuse protection qualification; existing access protection applies from MVP
21. Owner live-exam health/incident visibility
22. Evidence-backed recovery/preservation commitments, limitations stated
23. Cost/quota guardrails and approved event capacity envelope
24. Measured 500,000 simultaneously active examinations including saves/reconnect/finish; CDN alone cannot pass
25. Controlled owner-approved production release and operational handover within proven capacity

## Deferred earlier backlog and limitations
- Upload-to-live/source issue workflow, worker controls, JEE/COMEDK content, mistake-practice/bookmarks and verified historical rank evidence remain subject to separately approved checkpoints. Existing cohort insights and AI Answer Review are already present; do not describe them as entirely missing.
- No blanket file restructuring/refactoring authorised. Legacy generator cleanup and stale regression-test replacement belong with a separately approved manual-solve implementation, not this pause-only slice.
- No assertion that existing canonical mappings, source bytes, 25 insight quality, whole product regressions or 500,000-user capacity were independently reverified by the pause tests.

## Next action
Pause verification is complete (iterations 96–97). Await explicit owner approval for the remaining checkpoint 01 work; do not start it automatically.
