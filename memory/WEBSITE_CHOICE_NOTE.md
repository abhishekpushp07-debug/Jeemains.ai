JEELIVE.AI — note for the website project: STUDENT CHOICE (the chapter-wise questions, the student's own way)
(copy and paste this into the website project's chat)
=========================================================================================================
Written 26 Nov 2026. THIS REPLACES the Student Choice note written earlier the same day.
What changed: the owner corrected the app side. Student Choice has NO question bank of its own: its questions ARE the
JEE Main chapter-wise questions the website already has. So the first note's "door 1" (a bank of subjects and
chapters) is NOT needed. A chapter in Student Choice is a chapter-wise test of yours, under that test's own id.

STATUS, PLAINLY
- WORKS TODAY, with nothing new from the website (web preview only, not published): Home tile -> Student Choice lists
  your 81 chapter-wise tests (Physics 30, Chemistry 24, Mathematics 27; 3,750 questions on 26 Nov). The student ticks
  chapters (kept on the phone) and takes each ticked chapter's WHOLE test, one after another: the same set, the same
  page, the same 60 minutes, the same result as from your Chapter-wise section. Each row shows the student's own state
  of that test (Start / Resume / Result).
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

4. One thing only the owner can decide (nothing is asked of the website unless he says so)
-----------------------------------------------------------------------------------------
A WHOLE chapter test keeps the website's own time: every chapter-wise test has 60 minutes today, whatever its length
(68 Physics questions in 60 minutes; the owner's ratio above would give 164). The app cannot change a set's time, so
in Student Choice a whole chapter test runs 60 minutes and the app says so ("poore chapter test ka time uske page par
likha hota hai"). The owner's ratio applies to MADE papers (door C). If the owner wants it on whole chapter tests
too, that is a change of rules.minutes on the chapter-wise sets on the website, and it changes the Chapter-wise
section as well.

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
