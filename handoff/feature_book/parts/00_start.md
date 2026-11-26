<div class="box sky" markdown="1">

### Owner ke liye (short)

- Is book mein dono naye features ka poora hisaab hai: **Student Choice** aur **Matched**. App mein kya dikhta hai, website ko kya banana hai, super admin ko kya karna hai, aur kaun si cheez abhi check nahi hui.
- **Student Choice aaj chalta hai**: student chapters tick karta hai (naam likh kar dhoondh bhi sakta hai) aur har chune chapter ka poora test deta hai. Sawaal JEE Main ke chapter-wise sawaal hi hain; alag bank nahi hai.
- **Sawaal khud chunna aur random mock abhi band hain** ("Jald aa raha hai"). Website teen darwaze banayegi (Part 1.6), tab yeh dono app update ke bina khul jayenge.
- **Time ka ratio** (25 Maths = 80 min, 25 Physics = 60 min, 25 Chemistry = 40 min) banaye hue paper par lagega. Poore chapter test abhi 60 min ke hi hain; unka time sirf website badal sakti hai. Aapka faisla (26 Nov): unhe bhi yahi ratio, par **zyada se zyada 3 ghante** (Part 1.8).
- **Dream College meter**: chapter test aur Student Choice paper kabhi nahi ginte, chahe kitne bhi lambe hon.
- **Matched**: app taiyaar hai, par production mein abhi khaali hai. Super admin har shift ke baad matched sawaal daalega aur unka ek asli paper banayega. Aapka faisla (26 Nov): Home ka Matched card **pehla shift publish hote hi, usi din** aa jayega; AITS ke bache dinon mein All India series us card ke theek neeche ek bar ban jaati hai. (Koi shift na ho to bhi {{CARD_DAY}} se card aa jayega.) Yeh naya rule abhi preview par hai; students tak agle Publish ke saath pahunchega.
- Website agent ko yeh PDF (ya saath ki `BOOK.md`) dena hai. Super admin ke kaam ke hisse: Part 1.11, Part 2.8 aur Part 2.9.

</div>

## 0.1 The two features

**Student Choice** (Home's fourth tile, marked NEW). The student goes through the JEE Main chapter-wise questions his own way.

- **Today:** tick chapters in Physics, Chemistry and Maths (a search box finds any chapter by name), then take each ticked chapter's whole test, one after another.
- **Later, when the website can make such papers:** see the ticked chapters' questions **without options**, tick the ones wanted and get **one paper** made of them (75 questions at most); or ask for a **random mock** of N questions.

**Matched.** After every JEE Main shift, the questions of that shift that matched JE Live's own questions are shown side by side: the JEE Main question, and under it the question of ours it matched. Open to everyone, signed in or not. A signed-in student attempts all of ours in one **real paper** ("Attempt all matched"); a person without an account is asked to sign up first. On Home, the All India series card gives its place to the Matched card as soon as the first shift is published; for its remaining days the series is a bar right under that card.

## 0.2 Where things stand on {{TODAY}}

| What | State | Waits for |
| --- | --- | --- |
| Student Choice: Home tile, first screen, chapter list, chapter search, the ticked chapters' whole tests | **Works.** The app's server in production has it since 26 Nov 2026 (the screens: see the note under this table) | nothing |
| Student Choice: a chapter's questions without options, one paper of ticked questions | Built in the app, **closed** (shown under "Jald aa raha hai") | the website: doors A, B and C (Part 1.6) |
| Student Choice: random mock | Built in the app, **closed** | the website: doors A and C |
| Whole chapter tests timed by the 80 / 60 / 40 ratio, three hours at most | **Not true yet**: every chapter test has 60 minutes | the website: new minutes on 81 sets (Part 1.8) |
| Dream College meter never counts a chapter test or a Student Choice paper | **Works** in the app | the website: `test_kind` "choice" on made papers (Part 1.9) |
| Matched: public pages, sign-up sheet, the way back after sign-in, Home card, sign-in bar, the JEE question under ours | **Built.** In production the list is **empty** and the card is **off** | the website and the super admin: the admin page, the real paper, two public doors (Part 2.4) |
| Matched card on Home and the bar on the sign-in screen | **Off in production:** no shift is published. They come on by themselves **when the first shift is published**, and on **{{CARD_DAY}}** (India time) at the latest | the first published shift (Part 2.6) |
| The first-shift rule of the card, and the All India bar under the Matched card | **Built on 26 Nov 2026, on the preview.** Not in production yet: there the card still waits for {{CARD_DAY}} or for the switch `on` | the owner's next Publish of the app |

"In production" here means: the app's own server in production answers these addresses (checked on {{TODAY}}, Part 3.7). **The screens reach students with the app version that is published.** The chapter search, the three-hour sentence, the first-shift rule of the Matched card and the All India bar were built on 26 Nov 2026 and are on the preview; whether a Publish has been made after each of them cannot be seen from outside and is not known to the app side: ask the owner. A phone that still has an older installed build gets new screens when it updates.

## 0.3 Who does what

| Who | Student Choice | Matched |
| --- | --- | --- |
| **The website agent** (builds jeelive.ai) | Three doors: A the switch, B a chapter's questions without options, C make the paper (Part 1.6). New minutes on the chapter-wise sets (Part 1.8). `test_kind` on results and on the My Tests list (Part 1.9) | The super admin's "Matched" page (2.4a). One real paper per shift (2.4b). Two public read doors (2.4c) |
| **The super admin** (runs jeelive.ai) | Nothing new today. Publishing or hiding a chapter-wise test changes Student Choice within a few minutes (Part 1.11). Later: the switch of door A | After every JEE Main shift: enter the matched questions, check them, make the paper, publish (Part 2.8). Publishing the first shift is what puts Matched on Home; the card also has a switch |
| **The app side** | Built; the app's server is deployed (the screens: Part 0.2). Follows the website by itself: no new app build when a door opens | Built; the app's server is deployed (the first-shift rule and the All India bar: with the next Publish, Part 0.2). Copies the website's shifts every 2 minutes: no new app build when shifts arrive |
| **The owner** | Decides the open points of Part 3.8 | Decides the open points of Part 3.8 |

## 0.4 Twenty things nobody must get wrong

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
18. **Samples stay on the preview.** Made-up shifts and made-up chapters are for the owner's eyes there only. Never write them into production.
19. **The fields of the chapter-wise catalogue listed in Part 1.5 are in use.** Do not rename or drop one without telling the app side.
20. **The first real run is on a test setup.** The first door answered and the first shift published are the first true end-to-end runs: tell the app side before students see them.

## 0.5 How to read this book

- **Website agent:** Part 1.5 to 1.9 and 1.13 (Student Choice), Part 2.3 to 2.7 and 2.11 (Matched), then Part 3 as a reference. The JSON in the grey boxes is also in the `examples` folder of the download; every example in it was run through the app server's own code when this book was built.
- **Super admin:** Part 0, Part 1.2 (what students see), Part 1.11, Part 2.2, and above all **Part 2.8 (what to do after every shift)** and **Part 2.9 (mistakes and what the student would see)**.
- **Pictures** are from the app's web preview, at a phone's size, taken on {{TODAY}}. The Matched pictures show three **made-up sample shifts** that exist on the preview only. The pictures of question picking and the random mock (Part 1.7) show **made-up questions marked "(Sample)"**, with the browser answering in place of the website's doors that do not exist yet.

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
| a new build | a new version of the app that students must install. Everything in this book is made so that the website's future work needs **no** new build |
