# JEELIVE.AI — Super Admin PDF-to-Mock Publishing System

An owner-controlled publishing workspace that turns a PDF book into separate, source-backed mocks and an organised test series.
Original questions, diagrams, answer keys and worked solutions stay connected; automation handles routine work and exposes uncertainty instead of hiding it.

## Who it's for

- The JEELIVE.AI owner, uploading books through Super Admin without chat-based content imports.
- Students, receiving complete mocks, correct source-key associations and the corresponding explanation at the appropriate review stage.
- Website and future app users, sharing the existing canonical content, attempts and results.

“World's best” is a quality ambition, not a claim of market leadership or perfect recognition. The standard is dependable recovery, evidence-backed placement and honest limits—not automation that quietly publishes mistakes.

## Core features and experience

### 1. Current capability versus the missing product

These findings come from the current import implementation, not a fresh production certification.

| Area | Existing foundation | Missing for this proposal |
|---|---|---|
| Owner upload | Content Studio offers PDF-pair, structured chapter-book and spreadsheet workflows | One consistent book-upload workspace inside Super Admin |
| Ordinary PDF import | Separate Questions and Solutions PDFs, source-number/subject matching, explicit-key checks and source crops | General combined-book recognition across multiple mocks |
| Ordinary limits | Up to 50 MB per PDF; the ordinary parser accepts up to 300 pages and 300 question anchors | Reliable general handling of 50 mocks and 1,000 pages |
| Chapter books | Certain searchable layouts; the entry point allows up to 1,000 pages and 50 MB | A 1,000-page allowance does not establish arbitrary-book compatibility |
| Combined mock books | A specialised parser exists for a particular 50-mock BITSAT book layout | Reusable recognition across unfamiliar publisher layouts |
| AI-assisted import | Page extraction, paper-rule clarification, saved progress, budgets and publication code exist | That route builds AI explanations instead of preserving original worked solutions; reconciliation currently stops because automatic solving is paused |
| AI-assisted limits | 40 MB upload cap; PDF inspection shares a 300-page reader limit | Consistent large-book support |
| Fidelity and safety | Original regions, source references, integrity checks and ambiguity blocking | Integrated question/key/solution review and repair |
| Recovery | Duplicate-request protection and processing retries exist | Browser-level resumable upload and a consistent restart-safe journey |
| Publishing | Scheduling and publication controls exist | Per-mock automatic publication within a book, with isolated holds |

The proposal reuses these foundations. Neither the specialised parser nor the paused AI route is presented as an already-finished universal uploader. Planning does not change existing AI pauses or publication behaviour.

### 2. Upload a book, not fifty separate papers

The first release targets the requested workload: one PDF containing 10 or 50 mocks, including books of up to 1,000 pages. Proposed intake limits are **50 mocks, 1,000 pages and 50 MB per book**, covering the stated 15–20 MB examples. These are delivery targets, not measurements of present capacity or guarantees that every layout will be understood automatically.

The upload experience includes:
- A primary “Upload Book” action inside Super Admin.
- Continued access to the existing separate Questions/Solutions PDF workflow.
- File size, page count and searchable/scanned-page assessment before expensive processing.
- Resumption from completed upload parts after network interruption. If the browser loses file permission, reselect the same file rather than discard completed work.
- Recognition of an existing identical upload; open its progress instead of creating duplicate mocks. A deliberate corrected edition remains separate.
- Processing that continues after the received book's browser tab closes.
- Separate measured progress for transfer, reading, matching and publication—not a fixed percentage animation.

No compulsory publisher template is required. Readable pages and resolvable structure are required. Missing headings can be repaired through owner-selected ranges. Blurred, cut-off or missing content cannot be reliably reconstructed and remains blocked with a specific reason.

### 3. Map the book before creating mocks

First identify the book's structure, rather than treating every printed number as a question.

Each page is classified as cover, contents, instructions, questions, answer key, worked solutions, mixed content or unresolved. Each proposed mock shows its question, key and solution ranges, subjects and printed numbering.

The intended supported arrangements are:
- Each mock immediately followed by its key and solutions.
- All question papers first, with consolidated keys and solutions later.
- Questions and solutions sharing pages, when they can be safely separated.
- Questions or explanations continuing across pages and columns.
- Numbering restarting within a subject or mock.
- Shared passages and diagrams used by several questions.

A numbering reset alone cannot establish a new mock. Headings, instructions, layout and associated key/solution labels must support the interpretation. Unclear regions enter the owner review queue; independent complete mocks can continue.

### 4. Read clearly structured pages first; use AI selectively

The built-in reader handles clear searchable pages. On scans or unusual layouts, approved AI assistance proposes regions, headings, numbering and associations from the original page.

- Send only necessary pages and nearby context for assistance.
- Show the affected page count and estimated usage before paid processing.
- Where credible pricing is unavailable, state that and offer a bounded page/request allowance rather than an invented monetary total.
- Pause at the approved allowance and preserve completed work.
- Separate the budgets and labels for reading printed content and generating new explanations.
- Treat AI output as a proposal checked against source evidence, not proof.
- Ignore instructions inside the book that attempt to direct the application or AI.

Ordinary PDF parsing does not itself require LLM tokens. Processing, storage and delivery still have costs. AI reading and explanation generation consume additional usage. No fixed price or processing time is promised for an unseen book.

### 5. Pair questions, keys and solutions through their full identity

The matching rule is **book edition → mock → subject/section → printed question number**, supported by original page evidence. “Q12” alone is never sufficient.

Every question retains:
- Its printed number and display position.
- Complete stem, options, diagram and any shared passage.
- Original question page and region.
- Supplied answer and its source location.
- Original worked-solution regions in reading order.
- Conflicts, unresolved continuations and attributable owner corrections.

Reordering a question cannot reattach another question's explanation. Multi-page solutions remain one explanation. Mock 8's answer table cannot be paired with Mock 7 merely because the numbers agree.

Original crops are the primary representation for formulas, chemical structures and diagrams. Extracted text helps review and search but does not silently replace the source. Crops must not contain the next question, a visible key or solution, or a clipped denominator/diagram. If question and answer cannot be separated safely, hold the item rather than leak the answer during the test.

### 6. Original solutions first; labelled AI explanations when requested

There are three distinct student-facing states:

1. **Original book solution:** show the actual worked explanation and page reference, preserving its source layout.
2. **Answer key only:** show the supplied answer with “No worked solution in this book.” The owner can request explanations for an individual question or the book's missing-solution subset.
3. **AI-generated explanation:** show a prominent AI label, never attributing generated reasoning to the publisher.

As selected in the intake, generation is a separate owner-click action with an approved allowance. Uploading a book does not authorise paid explanation generation. Otherwise complete key-only mocks may publish with honest labels. Requested explanations can be added later as separately versioned supplements without changing scoring.

Generation requires a complete question and trusted supplied key. A separate check compares the reasoning and result with the key. Disagreement, unreadable notation or missing information holds the explanation. Agreement is not an academic guarantee. AI cannot overwrite the scoring key, invent missing source questions or masquerade as the book's author.

If an original solution exists but has not been successfully captured or matched, publication waits. Failed extraction must not be relabelled as “the book has no solution.”

### 7. Recognise examination rules without imposing the wrong pattern

The first release covers JEE Main, BITSAT, COMEDK and custom patterns explicitly written in the book.

Detect exam, year/edition where stated, duration, subjects, question types, scoring, compulsory/optional sections and bonus rules. Known exam patterns are cross-checks, not replacements for printed instructions.

Do not assume every JEE Main edition has 75 questions or every BITSAT edition has the same bonus rules. Missing duration, conflicting marks and unsupported numerical-answer rules require correction before publication.

If the current test experience cannot represent a printed instruction, label the mechanic unsupported and hold that mock. Never silently convert optional-choice papers to “attempt all” or change exam rules. “Any pattern written in the book” means explicit rules can be understood and checked; it is not a promise to implement every possible examination mechanic.

### 8. Publish clean mocks automatically as a series

The selected default is automatic publication, not mandatory approval of every book.

“Clean” means required completeness and consistency checks pass. It does not mean that an AI assigned a high confidence score or proved the publisher's answers correct.

Publication requires:
- Unambiguous mock and section boundaries.
- Accounted-for question counts, with unexplained gaps and duplicates resolved.
- Complete question content, answer controls and safe crops.
- An unambiguous supplied scoring key for every scored question.
- Every identified original solution correctly attached, or a truthful key-only state where none exists.
- Complete rules supported by the test experience.
- Available media and no unresolved blocking issue.
- Current owner publishing permission and confirmation of content-use rights.

Ready mocks appear inside one series in book order. Incomplete mocks remain private; their original numbering is preserved. Students see accurate published counts, not empty cards suggesting the entire book is ready. Publication retries cannot duplicate a mock.

Default release is immediate availability as each mock becomes ready. The owner may instead set a schedule before processing. If a blocked mock misses its release, it stays held for a new release decision rather than launching unexpectedly late. The owner can pause automatic publication for the book.

Answers and solutions must not be accessible during an active attempt, including through hidden asset links. Practice review unlocks after submission. Competitive scheduled tests withhold solutions until their release window closes. Whole source PDFs remain owner-private.

### 9. Resolve exceptions without restarting the book

An “Attention Needed” queue identifies the affected mock/question, source page, precise problem and repair action.

Examples: missing key; two candidate solutions; uncertain mock boundary; incomplete options; answer visible in crop; unsupported rule; unreadable page; conflicting supplied keys.

The review workspace allows the owner to:
- Correct mock/section boundaries and associate solution ranges.
- Resize, split or join original-page regions.
- Attach a continuation or shared passage.
- Correct a misread label or key using visible source evidence.
- Record an editorial correction and reason, distinguished from the printed source.
- Reprocess affected content without discarding unrelated completed work.

An override cannot simply dismiss a missing question or unsafe crop. Resolved items pass publication gates again. Published questions and keys are not silently overwritten: corrections create explicit new versions, preserving previous attempts and scores. A newly discovered source conflict permits pausing a mock without deleting student history.

### 10. Reliability, privacy and honest quality reporting

Show separate counts for detected, complete, held, published and awaiting-budget items. Every failure needs a recoverable action. No completion time is promised for 1,000 pages before scan complexity and capacity are known.

Upload, original-source access, repair and publishing remain owner-only in the first release. Rights confirmation covers student use of questions, explanations and reports.

The documented storage integration supports persistent objects and protected delivery, but does not provide native resumable multipart uploads, direct signed browser links or physical deletion. Upload recovery is therefore a product capability to build, not a storage feature already present. “Remove import” must describe access removal accurately; permanent erasure cannot be promised without an actual storage lifecycle capability. Historical-result assets remain available where required.

Report quality through separate measures:
- Automatically processed versus manually repaired content.
- Missing and duplicate associations.
- Original solutions, key-only entries and AI explanations.
- Crop defects and answer-leakage flags.
- Time to first ready mock, whole-book completion and owner review effort.
- Reading usage versus explanation-generation usage.

Zero unresolved blocking issues at publication is a release rule, not a claim that detection can never miss an error. Avoid unsupported accuracy percentages.

The previously reported intermittent live 520 transport issue remains a separate operational limitation. Resume and safe retry reduce its impact; they do not prove that infrastructure fault is resolved.

## User flow

1. **Super Admin → Uploads:** see books, live series, held mocks and paused work.
2. **Choose PDF:** confirm rights; source-first processing and automatic clean-mock publication are the defaults.
3. **Inspect:** receive page/file facts, scan assessment and unsupported conditions. Approve an allowance before paid reading.
4. **Map:** see proposed mocks, sections and question/key/solution ranges. Uncertain ranges enter Attention Needed.
5. **Organise:** private mock drafts receive their own complete questions, keys and original explanations.
6. **Repair exceptions:** open the exact source location and correct boundaries or associations without uploading again.
7. **Publish:** clean mocks enter the series automatically; incomplete mocks remain private.
8. **Optional explanations:** request labelled AI explanations for key-only entries after approving their workload.
9. **Student preview:** compare the active-attempt experience with the released-solution experience.
10. **Maintain:** recover interruptions, pause affected mocks or introduce corrected versions without losing student history.

## UI/UX feel

A focused publishing workbench within JEELIVE.AI's existing dark visual language, not a redesign of student pages.

- **Uploads overview:** one primary Upload Book action, clear progress and recent activity; the two-PDF workflow remains secondary.
- **Book map:** compact mock/subject tree with page coverage and counts, avoiding hundreds of full-size previews.
- **Review desk:** original page with crop outlines beside the question, supplied key and matched solution. Mock/section/question identity stays visible.
- **Clear states:** Received, Reading, Matching, Attention Needed, Ready, Published and Paused, expressed with text/icons as well as colour.
- **Distinct provenance:** original explanation, key-only entry and AI explanation have unmistakable labels.
- **Cost clarity:** approved allowance, usage and pause reason; no surprise “generate everything” action.
- **Responsive controls:** mobile upload, progress, simple review and pause/resume; full-screen zoom for crop work, with desktop preferred for complex editing.
- **Readable student content:** zoomable source crops and ordered multi-page explanations, not tiny whole-page screenshots. Images are not advertised as fully accessible transcriptions.

The companion `deck.md` presents this strategy as a slide-by-slide decision deck without adding scope.

## Implementation phases

### Phase 1 — MVP: dependable combined-book publishing

**Only this phase is proposed for the next build after approval. No implementation occurs during planning.**

Deliver the complete Super Admin journey: one combined book, recoverable upload, book map, original question/key/solution capture, private drafts, exception repair, selective AI reading, owner-requested labelled explanations and automatic clean-mock publication as a series.

Include JEE Main, BITSAT, COMEDK and explicit custom rules within supported test mechanics. Target 50 mocks, 1,000 pages and 50 MB per book. Common searchable, mixed and legible scanned layouts are included; unfamiliar regions may need owner guidance. Unsupported structures receive clear holds, not false success.

**Usable outcome:** a 10- or 50-mock book becomes individually organised mocks with correctly associated explanations; incomplete mocks are isolated, spending is controlled and uploading alone never triggers optional explanation generation.

**Excluded:** inventing missing source material, autonomous correction of publisher answers, handwriting guarantees, unrestricted examination mechanics, retrospective score changes and native-app interface redevelopment.

### Phase 2 — broader compatibility and less owner effort

Expand publisher-layout coverage, difficult scan handling, bilingual structures and complex shared diagrams/passages. Introduce reusable owner-confirmed layout profiles and improved edition comparisons. Saved conventions never bypass uncertainty or publication gates.

Add multi-book queue management and bulk scheduling. Improve mathematical and accessibility transcriptions as separately reviewed representations while retaining original sources.

**Usable outcome:** the next book from a recurring publisher needs less manual review without compromising evidence or student-facing fidelity.

### Phase 3 — publishing operations at scale

Add delegated editorial review with explicit permissions, approval responsibilities, richer quality reporting and controlled correction workflows across larger libraries. Expand processing capacity and documented workload limits based on demonstrated demand—not unsupported concurrency claims.

Provide richer calendars and edition comparisons while protecting canonical content and historical results. Permanent-erasure commitments require storage capabilities that genuinely support them.

**Usable outcome:** a larger publishing operation manages many series without losing accountability, original-source evidence or cost control.

Phases 2 and 3 are future scope. Approval does not authorise building them automatically.

## Assumptions

### Confirmed choices carried into this proposal

- Strategy, plan and deck only now; no code or deployment.
- The uploader belongs inside Super Admin; existing Content Studio capabilities are reused.
- AI may read difficult layouts after shown usage is approved.
- Missing worked solutions may receive clearly labelled AI explanations through a separate owner-click action.
- Clean mocks publish automatically as a series; problematic mocks remain held.
- JEE Main, BITSAT, COMEDK and explicit custom patterns belong in the first release.
- Original questions, supplied keys and original explanations are preserved; no fabricated source content.

### Decisions made without additional questions

- Proposed first-release ceiling: 50 mocks, 1,000 pages and 50 MB per book. This is a delivery target, not a claim about arbitrary layouts today.
- One combined PDF is primary; existing paired-PDF uploads remain available. New Word, spreadsheet or image-folder expansion is outside this scope.
- Each clean mock publishes immediately by default; scheduling can be chosen before processing. A missed blocked release needs a new release decision.
- Clearly labelled key-only mocks can publish; optional AI generation does not hold otherwise complete source-only publication.
- Missing/conflicting keys block publication. AI never supplies an authoritative missing scoring key or silently changes a printed answer.
- Printed instructions outrank generic exam presets. Unsupported mechanics are held rather than converted.
- The existing configured AI provider/model is retained; no model migration is authorised. Availability and pricing are not assumed guarantees.
- Existing AI integration and approved allowances are used; no additional paid OCR subscription is assumed. Declining paid reading leaves manual review available.
- Original source regions are the initial fidelity standard. Perfect OCR, unreadable handwriting recognition and fully accessible mathematical transcription are not promised.
- First-release upload, repair and publishing are owner-only; editorial delegation is future scope.
- Students receive authorised question/solution assets at the correct stage, never the private original book by default.
- Existing attempts/results remain unchanged. Supplemental explanations cannot alter historic scores.
- Storage removal means access removal unless physical deletion is supported. No invented permanent-erasure or retention promise is made.
- The deck is a written Markdown slide deck, not a generated PDF or PowerPoint.
