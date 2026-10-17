# Exam refinement delivery — 17 October 2026

## Status
Product refinement and bounded performance work delivered. **NOT a final-production, security-clean, or 500,000-concurrent-user certification.** No infrastructure configuration, production deployment, protected environment variables, owner identity, or original chapter publication windows changed.

## Implemented
- Compact chapter rows with subject/search controls, sticky filtering, availability, resume and results actions. First actionable row fits the 390x844 viewport.
- Scope-correct preflight copy: connection/browser storage checks do not academically certify questions or promise that every source formula is readable.
- Original source canvas opens at readable scale in Player and owner chapter previews. Fit/Readable/zoom/pan/fullscreen keep original pixels; no OCR guessing or invented option text. Mobile images intentionally pan horizontally rather than shrinking formulas into illegibility.
- Source-based answer choices use a clear A–D selection strip referencing the original option image. Desktop shortcuts respect focused controls, dialogs, asset failures and ended attempts.
- Results show sealed-answer and key-only disclosures, a review jump action, and do not promise worked explanations when none were supplied.
- Studio publication checklist separates 50-question checks, agreeing key checks, independent source evidence and failed-processing guidance. Invalid replacement-file selection no longer leaves the earlier valid file selected.
- Fixed owner preview close-animation requests containing `/chapters/null/` by binding assets to the loaded preview's chapter identity.
- Metadata-only Studio queries avoid transferring full question text/keys/crops. Per-chapter latest-attempt aggregation removes the old 200-history-row truncation bug and has an application-managed supporting index.
- Preflight validates each identical source reference once per request. No cross-user or cross-release validation cache; invalid unique regions still block.

## Verified evidence
- `test_reports/refinement-full-regression.log`: **342 passed**, 0 failed; 200 warnings (dependency deprecations), 94.65 seconds. This is the current safe `tests/packet1` suite, NOT a claim that an older 396-test scope was repeated. Ten new regression tests were reviewed and strengthened when initial fixtures did not reproduce the old bugs.
- `test_reports/refinement-final-build.log`: frontend production build compiled successfully, no compilation errors/warnings.
- Independent report83 overclaimed submission/PDF and mislabeled Q1 as text-only. Main discovered its stated attempt was still active; its results claim is rejected. Actual main browser then submitted QA87 with two incorrect answers and verified **-2/150**, 48 skipped, sealed notice, key-only disclosure and a real **1,510,413-byte PDF** (`test_reports/refinement-actual-qa-report.pdf`). QA85 naturally expired at60minutes and showed **3/150**, one correct/49skipped, independently exercising +3 and server deadline finalization.
- Main real browser source proof: loaded canvas pixels change under pan; Fit/Readable/zoom/fullscreen work. Body-focused A shortcut saves; controls retain their own keyboard behavior.
- Main offline proof: C selected offline, UI reports `Offline · 1 pending`, reconnect followed by reload retains C.
- Main deterministic failure injection: browser intercepts a question image with HTTP503; answering disables. Remove interception and click Try again; original image and answering recover. This is a **MOCKED test fault**, not a mocked application API.
- Owner real browser: 32/32 Chemistry question/key/independent checks, Q1 and Q50 source images, readable preview, actual Close button and zero `/chapters/null/` requests after close.
- Actual 1920x800 and 390x844 screenshots with empty horizontal-overflow results for catalogue, Player, owner preview/checklist. Light/dark catalogue verified. Original 94 published owner chapters remain available.
- `test_reports/capacity_catalog_smoke.json`: latest reproducible read-only run, 40/40 HTTP200; p50 71.91 ms, p95 107.89 ms, p99 229.38 ms. Raw samples, version and timing method included. Max4 workers/5rps; no write/load/failover qualification.
- `test_reports/bson_bytes_benchmark.json`: 94 owner chapters, 5,793,146 full-document BSON bytes vs 167,977 projected bytes, **97.1% reduction**. This is database-transfer reduction for Studio metadata, NOT 97.1% overall app acceleration.

## Evidence hygiene and incidents
- Iterations80–82 contained incomplete flows, incorrect OTP/API assumptions and unjustified percentages. They are historical artifacts, not acceptance reports.
- A test tool wrote an owner password literal into generated artifacts. The overwritten test was restored, faulty script removed, affected report redacted. **Rotate the owner password and revoke prior owner sessions before any wider release.** Rotation was not performed because it changes access and needs explicit authorization. Never reproduce the credential in documentation.
- An ad-hoc test operation introduced one synthetic `Test Book` with source fingerprint `abc123` / `test/path` into preview. Main detected count95, quarantined ONLY that exact synthetic book/chapter (`qa_only=true`, `live_enabled=false`, draft), and restored the public owner catalogue to94. The original three source books were untouched. Exact insertion mechanism was not established; do not claim pytest isolation failed. Safe pytest suite uses generated guarded databases; future test-data writes must stay there. No ad-hoc live fixture writes are permitted.
- RCA's suggestion that a database name such as `test_database` inherently proves a misconfiguration is rejected. A name is not topology evidence. No DB_NAME change was made.

## Remaining blockers
1. 500k qualification: visible preview is 2CPU quota/8GiB with colocated services and standalone MongoDB. Dedicated representative capacity, write-burst, failover and restore evidence is absent. See `strategy/INFRASTRUCTURE_CAPACITY_VERDICT.md`.
2. Frontend security: audit remains 49 vulnerable paths /25 unique advisories, including21 high paths; obsolete CRA/webpack dependencies and unpatched transitive entries. Existing compatible direct upgrades were already installed. No unsafe major overrides or untested migration were applied. See existing `FRONTEND_SECURITY_REMEDIATION.md`; CRA-to-supported-toolchain modernization remains unfinished.
3. Studio autonomy: diagnostics improved, but publication of unrecognised new books still requires independent source-check evidence. No reviewer/AI approval is fabricated.
4. This does not re-certify academic correctness of supplied keys, arbitrary/scanned PDFs, or every historical analytics/competition flow.

## Reproduction
From `/app`:
```
python -m pytest tests/packet1 -q
yarn --cwd frontend build
python tests/load/catalog_smoke.py
python tests/load/bson_bytes_benchmark.py
```
Smoke is read-only and guarded. Never raise its budgets to simulate 500k on shared preview.
