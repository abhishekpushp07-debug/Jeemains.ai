# Super Admin PDF Engine 2.0: the question and each option, cut cleanly from the book

Super Admin's PDF reader learns to cut every question into five clean pieces: the question, and options A, B, C and D, each exactly as printed in the book.
Students then see only the question in the question area, and the real content of each option on its own button. No AI reads the PDF, at upload or later.

## Who it's for

- **Owner (super admin):** uploads PYQ, All India Series, chapter-wise and plain mock PDFs and gets mocks at the new level without typing anything.
- **Reviewer:** fixes the few questions the engine refuses to guess.
- **Students:** read each option right where they tap it, which matters most on a phone.
- **App team:** gets a short guide so the app can show the same look.

## Core features and experience

### 1. What students see

| Part of the screen | Today | After |
| --- | --- | --- |
| Question area | One picture holding the question and all four options | Only the question, with its own diagram if it has one |
| Option buttons | "A", "B", "C", "D" with the words "as shown above" | Each button shows what that option says, exactly as printed |
| Hint "Read options A–D in the picture above" | Shown | Gone |
| Result and Solutions screens | Whole picture, then "your answer B, correct C" in words | Same split; the correct option and the student's pick are marked on the option itself |
| Numerical questions | Question picture and a number box | No change |

### 2. How the engine cuts a question

1. It finds where each question starts and ends, as it does today.
2. Inside the question it finds the option labels: the last full set of four, such as (A) (B) (C) (D) or (1) (2) (3) (4). Labels used for statements inside the question are not mistaken for options.
3. From where the labels sit, it works out the arrangement: one option per line, two per line, or all four in one line.
4. Each option gets its own box, from its label to the next label, with whatever is printed there: text, formula, diagram or graph. The printed label is left out of the picture, because the button already shows the letter.
5. Everything above the first option is the question picture, diagrams included.
6. Every piece is trimmed to the printed ink with the same small margin, and all five pieces of a question use the same zoom, so the text is the same size in the question and in every option.

This uses only the positions of the text and the white space in the PDF. The spaced format with bracketed labels is what makes a clean cut possible every time.

### 3. Checks before a cut is trusted

A question is accepted only when all of these hold:

- Four labels were found, in order, lined up as rows or columns.
- Every option has something printed in it.
- Nothing is lost: every printed mark of the question lies in the question picture or in exactly one option picture.
- Nothing is shared: no two pieces touch or overlap, and the gap between them is blank.
- All options sit on the same page as each other.

If any check fails, the engine does not guess. The question is marked with the reason in plain words, for example "Something is printed between option B and option C that belongs to neither".

### 4. Held questions and the fix tool

- A mock with even one such question stays a Draft and cannot go Live. This is the rule chosen by the owner.
- The Fix screen shows one card per held question: the piece of the page with five boxes drawn on it (Question, A, B, C, D), and beside it a preview of exactly what the student will see.
- Three ways to fix a question:
  1. Move or resize a box, then save. The checks run again by themselves.
  2. Type an option's text (this exists today and stays).
  3. Choose "Show this question as one whole picture", which gives that one question the old look by the owner's own decision.
- Answer type, answer buttons and the correct answer are fixed on the same card, as today.

### 5. What the owner sees after an upload

- A summary line on every mock: "75 questions · 73 cut cleanly · 2 need your eye".
- A proof view: every question of the mock as the student will see it, question and four options, so a whole paper can be checked by eye in a few minutes.
- "Try as student" opens the mock in the real test screen, as today.

### 6. One engine for every kind of upload

- PYQ, All India Series, chapter-wise tests and plain mocks all go through the same "Upload PDF" button. The mock type the PDF is uploaded into decides what it becomes.
- Answer key and solutions are read from the end of each chapter, from the end of the mock, or from separate PDFs, as today.
- Days, schedules, replacing an older mock and the Library work as today.

### 7. Mocks already on the site

- JEE Main PYQ stay exactly as they are, in the old look.
- Other PDF mocks in the old look: Super Admin shows a list of any that are still Live, with a "Move to Library" button. Nothing is moved without that button. Students keep their scores.
- An old mock gets the new look only by uploading its PDF again in the spaced format, with Replace.

### 8. Mobile app

- Nothing breaks in the app. App students keep seeing the old look until the app team adopts the new one.
- A short guide for the app team is written with the feature.

### 9. PDF format guide

One page inside the upload screen: how to make a PDF the engine reads correctly the first time (label style, spacing, the three arrangements, where diagrams go, headings for chapters, answer key and solutions).

### 10. Quality bar

The owner's instruction, recorded as given: the most elegant, the most beautiful, the most aesthetic and, more importantly, the most capable and the most powerful platform. For this work it is taken to mean:

- **No guessing.** A question either passes every check or is held with its reason. The proof view is the owner's final check by eye.
- **Nothing clipped.** Cuts are placed only in blank space, so fractions, integrals, matrices, superscripts and diagrams are whole in every piece.
- **No typing for a well-made book.** A PDF in the spaced, bracketed format goes from upload to a checked Draft with no manual work on its cleanly cut questions.
- **One upload, any size.** A PDF can hold one mock or a whole book of chapters, up to the current 100 MB limit. It is read in the background and each mock arrives by itself.
- **Fast to fix.** A held question is fixed on one card, without leaving the screen.
- **Honest counts.** The summary line counts held questions exactly. Nothing is hidden to make a mock look ready.
- **Student screens at the Analysis 2.0 standard.** The same fonts, spacing, motion and care, on phone and desktop, in light and dark theme.
- **Accepted when** the five sample questions from the owner's book come out cleanly cut with no manual fix, or the exact reason they do not is reported.

## User flow

**Owner**
1. Super Admin › Master › exam › mock type (PYQ, All India Series, chapter-wise or mocks) › Upload PDF. Same dialog as today.
2. The PDF is read in the background. Each mock arrives as a Draft with its summary line.
3. A mock with held questions is opened in Fix. Each card is fixed by moving a box, typing an option, or choosing the whole-picture look. It is rechecked by itself.
4. The proof view is scanned once. "Try as student" shows the real screen.
5. The mock is made Live, or given its series day, as today.

**Student**
1. Opens the mock. The question area shows only the question.
2. Reads the four options on their buttons and taps one.
3. After submitting, sees the same question and options with the correct one and their own pick marked.

## UI/UX feel

- Each option is a wide, tappable card: a letter chip on the left, the option's picture beside it.
- The selected option gets the blood-red outline and a tick. On result screens, correct and wrong are shown with an icon as well as colour.
- Phone (360 to 390 px): one option per row, full width. Desktop: two per row when all four options are short, otherwise one per row.
- Text is the same size in the question and in all four options. No stretched or blurry pictures.
- Book pictures stay on white "paper" cards in both light and dark theme.
- All pictures of a paper, option pictures included, start loading on the get-ready screen before the test begins, as question pictures do today, so nothing pops in during the test.
- Super Admin keeps its current look. The fix tool shows the boxes directly on the page picture, with the student preview next to it.

## Implementation phases

**Phase 1 (built now): everything in "Core features and experience" above.**
- The cutter, its checks and the hold rule.
- Fix tool with movable boxes and live preview, summary line, proof view.
- New look on the test screen, the result screen and the Solutions screen.
- All four kinds of upload.
- List of old-look mocks with "Move to Library".
- App guide and PDF format guide.
- Tuned on the first five questions of the owner's book, with their answer key and solutions.
- Preview only. It goes to jeelive.ai when the owner says "deploy".

**Phase 2 (separate approval):**
- Harder layouts cut automatically: a diagram beside the options, an option that runs onto the next page, four graphs drawn inside one picture, two-column pages.
- Scanned (photo) PDFs, with text found on the site's own server, still no AI credits.
- Options that are plain words shown as real text (sharper on phones, lighter to load).
- A "read again" button for Drafts uploaded before this engine.
- Solution pictures trimmed and cleaned the same way.
- JEE Main PYQ moved to the new look.

**Phase 3 (separate approval):**
- Question bank: every cut question saved with its chapter, so a new mock can be assembled from chosen chapters without a new PDF.
- Owner paper report with option pictures: which wrong option was picked most on each question.
- Faster checking of big books: approve a whole proof sheet from the keyboard.

**After Phase 1 is accepted:** the owner is reminded of the three parked student features (Galti Notebook, Subject Rank, Seekh Reminder). Their notes and decisions are saved in `parked_student_features.md` next to this plan and are moved into the project memory as the first step of the build.

## Assumptions

1. The uploaded book has not been opened yet. Planning mode offers only a reader that sends the whole book through an AI model, which the owner ruled out. The first step of the build opens only the first five questions, their answer key and their solutions with the site's own page reader (no AI). If they show a layout this plan did not expect, that is reported before the build goes further.
2. The book is not uploaded or run as a whole by the builder. The owner uploads it in Super Admin once the engine is ready. Reading a PDF on the site uses no AI and no AI credits.
3. "Question screen" and "option screen" are read as the two areas of the same test screen, not two separate pages.
4. Options are shown as pictures cut from the book, not retyped as text, so formulas and diagrams stay exact.
5. Label styles accepted: (A)–(D), A. or A), (a)–(d), (1)–(4), 1). Four options are expected; a question with a different count is held.
6. Phase 1 cuts three arrangements automatically: one per line, two per line, four in one line. Anything else is held and fixed with the boxes.
7. The third fix, "Show this question as one whole picture", is included as an owner's choice per question. It can be removed if the old look should never be possible in a new mock.
8. Because held papers never go Live by themselves, an All India Series paper with a held question does not open on its day. Series PDFs need to be uploaded early enough to fix.
9. All four kinds of upload already use the same "Upload PDF" button and the same reader, so one engine covers them. The code also holds older upload routes (a two-PDF importer, an Excel importer, an AI-based automatic importer and a fixed-format chapter-book importer). Whether any screen still reaches them was not checked while planning. They are not changed by this work.
10. The owner's answer about existing mocks is read as: JEE Main PYQ stay as they are; the other old mocks have already been removed by the owner; any left over go to the Library. The move is a button with a list, not automatic, because the builder cannot see or change the live site.
11. Mocks that are Live or Draft before this change are not read again in Phase 1.
12. The Solutions PDF and the Analysis report keep printing the whole question as in the book.
13. The printed question number stays inside the question picture.
14. Only searchable PDFs are cut automatically. A scanned page is held and its boxes are drawn by hand. The site's code already has two AI options that run only on the owner's explicit approval: AI reading of scanned pages, and AI explanations for questions that have only an answer key. Their screens were not opened while planning. Both are left as they are and are not removed; this work adds no AI call anywhere.
15. Answer key and solution reading is changed only as far as the five-question check shows is needed.
16. The fix tool is open to the owner and the reviewer, like the Fix screen today.
17. Super Admin text stays in English. Any new student-facing text is in Roman Hinglish, like the Analysis screens.
18. The app shows the old look until the app team changes it.
19. Galti Notebook, Subject Rank and Seekh Reminder are parked with no code written. Work on them resumes only after the owner is reminded and says so.
20. This plan replaces the Analysis 2.0 plan in this file. A full copy of that plan is saved next to it as `analysis2_plan.md`, and its pending Phase 2 and Phase 3 lists are also listed in `parked_student_features.md`.
21. The result screen and the Solutions screen were not opened while planning. Their "Today" row in the table is inferred from how the test screen works, and is confirmed at the start of the build.
22. The technical notes saved for the three parked features were not re-checked against the code in this planning session. They are labelled as unchecked in `parked_student_features.md`.
23. "Most powerful" and "perfect" are taken as the quality bar in section 10. They are not a promise that every possible PDF layout is cut automatically: in Phase 1 a layout outside the three arrangements is held and fixed by hand, and the harder layouts are Phase 2.
24. The new option cards and the fix tool follow the existing JEELIVE look. No new visual style is introduced.
