# Tejas — Supplied Document Review

Status: reading and proposal revision only. No application has been built, no paper has been approved, and no content has been publicly published.

## Source inventory

### Original five-volume foundation

1. [01_Product_Design_and_Experience.pdf](https://customer-assets-jt897jd0.emergentagent.net/job_7ba65a29-5776-49a1-8fd6-c0c826332711/artifacts/4dae65cd6152fef4_01_Product_Design_and_Experience.pdf)
2. [02_Exam_Engines_and_Simulation.pdf](https://customer-assets-jt897jd0.emergentagent.net/job_7ba65a29-5776-49a1-8fd6-c0c826332711/artifacts/d80f68ad65239148_02_Exam_Engines_and_Simulation.pdf)
3. [03_PDF_Ingestion_Questions_Solutions.pdf](https://customer-assets-jt897jd0.emergentagent.net/job_7ba65a29-5776-49a1-8fd6-c0c826332711/artifacts/ec7882e394c1d6b1_03_PDF_Ingestion_Questions_Solutions.pdf)
4. [04_Analytics_Results_and_Improvement.pdf](https://customer-assets-jt897jd0.emergentagent.net/job_7ba65a29-5776-49a1-8fd6-c0c826332711/artifacts/cc5107f6cddffd06_04_Analytics_Results_and_Improvement.pdf)
5. [05_Architecture_Security_Scale_QA.pdf](https://customer-assets-jt897jd0.emergentagent.net/job_7ba65a29-5776-49a1-8fd6-c0c826332711/artifacts/f428b7286d832dff_05_Architecture_Security_Scale_QA.pdf)

### Subsequently supplied brief and actual content

6. [Tejas_Emergent_01_Master_Brief_Blue_UX.pdf](https://customer-assets-agu9un31.emergentagent.net/job_campus-launch-2/artifacts/09214480ce08b44d_Tejas_Emergent_01_Master_Brief_Blue_UX.pdf)
7. [Tejas200_Paper01_Questions.pdf](https://customer-assets-agu9un31.emergentagent.net/job_campus-launch-2/artifacts/c44edb7ea0924065_Tejas200_Paper01_Questions.pdf)
8. [Tejas200_Paper01_Key_Solutions.pdf](https://customer-assets-agu9un31.emergentagent.net/job_campus-launch-2/artifacts/8c10e7774e825272_Tejas200_Paper01_Key_Solutions.pdf)

The six specification documents describe the intended product; the last two files are actual paper content. A publicly accessible attachment URL is not evidence of permission to redistribute that content to students.

## New master brief: substantive findings

The 26-page brief contains 23 implementation sections and explicitly identifies the two Tejas Paper 01 files as owner-provided ingestion material, not official examination-rule authority.

Its strongest product priorities are:

- Deliver individual interactive questions rather than embedding a whole PDF and calling it an examination platform.
- Complete one reviewed PDF → question → saved attempt → score → correctly linked solution journey before sophisticated dashboards.
- Separate Student, Content Studio, and Administration responsibilities. Draft preparation, subject approval, and publication remain distinct actions even in a solo-owner pilot.
- Keep keys and unreleased explanations private during active attempts; preserve the versions and option order with which an attempt began.
- Distinguish local drafts, pending saves, and acknowledged answers. A refreshed page, reconnect, or lost submission response must not silently create a different outcome.
- Provide pre-start instructions and device/content checks; do not start the clock merely by opening a paper.
- Preserve original figures, equations, chemical structures, and source references. Reviewers must be able to resolve segmentation and matching errors without treating extraction confidence as mathematical proof.
- Present actionable, evidence-backed results and permit honest unavailable states. Do not claim official ranks, readiness, cheating prevention, or admission outcomes.
- Target WCAG 2.2 AA through the actual experience rather than displaying an unsupported compliance badge.
- Obtain separate permission before public publication or new paid services.

### Differences from the earlier proposal

- The newer proposed design tokens change deep navy to #0B1F3A and the main page background to #F5F9FF, while retaining brand blue #2563EB. The revised proposal adopts these newer values.
- The newer analytics brief calls for at least 40 meaningful analyses and reserves 64 views. The original Volume 4 lists 55 metrics. The proposal retains both as a reconciled longer-term analytics commitment, not a promise of 40 completed analyses in the first paper journey.
- The brief supports a broad four-exam roadmap; the user's explicit first-version choices remain JEE Main and BITSAT. Missing BITSAT content is not filled by relabelling a JEE paper.
- The brief includes a broader account lifecycle, sharing, correction/regrading, notebook, support, and organizational roadmap. These are not implied complete by the basic first-version account and practice flows. The current proposal explicitly defers outbound-email verification/recovery and broader learning features.
- The user's direct requirement to download complete results with matched solutions remains part of the MVP even though the new brief does not specify this export in detail.
- The new brief's author-provided verification claims and reference date do not establish official 2027 examination policies.

## Tejas Paper 01: content inventory

| Item | Observed content |
| --- | --- |
| Source title | TEJAS 200 — PREDICTED PAPER 01 |
| Target printed in source | JEE Main 2027 pattern |
| Question document | 11 pages |
| Key/solutions document | 32 pages |
| Question count | 75, numbered Q1–Q75 |
| Mathematics | Q1–20 single-correct; Q21–25 integer answers |
| Physics | Q26–45 single-correct; Q46–50 integer answers |
| Chemistry | Q51–70 single-correct; Q71–75 integer answers |
| Total response types | 60 single-correct and 15 integer-answer questions |
| Stated duration | 3 hours / 180 minutes, one sitting |
| Stated maximum marks | 300 |
| Stated marking | +4 correct, −1 wrong, 0 unanswered in both sections |
| Solution content | Answer table, Q1–75 worked-solution entries, trap notes, concepts to recognise, author topic/difficulty labels |
| Content language | English questions; solutions include English and Roman-script Hindi/Hinglish |
| BITSAT paper supplied | No |
| Explicit redistribution/download licence found | No |

“Tejas 200” is part of the title. It is not evidence that this file contains 200 questions or that 200 other papers exist. List-matching and multiple-statement stems in this paper still use single-correct answer choices; they must not be misclassified as multi-select inputs.

## Fidelity findings and reading limitations

### Mathematical extraction needs deliberate review

Automated reading produced inconsistent transcriptions for some mathematical expressions. A separate retrieval of the PDF text preserved the missing notation and allowed these spot checks:

- **Q7:** the expression is the sum from k = 1 to 30 of k(ω^k + ω^(2k))^3, not a sum to 100 or an expression missing the cube. Its residue-class calculation gives 1020, matching answer option (3).
- **Q22:** the expansion is (x^3 − 2/x^2)^n. The sum of binomial coefficients gives n = 10, the constant term has index 6, and C(10,6) × 2^6 = 13440. Losing the denominator exponent changes the problem.
- **Q23:** the integral runs from 0 to r inside a sum over r = 1…30, not from 0 to 1 each time. For an integer r, π times the integral of (x+1)|cos(πx)| over 0…r is r(r+2), giving the printed key 10385 after summation.

These resolved reading discrepancies are not evidence that the original questions are defective. No correction to owner content should be made from an unreliable extracted rendering.

### Visual and structural material

- Q8 contains a determinant whose rows and columns must remain intact.
- Figure-dependent items include the P–V diagram in Q27; circuits in Q31 and Q41; the hexagon in Q34; capacitor geometry in Q38; and chemical structures in Q52, Q56, and Q67.
- Matching lists, statements, fractions, signs, vector notation, chemical charges, and option numbering need source-aware presentation.
- Worked solutions and their final concept notes can continue across page boundaries. A solution must end at the next actual question-solution entry, not automatically at the end of a page.
- Repeated stems in the solution document and the front answer table are not additional questions.
- Author-assigned difficulty is an expert/source label, not an empirically measured student difficulty.
- Some source concept labels contain editorial wording such as “legacy archetype (writer supplies).” These need reviewer handling rather than automatic promotion into polished student-facing taxonomy.

### Verification boundary

The answer table and solution-entry coverage have been read, and selected calculations have been spot-checked. This is **not** an independent mathematical audit of all 75 answers, every diagram, or every explanation. The file's statement that earlier solvers checked it is attributed to its author. Platform publication still requires source rendering, correct pairing, content rights, and subject-review approval.

## Result and export contract retained

For every completed attempt, align each delivered question and its original option order with the student's committed response, the approved key, marks, and its matched worked solution. Preserve supplied concept and trap explanations after review. The downloadable report includes the complete attempt, not only filtered mistakes and not two separately concatenated source PDFs.

Permission to view an explanation, permission to include it in a personal downloadable report, and permission to download the entire original source file are distinct. The proposed first published paper requires rights for the complete results-and-solutions report; the original source files remain private.

## Current proposal status

The proposal in plan.md has been updated with the actual paper facts, newer design guidance, extraction safeguards, language preservation, and expanded future analytics target. Approval remains pending. The latest request was to read the files, not to begin building or publish them.
