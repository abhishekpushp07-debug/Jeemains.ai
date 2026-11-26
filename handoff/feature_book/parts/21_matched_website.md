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

{{file:examples/matched_list.json}}

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
- Until the doors exist they answer 404 and nothing changes in the app. That is the state on {{TODAY}}.

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

Only shifts that came from the website are ever hidden by the copy. A shift written into the app's database by hand (as the preview's samples are) is shown and left alone, unless the website publishes a shift with the same id: then the website's shift takes its place.

## 2.6 Home's card and the sign-in bar: when they are on

One switch decides both: Home's Matched card (in the All India series card's place) and the Matched bar on the sign-in screen. **They are also the only ways into Matched:** with the switch at `off`, no student can reach the Matched pages from the app, even when shifts are published.

| The switch says | Meaning |
| --- | --- |
| `auto` | on **as soon as one shift is published** (the owner, 26 Nov 2026: on the day of JEE Main's first shift itself). "Published" means the shift is in the app server's list (`GET /api/matched` of the app's server), so about 5 minutes after the super admin publishes it. **And in any case from the day after the All India series' last day**, India time, also with no shift: the app's server reads that day from the website's own schedule (`last_date` of `GET /api/series/all-india-jee`) every 15 minutes and remembers it. On {{TODAY}} the website says the series runs **{{SERIES_FIRST}} to {{SERIES_LAST}}**, so with no shift at all the card comes on at 00:00 on **{{CARD_DAY}}**. If the only published shift is taken back while the series still runs, the All India card comes back |
| `on` | on now, whatever is published and whatever the dates are |
| `off` | never, also when shifts are published |

**The All India series while Matched has its place.** For the series' remaining days it is a bar right under the Matched card (Part 2.2, picture 10). There is no switch for the bar: the app shows it while the series' own `today` is not past its `last_date` (both from `GET /api/series/all-india-jee`), and drops it the day after. If the website moves the series' last day, the bar and the card's latest day move with it.

**Where this rule is.** The first-shift rule and the bar were built on 26 Nov 2026 and are on the app's preview. **Production gets them with the owner's next Publish of the app.** Until then production's `auto` still means only "from {{CARD_DAY}}", and the switch `on` would be needed to show Matched earlier. Before the exam session, ask the app side to confirm that production has the rule.

**Who holds the switch,** strongest first:

1. **The super admin, through the website:** `card` in the list door (Part 2.4c). When the website sends it, the app's server takes it over on every pass (every 2 minutes).
2. **The last word written in the app's database** (the row `matched:card`). It stays in force when the website sends no `card`. The app side can write it by hand; a `card` from the website overwrites it within 2 minutes.
3. **The word in the app server's code:** `auto`. Used when nothing else is set. That is production's state on {{TODAY}}.

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
