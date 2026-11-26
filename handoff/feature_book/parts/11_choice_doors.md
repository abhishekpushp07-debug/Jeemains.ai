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

{{file:examples/choice_door_A.json}}

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

{{file:examples/choice_door_B.json}}

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

{{SPLIT_TABLE}}

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

[[shots: s10_later_landing | 10. First screen with both ways open ; s11_later_random_mock | 11. Random mock: only the number is asked ; s12_later_questions | 12. Step 2: questions without options ; s13_later_review | 13. "Paper banao": the paper's make-up before it is made]]

**Random mock** (a sheet on the first screen). "Bas ginti batao. Sawaal Physics, Chemistry, Maths se barabar aur mile-jule aayenge, JEE Main ke paper ki tarah." A number box that starts at 30, quick buttons 15, 30, 45, 60, 75, the split subject by subject with each subject's time, the whole paper's questions and time, and one line: "Poore 120 marks · sahi +4, galat -1, chhoda 0 · time 1 hr 12 min". A number outside the range shows "3 se 75 ke beech ginti likho." and the button is off. **"Random mock banao"** sends door C; the new paper's page opens.

**Sawaal chuno** (step 2 of 2, after ticking chapters).

- Pills for the subjects that have a ticked chapter, each with how many questions are chosen in it; under them pills for that subject's ticked chapters.
- The chapter's name and "Maths · 12 sawaal · yahan sirf sawaal hain, options paper mein milenge".
- One card per question: a tick, "Q 1", MCQ or NUMERICAL, and the question's words or its picture. **No options.** A tap ticks it.
- At the end of a chapter: "Agla chapter: …".
- The bar: "7 / 75 sawaal", "17 min · 28 marks", and **"Paper banao"**.
- The 76th tap is refused: "75 sawaal ho gaye: ek paper mein isse zyada nahi. Koi hatao, tab naya chuno." With a top per subject: "Physics ke 25 sawaal ho gaye. Koi hatao, tab naya chuno."
- Unticking a chapter in step 1 takes its chosen questions out too.
- **"Paper banao"** opens the sheet "Aapka paper": the make-up subject by subject, "Poore 28 marks. Sahi jawab +4, galat -1, chhoda hua 0. Paper Physics, Chemistry, Maths ke order mein banega; result, analysis aur solutions har paper ki tarah milenge.", then **"Haan, paper banao"** (sends door C) and "Aur sawaal chuno".
- The chosen questions are kept while the app is open (going back and forth between the steps loses nothing); they are not kept after the app is closed.

**A known small thing in the make-up:** each subject's time is rounded up on its own, so the rows can add up to a minute or two more than the paper's total (picture 13: 8 + 4 + 7 minutes above "17 min"). The total is the right one, and it is what door C must give.
