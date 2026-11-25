JEELIVE.AI — note for the website project: STUDENT CHOICE (a student makes their own paper)
(copy and paste this into the website project's chat)
==========================================================================================
Written 26 Nov 2026.
STATUS, PLAINLY: Student Choice CANNOT WORK FOR A STUDENT YET. Its tile and screens are built in the app, but the
questions a student chooses from and the paper that is made both come from the website, and the website has none of
the three doors of part 2 today (door 1 was called on 26 Nov and answered 404; doors 2 and 3 were not called). Until
they exist the app's Student Choice screen says the question bank is being connected (part 3).
What has been checked (26 Nov, in the web preview only, against a made-up sample bank on our own server): choosing
chapters and questions, the 75 limit, the time and marks arithmetic, the random mock's split, and that "Paper banao"
sends door 3 once per paper with the same request_key on a retry (your server answered 404; the app said so and kept
the student's ticks). The app server's part has automated tests.
What has NOT been checked: anything on a real phone; anything against real doors, including a paper actually being
made and opened; and PICTURE questions (the sample has typed questions only, your chapter questions are pictures). The first answer of your doors on
a test setup is the first true end-to-end run: please tell us before it goes to students.
Students get the tile with the app release that contains this work (not published at the time of writing). After that
release nothing below needs a further app build.

1. What a student does in the app
---------------------------------
Home's fourth tile is now STUDENT CHOICE (the All India tile left; the series keeps its big card). Two ways:
  A. "Sawaal khud chuno": pick a subject -> tick chapters (in one, two or all three subjects) -> for every ticked chapter
     see ITS QUESTIONS WITHOUT OPTIONS and tick the ones wanted -> "Paper banao".
  B. "Random mock": type how many questions (or tap 15 / 30 / 45 / 60 / 75) -> "Random mock banao".
Then the paper's usual page opens (Start, the 60-second get-ready, the player) and after submitting the usual result,
analysis and solutions. In the app a Student Choice paper is an ordinary paper from that moment on.

The owner's rules (the app shows them; the website must apply them):
  - at most 75 questions in a paper;
  - marking: correct +4, wrong -1, left 0;
  - time by subject: every Mathematics question brings 3.2 minutes, Physics 2.4, Chemistry 1.6; the sum is rounded UP
    to a whole minute. So 25 + 25 + 25 questions = 80 + 60 + 40 = 180 minutes; 10 + 10 + 10 = 72; 25 Maths only = 80.

2. The three doors the website must add (all for a SIGNED-IN student, the usual cookie session)
-----------------------------------------------------------------------------------------------
Doors 1 and 2 give the same answer to every student. Our server reads them with the asking student's own session
(only the access_token cookie is sent), keeps the bank for 1 minute and a chapter's questions for 5 minutes, and serves
every student from that copy: however many students browse, the website gets a handful of reads. The phones never call
doors 1 and 2 directly. Door 3 is the student's own request through the usual proxy.
Answers may come in your usual envelope { "data": …, "error": null, "meta": {…} } or plain.

DOOR 1 — the bank:   GET /api/choice/bank?exam=jee-main
  {
    "exam": "JEE Main",
    "max_questions": 75,                 // optional. The app never allows more than 75; a smaller number is obeyed.
    "max_per_subject": null,             // optional. A number here caps every subject (for example 25). Today: no cap.
    "minutes_per_question": { "Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2 },   // optional; these are the defaults
    "subjects": [
      { "name": "Physics",               // exactly Physics, Chemistry, Mathematics (others are not shown)
        "chapters": [
          { "id": "<chapter id>",        // letters, digits, - or _, 6 to 80 characters. Stable: the same chapter keeps its id.
            "number": 1,                 // optional: the chapter's number in the book
            "title": "Units, Dimensions and Errors",   // up to 120 characters
            "count": 68,                 // questions a student can choose from in this chapter (0 = do not list it).
                                         // The app lists at most the first 300 questions of a chapter (door 2).
            "mcq": 64, "integer": 4 }    // optional: how many of each kind
        ] }
    ]
  }
  Chapters in the order they should be listed. Only questions that may go into a custom paper are counted: approved,
  with an answer key (and a solution where you have one). Up to 120 chapters a subject are read.

DOOR 2 — a chapter's questions, WITHOUT options, answers or solutions:
                     GET /api/choice/chapters/<chapter id>/questions?page=1
  {
    "chapter": { "id": "<chapter id>", "title": "Units, Dimensions and Errors", "subject": "Physics" },
    "pages": 1,                          // how many pages there are. At most 6 pages are read and at most the first 300
                                         // questions of a chapter are kept, so 50 questions a page is a good size.
    "items": [
      { "id": "<question id>",           // letters, digits, - or _, 6 to 80 characters. Stable. Sent back to door 3.
        "number": 1,                     // its number in the chapter (the list's order)
        "type": "mcq",                   // "mcq" or "integer"
        "text": "",                      // a typed question: its words, maths in $…$. "" for a picture question.
        "stem": [ { "url": "https://…", "w": 506.5, "h": 47 } ]   // a picture question: ONLY the question's own piece(s)
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
  - 404 for a chapter that does not exist or has no question to choose.

DOOR 3 — make the paper:   POST /api/choice/papers        (the student's own request, usual session and CSRF rules)
  A. chosen questions:   { "exam": "jee-main", "mode": "pick",   "question_ids": ["<id>", …], "request_key": "<uuid>" }
  B. random mock:        { "exam": "jee-main", "mode": "random", "count": 30,                 "request_key": "<uuid>" }
  Answer (200 or 201):   { "set_id": "<the new paper's id>" }
  The app then opens GET /api/my/sets/<set_id> and starts it with POST /api/sets/<set_id>/start, as for any paper.

  What the website does:
  - request_key: the same key = the same paper. A retry (slow network, double tap) must return the SAME set_id, never
    make a second paper.
  - Checks: 1 to 75 questions (mode pick: every id exists in the bank, no id twice; mode random: count from 3, one a
    subject, to 75; the app also never asks for more than three times what the smallest subject has);
    max_per_subject if you set one. A request that fails a check: 422 with a plain sentence in error.message
    (the app shows it to the student as it is).
  - mode "pick": the paper has exactly these questions. Order: Physics, then Chemistry, then Mathematics; inside a
    subject as in a JEE Main paper (single-correct first, then numerical); the app sends the ids already sorted by
    subject, chapter and number, which is a fine order to keep otherwise.
  - mode "random": split the count equally over Physics, Chemistry, Mathematics; one or two left over go to Physics,
    then Chemistry (10 -> 4 + 3 + 3; 11 -> 4 + 4 + 3; 30 -> 10 + 10 + 10; 75 -> 25 + 25 + 25). THE APP SHOWS THIS
    SPLIT AND ITS TIME TO THE STUDENT BEFORE THE PAPER IS MADE, so the website must use exactly this split. Inside a
    subject pick at random across ALL its chapters, about 4 single-correct to 1 numerical (JEE Main: 20 + 5), as far
    as the bank allows.
  - The paper (an ordinary set, owned by this student, not listed in any catalogue, never shown to other students):
      title:      "Student Choice · 30 Q · 26 Nov"   (anything short; it is shown in My Tests and on the result)
      exam:       "JEE Main"
      test_kind:  "choice"        (the app then writes "Student Choice" on its page; another kind works too)
      rules:      { "correct": 4, "wrong": -1, "skipped": 0, "minutes": <by the rule in part 1, rounded up> }
      count, maximum (count x 4), subjects, types: as for every set.
      Each question keeps its own subject (the player's subject tabs and the analysis use it), its pieces, its answer
      key and its solution, exactly as in the chapter-wise tests.
  - From here it is a normal paper: attempt, autosave, deadline, result, analysis, solutions, AI solutions, My Tests
    (in progress / completed), retry.

  SUGGESTIONS FROM THE APP SIDE (these are NOT the owner's rules; settle them with the owner before building):
  - In a random mock, prefer questions this student has not had in an earlier Student Choice paper.
  - A limit on how many papers a student may make in a day (for example 20): 429 with a plain sentence, which the app
    shows as it is.
  - Papers that were made and never started could be removed after a few days; a started one stays like any attempt.
  - A paper belongs to one student, so a leaderboard has nobody to compare with; we would leave it out, as for chapter
    practice.

  OPEN POINT (the owner decides, not settled yet)
  - The app counts a JEE paper as a "full mock" for the student's Dream College meter when it has 68 or more questions
    and 150 or more marks. A 68 to 75 question Student Choice paper would be counted too, even one made of a single
    subject or of hand-picked chapters. If the owner does not want that, the app needs to know the paper's kind when
    it reads the RESULT, so please keep test_kind "choice" on the paper and say whether
    GET /api/attempts/<id>/results can carry test_kind. Nothing is changed in the app about this yet.

3. Until the doors exist
------------------------
- Door 1 answers 404 today (called on 26 Nov): the app's Student Choice screen says the question bank is being
  connected and offers the chapter-wise tests instead. The day doors 1 and 2 answer, the chapters and questions appear
  by themselves.
- Door 3 (not called yet; the app treats 404 and 405 alike): "Paper banao" says the paper cannot be made yet and
  keeps the student's ticks.
- If door 1 answers but has no chapter with questions, the app treats the bank as not connected.

4. What our side already does (for your information)
----------------------------------------------------
- App server: GET /api/choice/bank and GET /api/choice/chapters/<id> (for signed-in students only; they turn your
  answers into the shape the app draws and drop everything else), backend/choice.py.
- The app enforces 75 (and max_per_subject when you send one) while ticking, shows the paper's make-up subject by
  subject with its time, and sends door 3 once per paper (the same request_key on every retry).
- Nothing about a student's choice is stored on our server.
