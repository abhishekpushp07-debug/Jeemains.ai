# jeemains.ai — Phase 1 Execution Plan (Premium Practice MVP + Scale Strategy)

## 1) Objectives

Deliver a premium, simple-to-use practice platform for **JEE Main**, **BITSAT**, and **COMEDK** students with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed.
  - “No lagging” is defined via measurable SLOs (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt.
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt**.

### Branding + positioning updates (confirmed)

- Platform name and branding: **jeemains.ai**
- Pre-login landing: premium posters + strong message **“100% FREE for all students”**.

**Truth / compliance constraint (non-negotiable):** any “prediction” copy (e.g., 60/75, 120+) remains aspirational with disclaimers unless backed by real analysis evidence.

### Binding communication preference (critical)

- **No routine checkpoints**: do not ask the user to confirm steps mid-build.
- Progress updates are informational, not approval gates.

### UPDATED USER CHECKPOINT (latest instruction) — AUTONOMOUS IMPLEMENTATION AUTHORIZED

User instruction now explicitly authorizes autonomous execution:
- “Do not ask… just build… world’s best… no lagging for 5 lakhs concurrent… upload pdf/word/excel → live… AI agent solve backend… results show detailed step-by-step.”

**This authorizes** end-to-end implementation + deep autonomous testing.

**Still forbidden / truth constraints**:
- No claim of “500k qualified” without evidence.
- No fabricated percentile/rank.
- No mutating the already-published **94 BITSAT chapter tests**.

### NEW USER REQUIREMENTS (confirmed)

1. **Auto-Publish Uploads (zero-touch for valid sources)**
   - Accept **PDF, Excel, Word**.
   - Automatically extract questions/options/keys + marking scheme, and publish **LIVE** after automated validation.
   - No “manual review gate” for valid papers.
   - If ambiguous/conflicting/unreadable: keep **private**, show actionable issues (no fabricated data).

2. **AI Step-by-Step Solutions (OpenAI Astra)**
   - If solutions/keys are missing or incomplete, automatically generate **detailed, step-by-step solutions** using **`gpt-6-astra`**.
   - Must be provenance-labeled as AI-generated.
   - Must not rewrite sealed scores.

3. **Deep Analytics**
   - Results include **real platform rank + platform percentile** computed from actual platform participants for the same cohort.
   - Per-question correct/wrong/skipped % + option distribution.
   - Subject/topic graphs + score distribution.
   - **Cohort display threshold remains authoritative at >=100** comparable profiles for rank/percentile UI exposure; below that show honest “insufficient cohort” state.

4. **Simple Navigation & Branding (already shipped)**
   - Post-login strictly: 3 cards (JEE Main, BITSAT, COMEDK) → (Mock Tests | Chapter-wise | Results).

5. **UI Update (already shipped)**
   - Question images default to **Fit** on every question change.

---

## 2) Execution updates and current status

### What is working (verified on current HEAD)

- Frontend: jeemains.ai rebrand + **100% free** landing + simplified navigation (3 exam cards → 3 hub cards).
- Player: **Fit default resets** on every question change.
- Backend: existing exam attempt flows, chapter-book pipeline and BITSAT chapter catalogue.
- Astra: provider canaries for **text+JSON** and **vision+JSON** succeeded; model verification for `gpt-6-astra` exists.

### What is currently broken (P0)

Backend is failing to start due to **route-contract / request-contract enforcement gaps** introduced while wiring smart-import + cohorts + AI solutions:

- `tejas/route_contracts.py` blocks startup when:
  - A route lacks an explicit **SPEC** entry, and/or
  - A **body-bearing JSON route** lacks a Pydantic model in `request_contracts.MODELS`.

Concrete observed failures:
- `Body-bearing route lacks an explicit input model: cohorts.air_scenario` (missing MODELS entry).

### In-progress foundation already exists (but unverified end-to-end)

- `tejas/smart_imports.py`: upload → prepare → per-page extraction → reconcile → finalize_paper (auto publish if safe).
- `tejas/office.py`: Word/Excel → PDF conversion boundary (timeout, size limits).
- `tejas/astra.py`: strict model verification + bounded concurrency + two-pass solve/check.
- `tejas/ai_solutions.py`: per-attempt question solution endpoint + background job integration.
- `tejas/cohorts.py`: cohort materialization and rank/percentile computation.

### Known gaps found during latest debug pass

These must be fixed before the pipeline can be trusted:
- **MODELS registry gaps**: missing `cohorts.air_scenario` request model.
- **Upload exemption rules**: ensure multipart endpoints are treated as uploads (no JSON model required) where applicable.
- **Missing helper**: `jobs.drain_for` referenced by `smart_imports`, but not implemented.
- **astra.py schema bug**: `SolutionStep.explanation` accidentally placed inside `reserve_call()` block (syntax/logic error). Needs to be restored inside `SolutionStep`.
- **finalize_paper import issue**: references `tejas_core.question_issues` but canonical implementation is in `tejas/content.py` as `question_issues`.
- **DB indexes missing** for new collections (smart imports, smart papers/questions/keys, ai solutions, cohorts snapshots/entries) to guarantee uniqueness and performance.
- **Design guidelines file hygiene**: the design addendum must be additive (do not overwrite historical design guidance; store addendum separately and reference it).

---

## 3) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

**Status:** Stable

- Existing attempt flows, grading, reporting, offline draft semantics are present.
- Existing chapter content is published and must remain unchanged.

### Phase 2 — V1 App Development (build full product around proven core)

**Status:** MVP exists; UI/UX premium polish ✅ delivered; simple navigation + brand + Fit default ✅ delivered.

### Phase 3 — Comprehensive testing, hardening, and regression

**Status:** Completed for the navigation + UI polish scope, but **NOT** for SmartImport/AI/cohorts.

- Backend regression suites previously passed before the new P0 backend startup break.

---

## 4) NEW Phase — Upload→Auto-Live + Deep Results + AI Solutions (CURRENT PHASE)

**Goal:** owner uploads a PDF/Word/Excel and the system makes it live automatically (if safe), generates missing step-by-step solutions via Astra, and shows deep cohort analytics.

### 4.0 P0: Restore backend startup + contract integrity (IN PROGRESS; DO FIRST)

**Why:** nothing else can be verified until the API boots reliably.

Work items:
1. **Fix request_contracts MODELS gaps**
   - Add missing Pydantic payload for `cohorts.air_scenario`.
   - Ensure every JSON body route in SPEC has a MODELS entry.
2. **Ensure upload routes are treated as uploads**
   - Multipart/form endpoints must not be required to have JSON MODELS.
   - Validate `smart_imports.upload` remains treated as upload.
3. **Implement `jobs.drain_for(set_id)`**
   - Bounded, safe background dispatcher to progress SmartImport pipelines without manual polling.
4. **Fix `astra.py` schema placement bug**
   - Restore `SolutionStep.explanation` as a real field; keep strict schema.
5. **Fix finalize_paper’s validation import**
   - Replace `from tejas_core import question_issues` with the correct import (or re-export safely).
6. **Add required DB indexes for new collections**
   - Uniqueness: smart_imports.request_key, smart_papers.id, smart_questions.id, smart_keys.id, ai_solutions.id, cohort_entries unique constraints.
   - Query performance: smart_questions by import_id/paper_id, cohorts snapshots by id, cohort_entries by cohort_id.

**Exit criteria**:
- `curl /api/health` returns 200.
- Server startup succeeds with route contract enforcement enabled.

### 4.1 P0: End-to-end Auto-Publish pipeline (PDF/Word/Excel) (IN PROGRESS)

**Required behavior** (no manual review gate for valid sources):
- Upload → extract → infer rules → extract questions/options/keys → solve/check missing → publish LIVE.
- Only block publication when extraction/verification is unsafe/ambiguous.

Work items:
1. **Office conversion boundary verification**
   - Word/Excel uploads convert deterministically to PDF via LibreOffice worker.
2. **Smart PDF page extraction**
   - Use Astra vision+JSON extraction per page.
   - Must crop question regions excluding embedded keys/solutions.
3. **Rule inference + dual-check**
   - Two-pass instruction extraction; disagreements set fields to null → triggers clarification.
4. **Reconcile + solve/check**
   - For each verified question: ensure an answer exists from supplied keys OR generate with Astra two-pass agreement.
   - If two-pass disagreement or ambiguity: mark question/paper private with issues.
5. **Finalize and publish**
   - If all questions verified and rules confirmed: create immutable set snapshot + publish automatically.

**Exit criteria**:
- Upload one PDF creates a live set with correct question count and rules.
- Upload one Word and one Excel also succeed.

### 4.2 P0: Student results show step-by-step solutions (AI provenance) (IN PROGRESS)

- For auto-import published sets: `solution_kind='ai_generated'` and step-by-step solution is visible post-submit.
- Ensure report generation includes these solutions in PDFs.
- Preserve embargo rules for competitions.

**Exit criteria**:
- A completed attempt can:
  - view per-question stepwise solution
  - download a single PDF report containing the same.

### 4.3 P0/P1: Deep analytics (platform cohort rank/percentile + question stats + graphs) (NOT STARTED end-to-end)

Backend:
- Ensure cohort materialization runs as background jobs and stores snapshots.
- Enforce **>=100** threshold for showing rank/percentile distribution.

Frontend:
- Integrate cohort results into Results UI:
  - rank, percentile
  - per-question right/wrong/skipped and option distribution
  - subject/topic graphs

**Exit criteria**:
- For cohorts with >=100 comparable profiles: rank+percentile visible.
- Below threshold: honest “insufficient cohort” UI.

### 4.4 P1: Predicted rank “as per 2026 JEE Mains” (DEFERRED / EVIDENCE-GATED)

- Remains non-authoritative and only supported with verified datasets.
- Until then: keep “scenario only” view based on user-entered official percentile.

---

## 5) Next Actions (updated)

### A) ✅ COMPLETE: Brand + navigation + Fit defaults

- jeemains.ai branding + 100% free landing.
- Strict 3-card navigation.
- Fit reset on every question change.

### B) P0: Restore backend startup

- Fix contracts/models, drain_for, astra.py schema, finalize_paper validation import, indexes.

### C) P0: Auto-import upload → AI solve → auto-publish LIVE

- Validate PDF/Word/Excel ingestion.
- Make auto-publish work for safe sources; keep unsafe sources private with actionable issues.

### D) P0: Results + PDF include step-by-step solutions

- Ensure AI solutions appear in student Results and downloaded PDF.

### E) P1: Cohort rank/percentile + per-question analytics graphs

- Materialized cohorts + UI graphs.

### F) P1: Scale qualification strategy (evidence-based)

- Implement app-level protections already present (bounded job lanes, DB pool caps, caching).
- Create reproducible load harness + staged plan; **do not** claim “no lag 5 lakh” without proof.

### G) P2: CRA dependency vulnerability remediation

- Track as explicit blocker until migration/re-audit.

---

## 6) Success Criteria

### Owner / Studio success

- Upload PDF/Word/Excel → automatic extraction → AI solve/check → **LIVE** without manual gates for valid sources.
- Unsafe/ambiguous sources remain private with actionable issues.

### Student success

- Simple navigation retained.
- Results include deep analytics (rank/percentile when cohort >=100) + graphs.
- Step-by-step solutions available in Results and in downloadable PDF.
- Offline draft recovery remains intact.

### Engineering success

- Backend boots with strict route contracts.
- AI runs **off the hot path**, bounded by concurrency and budget.
- No regressions to 94 existing chapter tests.
- Cohort computations are incremental/materialized (no full rescans on every view).

---

## Explicit Release Blockers (remain blockers until qualified)

- **500,000 concurrent user qualification** is unverified until staged load/fault/restore evidence exists on representative infra.
- **Preview infra is not representative** (standalone MongoDB, low CPU quota).
- **CRA/react-scripts vulnerabilities** remain until migration + re-audit.
- **AI-generated solutions** remain provenance-labeled and must not be misrepresented as supplied keys.
- **Predicted 2026 rank** cannot be shown as authoritative without verified datasets/calibration.
