# Tejas Exam Platform — UX Audit (Read-only)

Date: 2026-10-17  
Scope: **Product/design audit + strategy only**. No implementation.  
Primary audience: owner + main agent implementing next iteration.

## 0) Evidence & audit boundaries (what is / isn’t verified)

### Verified via code inspection (source-of-truth)
- Frontend: React (CRA) + Tailwind + shadcn/ui primitives.
- Key routes present:
  - Student: `/exams`, `/sets/:id` (preflight), `/attempts/:id` (player), `/results/:id`
  - Staff: `/studio`, `/studio/imports/:id` (organiser), `/studio/chapter-books/:id`, `/studio/:id` (legacy editor)
- Styling/tokens: matte maroon brand `#5C0025` implemented as `--blue`/`--brand-text` in `App.css` and `--primary` in `index.css`.

### Visual verification (screenshots)
The problem statement referenced fresh screenshots at `/app/docs/audit/2026-10-17/...jpg`, but **those files are not present** in the repo at that path.
- I therefore **cannot** claim visual verification of the specific “catalog hero takes whole mobile viewport” concern from those missing images.
- I *can* reference other available audit images under `/app/docs/audit/tests/*.jpeg` (e.g., Studio mobile, Player desktop, Login desktop) as secondary context, but they are not the requested “fresh” set.

### What this audit focuses on
- Evidence-based UX/product gaps that affect:
  - **Learning UX** (clarity, trust, cognitive load)
  - **Hot-path reliability UX** (offline saving, timer, submission confidence)
  - **Scale-readiness UX acceptance criteria** (INP, perceived performance, progressive disclosure)
- No new features/gamification.
- No palette/font reset.

---

## 1) Product reality snapshot (what exists today)

### 1.1 Current UX strengths worth preserving
These are real, visible in code and/or existing screenshots.

1) **Matte maroon identity + restrained UI**
- Tokens are coherent and consistent across surfaces (`--surface-card`, `--surface-alt`, `--line`, `--shadow-tint`).
- Buttons avoid `transition: all` and use targeted transitions (good for transform safety).
- Source: `/app/frontend/src/index.css`, `/app/frontend/src/App.css`.

2) **Player is already “exam-serious” and operationally honest**
- Clear save-state bar with offline indicator and pending count.
- Asset-load blocking: if a required source image fails, answering is locked and user is told not to guess.
- Navigator has meaningful states (answered/marked/pending).
- Source: `/app/frontend/src/features/Player.js` (savebar, assetBlocked/locked logic, navigator).

3) **Preflight is unusually strong for trust**
- Explicit offline-saving policy and device check.
- Clear rules list and marking.
- Source: `/app/frontend/src/features/SetDetail.js`.

4) **Results page avoids fake “percentile” claims**
- Explicit copy: “percentage … not a percentile”.
- Drill-through pattern exists (`openQuestion()` expands and scrolls to evidence).
- Source: `/app/frontend/src/features/Results.js`.

### 1.2 Current UX liabilities (high confidence from code)

- **Catalog density + navigation cost**: `/exams` uses pagination and large cards; for 94 chapter tests this can become many pages and high scroll cost.
  - Source: `/app/frontend/src/features/Exams.js` (page state, `set-grid`, pagination).

- **Preflight “device check passed” claim may overstate what’s actually verified**
  - UI says: “Connection, source images and saving verified.”
  - The check call is `POST /sets/:id/preflight` with `test_response` only; it does not obviously prove image clarity on-device.
  - Source: `/app/frontend/src/features/SetDetail.js` lines around the device check success message; API call at `post('/sets/' + id + '/preflight', ...)`.

- **Typed-option math rendering risk**
  - Player options render `MathText` only when `render_mode !== 'source'`, which is correct; however audit evidence indicates typed options previously displayed raw `$...$` in some path.
  - Current code *does* wrap typed option values with `<MathText text={value} />`.
  - This needs re-validation in real browser for all typed-option sources.
  - Source: `/app/frontend/src/features/Player.js` option rendering; math renderer: `/app/frontend/src/components/QuestionContent.js`.

---

## 2) Prioritized UX findings (P0/P1/P2) with evidence

Severity meaning in this doc:
- **P0**: blocks trust in core attempt flow (students will churn / complain)
- **P1**: major friction or confusion in hot path
- **P2**: polish / conversion / clarity improvements

### P0 — Trust & correctness perception gaps

#### F-P0-01: “Verified” language in preflight is too absolute
**Why it matters:** For low/mid-range phones, students interpret “verified” as a guarantee. If later an image fails or saving conflicts, trust collapses.

**Evidence**
- Copy: `Connection, source images and saving verified.`
- Source: `/app/frontend/src/features/SetDetail.js` (device check success message).

**Recommendation**
- Replace absolute “verified” with scoped truth:
  - “Connection check passed. Saving is enabled on this device. You can zoom source images during the attempt.”
- Add a micro-disclosure: “If any source image fails to load during the attempt, answering will pause until it loads.” (this is already true in Player).

**Acceptance criteria**
- Preflight copy must never claim on-device readability was verified.
- Must align with actual enforced behavior in Player.

#### F-P0-02: Catalog-to-attempt path must minimize “marketing hero” above the fold (mobile)
**Why it matters:** Students arriving to practice want the first actionable test card quickly. Any hero that consumes the viewport increases bounce.

**Evidence**
- Code shows a large heading block `.chapter-exams-heading` with H1 and a rules panel.
- Source: `/app/frontend/src/features/Exams.js` + `.chapter-exams-heading` styles in `/app/frontend/src/App.css`.
- **Screenshot verification missing** for the specific referenced images; this is code-based inference.

**Recommendation**
- Convert the top block into a **compact “Exam header”** on mobile:
  - Title (1 line), subtitle (1 line), and a compact rules chip row.
  - Move the longer description into a collapsible “About chapter tests” disclosure.
- Ensure first test card appears within ~1.2 screens on 390×844.

**Acceptance criteria**
- On 390×844, first card’s title must be visible without scrolling more than ~400px.
- INP target: filter/search interactions feel instant (see §6).

### P1 — Efficiency & cognitive load

#### F-P1-01: 94 items + pagination + large cards = high navigation cost
**Evidence**
- Pagination exists and cards are content-heavy.
- Source: `/app/frontend/src/features/Exams.js` (pagination, `SetCard`), `/app/frontend/src/App.css` (`.set-card`, `.chapter-test-card`).

**Recommendation: information hierarchy change (no new features)**
- Keep the same data, but change presentation:
  1) **Default view = compact list rows** (1 row per test) with:
     - Chapter number + title
     - 50Q/60m/+3/-1
     - Availability + attempt state
     - Primary CTA
  2) Optional “Card view” toggle for users who prefer cards.
- Add **sticky filter bar** on mobile (subject tabs + search) so users don’t scroll back up.

**Acceptance criteria**
- Median time-to-open a specific chapter test (e.g., “Physics Chapter 12”) should be achievable with:
  - 1 subject tap + 1 search + 1 tap (no pagination hunting).

#### F-P1-02: Options UX for source-rendered questions is cognitively tiring
**Evidence**
- When `render_mode === 'source'`, options show “Option A (as shown above)” rather than the option content.
- Source: `/app/frontend/src/features/Player.js` option rendering branch.

**Why it matters**
- Students must repeatedly zoom/scan the stem image to see options; this increases fatigue and errors.

**Recommendation (policy + UI pattern)**
- Establish a **Readable Math Policy**:
  - If options are not safely extractable as typed math, keep source images.
  - But provide **option-region thumbnails** (cropped from source) inline per option when available.
  - If not available, provide a single “Options strip” image anchored below the stem (one zoom target).
- This is not “worked solutions”; it’s faithful source rendering.

**Acceptance criteria**
- For source-rendered MCQ, user must be able to view all options with **one zoom action** maximum.

### P2 — Clarity, accessibility, and perceived performance

#### F-P2-01: Touch target consistency gaps
**Evidence**
- Audit report notes two mobile targets below 44px (brand link ~40px, login ~42px).
- Source: `/app/docs/audit/AUDIT_REPORT.md` (UI observations).

**Recommendation**
- Enforce `min-height: var(--touch-target)` for header actions and brand link hit area.

#### F-P2-02: Results page is powerful but risks “too much at once”
**Evidence**
- Results includes summary tiles, metrics, report CTA, subject/topic tables, insights, analytics workspace, then review list.
- Source: `/app/frontend/src/features/Results.js`.

**Recommendation**
- Progressive disclosure:
  - Keep summary + report CTA.
  - Collapse “Topic summary” by default (already in `<details>`).
  - Ensure analytics workspace has strong empty/unavailable states (already in guidelines; verify implementation).

---

## 3) Screen-by-screen strategy (what to change first)

### 3.1 `/exams` (Catalog)
**Goal:** fastest path to “Start” for chapter tests.

**Plan**
- Mobile-first:
  - Compact header
  - Sticky filter/search
  - Compact list rows
  - Keep disclosure “Answer keys only” visible but not bulky

**State patterns**
- Loading: skeleton rows (already used)
- Empty: existing `.empty-state`
- Error: `ErrorBox` with retry

### 3.2 `/sets/:id` (Preflight)
**Goal:** trust + readiness without overclaim.

**Plan**
- Keep two-column desktop layout.
- On mobile:
  - Make “Start attempt” sticky bottom CTA once device check passed + acknowledged.
- Copy corrections (see P0).

### 3.3 `/attempts/:id` (Player)
**Goal:** reduce fatigue, increase confidence in saving.

**Plan**
- Keep savebar + offline semantics.
- Improve source-option viewing (see P1).
- Keyboard:
  - Arrow keys for next/prev question
  - A/B/C/D keys to select options (desktop)

### 3.4 `/results/:id` (Results)
**Goal:** evidence-based review, not analytics theater.

**Plan**
- Keep “openQuestion” drill-through.
- Ensure “answer key only” disclosure is repeated near solution panel (already present).

### 3.5 `/studio/imports/:id` (Organiser)
**Goal:** staff confidence that pairing is safe; students never see unverified content.

**Plan**
- Keep schedule locked until issues resolved.
- Improve “Issues” tab to be scannable:
  - Group by type (missing answer, conflict, parse)
  - Provide “Upload corrected sources” CTA at top.

---

## 4) Readable Math / Source Fidelity Policy (no guessed formulas)

### Principles
1) **Never invent math**: if extraction is uncertain, show source image.
2) **Typed math must render consistently** using KaTeX via `MathText`.
3) **One-zoom rule for options** in source-rendered MCQ.

### Implementation guidance (for main agent later)
- Prefer:
  - `QuestionContent` source regions + `SourceDetailViewer` zoom.
- Add option-region support only if backed by real source refs; otherwise keep “Options strip” image.

---

## 5) Information hierarchy & component patterns (shadcn-first)

### Catalog row pattern (recommended)
- Use shadcn `Card` but styled as a row:
  - Left: chapter badge + title
  - Middle: meta chips
  - Right: primary CTA
- Every CTA must have `data-testid`.

### Sticky mobile action bars
- Use `position: sticky; bottom: 0;` with safe-area padding.
- Only for:
  - Preflight start
  - Player next/submit (optional)

---

## 6) Performance & scale UX acceptance criteria (frontend-facing)

These are UX-level criteria that correlate with “no lag” perception on low/mid phones.

### Interaction performance (INP-oriented)
- Catalog filter/search:
  - Input debounce already 180ms; ensure list updates do not cause long main-thread blocks.
  - Target: interaction-to-render under ~200ms on mid-range Android.

### Rendering strategy
- Avoid rendering 94 heavy cards at once.
- Prefer:
  - compact rows
  - pagination or virtualization (only if needed)

### Offline resilience UX
- Player must always show:
  - online/offline
  - pending count
  - conflict state with explicit resolution
- Already present; ensure copy is consistent across screens.

---

## 7) Accessibility & keyboard plan

### Minimum requirements
- Touch targets >= 44px (`--touch-target`).
- Focus visible (already global `:focus-visible`).
- Navigator buttons must have meaningful `aria-label` (already present).

### Keyboard shortcuts (desktop)
- Player:
  - `A/B/C/D` selects option
  - `←/→` prev/next
  - `M` toggle mark-for-review
- Results:
  - `Enter` expands/collapses question row

---

## 8) Concrete “next sprint” checklist (no new features)

1) **Catalog mobile header compaction** (reduce above-the-fold height)
2) **Catalog list density** (row view default)
3) **Preflight copy correction** (remove absolute “verified”)
4) **Source-rendered options: one-zoom rule** (options strip or option crops)
5) **Touch target fixes in header**
6) **Keyboard shortcuts in Player**

---

## 9) Source references (key files)

- Global tokens/styles:
  - `/app/frontend/src/index.css`
  - `/app/frontend/src/App.css`
- Catalog:
  - `/app/frontend/src/features/Exams.js`
- Preflight:
  - `/app/frontend/src/features/SetDetail.js`
- Player:
  - `/app/frontend/src/features/Player.js`
  - `/app/frontend/src/components/QuestionContent.js`
  - `/app/frontend/src/components/Shared.js` (`SourceImage`, zoom dialog)
- Results:
  - `/app/frontend/src/features/Results.js`
- Studio organiser:
  - `/app/frontend/src/features/StudioImport.js`

