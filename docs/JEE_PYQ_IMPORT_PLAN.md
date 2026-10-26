# JEE Main PYQ import: source-backed build plan

## Scope — 2026-10-25
Replace only the JEE Main Mock section/entry labels with date-wise PYQ. Preserve old results and all BITSAT/COMEDK/chapter content. Customer chose “Mock list badlo, history bachao” and clarified the current JEE mock section is empty. Source folder exactly: https://drive.google.com/drive/folders/1k1_N_p3yqWKNJK3HyEp1D3w_PAH63S4m

## Verified source facts
- Shared folder “Jee written pyq” lists 31 PDFs. Full names/IDs persisted in `/app/data/jee_pyq/source_audit/inventory.json`.
- Three actual samples downloaded and rendered/viewed: 2 April 2025 Shift 1 (25 pages); 21 January 2026 Shift 1 (25 pages); 24 January 2026 Shift 1 (27 pages). Last file's name omits its shift; printed page1 confirms Shift1.
- These samples are predominantly image-only. Ordinary PDF text extraction returns106/0/0 characters respectively, so existing text-anchor parser alone is insufficient.
- Viewed headers state180minutes,75questions,25perPCM,300marks,20single-choice+5integer per subject, +4correct/-1wrong for both types. Need reconcile actual question coverage rather than assume all75 exist.
- Two-column reading flow: left column then right, questions followed inline by Ans./Sol.; some questions/solutions span columns/pages. Do NOT assume leftcolumn=question/rightcolumn=solution. Crop originalmath/diagrams, never expose answerline in questionasset.
- Updated2026-10-25: all31originals downloaded;30completepapers mapped/source-reviewed, Jan23 2025S1missing48–50blocked. Approved30paper/2250questionprivatebundle built; isolatedQA140 passed. Authorizedoperationalpreviewimport inprogress; productionnotyetupdated. The chronologicalplan below is retained.

## Implementation sequence and acceptance gates

### 1. Inventory and metadata
Read/download only files in the supplied folder; retain filename, source ID, bytes and digest. OCR/render all cover pages to derive internal date/shift/rules with page evidence. Flag duplicates or metadata conflicts, do not invent a shift. Bound downloads and keep originals private.
Check: every listed file accounted for; no duplicates by content or canonical date+shift without explicit review; downloaded bytes start withPDF and hashes are stable.

### 2. Complete one-paper extraction pilot
OCR image coordinates only to locate subject/section/question-number/Ans./Sol. boundaries. Keep question/option/solution visuals from originalPDF. Join continuation crops in reading order. Map optionnumbers1–4 to stored responsecodes with explicit source numbering; extract integer keys from printedAns., never solve/re-generate missing answers. Preserve provenance per crop.
Check: all actual questionnumbers unique and contiguous within expected source sequence; subject counts reconcile; every key and solution has source evidence; visual check every pilot question/answer boundary plus cross-column/page continuations. No answer or solution pixels in active-test crops. Ambiguity blocks publication.

### 3. Backend import and canonical metadata
Use explicitPYQ classification/date/year/shift rather than label-only mocks. Reuse existing private sources,q_refs/s_refs,immutablepack,deadline/scoring machinery. Import staged,resumable,idempotent; retain per-paper audit and do not modify existingattempts/results. Separate original examdate from availability timestamps so historicalpapers do not become expired schedulingrecords. Missing/conflicting items stay review-only.
Check: repeated/interrupted import produces no duplicates; hashes/keys/crops stable; no sourcepath/answer/solution leak before submission; existing exams unchanged.

### 4. JEE-only catalogue and date tabs
Update JEEhome/card/hub/breadcrumb/destination labels consistently toPYQ. Preserve old links via compatible routing. Date tabs ordered chronologically, newestfirst; same-date shifts remain separate with source-confirmed labels. Year selector only if needed for multi-year collection. Show actualduration/count, no fabricated reviews/claims.
Check: cataloguefilters/dates match metadata;31files not automatically31publishedpapers; no JEEchapter or BITSAT/COMEDK bleed-through; keyboard/mobile navigation and zero horizontal pageoverflow.

### 5. Attempt-aware actions and solutions
Own never-startedpaper→Start; active→Resume; completed→ViewResult+AttemptAgain. AttemptAgain means new full timed paper, not wrong-question revision, and retains all previous results. Duplicate clicks/retries remain idempotent. Cropped suppliedsolutions appear under existingResults subject/question navigator only after submission; retakes remain practice, not fresh-paper rankclaims.
Check: per-userisolation, resumeafterrefresh, lateanswers, doubleclick, sequentialretakes, oldreceipts/results retained, question-to-solution identity verified.

### 6. Bulk validation and release
After pilot passes, process remainingpapers with identical validation and explicitexceptions. Use isolatedDB for functional tests; no tests againstcustomerdata. Render representative and flaggedcrops fromeachpaper, check allmappingcounts, then desktop/mobile Start→Save→Submit→Result→Solutions→AttemptAgain. Publish only reviewedcompletepapers; report anyblockedsource honestly. Productionimport/redeploy status must be separate from previewcompletion.

## No changes authorized to unrelated scope
No otherexamdeletions, no fullDrive access/OAuthsetup merely toreadthisfolder, no generatedreplacementsolutions, no productionDBclone, no fakecompletedmapping, no claim everyprovidedpaper is officialNTA-certified.
