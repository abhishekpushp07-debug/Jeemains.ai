## 2.8 The super admin's runbook

The exact buttons are the website's own (Part 2.4a). This is what has to be true, in order.

**Once, before the exam session**

1. The website's Matched page, the paper maker and the two doors have been run on a test setup together with the app side (Part 2.11). The first shift ever published is the first true end-to-end run.
2. Home's card (Part 2.6): **leave the switch at `auto`.** The owner decided on 26 Nov 2026 that Matched takes the All India card's place on the day of JEE Main's first shift: with `auto`, publishing the first shift does it, and the All India series stays as a bar under the card until its last day. Nothing is switched by hand. **Before the session, ask the app side to confirm that production has this rule** (it arrives with the owner's next Publish of the app; without it `auto` waits for {{CARD_DAY}} and `on` would be needed).
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
- **The All India bar on a real day of the series:** the series begins on {{SERIES_FIRST}}. On the preview the bar was seen before the series ("50 DAYS", "Starts 9 Dec", a tap opens the series hub) and, with the browser answering the schedule as a day of the series, as "DAY 46 / 50", "Live today · Start today's test" (at a phone's usual width and at a narrow one). Its tap into a paper was not pressed.
- **The card turning on with the first shift, against production:** the rule is covered by automated tests of the app's server; on the preview the card is switched `on` by hand, so `auto` was not watched there.

**The samples on the preview** ({{TODAY}})

- Three made-up shifts are published on the **preview's** database, for the owner's eyes: `2027-01-22-s1` (6 matched questions), `2027-01-22-s2` (3), `2027-01-24-s1` (2). So that the button and the JEE question under ours can be seen, the first one names a real paper of the website as a stand-in (the chapter test "01 Sets and Relations").
- Home's card is switched `on` by hand on the preview. (With the samples published it would be on under `auto` too, by the first-shift rule.)
- They are taken back with `python3 backend/tests/matched_sample.py hide` (and shown with `show`). Nothing is deleted.
- **Production has none of this:** its list is empty and its card follows `auto` (checked, Part 3.7). The day the website publishes a real shift with the id of a sample, the website's shift takes the sample's place.
