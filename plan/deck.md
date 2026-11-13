# JEELIVE.AI — PDF Publishing Strategy Deck

## Slide 1 — The product promise
One book in. Separate, source-backed mocks out.

A Super Admin publishing workspace that organises questions, supplied keys and original solutions, automatically publishes complete mocks, and keeps uncertain content private.

Quality means evidence and recoverability—not a promise of perfect AI recognition.

## Slide 2 — The starting point
Already present in the implementation:
- Structured PDF-pair imports and original source crops.
- Specific chapter-book and 50-mock BITSAT parsing foundations.
- Separate AI-assisted extraction, progress, budgets and publication code.

Not yet a unified universal importer:
- Different workflows and limits.
- General combined-book original-solution matching is missing.
- The AI publishing path depends on currently paused solving.

These are implementation findings, not a fresh live-system certification.

## Slide 3 — The first-release ambition
One combined PDF containing 10, 50 or more mocks.

Only intake limit: 100 MB per PDF. No fixed page or mock limit (owner decision, 2026-11-13); large books are read in batches. This covers the requested 15–20 MB books.

JEE Main, BITSAT, COMEDK and explicitly described custom rules, where the test experience supports those rules.

No compulsory publisher template. Legible source content and resolvable structure remain necessary.

## Slide 4 — The journey
Upload → inspect → map the book → create private drafts → pair source content → resolve exceptions → publish clean mocks as a series.

Interrupted transfer resumes. Received books continue processing after the browser closes. A failed region does not erase successful work.

## Slide 5 — The central matching rule
Book edition → mock → subject/section → printed question number.

Question 12 in Physics is not Question 12 in Chemistry. Mock 8's answer table is not Mock 7's.

Every association retains original page evidence. Shared passages and multi-page explanations stay connected to their questions.

## Slide 6 — Source fidelity before visual polish
Preserve formulas, chemistry, diagrams and options using original regions.

Hold clipped content, neighbouring questions and answer-leaking crops.

Show original worked solutions in reading order. Never substitute a newly generated explanation while labelling it as the publisher's solution.

## Slide 7 — AI has two separate jobs
**Reading assistance:** owner-approved, selective recognition of difficult/scanned page layout.

**Explanation generation:** separate owner-click action for questions with a supplied key but no original worked explanation; clearly labelled AI output.

Separate usage visibility and limits. Disagreements stay held. AI does not silently change scoring keys.

## Slide 8 — Automatic publication with boundaries
Clean mocks go live automatically in book order within one series.

Clean requires complete questions, unambiguous supplied keys, matched original solutions or honest key-only labels, supported rules and available safe media.

Incomplete mocks remain private. Readiness is not a confidence percentage. Retries cannot create duplicate mocks.

Default release: as ready. Optional schedule: chosen before processing. Blocked mocks do not unexpectedly launch late.

## Slide 9 — The owner workbench
- Uploads overview: progress, publication and held-work counts.
- Book map: mocks, subjects and question/key/solution ranges.
- Attention Needed: specific problems and direct repair actions.
- Review desk: original page beside question, key and solution.
- Student preview: attempt view versus released explanation view.

Dark JEELIVE styling; evidence and readable source content take priority over decorative dashboards.

## Slide 10 — Three phases
**Phase 1 — proposed next build:** combined-book upload through automatic series publication, including selective AI reading, exception repair and optional AI explanations.

**Phase 2 — future:** wider publisher/scan compatibility, reusable layout profiles, multi-book management and reviewed accessibility improvements.

**Phase 3 — future:** delegated editors, larger publishing operations and advanced edition/correction management.

Only Phase 1 is in scope after approval. No code is being built now.

## Slide 11 — Decisions worth challenging
- Auto-publish each complete mock rather than wait for the whole book.
- Allow clearly labelled key-only mocks while AI generation remains optional and owner-requested.
- Block missing keys or unsupported exam mechanics rather than improvise.
- The only intake limit is 100 MB per PDF, with no page or mock cap. Preview testing on synthetic labelled PDFs (storage and AI mocked) covered 1,501 pages / 150 mocks; that is not a guarantee for every publisher layout.
- Preserve source crops first; do not promise perfect OCR or transcription.
- Keep original books owner-private and protect solutions until the correct release stage.

## Slide 12 — Honest limits and success
No promise of zero recognition errors, instant processing of very large books or a fixed AI bill before the workload is known.

Storage documentation does not provide native resumable upload or permanent deletion; the product must implement recovery and accurately describe access removal.

The known live 520 transport issue is separate and remains unresolved by this plan.

Success: the owner spends time resolving genuine exceptions—not splitting PDFs, manually placing thousands of solutions, or discovering silent mistakes after publication.

The detailed proposal and controlling scope are in `plan.md`.
