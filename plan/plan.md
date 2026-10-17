# Tejas Exam Platform — Landing Page and Working Practice MVP

Tejas is a student-first preparation platform that turns supplied question and solution PDFs into reliable practice, clear results, and question-by-question explanations.
The first release combines a premium landing page with working JEE Main and BITSAT practice, including downloadable PDF reports containing results, questions, and their correctly matched solutions.

## Who it's for

- Students preparing for JEE Main and BITSAT who need to understand mistakes, not merely receive a score.
- Students using phones, keyboards, assistive technology, or unreliable connections.
- The platform owner and authorized content reviewers who supply question papers, answer keys, and solutions and approve them for student use.
- WBJEE and COMEDK students in a later release; these exams are not presented as available in the MVP.

## Core features and experience

### Supplied materials and the first real paper

The original five specifications remain the foundation. The subsequently supplied **Tejas_Emergent_01_Master_Brief_Blue_UX.pdf** refines that foundation: individual interactive questions rather than embedded papers, dependable saved answers, private keys, reviewed publication, and a complete student journey before advanced dashboards. The user's explicit downloadable results-and-solutions requirement remains mandatory even though the new brief does not describe that export in detail.

The supplied **Tejas200_Paper01_Questions.pdf** and **Tejas200_Paper01_Key_Solutions.pdf** provide the first actual content pair:

- **Tejas 200 — Predicted Paper 01:** 75 questions, not 200 questions. The question paper has 11 pages; the key-and-solutions document has 32 pages.
- Mathematics Q1–25, Physics Q26–50, and Chemistry Q51–75. Each subject contains 20 single-correct questions followed by 5 integer-answer questions: **60 multiple-choice and 15 numerical questions** overall.
- The paper's stated custom practice rules are **180 minutes, 300 maximum marks, +4 correct, −1 wrong, and 0 unanswered**, including the numerical section. All 75 questions are included; unanswered responses remain permitted and receive zero under the stated rules.
- Preserve its original question and option order for the initial full-paper attempt. Shorter revision sets must be separately labelled and must not inherit the full paper's duration or maximum marks.
- The source calls itself “JEE Main 2027 pattern.” Display it as an **owner-supplied, nonofficial JEE Main practice mock for 2027**, not an official 2027 paper, verified official pattern, actual PYQ, or prediction guarantee.
- The companion document supplies an answer table and Q1–75 solution entries, including worked steps, trap explanations, concept-recognition notes, and author-assigned topic/difficulty labels. Preserve these after review, including their original English/Hinglish wording; do not silently translate or rewrite them.
- Five-digit numerical keys occur, including Q22 = 13440 and Q23 = 10385. The practice input must accept the supplied approved answers rather than impose an assumed official digit limit.
- Extraction needs source-based review: powers, denominator exponents, integration limits, determinants, circuit diagrams, and chemical structures must not be flattened or guessed. Repeated stems and answer-table entries in the solution document must not create duplicate questions.
- The documents' claim of prior answer verification is an author statement, not independent approval by this platform. Rights, rendering, pairing, and answer review remain publication gates.
- **No BITSAT content paper has been supplied.** BITSAT remains an MVP-supported practice category, with an honest no-published-papers state until suitable owner-provided content is reviewed. The JEE paper is not relabelled as a BITSAT mock.

The source inventory and reading findings are recorded in the companion source review. These uploads update the proposal; they are not approval to begin construction or publish content publicly.

### 1. A landing page that leads into a real product

- Retain the **Tejas Exam Platform** name and the PDFs' blue-and-white identity.
- Explain the central learning loop: **practice → understand results → review matched solutions → improve**.
- Provide clear sections for JEE Main and BITSAT, how practice works, question-and-solution quality, results and downloads, accessibility, and frequently asked questions.
- Make **Start practicing** the primary action and **See how it works** an on-page explanatory action. Both lead to genuine, available experiences rather than placeholder destinations.
- Let visitors explore published practice sets without creating an account. An account is required to start and save an attempt.
- Show actual content availability. If supplied papers are not yet reviewed, explain that no practice sets are published; do not invent papers, question counts, or results.
- Show no invented testimonials, university endorsements, student totals, score improvements, ranks, countdowns, pricing, or performance guarantees.
- Describe later capabilities as planned rather than already available. Do not imply affiliation with exam authorities.

### 2. Owner-supplied PDFs become reviewed practice sets

- Provide an owner/reviewer workspace for uploading a question PDF and its corresponding solution PDF. A separate answer-key PDF can also be attached. A combined questions-and-solutions PDF is supported through the same review process.
- Require confirmation of permission to use the content and record its source, exam, paper or set identity, and year when known. Record permitted audience, attribution, expiry where applicable, and permission to include questions and solutions in downloadable personal reports; permission to upload alone does not establish redistribution rights.
- Preserve original documents and source-page references so reviewers can compare extracted content with the originals. Keep raw source PDFs private; report-download permission is separate from permission to download an entire source document.
- Assist extraction from text-based PDFs. For scanned pages, difficult equations, diagrams, or complex layouts, allow reviewers to select source regions and manually verify or enter the question, options, answer, and explanation.
- Provide visible upload and processing states, recoverable failures, and clear rejection messages for invalid or password-protected files.
- Treat automated extraction and matching as suggestions, not approval. The MVP does not promise unattended extraction of arbitrary PDFs.
- Support single-correct multiple-choice questions for both exams and numerical-answer questions for JEE Main. Unsupported question formats remain unpublished with an explanation.
- Require verified answer keys for scoring. If a supplied solution does not identify the answer clearly, the reviewer must resolve it before publication.
- Allow reviewers to correct content, divide it into practice sets, assign subject/topic labels, preview the student presentation, and publish or withdraw a set.

### 3. Correct question–solution pairing is the central content guarantee

- Match using the paper/set identity, section, question number, and source evidence—not merely the position of a question or solution in a PDF.
- Detect missing, duplicate, conflicting, or uncertain matches and hold affected sets for review.
- Display each question beside its own approved solution on the results page, even when the question and solution PDFs use different orders or numbering.
- Preserve the order in which the student received the questions. Rearrangement means bringing the correct solution to each question, not moving solutions independently or changing answer-option meaning.
- Require an approved question, options where applicable, answer key, and matched solution before a set becomes available.
- Keep completed attempts tied to the content and marking rules used at the time. Later corrections must not silently rewrite a student's past report.

### 4. A complete JEE Main and BITSAT practice journey

- Provide email-and-password accounts, exam selection, a simple student home, published-set discovery, attempt history, and a clear continue-practice action.
- Label initial sets **Practice**, not official-pattern simulations. Each set states its question count, subjects, question types, time allowance if any, marks, penalties, and numerical-answer acceptance rules before starting.
- Let reviewers publish untimed or timed practice sets with explicit rules. There is no assumed official exam year or silently applied official marking scheme. The supplied Tejas Paper 01 uses its documented 180-minute custom practice profile.
- Provide a brief pre-start device and content check for mathematical rendering, diagrams, answer entry, and saving. Reading instructions or checking the device must not start the clock, and missing essential figures must block starting that paper.
- Present individual interactive questions, not an embedded full-paper PDF. Provide readable question content, answer selection or numerical entry, a question navigator, answered/unanswered/review states, mark for review, clear response, and a submission confirmation.
- Freeze the question order, option order, content, key, and practice rules for each started attempt. Keep keys and unreleased solutions out of material delivered to the active player.
- Preserve saved answers across refreshes and recoverable connection interruptions. Clearly distinguish saved answers, pending changes, and reconnecting states.
- Timed attempts do not gain extra time through refresh or disconnection. The published deadline continues while offline; only responses acknowledged before it count. Late pending drafts remain distinguishable from accepted responses, with a clear explanation. Offline submission is not promised.
- Prevent repeat starts and submissions from creating duplicate attempts or results. Give a recoverable submission receipt so a lost confirmation does not require repeating the paper. Do not expose answer keys or solutions during an active attempt.
- Support comfortable mobile practice while reserving claims of faithful official exam simulation for later verified modes.

### 5. Results that explain the next step

- Show total marks, maximum possible marks, correct, incorrect, skipped, attempt rate, attempted accuracy, and marks lost to penalties.
- Define accuracy clearly: correct answers divided by attempted answers; show a neutral not-applicable state when no questions were attempted.
- Show total time and basic subject/topic summaries when the necessary timing and reviewed labels exist. Missing evidence is reported as unavailable, not replaced with fabricated metrics.
- Provide a question-by-question review with the original question and options, the student's response, the approved answer, marks earned or lost, and the correctly matched explanation, equations, and diagrams.
- Let students filter review by correct, incorrect, skipped, and marked-for-review questions.
- Offer a clearly labeled retry of incorrect or skipped questions, creating a separate practice attempt rather than overwriting the original result. Topic-level practice can use other published, reviewed questions when available.
- Do not display rank predictions, official percentiles, inferred careless-error diagnoses, or claims of readiness without supporting evidence.

### 6. Downloadable results and solutions in one PDF

- Add **Download results & solutions PDF** to completed results and attempt history.
- Include the exam and practice-set identity, attempt date, marking rules, score summary, and every question in the student's original attempt order—including skipped questions.
- Place the student's response, correct answer, awarded marks, and matched solution directly with each question. Include relevant source references and preserve readable equations, diagrams, and multi-page explanations.
- Export the full attempt even when the on-screen review is filtered, so the downloaded record is complete.
- Produce a paginated report that can be saved, printed, and read offline; downloading only a scorecard or the two unpaired source PDFs does not satisfy this requirement.
- Show report-generation progress, an actionable error when generation fails, and a retry option. Only the student and explicitly authorized staff may access a personal report.

### 7. Trust and accessibility from all five specifications

The five supplied volumes remain the combined product brief, with their requirements assigned across the three releases rather than discarded:

- **Product Design and Experience:** the landing page, student home, exam discovery, accessible practice, results, and solution reading begin in the MVP; richer revision and planning follow later.
- **Exam Engines and Simulation:** explicit practice rules, trustworthy scoring, answer recovery, and reliable submission begin in the MVP; year-verified official-pattern modes follow later.
- **PDF Ingestion, Questions and Solutions:** provenance, rights confirmation, human review, correct pairing, and reversible publication are MVP requirements.
- **Analytics, Results and Improvement:** clearly defined personal results begin in the MVP; the larger analytics inventory is introduced only when the necessary evidence exists.
- **Architecture, Security, Scale and QA:** private student records, restricted reviewer access, controlled document access, and visible correction history underpin the product. The 100,000-registered-learner goal is a later capacity objective, not a claim about launch traffic or proven concurrency.

No release may present uncertain scoring, unresolved solution matches, unavailable features, or unsupported official claims as trustworthy student-facing output.

## User flow

### Student

1. Arrive on the landing page, understand the learning loop, and choose JEE Main or BITSAT.
2. Browse real published sets and inspect their stated practice rules.
3. Create an account or sign in, then start an available set.
4. Answer questions, navigate, mark items for review, and see whether answers are saved. Resume an eligible unfinished attempt after returning.
5. Review the submission summary and submit, or reach the stated time limit for a timed set.
6. View the score and question-level results, with every question paired to its approved solution.
7. Download the complete results-and-solutions PDF, retry mistakes, or return to attempt history.

### Owner or reviewer

1. Sign in to the restricted content workspace and select the target exam.
2. Upload the supplied question/solution PDFs and confirm source and content rights.
3. Review extracted content or source crops, resolve numbering and pairing differences, confirm answers, and correct equations or diagrams as needed.
4. Set the practice instructions and marking rules; preview the complete student experience.
5. Publish only fully reviewed sets. Withdraw or correct problematic content with a visible change history and without silently altering previous attempts.

## UI/UX feel

- Premium, calm, and academically credible rather than crowded or gamified around anxiety.
- Adopt the newer master brief's proposed palette in place of the earlier navy/background choices: brand blue **#2563EB**, deep navy **#0B1F3A**, page background **#F5F9FF**, white cards, text **#14243A**, muted text **#52637A**, borders **#D7E2F0**, and focus outline **#1D4ED8**. Preserve meaningful green, amber, red, and purple statuses with labels or icons.
- Use clear typography with a 16px body baseline, generous spacing on a 4/8px rhythm, modest 12–16px card radii, strong hierarchy, restrained motion, and readable mathematical content. Render faithful mathematical text wherever possible; preserve high-resolution diagrams and chemical structures rather than rebuilding them inaccurately.
- Make the landing page visually distinctive through product-focused composition and purposeful explanation, not fabricated dashboards or decorative distractions.
- Keep the practice workspace quieter than the landing page. Prioritize the question, answer controls, save state, navigation, and timer when applicable.
- Make result review encouraging and specific: explain what happened without shaming students or promising admission outcomes.
- Support keyboard operation, visible focus, screen-reader labels, touch-friendly controls, reduced motion, and statuses that do not depend only on color. Provide reviewed text equivalents or descriptions where source-image content requires them.
- Keep mobile layouts genuinely usable and bandwidth-conscious. Avoid autoplay media and heavy visual effects that compete with learning.
- Use clear loading, empty, success, interruption, and recovery states throughout.

## Implementation phases

### Phase 1 — MVP: landing page plus real practice and PDF reports

**The user has directed implementation to proceed without further clarification. Phase 1 is the initial scope; all stated defaults are retained. The workspace is still restricted to Plan mode, so no application construction has begun.**

Included:

- The complete student-facing landing page and JEE Main/BITSAT discovery experience.
- Student accounts, student home, attempt history, and restricted owner/reviewer access, separating draft preparation, approval, and publication actions even when the owner holds multiple roles.
- Owner-supplied PDF intake, assisted extraction, source-crop/manual fallback, content-rights confirmation, pairing review, and controlled publication.
- The supplied Tejas Paper 01 as the first full-paper content candidate, with all 75 questions and matched solutions subject to review—not a token sample that omits difficult questions.
- Single-correct and JEE Main numerical practice with explicit set-level rules, timed or untimed sessions, pre-start checks, answer recovery, review controls, submission receipts, and dependable submission.
- Real scoring, basic personal performance summaries, question-aligned solutions, supplied concept/trap explanations, and retries of mistakes.
- Downloadable, complete results-and-solutions PDFs, with report-download rights confirmed before a paper is offered for that flow.
- Honest availability states for unreviewed content and for BITSAT until suitable papers are supplied.

The JEE content pair is now supplied. Its availability removes the earlier missing-source dependency for JEE, but does not replace rights confirmation and content review. BITSAT content remains outstanding. No substitute, generated, or invented question bank is included. Public release is a separate owner decision; supplying these files does not authorize public redistribution.

### Phase 2 — Broader exam preparation and revision

Future scope, not part of the initial build:

- Official-pattern presets for JEE Main and BITSAT tied to a confirmed year and primary-source rules, including verified BITSAT bonus-question behavior and applicable navigation restrictions.
- WBJEE and COMEDK support, including their verified paper structures, question types, and marking behavior.
- Sectional and full-length simulation, broader question-bank discovery, and more capable batch import/review.
- Bookmarks, personal notes, revision lists, study planning, and meaningful progress across attempts.
- Better weak-topic practice selection and simple evidence-based next actions.

Official modes remain unavailable until their year-specific rules and content have been approved. No exam year is guessed from the date of development.

### Phase 3 — Evidence-based learning intelligence and scale

Future scope, not part of the initial build:

- Extend from basic MVP results toward **at least 40 meaningful analyses within the newer master brief's 64-view catalogue**, reconciling it with the original Volume 4's 55 named metrics rather than dropping that earlier inventory. Categories include score, coverage, timing, strategy, question statistics, cohorts, learning, and reliability. This larger analytics commitment is future scope, not a claim that 40 analyses are included in the first paper journey.
- Use item correctness rates, option distributions, and comparable timing for question-level statistics. Do not present a binary question outcome as an official question percentile.
- Add personalized 7-day and 30-day action plans and longitudinal improvement views based on real attempts.
- Introduce cohort comparisons only with adequate real participation and visible cohort definitions, sample sizes, date ranges, formulas, tie handling, exclusions, and uncertainty.
- Keep all internal ranks, percentiles, and readiness measures explicitly nonofficial. Show insufficient data where evidence is inadequate; calibrated predictions are not unconditional promises.
- Expand content operations, recovery capabilities, privacy controls, and capacity toward the specified 100,000 registered learners without confusing registration capacity with simultaneous exam use.

## Assumptions

1. **Brand and language:** Tejas Exam Platform and an English-first interface are retained. Adopt the newer master brief's blue design tokens. Preserve the supplied English/Hinglish solutions without automatic translation; additional interface languages are later scope.
2. **Initial scope:** Both JEE Main and BITSAT are included as MVP practice categories. Only JEE content has been supplied so far; BITSAT does not show invented papers. WBJEE, COMEDK, and the complete specification feature set remain later scope. The newer brief's preference for four landing-page exam cards is deferred in favor of clearly prioritizing the user's two chosen exams; later exams may be named only as planned.
3. **Exam year and fidelity:** The supplied mock targets 2027 but provides no authority for official 2027 rules. It will use its stated custom practice rules. Future official profiles require primary-source verification independently of the mock's title.
4. **Content source:** The supplied Tejas Paper 01 question and key/solution PDFs are the first real content assets. Permission for the intended audience and downloadable reports must be confirmed before publication. No web-scraped, purchased, generated, or fabricated question bank is assumed.
5. **Upload ownership:** Upload and publication belong to the owner and authorized reviewers, not ordinary student accounts. Multiple paper/set identities can be maintained without relying on filename order.
6. **Human approval:** A reviewer is responsible for confirming extraction, correct answers, solution pairing, and practice rules. Ambiguous content is held back rather than automatically guessed or silently omitted.
7. **PDF interpretation:** “Rearrange questions with solutions” means correctly pairing each question to its solution for on-screen review and export, preserving the student's attempt order. It does not authorize arbitrary rewriting of questions or answer options.
8. **PDF support:** Text-based and scanned documents are accepted, but scanned or complex material may require source-region selection and manual review. AI-generated answers, automated OCR services, and guaranteed one-click imports are not included in the MVP.
9. **Initial upload boundaries:** Each PDF may be up to 50 MB and 300 pages. Larger documents must be split; encrypted or password-protected documents must be supplied unlocked. These are initial product limits, not claims about the storage provider.
10. **Question types:** Single-correct multiple choice and JEE Main numerical responses cover the initial practice formats. Other types are flagged for later support rather than incorrectly rendered or scored.
11. **Accounts and commercial scope:** Use built-in email/password accounts without social login, payment collection, subscriptions, or outbound email integrations. Browsing is public; saved practice is account-based. Automated email verification and email-based password recovery are deferred and must not appear as functioning links.
12. **Privacy:** Collect only information needed for accounts and practice. Keep individual attempts and reports private, provide clear student-facing privacy and consent information, and avoid public profiles, advertising trackers, or unsupported compliance claims.
13. **Private document storage:** Use the platform-provided object storage, subject to account availability and quota. Documents and reports are delivered only through authorized application access; public share links are not part of the MVP. The available service does not provide permanent-delete operations, so withdrawal/removal revokes application access but must not be described as certified physical erasure. Permanent-erasure commitments require a later storage capability change.
14. **Analytics:** The MVP reports only facts supported by actual responses, approved keys, labels, and recorded timing. No population comparisons, diagnostic certainty, rank guarantees, or predicted admissions outcomes are assumed.
15. **Reporting:** Each downloaded report includes all questions and solutions from one completed attempt. Files that students download are outside the application's access controls afterward; the interface should make this clear.
16. **Approval boundary:** Approval covers Phase 1 and the stated defaults. Phases 2 and 3 preserve the broader ambition but are not included in the first build or advertised as already working.
