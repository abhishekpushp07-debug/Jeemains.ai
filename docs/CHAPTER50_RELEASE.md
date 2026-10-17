# Chapter50 release — supplied books live

## User-authorized release

The owner explicitly requested the three supplied chapter books to be Live immediately for one year, each chapter containing50questions,60minutes,+3correct/−1incorrect/0unanswered. The source books contain answer keys, **not worked solutions**.

| Subject | Tests | Questions | Book ID |
|---|---:|---:|---|
| Physics |30|1,500|`f11ab410-5ff9-5fc7-8d1f-e9353701603f`|
| Chemistry |32|1,600|`75ee1d71-4bd1-58f9-a821-0ebec0e11f91`|
| Mathematics |32|1,600|`0f0fb45f-197f-5fae-9377-ce5c317f3201`|
| **Total** |**94**|**4,700**||

Published through the authenticated owner APIs on **17October2026**. Each book's exact UTC start/end is recorded in `test_reports/chapter50_publication.json`; end=start+365days, **17October2027**. Republish and duplicate upload do not extend expiry. Live/Unlive affects new admission, not an existing student's frozen timer.

## Working product flow

1. Studio defaults to **Chapter book ·1PDF**. Existing paired PDF and Excel modes remain available.
2. A searchable supported TEJAS200 subject book is stored privately and parsed in the bounded sandbox. No second solutions file is required.
3. Each chapter must have the exact sequence1–50, all four option labels, matching chapter/key titles, and50unambiguous keys. Reading-order and independent coordinate-based key extractions must agree.
4. Original source question regions are used for **all** supplied questions. No text-only approximation of mathematical notation is served. Individual source key crops are separate and inaccessible during active attempts.
5. Every supplied chapter has an independent testing-agent recheck bound to the exact source SHA256 and parsed manifest SHA256. All94passed; all4,700keys match the source. This is source fidelity, **not academic certification of the publisher's keys**.
6. Owner can inspect question1–50 with original question/key images, see per-test verification, and toggle Live without changing validity.
7. Student **Exams** catalog has subject counts, search, pagination, expiry, start/resume/results. A personal60-minute timer starts only after preflight. Submission immediately releases results and supplied keys; one-year availability is not a competition embargo.
8. Formula enlargement supports real100–500%canvas zoom, touch drag, arrow controls and keyboard panning without document overflow.
9. Results and PDF reports disclose that no worked solutions were supplied. The `solution_kind` metadata survives frozen packs and public attempt views. Legacy compatibility enrichment is derived only from immutable explicit source disclosures; no pack hash, answer, rule or score is rewritten.

## Independent and direct evidence

- `test_reports/chapter50_recheck.json`:94per-test records,50/50keys each; source/manifest hashes; no source-key pages in question regions.
- `test_reports/chapter50_validation.json`, `test_reports/formula_visual_inspection.json`: independent source/layout checks and dense-math samples.
- `test_reports/chapter_final_full_regression.log`: **396passed**, zero failed/skipped/xfail; existing importer, scoring, competitions, offline and Guide04 tests included. Earlier test-harness failures were corrected, not suppressed.
- `test_reports/chapter_frontend_final_build.log`: frontend production build passes.
- `test_reports/iteration_78.json`: source-only metadata regression tests plus independent canvas zoom/pan tests.
- `test_reports/iteration_79.json`: final opaque owner dialog,12real chapter cards,94live catalog and light-mode contrast checks. Its contrast note compared the dark-mode expectation against a light background; this is not an application defect. Main separately verified actual dark textRGB199,205,214 on backgroundRGB34,28,31.
- `test_reports/chapter_pdf_verification.json`: **actual downloaded**933,407-byte51-pagePDF, ordered question1–50 headings,50supplied-key labels, correct2/150summary and explicit no-worked-solution disclosure.
- Main real browser: phone login redirect; preflight;50-question/3,600-second attempt; forbidden active key asset403; no keys in attempt DTO; correctD and wrongA with offline pending save; reconnect acknowledgement; reload preserving answer/deadline; catalog Resume; submit;1correct/1incorrect/48skipped=2/150; PDFdownload.
- Main real owner browser: selecting Physics PDF in the actual file input and uploading reopens the same30-test/1,500-questionbook with the original expiry. Private Q1/Q50preview source and key images loaded. No duplicate tests were created.
- Final source dialogs, populated catalogs and zoom viewers captured at1920×800and390×844. Horizontal overflow checks empty. Mobile modal background and dark tab contrast defects found during testing were fixed.

## Explicit boundaries

- Supported import is the searchable, structured chapter-book layout described in the UI. Scanned/ambiguous files fail closed; they are not silently OCR-guessed.
- **An unrecognised/new source remains private until its independent per-test recheck is available.** No AI-agent integration or academic review is being faked inside the app. Current supplied books have matching independent reports and are live.
- Supplied answer keys are reproduced exactly; worked solutions and explanations were not invented.
- The earlier owner's75-questionpaired-PDFimport remains ready/unscheduled, unchanged.
- No application APIs are mocked. Isolated unit tests stub external object storage; live uploads, images, attempts and downloads use real services.
- This is a chapter-test feature release, not certification for500,000concurrent users or resolution of previously documented CRA/toolchain security advisories. Those remain separate release gates.
