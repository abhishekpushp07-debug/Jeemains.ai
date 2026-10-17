# Guide04 integration — verified continuation

## Implemented

- Optional confidence panel in the real Player. Probability is explicitly supplied, never defaulted. A saved estimate is locally durable and is sent with the first answer without an extra hot-path request. Zero is a valid probability. First committed responses lock the rating; later changed/reverted responses stay excluded from calibration.
- Private profile reflections in expanded Results questions, explicit mistake checklist, saved progress, idempotent retry and revision-CAS conflict/reload handling. Phone-only profiles do not prove phone ownership. Failed saves retain edits in the current page; unsaved reflection edits are **not** promised to survive a full reload.
- A44 expected-value calculator in the existing evidence dialog, using frozen published marking rules and the learner's hypothetical probability. It does not change answers or marks.
- A41 calibration bins (20 overall, 10 per displayed bin), A42 Brier (20), A43 low-confidence penalty exposure (10; configurable threshold default0.20), A45 learner-labelled wrong answers only (5). Prior mistaken metric labels/formulas were corrected against the original source guide and registry.
- A50 does not invent first exposure or mastery. It remains unavailable without verified first-exposure tasks. Checklist completion is a separate workflow indicator.

## Evidence

- `test_reports/iteration_72.json`: independent final review; all294 backend tests pass.37 confidence/review tests added.
- `test_reports/guide04_full_packet1.log`: actual294-pass run including PDF/Excel, owner identity, competitions, correction versions and privacy/embargo gates.
- `test_reports/guide04_final_build.log`: production frontend build passes.
- Main browser verification at the required1920x800 and390x844 viewports (both light/dark) found no horizontal overflow in expanded panels. Independent agent also used1920x1080; that additional viewport is not a replacement for main's1920x800 checks.
- Real browser: no-rating normal attempt, zero/full probability, clear, per-question isolation, first-response lock, changed/reverted exclusion, offline answer recovery/reload, submission; reflection category/note/checklist persist after reload, offline failure/retry, two-tab409 then explicit reload; EV p=0/.2/1 and live A43 threshold update; actual downloaded PDF signature confirmed.
- No application APIs are mocked. Restricted synthetic QA data was used for these browser tests, not the owner's unscheduled paper.

## Preserved boundaries

Original owner UUID/email retained. Owner import `2a830c16-2da1-5687-9d2e-18d3211236de` remains ready and unscheduled; no owner scheduling/live setting was changed. Working PDF-number detection was not edited.

## Not certified

These tests do not qualify500,000 concurrent students, multi-AZ durability, production failover or regional restore. Unsupported evidence-based analyses remain explicitly unavailable rather than fabricated.
