# jeemains.ai — simple navigation, Fit default and free landing

## Delivered scope (17 October 2026)
This is a completed navigation/branding phase, not completion of the AI publishing/analytics roadmap or a production/500k certification.

- Public app name and newly requested report/download branding: **jeemains.ai**. Original source-book attribution and internal database/storage namespaces remain unchanged. No custom-domain configuration or deployment was performed.
- Before signup: bold **100% free for all students** campaign, typographic student pass, separate JEE Main/BITSAT/COMEDK posters, clear free CTA, light/dark layouts and FAQ.
- The requested60/75 JEE Main2027 and120+ BITSAT2027 counts are explicitly **aspirational concept-coverage targets**, NOT measured outcomes or guaranteed predictions for any session. AI/PYQ-generated papers are disclosed as in development; no analysis evidence or future exam overlap was fabricated.
- Student phone login -> `/home` with exactly3 exam cards: JEE Main, BITSAT, COMEDK. Each exam -> exactly3 choices: Mock Tests, Chapter-wise Tests, Results. Header no longer says My Practice. Draft recovery and staff tools remain accessible in the account menu; staff login retains its Studio destination.
- Subject selection -> real chapter lists. Full mock catalogue uses explicit classification and excludes chapter/practice/sample papers. Unpublished, expired, scheduled, disabled, QA-only and unauthorized audience content is excluded server-side before pagination.
- Exam Results history is scoped to the authenticated profile and selected exam before pagination, with actual All/Mock/Chapter filters, date range, resume, result detail and historical review access. Ambiguous legacy practice is labelled Other practice, not invented as a full mock.
- Player originals default **Fit**. Readable/zoom/pan remain optional. Initial, Next, Previous, question jump and refresh all reset to Fit. Fit frame height follows the actual original-image aspect ratio to reduce blank space and keep mobile answer controls reachable.
- Submission and expiry still lead to real results. Existing supplied keys remain honestly key-only; no generated solutions were fabricated.
- Two protected metadata routes: `GET /api/exam-navigation/{slug}/catalogue` and `/history`. Response models, explicit ingress contracts, route evidence catalogue and supporting history index added. New attempts snapshot their test classification.
- Report cache keys include a branding-template version so a newly requested report does not silently reuse a pre-rebrand render. Previously downloaded documents are not rewritten.

## Verified evidence
### Backend
`test_reports/navigation-final-regression.log`: **368 passed,0 failed**,232 dependency deprecation warnings,95.94seconds. Includes26 new isolated cases for exam/type/audience/expiry/QA filtering, pre-pagination behavior, user isolation, legacy history classification, competition embargo, invalid queries, model schema and branded PDF rendering.

The first full run caught two evidence-maintenance failures: the operation catalogue omitted the two new routes, and an exact contract-count assertion still expected73. Both were updated to actual75 routes, preserving exact runtime/catalogue/schema equality, then the full suite was rerun. The audience negative assertion and PDF brand assertion were strengthened rather than weakened.

### Frontend
`test_reports/navigation-ui-verified/final_test_output.log` and `test_results.json`: **10/10 actual browser suites**,0 failed,22 screenshots,0 recorded horizontal-overflow issues, one real PDF. Latest run uses QA phone ending0347; all mutations are normal QA login/attempt activity, never source/publication edits.

Verified:
- Student login, Home3cards, BITSAT hub3cards, no My Practice header.
- **32 Chemistry tests**, actual pagination **12+12+8**.
- Correct source Fit/Readable selectors and aria-pressed state after initial/Next/Previous/Q10/reload. Mobile navigator also checked.
- Answer save, submission, actual score, review and download.
- PDF parsed with PyMuPDF: **51 pages**, **JEEMAINS.AI** brand and **RESULTS & ANSWER KEYS** disclosure. It is not mislabeled as AI worked solutions.
- Actual Chapter and Mock history-tab clicks; completed chapter attempt appears only in the appropriate filter.
- JEE Main/COMEDK empty catalogues contain no BITSAT content.
- Landing light/dark; desktop1920x800 and mobile390x844.

Main additional mobile checks and screenshots:
- `navigation-history-mobile-final.jpg`
- `navigation-chapters-mobile-final.jpg`
- `navigation-fit-mobile-final.jpg`
- `navigation-fit-desktop-final.jpg`
Fit is true at390px; no overflowing right edges. ResizeObserver/canvas reflow was allowed to settle before final captures.

`test_reports/navigation-build.log`: production frontend build succeeds.
`test_reports/navigation-owner-invariants.json`: **94 original BITSAT chapters /4,700 questions**, all published/live,50questions each,+3/-1,60minutes,original365-day windows and independent-check evidence preserved.

## Evidence corrections
- Iteration87 ignored the requested backend scope and created an irrelevant ad-hoc owner script; it was removed. It is not backend acceptance evidence.
- Iteration89's claim that there was only one Chemistry chapter counted an instrumentation wrapper, not paginated test rows. Its claim that Mole Concept was text-only used the wrong CSS selector; the screenshot visibly contained original source Fit/Readable controls. Those claims are rejected.
- Iteration90 correctly tested the source controls and32-test pagination, but its remaining empty-state failure was an exact-text selector missing the trailing period. The UI already rendered the correct empty state. Selector corrected, and the entire browser script rerun successfully by the main agent.
- Do not repeat any subagent's broad production-ready or100%platform claim. Accept scoped execution logs only.
- Historical test tooling exposed an owner credential; offending local artifacts have been redacted and faulty scripts removed. Authorized password rotation/session revocation remains recommended; not performed as an unapproved access change.

## Current content availability
All94 published owner chapter tests belong to BITSAT. There are currently no published full mocks or JEE Main/COMEDK chapter sets in the real non-QA catalogue. Those sections intentionally show informative empty states; no fake tests, fabricated counts or cross-exam copies are shown.

## Still unfinished — do not advertise as delivered
1. General PDF/Excel/Word upload -> paper-inferred marking/duration/sections -> in-app ambiguity clarification -> independently checked auto-publication.
2. OpenAI Astra missing-answer solving and detailed, versioned stepwise solutions, including a bounded plan for previous key-only papers. Exact managed runtime/model support still needs a real canary; no silent model substitution or bulk4700-question generation was performed.
3. Same-test/version cohort rank, percentile, per-question student correctness/option distributions and deep graphs.
4. Sourced and honestly calibrated2026 JEE Main AIR estimation; no arbitrary chapter-score-to-AIR conversion.
5. Frontend CRA-chain security remediation and dedicated500k/write-burst/failover qualification from earlier phases.

No application integration in this phase is mocked. Isolated backend fixtures are synthetic test data, not live papers.

## Reproduction
```
python -m pytest tests/packet1 -q
yarn --cwd frontend build
QA_PHONE=+12025550348 python tests/ui/comprehensive_navigation_test.py
```
Use a fresh QA-only phone for browser runs. Keep source/content fixtures in the guarded ephemeral pytest database; never insert ad-hoc test papers into the preview database.
