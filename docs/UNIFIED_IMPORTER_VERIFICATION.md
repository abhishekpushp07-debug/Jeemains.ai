# Unified PDF / Excel importer — verified pilot

## User flow

Content Studio → PDF files or Excel · direct text → upload → organisation/paired preview → start date/time (IST) → scheduled availability and Live/Unlive.

Excel supports `.xlsx`, not legacy `.xls`. Download templates in Studio:
- Combined Questions sheet with `solution_text`.
- Questions and Solutions sheets in one workbook.
- Questions workbook plus Solutions workbook.

Core columns: `question_no`, `question_text`, `option_a` to `option_d`, `correct_option`, `solution_text`. Optional `question_id` must be unique and agree with question numbers across sources. Optional `subject`, `topic`, `difficulty`, `type`, `exam`, `duration_minutes`. Use the downloadable template's complete column list. Integer questions use `type=integer` and an exact integer in `correct_option`. Formula cells must be pasted as values. No generated answers or invented matches.

Bounds: 5 MB/XLSX, 300 questions, 32 MB uncompressed workbook; 50 MB/PDF. Searchable numbered PDFs with explicit answer keys are supported; ambiguous, multi-column or scanned sources may be blocked. PDF regions preserve notation/diagrams; Excel is direct typed text. Source validation is not independent academic approval.

Default custom practice: JEE Main +4/-1, BITSAT +3/-1; duration 180 minutes unless supplied in source. These are not official-year simulations. After organisation no additional metadata form is required. Start time uses Asia/Kolkata; server gates admission. All participants share the same end time. Unlive blocks new attempts but preserves active attempts. Published import content is immutable; corrections require a new upload.

## Competition and analysis

- Real, original scored attempts only; first competition attempt per phone profile.
- Equal scores share competition ranks (1, 1, 3). No elapsed-time tiebreaker or official percentile.
- Phone-only login is intentionally unverified convenience access, not competition-grade identity proof.
- Scores, solution assets, revision attempts and reports stay locked until the window closes, including early submitters.
- Existing subject/topic summaries plus evidence-based missed-topic priorities and explicit small-sample caveats.
- Full 60-analysis specification is NOT completed by this slice.

## Verification and corrections to agent reports

- Final isolated suite: `185 passed, 6 xfailed`; log `/app/test_reports/product_final_regression.log`. Six xfails are pre-existing deferred architecture defects, NOT fixed by this feature.
- Frontend production build passes: `/app/test_reports/final_excel_competition_build.log`.
- Real storage PDF import → attempt → grading → 132,073-byte report, 6 pages / 6 source images: iteration49.
- Real storage XLSX → direct text → attempt → grading → 63,206-byte PDF, 3 pages: `/app/test_reports/excel_real_report_final.log`. This completes the incomplete iteration50 report.
- Actual browser Excel upload → READY → schedule using UI date/time → Unlive confirmation verified at 390px; also checked 1920px and dark mode. No horizontal overflow in final hub, organiser, leaderboard, or results-insight screens. Mobile toast sits below navigation.
- Iteration49's purported missing-source and missing-Unlive issues used incorrect URLs. Correct source route `/api/studio/imports/{id}/questions/{qid}/asset/question/0` and toggle `/api/studio/imports/{id}/live` both directly verified 200. Legacy unsafe-source routes remain deliberately held.
- App integrations are real. Isolated tests MOCK object storage, explicitly; separate real-storage smoke runs establish integration evidence.
- Eleven explicitly identified QA imports from this session archived from normal lists; six scheduled QA tests withdrawn. Source artifacts and test attempts retained privately for evidence. No existing owner content edited.

## Security and capacity limits (still release blockers)

Patched aiohttp3.14.5, urllib32.8.0, FastAPI0.143.0, Starlette1.8.0 and python-multipart0.0.32; scanner finds zero listed advisories for these versions. `pip check` passes. Fresh pip-audit still reports 144 advisory records across 20 other packages and skips the private emergentintegrations package. Frontend audit remains open. `/app/docs/packet1/dependency_triage.v1.json` now consumes current evidence; release remains disallowed. No blanket clean-security claim.

Sandbox retains chroot, low UID, seccomp and CPU/memory/time/output budgets. Required text codecs are preloaded before sealing. No weakened isolation fallback.

Importer dispatch is a bounded pilot using request-triggered processing and explicit interrupted-job retry, not a distributed worker fleet. Legacy queue/publication/retry defects remain deferred under safety holds. 500,000-concurrent capacity has NOT been load-tested/provisioned. No infrastructure or production deployment changes.

Credential literals created by testing subagents were removed/redacted from local scripts/artifacts; actual account rotation and session revocation remain an operator action and were not performed. Treat the prior credential exposure as unresolved; do not publish credentials or testing storage states.
