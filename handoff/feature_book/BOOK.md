# JEELIVE.AI — Student Choice, Matched, Misfire, Rapid Fire and one account: the website hand-off

For the JE Live website agent and the JE Live super admin. Written by the app side on 28 Nov 2026. Version 5.

The app side's final hand-off to jeelive.ai. The app's two new features, Student Choice and Matched: what a student sees, what the website has to build, what the super admin does after every JEE Main shift, every field, every limit, every sentence on screen. Then the three things that keep the website and the app one: Misfire (with Offline Misfire and the website's Misfire Mock, new in version 5), Rapid Fire in a browser, and one account. Then how the two sides work together: every door of the website the app uses, and how a change to one is agreed. And what has not been checked yet.

# Part 0 — Read this first

### Owner ke liye (short)

- Yeh **website ko dene wala hand-off, version 5** hai (28 Nov 2026). Version 4 ki saari baatein isme hain; **naya kya hai**, woh theek neeche ke box mein hai.
- **Production:** is book ke bante waqt wahan koi banawati (sample) shift nahi mila.
- Isme chheh cheezein hain: **Student Choice** (Part 1), **Matched** (Part 2), **Misfire** (Part 4: website ka hi, app sirf dikhata hai), **browser wala Rapid Fire** (Part 5: app ka, website sirf link lagati hai), **ek hi account** (Part 6: website ya app, kahin bhi sign up karo, dono jagah wahi phone + PIN chalta hai; yeh pehle se aisa hi hai), aur **saath kaam karne ke niyam** (Part 7, naya: app website ke kaun-kaun se darwaze use karta hai, aur website koi darwaza badalne se pehle kya kare, taaki students ke phone mein app kabhi na toote).
- **Student Choice aaj chalta hai**: student chapters tick karta hai (naam likh kar dhoondh bhi sakta hai) aur har chune chapter ka poora test deta hai. Sawaal JEE Main ke chapter-wise sawaal hi hain; alag bank nahi hai.
- **Naya rang (26 Nov):** Student Choice ke upar ka card result page jaisa gehra laal, aur Physics / Chemistry / Maths ke chamakte rangeen tabs (laal, amber, teal). Neeche ke cards safed hi hain. Banaye paper ke subject-wise minute ab hamesha total ke barabar judte hain.
- **Sawaal khud chunna aur random mock abhi band hain** ("Jald aa raha hai"). Website teen darwaze banayegi (Part 1.6), tab yeh dono app update ke bina khul jayenge.
- **Time ka ratio** (25 Maths = 80 min, 25 Physics = 60 min, 25 Chemistry = 40 min) banaye hue paper par lagega. Poore chapter test abhi 60 min ke hi hain; unka time sirf website badal sakti hai. Aapka faisla (26 Nov): unhe bhi yahi ratio, par **zyada se zyada 3 ghante** (Part 1.8).
- **Dream College meter**: chapter test aur Student Choice paper kabhi nahi ginte, chahe kitne bhi lambe hon.
- **Matched**: app taiyaar hai. Super admin har shift ke baad matched sawaal daalega aur unka ek asli paper banayega. Home ka Matched card **pehla asli shift publish hote hi, usi din** aa jayega; AITS ke bache dinon mein All India series us card ke theek neeche ek bar ban jaati hai. (Koi shift na ho to bhi 28 Jan 2027 se card aa jayega.)
- **Misfire**: website aur app ka Misfire ek hi hai (website ka). Website agent ko Part 4.4 ki 6 baatein check karni hain. All India Rapid ka "Misfires" tab Rapid Fire ka apna hai, alag.
- **Naya (28 Nov): Offline Misfire** (Part 4.7). Misfire ka "Mock" tab ab "Offline Misfire" hai: apni galtiyon ka mock phone par, bina internet bhi (phone par rakhe papers se). Yeh website ka paper kabhi nahi banta; sahi jawab internet aate hi website par "Samajh gaya" ho jaate hain. **Website ko kuch nahi banana.**
- **Naya (28 Nov): website wala Misfire Mock** (Part 4.8). App mein bana hua hai, par **band** hai: jab tak website door A mein `"misfire": true` nahi bhejti, students ko kuch nahi dikhega. Website ko paper banana hai (door C, `mode: "misfire"`), list aur result mein "Samajh gaya" ki ginti deni hai: Part 4.8 ki baatein.
- **Rapid Fire browser mein**: app ke server par chalta hai; website ko sirf "Rapid Fire" button / link lagana hai, code nahi lena (Part 5). **27 Nov ko mila:** production mein iske icons khaali dibbe dikh rahe hain (icon ki file Publish ke saath gayi hi nahi thi). Preview par theek kar diya gaya tha; yeh 28 Nov ke Publish ke saath gaya. Production mein aaj kya dikhta hai, woh Part 0.2 mein hai (book bante waqt padha gaya).
- **Students tak kab:** 26 Nov ke Publish (14:40 UTC) mein version 3 tak ka saara kaam server par pahunch gaya (pehli shift wala rule, AITS bar, 3 ghante wala sentence, naya rang, 26 Nov wala browser Rapid Fire). Aapka agla Publish 28 Nov ko hua: Offline Misfire ke banne ke baad, website wale Misfire Mock se pehle. Production mein aaj kya hai, woh is book ke bante waqt padha jaata hai (Part 0.2). Screens phone mein tabhi badalti hain jab naya app build install ho. Website wale Misfire Mock ka switch (door A ka `misfire`) agle Publish ke saath jayega.
- Website agent ko yeh PDF (ya saath ki `BOOK.md`) dena hai. Super admin ke kaam ke hisse: Part 1.11, Part 2.8, Part 2.9 aur Part 6.5.

### New in version 5 (28 Nov 2026): all that a reader of version 4 needs

1. **Offline Misfire** (Part 4.7, new). Misfire's "Mock" tab is now "Offline Misfire": a mock of the student's own Misfire questions on the phone, also with no internet, from the papers the phone keeps. It is never a paper on the website. A right answer becomes "Samajh gaya" through the website's own Misfire doors when the line is back. **Nothing for the website to build**; three things to keep as they are.
2. **The Misfire Mock made by the website** (Part 4.8, new). Built in the app and **shut** until door A says `"misfire": true`. The website makes the paper with door C (`mode: "misfire"`), lists every one with `GET /my/misfire/mocks`, and says in its result how many questions went to "Samajh gaya". The website and the app agreed every door, answer and sentence on 28 Nov 2026; Part 4.8 has them all, with the JSON.
3. Rules 27 and 28 are new in Part 0.4. Part 7.2 and Part 7.5 name the Misfire Mock's doors.
4. The owner published again on 28 Nov 2026, after Offline Misfire was built and before the Misfire Mock was (Part 0.2). Everything else says what version 4 said.

### New in version 4 (27 Nov 2026)

1. **Where things stand has changed** (Part 0.2). The owner published on 26 Nov 2026 (live at 14:40 UTC): the app's server in production now has everything of version 3. What is still only on the preview is said there, row by row.
2. **Rapid Fire in a browser** (Part 5.2). In production its icons are empty boxes: the icon font never reached production. Found on 27 Nov 2026 and mended on the preview; students get it with the owner's next Publish. The same new copy rests its decoration and its celebrations on a slow device. **Nothing for the website to do.**
3. **Part 7 is new: working together.** Every door of the website the app uses (64, checked against the app's code when this book is built), how the app's server reaches the website, **what the website must not change without telling the app side**, how a change is agreed, and the doors the app already asks for (among them the whole-series leaderboard of the All India series).
4. **Two more rules in Part 0.4** (25 and 26): never a redirect or an HTML page on an API door; tell the app side before a door changes.
5. **A made-up sample is never shown outside the app's own workspace** (Part 2.12). Before, this was only a rule for people; since 27 Nov 2026 the app's server keeps it by itself.
6. Parts 1, 4 and 6 say what they said in version 3. In Part 2 only the lines about production and about the samples changed.

## 0.1 What is in this hand-off

Two new features, three things the website must know so that the website and the app stay one, and (new in version 4) how the two sides work together:

**Student Choice** (Home's fourth tile, marked NEW). The student goes through the JEE Main chapter-wise questions his own way.

- **Today:** tick chapters in Physics, Chemistry and Maths (a search box finds any chapter by name), then take each ticked chapter's whole test, one after another.
- **Later, when the website can make such papers:** see the ticked chapters' questions **without options**, tick the ones wanted and get **one paper** made of them (75 questions at most); or ask for a **random mock** of N questions.

**Matched.** After every JEE Main shift, the questions of that shift that matched JE Live's own questions are shown side by side: the JEE Main question, and under it the question of ours it matched. Open to everyone, signed in or not. A signed-in student attempts all of ours in one **real paper** ("Attempt all matched"); a person without an account is asked to sign up first. On Home, the All India series card gives its place to the Matched card as soon as the first shift is published; for its remaining days the series is a bar right under that card.

**Misfire** (Part 4). Every wrong or left question of a finished paper, to be solved again. **It is the website's own**; the app shows it as it comes. The website agent checks six points so the two stay the same. New in version 5: **Offline Misfire** (Part 4.7), the phone's own practice mock of those questions, also without internet; and the **Misfire Mock** (Part 4.8), the website's paper of them, built in the app and waiting for the website's switch.

**Rapid Fire in a browser** (Part 5). The app's game also runs in any browser from the app's own server. **It is the app's**; the website only links to it.

**One account** (Part 6). Signing up or signing in, in the app or on the website, is the same account: the website's. **It already works so**; the website keeps its sign-in doors and its student ids as they are.

**Working together** (Part 7). Every door of the website the app uses, how the app's server reaches the website, and how a change to a door is agreed. An app in a student's phone cannot be changed without a new build, so the website must know what the app reads.

## 0.2 Where things stand on 28 Nov 2026

| What | State | Waits for |
| --- | --- | --- |
| Student Choice: Home tile, first screen, chapter list, chapter search, the ticked chapters' whole tests | **Works.** The app's server in production has it since 26 Nov 2026 (the screens: see the note under this table) | nothing |
| Student Choice: a chapter's questions without options, one paper of ticked questions | Built in the app, **closed** (shown under "Jald aa raha hai") | the website: doors A, B and C (Part 1.6) |
| Student Choice: random mock | Built in the app, **closed** | the website: doors A and C |
| Whole chapter tests timed by the 80 / 60 / 40 ratio, three hours at most | **Not true yet**: every chapter test has 60 minutes | the website: new minutes on 81 sets (Part 1.8) |
| Dream College meter never counts a chapter test or a Student Choice paper | **Works** in the app | the website: `test_kind` "choice" on made papers (Part 1.9) |
| Matched: public pages, sign-up sheet, the way back after sign-in, Home card, sign-in bar, the JEE question under ours | **Built.** In production the list is **empty** and the card is **off** | the website and the super admin: the admin page, the real paper, two public doors (Part 2.4) |
| Matched card on Home and the bar on the sign-in screen | **Off in production:** no shift is published. They come on by themselves **when the first shift is published**, and on **28 Jan 2027** (India time) at the latest | the first published shift (Part 2.6) |
| The first-shift rule of the card, and the All India bar under the Matched card | **In production's server since the Publish of 26 Nov 2026** (live at 14:40 UTC). The bar is a screen: a phone shows it with an app build made after that Publish | new app builds (whether one was made was not checked by the app side) |
| Student Choice's new colours (dark-red top cards, glossy subject tabs) and a made paper's subject minutes that add up to its time | **Published on 26 Nov 2026** (Part 1.2). Screens: with an app build made after that Publish | new app builds |
| Misfire | **Works:** the app shows the website's own Misfire, plus paper-wise tabs | the website: the checks of Part 4.4 |
| Offline Misfire: the phone's own practice mock of Misfire questions, also with no internet | **Built and checked on the preview on 28 Nov 2026**, and in the owner's Publish of that day. Screens: with an app build made after it | nothing from the website (Part 4.7) |
| Misfire Mock made by the website | **Built on the preview on 28 Nov 2026, shut:** no student sees it while door A does not say `"misfire": true`. The app's side of the switch reaches production with the owner's next Publish | the website: Part 4.8 |
| Rapid Fire in a browser (`…/api/arena` on the app's server) | **Works** in production, from the newest copy (built on 27 Nov 2026). Its icons are drawn in production | nothing; the website: a link (Part 5.3) |
| A made-up sample is never shown outside the app's own workspace | **Built on 27 Nov 2026** (Part 2.12); in the owner's Publish of 28 Nov 2026 | nothing |
| One account for the website and the app | **Works:** the app signs up and signs in only through the website's own doors | nothing new; the website keeps those doors (Part 6.3) |
| The website's doors the app uses (Part 7) | **Listed and checked against the app's code** when this book is built | the website: read Part 7.4 before changing one |



"In production" here means: the app's own server in production answers these addresses (checked on 28 Nov 2026, Part 3.7). The owner published on 26 Nov 2026 (live at 14:40 UTC; the one before at 05:33 UTC the same day), with everything of version 3 of this book, and again on 28 Nov 2026, after Offline Misfire (Part 4.7) was built and before the Misfire Mock (Part 4.8) was. What production answers today is read when this book is built (the rows above and Part 3.7). The Misfire Mock's switch on the app's server reaches production with the next Publish. **Screens reach a student only with a build:** a phone keeps the screens of the build installed on it until a newer build is installed. Whether an app build was made after that Publish was not checked by the app side.

## 0.3 Who does what

| Who | Student Choice | Matched |
| --- | --- | --- |
| **The website agent** (builds jeelive.ai) | Three doors: A the switch, B a chapter's questions without options, C make the paper (Part 1.6). New minutes on the chapter-wise sets (Part 1.8). `test_kind` on results and on the My Tests list (Part 1.9) | The super admin's "Matched" page (2.4a). One real paper per shift (2.4b). Two public read doors (2.4c) |
| **The super admin** (runs jeelive.ai) | Nothing new today. Publishing or hiding a chapter-wise test changes Student Choice within a few minutes (Part 1.11). Later: the switch of door A | After every JEE Main shift: enter the matched questions, check them, make the paper, publish (Part 2.8). Publishing the first shift is what puts Matched on Home; the card also has a switch |
| **The app side** | Built; the app's server is deployed (the screens: Part 0.2). Follows the website by itself: no new app build when a door opens | Built; the app's server is deployed (the first-shift rule: in production since the Publish of 26 Nov 2026; the All India bar: with app builds made after it, Part 0.2). Copies the website's shifts every 2 minutes: no new app build when shifts arrive |
| **The owner** | Decides the open points of Part 3.8 | Decides the open points of Part 3.8 |

| Who | Misfire (Part 4) | Rapid Fire in a browser (Part 5) | One account (Part 6) |
| --- | --- | --- | --- |
| **The website agent** | The six checks of Part 4.4; tells the app side the `kind` of Student Choice and Matched papers. Offline Misfire: nothing to build (Part 4.7). The Misfire Mock: Part 4.8, then the switch | A "Rapid Fire" button / link. Nothing else: never a copy of its code | Keeps the sign-in doors, their fields and every student's `id` as they are (Part 6.3) |
| **The super admin** | Nothing | Nothing | Deletes a website account by hand when the app's owner panel lists a request (Part 6.5) |
| **The app side** | Shows the website's Misfire. Its one practice of its own is Offline Misfire, on the phone, never a website paper (Part 4.7). The Misfire Mock is built and waits for the switch (Part 4.8) | Owns it; builds the browser copy again after screen changes | Uses only the website's accounts |
| **The owner** | — | Publishes the app | — |

**Working together (Part 7).** The website agent reads Part 7.4 before changing a door that Part 7.2 lists, and tells the app side first when the change is not a free one. The app side keeps the list true: the build of this book checks it against the app's code.

## 0.4 Twenty-eight things nobody must get wrong

1. **Student Choice has no question bank of its own.** Its questions ARE the JEE Main chapter-wise questions. A chapter in Student Choice is a chapter-wise test of the website, under that test's own id. Do not build a second bank.
2. **A question listed for choosing never carries its options, its answer or its solution** (door B). Options appear only inside the paper.
3. **A made paper has at most 75 questions. Never 90.**
4. **Marking: right +4, wrong −1, left 0.**
5. **Time comes from the subjects:** every Mathematics question brings 3.2 minutes, Physics 2.4, Chemistry 1.6; the sum is rounded **up** to a whole minute (25 Maths = 80 min, 25 Physics = 60, 25 Chemistry = 40; 25 + 25 + 25 = 180). **A whole chapter test** follows the same ratio and is **never longer than 180 minutes** (Part 1.8); a made paper is not cut.
6. **The same `request_key` must give the same paper** (door C). A retry never makes a second paper.
7. **`test_kind` is exactly `"choice"`** on a made paper and on its result. The Dream College meter decides by it.
8. **A random mock is split exactly as Part 1.6 says** (equally; one or two left over go to Physics, then Chemistry). The app shows that split and its time to the student before the paper exists.
9. **Door A answers 200 (open) or 404 (closed). Never 401 or 403 to a signed-in student, never 5xx.** A 5xx there takes the whole of Student Choice down for every student until it stops.
10. **An answer is either plain JSON or the website's envelope `{ "data": …, "error": null, "meta": { "api_version": … } }`.** An envelope without `meta` is not opened, and the answer is then read as empty.
11. **Matched: never delete a published shift.** Take it back; publish it again to bring it back.
12. **Matched: `updated_at` changes on every edit, and the list and the shift's own document carry the same number.** Otherwise a correction never reaches the app, or the app's server reads that shift again and again.
13. **Pictures.** In a Matched shift: plain https links that open without sign-in and never expire. In door B: https links that open without cookies for at least 24 hours.
14. **Matched: the button "Attempt all matched" appears only when the shift has `paper_id` AND at least one of ours has `question_id`** (that question's id inside the paper).
15. **The Matched paper is marked +4 / −1** (the card on the shift says so and counts its marks as questions × 4), and timed by the rule of point 5.
16. **Subjects are written exactly `Physics`, `Chemistry`, `Mathematics`.** Anything else is shown without a subject and cannot be filtered.
17. **Every option of a question must have words, or none of its options is shown.** One missing option would move the letters.
18. **Samples stay on the preview.** Made-up shifts and made-up chapters are for the owner's eyes there only. Never write them into production. (Since 27 Nov 2026 the app's server also keeps this by itself: outside its own workspace it never shows one, Part 2.12.)
19. **The fields of the chapter-wise catalogue listed in Part 1.5 are in use.** Do not rename or drop one without telling the app side.
20. **The first real run is on a test setup.** The first door answered and the first shift published are the first true end-to-end runs: tell the app side before students see them.
21. **Misfire is the website's.** Nobody builds a second Misfire. Keep the `/my/misfire…` answers and the item id `<attempt id>:<question id>` as they are (Part 4).
22. **Rapid Fire is the app's.** The website links to `…/api/arena` and never copies Rapid Fire's code, cards or data (Part 5).
23. **One account.** An account made in the app IS a website account. Never a second user list; never a second account for one phone number (Part 6).
24. **A student's `id` never changes**, not on a PIN change, not ever: the app's coins, friends and ranks hang on it (Part 6.3).
25. **An API door never answers with a redirect or an HTML page.** The app's server does not follow a redirect, and an HTML page is never shown to a student. Trouble is said as JSON: a status, `error.message` in plain words, `Retry-After` when there is one (Part 7.3).
26. **Tell the app side before a door of Part 7.2 changes.** A new field is always safe. A renamed or removed field, another address or method, or another meaning of a status is not: phones keep old app builds for months (Part 7.4).
27. **Offline Misfire is the phone's; the Misfire Mock is the website's.** An Offline Misfire mock is never a set, an attempt or a result on the website (Part 4.7). A Misfire Mock always is one, with `test_kind` exactly `"misfire"` (Part 4.8). Neither may make a second Misfire item for a question that already has one.
28. **`"misfire": true` in door A only when all of Part 4.8 is ready.** The app opens Misfire's "Mock" tab on every phone within about 2 minutes of reading it.

## 0.5 How to read this book

- **Website agent:** Part 1.5 to 1.9 and 1.13 (Student Choice), Part 2.3 to 2.7 and 2.11 (Matched), **all of Parts 4, 5, 6 and 7** (Misfire, Rapid Fire in a browser, one account, working together), then Part 3 as a reference. The JSON in the grey boxes is also in the `examples` folder of the download; every example in it was run through the app server's own code when this book was built.
- **Super admin:** Part 0, Part 1.2 (what students see), Part 1.11, Part 2.2, above all **Part 2.8 (what to do after every shift)** and **Part 2.9 (mistakes and what the student would see)**, and Part 6.5 (deleting an account).
- **Pictures** are from the app's web preview, at a phone's size, taken on 26 Nov 2026. The Matched pictures show three **made-up sample shifts** that exist on the preview only. The pictures of question picking and the random mock (Part 1.7) show **made-up questions marked "(Sample)"**, with the browser answering in place of the website's doors that do not exist yet.

## 0.6 Words used in this book

| Word | Meaning |
| --- | --- |
| the website | jeelive.ai and its API (`https://jeelive.ai/api/…`), where papers, attempts, results and accounts live |
| the app | the JE Live phone app |
| the app's server | the app's own small server (`…/api/…` of the app). It passes the student's requests on to the website and adds a few read-only pages of its own (the chapters of Student Choice, the Matched pages, the switches) |
| a door | one address (endpoint) of the website's API |
| a set, a paper | one test on the website. A chapter-wise test is a set whose `test_kind` is `chapter` |
| an attempt | one student's go at a paper: started, saved, submitted, marked |
| the catalogue | the website's list of an exam's tests: `GET /api/exam-navigation/jee-main/catalogue` |
| a shift | one sitting of JEE Main: a day and a shift number. Its id is written `2027-01-25-s1` |
| ours | a question of JE Live's own (from the All India series, the chapter-wise tests and so on) that a JEE Main question matched |
| the envelope | the website's usual wrapper round an answer: `{ "data": …, "error": null, "meta": { "api_version": "1" } }` |
| to tick | to choose a chapter or a question by tapping it |
| the ratio | the owner's time rule: 25 Maths = 80 minutes, 25 Physics = 60, 25 Chemistry = 40 |
| Offline Misfire | the app's practice mock of a student's own Misfire questions, kept on the phone; also with no internet (Part 4.7) |
| a Misfire Mock | a paper the website makes of a student's own open Misfire questions, `test_kind` `"misfire"` (Part 4.8) |
| a new build | a new version of the app that students must install. Everything in this book is made so that the website's future work needs **no** new build. The app side's own changes (Part 0.2) do need the owner's Publish, and the screens need new builds |

# Part 1 — Student Choice

## 1.1 What it is, and what the owner decided

Student Choice is **another way to reach the JEE Main chapter-wise questions the website already has**. In the owner's words: the questions come from the JEE Main chapter-wise bank, not from anywhere else; Student Choice is "only navigation and choices".

| Decision of the owner | Date | Where it shows |
| --- | --- | --- |
| The questions are the JEE Main chapter-wise questions. No separate bank. A chapter = a chapter-wise test, under that test's own id | 26 Nov 2026 | Part 1.5 |
| Until the website can make a paper: **"Abhi chapter tests, baad mein sawaal chunna"** (chapter tests now, question picking later) | 26 Nov 2026 | Part 1.2 and 1.7 |
| A made paper has **at most 75 questions** (not 90) | 26 Nov 2026 | Part 1.4 |
| Marking **+4 / −1**; the list for choosing shows **only the question, never its options** | 26 Nov 2026 | Part 1.4 and 1.6 |
| Time: **80 minutes for 25 Maths questions, 60 for 25 Physics, 40 for 25 Chemistry**. "Isi ratio me time dena. Bata bhi dena" (give time in this ratio, and tell the student) | 26 Nov 2026 | Part 1.4; the app shows the rule on Student Choice's first screen |
| A large Student Choice paper (68 questions or more) counts for the Dream College meter: **"Nahi, kabhi nahi"** (never) | 26 Nov 2026 | Part 1.9 |
| A search box so that a student finds any chapter by name in seconds | 26 Nov 2026 | Part 1.3 |
| Whole chapter tests follow the 80 / 60 / 40 ratio too, **once the website allows changing their time** | 26 Nov 2026 | Part 1.8: a change on the website, not done yet |
| Colour at the top only: the top card of each Student Choice screen **dark red like the result page's score card**, the subjects as **glossy tabs** (Physics red, Chemistry amber, Maths teal); the cards below stay white | 26 Nov 2026 | Part 1.2 |

What Student Choice must never do: make up an attempt, a result or a paper on the phone. Every test a student takes from Student Choice is a real paper of the website, with the website's own player, deadline, result, analysis and solutions.

## 1.2 What a student gets today, screen by screen

- Picture `shots/s01_home_tile.jpg`: 1. Home: the STUDENT CHOICE tile, fourth in "Practice"
- Picture `shots/s02_landing.jpg`: 2. First screen of Student Choice
- Picture `shots/s03_soon_and_time.jpg`: 3. The same screen, lower: what is coming, and the time rule
- Picture `shots/s04_chapters.jpg`: 4. Step 1: the chapters of one subject

**1. Home.** Under "Practice", after the website's exam tiles (JEE MAIN, BITSAT, COMEDK today), the fourth tile is **STUDENT CHOICE**, with the line "apne chapters chuno" and a NEW mark. It opens Student Choice. Only a signed-in student sees Home.

**2. First screen** ("Student Choice", small line "Apne chapters, apni marzi").

- At the top, a **dark-red card** like the result page's score card (a gloss, a glass shine from corner to corner, a coloured edge): the small line "JEE MAIN · CHAPTER-WISE SAWAAL", the title "Apne chapters, apni marzi.", one sentence, and three facts read from the website, in clear glass chips: how many chapters, how many questions, the marking. On 28 Nov 2026: **81 chapters, 3750 sawaal, +4 / −1**.
- The cards below stay white; their icons are red on soft pink.
- Card **"Chapters chuno"**: "Physics, Chemistry aur Maths ke chapters tick karo. Har chune chapter ka poora test milega: ek-ek karke do." When chapters are already ticked it adds "3 chapters chune hue hain".
- Card **"Aapke chapter tests"** (only when at least one chapter is ticked): straight to the ticked chapters' tests.
- Card **"Jald aa raha hai"** (coming soon): "Sawaal khud chunna" and "Random mock", each with a sentence, and "Khulte hi yahin dikhega, app update kiye bina."
- **"Banaye hue paper ka time"**: Physics 25 sawaal = 1 hr; Chemistry 25 sawaal = 40 min; Maths 25 sawaal = 1 hr 20 min; and the sentence "Har sawaal apne subject ka time laata hai, isliye chhota paper chhota time paata hai. 25 + 25 + 25 sawaal = 3 hr. Yeh time aapke banaye paper par lagega (sawaal chunna aur random mock). Poore chapter test ka time uske page par likha hota hai (abhi 1 hr)."
- Pulling the screen down reads everything again.

**3. Step 1 of 2, "Chapters chuno".**

- A search box on top ("Chapter ka naam likho…"), Part 1.3.
- Three **glossy tabs**, built like My Tests' tabs: Physics (red), Chemistry (amber), Maths (teal). Each shows how many chapters are ticked in it.
- One row per chapter, in the website's order: its number and name ("1. Units, Dimensions and Errors") and "68 sawaal · 64 MCQ · 4 numerical". A tap ticks or unticks it. A ticked row wears its subject's colour: a soft wash, a coloured edge and a coloured tick. Chapters can be ticked in one, two or all three subjects, as many as wanted.
- The bar at the bottom: "3 chapters chune" and "3 tests · 165 sawaal", and the red button **"Tests dekho"**. With nothing ticked the button is off and the bar says "Kam se kam ek chapter tick karo".
- The ticks are kept **on the phone, for that account**: they are still there the next day. They are not sent to any server (Part 1.10).

- Picture `shots/s05_search.jpg`: 5. Search: "therm" finds chapters in two subjects
- Picture `shots/s06_search_near_spelling.jpg`: 6. A wrong spelling still finds the chapter
- Picture `shots/s07_chapters_ticked.jpg`: 7. Three chapters ticked, one in each subject
- Picture `shots/s08_chapter_tests.jpg`: 8. Step 2: the ticked chapters' tests, with the student's own state

**4. Step 2 of 2, "Aapke chapter tests".**

- On top, the same **dark-red card**: "STUDENT CHOICE · AAPKE CHAPTER TESTS", "3 chapter tests · 2 ho gaye" (how many of them this student has finished), and three counts side by side: **Ho gaye** (finished), **Chal rahe** (in progress), **Baaki** (left). Until the student's states have been read, the counts show "–".
- The tests under their subject, in the website's order. Each row: the chapter's number in a circle of its subject's colour, its name, then "68 Q · 60 min · +4/-1 · 272 marks" (all four read from the website), and the student's own state of that test:

| The student's state of that test (from the website) | The row shows | A tap opens |
| --- | --- | --- |
| never started | **Start** (red) | the paper's usual page (picture 9) |
| started, not submitted | "In progress" and **Resume** (yellow, as My Tests' "In progress") | the attempt, where it was left |
| submitted | "Completed" and **Result** (baby pink, as My Tests' "Completed") | its result |

- A test that is in progress is always resumed, never started a second time: until the student's states have been read, a row cannot be tapped.
- **"Chapters badlo"** at the bottom goes back to step 1.

- Picture `shots/s09_paper_page.jpg`: 9. "Start" opens the paper's usual page. From here nothing is special

**5. From "Start" on it is an ordinary paper.** The page says "JEE MAIN · CHAPTER PRACTICE", the number of questions, the minutes, the marks, the marking, "Before you start", and "Start attempt". Then the 60-second get-ready, the player, submit, the result, the analysis, the solutions. It is **the same set** as in the website's Chapter-wise section: the same attempt shows in My Tests (in progress, completed) and in the Chapter-wise list, on the website and in the app.

**The colours, in short.** Only the top card of each screen, the subject tabs, a ticked row, a test's number and its button carry colour; every other card stays white. They are the app's own (its theme, the result page's dark red, My Tests' tabs and badges): the website does not need to copy them. On a phone that cannot keep up, the app's Smooth Mode draws the shine plain.

**What Student Choice adds today,** plainly: one place where the chapters of all three subjects can be ticked and searched, a list of only the student's own chapters with where he stands in each, and the time rule told in advance. It adds no new paper and no new question.

## 1.3 The chapter search

The box on step 1 looks in **all three subjects at once**, with every letter typed, on the phone itself (no request is made). Each result says its subject. A tap on a result ticks it; the typed name and the keyboard stay, so several can be ticked one after another; dragging the list puts the keyboard away.

| What is typed | Finds | How |
| --- | --- | --- |
| `therm` | Thermal Properties of Matter, Thermodynamics, Thermodynamics and Thermochemistry | a word of the name starts so |
| `p block` | p-Block Elements | every typed word must fit a word of the name |
| `goc`, `ktg`, `wep`, `aod` | General Organic Chemistry, Kinetic Theory of Gases, Work Energy and Power, Application of Derivatives | the first letters of the name's words (small words such as "and", "of" may be left out) |
| `com` | Centre of Mass, Momentum and Collisions | the first letters start so |
| `organic`, `pblock` | General Organic Chemistry, p-Block Elements | the letters are inside the name (3 letters or more) |
| `3d`, `shm`, `emi`, `emw`, `nlm`, `pnc` | Three-Dimensional Geometry, Oscillations, Electromagnetic Induction, Electromagnetic Waves, Laws of Motion, Permutations and Combinations | six short names students use that the titles do not hold. **They are written in the app**: if the website renames those chapters, these six simply stop finding them |
| `kinametics`, `probablity`, `matrix` | Kinematics, Probability, Matrices and Determinants | a near spelling, **only when nothing fits as typed**: the same first letter, one slip (two in a long word). The list is then headed "Is naam ka chapter nahi mila. Milte-julte naam:" |
| `zzzz` | nothing: "Is naam ka chapter nahi mila", "Spelling dekh lo, ya subject se chapter chuno." and the button "Search hatao" | |

Results are ordered best fit first; equal fits stay in the website's order (Physics, Chemistry, Maths). The count line reads "3 chapters mile · teeno subjects mein dhoonda". The search uses only the chapters' **titles** as the website gives them: a new chapter is searchable as soon as it is in the list.

Checked on 28 Nov 2026: 55 searches against the 81 real chapter names all give the expected chapters (`node /app/tests/choice_search_check.js`); 2000 searches take about 33 thousandths of a second on the build machine.

## 1.4 The owner's rules for a made paper

These rules apply to a paper **made** in Student Choice (chosen questions, or a random mock). The app shows them to the student before the paper exists; **the website must apply them** when it makes the paper (door C).

| Rule | Value |
| --- | --- |
| Most questions in one paper | **75** |
| Fewest | 1 chosen question; a random mock: 3 (one a subject) |
| Right answer | **+4** |
| Wrong answer | **−1** |
| Left | 0 |
| Full marks | questions × 4 |
| Time a Mathematics question brings | **3.2 minutes** (25 questions = 80 minutes) |
| Time a Physics question brings | **2.4 minutes** (25 questions = 60 minutes) |
| Time a Chemistry question brings | **1.6 minutes** (25 questions = 40 minutes) |
| The paper's time | the sum over all its questions, rounded **up** to a whole minute |
| Order of the paper | Physics, then Chemistry, then Mathematics |

Worked examples (every row was computed by the app server's own function when this book was built):

| The paper | Minutes its questions bring | The paper's time | Full marks |
| --- | --- | --- | --- |
| 25 Physics + 25 Chemistry + 25 Maths | 60 + 40 + 80 = 180 | **3 hr** | 300 |
| 10 Physics + 10 Chemistry + 10 Maths | 24 + 16 + 32 = 72 | **1 hr 12 min** | 120 |
| 25 Maths | 80 | **1 hr 20 min** | 100 |
| 25 Physics | 60 | **1 hr** | 100 |
| 25 Chemistry | 40 | **40 min** | 100 |
| 5 Physics | 12 | **12 min** | 20 |
| 1 Chemistry | 1.6, rounded up to 2 | **2 min** | 4 |
| 1 Physics + 1 Chemistry + 1 Maths | 2.4 + 1.6 + 3.2 = 7.2, rounded up to 8 | **8 min** | 12 |
| 3 Physics + 2 Chemistry + 2 Maths | 7.2 + 3.2 + 6.4 = 16.8, rounded up to 17 | **17 min** | 28 |
| 20 Physics + 15 Chemistry + 10 Maths | 48 + 24 + 32 = 104 | **1 hr 44 min** | 180 |
| 75 Maths | 240 | **4 hr** | 300 |

How the app writes a time: under an hour "45 min"; from an hour "1 hr", "1 hr 12 min", "3 hr".

The website may **lower** the top of 75 (door A, `max_questions`), may add a top per subject (`max_per_subject`), and may send other minutes per question (`minutes_per_question`); the app obeys and shows them. It can never raise the top above 75: a larger number is ignored.

## 1.5 What the app reads from the website today

Nothing new is needed for what works today. The app's server reads the website's own chapter-wise catalogue:

```
GET https://jeelive.ai/api/exam-navigation/jee-main/catalogue?kind=chapters&subject=Physics&q=&page=1
        (and subject=Chemistry, subject=Mathematics; every page of each)
```

- **Who reads:** the app's server, as the signed-in student who asked (only that student's `access_token` cookie is sent). The answer is the same for every student, so one student's read serves all the others.
- **How often:** every page of the three subjects (8 reads today: a page holds 12 chapters) plus one read of door A, **at most once every two minutes for each process of the app's server**, however many students are browsing. Nothing is read while nobody is in Student Choice. Phones never make these reads for the chapter list.
- **What is kept:** the list is held in the server's memory for two minutes (and answers for up to two minutes more while a fresh copy is read behind). Nothing about any student is kept from it. Nothing is written to any database.

**The fields in use.** Of every row of `items`, and of the page itself:

| Field | Used for | A row is left out, or shown differently, when |
| --- | --- | --- |
| `id` | the chapter's id = the set's id; "Start" opens `/set/<id>` | it is not 6 to 80 letters, digits, `-` or `_` |
| `test_kind` | must be `chapter` | it is anything else: left out |
| `chapter_subject` | must be the subject that was asked for | it differs: left out |
| `status` | must be `published` | it is anything else: left out |
| `live_enabled` | must not be `false` | it is `false`: left out |
| `title` | the chapter's name. A leading chapter number ("01 ") is taken off | it is empty: left out |
| `chapter_number` | the number shown before the name (1 to 999) | missing: the name is shown without a number |
| `count` | "68 sawaal" (a whole number, 1 to 5000) | 0 or missing: left out |
| `types.mcq`, `types.integer` | "64 MCQ · 4 numerical" | both missing: that part of the line is not shown |
| `rules.minutes` | "60 min" on the test's row. A value that is not whole is shown rounded **down** (163.2 shows 163) | missing: "Untimed" |
| `rules.correct`, `rules.wrong`, `maximum` | "+4/-1 · 272 marks" on the test's row | one is missing: the chapter can be ticked but has **no test row** in step 2 |
| `pages` (of the page) | how many pages to read (12 at most for a subject) | missing: only the first page is read |
| `attempt` (of a row) | read **by the phone**, with the student's own session, from the same list: `{ id, status, resumable, result_available }` → Start, Resume or Result | missing or `null`: "Start" |

- The app shows a subject's first 120 chapters at most.
- **Half a list is never shown:** if one page of one subject fails, the student sees "Sawaal abhi load nahi ho paaye. Dobara try karo." with a retry, not two subjects out of three.
- If the first page of a subject answers **404** (the owner has hidden the chapter-wise section), that subject has no chapters. With all three empty the first screen says "Chapters abhi nahi mile".
- The student's own state of the tests is read by the phone from `GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=…&q=&page=…`, only for the pages that hold ticked chapters: the same request the app's Chapter-wise screen makes.

## 1.6 What stays closed until the website builds it: three doors

**Why the app cannot do it alone.** The website hands out a paper's questions only inside a started attempt (`GET /attempts/<id>`, `/attempts/<id>/assets/…`), and it has no way to make a set out of a list of question ids. Checked with a signed-in student on 26 Nov 2026: `sets/<id>/questions`, `sets/<id>/preview`, `my/sets/<id>/questions`, `choice/bank` and `choice/chapters/<id>/questions` all answer 404. The questions, their cut pieces, their keys and their solutions all exist on the website; only the doors are missing.

All three doors are for a **signed-in student**, with the website's usual cookie session. An answer may be plain JSON or the usual envelope; **an envelope must carry `meta`** (point 10 of Part 0.4).

| Door | Address | Opens in the app |
| --- | --- | --- |
| **A** the switch | `GET /api/choice/bank?exam=jee-main` | says which ways are open: "Sawaal khud chuno" (`pick`) and "Random mock" (`random`) |
| **B** a chapter's questions | `GET /api/choice/chapters/<set id>/questions?page=1` | the list of questions without options (needed for `pick`) |
| **C** make the paper | `POST /api/choice/papers` | "Paper banao" and "Random mock banao" |

Doors A and C are enough for the random mock. Question picking needs all three.

### Door A — the switch

```
GET /api/choice/bank?exam=jee-main
```

```json
{
  "pick": true,
  "random": true,
  "max_questions": 75,
  "max_per_subject": null,
  "minutes_per_question": { "Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2 }
}
```

| Field | Type | Meaning | When it is missing or wrong |
| --- | --- | --- | --- |
| `pick` | true or false | doors B and C (mode `pick`) work: the app opens "Sawaal khud chuno" | not `true`: closed |
| `random` | true or false | door C (mode `random`) works: the app opens "Random mock" | not `true`: closed |
| `max_questions` | whole number 1 to 75 | lowers the top of a made paper | missing, 0, more than 75, or not a whole number: 75 |
| `max_per_subject` | whole number 1 to 75, or `null` | a top for every subject (for example 25) | missing or `null`: no top per subject |
| `minutes_per_question` | three numbers, each 0.5 to 10 | minutes a question of each subject brings | a subject missing or out of range: that subject's default (2.4, 1.6, 3.2) |

Rules of door A:

- **404 = both ways closed.** That is today's answer, and it is a correct answer. Each way can be opened on its own; send `false` to close one again.
- **Never 401 or 403 to a student whose session is good, and never 5xx.** On 401 or 403 the app renews the student's session and asks once more; if the door refuses again the student is told to sign in again. On 5xx the whole chapter list fails with "Sawaal abhi load nahi ho paaye. Dobara try karo.", for every student, also for the chapter tests that work today.
- **Do not send `subjects`.** The chapters come from the chapter-wise catalogue (Part 1.5). (If a list `subjects` is sent, in the shape of the first note of 26 Nov, its chapters are shown **instead of** the catalogue's, their ids go to door B, and both ways count as open unless `pick` or `random` is sent as `false`. That list has no tests, so step 2's chapter tests disappear with it. Not recommended.)
- It is read by the app's server only, at most once every two minutes for each server process (Part 1.5), never by phones.
- **How fast a change shows:** the app's server holds the answer for two minutes. A student who opens Student Choice, or pulls the first screen down, usually has the new ways within 2 to 4 minutes of the door changing. No new app build, for every app version that contains Student Choice.

### Door B — a chapter's questions, without options

```
GET /api/choice/chapters/<id of the chapter-wise test>/questions?page=1
```

The id is the set id of the chapter-wise test (the `id` of its catalogue row). Example: `4b4ff9a5-85ba-5325-83cd-60f2994acc57` is "01 Units, Dimensions and Errors". The questions are that test's questions, in its order.

```json
{
  "chapter": { "id": "4b4ff9a5-85ba-5325-83cd-60f2994acc57", "title": "Units, Dimensions and Errors", "subject": "Physics" },
  "pages": 2,
  "items": [
    {
      "id": "q-4b4ff9a5-001",
      "number": 1,
      "type": "mcq",
      "text": "The dimensional formula of Planck's constant is",
      "stem": []
    },
    {
      "id": "q-4b4ff9a5-002",
      "number": 2,
      "type": "integer",
      "text": "",
      "stem": [
        { "url": "https://files.jeelive.example/pieces/q-4b4ff9a5-002-q1.webp?expires=1800950400&sig=EXAMPLE", "w": 506.5, "h": 47 }
      ]
    }
  ]
}
```

| Field | Type and limit | Meaning |
| --- | --- | --- |
| `chapter.id`, `chapter.title`, `chapter.subject` | the same id; text to 120 characters; exactly Physics, Chemistry or Mathematics | named on the first page; the app shows the catalogue's own title |
| `pages` | whole number, 1 to 6 | how many pages there are. **At most 6 pages are read and at most the first 300 questions of a chapter are kept**, so 50 questions a page is a good size (the largest chapter today has 103). Without `pages` only page 1 is read |
| `items[].id` | 6 to 80 letters, digits, `-` or `_` | the question's id. **Stable.** It is sent back to door C. A question whose id does not fit is left out |
| `items[].number` | whole number 1 to 9999 | its number in the chapter test; shown as "Q 1" |
| `items[].type` | `mcq` or `integer` | shown as MCQ or NUMERICAL. Anything else is taken as `mcq` |
| `items[].text` | to 3000 characters; maths in `$…$` | a typed question's words. `""` for a picture question. Longer text is cut at 3000 |
| `items[].stem` | list of `{ "url", "w", "h" }`, at most 4 | a picture question: **only the question's own piece or pieces**, in order |
| `stem[].url` | https, no spaces, **at most 900 characters** | a longer link is cut at 900 characters and will not open |
| `stem[].w`, `stem[].h` | positive numbers (print points, as in a paper's pieces: the file holds 2 pixels a point) | both or neither. Without them the app measures the picture when it arrives (the list then moves a little) |

Rules of door B:

- **Never send options, the answer, the solution, or anything else about the question.** The app's server drops everything except the fields above, but it must not leave the website at all.
- A question needs `text` or at least one stem picture; otherwise it is left out.
- A question that appears twice (the same id on two pages) is listed once.
- **Picture links:** https; they must open on a phone **without cookies** (a signed link is right); they must stay good for **at least 24 hours** after the answer is given. WebP if there is one. The app's server keeps a chapter's answer for 5 minutes (and may answer from it for up to 5 more while it reads a fresh copy), and every student is served from that copy; a phone keeps it while the app is open.
- The answer is the same for every student. The app's server reads it as the asking student (only the `access_token` cookie is sent).
- **404** for a chapter that does not exist or has no question to choose: the student sees "Is chapter ke sawaal abhi yahan nahi khul paaye. Doosra chapter chuno, ya thodi der mein dobara dekho."
- 401 or 403: the app renews the session and asks once more. 5xx: "Sawaal abhi load nahi ho paaye. Dobara try karo."

### Door C — make the paper

```
POST /api/choice/papers
```

It is the student's own request. It arrives through the app's server exactly like `POST /api/sets/<id>/start` does today: the student's cookies, `Content-Type: application/json`, **no CSRF header and no browser Origin**. Whatever lets `sets/<id>/start` through for the app must let this through.

Chosen questions:

```json
{ "exam": "jee-main", "request_key": "0b6f6d2e-6c1c-4c0e-9a35-0c5f4f0d9b11", "mode": "pick",
  "question_ids": ["<id>", "<id>", "<id>"] }
```

Random mock:

```json
{ "exam": "jee-main", "request_key": "5d2a0a6e-0e0b-4f61-8a76-2f0f3c1f7a55", "mode": "random", "count": 30 }
```

Answer, 200 or 201 (plain, or in the envelope with `meta`):

```json
{ "set_id": "<the new paper's id>" }
```

`set_id` must be 6 to 80 letters, digits, `-` or `_`; anything else and the student is told "Paper ban nahi paaya. Dobara try karo." The app then opens `GET /api/my/sets/<set_id>` (the paper's page) and the student starts it with `POST /api/sets/<set_id>/start`, as for any paper.

**What the app has already made sure of before it asks**

| Mode | The app guarantees |
| --- | --- |
| `pick` | 1 to 75 ids (or to `max_questions`), no id twice, never more than `max_per_subject` of one subject; every id came from door B; the ids are sorted: Physics, Chemistry, Mathematics; inside a subject by the catalogue's chapter order, then by the question's number |
| `random` | `count` is a whole number from 3 to the smaller of `max_questions` and three times what the smallest subject can give (its question count, or `max_per_subject`) |
| both | `request_key` is a fresh UUID for each new ask. **Every retry of the same ask** (the same ids, or the same count, while the student stays on that screen) **carries the same key** |

The website must check all of it again: the app is not to be trusted.

**What the website does**

**`request_key`.** The same key = the same paper. A retry (slow network, double tap) returns the **same** `set_id` and never makes a second paper.

**Checks.** 1 to 75 questions. Mode `pick`: every id is a question of a published JEE Main chapter-wise test; no id twice. Mode `random`: `count` from 3 to 75. `max_per_subject` if one is set. **A request that fails a check: 422**, with one plain sentence in `error.message` (or `detail`): the app shows that sentence to the student as it is.

**Mode `pick`.** The paper has exactly these questions. Order: Physics, then Chemistry, then Mathematics; inside a subject as in a JEE Main paper (single-correct first, then numerical). The order the app sends is a fine order to keep otherwise.

**Mode `random`.** Split `count` equally over Physics, Chemistry and Mathematics; one or two left over go to Physics, then Chemistry. **The app shows this split and its time to the student before the paper is made, so the website must use exactly this split:**

| `count` | Physics | Chemistry | Mathematics | The paper's time | Full marks |
| --- | --- | --- | --- | --- | --- |
| 3 | 1 | 1 | 1 | 8 min | 12 |
| 4 | 2 | 1 | 1 | 10 min | 16 |
| 5 | 2 | 2 | 1 | 12 min | 20 |
| 10 | 4 | 3 | 3 | 24 min | 40 |
| 11 | 4 | 4 | 3 | 26 min | 44 |
| 15 | 5 | 5 | 5 | 36 min | 60 |
| 30 | 10 | 10 | 10 | 1 hr 12 min | 120 |
| 31 | 11 | 10 | 10 | 1 hr 15 min | 124 |
| 45 | 15 | 15 | 15 | 1 hr 48 min | 180 |
| 50 | 17 | 17 | 16 | 2 hr | 200 |
| 60 | 20 | 20 | 20 | 2 hr 24 min | 240 |
| 74 | 25 | 25 | 24 | 2 hr 57 min | 296 |
| 75 | 25 | 25 | 25 | 3 hr | 300 |

Inside a subject pick at random across **all** its chapter-wise chapters, about 4 single-correct to 1 numerical (JEE Main: 20 + 5), as far as the questions allow.

**If a subject has no published chapter-wise test at all,** the app splits the count over the subjects that have one (two subjects: equally, one left over goes to the first; the fewest it then asks for is 2). The website must split the same way, or refuse with 422 and a plain sentence. With all three subjects present, as today, the table above is the whole rule.

**The paper** is an ordinary set, owned by this student, not listed in any catalogue, never shown to another student:

| Attribute | Value |
| --- | --- |
| `title` | something short, for example "Student Choice · 30 Q · 26 Nov". It is shown in My Tests and on the result |
| `exam` | "JEE Main" |
| `test_kind` | **`"choice"`**, exactly. The paper's page then says "Student Choice", and the Dream College meter never counts it (Part 1.9) |
| `rules` | `{ "correct": 4, "wrong": -1, "skipped": 0, "minutes": <the rule of Part 1.4, rounded up> }` |
| `count`, `maximum` (count × 4), `subjects`, `types` | as for every set |
| every question | keeps its own subject (the player's subject tabs and the analysis use it), its pieces, its answer key and its solution, exactly as in the chapter-wise test it came from |

**From here it is a normal paper:** the paper's page, attempt, autosave, deadline, result, analysis, solutions, AI solutions, My Tests (in progress, completed), retry.

**What the student sees for each answer of door C**

| The website answers | The student sees |
| --- | --- |
| 200 or 201 with a good `set_id` | the new paper's page. After a paper of chosen questions, all ticks are cleared |
| 404 or 405 (today) | "Paper banana abhi jeelive.ai se jud raha hai. Thodi der mein yeh khul jayega; aapke chune sawaal yahin rahenge." The ticks stay |
| 422, 409, 429 or another 4xx with `error.message` | that sentence, as written by the website. The ticks stay |
| 401 | the app renews the session and sends the same request again, with the same key |
| 5xx, or a technical text | "The website is not answering right now. Your saved work is safe. Please try again in a moment." The ticks stay |
| 200 without a usable `set_id` | "Paper ban nahi paaya. Dobara try karo." |

**Suggestions from the app side** (these are **not** the owner's rules; settle them with the owner before building):

- In a random mock, prefer questions this student has not had in an earlier Student Choice paper.
- A limit on how many papers a student may make in a day (for example 20): answer 429 with a plain sentence.
- Papers that were made and never started could be removed after a few days; a started one stays like any attempt.
- A paper belongs to one student, so a leaderboard has nobody to compare with; leave it out, as for chapter practice.

## 1.7 How the closed ways open by themselves, and what the student then sees

The screens are already in the app. The day door A answers `"pick": true` or `"random": true`, they appear without a new build:

- the first screen's title becomes "Apna paper, apni marzi." and its small line "Apna paper khud banao";
- the facts become "75 sawaal tak", "+4 / −1", "time subject ke hisaab se";
- with `pick`: the card "Chapters chuno" becomes **"Sawaal khud chuno"**, step 2 becomes the question list, and the card "Aapke chapter tests" is no longer shown on the first screen (the chapter tests stay in the Chapter-wise section);
- with `random`: the card **"Random mock"** appears;
- "Jald aa raha hai" keeps only what is still closed, and goes away when both are open.

The four pictures below were taken with **the browser answering in place of doors A and B** (made-up questions marked "(Sample)"); nothing was changed on any server, and no paper was made.

- Picture `shots/s10_later_landing.jpg`: 10. First screen with both ways open
- Picture `shots/s11_later_random_mock.jpg`: 11. Random mock: only the number is asked
- Picture `shots/s12_later_questions.jpg`: 12. Step 2: questions without options
- Picture `shots/s13_later_review.jpg`: 13. "Paper banao": the paper's make-up before it is made

**Random mock** (a sheet on the first screen). "Bas ginti batao. Sawaal Physics, Chemistry, Maths se barabar aur mile-jule aayenge, JEE Main ke paper ki tarah." A number box that starts at 30, quick buttons 15, 30, 45, 60, 75, the split subject by subject with each subject's time, the whole paper's questions and time, and one line: "Poore 120 marks · sahi +4, galat -1, chhoda 0 · time 1 hr 12 min". A number outside the range shows "3 se 75 ke beech ginti likho." and the button is off. **"Random mock banao"** sends door C; the new paper's page opens.

**Sawaal chuno** (step 2 of 2, after ticking chapters).

- Glossy tabs for the subjects that have a ticked chapter (Physics red, Chemistry amber, Maths teal), each with how many questions are chosen in it; under them pills for that subject's ticked chapters.
- The chapter's name and "Maths · 12 sawaal · yahan sirf sawaal hain, options paper mein milenge".
- One card per question: a tick, "Q 1", MCQ or NUMERICAL, and the question's words or its picture. **No options.** A tap ticks it.
- At the end of a chapter: "Agla chapter: …".
- The bar: "7 / 75 sawaal", "17 min · 28 marks", and **"Paper banao"**.
- The 76th tap is refused: "75 sawaal ho gaye: ek paper mein isse zyada nahi. Koi hatao, tab naya chuno." With a top per subject: "Physics ke 25 sawaal ho gaye. Koi hatao, tab naya chuno."
- Unticking a chapter in step 1 takes its chosen questions out too.
- **"Paper banao"** opens the sheet "Aapka paper": the make-up subject by subject, "Poore 28 marks. Sahi jawab +4, galat -1, chhoda hua 0. Paper Physics, Chemistry, Maths ke order mein banega; result, analysis aur solutions har paper ki tarah milenge.", then **"Haan, paper banao"** (sends door C) and "Aur sawaal chuno".
- The chosen questions are kept while the app is open (going back and forth between the steps loses nothing); they are not kept after the app is closed.

**The make-up adds up (since 26 Nov 2026).** The paper's minutes are shared out between its subjects in whole minutes that add up to exactly the paper's time: each subject first gets its whole minutes, then the minute or two left over go to the subjects with the largest remainders (picture 13: 7 + 3 + 7 = "17 min"; before, each row was rounded up on its own and showed 8 + 4 + 7). The total is what door C must give; the rows are only how the app shows it.

## 1.8 Whole chapter tests by the 80 / 60 / 40 ratio, three hours at most: a change on the website

The owner asked: "Make whole chapter tests follow the 80/60/40 time ratio once the website allows changing their time". Shown what the ratio alone gives (some tests longer than four hours), he added on 26 Nov 2026: **a longest time of three hours.** **The app cannot do it.** An attempt's deadline is the website's, taken from the set's `rules.minutes`. **Not done yet:** on 28 Nov 2026 every JEE Main chapter-wise test has 60 minutes, whatever its length.

**What to change on the website**

- For every published JEE Main chapter-wise set (`test_kind` "chapter"):
  `rules.minutes` = (the set's `count`) × (the minutes a question of its `chapter_subject` brings), rounded **up** to a whole minute, **and never more than 180**. Physics 2.4, Chemistry 1.6, Mathematics 3.2.
- Keep it true: when a chapter's question count changes, its minutes change with it.
- A new attempt gets the new time. **An attempt that is already running keeps the deadline it has.**
- A whole number of minutes, please: the app's pages show `rules.minutes` as it is.

**What it gives, chapter by chapter** (counts as on 26 Nov 2026; today's 60 minutes → by the rule; where the three hours hold a test back, what the ratio alone would give is in brackets):

### Physics: 2.4 minutes a question (30 tests, 1250 questions)

| No. | Chapter | Questions | Today | By the rule |
| --- | --- | --- | --- | --- |
| 1 | Units, Dimensions and Errors | 68 | 60 min | **164 min** |
| 2 | Kinematics | 66 | 60 min | **159 min** |
| 3 | Laws of Motion | 46 | 60 min | **111 min** |
| 4 | Work, Energy and Power | 42 | 60 min | **101 min** |
| 5 | Centre of Mass, Momentum and Collisions | 17 | 60 min | **41 min** |
| 6 | Rotational Motion | 60 | 60 min | **144 min** |
| 7 | Gravitation | 40 | 60 min | **96 min** |
| 8 | Mechanical Properties of Solids | 29 | 60 min | **70 min** |
| 9 | Fluids | 31 | 60 min | **75 min** |
| 10 | Surface Tension | 22 | 60 min | **53 min** |
| 11 | Thermal Properties of Matter | 16 | 60 min | **39 min** |
| 12 | Thermodynamics | 52 | 60 min | **125 min** |
| 13 | Kinetic Theory of Gases | 41 | 60 min | **99 min** |
| 14 | Oscillations | 27 | 60 min | **65 min** |
| 15 | Waves and Sound | 30 | 60 min | **72 min** |
| 16 | Electrostatics | 76 | 60 min | **180 min** (183) |
| 17 | Capacitors | 30 | 60 min | **72 min** |
| 18 | Current Electricity | 55 | 60 min | **132 min** |
| 19 | Magnetic Effects of Current | 62 | 60 min | **149 min** |
| 20 | Magnetism and Matter | 7 | 60 min | **17 min** |
| 21 | Electromagnetic Induction | 34 | 60 min | **82 min** |
| 22 | Alternating Current | 35 | 60 min | **84 min** |
| 23 | Electromagnetic Waves | 41 | 60 min | **99 min** |
| 24 | Ray Optics and Optical Instruments | 74 | 60 min | **178 min** |
| 25 | Wave Optics | 49 | 60 min | **118 min** |
| 26 | Dual Nature of Matter and Radiation | 45 | 60 min | **108 min** |
| 27 | Atoms | 35 | 60 min | **84 min** |
| 28 | Nuclei | 30 | 60 min | **72 min** |
| 29 | Semiconductors and Logic Gates | 56 | 60 min | **135 min** |
| 30 | Experimental Skills | 34 | 60 min | **82 min** |

### Chemistry: 1.6 minutes a question (24 tests, 1250 questions)

| No. | Chapter | Questions | Today | By the rule |
| --- | --- | --- | --- | --- |
| 1 | Mole Concept and Stoichiometry | 68 | 60 min | **109 min** |
| 2 | Atomic Structure | 52 | 60 min | **84 min** |
| 3 | Classification of Elements and Periodicity | 45 | 60 min | **72 min** |
| 4 | Chemical Bonding and Molecular Structure | 65 | 60 min | **104 min** |
| 5 | Thermodynamics and Thermochemistry | 59 | 60 min | **95 min** |
| 6 | Chemical Equilibrium | 31 | 60 min | **50 min** |
| 7 | Ionic Equilibrium | 28 | 60 min | **45 min** |
| 8 | Redox Reactions | 16 | 60 min | **26 min** |
| 9 | Solutions | 47 | 60 min | **76 min** |
| 10 | Electrochemistry | 56 | 60 min | **90 min** |
| 11 | Chemical Kinetics | 56 | 60 min | **90 min** |
| 12 | p-Block Elements | 54 | 60 min | **87 min** |
| 13 | d- and f-Block Elements | 72 | 60 min | **116 min** |
| 14 | Coordination Compounds | 88 | 60 min | **141 min** |
| 15 | Purification and Characterisation of Organic Compounds | 57 | 60 min | **92 min** |
| 16 | General Organic Chemistry | 103 | 60 min | **165 min** |
| 17 | Hydrocarbons | 58 | 60 min | **93 min** |
| 18 | Haloalkanes and Haloarenes | 46 | 60 min | **74 min** |
| 19 | Alcohols, Phenols and Ethers | 32 | 60 min | **52 min** |
| 20 | Aldehydes, Ketones and Carboxylic Acids | 60 | 60 min | **96 min** |
| 21 | Amines and Diazonium Salts | 57 | 60 min | **92 min** |
| 22 | Biomolecules | 56 | 60 min | **90 min** |
| 23 | Principles Related to Practical Chemistry | 42 | 60 min | **68 min** |
| 24 | Miscellaneous (beyond the current syllabus) | 2 | 60 min | **4 min** |

### Mathematics: 3.2 minutes a question (27 tests, 1250 questions)

| No. | Chapter | Questions | Today | By the rule |
| --- | --- | --- | --- | --- |
| 1 | Sets and Relations | 38 | 60 min | **122 min** |
| 2 | Functions | 54 | 60 min | **173 min** |
| 3 | Basic Algebra (Inequalities, Modulus, Logarithms) | 13 | 60 min | **42 min** |
| 4 | Trigonometric Ratios, Identities and Equations | 40 | 60 min | **128 min** |
| 5 | Complex Numbers | 48 | 60 min | **154 min** |
| 6 | Quadratic Equations | 49 | 60 min | **157 min** |
| 7 | Permutations and Combinations | 53 | 60 min | **170 min** |
| 8 | Binomial Theorem | 50 | 60 min | **160 min** |
| 9 | Sequences and Series | 75 | 60 min | **180 min** (240) |
| 10 | Straight Lines | 50 | 60 min | **160 min** |
| 11 | Circles | 44 | 60 min | **141 min** |
| 12 | Parabola | 23 | 60 min | **74 min** |
| 13 | Ellipse | 36 | 60 min | **116 min** |
| 14 | Hyperbola | 28 | 60 min | **90 min** |
| 15 | Limits | 29 | 60 min | **93 min** |
| 16 | Statistics | 29 | 60 min | **93 min** |
| 17 | Probability | 51 | 60 min | **164 min** |
| 18 | Matrices and Determinants | 86 | 60 min | **180 min** (276) |
| 19 | Inverse Trigonometric Functions | 24 | 60 min | **77 min** |
| 20 | Continuity and Differentiability | 41 | 60 min | **132 min** |
| 21 | Application of Derivatives | 37 | 60 min | **119 min** |
| 22 | Indefinite Integration | 15 | 60 min | **48 min** |
| 23 | Definite Integration | 73 | 60 min | **180 min** (234) |
| 24 | Area under Curves | 45 | 60 min | **144 min** |
| 25 | Differential Equations | 70 | 60 min | **180 min** (224) |
| 26 | Vector Algebra | 67 | 60 min | **180 min** (215) |
| 27 | Three-Dimensional Geometry | 82 | 60 min | **180 min** (263) |

**What the rule does**

- Of the 81 tests, **70 get longer**, **11 get shorter**, and none stays at 60 minutes.
- **7 tests are held at 3 hours**; the ratio alone would give them more: Matrices and Determinants (4 h 36 min); Three-Dimensional Geometry (4 h 23 min); Sequences and Series (4 h 00 min); Definite Integration (3 h 54 min); Differential Equations (3 h 44 min); Vector Algebra (3 h 35 min); Electrostatics (3 h 03 min).
- **So no chapter test is longer than a full mock (180 minutes).** The student's session, the autosave and the attempt's picture links (`GET /attempts/<id>/assets/links`) need to last no longer than they already do for a full mock, plus the get-ready minute.
- **11 tests become shorter than today's 60 minutes:** Miscellaneous (beyond the current syllabus) 4 min; Magnetism and Matter 17 min; Redox Reactions 26 min; Thermal Properties of Matter 39 min; Centre of Mass, Momentum and Collisions 41 min; Basic Algebra (Inequalities, Modulus, Logarithms) 42 min; Ionic Equilibrium 45 min; Indefinite Integration 48 min; Chemical Equilibrium 50 min; Alcohols, Phenols and Ethers 52 min; Surface Tension 53 min.
- 12 chapter tests have 68 questions or more. (These are the ones an older app version counted for the Dream College meter: Part 1.9.)

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

- The new colours (26 Nov 2026) on a real phone and on a slow Android phone. They were walked in the web preview only, 390 and 320 points wide, with no sideways scrolling.

**Known small things, not changed**

- The six short search names are fixed in the app (Part 1.3).
- The Student Choice tile has no switch: taking it off Home needs a new app build (Part 3.4).

**Changed on 26 Nov 2026:** the subjects' minutes in a paper's make-up now add up to exactly the paper's time (Part 1.7); before, they could add up to a minute or two more.

# Part 2 — Matched

## 2.1 What it is, and what the owner decided

After a JEE Main shift, some of its questions turn out to be the same as, or very close to, questions JE Live had already given its students. **Matched shows them**: the JEE Main question, and under it the question of ours it matched, with where ours was asked and how close the match is.

| Decision of the owner | Date | Where it shows |
| --- | --- | --- |
| When the All India series is over, Home's All India card turns **by itself** into the card "Matched: JEE Mains questions matched with ours" | 25 Nov 2026 | Part 2.6 |
| **Sooner than that:** the card turns to Matched **on the day of JEE Main's first shift itself**, as soon as that shift is published. For the series' remaining days the All India series is **a simple bar right under the Matched card**, above the four exam boxes | 26 Nov 2026 | Part 2.2 (picture 10), Part 2.6 |
| The list shows the JEE question and ours on one card, **without options**, with the tabs "Question" and "Solution" | 25 Nov 2026 | Part 2.2 |
| Real counts and what matched. "Attempt all matched" opens a **real paper** of the website; nothing is made up or marked on the phone | 26 Nov 2026 | Part 2.4b |
| Looking is open to everyone. **Attempting needs an account:** a person without one is asked to sign up (free) and comes back to the same shift | 26 Nov 2026 | Part 2.2 |
| The look: sun yellow into orange, a golden cup, fireworks | 26 Nov 2026 | the pictures below |

**Not built, and not part of the app:** the machine or the people who compare a JEE Main paper with our questions. The app shows whatever the super admin publishes. What counts as a match is the academic team's judgement; the pages are public, so a claim made there is made to everyone.

## 2.2 What a student sees, screen by screen

The pictures show **three made-up sample shifts** (22 and 24 Jan 2027) that exist on the app's preview only.

- Picture `shots/m08_home_card.jpg`: 1. Home with the Matched card in the All India card's place
- Picture `shots/m01_signin_bar.jpg`: 2. The sign-in screen with the Matched bar
- Picture `shots/m02_matched_page.jpg`: 3. The Matched page: month, day, shift
- Picture `shots/m03_shift_top.jpg`: 4. A shift: its count, its paper, the button

**1. Home's card** (only while the switch of Part 2.6 is on). Under the title "Matched with JEE Main" (with "view all"), in the place of the All India series card: "JEE MAIN", how many shifts ("3 SHIFTS"), the word MATCHED, the line "JEE Mains questions matched with ours", the cup and the fireworks, two facts ("11 questions matched", "24 Jan · Shift 1, latest shift") and the button **"See matched questions"**. Before the first shift is published it says "JEE Main ke har shift ke baad yahan woh questions aayenge jo hamare questions se match hue." and the button reads "Open Matched".

**The All India series under the card** (picture 10; built on 26 Nov 2026, in app builds made after the Publish of that day). While the series still has days left, a dark bar sits right under the Matched card, above the four exam boxes. Its small line reads "ALL INDIA SERIES · DAY 46 / 50"; its big line says what the day has for the student: "Live today · Start today's test", "In progress · Resume", "Completed · View result", "Completed · Results at 11:59 PM", "Awaiting paper", "Starts closed", "Day ended"; before the series begins "50 DAYS" and "Starts 9 Dec". **One tap does what the big card's button did:** today's test page, the running attempt, its result, or the series hub. From the day after the series' last day the bar is gone, and the series and its practice archive are reached from "all india series" under Explore on Home (that chip is always there). An app version from before the bar shows the Matched card alone.

**2. The sign-in screen** shows a Matched bar while the same switch is on: MATCHED, the line, and "Dekho". A person without an account can open Matched from it.

**3. The Matched page** ("Matched", small line "JEE Main"). Open to everyone.

- The top card: how many questions matched in how many shifts ("11 questions matched in 3 shifts").
- When shifts of more than one month exist: a pill for each month with its count ("Jan 2027", "Apr 2027"). With one month, its name.
- The days, newest first ("SUN, 24 JAN"); under a day its shifts in order (1, then 2).
- A shift's row: "SHIFT 1", "6 of 75 matched" with a bar, and a chip for each subject with its count ("Physics 2", "Chemistry 2", "Maths 2"). Without `asked` it reads "6 matched", with no bar.
- Before the first shift: "Pehla shift hote hi yahan aayega", "JEE Main ke har shift ke baad yahan woh questions dikhenge jo hamare questions se match hue: unka question, aur uske saamne hamara."

**4. A shift's page** ("Shift 1 · Fri, 22 Jan", small line "JEE MAIN 2027": the day, the shift and the year are read from the shift's id). Open to everyone.

- **The top card.** The big count: "6 of 75 questions matched with ours" with a bar. Then the paper's three facts: **"7 questions"**, **"28 marks"**, **"+4 / −1 marking"**. The 7 is how many of **our** questions are in the shift's paper: one JEE question may have matched more than one of ours (here 6 JEE questions matched 7 of ours). The marks are that number × 4.
- The line above the button: signed out "Dekhna sabke liye khula hai. Paper attempt karne ke liye free account banao."; signed in "Hamare woh sawaal jo JEE Main mein match hue, ek paper mein. Timer, result, analysis aur solutions: har paper ki tarah."
- The button **"Attempt all matched"**. A shift that has no paper yet shows no facts and no button, only "Is shift ke matched sawaalon ka paper jald yahan khulega."
- "KAUN SA SAWAAL KISSE MATCH HUA", then pills "All 6", "Physics 2", "Chemistry 2", "Maths 2" (only when the shift has more than one subject), then one card per matched question, in the order of the JEE paper.

- Picture `shots/m04_question_card.jpg`: 5. One matched question: the JEE question, the seal, ours
- Picture `shots/m05_solution_tab.jpg`: 6. The Solution tab opens both solutions
- Picture `shots/m06_signup_sheet.jpg`: 7. Without an account: the sheet
- Picture `shots/m07_signup_screen.jpg`: 8. Sign-up, with the note; afterwards back on the shift

**5. A matched question's card.**

- The top strip: "Q4" (its number in the JEE paper), the subject, the chapter.
- Two tabs: **Question** and **Solution**.
- The panel "JEE MAIN 2027 · Fri, 22 Jan · Shift 1": the JEE Main question, its words and pictures, **without options**.
- The seal between the two: how close the match is, in capitals ("SAME CONCEPT", "SAME QUESTION"). With no tag it reads "MATCHED".
- The panel "HAMARA QUESTION · AITS Day 12 · Q 7": our question, and where it was asked, **without options**. When the JEE question matched more than one of ours, each has its own seal and panel (four at most).
- **Solution** opens, for the JEE question and for ours: "SAHI JAWAB" (the right option's words, or the answer as written) and "SOLUTION" (the worked solution and its pictures). A question that came with only its answer says "Iska likha hua solution abhi nahi hai; sahi jawab upar diya hai."; one that came with neither says "Is question ka solution abhi nahi aaya."
- A tap on a picture makes it twice as wide (it then slides sideways); a picture that did not load says "Picture load nahi hui. Dobara try karo".

**6. "Attempt all matched".**

- **Without an account:** the sheet "Sign up karke attempt karo": "Matched sawaal dekhna sabke liye khula hai. Inhe paper ki tarah attempt karne ke liye (timer, result, analysis aur solutions ke saath) free account banao: sirf mobile number aur PIN." with **"Free account banao"** and "Mera account hai · Sign in". The sign-in screen then carries the note "Account banao ya sign in karo. Uske baad Matched paper attempt kar sakte ho." **After signing up or in, the student is back on the same shift**, and taps the button again.
- **Signed in:** the shift's real paper opens: its usual page ("JEE MAIN · MATCHED PAPER" when the paper's kind is `matched`), "Start attempt", the 60-second get-ready, the player, submit, the result, the analysis, the solutions, My Tests. Nothing about this paper is special in the app, except one thing:

- Picture `shots/m09_under_ours_in_solutions.jpg`: 9. In the paper's solutions: the JEE question our question matched, with its own answer and solution
- Picture `shots/m10_home_series_bar.jpg`: 10. Home while the All India series still has days: its bar under the Matched card, then the four exam boxes. (Taken before the series began, so the bar says when it starts)

**7. The JEE question under ours.** In the player, under each of our questions, a panel "JEE MAIN 2027 MEIN AAYA · 22 Jan · Shift 1 · Q4" shows the JEE Main question it matched, **without options and without its answer**. In the solutions after submitting, the same panel also shows the JEE question's answer and solution (picture 9). An ordinary paper shows nothing of this and asks nothing extra (Part 2.7).

## 2.3 One document per shift: every field

Everything Matched shows comes from **one document per shift**. The website publishes it (Part 2.4c); the app's server copies it and hands the app only what the app can draw. **Anything that does not fit is left out and not counted; it can never break a screen.**

```json
{
  "id": "2027-01-25-s1",
  "asked": 75,
  "updated_at": 1800860400,
  "paper_id": "b7c1d2e3-4f50-4a61-9b72-8c93d0e1f2a3",
  "items": [
    {
      "n": 12,
      "subject": "Physics",
      "chapter": "Kinematics",
      "jee": {
        "text": "A particle is projected with speed $u = 20\\,\\text{m/s}$ at $30^\\circ$ above the horizontal. Taking $g = 10\\,\\text{m/s}^2$, its time of flight is",
        "options": ["1 s", "2 s", "3 s", "4 s"],
        "correct": "B",
        "solution": "$T = \\dfrac{2u\\sin\\theta}{g} = \\dfrac{2 \\times 20 \\times \\frac{1}{2}}{10} = 2\\,\\text{s}$."
      },
      "ours": [
        {
          "text": "A ball is thrown with speed $u = 40\\,\\text{m/s}$ at $30^\\circ$ above the horizontal ($g = 10\\,\\text{m/s}^2$). Its time of flight is",
          "options": ["2 s", "4 s", "6 s", "8 s"],
          "correct": 2,
          "solution": "$T = \\dfrac{2u\\sin\\theta}{g} = \\dfrac{2 \\times 40 \\times \\frac{1}{2}}{10} = 4\\,\\text{s}$.",
          "source": "AITS Day 12 · Q 7",
          "tag": "Same concept",
          "question_id": "q-aits12-007"
        }
      ]
    },
    {
      "n": 41,
      "subject": "Chemistry",
      "chapter": "Mole Concept and Stoichiometry",
      "jee": {
        "text": "The number of moles of oxygen atoms in 0.5 mol of $\\text{Al}_2(\\text{SO}_4)_3$ is ____.",
        "answer": "6",
        "solution": "One formula unit has $3 \\times 4 = 12$ oxygen atoms, so $0.5 \\times 12 = 6$ mol."
      },
      "ours": [
        {
          "text": "The number of moles of oxygen atoms in 0.25 mol of $\\text{Al}_2(\\text{SO}_4)_3$ is ____.",
          "answer": "3",
          "solution": "$0.25 \\times 12 = 3$ mol.",
          "source": "AITS Day 31 · Q 52",
          "tag": "Same concept",
          "question_id": "q-aits31-052"
        },
        {
          "text": "",
          "images": [ { "url": "https://files.jeelive.example/matched/2027-01-25-s1/q41-ours-2.png", "w": 1200, "h": 380 } ],
          "answer": "(C)",
          "solution_images": [ { "url": "https://files.jeelive.example/matched/2027-01-25-s1/q41-ours-2-solution.png", "w": 1200, "h": 520 } ],
          "source": "Chapter test · Mole Concept · Q 14",
          "tag": "Same question",
          "question_id": "q-chap-mole-014"
        }
      ]
    },
    {
      "n": 68,
      "subject": "Mathematics",
      "chapter": "Probability",
      "jee": {
        "text": "Two fair dice are thrown. The probability that the sum of the numbers is 7 is",
        "options": ["$\\dfrac{1}{6}$", "$\\dfrac{1}{12}$", "$\\dfrac{5}{36}$", "$\\dfrac{7}{36}$"],
        "correct": 1,
        "solution": "6 of the 36 equally likely results add up to 7, so the probability is $\\dfrac{6}{36} = \\dfrac{1}{6}$."
      },
      "ours": [
        {
          "text": "Two fair dice are thrown. The probability that the sum of the numbers is 8 is",
          "options": ["$\\dfrac{1}{6}$", "$\\dfrac{5}{36}$", "$\\dfrac{1}{9}$", "$\\dfrac{7}{36}$"],
          "correct": "B",
          "solution": "5 of the 36 results add up to 8, so the probability is $\\dfrac{5}{36}$.",
          "source": "AITS Day 44 · Q 70",
          "tag": "Same concept",
          "question_id": "q-aits44-070"
        }
      ]
    }
  ]
}
```

(The ids and the picture links in the example are made up.)

**The shift**

| Field | Type and limit | Meaning | When it is missing or wrong |
| --- | --- | --- | --- |
| `id` | `YYYY-MM-DD-sN`: the exam day in India, `-s`, the shift number 1 to 9 | the day, the shift number and the year shown everywhere are read from it | not exactly this shape (`2027-1-25-s1`, `2027-01-25-S1`, `…-s10`), or not a real date: **the whole shift is ignored** |
| `asked` | whole number 1 to 300 | how many questions the shift's paper had (75) | missing, or smaller than the number of matched questions: "18 matched" is shown instead of "18 of 75 matched", with no bar |
| `updated_at` | unix seconds | the moment of the last change. **Change it on every edit** | missing: the app's server reads the shift again every 10 minutes instead of only when it changed |
| `paper_id` | 6 to 80 letters, digits, `-` or `_` | the id of the shift's real paper (Part 2.4b) | missing, or no question of ours carries a `question_id`: no button, "paper jald yahan khulega" |
| `items` | list, the first 150 are read | **only the questions that matched**. The app counts them: that count is the "18" of "18 of 75" | empty: the shift shows "0 of 75 matched" and "Is shift mein koi match nahi mila" |

**One matched question** (an entry of `items`)

| Field | Type and limit | Meaning | When it is missing or wrong |
| --- | --- | --- | --- |
| `n` | whole number 1 to 300 | the question's number in the JEE paper: "Q12" on the card, and the order of the cards | missing: the card has no number and comes after the numbered ones, in the order written |
| `subject` | exactly `Physics`, `Chemistry` or `Mathematics` | the subject on the card, the pills, the chips on the shift's row | anything else ("Maths", "physics"): the question is shown and counted, but without a subject and outside every subject pill |
| `chapter` | text to 80 characters | shown next to the subject | missing: nothing is shown there |
| `jee` | a question (below) | the JEE Main question | missing, or it has neither words nor a picture: **the whole entry is left out and not counted** |
| `ours` | a list of 1 to 4 questions (below) | the question or questions of ours it matched | none that can be shown: **the whole entry is left out and not counted**. More than 4: the first 4 |

**A question** (the JEE one, and each of ours)

| Field | Type and limit | Meaning | When it is missing or wrong |
| --- | --- | --- | --- |
| `text` | to 6000 characters; maths in `$…$` (TeX), as in the website's typed questions | the question's words | longer text is cut. `""` is fine when there is a picture |
| `images` | list of `{ "url", "w", "h" }` or of plain links; the first 6 good ones | the question's pictures. `url`: **https**, no spaces, **to 600 characters**, opens **without sign-in**, **never expires**. `w`, `h`: whole numbers of pixels, both or neither | http, or a link with a space: that picture is dropped. A longer link is cut and will not open. Without `w` and `h` the page moves a little when the picture arrives |
| `options` | list of texts, to 6, each to 1500 characters | the options in order (A, B, C, D). **In the list they are never drawn**; they give the words of the right answer | **one empty option: none is kept**, and `correct` is lost with them. Then give the answer in `answer` |
| `correct` | the right option's place from 1 (`2`), or its letter (`"B"`) | which option is right | outside the options: ignored |
| `answer` | text to 300 characters | the right answer in words, for a question without option texts: `"8"`, `"(C)"` | missing, and no `correct`: no "SAHI JAWAB" |
| `solution` | to 6000 characters; maths in `$…$` | the worked solution | missing, and no solution picture: one of the two sentences of Part 2.2, point 5 |
| `solution_images` | as `images` | pictures of the solution | as `images` |

**Only on a question of ours**

| Field | Type and limit | Meaning | When it is missing or wrong |
| --- | --- | --- | --- |
| `source` | text to 80 characters | where ours was asked: "AITS Day 12 · Q 7" | missing: only "HAMARA QUESTION" |
| `tag` | text to 40 characters | how close the match is, shown in capitals on the seal: "Same question", "Same concept" | missing: the seal says "MATCHED" |
| `question_id` | 6 to 80 letters, digits, `-` or `_` | **this question's id inside the shift's real paper** (`questions[].id` of `GET /api/attempts/<id>`) | missing or wrong: the question is in the list, but it is not counted in the paper's "7 questions" and the JEE question does not appear under it in the player and the solutions |

A question needs `text` or at least one picture. **Both the JEE question and ours should come with their answer (`correct` or `answer`) and their solution (`solution` or `solution_images`):** every question has a Solution tab.

**What the app's server makes of the example above** (this is exactly what a phone receives from `GET /api/matched/2027-01-25-s1`; the questions are shortened here):

```
{"id": "2027-01-25-s1", "day": "2027-01-25", "shift": 1, "asked": 75, "matched": 3, "paper_id": "b7c1d2e3-4f50-4a61-9b72-8c93d0e1f2a3", "paper_questions": 4, "subjects": [{"name": "Physics", "n": 1}, {"name": "Chemistry", "n": 1}, {"name": "Mathematics", "n": 1}], "updated_at": 1800860400,
  "items": [
    … the first matched question …,
    {
      "n": 41,
      "subject": "Chemistry",
      "chapter": "Mole Concept and Stoichiometry",
      "jee": {
        "text": "The number of moles of oxygen atoms in 0.5 m…",
        "options": [],
        "images": [],
        "correct": null,
        "answer": "6",
        "solution": "One formula unit has $3 \\times 4 = 12$ oxyge…",
        "solution_images": []
      },
      "ours": [
        {
          "text": "The number of moles of oxygen atoms in 0.25…",
          "options": [],
          "images": [],
          "correct": null,
          "answer": "3",
          "solution": "$0.25 \\times 12 = 3$ mol.",
          "solution_images": [],
          "source": "AITS Day 31 · Q 52",
          "tag": "Same concept",
          "qid": "q-aits31-052"
        },
        {
          "text": "",
          "options": [],
          "images": [
            {
              "url": "https://files.jeelive.example/matched/2027-0…",
              "w": 1200,
              "h": 380
            }
          ],
          "correct": null,
          "answer": "(C)",
          "solution": "",
          "solution_images": [
            {
              "url": "https://files.jeelive.example/matched/2027-0…",
              "w": 1200,
              "h": 520
            }
          ],
          "source": "Chapter test · Mole Concept · Q 14",
          "tag": "Same question",
          "qid": "q-chap-mole-014"
        }
      ]
    },
    … the third matched question …
  ]
}
```

- `matched` = the entries that could be shown. `asked` is sent only when it is at least `matched`.
- `paper_id` is sent only when at least one of ours has a `question_id`; `paper_questions` = how many **different** `question_id` the shift has.
- `subjects` = the count for each of the three subjects, in the order Physics, Chemistry, Mathematics; a subject with none is left out.
- `correct` is sent as the option's place **from 0**; `qid` is the `question_id`.
- The list of all shifts (`GET /api/matched` of the app's server) is the same rows without `items`, newest first, with `total` = all matched questions of all published shifts. At most 200 shifts are listed.

## 2.4 What the website must have: three things

### 2.4a The super admin's page "Matched"

For every JEE Main shift the super admin enters (or imports) the questions of that shift that matched ours.

| On the page | What it is |
| --- | --- |
| The shift | the exam's day in India and the shift number (1 to 9). Its id is made from them: `2027-01-25-s1` |
| `asked` | how many questions the shift's paper had (75) |
| For each matched question | its number in the JEE paper; subject (one of the three, chosen from a list, not typed); chapter; the JEE Main question (words or pictures, its options if it has any, its right answer, its solution) |
| For each of ours it matched (1 to 4) | the question picked **from our own bank** (so that its id is known); where it was asked (`source`); how close the match is (`tag`); its answer; its solution |
| **Make the paper** | one button. It makes ONE ordinary paper of all our matched questions of the shift (2.4b), writes its id into the shift (`paper_id`) and each question's id inside that paper next to the question (`question_id`) |
| **Publish / take back** | a published shift is in the first door's list; a shift taken back leaves it. Nothing is deleted |
| **Home's card** | a switch with three positions: auto, on, off (Part 2.6) |

What the page should refuse or warn about **before** it lets a shift be published (each of these is silently dropped or shown wrongly by the app otherwise: Part 2.9):

- a subject that is not exactly one of the three;
- a JEE question or one of ours with neither words nor a picture;
- an option left empty while others are filled;
- a right answer that is not one of the options;
- a question with no answer at all, or with no solution (a warning);
- a picture that is not https, or does not open without sign-in (the page can try the link without cookies);
- more than 150 matched questions, more than 4 of ours for one question, text over the limits of Part 2.3;
- `asked` smaller than the number of matched questions;
- a paper that is missing, or one of ours without its `question_id` (a warning: that question is then only in the list).

And on every save of a published shift: **`updated_at` becomes the current time**, in the shift's document and in the list.

### 2.4b The real paper of a shift

An ordinary paper, like every mock. Nothing new is needed in the player or the result.

| Attribute | Value |
| --- | --- |
| Who can open it | **every signed-in student**: `GET /api/my/sets/<paper id>` answers for all of them, and `POST /api/sets/<paper id>/start` starts it, exactly like any other paper |
| `title` | for example "Matched · JEE Main 25 Jan 2027 · Shift 1" |
| `exam` | "JEE Main" |
| `rules` | **correct +4, wrong −1, skipped 0** (the shift's card says "+4 / −1" and counts the marks as questions × 4). `minutes`: the owner's rule by subject: every Mathematics question 3.2 minutes, Physics 2.4, Chemistry 1.6, the sum rounded up to a whole minute |
| `test_kind` | **`"matched"`** if a new kind is easy: the paper's page then says "Matched paper". Any existing kind also works, but the page then says what that kind says ("Full mock"; with `chapter`: "Chapter practice") |
| Catalogue | it need not be listed anywhere: the app opens it by its id |
| Its questions | all our matched questions of the shift, each once. Each keeps its subject, its pieces, its key and its solution |
| From there | attempts, autosave, deadline, result, analysis, solutions, My Tests: as for every paper |

**The one thing that matters most:** the id every question has **inside this paper** (`questions[].id` of `GET /api/attempts/<id>`, and the question ids of `GET /api/attempts/<id>/results`) must be written next to that question in the shift, as `question_id`. That is how the app finds the JEE Main question to show under it. It is also what switches the button on, and what the card counts as "7 questions". The attempt and the result must carry the paper's id as `set_id`, as they do for every paper today.

**Keep the paper and the shift in step.** If a matched question is added to a published shift later, either the paper gets it too (and the question its `question_id`), or it stays in the list only. Do not take a question out of a paper students have already attempted.

### 2.4c Two public read doors

No sign-in: the Matched pages are public. **The app's server reads them, not the phones.** Every 2 minutes it asks the first; it asks the second only for a shift that is new or has changed.

**The list**

```
GET /api/matched
```

```json
{
  "card": "auto",
  "shifts": [
    { "id": "2027-01-25-s2", "updated_at": 1800882000 },
    { "id": "2027-01-25-s1", "updated_at": 1800860400 }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `shifts` | **only the published shifts.** A list is required: with anything else the app's server changes nothing. Each entry: the shift's `id` and its `updated_at` (an entry may also be just the id) |
| `shifts[].updated_at` | **the same number as `updated_at` inside that shift's document.** The app's server compares the two: when they differ it reads the shift again |
| `card` | optional: `"auto"`, `"on"` or `"off"` = the super admin's switch for Home's card (Part 2.6). Any other value is ignored |

**One shift**

```
GET /api/matched/2027-01-25-s1          404 when it is not published
```

The document of Part 2.3 (`id`, `asked`, `updated_at`, `paper_id`, `items`).

Rules of the two doors:

- Plain JSON, or the usual envelope **with `meta`**.
- **Pictures in a shift:** plain https links that open **without sign-in** and **do not expire**. Not the signed links of a paper: the app's server keeps its copy of a shift until the shift changes. A question of ours that exists only as cut pictures: give its question picture or pictures in `images`, its answer in `answer`, and its solution picture or pictures in `solution_images`.
- Limits read by the app: 200 shifts, 150 matched questions a shift, 4 of ours for one question.
- Until the doors exist they answer 404 and nothing changes in the app. That is the state on 28 Nov 2026.

## 2.5 How the shifts reach the app

The app's server keeps its own copy of every shift, in its own database, so the Matched pages stay up and fast while the website is busy. One pass runs **every 2 minutes**, in every process of the app's server:

1. It asks the list (`GET /api/matched` of the website). If the answer is not a list of shifts (404, an error, something else), **nothing is changed** and what the app has keeps being shown.
2. For every shift of the list it decides whether to read the shift's document:

| The app's server reads a shift's document when | Otherwise |
| --- | --- |
| it does not have the shift yet | it is not read |
| it has it, but hidden (the shift was taken back and is published again) | |
| the list's `updated_at` differs from the one in its copy | |
| the list sends no `updated_at` and its copy is older than 10 minutes | |

3. **At most 20 shifts are read in one pass.** A first load of 50 shifts arrives over three passes (about 6 minutes).
4. A shift that was read is written into the copy as published. A document that is not a shift (a wrong id) is skipped and tried again on the next pass.
5. A shift the app's server has from the website, and the list **no longer names**, is **hidden** (never deleted). Publishing it again brings it back.
6. If the list carries `card`, that word is written as Home's card switch (Part 2.6).

Why point 12 of Part 0.4 matters: when a shift's own `updated_at` and the list's are not the same number, that shift looks changed on every pass. It is read again every 2 minutes for ever, and with more than 20 such shifts the ones further down the list are **never** read.

**How long a change takes to reach a student**

| Step | At most |
| --- | --- |
| the website's change is picked up by the next pass | 2 minutes |
| the app's server answers the phone from its own short memory | 1 minute (sometimes 2, when hardly anyone is asking) |
| the phone, or a cache on the way, holds the answer | 1 minute |
| **together** | **usually within 3 minutes, about 5 at the outside**. The student sees it on opening the page, on coming back to it, or on pulling it down |

Only shifts that came from the website are ever hidden by the copy. A shift written into the app's database by hand (as the preview's samples are) is left alone, unless the website publishes a shift with the same id: then the website's shift takes its place. **A sample is shown only by the app's own preview** (Part 2.12): a server in production never lists one.

## 2.6 Home's card and the sign-in bar: when they are on

One switch decides both: Home's Matched card (in the All India series card's place) and the Matched bar on the sign-in screen. **They are also the only ways into Matched:** with the switch at `off`, no student can reach the Matched pages from the app, even when shifts are published.

| The switch says | Meaning |
| --- | --- |
| `auto` | on **as soon as one shift is published** (the owner, 26 Nov 2026: on the day of JEE Main's first shift itself). "Published" means the shift is in the app server's list (`GET /api/matched` of the app's server), so about 5 minutes after the super admin publishes it. **And in any case from the day after the All India series' last day**, India time, also with no shift: the app's server reads that day from the website's own schedule (`last_date` of `GET /api/series/all-india-jee`) every 15 minutes and remembers it. On 28 Nov 2026 the website says the series runs **9 Dec 2026 to 27 Jan 2027**, so with no shift at all the card comes on at 00:00 on **28 Jan 2027**. If the only published shift is taken back while the series still runs, the All India card comes back |
| `on` | on now, whatever is published and whatever the dates are |
| `off` | never, also when shifts are published |

**The All India series while Matched has its place.** For the series' remaining days it is a bar right under the Matched card (Part 2.2, picture 10). There is no switch for the bar: the app shows it while the series' own `today` is not past its `last_date` (both from `GET /api/series/all-india-jee`), and drops it the day after. If the website moves the series' last day, the bar and the card's latest day move with it.

**Where this rule is.** The first-shift rule and the bar were built on 26 Nov 2026. **The rule is in production's server since the owner's Publish of that day** (live at 14:40 UTC); the bar is a screen, and a phone shows it with an app build made after that Publish. Before the exam session, ask the app side to confirm on production that publishing a shift turns the card.

**Who holds the switch,** strongest first:

1. **The super admin, through the website:** `card` in the list door (Part 2.4c). When the website sends it, the app's server takes it over on every pass (every 2 minutes).
2. **The last word written in the app's database** (the row `matched:card`). It stays in force when the website sends no `card`. The app side can write it by hand, signed `by: "owner"`; a `card` from the website overwrites it within 2 minutes. **A word that nobody signed counts only on the app's own preview** (the samples' switch is such a word, Part 2.12): in production it is passed over.
3. **The word in the app server's code:** `auto`. Used when nothing else is set, which is how production is meant to run.

**How fast a phone follows:** the app's server learns the switch within about 3 minutes, and a newly published shift within about 5. A phone asks when the app is opened, and again when it is brought back after half an hour or more; it remembers the last answer, so the right card is there from the first moment of the next launch, also without a network.

**Good to know**

- **With `auto` nothing has to be switched by hand:** publishing the first shift is what puts Matched on Home. If that shift is published late, the card turns late.
- **To put Matched on Home before any shift is published** (the card and the page then say that matches will appear after every shift, Part 2.2), set `on`.
- **If a new series is later run under the same address:** while a shift is published the Matched card stays, and the bar comes back for that series' days. With no shift published, `auto` shows the All India card again until that series ends.
- **A phone with an app version from before 26 Nov 2026's work** follows the same switch but has no bar: it shows the Matched card alone, and the series is reached from "all india series" under Explore.

## 2.7 The JEE question under ours, in the player and the solutions

- The phone keeps a small list of **papers it knows to be Matched papers**: the `paper_id` of every shift it has shown (Home's card, the Matched page, a shift's page), up to 300.
- When a paper is opened in the player or in the solutions and its id (`set_id` of the attempt or the result) is on that list, the phone asks the app's server once: `GET /api/matched/paper/<paper id>` → the published shift whose paper this is. For each question on screen it looks for the one of ours whose `question_id` is that question's id, and shows the JEE question that matched it.
- In the player: the JEE question without options and without its answer. In the solutions: with its answer and its solution.
- **An ordinary paper costs nothing:** its id is not on the list, so nothing is asked and nothing is shown.
- When two shifts name the same paper, the newer shift is used. When the shift is taken back, the panel is gone.
- **A limit to know:** a phone that has never shown Matched (a new phone that opens the paper straight from My Tests) does not know the paper is a Matched paper, and shows the paper without the panels until Home's card or a Matched page has been on its screen once.

## 2.8 The super admin's runbook

The exact buttons are the website's own (Part 2.4a). This is what has to be true, in order.

**Once, before the exam session**

1. The website's Matched page, the paper maker and the two doors have been run on a test setup together with the app side (Part 2.11). The first shift ever published is the first true end-to-end run.
2. Home's card (Part 2.6): **leave the switch at `auto`.** The owner decided on 26 Nov 2026 that Matched takes the All India card's place on the day of JEE Main's first shift: with `auto`, publishing the first shift does it, and the All India series stays as a bar under the card until its last day. Nothing is switched by hand. **Before the session, ask the app side to confirm that production has this rule** (it arrives with the owner's next Publish of the app; without it `auto` waits for 28 Jan 2027 and `on` would be needed).
3. With the owner: fix the wording of `source` and `tag` once, and keep to it (below).
4. The app side hides the preview's made-up sample shifts before the first real shift.

**After every JEE Main shift**

| Step | What to do | What must be true afterwards |
| --- | --- | --- |
| 1 | Open a new shift: the exam's day (India date) and the shift number | its id reads `2027-01-25-s1`: four digits, two, two, `-s`, one digit |
| 2 | Enter how many questions the paper had (`asked`: 75) | |
| 3 | For each question that matched: its number in the JEE paper, subject (from the list of three), chapter, the JEE question with its right answer and its solution | words or a picture; an answer; a solution |
| 4 | For each of ours it matched (1 to 4): pick it from our bank; write where it was asked and how close the match is; its answer and solution | the question is the right one from the bank; `source` and `tag` in the agreed wording |
| 5 | Go through the check list below for every question | |
| 6 | Press "Make the paper" | the paper has as many questions as there are different questions of ours in the shift; +4 / −1; its minutes follow the subject rule; every one of ours shows its `question_id` |
| 7 | Open the paper as a test student | the paper's page opens; the questions and their keys are right |
| 8 | Publish | the shift is in the first door's list |
| 9 | Look at it in the app within about 5 minutes | the row's count, every card (both tabs), the three facts on the top card, the button, the paper; the JEE question under ours in the solutions. **After the first shift of the session also:** close the app and open it again; Home shows the Matched card, and the All India bar under it |

**The check list for one matched question**

- The JEE question is word for word what was asked in that shift, with the right question number.
- Ours really is the question named in `source`, and the `tag` says honestly how close the two are.
- The subject is one of the three, from the list.
- Both questions have their right answer and their solution.
- Every option has words (or none is entered and the answer is written in `answer`).
- Every picture opens in a private browser window (no sign-in), and is a file that will stay where it is.
- Maths is written in `$…$` like in the website's typed questions.

**Wording to keep the same on every shift** (the app shows these as they are written)

| Field | Use | Length |
| --- | --- | --- |
| `source` | where ours was asked, the test and the question number: "AITS Day 12 · Q 7", "Chapter test · Kinematics · Q 14" | 80 characters |
| `tag` | how close, in two or three words. Shown in capitals on a yellow seal: "Same question", "Same concept" | 40 characters |

**Afterwards**

- **A correction:** change the shift and save. `updated_at` must change (the page does this by itself). The app shows the correction within about 5 minutes.
- **Taking a shift back:** unpublish it. It leaves the app within about 5 minutes. **Never delete it.** Publishing again brings it back.
- **Home's card:** `auto`, `on` or `off` on the same page. With `auto` the first published shift turns the card on by itself. A phone follows the next time the app is opened.

## 2.9 Mistakes, and what the student would see

| What went wrong | What the app shows |
| --- | --- |
| The subject is written "Maths", "physics", "PHY" | the question is shown and counted, but with no subject on its card, in no subject pill and in no subject chip |
| One option is left empty | none of that question's options is kept. If the right answer was given as an option's place, **the right answer is lost too**: no "SAHI JAWAB" unless `answer` is filled |
| `correct` names an option that is not there ("E" with four options) | no "SAHI JAWAB" unless `answer` is filled |
| A picture link is http, or has a space in it | that picture is not shown at all |
| A picture link needs sign-in, or has expired | "Picture load nahi hui. Dobara try karo" in place of the picture |
| A picture link is longer than 600 characters | it is cut and does not open |
| The JEE question has neither words nor a picture, or none of ours can be shown | **the whole question disappears** and the count drops ("6 of 75" becomes "5 of 75") |
| `asked` is smaller than the number of matched questions | "18 matched", without "of 75" and without the bar |
| More than 4 of ours for one question | the first 4 |
| More than 150 matched questions in a shift | the first 150 entries |
| `n` is missing | the card has no question number and comes after the numbered ones |
| The shift's id has another shape (`2027-1-25-s1`, `…-S1`, `…-s10`) | the shift is not shown at all |
| `paper_id` is there, but no question of ours has a `question_id` | no button: "Is shift ke matched sawaalon ka paper jald yahan khulega." |
| A `question_id` is not the question's id inside the paper | the button works, but the card's "7 questions" may be wrong, and the JEE question does not appear under that question in the player and the solutions |
| The paper is not marked +4 / −1 | the shift's card says "+4 / −1" and counts the marks as questions × 4; the paper's own page says otherwise |
| The paper is not open to every signed-in student | "Attempt all matched" leads to the paper's page with the website's error |
| `updated_at` was not changed after an edit | the edit does not reach the app |
| The list's `updated_at` and the shift's own are different numbers | the app's server reads that shift again every 2 minutes, for ever; with more than 20 such shifts, later ones are never read |
| A shift is published with no matched question | a row "0 of 75 matched", and on its page "Is shift mein koi match nahi mila" |
| Text longer than the limits of Part 2.3 | it is cut at the limit |
| A question has no solution | the Solution tab says "Is question ka solution abhi nahi aaya." (or, with only the answer, "Iska likha hua solution abhi nahi hai; sahi jawab upar diya hai.") |
| Two shifts name the same paper | the newer shift's questions are shown under that paper's questions |

## 2.10 What happens when…

| Situation | What happens |
| --- | --- |
| The website is slow or down | the Matched pages keep working: they are answered from the app server's own copy. New shifts and corrections wait until the website answers again |
| The website's list door answers 404, an error, or something that is not a list of shifts | nothing is changed in the app |
| The app's server restarts | nothing is lost: the shifts, the card's word and the series' last day are in its database |
| A shift is taken back while a student is reading it | on the next read: "Yeh shift ab yahan nahi hai." It is gone from the list |
| A person without an account taps "Attempt all matched" | the sign-up sheet; after signing up or in, back on the same shift |
| A link to a shift that is not published is opened | "Yeh shift ab yahan nahi hai." |
| The phone has no network | Home shows the card the phone last knew. A list read less than 10 minutes ago is shown; otherwise "Matched abhi load nahi ho paaya. Dobara try karo." |
| The first shift is published (or the series ends) while a student has the app open | Home changes when the student comes back to the app after half an hour or more, or opens it afresh: the phone asks for the switch again then |
| The card is on and no shift is published (`on`, or the series is over) | the card and the page say that matches will appear after every shift |
| The switch is `off` and shifts are published | nobody can reach Matched from the app (Part 2.6) |
| The only published shift is taken back while the series still runs (`auto`) | Home goes back to the All India card, at each phone's next app launch |
| The series' last day has passed | the All India bar under the Matched card is gone; the series and its archive are under Explore |
| A phone has an app version from before the All India bar | the Matched card alone; the series is under Explore |
| The paper is opened on a phone that never showed Matched | the paper works; the JEE questions are not shown under ours (Part 2.7) |

## 2.11 Checks for the website agent

On a test setup. `<website>` is the website's API, `<app server>` the app's server that reads it (tell the app side which one).

**The two doors** (no cookies)

- `curl -s https://<website>/api/matched` → 200; `shifts` holds only published shifts, each with `id` and `updated_at`.
- `curl -s https://<website>/api/matched/2027-01-25-s1` → 200, the document of Part 2.3; its `updated_at` is the same number as in the list. A shift that is not published → 404.
- Every picture link of the shift opens in a private browser window.

**The paper** (as a signed-in test student)

- `GET /api/my/sets/<paper_id>` → 200 for any student; `rules` +4 / −1 / 0; `minutes` by the subject rule; `test_kind` "matched".
- Start it. `GET /api/attempts/<id>` → `set_id` is the `paper_id`; the `questions[].id` are exactly the shift's `question_id`s, no more and no fewer.
- Submit it. `GET /api/attempts/<id>/results` → the same `set_id` and question ids.

**Through the app's server** (2 to 5 minutes after publishing)

- `curl -s https://<app server>/api/matched` → the shift is in `shifts`.
- `curl -s https://<app server>/api/matched/2027-01-25-s1` → **`matched` equals the number of questions entered** (lower = something was left out: Part 2.9); **`paper_questions` equals the number of questions in the paper**; the numbers in `subjects` add up to `matched`; `paper_id` is the paper.
- `curl -s https://<app server>/api/matched/paper/<paper_id>` → the same shift.
- Change a question and save → the change is there within 5 minutes. Unpublish → 404 within 5 minutes. Publish again → back.
- Set `card` to `on` → `curl -s https://<app server>/api/app/switches` → `"matched": true` within about 3 minutes. `off` → `false`. `auto` → `true` while a shift is published (unpublish the last one → `false` within about 5 minutes, as long as the series has not ended); with none, by the series' date.

**Then in the app:** the page, the shift, a card's two tabs, the sign-up sheet, the paper, the JEE question under ours in the player and in the solutions.

## 2.12 Limits, what was not checked, and the samples on the preview

**What the app cannot show without a new build**

- video solutions; a picture that needs sign-in;
- more than 4 of ours for one JEE question;
- a subject other than Physics, Chemistry, Mathematics (it shows, without a name and without a pill);
- one paper across several shifts (the button is per shift);
- marking other than +4 / −1 on the shift's card;
- a way into Matched while the card's switch is off.

**Not checked**

- Anything on a real phone. Everything was walked in the app's web preview, at a phone's size.
- **One real shift going all the way from the website to a phone:** the two doors and the real paper do not exist yet. The copy of the website's shifts has automated tests against a stand-in for the website.
- **The JEE question under ours while a paper is being solved** (that needs a started attempt). It was seen in the solutions of a finished paper.
- Signing up from the sheet to the end. The sheet, the sign-up form with its note, and the way back to the shift after **signing in** were walked.
- A shift with pictures: the sample shifts are typed questions.
- **The All India bar on a real day of the series:** the series begins on 9 Dec 2026. On the preview the bar was seen before the series ("50 DAYS", "Starts 9 Dec", a tap opens the series hub) and, with the browser answering the schedule as a day of the series, as "DAY 46 / 50", "Live today · Start today's test" (at a phone's usual width and at a narrow one). Its tap into a paper was not pressed.
- **The card turning on with the first shift, against production:** the rule is covered by automated tests of the app's server; on the preview the card is switched `on` by hand, so `auto` was not watched there.

**The samples on the preview** (28 Nov 2026)

- Three made-up shifts are published on the **preview's** database, for the owner's eyes: `2027-01-22-s1` (6 matched questions), `2027-01-22-s2` (3), `2027-01-24-s1` (2). So that the button and the JEE question under ours can be seen, the first one names a real paper of the website as a stand-in (the chapter test "01 Sets and Relations").
- Home's card is switched `on` by hand on the preview. (With the samples published it would be on under `auto` too, by the first-shift rule.)
- They are taken back with `python3 backend/tests/matched_sample.py hide` (and shown with `show`). Nothing is deleted. The tool refuses to write into a database that is not the workspace's own.
- **A sample never leaves the workspace (since 27 Nov 2026).** The app's server shows a shift marked `sample: true`, and follows the samples' own switch, only when it is the workspace's own server (its database runs on the same machine). Any other server, production above all, leaves them out of the list, answers 404 for their pages and their paper, and does not turn Home's card for them, **whatever its database holds**. Checked by `backend/tests/test_samples_stay_home.py`, also against the preview's own database read the way production would read it: 3 samples kept in, no shift given out, the card off.
- **Production has none of this** (checked, Part 3.7). The day the website publishes a real shift with the id of a sample, the website's shift takes the sample's place.

# Part 3 — Reference

## 3.1 Every address

**The app's own server** (the app calls these; base address: the app's server, then `/api`)

| Address | Who may call | What it gives | Other answers |
| --- | --- | --- | --- |
| `GET /api/choice/bank` | a signed-in student (a short pass in the `Authorization` header) | the chapters of the three subjects with their tests, the owner's rules, `pick` / `random`, and `misfire` (Part 4.8: `true` only when door A says exactly `true`) | `{ "ready": false, "misfire": … }` when there is no chapter at all; 401 without a pass; 401 with the code `website_session` when the website wants a fresh session; 503 when the website does not answer |
| `GET /api/choice/chapters/<id>` | a signed-in student | door B's questions in the shape the app draws; everything else dropped | 404 no questions to choose; 401; 503 |
| `POST /api/jl/choice/papers` | the student's own session | passed on to the website's door C as it is | the website's own answer |
| `GET /api/matched` | everyone | all published shifts, newest first, without their questions; `total` | |
| `GET /api/matched/<shift id>` | everyone | one shift with its questions | 404 not published; 422 an id of another shape |
| `GET /api/matched/paper/<paper id>` | everyone | the published shift whose real paper this is | 404 |
| `GET /api/app/switches` | everyone | `{ "pictures": …, "matched": true or false }`: whether Home shows the Matched card | |
| `DELETE /api/rf/dream/mocks/<attempt id>` | a signed-in student | takes a paper that is no full mock out of that account's Dream College meter, for good | |

**The website: doors in use today** (nothing to build; do not change their fields without telling the app side). These are the ones the two new features lean on. **The whole list of the website's doors the app uses is in Part 7.2.**

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
| `"misfire": true` in door A; door C with `mode: "misfire"`; `GET /api/my/misfire/mocks` | the Misfire Mock | 4.8 |

And three changes to what exists: `rules.minutes` of the chapter-wise sets (Part 1.8); `test_kind` "choice" and "matched" on those papers and their results; `test_kind` on the items of `GET /api/my/tests` (Part 1.9). For the Misfire Mock also `test_kind` "misfire", and `misfire: { understood, total }` in its result (Part 4.8).

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
| `rf_meta`, row `matched:card` | Home's card: `on`, `off` or `auto`, and `by`: who wrote it (`website`, `owner`, or `sample` for the preview's samples). Outside the app's own preview only a word by `website` or `owner` counts |
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
| Turn Home's Matched card and the sign-in bar on or off | `card` in the website's list door; or the row `matched:card` in the app's database, written with `by: "owner"`, when the website sends no `card` | the super admin; the app side | about 3 minutes, then at each phone's next app launch |
| Take one shift back | unpublish it on the website | the super admin | about 5 minutes |
| Take a shift back when the website cannot | set `published` to `false` on its document in `matched_shifts` (a shift the website still lists comes back on the next pass) | the app side | 1 to 2 minutes |
| Stop the JEE question showing under ours for a paper | take the shift back, or take the `question_id`s out and save | the super admin | about 5 minutes |
| Hide the preview's samples | `python3 backend/tests/matched_sample.py hide`; `python3 backend/tests/choice_sample.py hide`. (A server that is not the workspace's own never shows them anyway: Part 2.12) | the app side | 1 to 2 minutes |

None of these needs an app update, except taking the tile off Home.

## 3.5 Every sentence a student can read

**Student Choice**

| Where | Words | When |
| --- | --- | --- |
| Home tile | STUDENT CHOICE · apne chapters chuno · NEW | always |
| First screen, top | Student Choice · JEE MAIN · CHAPTER-WISE SAWAAL · Apne chapters, apni marzi. | today |
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
| Step 2, tests | Aapke chapter tests · Student Choice · Step 2 of 2 · STUDENT CHOICE · AAPKE CHAPTER TESTS · 3 chapter tests · 2 ho gaye · Ho gaye · Chal rahe · Baaki | |
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
| Student Choice, app | `frontend/app/choice/index.tsx`, `pick.tsx`, `tests.tsx`, `questions.tsx`; `frontend/src/choice/api.ts`, `search.ts`, `store.ts`, `parts.tsx`, `looks.tsx` (the dark-red top card and the subject tabs; their colours are in `frontend/src/theme.ts`); Home's tile in `frontend/app/(tabs)/index.tsx` |
| Dream College meter | `frontend/src/dream/store.ts` (`isFullMock`), `frontend/app/result/[id].tsx`, `backend/dream.py` |
| Matched, server | `backend/matched.py` (the pages, the copy of the website's shifts, the card's day), `backend/app_switches.py`, started in `backend/server.py` |
| Matched, app | `frontend/app/matched/index.tsx`, `[id].tsx`; `frontend/src/matched/api.ts`, `gate.tsx`, `MatchedCard.tsx`, `looks.tsx`, `Pair.tsx`, `QuestionBlock.tsx`, `MatchedWith.tsx`, `parts.tsx`, `html.ts`; Home `frontend/app/(tabs)/index.tsx`; the All India bar under the card `frontend/src/components/series/HomeSeriesBar.tsx`; sign-in `frontend/app/entry.tsx`; public routes `frontend/app/_layout.tsx`; player `frontend/app/attempt/[id].tsx`; result `frontend/app/result/[id].tsx`; paper's page `frontend/app/set/[id].tsx` |
| Tests | `backend/tests/test_choice.py` (12), `test_matched.py` (6), `test_matched_sync.py` (5), `test_samples_stay_home.py` (6): all 29 pass on 28 Nov 2026. Search: `node tests/choice_search_check.js`. Looks on the preview (read only): `python3 tests/home_series_bar_look.py`, `python3 tests/choice_cap_sentence_look.py`, `python3 tests/choice_colour_look.py` (390 and 320 points wide) |
| Misfire, app | `frontend/app/misfire/index.tsx`, `[id].tsx`, `solve.tsx`; `frontend/src/misfire/api.ts`, `AllTab.tsx`, `PapersTab.tsx`, `ChapterReport.tsx`, `SolveCard.tsx`, `NumPad.tsx`, `HomeMisfire.tsx`, `store.ts`, `usePaged.ts`, `parts.tsx`. It keeps no Misfire data of its own (Part 4), except Offline Misfire's mocks and its note of the "Samajh gaya" ids (Part 4.7) |
| Offline Misfire (Part 4.7) | `frontend/app/misfire/mock/new.tsx`, `[id].tsx`; `frontend/app/offline/misfire/index.tsx`, `new.tsx`, `[id].tsx`; `frontend/src/misfire/mock/` (`build.ts`, `store.ts`, `marking.ts`, `pictures.ts`, `offline.ts`, `MocksTab.tsx`, `Ready.tsx`, `Player.tsx`, `Result.tsx`, `Closed.tsx`); `frontend/src/misfire/known.ts`; the offline door `frontend/src/offline/door.tsx`. Checks: `python3 tests/offline_misfire_check.py` (30), `python3 tests/misfire_mock_check.py` |
| Misfire Mock (Part 4.8) | `frontend/src/misfire/web.ts`, `web/WebMocksTab.tsx`, `web/Understood.tsx`; the setup `frontend/app/misfire/mock/new.tsx` (`?web=1`); the tab `frontend/app/misfire/index.tsx`; the switch on the server `backend/choice.py` (`misfire_on`). Check: `python3 tests/misfire_web_check.py` (30) |
| All India Rapid's "Misfires" | server `backend/daily.py` (`GET /api/rf/daily/misses`); app `frontend/src/rapid/DailyMisses.tsx` |
| Rapid Fire in a browser | the built copy `backend/arena_web/`, served by `backend/arena_web.py` at `/api/arena`; built by `scripts/build_arena_web.sh` (then the owner's Publish); `backend/tests/test_arena_web_complete.py` (every file the copy names is answered; no file is left out of a Publish; no workspace address in it). In a browser: `python3 tests/slow_phone_check.py arena`, `python3 tests/slow_phone_wins.py arena` (also with `calm`, `reduce`, `narrow`, `laptop`) |
| One account | `frontend/src/auth.tsx`, `frontend/src/api/client.ts`, `backend/jl_proxy.py` (the website's doors), `backend/rf_access.py` (Rapid Fire's id from `auth/me`), `backend/account_deletion.py`, `backend/pin_reset.py` |
| Working together (Part 7) | the app's calls: `frontend/src/api/client.ts` and the screens; the app's server: `backend/jl_proxy.py`, `jl_transport.py`, `website_shield.py`, `session_coordination.py`, `login_guard.py`, `client_ip.py`. The read-only walk: `python3 tests/website_doors_walk.py`. The list of Part 7.2 is checked against the app's code by `build_book.py` |
| Samples stay in the workspace | `backend/workspace.py`; used by `backend/matched.py` and `backend/choice.py`; `backend/tests/test_samples_stay_home.py` (6) |
| Samples (preview only) | `backend/tests/matched_sample.py show` or `hide`; `backend/tests/choice_sample.py show` or `hide` |
| Earlier notes | `memory/WEBSITE_CHOICE_NOTE.md`, `memory/WEBSITE_MATCHED_NOTE.md`, `memory/MATCHED_CONTRACT.md`, `memory/WEBSITE_MISFIRE_MOCK_NOTE.md`. This book was written from the code on 28 Nov 2026 and takes their place for readers outside the app side |
| This book | `handoff/feature_book/`: `parts/` (the text), `examples/` (the JSON), `shots/` (the pictures), `build_book.py`, `take_shots.py`, `take_shots_more.py`, `take_shots_misfire.py` |

### Names of the screens' parts, for automated checks

Every part of the two features carries a fixed name (`testID`; in the web preview it is the `data-testid`). The ones a check needs most:

| Screen | Names |
| --- | --- |
| Home | `home-tile-choice` (the tile), `home-tile-choice-badge`; `home-matched` (the card), `home-matched-total`, `home-matched-latest`, `home-matched-cta`, `home-matched-soon`, `home-matched-view-all`; `home-series-bar` (the All India bar under the Matched card), `home-series-bar-day`, `home-series-bar-line`; `home-series-view-all` (the All India card is on instead) |
| Sign-in screen | `entry-matched` (the bar), `entry-matched-note` (the note after "Attempt all matched") |
| Student Choice, first screen | `choice-screen`, `choice-hero` (the dark-red card), `choice-title`, `choice-facts`, `choice-way-chapters`, `choice-way-tests`, `choice-way-pick`, `choice-way-random`, `choice-soon`, `choice-soon-pick`, `choice-soon-random`, `choice-time`, `choice-time-physics` / `-chemistry` / `-mathematics`, `choice-time-note`, `choice-not-ready`, `choice-error`, `choice-refresh` |
| Random mock sheet | `choice-random-sheet`, `choice-random-input`, `choice-random-quick-15` … `-75`, `choice-random-makeup`, `choice-random-rule`, `choice-random-range`, `choice-random-error`, `choice-random-make` |
| Step 1, chapters | `choice-pick-screen`, `choice-search-input`, `choice-search-clear`, `choice-search-count`, `choice-search-none`, `choice-search-reset`, `choice-subject-physics` / `-chemistry` / `-mathematics` (the glossy tabs; `-count` is the ticked count on a tab), `choice-chapter-list`, `choice-chapter-<id>` (a row; it is a checkbox), `choice-chapter-<id>-title`, `-subject`, `-picked`, `choice-pick-hint`, `choice-pick-bar` |
| Step 2, chapter tests | `choice-tests-screen`, `choice-tests-hero` (the dark-red card), `choice-tests-count`, `choice-tests-done` / `-running` / `-left` (its three counts), `choice-tests-subject-physics` / `-chemistry` / `-mathematics`, `choice-test-<id>` (a row), `-title`, `-facts`, `-status`, `-action` (Start, Resume or Result), `choice-tests-error`, `choice-tests-change` |
| Step 2, questions (later) | `choice-questions-screen`, `choice-q-subject-…`, `choice-q-chapter-…`, `choice-questions-chapter`, `choice-questions-hint`, `choice-question-list`, `choice-full`, `choice-next-chapter`, `choice-questions-bar`, `choice-review-sheet`, `choice-review-makeup` (a subject's minutes: `choice-review-makeup-physics-time`, and so on; the same on `choice-random-makeup`), `choice-review-rule`, `choice-review-error`, `choice-make`, `choice-review-back` |
| Matched page | `matched-screen`, `matched-total`, `matched-month-…` (the pills) or `matched-month-only`, `matched-day-<day>`, `matched-shift-<shift id>` (a row), `-count`, `-number`, `matched-empty`, `matched-error`, `matched-refresh` |
| A shift | `matched-shift-screen`, `matched-shift-count`, `matched-attempt` (the button), `matched-attempt-facts`, `matched-attempt-questions`, `matched-attempt-note`, `matched-attempt-soon`, `matched-shift-list-title`, `matched-subject-…` (the pills), `matched-shift-list`, `matched-shift-empty`, `matched-shift-error`, `matched-signup-sheet`, `matched-signup-yes`, `matched-signup-login` |
| The paper's page, player, solutions, result | `set-detail-screen`; `matched-with` (the JEE question under ours), `matched-with-where`, `matched-with-jee`; `result-dream` (the Dream College meter: must be absent on a chapter test and on a Student Choice paper) |
| Misfire's two mocks (Parts 4.7, 4.8) | the tabs `misfire-tab-mock` ("Offline Misfire") and `misfire-tab-web` ("Mock", only with the switch on); `misfire-mock-hero`, `misfire-mock-new`; `misfire-web-hero`, `misfire-web-new`, `misfire-web-<attempt id>`; the setup `mock-new-screen`, `mock-new-header`, `mock-new-phone` (the phone's sentence), `mock-new-web-retry`, `mock-new-bar-go`, `mock-making-error`, `mock-making-retry`; offline `offline-misfire-open`, `mock-closed`; the results `mock-result-waiting`, `mock-result-moved`, `result-misfire-understood`, `result-misfire-understood-count` |

A row of the chapter list is best found as `[role=checkbox][data-testid^=choice-chapter-]`: the list's own name starts with the same letters.

**A hard rule for anyone testing on the app's preview:** the test learner there is the owner's own account on the real website. Never press Start, Begin, Resume or Submit with it, never open an attempt, never tap a chapter test whose button says Resume. Walks that need a started or finished paper use a test student on the website's test setup, or answers given by the browser in place of the website.

## 3.7 The state on 28 Nov 2026, and how to check it again

Read by the build of this book, at 16:12 India time on 28 Nov 2026:

| What was asked | The answer | What it means |
| --- | --- | --- |
| The app's server in production: `GET /api/app/switches` | 200, `"matched": false` | Home shows the All India series card; no Matched bar on the sign-in screen |
| The app's server in production: `GET /api/matched` | 200, 0 shifts, 0 questions | no shift is published in production |
| The app's server in production: `GET /api/choice/bank`, signed out | 401 | the door is there, for signed-in students only |
| The website: `GET /api/matched` | 404 | Matched: the list of shifts: not built yet |
| The website: `GET /api/matched/2027-01-25-s1` | 404 | Matched: one shift: not built yet |
| The website: `GET /api/choice/bank?exam=jee-main` | 401 | Student Choice: door A (asked signed out here; a signed-in student got 404 on 26 Nov 2026): the website answers; tell the app side |
| The website: `GET /api/series/all-india-jee` | 200, 2026-12-09 to 2027-01-27 | with no shift published, Home's card turns to Matched on 28 Jan 2027 (India time); a published shift turns it sooner, the switch at any time |
| The app's server in production: `GET /api/arena` (Rapid Fire in a browser, Part 5) | 200 | the newest copy is live |
| The app's server in production: the icon font of Rapid Fire in a browser | 200 | the icons are drawn |
| The website: `GET /api/auth/session`, signed out | 200, `"user": null` | the website's sign-in doors answer; the app signs up and signs in only through them (Part 6) |

Also true on 28 Nov 2026, seen through the app's preview: the website lists **81 chapter-wise tests** (Physics 30, Chemistry 24, Mathematics 27) with **3750 questions**, and every one of them has **60 minutes**.

To check again, from any machine:

```
# "matched": true only when a real shift is published, or from the day after the series ends
curl -s https://jeelive-mobile.emergent.host/api/app/switches
# the published shifts (none is real before JEE Main's first shift: Part 0.2)
curl -s https://jeelive-mobile.emergent.host/api/matched
# 401 = the door is there, for signed-in students only
curl -s -o /dev/null -w "%{http_code}\n" https://jeelive-mobile.emergent.host/api/choice/bank
# 404 = the website's Matched door is not built yet
curl -s -o /dev/null -w "%{http_code}\n" https://jeelive.ai/api/matched
# "last_date": with no shift published, the card turns the day after
curl -s https://jeelive.ai/api/series/all-india-jee
# 200 = Rapid Fire in a browser (Part 5)
curl -s -o /dev/null -w "%{http_code}\n" https://jeelive-mobile.emergent.host/api/arena
# the website's sign-in doors (Part 6): "user": null for a signed-out visitor
curl -s https://jeelive.ai/api/auth/session
```

## 3.8 Decided by the owner, and still open

**Decided on 26 Nov 2026** (the first two were open points in version 1 of this book)

| The question | The owner's answer | Where |
| --- | --- | --- |
| Whole chapter tests by the ratio as given, or with a longest time? | **A longest time of three hours.** 7 tests are held at 180 minutes; no chapter test is longer than a full mock | Part 1.8 |
| When should Matched appear if JEE Main shifts are held before the All India series ends? | **On the day of the first shift itself:** the card turns to Matched as soon as the first shift is published; the series is a bar under it for its remaining days | Part 2.6 |
| How should Student Choice look? | **Colour at the top only:** a dark-red top card like the result page's, glossy subject tabs; the cards below stay white | Part 1.2 |
| Misfire on the website and in the app? | **The same: one calculation, the website's** | Part 4 |
| Accounts? | **One user list:** sign up on either side, sign in on both | Part 6 |
| Rapid Fire now? | **No change to its code.** Its browser copy is built again from the app's code as it is | Part 5 |

**Still open**

| # | The question | What happens until it is answered |
| --- | --- | --- |
| 1 | **Should the three hours also be the longest time of a paper the student makes?** By the ratio alone 75 Mathematics questions get 240 minutes. (A top of 25 questions per subject, door A's `max_per_subject`, would also keep every made paper within 180.) | made papers are not cut |
| 2 | **A shortest time for whole chapter tests?** By the rule 11 tests become shorter than today's 60 minutes; the shortest gets 4 minutes for its 2 questions (Part 1.8) | the rule as given: no shortest time |
| 3 | **Should a Matched paper ever count for the Dream College meter?** Today it would, if it had 68 questions or more and 150 marks or more. Chapter tests and Student Choice papers never count | it would count; a shift's paper is far smaller than that |
| 4 | **The app side's suggestions for made papers** (Part 1.6): fresh questions first in a random mock; a daily limit; removing papers never started; no leaderboard | the website agent should not build them unasked |
| 5 | **The wording of `source` and `tag` on Matched** (Part 2.8) | the super admin writes what seems right |
| 6 | **The made-up sample shifts on the preview:** keep them for looking, or hide them now? | they stay published on the preview only |
| 7 | **The `kind` of Student Choice papers and Matched papers in the paper history** (a question for the website agent, Part 4.4 point 5) | their Misfire questions are in "Sab" |
| 8 | **Opening Rapid Fire from the website without typing the PIN again** (Part 5.4: written, not built) | the student types the phone and PIN once in the browser Rapid Fire |


# Part 4 — Misfire: the website's own, shown in the app

## 4.1 What it is, and who owns it

**Misfire** is every question a student got wrong or left in a finished paper, kept so they can solve it again. jeelive.ai has it, and the app has had it since 24 Nov 2026.

**It is the website's Misfire.** The app does not keep, count or mark Misfire questions of its own. (Its one practice of its own, new on 28 Nov 2026, is **Offline Misfire**, Part 4.7: a mock kept on the phone, which never changes the website's Misfire by itself and sends a right answer only through the website's own doors. The website's own **Misfire Mock**, built in the app and waiting for its switch, is Part 4.8.) It reads the website's answers and sends the student's tries back to the website. So the website and the app always show the same open questions, the same "Samajh gaya" (understood) questions and the same counts. **Nothing has to be handed over in either direction for it to work: it is already connected.** This part is here so the website agent can check that the two stay the same (Part 4.4).

| Decision | Date | Where it shows |
| --- | --- | --- |
| Misfire must be the same on the website and in the app: one calculation, the website's | 26 Nov 2026 (the owner) | the whole of this part |
| The app also shows it paper-wise for AITS, JEE Chapter-wise, JEE PYQ, BITSAT Mocks, BITSAT Chapter-wise and COMEDK Mocks | 24 Nov 2026 | Part 4.2 |
| All India Rapid's "Misfires" tab is Rapid Fire's own and is not given to the website | 26 Nov 2026 | Part 4.5 |
| The app's "Mock" tab becomes "Offline Misfire": on the phone, also with no internet | 28 Nov 2026 (the owner) | Part 4.7 |
| A Misfire mock for the website and the app alike is the website's paper, behind the switch `misfire` | 28 Nov 2026 (the owner) | Part 4.8 |

## 4.2 What a student sees in the app

- Picture `shots/x01_home_misfire.jpg`: 14. Home: the Misfire card under the exam tiles
- Picture `shots/x02_misfire_all.jpg`: 15. Misfire, tab "Sab": the website's own list
- Picture `shots/x03_misfire_papers.jpg`: 16. A paper-wise tab: the finished papers of one test family

- **Home card "MISFIRE"** (blood red, the word in glossy yellow, a row of lights round its edge): "607 sawaal dobara solve karne hain", plus one chip per subject with its open count. It is hidden until the student has a graded paper. It is read from `GET /api/my/misfire/summary`.
- **`/misfire`**, small line "Galat + chhode sawaal · dobara solve karo", with the count "607 OPEN" at the top right. Its tabs are **Sab** (all), then **AITS · JEE Chapter-wise · JEE PYQ · BITSAT Mocks · BITSAT Chapter-wise · COMEDK Mocks**. A family whose exam the website hides is not offered.
- **Sab** is the website's Misfire as it is:
    - **Galtiyan** = `status=open`, and **Samajh gaya** = `status=fixed`, 20 a page with "Aur dikhao" (show more);
    - subject pills, and a chapter sheet ("Saare chapter");
    - **Chapter report** = `GET /api/my/chapters`;
    - the questions sit under their paper's name.
- **A family tab** lists that family's finished, scored papers, newest first, each with its wrong and left counts. A tap opens **the paper's page** `/misfire/<attempt id>`. That page lists the paper's wrong and left questions, with subject, "Galat" and "Chhode" filters, plus "Dobara solve karo" (solve again) and "Poora analysis" (the normal result).
- **Solve again** shows the question as it was printed and the answer given in the paper, then takes a fresh try:
    - option tiles or option cards, or the app's own number keys for a numerical;
    - after a wrong try, the right answer;
    - after any try, the solution;
    - after a right try, "Samajh gaya"; and "Wapas list mein" (back to the list);
    - "Pichhla / Agla" (previous / next) at the bottom.
- **AITS:** the AITS Analysis list has one button, "AITS ki galtiyan dobara solve karo", which opens the AITS tab.
- While the website says some papers are still being prepared (`waiting` > 0), the app shows "Aapke kuch papers abhi jud rahe hain…" and asks again every 3 seconds, 8 times at most.

**Every request, and what the app expects back** (through the app's server, which passes them unchanged to `https://jeelive.ai/api/…`):

| Request | What the app reads |
| --- | --- |
| `GET /my/misfire/summary` | `open`, `fixed`, `waiting`, `subjects[] {name, open, fixed}` |
| `GET /my/misfire?status=open\|fixed&subject=&chapter=&page=` | `items[]`, `total`, `page`, `pages`, `waiting`, `chapters[] {name, count}`; each item: `id`, `attempt_id`, `question_id`, `title`, `exam`, `subject`, `chapter`, `number`, `outcome` (`incorrect` \| `skipped`), `lost`, `your_answer`, `type`, `question`, `solution_count`, `status`, `tries`, `last_correct`, `at` |
| `GET /my/chapters` | `papers`, `waiting`, `chapters[]` and `subjects[]` {subject, chapter, papers, total, correct, wrong, skipped, lost, sahi, accuracy, trend}, `untagged` |
| `POST /my/misfire/<id>/try {value}` | `{correct, item}`; the item carries `answer` and `solution_text` only after a try |
| `POST /my/misfire/<id>/done` | refused (409) until a right try; then the question moves to "Samajh gaya" |
| `POST /my/misfire/<id>/reopen` | back to the open list, tries back to 0 |
| `GET /exam-navigation/<slug>/history?kind=<kind>&page=` | the family tabs: JEE Main `chapter` and `pyq`; BITSAT `mock` and `chapter`; COMEDK `mock` |
| `GET /series/all-india-jee/history?page=` | the AITS tab (20 a page) |
| `GET /attempts/<id>/results?score_version=original` | a paper's page: its wrong and left questions |

## 4.3 The only three things the app works out by itself

| What | How the app does it | What the website should confirm |
| --- | --- | --- |
| **Which papers a family tab lists** | The website's paper history of that family. Attempts whose `mode` is `retry`, `preview` or begins with `series_` are left out of the family tabs: a retry repeats its own paper's questions, and an All India day has its own tab. Only papers that have a score (`summary`) are listed; the wrong and left counts are the summary's `incorrect` and `skipped` | that these kinds and modes mean what the app takes them to mean |
| **A paper's wrong and left questions** | From that paper's own result: every question whose `outcome` is `incorrect` or `skipped`. The question's Misfire id is built as **`<attempt id>:<question id>`**, and the tries on that page are sent to that id. "Samajh gaya" on that page comes from the website's `status=fixed` list (the newest 100). A result that is not out yet reads "Is paper ka result abhi nahi khula." | that every wrong or left question of every scored paper has a Misfire item, and that its id is written exactly so |
| **"Kitne marks gaye"** (marks lost) on a paper's page | The question's own `scoring.correct` (or the paper's `rules.correct`) minus the marks the question got. Under +4 / −1: wrong = 5, left = 4 | that the website's own `lost` in `/my/misfire` means the same |

Everything else on these screens (what is open, what is understood, every count, the chapter report, whether a try is right) is the website's answer, shown as it comes.

## 4.4 Checks for the website agent

1. The answers of Part 4.2 keep their fields. **A field may be added; none may be renamed or dropped without telling the app side** (rule 3 of the "who builds what" table the two sides keep).
2. Every wrong or left question of **every** scored paper has a Misfire item with the id `<attempt id>:<question id>`. That includes All India days, chapter tests, PYQ papers, BITSAT and COMEDK papers, a **Student Choice paper** (`test_kind` `choice`, when door C exists) and a **Matched paper** (Part 2.4b).
3. `lost` means "the marks a right answer would have given, minus the marks given" (Part 4.3).
4. `try` accepts the answer as the paper took it: the option's key for an MCQ (the same key `your_answer` holds), and the number as typed for a numerical. A numerical try may have a decimal point unless the question's `type` is `integer`.
5. **A question for the website:** what `kind` will Student Choice papers and Matched papers have in `GET /exam-navigation/jee-main/history?kind=…` (for example `choice` and `matched`)? Tell the app side. The app can then give each its own Misfire tab. Until then their questions are in "Sab" like every other paper's, and chapter tests taken from Student Choice are already in "JEE Chapter-wise".
6. A paper that has just been submitted, whose Misfire is still being prepared, is counted in `waiting`, and the app waits for it. Please keep doing that, rather than answering an empty list.

## 4.5 All India Rapid's "Misfires" tab: a different thing, Rapid Fire's own

The result screen of **All India Rapid** has a **"Misfires"** tab. All India Rapid is the app's daily Rapid Fire round, 45 cards, the same for all of India. The tab lists the cards of that round the student did not answer right: wrong, timed out or skipped, each with "You chose", the right answer and the explanation, and subject pills to filter them.

- It is **Rapid Fire's**, on the app's server (`GET /api/rf/daily/misses`). It is **never mixed** with the papers' Misfire above and needs nothing from the website. The website has no Rapid Fire of its own (Part 5).
- Cards the student never reached (they left the round early) stay sealed: all of India plays the same cards that day, so their answers must not come out through a student who quits at card 1. The tab's number counts every card not answered right; the list shows only the cards the student saw, and a note under it says how many were never reached.
- It is in the app since 25 Nov 2026. It is also in the browser Rapid Fire, rebuilt on 26 Nov 2026 (Part 5).

## 4.6 Not checked

- BITSAT and COMEDK papers in Misfire (the test learner has none), and questions the website sends in cut pieces inside Misfire.
- A real All India day (the series begins on 9 Dec 2026).
- Anything on a real phone.

## 4.7 Offline Misfire: a practice mock on the phone, also without internet

**New on 28 Nov 2026 (the owner's decision of that day).** Misfire's tab that was called "Mock" is now **"Offline Misfire"**. It makes a JEE Main-like mock out of the student's own Misfire questions, **on the phone**. With a line it takes them from the website's fresh Misfire list, as before; with no line, from the finished papers the phone already keeps. **It is never a paper on the website.** It never changes the website's Misfire by itself: the one thing it sends is a right answer, through the website's own Misfire doors, once the line is back.

| Decision | Date | Where it shows |
| --- | --- | --- |
| The "Mock" tab is called "Offline Misfire"; its setup, player and result stay as they were | 28 Nov 2026 (the owner) | the tab, My Tests, the mock's own screens |
| With no line, the questions come from the finished papers kept on the phone, leaving out those last seen as "Samajh gaya" | 28 Nov 2026 | below |
| A right answer becomes "Samajh gaya" on the website when the line is back | 28 Nov 2026 | below |
| Offline Misfire mocks are not on the website; they are in the app's My Tests | 28 Nov 2026 | below |
| The rules of the app's offline part stay: a sign-in with a line in the last 7 days, only the pictures already on the phone (512 MB at most) | 28 Nov 2026 | below |

- Picture `shots/x04_offline_home.jpg`: 17. No internet: the offline home offers Offline Misfire
- Picture `shots/x05_offline_setup.jpg`: 18. Its setup, from the papers kept on the phone
- Picture `shots/x06_offline_result.jpg`: 19. Its result: the right answers wait for the line

**What a student sees**

- **Misfire → "Offline Misfire"** (`/misfire?tab=mock`): the dark-red card "OFFLINE MISFIRE · Galtiyon se JEE Main mock", the button "Naya mock banao", and every mock made on this phone, newest first.
- **With no line**, the offline home ("Phone par rakha hua · Rapid Fire, results aur Misfire") has the card **"Offline Misfire"** ("Apni galtiyon se JEE Main jaisa mock, bina internet. Jo sahi karoge, internet aate hi “Samajh gaya” ho jayenge."). It opens the same list at `/offline/misfire`.
- **The setup** is the one it always was: Physics, Chemistry and Mathematics, up to 25 each (5, 10, 25 or "Max"), and the chapters. Time by the owner's ratio: 25 Physics = 60 min, 25 Chemistry = 40, 25 Maths = 80. When the questions come from the phone, it says so:
    - no line: "Sirf phone par rakhe N papers se · M sawaal mile. Jo pehle “Samajh gaya” ho chuke, woh nahi liye.";
    - a line, but the website's Misfire list does not come: "Website se list abhi nahi aa paayi." before the same sentence, and a button "Website se dobara laao".
- **The ready screen** adds "Phone par rakhe papers se bana: internet ke bina bhi poora chalega.", and "Saare sawaal phone par taiyaar" once every picture is there.
- **The result** is the one it always was: the score, subject by subject, the chapters to look at again, and every question with its key and solution. While right answers wait for the line: "N sahi sawaal “Samajh gaya” mein ja rahe hain. Internet aate hi pahunch jayenge." Once they are through: "N sawaal “Samajh gaya” mein chale gaye".
- **My Tests** lists it as "Offline Misfire #n", and its own screens are titled "OFFLINE MISFIRE #n".

**How it works (all of it on the phone)**

| What | How |
| --- | --- |
| The questions, with a line | the website's open Misfire list, `GET /my/misfire?status=open&subject=…` (Part 4.2), as before |
| The questions, with no line | every `incorrect` or `skipped` question of the finished papers the phone keeps (the same papers "Mere results" opens offline), of Physics, Chemistry and Mathematics, with its key; not a bonus or dropped question; once only (the newest paper's copy when a question was in two); and **only when its pictures are already on the phone**. A result kept but never opened once is left out, as it is everywhere offline. The question's id is its Misfire id `<attempt id>:<question id>` |
| "Samajh gaya", with no line | the phone remembers the ids it last saw in the website's `status=fixed` list, and leaves them out. It learns them from Misfire's own screens and, after the phone keeps papers, at most once in 15 minutes and never during a paper: `GET /my/misfire/summary`, and the `status=fixed` pages (20 a page, 50 pages at most) only when the website's count differs from the phone's, or a day after the last full read. A question marked on the website since then can still come in once |
| Who may open it with no line | the same rule as for the rest of the app's offline part: the account signed in on this phone **with a line in the last 7 days**. Otherwise: "Pehle ek baar internet ke saath app kholo" |
| A right answer | kept on the phone. When the line and the session are back, the app sends it **through the website's own doors**: `POST /my/misfire/<id>/try` with the answer, then `POST /my/misfire/<id>/done` when the website says it is right. It tries again every 45 seconds while the student is signed in, until it is through. **Nothing is sent while nobody is signed in** |
| Pictures | only those already on the phone (the same 512 MB as before); nothing new is fetched without a line |
| Where the mock is kept | on the phone only, under that account. It is **never** a set, an attempt or a result on the website, and the website's Mock tab never lists it |

**For the website: nothing to build.** Please keep three things as they are (Part 4.4 and Part 7.2 already ask for them):

1. `POST /my/misfire/<id>/try` judges the answer itself and gives `correct`. The app never decides on the website's behalf that an answer is right. A try that comes **hours later**, from a phone that was offline, is judged the same way.
2. `POST /my/misfire/<id>/done` after a right try moves the item to "Samajh gaya". A second `done` on an item already there does no harm (the app may send it again after an answer that got lost).
3. A try on an item the student has meanwhile marked "Samajh gaya" on the website is answered like any other try (the app then sends `done`, which changes nothing).

**Checked on 28 Nov 2026** (`tests/offline_misfire_check.py`, 30 checks; the website's writes were answered by the browser, nothing was written): the tab's name; the website's list with a line; the phone's papers when the list does not come, with the sentence and the button; a question listed as "Samajh gaya" left out; the offline door, the list, the setup, the mock and its result with no line at all, every picture from the phone; nothing sent while signed out; each right answer sent once (try, then done) about 6 seconds after the line came back; My Tests' name; shut on a phone with no confirmed session. The app side's independent review found no fault.

**Not checked:** a real phone with no network (the preview's browser was cut off from the network instead); many days offline; one student's two phones offline at once.

## 4.8 Misfire Mock made by the website: built in the app, shut until its switch

**Built in the app on 28 Nov 2026, and shut until the website opens it.** The owner decided (28 Nov 2026) that a Misfire mock taken **on the website and in the app alike** must be the website's own paper. So the app asks the website to make it, and from then on it is an ordinary paper on both sides: its page, its timer, autosave, its result, its Analysis, My Tests. **Until door A says `"misfire": true`, no student sees any of it.** The app was checked with the switch off and with it on.

| Decision | Date |
| --- | --- |
| A Misfire mock for both sides is the website's paper, made by door C with `mode: "misfire"` | 28 Nov 2026 (the owner) |
| Its switch is `misfire` in door A, shut unless it is exactly `true` | 28 Nov 2026 |
| Its result says how many of its questions went to "Samajh gaya" | 28 Nov 2026 |
| Offline Misfire (Part 4.7) stays as it is, next to it | 28 Nov 2026 |
| The website and the app agreed every door, answer and sentence below (the website's contract: its `memory/MISFIRE_MOCK_CONTRACT.md`) | 28 Nov 2026 (the website and the app side) |
| A Misfire Mock's result is not counted in Misfire's chapter report; a question already "Samajh gaya" that is wrong in the mock stays "Samajh gaya" | 28 Nov 2026 (the website) |

- Picture `shots/x07_mock_tab.jpg`: 20. Switch on: Misfire's "Mock" tab
- Picture `shots/x08_mock_setup.jpg`: 21. Its setup asks jeelive.ai for the paper
- Picture `shots/x09_mock_paper.jpg`: 22. The made paper's page
- Picture `shots/x10_mock_result.jpg`: 23. Its result: how many went to "Samajh gaya"

The pictures are from the app's preview, with the browser answering in place of the website: the website's doors for the Misfire Mock do not exist yet. The scores in them belong to a paper played as a Misfire Mock.

**What a student sees, once the switch is on**

- Misfire gets a tab **"Mock"**, right after "Sab" (then "Offline Misfire" and the paper-wise tabs). Its dark-red card: "MISFIRE MOCK · Galtiyon se JEE Main mock · Paper jeelive.ai par banega: timer, autosave, result aur Analysis har paper ki tarah. App aur website, dono par chalega. Jo sahi karoge, woh “Samajh gaya” ho jayenge.", the button **"Naya mock banao"**, then every Misfire Mock of the student's, newest first, with its size ("15 sawaal · 32 min"): one not started yet, "SHURU NAHI HUA" ("Shuru karo", its paper's page); one being taken, "CHAL RAHA HAI" ("Resume"); a finished one with its score and its right, wrong and left counts ("Result dekho").
- **"Naya mock banao"** opens the setup of Part 4.7, titled "Misfire Mock banao", with the website's open Misfire list only (never the phone's papers). The time it shows comes from door A's minutes (the owner's ratio).
- **"Mock banao"** asks door C. While it waits: "jeelive.ai aapki galtiyon se paper bana raha hai…". Then the made paper's page opens ("JEE MAIN · MISFIRE MOCK"), and the student starts it like any paper. When fewer questions came than were asked, it says so first: "Aapne 15 sawaal maange the, 12 mile: chune hue chapters mein itne hi khule sawaal the.", with "Paper kholo".
- **The result** of a paper whose `test_kind` is `misfire` has a card on its Analysis tab: "3 / 15 sawaal “Samajh gaya” mein chale gaye" and "Jo sahi kiye, woh Misfire ki list se hat gaye. Baaki galtiyan wahin hain, agle mock ke liye.", with "Misfire kholo". A retry of the wrong questions changes nothing in Misfire, so its result has no card. The top line reads "JEE Main · Misfire Mock".
- **My Tests** shows "JEE Main · Misfire Mock" under the paper's name.
- **The Dream College meter never counts it**, like a chapter test and a Student Choice paper.

### What the website builds

The doors are Student Choice's (Part 1.6); the Misfire Mock only adds to them. The JSON is also in the `examples` folder (`misfire_mock_ask.json`, `misfire_mock_answers.json`).

**1. The switch, in door A** (`GET /api/choice/bank?exam=jee-main`). With only the Misfire Mock open it answers `200 { "pick": false, "random": false, "misfire": true, … }`; Student Choice then stays exactly as today (`pick` and `random` false = shut), and only Misfire's "Mock" tab opens. Anything else (no `misfire`, `false`, `"true"`, `1`, or the 404 of all switches off) keeps the tab shut. Door A answers 401 without a student's cookie. The app's server reads door A every 2 minutes, so the tab appears (or goes) within about 2 minutes, on every phone.

**2. Make the paper: door C** (`POST /api/choice/papers`, sent with the student's own session):

```json
{
  "exam": "jee-main",
  "request_key": "0f6c2a8e-3b1d-4c55-9a47-7e2d1b9c4f10",
  "mode": "misfire",
  "counts": { "Physics": 10, "Chemistry": 5, "Mathematics": 0 },
  "chapters": { "Physics": ["01 Units and Measurement", "02 Kinematics"] }
}
```

- `counts`: 0 to 25 for each subject, at least 1 in all; a subject left out counts as 0.
- `chapters`: only for a subject where the student ticked some chapters, by their names exactly as `chapters[].name` in `GET /my/misfire?status=open&subject=…`. A subject not named means every chapter; a name not in the student's open list brings no question.
- The questions are the student's own **open** Misfire items (never "Samajh gaya") of Physics, Chemistry and Mathematics, from JEE Main and BITSAT papers alike; the paper's exam is JEE Main. A question listed twice comes once; answered right, both entries go to "Samajh gaya".
- **The same `request_key` gives the same paper.** A retry never makes a second one (rule 6). The app keeps one key while the student stays on the screen with the same counts and chapters, and takes a new one when they change.
- The answer (200 or 201): `{ "set_id", "title", "number", "asked", "given", "minutes" }` (the whole example below). When `given` is less than `asked`, the app says so before the paper opens.
- The trouble answers, each `error.message` shown word for word:

| Status | `error.message` | When |
| --- | --- | --- |
| 422 | "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno." | no open question in the chosen chapters |
| 422 | "Har subject mein 25 tak sawaal chuno, kul kam se kam 1." | counts out of bounds |
| 409 | "Misfire Mock abhi band hai." | the switch is off |
| 409 | "Yeh mock pehle hi ban chuka hai. Misfire ke Mock tab mein dekho." | the same `request_key` with another request |
| 429 | "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao." | 5 a day (apart from Student Choice's 5) |

404 or 405 mean "not built yet" ("Paper banana abhi jeelive.ai se jud raha hai…"); 5xx: "jeelive.ai abhi jawab nahi de raha. Thodi der mein dobara try karo; aapki ginti aur chapters yahin rahenge."

**3. The paper.** A set of the student's own, `test_kind: "misfire"`, exam JEE Main, marked +4 / −1 / 0 and timed by the ratio (rule 5; a made paper is not cut). Every question has its own subject, pieces, key and solution, so that the paper's page, start, player, autosave, deadline, result and Analysis work unchanged, in the app and on the website. `test_kind: "misfire"` also on its rows in `GET /api/my/tests`.

**4. Its list.** `GET /api/my/misfire/mocks?page=`: every Misfire Mock of the student's, **those not started too** (5 can be made a day, so each must be findable), newest first, 20 a page; `attempt` is its newest attempt, or `null`. The app opens one not started at its paper's page, one being taken (`resumable`) in the paper, and any other at its result. (`history?kind=misfire` is not built: the history lists only attempts.)

**5. Its result.** `GET /api/attempts/<id>/results` carries `test_kind: "misfire"` and, once the result is ready (with the score), `"misfire": { "understood": 3, "total": 15 }`: how many of its **questions** (not entries) the website moved to "Samajh gaya" because they were answered right, out of how many. A retry of the wrong questions changes nothing in Misfire, and its result has no `misfire`. A fresh attempt of the same mock moves right answers again.

```json
{
  "door_A_with_only_the_misfire_mock_open": { "pick": false, "random": false, "misfire": true },
  "door_C_answer_200_or_201": { "set_id": "misfire-set-0004", "title": "Misfire Mock #4", "number": 4, "asked": 15, "given": 12, "minutes": 26 },
  "my_misfire_mocks_page_1": {
    "items": [
      { "set_id": "misfire-set-0004", "title": "Misfire Mock #4", "number": 4, "created_at": 1764400000, "asked": 15, "given": 12, "minutes": 26,
        "attempt": null },
      { "set_id": "misfire-set-0003", "title": "Misfire Mock #3", "number": 3, "created_at": 1764299000, "asked": 10, "given": 10, "minutes": 21,
        "attempt": { "id": "<attempt id>", "status": "active", "resumable": true, "started_at": 1764300000, "submitted_at": null, "summary": null } },
      { "set_id": "misfire-set-0002", "title": "Misfire Mock #2", "number": 2, "created_at": 1764199000, "asked": 15, "given": 15, "minutes": 32,
        "attempt": { "id": "<attempt id>", "status": "submitted", "resumable": false, "started_at": 1764200000, "submitted_at": 1764203000,
                     "summary": { "score": 20, "maximum": 60, "correct": 6, "incorrect": 5, "skipped": 4 } } }
    ],
    "page": 1,
    "pages": 1,
    "total": 3
  },
  "result_adds": { "test_kind": "misfire", "misfire": { "understood": 3, "total": 15 } }
}
```

**6. What the website decided** (28 Nov 2026): a Misfire Mock's result is **not counted** in Misfire's chapter report, so one question is never counted twice; a question already "Samajh gaya" before the mock and wrong in it **stays** "Samajh gaya"; a question wrong or left in the mock does not become a second Misfire item, and stays open under its first id `<attempt id>:<question id>`.

**Until all of this is built, keep `misfire` off.** Then tell the app side, with the switch still off: the first real end-to-end run is on a test account (rule 20), and only then the switch goes on. On the app side, door A's `misfire` reaches production with the owner's next Publish; nothing else waits for the app.

**Checked on 28 Nov 2026** (`tests/misfire_web_check.py`, 37 checks, to the agreed contract; the browser answered in place of the website, and nothing was written). With the switch as the website answers today (not said): no tab, and nothing changed anywhere (Misfire's tabs, a link to `?tab=web`, the setup, Student Choice); door C never asked. With the switch on: the tab right after "Sab"; the list (one not started, newest first, opening its paper's page; one being taken with "Resume"; a finished one with its score and size); the result's count, and no card on a retry's result; the setup asking door C (404, then 503, then a paper) with **one** `request_key` for all three; the five sentences of the table word for word; "maange 5, mile 3" before the paper; the chosen chapters sent by name, under a new key; the made paper's page; My Tests' label; Offline Misfire unchanged. On the app's server, `misfire` is `true` only for an exact `true` (`backend/tests/test_choice.py`).

**Not checked:** anything against a real website door (none exists yet); a Misfire Mock started on the website and finished in the app, or the other way round; a real phone.

# Part 5 — Rapid Fire in a browser: the app's, linked from the website

## 5.1 What it is, and who owns it

**Rapid Fire** is the app's game: 20-second formula cards, duels with friends, Gang War, Cup Night and All India Rapid. It is the app's own part. It runs on the app's server and its data (cards, coins, diamonds, friends, ranks) lives there.

**Rapid Fire also runs in a normal browser** (phone, iPhone, laptop) at:

```
https://jeelive-mobile.emergent.host/api/arena
```

This is the app's own live server. If the app's live address ever changes, the arena is `<new address>/api/arena`.

- It was built by **the app side** on 15 Nov 2026, from the owner's plan "students of the website can play Rapid Fire in a browser too". **The website agent did not build it and does not need to.** It is the app's own screens, made for the web, with only Rapid Fire in them.
- A student signs in there with **the same phone number and PIN as on the website** (Part 6). It is the same id, the same coins and diamonds, and the same friends as in the app.
- On a laptop it stays a phone-wide column on the blood-red stage. Home in its bar goes to jeelive.ai. The student's own profile has "Account & sign out".
- It is also what a person without the app gets from a match link ("Play in your browser").

- Picture `shots/r01_arena_laptop.jpg`: 24. Rapid Fire in a laptop's browser, from the app's server

## 5.2 What changed for it (26 and 27 Nov 2026)

The browser copy has to be built again whenever the app's screens change. Building it is one command on the app side, followed by the owner's Publish. It is not a code change.

- **26 Nov 2026:** built again with **All India Rapid's "Misfires" tab** (Part 4.5). This copy is in production since the owner's Publish of that day.
- **Found on 27 Nov 2026: in production its icons are empty boxes.** The copy's icon font sat in a folder that does not travel with a Publish, so production answers 404 for it. On the sign-in screen the phone, the lock and the eye are drawn as empty boxes, and so is every other icon that comes from that font; words, pictures and the game itself are right. The preview read the font from its own disk, so it was not seen there. **Mended on 27 Nov 2026, on the preview:** the font now ships under a name that travels; the build refuses to put a copy in place when one of its files would be left out of a Publish; and a test asks the app's server for every file the copy's pages name (`backend/tests/test_arena_web_complete.py`).
- **27 Nov 2026, the same new copy:** on a slow device the browser Rapid Fire now notices it and rests its decoration and its celebrations, as the app does; scores, coins and the game do not change. The copy talks only to the server it was opened from: no address of a workspace is in it (the build refuses one).
- Students got the new copy **with the owner's Publish of 28 Nov 2026**. The state in production is read when this book is built (Part 0.2 and Part 3.7).

Nothing in the address, the sign-in or the website's part changes with a rebuild.

## 5.3 What the website does: a link, nothing else

1. Put a **"Rapid Fire"** card or button on the website's Home, near the top (next to the All India series or the practice area):
    - title "Rapid Fire";
    - line "20-second formula duels with friends. Same account." (an earlier note said 15 seconds; every card of Rapid Fire has 20 seconds);
    - button **"Play now"**, which opens `https://jeelive-mobile.emergent.host/api/arena` in the same tab.
2. Put a "Rapid Fire" item with the same link in the main menu. Optionally, add "Revise in Rapid Fire" on the result page.
3. **The link is a plain link:** no session, no cookie and no PIN in it.
4. "Rapid Fire" is always written as two words, both capitalised. The name and logo are JEELIVE.AI's own, the same on both sides.

**The website must not** copy Rapid Fire's code, cards or rules into its own project, keep a second copy of Rapid Fire's data, or change anything under `/api/arena` or `/api/rf/…`. Those are the app's. When the website wants something in Rapid Fire changed, it asks the app side in writing.

## 5.4 Later, not built: open Rapid Fire from the website without typing the PIN again

Today a student who is signed in on the website types the phone and PIN once more in the browser Rapid Fire. The plan to remove that is written down and **not built**. The website stays the only place that checks the phone and PIN, and the arena never sees the PIN or the website's cookies.

- **New website door (signed-in student only):** `POST /api/arena/ticket`. It makes a random one-time ticket (32 or more random bytes), stores only its SHA-256 hash with the student's id, and keeps it valid for 60 seconds and one use. It answers `{ "url": "https://<arena address>/api/arena/sso?ticket=<ticket>" }`. The website's Rapid Fire button would call it and open that url.
- **New website door for the app's server only** (server to server, behind a shared secret header): `POST /api/internal/arena/ticket/redeem { "ticket": "…" }`. It marks the ticket used in one step (failing if it is expired, used or unknown) and answers `{ "user_id": "<the same student id>", "name": "…", "pin_version": <n> }`.
- The app's server then gives the browser its normal Rapid Fire session and removes the ticket from the address bar.
- **Rules:** a ticket is never logged and never sent to analytics; that page sends no referrer; one use; 60 seconds at most; the student id never changes.

**Build this only when the owner asks for it.** The app side builds its half at the same time.

## 5.5 Not checked

- The website's Rapid Fire button: whether it is on jeelive.ai today was not checked by the app side.
- The copy of 27 Nov 2026 in production went with the owner's Publish of 28 Nov 2026; whether production serves it, and its icon font, is read when this book is built (Part 0.2). Only on the preview was it walked in a browser at a phone's width, at 320 points and at a laptop's width, at full motion and at rest: it opens, signs in and plays a practice round answered by the browser (picture 24 is the copy of 26 Nov).
- A real slow phone: the rest on a slow device was checked in a browser slowed down on purpose, not on a phone.

# Part 6 — One account for the website and the app

## 6.1 The rule, and how it already works

The owner (26 Nov 2026): a student who signs up on the website can sign in to the app, and one who signs up in the app can sign in on the website, whenever they like. The two together make **one user list**, and one sign-up gives the student everything on both sides.

**This is already how it works.** It was checked from the app's code and its live answers on 28 Nov 2026:

- **The app has no account system of its own.** Signing up, signing in, the session, renewing it, changing the PIN and signing out are all **the website's own doors**. The app's server passes them on unchanged to `https://jeelive.ai/api/…`.
- So **an account made in the app is a website account**, and the same phone number and PIN sign in on jeelive.ai. **An account made on the website signs in to the app** at once. Nothing is copied from one side to the other: there is only one account, the website's.
- **One user list:** the website's. The app's server keeps only the app's own extras (Rapid Fire profile, coins, diamonds, friends, Dream College, Mission) under the **website's own student id**. It reads that id from the website's `GET /api/auth/me` and never makes up an id of its own.
- **The browser Rapid Fire** (Part 5) signs in the same way, with the same id.

- Picture `shots/a01_signin.jpg`: 25. The app's sign-in screen: the same phone number and PIN as on jeelive.ai

## 6.2 Every door the app uses for accounts

All of them go through the app's server, at `…/api/jl/<path>` of the app, to `https://jeelive.ai/api/<path>`, with the website's own cookies. The cookies are kept on the app's server for each device, never on the phone.

| What the student does in the app | The website's door | Sent | What the app needs back |
| --- | --- | --- | --- |
| Sign up | `POST auth/phone/signup` | `phone`, `pin`, `confirm_pin` | the student (with `id`) and the session cookies |
| Sign in | `POST auth/phone` | `phone`, `pin` | the same |
| Open the app | `GET auth/session` | — | `{ "user": … }`, or `user: null` when signed out |
| Session renewal | `POST auth/refresh` | — | new cookies |
| Who am I | `GET auth/me` | — | the student, with the same `id` |
| Change PIN (signed in) | `POST auth/pin` | `phone`, `new_pin`, `confirm_pin` | success. Other sessions end; this one stays, and its `id` must not change |
| Sign out | `POST auth/logout` | — | success |
| Forgot PIN | on the app's server: `POST /api/account/forgot-pin`. The website has no public reset, so the app's server uses the website owner's own reset for that number | — | — |

The exam a student chose, papers, attempts, results, Misfire and the All India series are all read from the website under the same session (Parts 1 to 4).

## 6.3 What the website must keep, so it stays one account

1. **The doors of Part 6.2 and their fields**, as they are. Above all, `user.id` in the answers of `auth/phone`, `auth/phone/signup`, `auth/session` and `auth/me`.
2. **A student's `id` never changes.** Not on a PIN change, not on a phone change, not ever. The app's extras (coins, friends, Rapid Fire ranks, Dream College) hang on it. A new id would leave the student without them.
3. **One phone number = one account.** Signing up again with a number that already has an account must be refused with a plain sentence ("this number already has an account: sign in"), never answered by making a second account.
4. **The same PIN rules on both sides.** The app checks a PIN's shape before sending it and shows the website's own message when the website refuses one.
5. **Never a second user list.** The CEO dashboard joins the two sides on this one `id` (the `uid` of its export); the app's server keeps no copy of phone numbers to edit. It keeps only what it needs for friend search: a one-way hash and the last four digits.
6. A new sign-in door (an OTP, a login with Google…) must give the **same** student id for the same person. Tell the app side before such a door goes live.

## 6.4 What is not automatic

- **Being signed in on one device or browser does not sign another in.** On a new phone, or in the browser Rapid Fire, the student types the same phone and PIN once. Opening the browser Rapid Fire straight from a signed-in website, without typing again, is the plan of Part 5.4: written, not built.
- **Signing out in the app** sends the website's own `auth/logout` for that device's session, and forgets the account on that phone.

## 6.5 Deleting an account

- The app has an in-app "delete my account" request (and a public web page for Google Play). It **erases the app's own extras at once** and signs every device of that account out of the app.
- **The website has no door to delete an account.** The website account is deleted **by the owner on the website by hand**, within 30 days, from the list in the app's owner panel. While a request waits, the app does not sign that account in again.
- If the website ever adds a delete door, tell the app side: the request can then be finished in one step.

## 6.6 How it was checked (28 Nov 2026)

- The app's code: sign-up, sign-in, session, renewal, PIN and sign-out are only ever sent to the website's doors above (`frontend/src/auth.tsx`, `frontend/src/api/client.ts`, `backend/jl_proxy.py`). Rapid Fire takes its id from the website's `auth/me` (`backend/rf_access.py`).
- The live answers: the website's `GET /api/auth/session` answers for a signed-out visitor (Part 3.7). The test learner's account is a website account: its papers, results and Misfire are the website's, and it signs in to the app and to the browser Rapid Fire with the same phone and PIN.
- **Not done by the app side:** a brand-new account made in the app and then used on jeelive.ai (it would add a real account to the website's list). The website agent can do it on its test setup: sign up in the app's preview with a throw-away number, sign in on the website with the same number and PIN, and check that `auth/me` gives the same `id` on both.

# Part 7 — Working together: the website's doors the app uses

## 7.1 Why this part is here

The website can be changed any day. **An app in a student's phone cannot:** it changes only when the student installs a new build, and phones keep an old build for months. So every answer of the website that the app reads is, in effect, a promise. This part lists those answers, so that the website's own work never breaks the app unseen:

- **7.2** every door of the website the app uses today (64 of them);
- **7.3** how the app's server reaches the website, and what it does with what comes back;
- **7.4** what may change freely, what may not, and how a change is agreed;
- **7.5** the doors the app already asks for that the website has not built;
- **7.6** what was checked, and what was not.

The list of 7.2 is not written from memory: when this book is built, every door named in the app's own code is looked up in it, and the build stops if one is missing.

## 7.2 Every door of the website the app uses

**How to read the tables.** A door is written without its beginning: `GET /my/tests` is `GET https://jeelive.ai/api/my/tests`. `<id>` stands for an id (of a paper, an attempt, a question, a job, a Misfire item) or, in the exam doors, for the exam's slug (`jee-main`, `bitsat`, `comedk`). The phone never calls the website itself: it calls the app's server (`…/api/jl/<the same path>`), which passes the call on **unchanged**, with the student's own website cookies (Part 7.3). Doors marked **(server)** are called by the app's server on its own.

**The account** (the whole story: Part 6.2)

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `POST /auth/phone/signup` | sign up | `phone`, `pin`, `confirm_pin` | the student with `id`; the session cookies |
| `POST /auth/phone` | sign in | `phone`, `pin` | the same. **A wrong PIN is answered 401 or 403** (the app's server counts them, Part 7.3) |
| `GET /auth/session` | every time the app opens; after a 401 | — | 200 with `user` (an object with a text `id`) or `user: null`. Anything else is read as "could not be checked" and tried again |
| `POST /auth/refresh` | renewing the session | `{}` | 200 with a JSON object and new cookies; **401 with a plain message** when the session is really over |
| `GET /auth/me` | who am I; **(server)** the id Rapid Fire plays under | — | the student with the same `id` |
| `POST /auth/pin` | change the PIN | `phone`, `new_pin`, `confirm_pin` | success; this session stays, the `id` stays |
| `POST /auth/logout` | sign out | `{}` | success |
| `POST /auth/login` | **(server)** the owner's own account, for the two doors below | the owner's email and password | the owner's session |
| `GET /admin/students` | **(server)** Forgot PIN: find the account of a number | `?q=<number>` | `items[]` with `phone` and a whole-number `pin_version` |
| `POST /auth/owner/student-pin-reset` | **(server)** Forgot PIN: set the new PIN | `phone`, `new_pin`, `confirm_pin`, `expected_pin_version` | 200 |

**Exams and the lists of papers**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /catalog/exams` | Home's exams | — | `items[]`: `slug`, `name`, `shown`, `order`, `sections` |
| `GET /catalog/exams/<id>` | an exam's page and its sections | — | `sections[]`: `slug`, `name`, `layout` (`list` or `chapters`), `hidden`, `order`, `live_count`. **404 = the owner has hidden the exam** |
| `GET /exam-navigation/<id>/catalogue` | every list of tests; **(server)** the chapters of Student Choice | `?kind=` (`mocks` or `chapters`) `&section=&subject=&q=&page=` | the fields of Part 1.5; `pages` |
| `GET /exam-navigation/<id>/history` | previous years' papers; Misfire's paper tabs | `?page=` (Misfire also `kind=`) | the list and its paging |
| `GET /pyq/jee-main` | the PYQ page | — | the years, their papers, each paper's own `attempt` |

**A paper, before it starts**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /my/sets/<id>` | the paper's page; the paper's `test_kind` for the Dream College meter | — | `test_kind`, `saved`, the student's own `attempt` |
| `GET /sets/<id>` | the same page for a visitor without a session | — | the paper |
| `POST /sets/<id>/preflight` | the device check before the start | `preview: false`, `test_response: "25"` | 2xx = may start; a refusal's `error.message` is shown |
| `POST /sets/<id>/start` | start | `start_key`, `device_checked: true`, `preview: false`, `get_ready: true` | the attempt's `id` and `status`. A retry sends the same `start_key` |
| `POST /my/tests/saved/<id>` | save a paper for later | `{}` | success |
| `DELETE /my/tests/saved/<id>` | take it off the saved list | — | success |

**The paper being taken**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /attempts/<id>` | the player | — | `set_id`, `questions[]` with `id` and `type` (`integer` for a typed answer), the clock |
| `POST /attempts/<id>/begin` | the get-ready minute is over | `{}` | `server_now`, `ready_until`, `deadline` |
| `PUT /attempts/<id>/answers/<id>` | saving one answer (the second `<id>` is the question's) | the answer; `timeline` when time events ride along | `timeline_cursor` |
| `POST /attempts/<id>/visit` | a question was opened | `question_id` | success |
| `POST /attempts/<id>/timeline` | time events on their own | a batch | `cursor` |
| `POST /attempts/<id>/bonus` | entering the bonus part | `{}` | `bonus_unlocked_at` |
| `POST /attempts/<id>/submit` | hand in | `timeline` when there is one, else `{}` | the receipt |
| `GET /attempts/<id>/assets/links` | the pictures of a paper, in parts | `?kind=solution`, `format=webp`, `look=cut`, `score_version=` (each only when needed) | `limit`, `total`, `parts[]`. **403 or 409 = these pictures are not given in parts**: the app then asks for them one by one |
| `GET /attempts/<id>/questions/<id>/asset/question/<n>` | one picture (also `…/asset/solution/<n>` and `…/asset/piece/<n>`) | `?score_version=`, `format=webp`; `If-None-Match` | the picture; `ETag`; 304 when unchanged; 429 = busy (with `Retry-After`) |

**The result and the analysis**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /attempts/<id>/results` | the result; a paper's Misfire page | `?score_version=` | `set_id`, the questions' ids, `test_kind` |
| `GET /attempts/<id>/analysis` | the analysis | `?mode=` (`personal`, `comparative`) `&compare=&score_version=` | the analysis; `score_version` |
| `GET /attempts/<id>/analysis/report.pdf` | the A4 report | `?score_version=` | a PDF file |
| `GET /attempts/<id>/analysis/share.png` | the scorecard picture | — | a PNG file |
| `GET /attempts/<id>/leaderboard` | a paper's leaderboard; the All India day leaderboard; the Rank journey | `?q=` | `state`, `n`, `rows`, `around`, `found`, `you`; a row: `rank`, `name`, `handle`, `score`, `attempted`, `accuracy`, `time`, `is_you` |
| `GET /attempts/<id>/journey` | the result's Progress tab | — | `state` (`available` or not) |
| `GET /attempts/<id>/historical-rank` | the result's Rank tab | `?score_version=` | `kind` |
| `GET /attempts/<id>/ai-solutions` | the AI's step-by-step solutions | — | the solutions |
| `POST /attempts/<id>/questions/<id>/solution-open` | a solution was opened | `{}` | success |
| `POST /attempts/<id>/questions/<id>/report-wrong` | "this question is wrong" | `category`, `context: "solutions"`, `note` (600 letters at most) | the receipt |
| `PUT /attempts/<id>/reviews/<id>` | the student's review of one question | `request_id`, `revision`, `score_version`, `category`, `note`, and the review's ticks | the saved review |
| `PUT /attempts/<id>/learnings` | "what I learnt" | `items[]` | `items[]` |
| `POST /attempts/<id>/retry` | take the paper again | `start_key`, `score_version` | the new attempt |
| `GET /jobs/<id>` | a result still being made | — | the job's state |
| `POST /jobs/<id>/retry` | make it again | `{}` | success |

**My Tests, Misfire, the All India series**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /my/tests` | My Tests; the Dream College meter's first read on a new phone | `?tab=&page=&q=&status=&exam=` | `items[]` |
| `POST /my/tests/compare` | compare two papers | `left`, `right` | the comparison |
| `GET /my/misfire/summary` | Misfire's counts | — | Part 4 |
| `GET /my/misfire` | Misfire's list | `?status=&subject=&chapter=&page=` | Part 4; an item's id is `<attempt id>:<question id>` |
| `GET /my/chapters` | Misfire's chapter report | — | Part 4 |
| `POST /my/misfire/<id>/try` | "Check karo" | `value` | `correct`, `item` |
| `POST /my/misfire/<id>/done` | "Samajh gaya" | `{}` | success |
| `POST /my/misfire/<id>/reopen` | "Wapas list mein" | `{}` | success |
| `GET /series/all-india-jee` | the All India series; **(server)** its `last_date`, every 15 minutes, for Home's card | — | `first_date`, `last_date`, `today`, `total`, `slots[]` |
| `GET /series/all-india-jee/history` | the student's days | `?page=` | the days and their attempts |
| `GET /series/all-india-jee/streak` | the streak | — | the streak |
| `PUT /profile/display-name` | the name on leaderboards | `name` | `display_name` |

**Asked today, not built yet on the website** (they answer 404; the app waits: Part 7.5)

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /choice/bank` | **(server)** Student Choice, door A; the Misfire Mock's switch `misfire` | `?exam=jee-main` | Part 1.6; Part 4.8 |
| `GET /choice/chapters/<id>/questions` | **(server)** Student Choice, door B | `?page=` | Part 1.6 |
| `POST /choice/papers` | Student Choice, door C; the Misfire Mock (`mode: "misfire"`) | Part 1.6; Part 4.8 | Part 1.6; Part 4.8 |
| `GET /my/misfire/mocks` | the Misfire Mock's list, asked only while door A says `"misfire": true` | `?page=` | Part 4.8 |
| `GET /matched` | **(server)** Matched: the list, every 2 minutes | — | Part 2.4c |
| `GET /matched/<id>` | **(server)** Matched: one shift | — | Part 2.4c |
| `GET /series/all-india-jee/leaderboard` | the whole-series leaderboard | `?q=` | Part 7.5 |

## 7.3 How the app's server reaches the website

**One address.** Every call above arrives at the website **from the app's server**, never from a student's phone or browser. So the website sees a small number of addresses (the app's servers) for all app students.

- **The student's own address** is sent in `X-Forwarded-For`: exactly one address, checked by the app's server; what a caller wrote into that header himself is never passed on. **A limit the website keeps per address must count this header when the call comes from the app's server**, and must never treat the app's server as one student. (June 2026: the website's limiter stopped sign-ins that came through the app's server, because they all arrived from one address; the header was added then. Whether the website counts it today was not checked by the app side: Part 7.6.)
- **Cookies.** The website's cookies of each device are kept on the app's server, never on the phone. They are sent back as one `Cookie` header. What the app's server understands of a `Set-Cookie`: the name, the value, and **`Max-Age=0` or an empty value = this cookie is gone**. It does not read `Path`, `Domain` or `Expires`. So: **to take a cookie away, send `Max-Age=0` (or an empty value)**; a cookie taken away only by an `Expires` in the past stays in use.
- **The access cookie is named `access_token`.** Student Choice's chapter list is read with that one cookie alone (so that this read can never renew or end the student's session). Under another name the list would stop.
- **Headers passed on to the website:** `Accept`, `Content-Type`, `If-None-Match`, `If-Modified-Since`, `If-Range`, `Range`. **Passed back to the phone:** `Content-Type`, `Retry-After`, `Location`, `Cache-Control`, `ETag`, `Last-Modified`, `Content-Range`, `Accept-Ranges`. No other header of the website reaches the app.
- **Redirects are not followed.** A 301, 302, 307 or 308 on an API door reaches the app as a failure. Answer the door itself, at the address written here, over https.
- **Never two session calls at once.** For one device, `auth/session`, `auth/refresh`, `auth/phone`, `auth/phone/signup`, `auth/pin` and `auth/logout` are sent one after another, never together, also across the app's server processes. A refresh token is therefore never used twice by the app.
- **Nothing private is logged:** not a PIN, not a cookie, not a request's body. A PIN is passed on and never kept. A device's cookies unused for 90 days are removed.

**How long the app waits, and what it tries again**

| What | The rule |
| --- | --- |
| The app's server waits for the website | 28 seconds (a picture: 22); 4 seconds to connect |
| The phone waits for the app's server | 32 seconds (a file: 60; a picture: 25) |
| A read (`GET`) that fails with 408, 500, 502, 503, 504, 520, 522, 524, or does not connect | tried **once** more after a quarter second (or after `Retry-After`, when it is under two seconds). The session doors are not tried again, except `auth/me` |
| A write (`POST`, `PUT`, `DELETE`) | **never sent twice** by the app's server. When the student tries again, a paper's start carries the same `start_key` and a made paper the same `request_key`: the website must answer the same thing for the same key |
| 401 on any door but the session doors | one `auth/refresh`, then the call once more. If the refresh is refused with a plain message, `auth/session` is asked; `user: null` signs the student out. **An empty 401, or one without a plain message, is not taken as "signed out"** |
| Ten wrong PINs for one number in 15 minutes (401 or 403 on `auth/phone`) | the app's server stops sign-in for that number itself (429) until the 15 minutes pass. This is the website's own limit, kept in step so that the website's "tries left" stays true |

**When the website is in trouble**

- **The shield.** When 8 or more calls in 10 seconds fail, and they are at least half of the calls, the app's server stops calling the website for 5 seconds (then 10, 20, 30 at most), and lets one call through to see. "Fail" = no connection, a time-out, an answer slower than 10 seconds, or 502, 503, 504, 520 to 527, 530. Meanwhile the student reads "The website is not answering right now. Your saved work is safe." So **an outage of the website is not made worse by the app**, and Rapid Fire, which runs on the app's server, keeps playing.
- **An HTML page is never shown to a student.** A 5xx whose body is not JSON with a plain `error.message` (a Cloudflare page, a stack trace) is replaced by the sentence above.
- **For planned work, answer 503** with JSON, a plain `error.message` and `Retry-After` in seconds: the student reads the website's own sentence. (While most calls are answered so, the shield is shut and the student reads the app's sentence instead.)

**What an answer looks like to the app**

| What | The rule |
| --- | --- |
| A good answer | plain JSON, or the envelope `{ "data": …, "error": null, "meta": { "api_version": … } }`. The envelope is opened only when `meta.api_version` is there. Its value is not compared: **a new `api_version` alone tells the app nothing** |
| A refusal | `error.message` (or `detail`) in plain words is shown to the student **as it is**; `error.code` is read where Part 1 and Part 2 say so; `Retry-After` in seconds or as a date |
| 204 | accepted as success without a body |
| A good status with a body that is not JSON | "The server response was incomplete": the student is asked to try again |
| Words | `Physics`, `Chemistry`, `Mathematics`; `test_kind` and `kind` exactly as Parts 1, 2 and 4 write them |

**How much the app's server may ask at once** (its settings, **not a measured capacity**): 400 connections to the website for each server process, kept open 45 seconds; when more than 3000 calls of one process are waiting for the website, new ones are answered "busy" at once. The two sides have never been load-tested together (Part 7.6).

## 7.4 Changing a door: what is free, what is not, and how it is agreed

**Free, at any time, without telling anybody**

- A **new field** in an answer. The app reads fields by name and leaves the rest.
- A **new door**.
- Different numbers, words and lists inside the fields that exist (more papers, another exam, a section hidden): that is the website's daily work, and the app follows.
- Making a door faster.

**Not free: tell the app side first** (through the owner, in writing: the door, the answer before and after, the day)

- Renaming, removing or re-typing a field named in this book (a number that becomes text, a list that becomes an object, `null` where an object was).
- A door's address or method; a parameter's name.
- What a status means on a door (above all 401, 403, 404 and 409 where 7.2 gives them a meaning).
- The envelope, the shape of `error`, the cookies' names, the session doors.
- A new limit per address or per account that could meet the app's server (7.3).
- A student's `id`, an attempt's id, a paper's id: they never change (Part 6.3).

**How such a change is made safely**

1. **The new thing comes beside the old:** a new field next to the old field, a new door next to the old door. The old one keeps working.
2. The app side says which app builds read the old one, and builds the new reading. The owner publishes; new builds go to the stores.
3. **The old one is removed only when the owner says so**: phones keep old builds for months, and an old build that meets a missing field shows an error, an empty page, or nothing at all.
4. **First on the test setup** (rule 20 of Part 0.4), then for students.

What the app side promises in return: it asks for nothing that is not in 7.2; when it starts using a new door or a new field, the next version of this book lists it; `/api/arena` and `/api/rf/…` stay the app's own (Part 5).

## 7.5 Doors the app already asks for

The app asks these today and gets 404. **Nothing breaks; a part of the app simply waits.** The day the door answers in the agreed shape, that part appears by itself, without a new app build.

| Door | What appears | The shape |
| --- | --- | --- |
| `GET /api/choice/bank?exam=jee-main`, `GET /api/choice/chapters/<set id>/questions`, `POST /api/choice/papers` | question picking and the random mock | Part 1.6 |
| `GET /api/matched`, `GET /api/matched/<shift id>` | the real shifts of Matched | Part 2.4c |
| `GET /api/series/all-india-jee/leaderboard` (and `?q=<name or Rank>`) | a "Poori series" tab on the AITS Leaderboard, with its Rank card and share card | below |
| `"misfire": true` in `GET /api/choice/bank?exam=jee-main`; then `POST /api/choice/papers` with `mode: "misfire"`, `GET /api/my/misfire/mocks`, and `misfire` in a result | Misfire's "Mock" tab and the Misfire Mock. The last three are asked only once door A says `true`; all agreed with the website on 28 Nov 2026 | Part 4.8 |

**The whole-series leaderboard** (the app side's earlier note, repeated here so that it is in one book). The same envelope and the same row as `GET /api/attempts/<id>/leaderboard`, plus three fields:

```json
{
  "state": "ready",
  "n": 5120,
  "title": "All India JEE Mains · poori series",
  "days_counted": 12,
  "maximum": 3600,
  "min_finishers": 10,
  "query": "",
  "rows": [ { "rank": 9, "name": "Arjun Sharma", "named": true, "handle": "<the same for a student on every day>",
              "score": 3075, "days": 11, "attempted": 770, "accuracy": 92.3, "time": 104500, "is_you": false } ],
  "around": [],
  "found": [],
  "you": null
}
```

- New: `days_counted` (how many released live days are added up), `maximum` (optional), and `days` in a row (how many of them this student handed in).
- Only live attempts of released days count; a student's first attempt of a day; the same tie-break and the same names as on the day leaderboard. The app never adds up Scores itself.
- **The app shows it only when the shape is whole:** `state` and `n` there, `days_counted` a number, `rows` and `around` lists, and every row (and `you`, when not `null`) with number `rank`, `score`, `days` and text `name`, `handle`. **Until it is ready, keep answering 404.** A half-built answer stays hidden.

## 7.6 What was checked, and what was not

**Checked on 28 Nov 2026**

- **The list against the code:** every door the app's screens name in their code is in 7.2 (the build of this book stops otherwise). The doors of the app's server were read from its code (`backend/jl_proxy.py`, `choice.py`, `matched.py`, `rf_access.py`, `pin_reset.py`, `account_deletion.py`, `owner_panel.py`).
- **A read-only walk** (`tests/website_doors_walk.py`): 30 screens of the app's preview were opened as the test learner, and every call to the website was written down. Signing in was the one write; nothing was started, answered, saved or submitted. 21 doors were seen: 19 answered 200; `auth/refresh` answered 401 once, before sign-in, as it should; `series/all-india-jee/leaderboard` answered 404 (7.5).
- **The rules of 7.3** were read from the app server's code (`jl_proxy.py`, `jl_transport.py`, `website_shield.py`, `session_coordination.py`, `login_guard.py`) and from the app's (`frontend/src/api/client.ts`).
- **Misfire's two mocks (28 Nov 2026):** Offline Misfire and the Misfire Mock were walked on the preview with the website's answers played by the browser (Parts 4.7 and 4.8). Nothing was written to the website.

**Not checked**

- **The doors that write** (start, begin, answers, visit, bonus, submit, timeline, retry, reviews, learnings, report-wrong, solution-open, save, compare, the name, the PIN, sign-up, Misfire's three buttons) were not called on this walk: the test learner is the owner's own account on the real website. They are in 7.2 from the code.
- **Whether the website counts `X-Forwarded-For`** from the app's server for its own limits today.
- **The two sides under load.** No test has put many students through the app's server and the website together. No number of students at once is claimed for the pair.
- **A change made the way 7.4 says** has not been walked yet: the first one is the test of the method.
