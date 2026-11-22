# RCA — BITSAT chapter-wise books: ~50 "fix required" on every chapter

Deployment: campus-search-debug (jeelive.ai) · DB: pdf-engine-v2-test_database
Reader: READER_VERSION=6, book_reader.py sha256 2671148024f36bae…
Reporter: abhishek@billpe.com (id edc17534-b756-4b0b-9734-7e1f9a9d3b97)
Mode: READ-ONLY diagnosis. Nothing modified/re-enqueued/published/deleted.

## Symptom
Super Admin shows ~50 "fix required" on EVERY chapter of an uploaded BITSAT chapter-wise PDF.

## Affected books (tejas_books, BITSAT + layout=chapters, reader_version=6)
- 9983c518-67b0-53d9-93dc-c19730259d77 "logicalreasoning" — state attention_needed, rev 29,
  pages 1119, metrics.blocking_issues 3532. (symptom book / most recent)
- 69f7ecde-9456-5ef9-8208-e4052fbdc7be "chemistry" — state matching, rev 53, pages 2167,
  metrics.blocking_issues 4905. (same defect)

## Root cause (PROVEN from production docs)
Reader v6 misclassifies the per-chapter printed "Answer key" page.

Evidence — tejas_book_pages page 54 (_id b1c88393-97ab-513f-a911-cf95a3776aae), Book A Ch1:
  - classification = "instructions"  (WRONG)
  - context.role   = "key"           (chapter plan correctly expects a key page here)
  - single region: role "instructions", response_type "unresolved", number 0,
    option_labels [], answer "", rect [0.01,0.01,0.99,0.99]
  - region.text contains a CLEAN, fully-OCR'd key: Q01 A, Q02 B, Q03 C, Q04 A, Q05 C … Q50 D
So the key page is readable, but the reader neither classifies it as a key nor parses the
Q->answer table into a key region.

Cascade:
1. pages.key = [] on ALL 18 chapter mocks (tejas_book_mocks). The key page (54,115,176,…)
   is folded into pages.instructions instead.
2. tejas_book_pages classification counts for Book A: questions 900, solutions 197,
   instructions 19, cover 3, key 0 (the "key" classification value does not exist at all).
3. With no key region, the key resolver falls back to scraping answer letters off
   worked-solution pages → per question it finds 20 CONFLICTING letters
   (Q1 source_regions.key: A/A/C/A/B/D/B/C/D/A/C/C/A/B/D/B/C/B/D/A) or nothing
   (Q4+: solution_kind "answer_key_only", key []).
4. Structured fields never populated: options are placeholder stubs
   {"A":"Original option A",...}, solution = "Original book worked solution.",
   answer "" (blank) for most questions; question page regions have option_texts {}.

Result = five repeating issues per question, ~50 per chapter × 18 ≈ blocking_issues 3532,
every mock held, book parked in attention_needed.

## Issue histogram (digits normalised to N; section "Questions")
- "Questions QN: missing or conflicting supplied key."                              ~895
- "Questions QN: incomplete options or key does not match printed labels."          ~895
- "Questions QN: original solution expected but not captured; attach its regions."  ~855
- "Questions QN: original key region required."                                     ~855
- "Questions QN: ambiguous worked-solution start/continuations."                    ~32
(Ch1 fully read = 195 issues, Ch2 = 198; identical structure book-wide, totals ≈ 3532.)

## Classification
CODE bug in the user's app source: book_reader.py (reader_version 6) page-classification +
key-extraction logic. It does not honour the chapter_plan role "key"; answer-key pages are
bucketed as "instructions" and their Q->answer table is never parsed into a key region.
NOT a secret, infra, tier, manifest, or DB-data issue.

## Fix (for E1 / main agent)
In book_reader.py, make the chapter answer-key page classify as a key and parse its
Q->answer grid into a key region:
- Honour chapter_plan role == "key" (and/or detect the "ANSWER KEY" header + Qnn<->letter
  grid) so the page is classified "key" rather than "instructions".
- Emit a key region per question with the printed letter (the data is already cleanly OCR'd),
  instead of falling back to scraping conflicting letters from worked-solution pages.
- Populate structured options/solution/answer from the parsed content rather than leaving the
  "Original option A"/"Original book worked solution" placeholder stubs.
Then re-run the reader for both books (9983c518… and 69f7ecde…).

## Not reproduced in sandbox
The defect lives in the PDF-classification pipeline and requires the source PDF + reader; the
eph pod has neither the source PDF nor secrets, so it cannot be reproduced there. Diagnosis
rests on the production documents quoted above.
