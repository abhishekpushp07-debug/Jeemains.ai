JEELIVE.AI — note for the website project: MATCHED (JEE Main questions that matched ours)
(copy and paste this into the website project's chat)
==========================================================================================
Written 26 Nov 2026.
STATUS, PLAINLY: the app side and the app's own server are built.
What has been checked (26 Nov, in the web preview only, with made-up sample shifts and one ordinary website paper
standing in for a Matched paper): the public pages, the sign-up sheet and the way back to the shift after sign-in, the
button opening the paper's page, and the JEE Main question shown under ours in the solutions. The app server's part has
automated tests, including the copy of the website's shifts, run against a stand-in for the website.
What has NOT been checked: anything on a real phone; the JEE Main question under ours WHILE a paper is being solved
(that needs a started attempt); and one real shift going all the way from the website to a phone, because the two
doors and the real paper of part 2 do not exist yet. The first shift
you publish on a test setup is the first true end-to-end run: please tell us before it goes to students.
Students get all of this with the app release that contains this work (not published at the time of writing). After
that release nothing below needs a further app build: the day the website has the three things in part 2, Matched
fills up by itself.

1. What a student sees in the app
---------------------------------
- Home: from the day after the All India series ends (the website's own schedule: last_date of series/all-india-jee,
  today 27 Jan 2027, so from 28 Jan 2027) the big All India card gives its place to the MATCHED card (yellow and orange,
  fireworks, golden cup): "JEE Mains questions matched with ours", how many matched, the latest shift. Automatic: no app
  update and no publish on that day. The super admin can also switch the card on or off at any time (part 2, "card").
- The sign-in screen shows a Matched bar from the same day. Matched is open to people WITHOUT an account.
- Matched page: months -> days -> shifts ("Shift 1 · 18 of 75 matched").
- A shift's page, open to everyone: the count ("18 of 75 questions matched with ours"), then one card per matched question:
  the JEE Main question, and under it OUR question(s) it matched (where ours was asked: "AITS Day 12 · Q 7"; how close:
  "Same concept"), without options, with tabs Question | Solution.
- The button "Attempt all matched" on the shift's card:
    - no account: a sheet asks to sign up (free). After sign-up the student is back on the shift.
    - signed in: the shift's REAL PAPER on the website opens (its usual page, Start, the 60-second get-ready, the player,
      and after submitting the usual result, analysis and solutions). Nothing about this paper is special in the app,
      except one thing: under each of our questions the player and the solutions show the JEE Main question it matched
      (without options while solving; with its answer and solution afterwards).
    - a shift without a paper says "Is shift ke matched sawaalon ka paper jald yahan khulega" and has no button.

2. What the website must have (three things)
--------------------------------------------
2a. The super admin page ("Matched")
  For every JEE Main shift the super admin enters (or imports) the questions of that shift that matched ours:
    - the JEE Main question: its number in the JEE paper, subject, chapter, the question, its answer and its solution;
    - the question(s) of ours it matched (1 to 4), picked from our own bank, each with: where it was asked ("source"),
      how close the match is ("tag"), its answer and its solution;
    - "asked": how many questions the shift's paper had (75);
    - Publish / take back for the shift; and the switch for Home's card: auto / on / off.
  Then one button: "Make the paper". It makes ONE ordinary paper of all our matched questions of that shift (2b) and
  writes its id into the shift.

2b. The real paper of a shift (an ordinary paper, like every mock)
  - Answers GET /api/my/sets/<paper id> for every signed-in student and starts with POST /api/sets/<paper id>/start,
    exactly like any other paper: attempts, autosave, deadline, result, analysis, solutions, My Tests. Nothing new.
  - title: for example "Matched · JEE Main 25 Jan 2027 · Shift 1"; exam "JEE Main".
  - rules: correct +4, wrong -1, skipped 0. minutes: the owner's rule, by subject: every Mathematics question 3.2
    minutes, Physics 2.4, Chemistry 1.6, the sum rounded up to a whole minute (25 + 25 + 25 questions = 180 minutes).
  - test_kind: "matched" if a new kind is easy for you (the app then writes "Matched paper" on its page); any existing
    kind also works (the page then says "Full mock").
  - It need not be listed in any catalogue: the app opens it by its id.
  - IMPORTANT: the id every question has inside this paper (questions[].id in GET /api/attempts/<id>) must be written
    next to that question in the shift (question_id, below). That is how the app finds the JEE Main question to show
    under it. It is also what switches the button on: a shift whose paper_id is set but where NONE of "ours" carries a
    question_id is treated as a shift without a paper (no button). The button's line says how many of ours are in the
    paper = how many different question_id the shift has.

2c. Two public read doors (no sign-in: the Matched pages are public). Our server reads them, not the phones:
  every 2 minutes it asks the first; it asks the second only for a shift that is new or whose updated_at changed.

      GET /api/matched
      {
        "card": "auto",                                    // optional: "auto" | "on" | "off" = the super admin's switch for Home's card
        "shifts": [ { "id": "2027-01-25-s1", "updated_at": 1800000000 } ]     // ONLY published shifts
      }

      GET /api/matched/2027-01-25-s1                        // 404 when it is not published
      {
        "id": "2027-01-25-s1",          // the exam day in India + "-s" + the shift number (1 to 9)
        "asked": 75,                    // optional (1 to 300); without it, or if it is smaller than the number of items, the app says "18 matched"
        "updated_at": 1800000000,       // unix seconds of the last change; CHANGE IT ON EVERY EDIT: our copy is refreshed when it changes
                                        // (a shift sent without updated_at is read again every 10 minutes instead)
        "paper_id": "<id of the real paper of 2b>",        // optional; no button until it is there AND at least one of "ours" has its question_id
        "items": [                      // ONLY the questions that matched; the app counts them
          {
            "n": 12,                    // the question's number in the JEE paper (optional)
            "subject": "Physics",       // exactly Physics, Chemistry or Mathematics
            "chapter": "Kinematics",    // optional
            "jee":  { <question> },
            "ours": [ { <question>, "source": "AITS Day 12 · Q 7", "tag": "Same concept", "question_id": "<its id inside the paper>" } ]
          }
        ]
      }

  <question> (the JEE one and each of ours):
      "text":            the question's words, maths in $…$ (TeX). Up to 6000 characters.
      "options":         list of option texts in order (shown as A, B, C, D). Up to 6, each up to 1500 characters.
                         Every option needs words; if one is empty, none is shown.
      "images":          list of { "url": "https://…", "w": 800, "h": 300 } (or just the link). Up to 6.
      "correct":         the right option: its place from 1 (2) or its letter ("B").
      "answer":          the right answer in words, for a question without option texts ("8", or "Option B").
      "solution":        the worked solution, maths in $…$. Up to 6000 characters.
      "solution_images": pictures of the solution, same shape as "images". Up to 6.
    A question needs "text" or at least one picture. An item needs the JEE question and at least one of ours.
    Both the JEE question and ours should come with their answer ("correct" or "answer") and their solution.

  PICTURES IN A SHIFT: plain https links that open WITHOUT sign-in and DO NOT EXPIRE (not the signed links of a paper:
  our server keeps its copy of a shift until the shift changes). A question of ours that exists only as cut pictures:
  give its question picture(s) in "images", its answer in "answer" and its solution picture(s) in "solution_images".

  The answers may come in your usual envelope { "data": …, "error": null, "meta": {…} } or plain.
  Limits read by the app: 200 shifts, 150 items a shift, 4 of ours per item.

3. Rules to keep
----------------
- Never delete a shift that was published: take it back (it then leaves the list of the first door; our server hides
  its copy within 2 minutes). Publishing it again brings it back.
- A change reaches students within about 3 minutes (2 minutes for our server's copy + 1 minute it keeps each answer).
  Our server reads at most 20 new or changed shifts in one 2-minute pass, so a first load of many shifts arrives
  20 at a time.
- Anything that does not fit the shapes above is left out by our server and not counted; it cannot break the app.
- Until the two doors exist they answer 404 and nothing changes in the app (today the Matched page says the first
  shift will appear there as soon as it has been held).

OPEN POINT (the owner decides, not settled yet)
- The app counts a JEE paper as a "full mock" for the student's Dream College meter when it has 68 or more questions
  and 150 or more marks. A Matched paper that large would be counted too. If the owner does not want that, the app
  needs to know the paper's kind when it reads the RESULT, so please keep test_kind "matched" on the paper and say
  whether GET /api/attempts/<id>/results can carry test_kind. Nothing is changed in the app about this yet.

4. What our side already does (for your information)
----------------------------------------------------
- Our server copies the shifts into its own database and answers the app from there, so Matched stays up and fast while
  the website is busy (GET /api/matched, /api/matched/<shift>, /api/matched/paper/<paper id> on the app's server).
- Home's card: "auto" = from the day after the series' last day (read from GET /api/series/all-india-jee every 15
  minutes and remembered); "card" in the first door wins over it.
- The app remembers on the phone which papers are Matched papers (from the shifts it has shown), so an ordinary paper
  never asks anything extra.
