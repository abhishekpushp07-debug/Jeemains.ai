JEELIVE.AI — note for the website project: the student's name, Class 11 / Class 12, test students, and what is still open
(copy and paste this into the website project's chat)                                                  27 Nov 2026
==============================================================================================================

How to read this
- Written by the app project. The website stays the owner of students, names, questions and papers; the app only asks.
- Paths are the website's own (/api/...). "Seen" = read from the live website on 27 Nov 2026 with the QA learner,
  read only. Nothing was written.
- Parts 1 to 3 are new. Part 4 is NOT asked for yet (the owner will decide). Part 5 repeats what is still open from
  the book (version 4). Part 6 is questions only.
- Nothing in the app is broken while these are missing: every part says what the app does until then.


PART 1 — the student's own name can be written but not read                                       (priority: high)
--------------------------------------------------------------------------------------------------------------
What the app did on 27 Nov
- The Account screen now has "Add your name / Change your name". It uses your call, unchanged:
      PUT /api/profile/display-name      { "name": "Asha Rao" }      ->   data: { "display_name": "Asha Rao" }
      an empty name takes the name away.
- The owner's rule: ONE name everywhere (your leaderboards, and Rapid Fire, which lives on the app's server).
  So the app's server keeps a copy of the name. It copies ONLY your own answer to that PUT (status 2xx, a
  "display_name" key in data), for the account whose session made the request. A phone can never tell it a name.

What was seen
- POST /api/auth/phone and GET /api/auth/me answer
      data: { id, name, phone, role, exam, access_type, pin_configured }
  "name" is "Learner XXXXXXXX". The display name is not there.
- GET /api/me, /api/account, /api/profile/summary, /api/my/profile, /api/settings: 404. We found no call that says
  the display name of the signed-in student. (Your leaderboard rows carry it, but only for a student who has a row.)

What that costs today
- A name saved before 27 Nov, or saved on jeelive.ai itself, never reaches the app's server: Rapid Fire shows the old
  name, and Account says "Add your name" although your leaderboards already show one. It heals only when the student
  saves the name once more from the app.

What the app needs
  (a) "display_name" in data of GET /api/auth/me:   the name as you keep it, or null when the student has none.
      - always present (null, not left out), and never the "Learner XXXXXXXX" fallback;
      - the same key in the answers of POST /api/auth/phone, /api/auth/phone/signup and /api/auth/refresh, if they
        send the user.
      Nothing else is needed. The app's server already looks for this key every time it checks a session with
      auth/me and takes the name from it. The day it appears, every student's name is right in Rapid Fire and on
      the Account screen, with no app update.
  (b) optional:   "display_name_changes_left": 2      (of today's 3) beside it, so the sheet can say it before the
      student types. (Small app change, made when you say it exists.)

Please confirm (the app assumes these; a real save was never made, because the QA learner is the owner's own account)
- success: 2xx with data.display_name = the name as kept.   Removal: 2xx with data.display_name null or "".
- refusal (too short, too long, a sign, the fourth change of a day): 4xx with a plain sentence in error.message.
  The app shows that sentence to the student as it is.
- rules: 2 to 20 letters, digits or spaces; 3 changes a day. Is anything else checked (a name another student
  already has, bad words)?


PART 2 — which class a chapter belongs to (Class 11 / Class 12)                                 (priority: medium)
--------------------------------------------------------------------------------------------------------------
What the app did on 27 Nov
- Chapter-wise (JEE Main: Physics, Chemistry, Mathematics) has three tabs: All | Class 11 | Class 12. Rapid Fire's
  chapter picker lists Class 11 first, then Class 12. One tap still opens one chapter test; nothing else changed.

What was seen
      GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=Physics&q=&page=1
      ->  data: { exam, kind, section, subject_counts, total: 30, page: 1, pages: 3, items: [ 12 rows ] }
- A row has id, title, chapter_number, chapter_subject, chapter_book_id (null), test_kind, count, rules, attempt, ...
  Nothing says the class.
- Always 12 rows a page: per_page, page_size, limit and size are ignored (all four tried: 200, 12 rows, pages 3).

What the app does until then
- The class comes from the app's own list, found by the chapter's TITLE (leading number dropped, capitals and signs
  ignored): "02 Kinematics" -> "kinematics" -> 11. A title the list does not know is never hidden: it is shown
  under "Other" (as "24 Miscellaneous (beyond the current syllabus)" is today).
- To show a subject by class the app reads all its pages: 3 requests for Physics and for Mathematics, 2 for Chemistry.

What the app needs
  (a) on every chapter row:    "class_level": 11 | 12 | null            (null = neither, for example Miscellaneous)
      Then the class is yours, a renamed or new chapter can never land under "Other", and other exams can get the
      tabs too. (Small app change to read it; say when it exists.)
  (b) a whole subject in one answer: honour  per_page=100  (the default stays 12), or any other way you prefer.
      One request instead of three each time a student opens a subject. (Small app change; say the parameter.)
  (c) until (a) exists: tell the app project BEFORE a JEE Main chapter-wise test is renamed, added, merged or removed.

Where the app has put your 81 chapters today — please correct anything that is wrong
  Physics, Class 11 (15):     01 Units, Dimensions and Errors; 02 Kinematics; 03 Laws of Motion; 04 Work, Energy and
      Power; 05 Centre of Mass, Momentum and Collisions; 06 Rotational Motion; 07 Gravitation; 08 Mechanical
      Properties of Solids; 09 Fluids; 10 Surface Tension; 11 Thermal Properties of Matter; 12 Thermodynamics;
      13 Kinetic Theory of Gases; 14 Oscillations; 15 Waves and Sound
  Physics, Class 12 (15):     16 Electrostatics; 17 Capacitors; 18 Current Electricity; 19 Magnetic Effects of
      Current; 20 Magnetism and Matter; 21 Electromagnetic Induction; 22 Alternating Current; 23 Electromagnetic
      Waves; 24 Ray Optics and Optical Instruments; 25 Wave Optics; 26 Dual Nature of Matter and Radiation;
      27 Atoms; 28 Nuclei; 29 Semiconductors and Logic Gates; 30 Experimental Skills *
  Chemistry, Class 11 (11):   01 Mole Concept and Stoichiometry; 02 Atomic Structure; 03 Classification of Elements
      and Periodicity; 04 Chemical Bonding and Molecular Structure; 05 Thermodynamics and Thermochemistry;
      06 Chemical Equilibrium; 07 Ionic Equilibrium; 08 Redox Reactions; 15 Purification and Characterisation of
      Organic Compounds; 16 General Organic Chemistry; 17 Hydrocarbons
  Chemistry, Class 12 (12):   09 Solutions; 10 Electrochemistry; 11 Chemical Kinetics; 12 p-Block Elements *;
      13 d- and f-Block Elements; 14 Coordination Compounds; 18 Haloalkanes and Haloarenes; 19 Alcohols, Phenols
      and Ethers; 20 Aldehydes, Ketones and Carboxylic Acids; 21 Amines and Diazonium Salts; 22 Biomolecules;
      23 Principles Related to Practical Chemistry *
  Chemistry, no class (1):    24 Miscellaneous (beyond the current syllabus)
  Mathematics, Class 11 (17): 01 Sets and Relations *; 02 Functions *; 03 Basic Algebra (Inequalities, Modulus,
      Logarithms); 04 Trigonometric Ratios, Identities and Equations; 05 Complex Numbers; 06 Quadratic Equations;
      07 Permutations and Combinations; 08 Binomial Theorem; 09 Sequences and Series; 10 Straight Lines;
      11 Circles; 12 Parabola; 13 Ellipse; 14 Hyperbola; 15 Limits; 16 Statistics; 17 Probability *
  Mathematics, Class 12 (10): 18 Matrices and Determinants; 19 Inverse Trigonometric Functions; 20 Continuity and
      Differentiability; 21 Application of Derivatives; 22 Indefinite Integration; 23 Definite Integration;
      24 Area under Curves; 25 Differential Equations; 26 Vector Algebra; 27 Three-Dimensional Geometry *
- * = the app side was not sure: in the school books these span both classes. What do these seven tests really
  hold: Class 11 questions, Class 12, or both? (If both, whether to split a test in two is the owner's call; it is
  not asked here.)


PART 3 — two test students                                                                        (priority: high)
--------------------------------------------------------------------------------------------------------------
- The only account the app project may sign in with is the owner's own, so it is used read only. Never done for
  real from the app: saving or removing a name, the fourth name change of a day, two students on one phone, an app
  sign-up followed by a jeelive.ai sign-in (and the reverse; auth/me must give the same id). Starting and handing in
  papers is avoided for the same reason.
- Needed: TWO student accounts (phone + PIN) that the website marks as test: kept out of the students' leaderboards,
  counts and exports (or easy to wipe), and safe to write to. If you can, no 3-a-day limit on their names.
- Give the numbers and PINs to the owner; he passes them to the app project.


PART 4 — a Class 11 mock: NOT ASKED FOR YET (the owner will talk it through first)
--------------------------------------------------------------------------------------------------------------
Listed only so that door C (Part 5) is built with it in mind. Do not build this part before the owner says so.
- The app cannot put a paper together: you give questions only inside a started attempt and cannot make a set from
  question ids (seen 26 Nov). So any mock made from chapters is made by the website.
- A student's own random mock from Class 11 chapters = door C, mode "random", with one more field:
      POST /api/choice/papers
      { "exam": "jee-main", "mode": "random", "count": 30, "chapters": ["<chapter test id>", ...], "request_key": "<uuid>" }
      ->  { "set_id": "<the new paper's id>" }
  "chapters" = pick only from these chapter-wise tests (the app sends the Class 11 ones). Left out = all chapters,
  as door C says today. Everything else as door C: the split over the subjects, +4 / -1, time by subject, 75 at
  most, the same request_key = the same paper.
- One All India mock for everybody, with a Rank = a paper you publish (as the All India JEE Mains days are). The app
  only shows it; how it is listed is to be agreed then.


PART 5 — still open from the book (version 4): a checklist, nothing new
--------------------------------------------------------------------------------------------------------------
Please answer each line with: done / in work / not started.
  1. Student Choice, door A    GET /api/choice/bank?exam=jee-main                        (404 today = closed)
  2. Student Choice, door B    GET /api/choice/chapters/<chapter test id>/questions?page=1
                               (the questions WITHOUT options, answers or solutions)
  3. Student Choice, door C    POST /api/choice/papers    (pick / random; 75 at most, never 90; +4 / -1;
                               Mathematics 3.2, Physics 2.4, Chemistry 1.6 minutes a question, rounded up;
                               test_kind "choice")
  4. The 81 chapter-wise tests: time by the same ratio, 180 minutes at most (today every one is 60 minutes).
  5. Matched (before the first JEE Main shift, January 2027):   GET /api/matched,   GET /api/matched/<shift>,
     one ordinary paper a shift, the super admin page, and the machine that matches a JEE paper with our questions
     (built nowhere yet).
  6. All India series leaderboard    GET /api/series/all-india-jee/leaderboard[?q=]    (404 when last seen; the app
     shows it by itself the day it answers).  Optional: GET /api/series/all-india-jee/my-days.
  7. One handle per student on every All India day (today a new handle on every paper), or
     GET /api/series/all-india-jee/compare?with=<handle>.
  8. Misfire: the six checks of the book (Part 4.4); the test_kind of Student Choice and Matched papers in the
     history; test_kind on every row of GET /api/my/tests.
  9. An account-deletion call. Today the website has none: the app erases its own side at once and the owner deletes
     the website account by hand. Any shape will do (the student's own request with the PIN, or a call the app's
     server may make); say which.
 10. Pictures fast-load live on jeelive.ai; the "Rapid Fire" button on the website; the signups export for the CEO
     dashboard. The app project does not know where these three stand.


PART 6 — for the owner's target (1 lakh students at once, 10 lakh in all): questions only
--------------------------------------------------------------------------------------------------------------
The app project claims no number until it is measured. To measure, it needs to know:
- Every app request reaches you from the app's server, with the student's own cookies. Is there any limit by
  address (rate limit, firewall, bot rule)? A limit by address would stop all app students together. How would you
  like to recognise the app's server, so that a limit counts the student and not the address?
- What has the website itself been tested to, in requests a second: sign-in, auth/me, the catalogue, start,
  autosave, hand-in, results, leaderboard?
- Where and when may a load test run (a staging copy, or an agreed hour), so that no real student is touched? It
  would use the test students of Part 3.


WHAT TO SEND BACK
--------------------------------------------------------------------------------------------------------------
- Part 1: "done" + one real answer of GET /api/auth/me (the values may be made up), and the three confirmations.
- Part 2: "done" + one row of the catalogue with class_level, the page-size parameter, and corrections to the list.
- Part 3: the two test students, to the owner.
- Part 4: nothing yet.
- Part 5: one word a line.
- Part 6: the answers, even if an answer is "not measured yet".
