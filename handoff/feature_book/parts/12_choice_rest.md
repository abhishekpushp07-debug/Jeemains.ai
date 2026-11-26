## 1.8 Whole chapter tests by the 80 / 60 / 40 ratio, three hours at most: a change on the website

The owner asked: "Make whole chapter tests follow the 80/60/40 time ratio once the website allows changing their time". Shown what the ratio alone gives (some tests longer than four hours), he added on 26 Nov 2026: **a longest time of three hours.** **The app cannot do it.** An attempt's deadline is the website's, taken from the set's `rules.minutes`. **Not done yet:** on {{TODAY}} every JEE Main chapter-wise test has 60 minutes, whatever its length.

**What to change on the website**

- For every published JEE Main chapter-wise set (`test_kind` "chapter"):
  `rules.minutes` = (the set's `count`) × (the minutes a question of its `chapter_subject` brings), rounded **up** to a whole minute, **and never more than 180**. Physics 2.4, Chemistry 1.6, Mathematics 3.2.
- Keep it true: when a chapter's question count changes, its minutes change with it.
- A new attempt gets the new time. **An attempt that is already running keeps the deadline it has.**
- A whole number of minutes, please: the app's pages show `rules.minutes` as it is.

**What it gives, chapter by chapter** (counts as on 26 Nov 2026; today's 60 minutes → by the rule; where the three hours hold a test back, what the ratio alone would give is in brackets):

{{CHAPTER_TABLE}}

**What the rule does**

{{RATIO_FACTS}}

- **The longest time is for whole chapter tests only.** A paper the student makes (Part 1.6) keeps the plain ratio: 75 Mathematics questions get 240 minutes, and the app shows the student that time before the paper exists. Do not cut a made paper unless the owner says so (Part 3.8); the app would have to change with it.
- The owner has not asked for a shortest time. If he does, it is again only `rules.minutes` on the website; the app shows whatever is set.
- It is the same set as in the Chapter-wise section, so that section, on the website and in the app, shows the new time too.

**What the app does with it. Nothing else is needed from the website.**

- Every app version, also older ones: the paper's page shows the set's `rules.minutes` when it is opened; the Chapter-wise list shows the list's minutes; the player runs on the attempt's own deadline.
- Student Choice's list of chapter tests shows each test's minutes from the catalogue (Part 1.5), a few minutes behind at most.
- Student Choice's first screen says today "Poore chapter test ka time uske page par likha hota hai (abhi 1 hr)". **On the day every chapter test has its time by the rule** (the ratio, 180 at most; a minute's rounding apart at most) **the sentence changes by itself** to "Poore chapter test ko bhi isi hisaab se time milta hai: jitne sawaal, utna time (zyada se zyada 3 hr)." With the ratio alone, without the 180, the sentence does not change: the rule is the two together. (The words about three hours are in the app version on the preview since 26 Nov 2026.)
- Checked on 26 Nov 2026 on the web preview, with the catalogue answered in the browser: with the rule's times (81 tests, the longest 180 minutes, the shortest 4) the sentence changed; with the ratio alone (the longest 276) it did not. **Not checked** against the real website (nothing is changed there yet).

## 1.9 The Dream College meter

**The owner's decision (26 Nov 2026):** a chapter test and a Student Choice paper **never** count as a full mock for the Dream College meter, however long they are.

- **The rule in the app:** a JEE Main paper counts as a full mock when it has 68 questions or more and 150 marks or more, **and its `test_kind` is not `chapter` and not `choice`**. Before 26 Nov the kind was not looked at, and a long chapter test was counted.
- **Where the app reads the kind:** `test_kind` of `GET /api/attempts/<id>/results`. "chapter" is there today. **A made Student Choice paper must carry `test_kind` "choice" on the set AND on its result.**
- **A chapter test that an older app version had already counted** is taken out when the student opens that result in an app version with this work. The account remembers it (up to 200 such papers), so no phone and no app version can put it back.
- **Please also put `test_kind` on every item of `GET /api/my/tests`** (the items have none today). A phone that signs in for the first time reads that list to find the student's full mocks; without `test_kind` it opens the paper's page (`GET /api/my/sets/<set_id>`) for every long paper in the list, up to 12 extra reads, once. A paper whose kind cannot be read is left out until its result is opened.
- **Known:** app versions that students had before this work keep counting long chapter tests until they update.
- **The Matched paper is not on the never-count list.** It was not asked for, and a shift's Matched paper is far below 68 questions. See the open points, Part 3.8.

## 1.10 What is stored where

| What | Where | For how long |
| --- | --- | --- |
| The ticked chapters | on the phone, for each account (up to 300 ids) | until unticked. A new phone, or the app installed again, starts with none. After a paper of chosen questions is made, all ticks are cleared |
| The ticked questions | in the app's memory | while the app is open |
| The chapter list (with door A's answer) | the app server's memory; the phone's own copy | server: 2 minutes (answers up to 2 more while it reloads). Phone: shown at once from its copy, read again every time the screen opens |
| A chapter's questions (door B) | the app server's memory; the phone's memory | server: 5 minutes (answers up to 5 more while it reloads). Phone: while the app is open |
| The student's state of the chapter tests | read by the phone from the website | read again when the screen comes back to the front, and on pull-down |
| Anything about a student's choice on the app's server | **nothing is stored** | |
| A made paper, its attempt and its result | the website | like every paper |

Who may ask the app's server for the chapter list: a signed-in student only. The request carries a short pass (15 minutes) that the app's server gives only for a session the website has verified; anything else gets 401.

## 1.11 The super admin's part in Student Choice

**Today there is nothing new to operate.** Student Choice shows what the website's Chapter-wise section has. These actions on the website change Student Choice by themselves, within about four minutes:

| What the super admin does on the website | What happens in Student Choice |
| --- | --- |
| publishes a new JEE Main chapter-wise test | it appears as a chapter of its subject, at its place in the website's order, and can be searched by its title |
| takes a chapter-wise test back (not published, or live off) | it leaves the list. A student who had ticked it simply no longer has it in his tests; nothing breaks |
| renames a chapter-wise test | the new name shows and is searched. (Six short search names are written in the app: Part 1.3) |
| changes its questions | the counts ("68 sawaal · 64 MCQ · 4 numerical") follow |
| changes its minutes or marking | the test's row follows ("60 min · +4/-1 · 272 marks") |
| hides the whole Chapter-wise section | the first screen says "Chapters abhi nahi mile" and offers the button "Chapter-wise tests" |

**When the doors exist** the super admin (or whoever holds the switch of door A) decides: question picking on or off; random mock on or off; a lower top than 75; a top per subject; other minutes per question. A change shows within 2 to 4 minutes, with no app update.

**What to tell a student who asks**

| The student asks | The answer |
| --- | --- |
| "Sawaal khud kyun nahi chun sakta?" | That part is coming ("Jald aa raha hai"). Today the whole test of every chosen chapter can be taken. It will open in the app by itself, without an update |
| "Chapter test 60 minute ka hi kyun hai?" | The time rule on the first screen is for a paper made in Student Choice. A whole chapter test has the time written on its page: 60 minutes today. (Once the website sets the new times: by the same ratio, three hours at most) |
| "Mere chune hue chapters gayab ho gaye." | The ticks are kept on the phone, for the account. A new phone or a fresh install starts empty; a chapter the website took back leaves the list |
| "Kya yeh Dream College meter mein ginta hai?" | No. Chapter tests and Student Choice papers never count; only full mocks do |
| "Student Choice ke sawaal alag hain kya?" | No. They are the JEE Main chapter-wise questions; the attempts are the same ones as in the Chapter-wise section and My Tests |

## 1.12 What happens when…

| Situation | What the student sees | Why |
| --- | --- | --- |
| The website does not answer, or answers 5xx, while the chapter list is read | "Sawaal abhi load nahi ho paaye. Dobara try karo." with a retry. If the phone has the list from before, it stays on screen | the app's server answers 503 and keeps nothing of a failed read |
| The student's website session has run out | nothing: the app renews it and asks again, once | 401 with the code `website_session` |
| The student is signed out | Student Choice cannot be reached: Home is for signed-in students | |
| One page of one subject fails | the whole list fails with a retry | half a list is never shown |
| A ticked chapter is no longer published | it is not listed and not counted | only chapters the list still has count |
| A ticked chapter's test is in progress | "In progress" and **Resume** | a test in progress is never started twice |
| The student's states cannot be read | the rows show no button and cannot be tapped; an error with a retry is shown | |
| The page of step 2 is opened with nothing ticked | the app goes back to step 1 | |
| The 76th question is ticked | it is refused, with the sentence of Part 1.7 | the owner's top |
| Door C is asked twice for the same paper (double tap, slow network) | one paper | the same `request_key` |
| Door A opens while a student is in step 2's chapter tests | on the next read, step 2 becomes the question list for him | the list says which ways are open |
| Door A closes again | the ways go back under "Jald aa raha hai"; the chapter tests are back in step 2 | |
| A question's picture link has expired | "Is sawaal ki picture load nahi hui." in place of the picture | links must live 24 hours |

## 1.13 Checks for the website agent

Run these on a test setup, signed in as a test student (`-b` = that student's cookies).

**Door A**

- `curl -s -b cookies.txt "https://<website>/api/choice/bank?exam=jee-main"` → 200 with `pick` and `random`; no `subjects`.
- The same without cookies → 401 is fine (the app's server always sends the student's cookie).
- Closed → 404.

**Door B**

- For the set id of a chapter-wise test: 200; `items[].id` stable between two calls; **no** `options`, `answer`, `correct`, `solution` or key of any kind anywhere in the answer.
- Every `stem[].url` opens in a private browser window (no cookies), and still opens the next day.
- `pages` is right; the last page is not empty; page `pages + 1` answers 404 or an empty list.
- A set id that is not a chapter-wise test → 404.

**Door C**

- The same body sent twice → the same `set_id`, one set made.
- `question_ids` with 76 ids, with a repeated id, with an id that is not a chapter-wise question, `count` 2, `count` 76 → 422 with a plain sentence.
- The made set: `test_kind` "choice"; `rules` +4 / −1 / 0; `minutes` as Part 1.4 (check 3 Physics + 2 Chemistry + 2 Mathematics = 17; 10 + 10 + 10 = 72; 25 Mathematics = 80); `maximum` = count × 4; questions in the order Physics, Chemistry, Mathematics.
- Random: `count` 10 → 4 + 3 + 3; 11 → 4 + 4 + 3; 75 → 25 + 25 + 25.
- `GET /api/my/sets/<set_id>` and `POST /api/sets/<set_id>/start` work for the owner of the paper and for nobody else.
- After submitting: `GET /api/attempts/<id>/results` carries `test_kind` "choice"; the paper is in My Tests.

**Then, with the app** (tell the app side first): the first screen shows the open ways within 2 to 4 minutes; a paper of chosen questions and a random mock are made, started, submitted; the result shows no Dream College meter.

## 1.14 Not checked, and known small things

**Not checked**

- Anything on a real phone: the lists, the keyboard over the search box and the random sheet, the safe areas. Everything was walked in the app's web preview, at a phone's size.
- Doors A, B and C: they do not exist. The question list and "Paper banao" were walked against made-up typed questions only, **never with picture questions** (the real chapter-wise questions are pictures).
- A chapter test started from Student Choice by the app side (the button was never pressed in a test; it opens the same page the Chapter-wise section opens).
- The rule's times against the real website, and any attempt longer than 180 minutes (a whole chapter test never is; a made paper can be: 75 Mathematics questions get 240 minutes).

**Known small things, not changed**

- In the paper's make-up the subjects' rounded times can add up to a minute or two more than the total (Part 1.7).
- The six short search names are fixed in the app (Part 1.3).
- The Student Choice tile has no switch: taking it off Home needs a new app build (Part 3.4).
