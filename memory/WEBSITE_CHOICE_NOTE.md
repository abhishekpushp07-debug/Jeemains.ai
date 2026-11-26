JEELIVE.AI — note for the website project: STUDENT CHOICE (the chapter-wise questions, the student's own way)
(copy and paste this into the website project's chat)
=========================================================================================================
Written 26 Nov 2026, part 4 rewritten later the same day (the owner decided: whole chapter tests get the ratio time).
PART 4 CHANGED ONCE MORE ON 26 NOV: the owner added a LONGEST TIME for a whole chapter test: THREE HOURS (180 minutes).
THIS REPLACES the Student Choice notes written earlier the same day.
THE WEBSITE IS ASKED FOR TWO THINGS: (1) three doors (part 2) so that students can choose questions; (2) new minutes on
the chapter-wise sets (part 4). They do not depend on each other.
What changed: the owner corrected the app side. Student Choice has NO question bank of its own: its questions ARE the
JEE Main chapter-wise questions the website already has. So the first note's "door 1" (a bank of subjects and
chapters) is NOT needed. A chapter in Student Choice is a chapter-wise test of yours, under that test's own id.

STATUS, PLAINLY
- WORKS TODAY, with nothing new from the website (web preview only, not published): Home tile -> Student Choice lists
  your 81 chapter-wise tests (Physics 30, Chemistry 24, Mathematics 27; 3,750 questions on 26 Nov). The student ticks
  chapters (kept on the phone) and takes each ticked chapter's WHOLE test, one after another: the same set, the same
  page, the same 60 minutes, the same result as from your Chapter-wise section. Each row shows the student's own state
  of that test (Start / Resume / Result). A search box finds a chapter by name in all three subjects (on the phone).
- DOES NOT WORK YET, and cannot without the website:
    (a) seeing a chapter's questions WITHOUT options and ticking the ones wanted;
    (b) one paper made of the ticked questions (from one or many chapters), 75 at most;
    (c) a random mock of N questions.
  Why: the website hands out a paper's questions only inside a started attempt (GET /attempts/<id>,
  /attempts/<id>/assets/...), and it has no way to make a set out of a list of question ids. Checked on 26 Nov with a
  signed-in student: GET sets/<id>/questions, sets/<id>/preview, my/sets/<id>/questions, choice/bank and
  choice/chapters/<id>/questions all answer 404; in your own pages the only look at questions before an attempt is the
  owner-only preview. The questions, their cut pieces, keys and solutions all exist; only the doors below are missing.
- Until then the app shows (a), (b), (c) under "Jald aa raha hai". The day door A says they are open they appear in
  the app by themselves, within about four minutes, WITHOUT a new app build (for app versions that contain this work).
- NOT checked: anything on a real phone; doors A, B, C (they do not exist: the app's question list and "Paper banao"
  were last walked against a made-up sample on 26 Nov, with typed questions only, never with picture questions).
  The first answer of your doors on a test setup is the first true end-to-end run: please tell us before students.
- THE TIME OF A WHOLE CHAPTER TEST is still 60 minutes for every chapter. The owner wants the ratio there too, three
  hours at most: part 4.

1. What our server reads today (so you know the load, and what must not change without telling us)
--------------------------------------------------------------------------------------------------
GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=<Physics|Chemistry|Mathematics>&q=&page=<n>
with a signed-in student's access_token cookie, every page of the three subjects (8 reads today) plus door A:
at most once every two minutes for each app-server process, however many students are browsing. Phones never make
these reads for Student Choice. Of every row we use only:
  id, test_kind ("chapter"), chapter_subject, chapter_number, title, count, types.mcq, types.integer,
  rules.minutes, rules.correct, rules.wrong, maximum, status ("published"), live_enabled (not false);  and "pages".
Nothing of any student is kept from them. A row that is not a published chapter test of that subject is left out.
The student's own state of a test comes from the same list read by the phone with the student's own session (the
row's "attempt": {id, status}), exactly as your Chapter-wise screen in the app does: only the pages that hold the
ticked chapters.

2. The three doors the website must add (all for a SIGNED-IN student, the usual cookie session)
-----------------------------------------------------------------------------------------------
Answers may come in your usual envelope { "data": ..., "error": null, "meta": {...} } or plain.

DOOR A — the switch:   GET /api/choice/bank?exam=jee-main
  { "pick": true,                      // doors B and C (mode "pick") work: the app opens "Sawaal khud chuno"
    "random": true,                    // door C (mode "random") works: the app opens "Random mock"
    "max_questions": 75,               // optional. The app never allows more than 75; a smaller number is obeyed.
    "max_per_subject": null,           // optional. A number here caps every subject (for example 25). Today: no cap.
    "minutes_per_question": { "Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2 } }   // optional; these are the defaults
  - 404 (today) = both closed. Each of the two can be opened on its own. Set one to false to close it again.
  - Do NOT send "subjects": the chapters are read from your chapter-wise catalogue (part 1). (If you had already built
    the first note's door 1 with a "subjects" list, it still works: its chapters are shown instead, their ids go to
    door B, and both ways count as open unless you send "pick": false / "random": false.)
  - Read by our server only (part 1), never by phones.

DOOR B — a chapter's questions, WITHOUT options, answers or solutions:
                     GET /api/choice/chapters/<id of the chapter-wise test>/questions?page=1
  The id is the set id of the chapter-wise test (the "id" of its catalogue row), for example
  4b4ff9a5-85ba-5325-83cd-60f2994acc57 = "01 Units, Dimensions and Errors". The questions are that test's questions.
  {
    "chapter": { "id": "<the same id>", "title": "Units, Dimensions and Errors", "subject": "Physics" },
    "pages": 2,                          // how many pages there are. At most 6 pages are read and at most the first 300
                                         // questions of a chapter are kept, so 50 questions a page is a good size.
    "items": [
      { "id": "<question id>",           // letters, digits, - or _, 6 to 80 characters. Stable. Sent back to door C.
        "number": 1,                     // its number in the chapter test (the list's order)
        "type": "mcq",                   // "mcq" or "integer"
        "text": "",                      // a typed question: its words, maths in $...$. "" for a picture question.
        "stem": [ { "url": "https://...", "w": 506.5, "h": 47 } ]   // a picture question: ONLY the question's own piece(s)
      }
    ]
  }
  - NEVER send options, the answer, the solution or anything else about the question here; our server would drop it
    anyway, but it must not leave the website.
  - "stem" = the question piece(s) you already cut (part "q"), in order, at most 4 a question, each link at most 900
    characters. w and h in print points, as in the paper's pieces (the picture file holds 2 pixels per point).
    A question needs "text" or at least one stem picture.
  - PICTURE LINKS: https, and they must open on a phone WITHOUT cookies (a signed link is right), for at least
    24 hours after the answer is given. WebP if you have it.
  - The answer is the same for every student: our server reads it with the asking student's own session (only the
    access_token cookie is sent), keeps it for 5 minutes and serves every student from that copy.
  - 404 for a chapter that does not exist or has no question to choose.

DOOR C — make the paper:   POST /api/choice/papers        (the student's own request, usual session and CSRF rules)
  A. chosen questions:   { "exam": "jee-main", "mode": "pick",   "question_ids": ["<id>", ...], "request_key": "<uuid>" }
  B. random mock:        { "exam": "jee-main", "mode": "random", "count": 30,                   "request_key": "<uuid>" }
  Answer (200 or 201):   { "set_id": "<the new paper's id>" }
  The app then opens GET /api/my/sets/<set_id> and starts it with POST /api/sets/<set_id>/start, as for any paper.

  What the website does:
  - request_key: the same key = the same paper. A retry (slow network, double tap) must return the SAME set_id, never
    make a second paper.
  - Checks: 1 to 75 questions (mode pick: every id is a question of a published chapter-wise test, no id twice;
    mode random: count from 3, one a subject, to 75; the app also never asks for more than three times what the
    smallest subject has); max_per_subject if you set one. A request that fails a check: 422 with a plain sentence in
    error.message (the app shows it to the student as it is).
  - mode "pick": the paper has exactly these questions. Order: Physics, then Chemistry, then Mathematics; inside a
    subject as in a JEE Main paper (single-correct first, then numerical); the app sends the ids already sorted by
    subject, chapter and number, which is a fine order to keep otherwise.
  - mode "random": split the count equally over Physics, Chemistry, Mathematics; one or two left over go to Physics,
    then Chemistry (10 -> 4 + 3 + 3; 11 -> 4 + 4 + 3; 30 -> 10 + 10 + 10; 75 -> 25 + 25 + 25). THE APP SHOWS THIS
    SPLIT AND ITS TIME TO THE STUDENT BEFORE THE PAPER IS MADE, so the website must use exactly this split. Inside a
    subject pick at random across ALL its chapter-wise chapters, about 4 single-correct to 1 numerical (JEE Main:
    20 + 5), as far as the questions allow.
  - The paper (an ordinary set, owned by this student, not listed in any catalogue, never shown to other students):
      title:      "Student Choice · 30 Q · 26 Nov"   (anything short; it is shown in My Tests and on the result)
      exam:       "JEE Main"
      test_kind:  "choice"        REQUIRED, exactly this word (see part 3: the app decides by it)
      rules:      { "correct": 4, "wrong": -1, "skipped": 0, "minutes": <by the owner's rule below, rounded up> }
      count, maximum (count x 4), subjects, types: as for every set.
      Each question keeps its own subject (the player's subject tabs and the analysis use it), its pieces, its answer
      key and its solution, exactly as in the chapter-wise tests.
  - From here it is a normal paper: attempt, autosave, deadline, result, analysis, solutions, AI solutions, My Tests
    (in progress / completed), retry.

  THE OWNER'S RULES for a made paper (the app shows them to the student; the website must apply them):
  - at most 75 questions;
  - marking: correct +4, wrong -1, left 0;
  - TIME BY SUBJECT (the owner said it again on 26 Nov): 25 Mathematics questions = 80 minutes, 25 Physics = 60,
    25 Chemistry = 40. So every Mathematics question brings 3.2 minutes, Physics 2.4, Chemistry 1.6; the sum is
    rounded UP to a whole minute. 25 + 25 + 25 = 180 minutes; 10 + 10 + 10 = 72; 25 Maths only = 80; 5 Physics = 12.

  SUGGESTIONS FROM THE APP SIDE (these are NOT the owner's rules; settle them with the owner before building):
  - In a random mock, prefer questions this student has not had in an earlier Student Choice paper.
  - A limit on how many papers a student may make in a day (for example 20): 429 with a plain sentence, which the app
    shows as it is.
  - Papers that were made and never started could be removed after a few days; a started one stays like any attempt.
  - A paper belongs to one student, so a leaderboard has nobody to compare with; we would leave it out, as for chapter
    practice.

3. Two things the app now decides by a paper's test_kind
--------------------------------------------------------
- DREAM COLLEGE METER (the owner's decision, 26 Nov): a chapter test and a Student Choice paper NEVER count as a full
  mock, however long (12 of your chapter tests have 68 questions or more; before today the app counted those). The
  app reads test_kind from GET /api/attempts/<id>/results ("chapter" is there today; "choice" must be there for a
  made paper). So a made paper MUST carry test_kind "choice" on the set AND on its result.
- PLEASE ALSO put test_kind on every item of GET /api/my/tests (today the items have none). A phone that signs in for
  the first time reads that list to find the student's full mocks; without test_kind it has to open the paper's page
  (GET /api/my/sets/<set_id>) for every long paper in the list, up to 12 extra reads, once.

4. THE OWNER'S DECISION (26 Nov 2026): a WHOLE chapter test gets its time by the same ratio, THREE HOURS AT MOST — a
   change on the website
---------------------------------------------------------------------------------------------------------------------
The owner asked for it in the app: "Make whole chapter tests follow the 80/60/40 time ratio". Told what that gives
(below), he added the same day: "a longest time of three hours". The app cannot do it:
an attempt's deadline is the website's, from the set's rules.minutes. So this is asked of the website. NOT DONE YET:
on 26 Nov every chapter-wise test still has 60 minutes.

WHAT TO CHANGE
- For every published JEE Main chapter-wise set (test_kind "chapter"):
      rules.minutes = (the set's count) x (minutes a question of its chapter_subject), rounded UP to a whole minute,
                      and NEVER MORE THAN 180 (three hours)
      Physics 2.4    Chemistry 1.6    Mathematics 3.2        (25 Maths = 80 min, 25 Physics = 60, 25 Chemistry = 40)
- Keep it true: when a chapter's question count changes, its minutes change with it.
- A new attempt gets the new time. An attempt that is already running keeps the deadline it has.
- A whole number of minutes, please (the app's pages show rules.minutes as it is).

WHAT IT GIVES, chapter by chapter (counts as on 26 Nov 2026; today -> by the rule; 7 tests are held at 180)
  Physics (2.4 minutes a question)
     1  Units, Dimensions and Errors                                68 questions    60 -> 164 min
     2  Kinematics                                                  66 questions    60 -> 159 min
     3  Laws of Motion                                              46 questions    60 -> 111 min
     4  Work, Energy and Power                                      42 questions    60 -> 101 min
     5  Centre of Mass, Momentum and Collisions                     17 questions    60 ->  41 min
     6  Rotational Motion                                           60 questions    60 -> 144 min
     7  Gravitation                                                 40 questions    60 ->  96 min
     8  Mechanical Properties of Solids                             29 questions    60 ->  70 min
     9  Fluids                                                      31 questions    60 ->  75 min
    10  Surface Tension                                             22 questions    60 ->  53 min
    11  Thermal Properties of Matter                                16 questions    60 ->  39 min
    12  Thermodynamics                                              52 questions    60 -> 125 min
    13  Kinetic Theory of Gases                                     41 questions    60 ->  99 min
    14  Oscillations                                                27 questions    60 ->  65 min
    15  Waves and Sound                                             30 questions    60 ->  72 min
    16  Electrostatics                                              76 questions    60 -> 180 min   (the ratio alone: 183)
    17  Capacitors                                                  30 questions    60 ->  72 min
    18  Current Electricity                                         55 questions    60 -> 132 min
    19  Magnetic Effects of Current                                 62 questions    60 -> 149 min
    20  Magnetism and Matter                                         7 questions    60 ->  17 min
    21  Electromagnetic Induction                                   34 questions    60 ->  82 min
    22  Alternating Current                                         35 questions    60 ->  84 min
    23  Electromagnetic Waves                                       41 questions    60 ->  99 min
    24  Ray Optics and Optical Instruments                          74 questions    60 -> 178 min
    25  Wave Optics                                                 49 questions    60 -> 118 min
    26  Dual Nature of Matter and Radiation                         45 questions    60 -> 108 min
    27  Atoms                                                       35 questions    60 ->  84 min
    28  Nuclei                                                      30 questions    60 ->  72 min
    29  Semiconductors and Logic Gates                              56 questions    60 -> 135 min
    30  Experimental Skills                                         34 questions    60 ->  82 min
  Chemistry (1.6 minutes a question)
     1  Mole Concept and Stoichiometry                              68 questions    60 -> 109 min
     2  Atomic Structure                                            52 questions    60 ->  84 min
     3  Classification of Elements and Periodicity                  45 questions    60 ->  72 min
     4  Chemical Bonding and Molecular Structure                    65 questions    60 -> 104 min
     5  Thermodynamics and Thermochemistry                          59 questions    60 ->  95 min
     6  Chemical Equilibrium                                        31 questions    60 ->  50 min
     7  Ionic Equilibrium                                           28 questions    60 ->  45 min
     8  Redox Reactions                                             16 questions    60 ->  26 min
     9  Solutions                                                   47 questions    60 ->  76 min
    10  Electrochemistry                                            56 questions    60 ->  90 min
    11  Chemical Kinetics                                           56 questions    60 ->  90 min
    12  p-Block Elements                                            54 questions    60 ->  87 min
    13  d- and f-Block Elements                                     72 questions    60 -> 116 min
    14  Coordination Compounds                                      88 questions    60 -> 141 min
    15  Purification and Characterisation of Organic Compounds      57 questions    60 ->  92 min
    16  General Organic Chemistry                                  103 questions    60 -> 165 min
    17  Hydrocarbons                                                58 questions    60 ->  93 min
    18  Haloalkanes and Haloarenes                                  46 questions    60 ->  74 min
    19  Alcohols, Phenols and Ethers                                32 questions    60 ->  52 min
    20  Aldehydes, Ketones and Carboxylic Acids                     60 questions    60 ->  96 min
    21  Amines and Diazonium Salts                                  57 questions    60 ->  92 min
    22  Biomolecules                                                56 questions    60 ->  90 min
    23  Principles Related to Practical Chemistry                   42 questions    60 ->  68 min
    24  Miscellaneous (beyond the current syllabus)                  2 questions    60 ->   4 min
  Mathematics (3.2 minutes a question)
     1  Sets and Relations                                          38 questions    60 -> 122 min
     2  Functions                                                   54 questions    60 -> 173 min
     3  Basic Algebra (Inequalities, Modulus, Logarithms)           13 questions    60 ->  42 min
     4  Trigonometric Ratios, Identities and Equations              40 questions    60 -> 128 min
     5  Complex Numbers                                             48 questions    60 -> 154 min
     6  Quadratic Equations                                         49 questions    60 -> 157 min
     7  Permutations and Combinations                               53 questions    60 -> 170 min
     8  Binomial Theorem                                            50 questions    60 -> 160 min
     9  Sequences and Series                                        75 questions    60 -> 180 min   (the ratio alone: 240)
    10  Straight Lines                                              50 questions    60 -> 160 min
    11  Circles                                                     44 questions    60 -> 141 min
    12  Parabola                                                    23 questions    60 ->  74 min
    13  Ellipse                                                     36 questions    60 -> 116 min
    14  Hyperbola                                                   28 questions    60 ->  90 min
    15  Limits                                                      29 questions    60 ->  93 min
    16  Statistics                                                  29 questions    60 ->  93 min
    17  Probability                                                 51 questions    60 -> 164 min
    18  Matrices and Determinants                                   86 questions    60 -> 180 min   (the ratio alone: 276)
    19  Inverse Trigonometric Functions                             24 questions    60 ->  77 min
    20  Continuity and Differentiability                            41 questions    60 -> 132 min
    21  Application of Derivatives                                  37 questions    60 -> 119 min
    22  Indefinite Integration                                      15 questions    60 ->  48 min
    23  Definite Integration                                        73 questions    60 -> 180 min   (the ratio alone: 234)
    24  Area under Curves                                           45 questions    60 -> 144 min
    25  Differential Equations                                      70 questions    60 -> 180 min   (the ratio alone: 224)
    26  Vector Algebra                                              67 questions    60 -> 180 min   (the ratio alone: 215)
    27  Three-Dimensional Geometry                                  82 questions    60 -> 180 min   (the ratio alone: 263)

WHAT THE RULE DOES (the owner was told what the ratio alone gives on 26 Nov, and answered the same day with the
longest time of three hours)
- 7 tests are HELD AT 3 HOURS; the ratio alone would give them more:
  Matrices and Determinants (4 h 36 min by the ratio alone); Three-Dimensional Geometry (4 h 23 min); Sequences and Series (4 h 00 min); Definite Integration (3 h 54 min); Differential Equations (3 h 44 min); Vector Algebra (3 h 35 min); Electrostatics (3 h 03 min).
- So NO chapter test is longer than a full mock (180 minutes): the student's session, the autosave and the attempt's
  picture links (GET /attempts/<id>/assets/links) need to last no longer than they already do for a full mock (plus
  the get-ready minute).
- 11 tests become SHORTER than today's 60 minutes:
  Miscellaneous (beyond the current syllabus) 4 min; Magnetism and Matter 17 min; Redox Reactions 26 min; Thermal Properties of Matter 39 min; Centre of Mass, Momentum and Collisions 41 min; Basic Algebra (Inequalities, Modulus, Logarithms) 42 min; Ionic Equilibrium 45 min; Indefinite Integration 48 min; Chemical Equilibrium 50 min; Alcohols, Phenols and Ethers 52 min; Surface Tension 53 min.
  The owner has not asked for a shortest time. If he does, it is again only rules.minutes on your side.
- THE LONGEST TIME IS FOR WHOLE CHAPTER TESTS ONLY. A paper the student makes (part 2) keeps the plain ratio: 75
  Mathematics questions get 240 minutes, and the app shows the student that time before the paper exists. Do NOT cut
  a made paper unless the owner says so (it is an open question to him); the app would have to change with it.
- It is the same set as in your Chapter-wise section, so that section (website and app) shows the new time too.

WHAT THE APP DOES WITH IT (nothing else is needed from you)
- Every app version, also the ones students have today: the paper's page shows rules.minutes of the set when it is
  opened, the Chapter-wise list shows the list's minutes, and the player runs on the attempt's deadline.
- The Student Choice lines below are in the app version on the preview (not published yet):
- Student Choice's list of chapter tests shows each test's minutes from your chapter-wise list (part 1), a few minutes
  behind at most. Minutes that are not a whole number are shown rounded DOWN (163.2 -> 163), never more than you give.
- Student Choice's first screen says "Poore chapter test ka time uske page par likha hota hai (abhi 1 hr)" today.
  The day every chapter test has its time by the rule above (the ratio, 180 at most; a minute's rounding apart at
  most) the sentence changes by itself to
  "Poore chapter test ko bhi isi hisaab se time milta hai: jitne sawaal, utna time (zyada se zyada 3 hr)."
  (With the ratio alone, without the 180, the sentence does NOT change: the rule is the two together.)
- Checked on 26 Nov on the web preview with your list answered in the browser: with the rule's times (81 tests, the
  longest 180 min, the shortest 4) the sentence changed; with the ratio alone (the longest 276) it did not. NOT
  checked with the real website (nothing is changed there yet).

5. What our side does (for your information)
--------------------------------------------
- App server (backend/choice.py), for signed-in students only, nothing written anywhere:
    GET /api/choice/bank            the chapters (part 1), the owner's rules, and "pick" / "random" from door A
    GET /api/choice/chapters/<id>   door B's questions in the shape the app draws; everything else is dropped
- The app: Home tile STUDENT CHOICE -> "Chapters chuno" (tick chapters in one, two or all three subjects) ->
    today:          "Aapke chapter tests": the ticked chapters' tests with Start / Resume / Result;
    "pick" open:    "Sawaal chuno": each ticked chapter's questions without options -> "Paper banao" (door C);
    "random" open:  "Random mock": a number of questions -> door C.
  It enforces 75 (and max_per_subject when you send one) while ticking, shows the paper's make-up subject by subject
  with its time, and sends door C once per paper (the same request_key on every retry).
- Nothing about a student's choice is stored on our server (the ticked chapters stay on the phone).
