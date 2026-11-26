<div class="box sky" markdown="1">

### Owner ke liye (short)

- Yeh **website ko dene wala hand-off, version 4** hai ({{TODAY}}). Version 3 ki saari baatein isme hain; **naya kya hai**, woh theek neeche ke box mein hai.
- {{OWNER_PROD_LINE}}
- Isme chheh cheezein hain: **Student Choice** (Part 1), **Matched** (Part 2), **Misfire** (Part 4: website ka hi, app sirf dikhata hai), **browser wala Rapid Fire** (Part 5: app ka, website sirf link lagati hai), **ek hi account** (Part 6: website ya app, kahin bhi sign up karo, dono jagah wahi phone + PIN chalta hai; yeh pehle se aisa hi hai), aur **saath kaam karne ke niyam** (Part 7, naya: app website ke kaun-kaun se darwaze use karta hai, aur website koi darwaza badalne se pehle kya kare, taaki students ke phone mein app kabhi na toote).
- **Student Choice aaj chalta hai**: student chapters tick karta hai (naam likh kar dhoondh bhi sakta hai) aur har chune chapter ka poora test deta hai. Sawaal JEE Main ke chapter-wise sawaal hi hain; alag bank nahi hai.
- **Naya rang (26 Nov):** Student Choice ke upar ka card result page jaisa gehra laal, aur Physics / Chemistry / Maths ke chamakte rangeen tabs (laal, amber, teal). Neeche ke cards safed hi hain. Banaye paper ke subject-wise minute ab hamesha total ke barabar judte hain.
- **Sawaal khud chunna aur random mock abhi band hain** ("Jald aa raha hai"). Website teen darwaze banayegi (Part 1.6), tab yeh dono app update ke bina khul jayenge.
- **Time ka ratio** (25 Maths = 80 min, 25 Physics = 60 min, 25 Chemistry = 40 min) banaye hue paper par lagega. Poore chapter test abhi 60 min ke hi hain; unka time sirf website badal sakti hai. Aapka faisla (26 Nov): unhe bhi yahi ratio, par **zyada se zyada 3 ghante** (Part 1.8).
- **Dream College meter**: chapter test aur Student Choice paper kabhi nahi ginte, chahe kitne bhi lambe hon.
- **Matched**: app taiyaar hai. Super admin har shift ke baad matched sawaal daalega aur unka ek asli paper banayega. Home ka Matched card **pehla asli shift publish hote hi, usi din** aa jayega; AITS ke bache dinon mein All India series us card ke theek neeche ek bar ban jaati hai. (Koi shift na ho to bhi {{CARD_DAY}} se card aa jayega.)
- **Misfire**: website aur app ka Misfire ek hi hai (website ka). Website agent ko Part 4.4 ki 6 baatein check karni hain. All India Rapid ka "Misfires" tab Rapid Fire ka apna hai, alag.
- **Rapid Fire browser mein**: app ke server par chalta hai; website ko sirf "Rapid Fire" button / link lagana hai, code nahi lena (Part 5). **27 Nov ko mila:** production mein iske icons khaali dibbe dikh rahe hain (icon ki file Publish ke saath gayi hi nahi thi). Preview par theek kar diya hai; agle Publish se students ko theek dikhega.
- **Students tak kab:** 26 Nov ke Publish (14:40 UTC) mein version 3 tak ka saara kaam server par pahunch gaya (pehli shift wala rule, AITS bar, 3 ghante wala sentence, naya rang, 26 Nov wala browser Rapid Fire). Screens phone mein tabhi badalti hain jab us Publish ke baad bana naya app build install ho. 27 Nov ka kaam (icons, slow phone par aaram, sample ki rok) agle Publish ke saath jayega.
- Website agent ko yeh PDF (ya saath ki `BOOK.md`) dena hai. Super admin ke kaam ke hisse: Part 1.11, Part 2.8, Part 2.9 aur Part 6.5.

</div>

<div class="box" markdown="1">

### New in version 4 ({{TODAY}}): all that a reader of version 3 needs

1. **Where things stand has changed** (Part 0.2). The owner published on 26 Nov 2026 (live at 14:40 UTC): the app's server in production now has everything of version 3. What is still only on the preview is said there, row by row.
2. **Rapid Fire in a browser** (Part 5.2). In production its icons are empty boxes: the icon font never reached production. Found on 27 Nov 2026 and mended on the preview; students get it with the owner's next Publish. The same new copy rests its decoration and its celebrations on a slow device. **Nothing for the website to do.**
3. **Part 7 is new: working together.** Every door of the website the app uses ({{DOOR_COUNT}}, checked against the app's code when this book is built), how the app's server reaches the website, **what the website must not change without telling the app side**, how a change is agreed, and the doors the app already asks for (among them the whole-series leaderboard of the All India series).
4. **Two more rules in Part 0.4** (25 and 26): never a redirect or an HTML page on an API door; tell the app side before a door changes.
5. **A made-up sample is never shown outside the app's own workspace** (Part 2.12). Before, this was only a rule for people; since 27 Nov 2026 the app's server keeps it by itself.
6. Parts 1, 4 and 6 say what they said in version 3. In Part 2 only the lines about production and about the samples changed.

</div>

## 0.1 What is in this hand-off

Two new features, three things the website must know so that the website and the app stay one, and (new in version 4) how the two sides work together:

**Student Choice** (Home's fourth tile, marked NEW). The student goes through the JEE Main chapter-wise questions his own way.

- **Today:** tick chapters in Physics, Chemistry and Maths (a search box finds any chapter by name), then take each ticked chapter's whole test, one after another.
- **Later, when the website can make such papers:** see the ticked chapters' questions **without options**, tick the ones wanted and get **one paper** made of them (75 questions at most); or ask for a **random mock** of N questions.

**Matched.** After every JEE Main shift, the questions of that shift that matched JE Live's own questions are shown side by side: the JEE Main question, and under it the question of ours it matched. Open to everyone, signed in or not. A signed-in student attempts all of ours in one **real paper** ("Attempt all matched"); a person without an account is asked to sign up first. On Home, the All India series card gives its place to the Matched card as soon as the first shift is published; for its remaining days the series is a bar right under that card.

**Misfire** (Part 4). Every wrong or left question of a finished paper, to be solved again. **It is the website's own**; the app shows it as it comes. The website agent checks six points so the two stay the same.

**Rapid Fire in a browser** (Part 5). The app's game also runs in any browser from the app's own server. **It is the app's**; the website only links to it.

**One account** (Part 6). Signing up or signing in, in the app or on the website, is the same account: the website's. **It already works so**; the website keeps its sign-in doors and its student ids as they are.

**Working together** (Part 7). Every door of the website the app uses, how the app's server reaches the website, and how a change to a door is agreed. An app in a student's phone cannot be changed without a new build, so the website must know what the app reads.

## 0.2 Where things stand on {{TODAY}}

| What | State | Waits for |
| --- | --- | --- |
| Student Choice: Home tile, first screen, chapter list, chapter search, the ticked chapters' whole tests | **Works.** The app's server in production has it since 26 Nov 2026 (the screens: see the note under this table) | nothing |
| Student Choice: a chapter's questions without options, one paper of ticked questions | Built in the app, **closed** (shown under "Jald aa raha hai") | the website: doors A, B and C (Part 1.6) |
| Student Choice: random mock | Built in the app, **closed** | the website: doors A and C |
| Whole chapter tests timed by the 80 / 60 / 40 ratio, three hours at most | **Not true yet**: every chapter test has 60 minutes | the website: new minutes on 81 sets (Part 1.8) |
| Dream College meter never counts a chapter test or a Student Choice paper | **Works** in the app | the website: `test_kind` "choice" on made papers (Part 1.9) |
| Matched: public pages, sign-up sheet, the way back after sign-in, Home card, sign-in bar, the JEE question under ours | **Built.** {{MATCHED_PROD}} | the website and the super admin: the admin page, the real paper, two public doors (Part 2.4) |
| Matched card on Home and the bar on the sign-in screen | {{CARD_PROD}} | {{CARD_WAITS}} |
| The first-shift rule of the card, and the All India bar under the Matched card | **In production's server since the Publish of 26 Nov 2026** (live at 14:40 UTC). The bar is a screen: a phone shows it with an app build made after that Publish | new app builds (whether one was made was not checked by the app side) |
| Student Choice's new colours (dark-red top cards, glossy subject tabs) and a made paper's subject minutes that add up to its time | **Published on 26 Nov 2026** (Part 1.2). Screens: with an app build made after that Publish | new app builds |
| Misfire | **Works:** the app shows the website's own Misfire, plus paper-wise tabs | the website: the checks of Part 4.4 |
| Rapid Fire in a browser (`…/api/arena` on the app's server) | {{ARENA_COPY}}. {{ARENA_ICONS}} | {{ARENA_WAITS}} |
| A made-up sample is never shown outside the app's own workspace | **Built on 27 Nov 2026, on the preview** (Part 2.12) | the owner's next Publish |
| One account for the website and the app | **Works:** the app signs up and signs in only through the website's own doors | nothing new; the website keeps those doors (Part 6.3) |
| The website's doors the app uses (Part 7) | **Listed and checked against the app's code** when this book is built | the website: read Part 7.4 before changing one |

{{PROD_NOTE}}

"In production" here means: the app's own server in production answers these addresses (checked on {{TODAY}}, Part 3.7). The owner's last Publish before this book went live on 26 Nov 2026 at 14:40 UTC (the one before it at 05:33 UTC the same day). The server it published holds everything of version 3 of this book. **It does not hold** what was built after it: the browser Rapid Fire copy of 27 Nov 2026 with its icon font, the rest on slow devices, and the rule that keeps samples in the workspace. Those reach production with the next Publish. **Screens reach a student only with a build:** a phone keeps the screens of the build installed on it until a newer build is installed. Whether an app build was made after that Publish was not checked by the app side.

## 0.3 Who does what

| Who | Student Choice | Matched |
| --- | --- | --- |
| **The website agent** (builds jeelive.ai) | Three doors: A the switch, B a chapter's questions without options, C make the paper (Part 1.6). New minutes on the chapter-wise sets (Part 1.8). `test_kind` on results and on the My Tests list (Part 1.9) | The super admin's "Matched" page (2.4a). One real paper per shift (2.4b). Two public read doors (2.4c) |
| **The super admin** (runs jeelive.ai) | Nothing new today. Publishing or hiding a chapter-wise test changes Student Choice within a few minutes (Part 1.11). Later: the switch of door A | After every JEE Main shift: enter the matched questions, check them, make the paper, publish (Part 2.8). Publishing the first shift is what puts Matched on Home; the card also has a switch |
| **The app side** | Built; the app's server is deployed (the screens: Part 0.2). Follows the website by itself: no new app build when a door opens | Built; the app's server is deployed (the first-shift rule: in production since the Publish of 26 Nov 2026; the All India bar: with app builds made after it, Part 0.2). Copies the website's shifts every 2 minutes: no new app build when shifts arrive |
| **The owner** | Decides the open points of Part 3.8 | Decides the open points of Part 3.8 |

| Who | Misfire (Part 4) | Rapid Fire in a browser (Part 5) | One account (Part 6) |
| --- | --- | --- | --- |
| **The website agent** | The six checks of Part 4.4; tells the app side the `kind` of Student Choice and Matched papers | A "Rapid Fire" button / link. Nothing else: never a copy of its code | Keeps the sign-in doors, their fields and every student's `id` as they are (Part 6.3) |
| **The super admin** | Nothing | Nothing | Deletes a website account by hand when the app's owner panel lists a request (Part 6.5) |
| **The app side** | Shows the website's Misfire; builds nothing of its own | Owns it; builds the browser copy again after screen changes | Uses only the website's accounts |
| **The owner** | — | Publishes the app | — |

**Working together (Part 7).** The website agent reads Part 7.4 before changing a door that Part 7.2 lists, and tells the app side first when the change is not a free one. The app side keeps the list true: the build of this book checks it against the app's code.

## 0.4 Twenty-six things nobody must get wrong

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
| a new build | a new version of the app that students must install. Everything in this book is made so that the website's future work needs **no** new build. The app side's own changes (Part 0.2) do need the owner's Publish, and the screens need new builds |
