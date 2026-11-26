# Part 3 — Reference

## 3.1 Every address

**The app's own server** (the app calls these; base address: the app's server, then `/api`)

| Address | Who may call | What it gives | Other answers |
| --- | --- | --- | --- |
| `GET /api/choice/bank` | a signed-in student (a short pass in the `Authorization` header) | the chapters of the three subjects with their tests, the owner's rules, and `pick` / `random` | `{ "ready": false }` when there is no chapter at all; 401 without a pass; 401 with the code `website_session` when the website wants a fresh session; 503 when the website does not answer |
| `GET /api/choice/chapters/<id>` | a signed-in student | door B's questions in the shape the app draws; everything else dropped | 404 no questions to choose; 401; 503 |
| `POST /api/jl/choice/papers` | the student's own session | passed on to the website's door C as it is | the website's own answer |
| `GET /api/matched` | everyone | all published shifts, newest first, without their questions; `total` | |
| `GET /api/matched/<shift id>` | everyone | one shift with its questions | 404 not published; 422 an id of another shape |
| `GET /api/matched/paper/<paper id>` | everyone | the published shift whose real paper this is | 404 |
| `GET /api/app/switches` | everyone | `{ "pictures": …, "matched": true or false }`: whether Home shows the Matched card | |
| `DELETE /api/rf/dream/mocks/<attempt id>` | a signed-in student | takes a paper that is no full mock out of that account's Dream College meter, for good | |

**The website: doors in use today** (nothing to build; do not change their fields without telling the app side)

| Door | Used for |
| --- | --- |
| `GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=…&q=&page=…` | the chapters of Student Choice (the app's server), and the student's own state of each test (the phone). Fields: Part 1.5 |
| `GET /api/my/sets/<id>` | the paper's page; also the paper's `test_kind` for the Dream College meter |
| `POST /api/sets/<id>/start` | starting a paper |
| `GET /api/attempts/<id>` | the player: `set_id`, `questions[].id` |
| `GET /api/attempts/<id>/results` | the result: `set_id`, the question ids, `test_kind` |
| `GET /api/my/tests` | My Tests; the Dream College meter's first read on a new phone |
| `GET /api/series/all-india-jee` | `today` and `last_date`: the All India bar shows under the Matched card until `last_date`; the day after it, Home's card turns to Matched also when no shift is published |
| the sign-in and session doors | unchanged |

**The website: doors to build**

| Door | For | Part |
| --- | --- | --- |
| `GET /api/choice/bank?exam=jee-main` | Student Choice: the switch | 1.6, door A |
| `GET /api/choice/chapters/<set id>/questions?page=N` | Student Choice: a chapter's questions without options | 1.6, door B |
| `POST /api/choice/papers` | Student Choice: make the paper | 1.6, door C |
| `GET /api/matched` | Matched: the list of published shifts, and the card's switch | 2.4c |
| `GET /api/matched/<shift id>` | Matched: one shift | 2.4c |

And three changes to what exists: `rules.minutes` of the chapter-wise sets (Part 1.8); `test_kind` "choice" and "matched" on those papers and their results; `test_kind` on the items of `GET /api/my/tests` (Part 1.9).

## 3.2 Every number

**Student Choice**

| Number | Value |
| --- | --- |
| Most questions in a made paper | 75 (the website may lower it, never raise it) |
| Fewest in a random mock | 3 |
| Marking | +4, −1, 0 |
| Minutes a question brings | Mathematics 3.2, Physics 2.4, Chemistry 1.6; the sum rounded up |
| Longest time of a whole chapter test (the owner's rule; the website sets it) | 180 minutes. A made paper is not cut (75 Mathematics questions: 240) |
| Other minutes per question the website may send | 0.5 to 10 each |
| A top per subject the website may send | 1 to 75 |
| Random mock: number box and quick buttons | starts at 30; buttons 15, 30, 45, 60, 75 |
| Chapters shown for one subject | 120 |
| Pages of the catalogue read for one subject | 12 |
| A chapter: its question count; its number; its title | 1 to 5000; 1 to 999; 120 characters |
| A chapter's test: marks; right; wrong; minutes | 1 to 20000; 1 to 20; −20 to 0; 1 to 1000 |
| Door B: pages read; questions kept; pictures of a question | 6; 300; 4 |
| Door B: a question's words; a picture link; an id | 3000 characters; 900 characters; 6 to 80 characters |
| The app's server keeps the chapter list | 2 minutes (and answers 2 more while it reads a fresh copy) |
| The app's server keeps a chapter's questions | 5 minutes (and answers 5 more while it reads a fresh copy) |
| The student's pass for the app's server | 15 minutes, renewed by the app |
| Ticked chapters kept on a phone | 300 |
| Search: letters typed; words used | 60; 8 |
| Dream College meter: a full mock (JEE Main) | 68 questions or more and 150 marks or more, and not a chapter test or a Student Choice paper |

**Matched**

| Number | Value |
| --- | --- |
| Shifts listed | 200 |
| Matched questions read in a shift | 150 |
| Of ours for one JEE question | 4 |
| Options; pictures; solution pictures of a question | 6; 6; 6 |
| Words: question; an option; answer; solution | 6000; 1500; 300; 6000 characters |
| Words: source; tag; chapter | 80; 40; 80 characters |
| A picture link | 600 characters, https |
| Question number in the JEE paper; `asked` | 1 to 300; 1 to 300 |
| Shift number | 1 to 9 |
| An id (paper, question) | 6 to 80 letters, digits, `-` or `_` |
| The copy of the website's shifts | every 2 minutes; 20 shifts read in one pass; a shift without `updated_at` read again every 10 minutes |
| The series' last day | read every 15 minutes (2 minutes after a miss) |
| The card's switch in the app's database | read again at most once a minute |
| The app's server keeps each Matched answer | 1 minute (and answers 1 more while it reads a fresh copy) |
| A phone asks for the switch | when the app is opened, and when it comes back after 30 minutes or more |
| Matched papers a phone remembers | 300 |
| Marks on the shift's card | questions × 4 |

## 3.3 Where data is kept

**The app server's database**

| Where | What |
| --- | --- |
| collection `matched_shifts` | one document per shift: `_id` (the shift's id), `published`, `asked`, `updated_at`, `paper_id`, `items`; `source: "website"` and `synced_at` on a shift copied from the website; `sample: true` on the preview's made-up shifts |
| `rf_meta`, row `matched:card` | Home's card: `on`, `off` or `auto` |
| `rf_meta`, row `matched:aits_last_day` | the All India series' last day, as last read from the website |
| `rf_meta`, row `choice:sample` and collection `choice_sample` | **preview only:** made-up chapters and questions for walking the question-picking screens. Off. Production has no such row |
| `rf_dreams`, field `dropped` | papers taken out of a student's Dream College meter (up to 200 for an account) |

Nothing about Student Choice is written anywhere on the app's server: no chapter, no question, no student's choice.

**The phone**

| Key | What |
| --- | --- |
| `choice.chapters.<account id>` | the ticked chapters of that account |
| `matched.on` | the last answer of the card's switch |
| `matched.papers` | the ids of the Matched papers this phone has seen |
| the phone's short copies of the chapter list and of the Matched list | shown at once when a screen opens, then read again |

## 3.4 Switches and ways back

| To do this | Do this | Who | How fast |
| --- | --- | --- | --- |
| Close question picking, or the random mock | door A: `"pick": false` or `"random": false` (or 404 for both) | the website | 2 to 4 minutes |
| Lower the top of a made paper, cap a subject | door A: `max_questions`, `max_per_subject` | the website | 2 to 4 minutes |
| Take one chapter out of Student Choice | take that chapter-wise test back on the website | the super admin | about 4 minutes |
| Empty Student Choice | hide the Chapter-wise section: the tile stays and says "Chapters abhi nahi mile" | the super admin | about 4 minutes |
| Take the Student Choice tile off Home | **there is no switch:** a new app build | the app side | a new build |
| Turn Home's Matched card and the sign-in bar on or off | `card` in the website's list door; or the row `matched:card` in the app's database when the website sends no `card` | the super admin; the app side | about 3 minutes, then at each phone's next app launch |
| Take one shift back | unpublish it on the website | the super admin | about 5 minutes |
| Take a shift back when the website cannot | set `published` to `false` on its document in `matched_shifts` (a shift the website still lists comes back on the next pass) | the app side | 1 to 2 minutes |
| Stop the JEE question showing under ours for a paper | take the shift back, or take the `question_id`s out and save | the super admin | about 5 minutes |
| Hide the preview's samples | `python3 backend/tests/matched_sample.py hide`; `python3 backend/tests/choice_sample.py hide` | the app side | 1 to 2 minutes |

None of these needs an app update, except taking the tile off Home.

## 3.5 Every sentence a student can read

**Student Choice**

| Where | Words | When |
| --- | --- | --- |
| Home tile | STUDENT CHOICE · apne chapters chuno · NEW | always |
| First screen, top | Student Choice · Apne chapters, apni marzi. | today |
| | Apna paper, apni marzi. (small line: Apna paper khud banao) | when a way of making a paper is open |
| First screen, text | JEE Main ke chapter-wise sawaal, aapke chune chapters ke hisaab se. Result, analysis aur solutions har paper ki tarah milte hain. | today |
| | JEE Main ke chapter-wise sawaalon mein se chapters aur sawaal khud chuno. Result, analysis aur solutions har paper ki tarah milte hain. | question picking open |
| Card | Chapters chuno: Physics, Chemistry aur Maths ke chapters tick karo. Har chune chapter ka poora test milega: ek-ek karke do. | today |
| Card | Aapke chapter tests: Chune hue 3 chapters ke test: shuru karo, jaari rakho ya result dekho. | chapters are ticked |
| Card | Sawaal khud chuno: Subject, phir chapters, phir sawaal. Sirf sawaal dikhte hain, options paper mein milte hain. | question picking open |
| Card | Random mock: Bas sawaalon ki ginti batao. Physics, Chemistry aur Maths mile-jule aayenge, JEE Main ki tarah. | random mock open |
| Coming soon | Jald aa raha hai. Sawaal khud chunna. Chune chapters ke sawaal dekho (bina options), jo chahiye tick karo, aur un sab ka ek hi paper banao: 75 sawaal tak. Random mock. Bas ginti batao; Physics, Chemistry aur Maths ke sawaal mile-jule aayenge, JEE Main ki tarah. Khulte hi yahin dikhega, app update kiye bina. | while a way is closed |
| Time | Banaye hue paper ka time (later: Time kaise milta hai). Har sawaal apne subject ka time laata hai, isliye chhota paper chhota time paata hai. 25 + 25 + 25 sawaal = 3 hr. | always |
| Time, last sentence | Yeh time aapke banaye paper par lagega (sawaal chunna aur random mock). Poore chapter test ka time uske page par likha hota hai (abhi 1 hr). | today |
| | Poore chapter test ko bhi isi hisaab se time milta hai: jitne sawaal, utna time (zyada se zyada 3 hr). | the day every chapter test has its time by the rule of Part 1.8 |
| No chapters | Chapters abhi nahi mile. Student Choice ke sawaal JEE Main ke chapter-wise sawaal hi hain. Abhi koi chapter khula nahi mila. Thodi der mein dobara dekho, ya chapter-wise tests kholo. (button: Chapter-wise tests) | the website lists no chapter-wise test |
| Step 1 | Chapters chuno · Student Choice · Step 1 of 2 · Chapter ka naam likho… | |
| Step 1 | Jitne chahiye utne chapter tick karo, kisi bhi subject se. Agle step mein har chune chapter ka poora test milega. | today |
| Search | 3 chapters mile · teeno subjects mein dhoonda | chapters found |
| Search | Is naam ka chapter nahi mila. Milte-julte naam: | only near spellings found |
| Search | Is naam ka chapter nahi mila. Spelling dekh lo, ya subject se chapter chuno. (button: Search hatao) | nothing found |
| Step 1, bar | Chapter chuno · Kam se kam ek chapter tick karo | nothing ticked |
| Step 1, bar | 3 chapters chune · 3 tests · 165 sawaal · Tests dekho | chapters ticked |
| Step 2, tests | Aapke chapter tests · Student Choice · Step 2 of 2 · 3 chapter tests · 2 ho gaye | |
| Step 2, tests | Har chapter ka poora test hai: jo chaho pehle do, ek-ek karke. Result, analysis aur solutions har paper ki tarah milte hain. | |
| Step 2, a row | 68 Q · 60 min · +4/-1 · 272 marks · Start (or In progress · Resume, or Completed · Result) · Chapters badlo | |
| Step 2, questions | Sawaal chuno · Maths · 12 sawaal · yahan sirf sawaal hain, options paper mein milenge | question picking open |
| Step 2, questions | 75 sawaal ho gaye: ek paper mein isse zyada nahi. Koi hatao, tab naya chuno. | the 76th tap |
| Step 2, questions | Physics ke 25 sawaal ho gaye. Koi hatao, tab naya chuno. | a subject's top is reached |
| Step 2, questions | Is chapter mein sawaal nahi mile. Doosra chapter chuno. | the chapter's list is empty |
| Step 2, bar | 7 / 75 sawaal · 17 min · 28 marks · Paper banao (nothing chosen: Sawaal par tap karke chuno) | |
| Sheet | Aapka paper. Poore 28 marks. Sahi jawab +4, galat -1, chhoda hua 0. Paper Physics, Chemistry, Maths ke order mein banega; result, analysis aur solutions har paper ki tarah milenge. (buttons: Haan, paper banao · Aur sawaal chuno) | "Paper banao" |
| Random mock | Bas ginti batao. Sawaal Physics, Chemistry, Maths se barabar aur mile-jule aayenge, JEE Main ke paper ki tarah. Kitne sawaal? (3 se 75) | |
| Random mock | Poore 120 marks · sahi +4, galat -1, chhoda 0 · time 1 hr 12 min (button: Random mock banao) | a good number |
| Random mock | 3 se 75 ke beech ginti likho. | a number outside the range |
| Trouble | Sawaal abhi load nahi ho paaye. Dobara try karo. | the list could not be read |
| Trouble | Is chapter ke sawaal abhi yahan nahi khul paaye. Doosra chapter chuno, ya thodi der mein dobara dekho. | a chapter's questions could not be opened |
| Trouble | Is sawaal ki picture load nahi hui. | a question's picture did not load |
| Trouble | Paper banana abhi jeelive.ai se jud raha hai. Thodi der mein yeh khul jayega; aapke chune sawaal yahin rahenge. | door C answers 404 or 405 |
| Trouble | Paper ban nahi paaya. Dobara try karo. / Mock ban nahi paaya. Dobara try karo. | the paper could not be made |
| Trouble | Connection interrupted. Please try again. / Please sign in again. | no network; the session could not be renewed |

**Matched**

| Where | Words | When |
| --- | --- | --- |
| Everywhere | MATCHED · JEE Mains questions matched with ours | |
| Home | Matched with JEE Main · view all · JEE MAIN · 3 SHIFTS · 11 questions matched · 24 Jan · Shift 1, latest shift · See matched questions | shifts are published |
| Home | JEE Main ke har shift ke baad yahan woh questions aayenge jo hamare questions se match hue. (button: Open Matched) | no shift yet |
| Home | Dekh rahe hain… / Abhi load nahi hua. Kholo aur dobara try karo. | loading; could not load |
| Home, the bar under the card | ALL INDIA SERIES · DAY 46 / 50 · Live today · Start today's test (also: In progress · Resume; Completed · View result; Completed · Results at 11:59 PM; Awaiting paper; Starts closed; Day ended; Live series. Before the series: 50 DAYS · Starts 9 Dec. On a narrow phone: ALL INDIA) | Matched is on and the All India series still has days |
| Sign-in screen | Dekho | the bar |
| Sign-in screen | Account banao ya sign in karo. Uske baad Matched paper attempt kar sakte ho. | reached from "Attempt all matched" |
| Matched page | Matched · JEE Main · 11 questions matched in 3 shifts · SHIFT 1 · 6 of 75 matched | |
| Matched page | Pehla shift hote hi yahan aayega. JEE Main ke har shift ke baad yahan woh questions dikhenge jo hamare questions se match hue: unka question, aur uske saamne hamara. | no shift yet |
| Shift, top card | JEE MAIN 2027 · 6 of 75 questions matched with ours · 7 questions · 28 marks · +4 / −1 marking · Attempt all matched | the shift has a paper |
| Shift, top card | Dekhna sabke liye khula hai. Paper attempt karne ke liye free account banao. | signed out |
| Shift, top card | Hamare woh sawaal jo JEE Main mein match hue, ek paper mein. Timer, result, analysis aur solutions: har paper ki tarah. | signed in |
| Shift, top card | Is shift ke matched sawaalon ka paper jald yahan khulega. | no paper yet |
| Shift | KAUN SA SAWAAL KISSE MATCH HUA · All · Physics · Chemistry · Maths | |
| Shift | Is shift mein koi match nahi mila. Doosre shifts dekhne ke liye wapas jao. | a shift with no question |
| A card | Question · Solution · JEE MAIN 2027 · HAMARA QUESTION · SAHI JAWAB · SOLUTION | |
| A card | Iska likha hua solution abhi nahi hai; sahi jawab upar diya hai. | only the answer was given |
| A card | Is question ka solution abhi nahi aaya. | neither answer nor solution |
| A card | Picture load nahi hui. Dobara try karo | a picture did not load |
| Sheet | Sign up karke attempt karo. Matched sawaal dekhna sabke liye khula hai. Inhe paper ki tarah attempt karne ke liye (timer, result, analysis aur solutions ke saath) free account banao: sirf mobile number aur PIN. (buttons: Free account banao · Mera account hai · Sign in) | signed out, "Attempt all matched" |
| Paper's page | JEE MAIN · MATCHED PAPER | the paper's kind is `matched` |
| Player, solutions | JEE MAIN 2027 MEIN AAYA · 22 Jan · Shift 1 · Q4 | a Matched paper |
| Trouble | Matched abhi load nahi ho paaya. Dobara try karo. / Yeh shift ab yahan nahi hai. / Connection interrupted. Please try again. | |

## 3.6 Files and tests (for the app side)

| Part | Files |
| --- | --- |
| Student Choice, server | `backend/choice.py`; door C passes through `backend/jl_proxy.py` |
| Student Choice, app | `frontend/app/choice/index.tsx`, `pick.tsx`, `tests.tsx`, `questions.tsx`; `frontend/src/choice/api.ts`, `search.ts`, `store.ts`, `parts.tsx`; Home's tile in `frontend/app/(tabs)/index.tsx` |
| Dream College meter | `frontend/src/dream/store.ts` (`isFullMock`), `frontend/app/result/[id].tsx`, `backend/dream.py` |
| Matched, server | `backend/matched.py` (the pages, the copy of the website's shifts, the card's day), `backend/app_switches.py`, started in `backend/server.py` |
| Matched, app | `frontend/app/matched/index.tsx`, `[id].tsx`; `frontend/src/matched/api.ts`, `gate.tsx`, `MatchedCard.tsx`, `looks.tsx`, `Pair.tsx`, `QuestionBlock.tsx`, `MatchedWith.tsx`, `parts.tsx`, `html.ts`; Home `frontend/app/(tabs)/index.tsx`; the All India bar under the card `frontend/src/components/series/HomeSeriesBar.tsx`; sign-in `frontend/app/entry.tsx`; public routes `frontend/app/_layout.tsx`; player `frontend/app/attempt/[id].tsx`; result `frontend/app/result/[id].tsx`; paper's page `frontend/app/set/[id].tsx` |
| Tests | `backend/tests/test_choice.py` (12), `test_matched.py` (6), `test_matched_sync.py` (5): {{TESTS_LINE}}. Search: `node tests/choice_search_check.js`. Looks on the preview (read only): `python3 tests/home_series_bar_look.py`, `python3 tests/choice_cap_sentence_look.py` |
| Samples (preview only) | `backend/tests/matched_sample.py show` or `hide`; `backend/tests/choice_sample.py show` or `hide` |
| Earlier notes | `memory/WEBSITE_CHOICE_NOTE.md`, `memory/WEBSITE_MATCHED_NOTE.md`, `memory/MATCHED_CONTRACT.md`. This book was written from the code on {{TODAY}} and takes their place for readers outside the app side |
| This book | `handoff/feature_book/`: `parts/` (the text), `examples/` (the JSON), `shots/` (the pictures), `build_book.py`, `take_shots.py` |

### Names of the screens' parts, for automated checks

Every part of the two features carries a fixed name (`testID`; in the web preview it is the `data-testid`). The ones a check needs most:

| Screen | Names |
| --- | --- |
| Home | `home-tile-choice` (the tile), `home-tile-choice-badge`; `home-matched` (the card), `home-matched-total`, `home-matched-latest`, `home-matched-cta`, `home-matched-soon`, `home-matched-view-all`; `home-series-bar` (the All India bar under the Matched card), `home-series-bar-day`, `home-series-bar-line`; `home-series-view-all` (the All India card is on instead) |
| Sign-in screen | `entry-matched` (the bar), `entry-matched-note` (the note after "Attempt all matched") |
| Student Choice, first screen | `choice-screen`, `choice-title`, `choice-facts`, `choice-way-chapters`, `choice-way-tests`, `choice-way-pick`, `choice-way-random`, `choice-soon`, `choice-soon-pick`, `choice-soon-random`, `choice-time`, `choice-time-physics` / `-chemistry` / `-mathematics`, `choice-time-note`, `choice-not-ready`, `choice-error`, `choice-refresh` |
| Random mock sheet | `choice-random-sheet`, `choice-random-input`, `choice-random-quick-15` … `-75`, `choice-random-makeup`, `choice-random-rule`, `choice-random-range`, `choice-random-error`, `choice-random-make` |
| Step 1, chapters | `choice-pick-screen`, `choice-search-input`, `choice-search-clear`, `choice-search-count`, `choice-search-none`, `choice-search-reset`, `choice-subject-…` (the pills), `choice-chapter-list`, `choice-chapter-<id>` (a row; it is a checkbox), `choice-chapter-<id>-title`, `-subject`, `-picked`, `choice-pick-hint`, `choice-pick-bar` |
| Step 2, chapter tests | `choice-tests-screen`, `choice-tests-count`, `choice-tests-subject-physics` / `-chemistry` / `-mathematics`, `choice-test-<id>` (a row), `-title`, `-facts`, `-status`, `-action` (Start, Resume or Result), `choice-tests-error`, `choice-tests-change` |
| Step 2, questions (later) | `choice-questions-screen`, `choice-q-subject-…`, `choice-q-chapter-…`, `choice-questions-chapter`, `choice-questions-hint`, `choice-question-list`, `choice-full`, `choice-next-chapter`, `choice-questions-bar`, `choice-review-sheet`, `choice-review-makeup`, `choice-review-rule`, `choice-review-error`, `choice-make`, `choice-review-back` |
| Matched page | `matched-screen`, `matched-total`, `matched-month-…` (the pills) or `matched-month-only`, `matched-day-<day>`, `matched-shift-<shift id>` (a row), `-count`, `-number`, `matched-empty`, `matched-error`, `matched-refresh` |
| A shift | `matched-shift-screen`, `matched-shift-count`, `matched-attempt` (the button), `matched-attempt-facts`, `matched-attempt-questions`, `matched-attempt-note`, `matched-attempt-soon`, `matched-shift-list-title`, `matched-subject-…` (the pills), `matched-shift-list`, `matched-shift-empty`, `matched-shift-error`, `matched-signup-sheet`, `matched-signup-yes`, `matched-signup-login` |
| The paper's page, player, solutions, result | `set-detail-screen`; `matched-with` (the JEE question under ours), `matched-with-where`, `matched-with-jee`; `result-dream` (the Dream College meter: must be absent on a chapter test and on a Student Choice paper) |

A row of the chapter list is best found as `[role=checkbox][data-testid^=choice-chapter-]`: the list's own name starts with the same letters.

**A hard rule for anyone testing on the app's preview:** the test learner there is the owner's own account on the real website. Never press Start, Begin, Resume or Submit with it, never open an attempt, never tap a chapter test whose button says Resume. Walks that need a started or finished paper use a test student on the website's test setup, or answers given by the browser in place of the website.

## 3.7 The state on {{TODAY}}, and how to check it again

Read by the build of this book, at {{NOW}}:

{{STATE_TABLE}}

Also true on {{TODAY}}, seen through the app's preview: the website lists **81 chapter-wise tests** (Physics 30, Chemistry 24, Mathematics 27) with **3750 questions**, and every one of them has **60 minutes**.

To check again, from any machine:

```
# "matched": false until the card is on
curl -s https://jeelive-mobile.emergent.host/api/app/switches
# the published shifts ("shifts": [] today)
curl -s https://jeelive-mobile.emergent.host/api/matched
# 401 = the door is there, for signed-in students only
curl -s -o /dev/null -w "%{http_code}\n" https://jeelive-mobile.emergent.host/api/choice/bank
# 404 = the website's Matched door is not built yet
curl -s -o /dev/null -w "%{http_code}\n" https://jeelive.ai/api/matched
# "last_date": with no shift published, the card turns the day after
curl -s https://jeelive.ai/api/series/all-india-jee
```

## 3.8 Decided by the owner, and still open

**Decided on 26 Nov 2026** (both were open points in version 1 of this book)

| The question | The owner's answer | Where |
| --- | --- | --- |
| Whole chapter tests by the ratio as given, or with a longest time? | **A longest time of three hours.** 7 tests are held at 180 minutes; no chapter test is longer than a full mock | Part 1.8 |
| When should Matched appear if JEE Main shifts are held before the All India series ends? | **On the day of the first shift itself:** the card turns to Matched as soon as the first shift is published; the series is a bar under it for its remaining days | Part 2.6 |

**Still open**

| # | The question | What happens until it is answered |
| --- | --- | --- |
| 1 | **Should the three hours also be the longest time of a paper the student makes?** By the ratio alone 75 Mathematics questions get 240 minutes. (A top of 25 questions per subject, door A's `max_per_subject`, would also keep every made paper within 180.) | made papers are not cut |
| 2 | **A shortest time for whole chapter tests?** By the rule {{SHORTER_COUNT}} tests become shorter than today's 60 minutes; the shortest gets 4 minutes for its 2 questions (Part 1.8) | the rule as given: no shortest time |
| 3 | **Should a Matched paper ever count for the Dream College meter?** Today it would, if it had 68 questions or more and 150 marks or more. Chapter tests and Student Choice papers never count | it would count; a shift's paper is far smaller than that |
| 4 | **The app side's suggestions for made papers** (Part 1.6): fresh questions first in a random mock; a daily limit; removing papers never started; no leaderboard | the website agent should not build them unasked |
| 5 | **The wording of `source` and `tag` on Matched** (Part 2.8) | the super admin writes what seems right |
| 6 | **The made-up sample shifts on the preview:** keep them for looking, or hide them now? | they stay published on the preview only |
