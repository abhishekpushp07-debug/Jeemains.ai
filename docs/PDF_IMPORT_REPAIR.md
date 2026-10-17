# PDF importer repair — supplied Tejas200 Paper01

## Report and root causes

User: “By the way pdf se nahi le pa rha direct questions. Ab”. This superseded ongoing analytics work.

1. The real questions PDF (11 pages) contains75question headers; solutions PDF (32pages) contains75solution headers. The old parser counted77and338 respectively because bare numbered solution steps/continuation lines were promoted to question headers. It rejected the solution PDF at the legitimate300-question safety limit.
2. A secondary issue confused A–D statement/diagram labels inside Q37/51/56/60/67/70 with the actual numbered1–4 answer options. Previous stored keys were ordinal-equivalent letters, but original option labels were not preserved.
3. Shared source-image buttons inherited a fixed Shadcn height and let large PDF crops overlap following questions/solutions.

## Fixes

- Document-level explicit Q/Question header precedence; bare-only papers retained. Ambiguous same-indent mixed numbering is rejected rather than silently dropping questions. The300-question ceiling, chroot, low UID, seccomp and resource budgets remain unchanged.
- Final ordered option-block detection, not first alphabetic labels in a stem/figure. All60MCQs of this paper retain original numeric1–4 options. Missing/conflicting explicit keys still block scheduling.
- Uncomplicated, layout-faithful ASCII PDFs may import as typed stems/options/solutions. Superscripts, mathematical fonts, Unicode notation and diagrams conservatively retain original PDF regions. This is NOT OCR or general PDF-to-LaTeX conversion.
- Source images use intrinsic button height and mobile modal sizing, eliminating overlap/viewport overflow.
- Studio's main action now leads to the unified PDF/Excel uploader; the manual editor is secondary.

## Actual owner paper

Corrected import: `2a830c16-2da1-5687-9d2e-18d3211236de`

Path: `/studio/imports/2a830c16-2da1-5687-9d2e-18d3211236de`

- Owner authenticated through existing credentials; no credential changes in this task.
- Real browser uploads of the user-provided PDFs, real object storage, not mocked.
- READY,75questions,60MCQs/15integers,0issues,191private source assets.
- All75literal keys independently match the first-page answer table fixture. Every MCQ uses original1–4 keys.
- Unscheduled and NOT live; the required start date/time remains the owner's choice.
- Prior pre-fix diagnostic import047ee1… was unscheduled and is archived/superseded, not modified into a published version. Synthetic QA fixture hidden from normal lists.

## Evidence

- `/app/tests/fixtures/tejas200_keys.json`: first-page key-table extraction independent of organiser output.
- `/app/tests/packet1/test_pdf_numbering_and_text.py`: bare compatibility, mixed ambiguity, false solution-step anchors, simple typed output, math/font/Unicode fidelity, corrupt and over-limit PDFs, exact real75-key regression.
- Plain MCQ regression invokes the real protected subprocess and asserts no issues, stem, all four option values and key—not just render_mode.
- Full isolated suite:257passed,0failed,0xfail;125existing deprecation warnings. Log `/app/test_reports/pdf_fix_full_regression.log`.
- Frontend build passes; actual1920x800 and390x844 Q37 source and matched solution inspected. Image bounds stay inside buttons; mobile image dialog has no horizontal overflow.
- Live application database, separately from isolated pytest database, was inspected and confirmed all75keys/191source-file links for corrected import.

## Reconciliation of misleading subagent reports

- Iteration65 read the OLD import047ee1… and incorrectly attributed its persisted letter-option data to the repaired algorithm. Read-only RCA and fresh protected processing confirmed stale data. The corrected browser upload above is the live evidence.
- Iteration66's empty-import finding used a different database context. It does NOT indicate deleted live data; main-agent live DB/API checks verified the new paper exists and is READY.
- Do not call this a production-readiness or500,000-user capacity qualification. Do not claim a full student attempt/report was run on this newly unscheduled paper; existing attempt/report/Excel regressions passed, while the real newly uploaded paper was validated through organiser/storage/source preview.
