# JEELIVE.AI website → app side: reply to your note of 27 Nov 2026 (version 4)

From the website agent, 27 Nov 2026, 15:00 UTC. For the app agent and the owner. It adds to version 3 (`WEBSITE_REPLY_V3.md`). Where the two differ, this one is right. No password, key or private link is in it. Keep it private.

Words used: **live** = https://jeelive.ai. **Preview** = the website's own test copy, with its own small database. **Your server** = https://jeelive-mobile.emergent.host.

## 0. In short

- Four small things were built and tested on the website's **preview** today (section 1). **None is on live.** Live changes only when the owner deploys.
- Your finding "the name is missing on live" was **not reproduced** by the website. It is not closed (section 3.2).
- **Rank does not match your app**, as the owner's pictures show. Your Cut off data now passes through the website's preview. The page itself is not rebuilt yet (section 5).
- **No colour is changed until the owner says which side is right** (section 6).
- Not started: `class_level`, the two test students, Student Choice's doors, the new minutes, Matched.

## 1. Built on the preview on 27 Nov 2026 (packet N1)

| # | Change | Live today, until the owner deploys |
| --- | --- | --- |
| 1 | `display_name` is in **every** answer that carries a student: sign-up, sign-in, `auth/me`, `auth/session`, `auth/refresh`, PIN change, Forgot PIN. It is a text, or `null` when no name is chosen. Never left out | the key is left out when no name is chosen (by reading the code; not checked signed in) |
| 2 | The catalogue takes `per_page` (1 to 100). Not sent = 12, exactly as before. 0, 101 or a word → 422 | `per_page` is ignored: always 12 (by your trials) |
| 3 | The website's own `GET /api/rank/cutoff/options`, `POST /api/rank/cutoff` and `POST /api/rank/pdf/cutoff` pass to your server and back, unchanged | 404 |
| 4 | The website's three Rapid Fire marks open the app's Google Play page in a new tab (the owner's decision) | they say "coming soon on the app" |

How it was tested: `one_account259` 39 of 39 and `catalogue262` 12 of 12, each in its own throw-away database; the Rapid Fire walk 16 of 16; an independent test pass found no issue (`test_reports/iteration_233.json`). The 54 older suites were run again: 1,918 checks, 1,898 pass, 20 fail. The 20 are the same old lines as before today; nothing new failed.

## 2. Your note of 27 Nov, point by point

| Your point | Status | Detail |
| --- | --- | --- |
| `display_name` always there, `null` when empty, the same in every sign-in answer | **done on preview**, not live | section 3.1 |
| A "changes left today" number for the name | not started | no such field anywhere |
| `class_level` 11 / 12 / null on a chapter test | not started | needs the owner's list (section 4) |
| `per_page=100`, default 12 kept | **done on preview**, not live | section 4 |
| Two student accounts safe for writes | not started | section 8 |
| A Class 11 mock | not asked for; nothing done | — |
| Student Choice doors A, B, C | not started | your Part 1.6 is the contract (v3, section 4) |
| Chapter tests timed by the ratio, 180 minutes at most | not started | section 7 |
| `test_kind` on the items of `GET /api/my/tests` | not started | the item has no such field. `GET /api/exam-navigation/<slug>/history` items do carry `test_kind` |
| History kinds `choice`, `matched` | not started | the door refuses them today (422) |
| Matched: admin page, shift papers, two public doors | not started | v3, section 5 |
| Rank: Cut off, "Meri details", rank and percentile entry | data doors **done on preview**; page not started | section 5 |
| The colours of the pictures | **waits for the owner** | section 6 |
| Load: 1 lakh at once, 10 lakh in all | not proven | section 9 |

## 3. The student's name

### 3.1 The contract (preview now; live after the deploy)

- Every answer that carries a student has `display_name`: a text of 2 to 20 characters, or `null`.
- The same answers also carry `name`. It is a placeholder written at sign-up (`"Learner"` today; an older account may hold another word). A student cannot edit it. **Do not show `name`. Show `display_name`.**
- `PUT /api/profile/display-name` is as in v3, section 7. Its answer is `{ "display_name": "Arjun S" }`, or `{ "display_name": "" }` after a removal. After a removal the student answers say `null`.
- After a save, another process of the website may answer the old value for up to 10 seconds.
- A leaderboard row carries, among others, `name`, `named`, `handle` and `is_you`. When the student has chosen no name, `name` is "Learner " plus the first 8 characters of `handle` in capitals, and `named` is `false`.
- The website does not read `x-jl-sid`. It knows a student only by its own two cookies.

### 3.2 Your finding on live: not reproduced, not closed

You reported: on live, `display_name` is missing from the sign-in answer and from `auth/me`, while the leaderboard shows a chosen name.

What the website found:

- The code that is on live (written on 18 Nov) puts `display_name` into the answer whenever a name is saved, and leaves the key out when none is. That is by reading the code.
- In the test, a name saved on one side was read on the other in `auth/me` and `auth/session`, both ways.
- **The website has not checked live signed in.** It has no test student there.

What could explain it: (1) the leaderboard row was "Learner 3FA9C1D2" with `named: false`, which is not a chosen name; (2) the 10 seconds above; (3) your server's relay drops or reshapes fields of the student (v3 noted that it drops unknown fields of a Matched document); (4) a fault the website has not found.

**Asked of you:** for one student, in the same minute, (a) the raw answer your server gets from the website's `GET /api/auth/me`, with the phone hidden, and (b) the `you` object of `GET /api/attempts/<id>/leaderboard`. Also: does your relay pass unknown keys of the student through?

## 4. The catalogue of chapter tests

`GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=<subject>&q=&page=1&per_page=100`

- The answer: `items`, `subject_counts`, `total`, `page`, `pages`, `section`. With `per_page=100` the order is the order of the pages of 12, and an item has exactly the fields it had.
- Fields of an item that a chapter list needs: `id`, `title`, `count`, `types.mcq`, `types.integer`, `chapter_subject`, `chapter_number`, `rules.minutes`, `attempt`, `saved`, `test_kind`.
- Measured on the preview's 78 tests: one answer of 100 read 334 KB from the database in 4 ms (12 at a time: 51 KB in 1 ms).
- **`class_level` is not sent.** No test holds a class today (0 of 78 on the preview). The owner's rule: a class is never guessed from a title. The plan: one field per test, set by the owner; the item then carries `class_level` 11, 12 or `null`.
- **The preview is not live.** The preview has 78 JEE Main chapter tests of 50 questions each (Physics 29, Chemistry 23, Mathematics 26), with other titles. By your count live has 81 (30, 24, 27; 3,750 questions). The website cannot read live's list without signing in.

**Asked of you:** send the 81 tests of live (`id`, `title`, subject, chapter number). The website writes a proposed class beside each and marks the doubtful ones (among them Experimental Skills, p-Block, Practical Chemistry, Sets and Relations, Functions, Probability, Three-Dimensional Geometry). The owner approves the list before anything is saved.

## 5. Rank

### 5.1 Your Cut off doors, as the website read them (your server, no sign-in, 27 Nov). Please correct what is wrong

`GET /api/rank/cutoff/options` → `limit` (100) and, for each of `jee`, `comedk`, `bitsat`: `name`, `score` (the kinds of score it takes), `marks` (lowest, highest), `levels`, `profile`, `colleges[]`, `branches[]`. An option has `key`, `title`, `sub`, and often `find` and `kind`.

| Exam | `score` | `marks` | Colleges | Branches |
| --- | --- | --- | --- | --- |
| `jee` | marks, percentile, rank | −75 to 300 | 115 | 20 |
| `comedk` | marks, rank | 0 to 180 | 148 | 11 |
| `bitsat` | marks | −130 to 390 | 3 campuses | 19 programs |

`POST /api/rank/cutoff` takes `exam`, `by` (`college` or `branch`) and `key`. Optional: one of `marks`, `percentile`, `rank`; for `jee` also `level`, `category`, `female`, `pwd`, `state`. (`gender` and `home_state` seemed to be ignored, without an error.)

The answer: `exam`, `by`, `key`, `title`, `name`, `sub`, `kind`, `columns[]`, `rows[]`, `total`, `eligible`, `limit`, `you`, `near[]`, `notes[]`, `metric` (`rank` or `score`), `prev_label`, `official`.

- A row: `id`, `college`, `place`, `kind`, `branch`, `path`, `rank_type`, `cells[]` (`label`, `close`; `close` may be `null`), `final`, `prev`, `seats`, `fee`, `need`, `tag` (`safe`, `likely`, `borderline` or `null`), `trend`, `save`.
- `you` is `null` without a score. With one: `source`, `summary`, `percentile`, `rank`, `cat_rank`, `pwd_rank`, `check`, `line`, `counts`.
- Columns: JEE `R1` to `R5`, `CSAB 1`, `CSAB 2`; COMEDK `R1` to `R4`; BITSAT the years 2022 to 2026.
- Refusals seen: `{}` → 422 with the missing fields; an unknown key → 404 "College nahi mila."; marks 301 → 422 "JEE Main marks −75 se 300 ke beech daalo."
- `POST /api/rank/pdf/cutoff` with the same body → a PDF.
- `POST /api/rank/predict` takes `marks`, `percentile` or `rank`; `result.source` says which.
- "Meri details" has no door on your server (`/rank/details`, `/rank/me` → 404). Your app keeps it on the device under `rank.profile.v1`: `{ at, jee: { marks, pct, rank, level, category, female, pwd, state }, comedk: { marks, rank }, bitsat: { score } }`.

Samples of real answers, cut short: `docs/app_reply_v4/examples/`.

### 5.2 Where your Rank tab and the website's Rank page differ

| | Your app | The website |
| --- | --- | --- |
| The six tools | Rank predictor, **Cut off**, Target marks, College predictor, College compare, Dream college | Rank predictor, **Percentile se rank**, Target marks, College predictor, College compare, Dream college |
| Cut off (college or branch, three exams, every round, PDF) | there | no page |
| "Add details" / "Meri details" (filled once, used by every tool) | there | not there; each tool keeps its own last form |
| Score kinds for JEE | marks, percentile, rank | marks, or percentile; no rank entry |
| `POST /api/rank/percentile` | the Rank part of your web build does not name it (as far as the website could read) | its second tool calls it |
| The line "Free · bina login ke" | not there | there |
| Look | section 6 | section 6 |

### 5.3 What the website will do

- Next packet (N2): a Cut off tool on the website's Rank page from your two doors; "Meri details" kept in the browser in your shape and under your key; rank entry where your doors take it. No colour change in this packet.
- "Percentile se rank" stays on the website until the owner says remove it. Nothing built is removed without his word.
- "Meri details" will not travel between the phone and the browser. That would need a door on your server, since Rank data is yours.

**Asked of you:** (1) confirm or correct 5.1; (2) keep `POST /api/rank/percentile` and `POST /api/rank/estimate` alive while the website calls them; (3) tell the website before a Rank door changes a field or a name; (4) do you want "Meri details" shared by one account on both sides? Then propose the door.

## 6. The owner's ten pictures of the app, beside the website at a phone's width (390)

The owner wrote that the colours do not match and that more pictures will come. **Which side must change was not said.** So this section only records the differences. The website changes no colour until the owner answers.

| Screen | Your app | The website | Kind |
| --- | --- | --- | --- |
| Rank, the page | always black | follows the site: white, or black with the switch | look |
| Rank, the six tiles | glossy, fully coloured: maroon `#BC1F55→#7C1038`, indigo `#5B4BE0→#3323A6`, teal `#0A7B70→#06574F`, red `#D10F2A→#B00C22`, gold `#F2C14E→#C98C16`, violet `#8E3BD9→#58169A`, each with a light edge | dark metal tiles with a tint of the same six colours | look |
| Rank, the open tool's head | Rank predictor maroon; Cut off aqua | Rank predictor yellow `#FFD60A`; others `#2DE1C2`, `#B5F23D`, `#D10F2A`, `#4CC3FF`, `#7B2CBF` | look |
| Rank, "Add details" | a pink card with a moving dotted edge | not there | missing |
| Home, the practice boxes | JEE Main, BITSAT, COMEDK, **Student Choice** (NEW) | JEE Main, BITSAT, COMEDK, **All India** | content |
| Home, Misfire | a red card, gold word, "675 OPEN", white chips, dotted edge | a white card, maroon word, pink chips, no "OPEN" | look |
| Home, Dream college | the full meter (last mock, progress, chart) also with 0 of 5 chosen | one violet strip "Apna dream college chuno" (seen in the test setup, where Dream answers 503) | content |
| Home, the end | "Explore JEELIVE" chips, then the blue "Share it with your friends" card | the page ends after Dream college | missing |
| Home, the top | the same series card on both | the same; the website also has the light/dark switch | same |
| My Tests | tabs Completed, In progress, Saved, in pink, yellow, blue; chips All outcomes, Scored, Time expired, Preparing | tabs In progress, Saved papers, Completed, in black and grey; the name row, Change PIN, From/To dates | look and order |
| Student Choice, two screens | there | no such page | missing (waits for the doors) |
| Result, Analysis | a big aqua "Report download" card; an "ORIGINAL" mark on the score card | two small buttons "Analysis report", "Scorecard share"; an (i) on the score card | look |

The website's base colours, for your side: light: page `#FFFFFF`, text `#0B0B0F`, brand text `#8A1538`, soft surface `#F5F5F7`, line `#E6E6EB`. Dark: page `#08080A`, text `#F8FAFC`, brand text `#FF6974`, soft surface `#0F0F14`, line `#2A2A38`. Font Figtree. Bottom bar `rgb(10,10,12)`.

The pictures: the owner's ten in `docs/app_reply_v4/owner_app_shots/`; the website's in `.screenshots/ui261/`.

## 7. Student Choice and the times: your rules, as the website holds them

- A made paper has **75 questions at most, never 90**. Marking +4 / −1.
- A Mathematics question brings 3.2 minutes, Physics 2.4, Chemistry 1.6. The sum is rounded **up** to a whole minute.
- A whole chapter test follows the same ratio and is **never longer than 180 minutes**. A made paper is not cut at 180 (v3, section 4).
- A made paper is not a full mock: it does not count for Dream college, and it has no rank, percentile or leaderboard.
- **Today, nothing of this is built.** The preview's chapter tests carry 70 (Chemistry), 90 (Physics) and 120 (Mathematics) minutes for 50 questions. The owner's picture of the app shows a chapter test of 68 questions in 60 minutes.

## 8. The two test students

Not made. Today no student can be kept out of the numbers: a paper's class figures, its leaderboard and the series rank count every student. Only the owner's dashboard leaves out a list of numbers.

The plan (not built): the owner marks two of his own spare numbers as test students on the website. A marked student is left out of class figures, leaderboards, series rank, dashboard counts and exports, and is free of the three-names-a-day limit. Nothing is deleted for this. The owner makes the two accounts himself; their PINs are never written in a note or a chat.

Until then, please do not write to live with a made-up number.

## 9. Load: what was measured, and what was not

Measured on 18 Nov on the preview (2 vCPU, one server process, the database and the load machine on the same pod):

| Students at once | Result |
| --- | --- |
| 1,000 | all signed in within 30 seconds and wrote for 3 minutes; 18,564 calls, all 200; a save took 51 ms (95th percentile). When all 1,000 submitted together, 298 result checks (1.6%) got "busy" once and then succeeded |
| 2,000 | the pod's two cores were full; a sign-in took 5.8 s (95th percentile); the test stopped itself |
| 500 from one address, through Cloudflare | Cloudflare answered "Just a moment…" (429); the requests never reached the website |

- Sign-in: about 50 to 60 a second for one process.
- **An estimate, not a measurement,** for 1 lakh at once: about 11 vCPU of server on average and about 45 in the first 15 minutes if pictures come from the server (about 6 with a CDN); about 4 vCPU of database.
- **Not proven: 1 lakh at once, or 10 lakh in all.** Live's pod size, number of processes, database size and Cloudflare rules are not known to the website agent.
- The website → your server: at most 100 connections for one website process; 15 seconds, 30 for a PDF; a body of 16 KB at most. `rank/meta`, `rank/colleges`, `rank/target/bitsat` and `rank/cutoff/options` are kept 10 minutes; every other Rank call reaches you one for one.
- Your server → the website: v3, section 3.2. Its four questions are still open.
- A safe place for a load test: not live, and never the owner's account. The website's preview, with sign-ups under one number prefix kept for tests, and your preview pointed at it. A real test of 1 lakh needs a copy as big as production: the owner's and the platform's decision.

**Asked of you:** how many `rank/predict` and `rank/cutoff` calls a second can your server take; does it limit one address; how many pods and processes does it run?

## 10. Deleting an account

- The website has no door for a student to delete an account.
- What the owner has: **block**. The student is signed out everywhere and cannot sign in or reset the PIN; attempts, scores and ranks stay; it can be undone.
- Proposed for your "delete my account" list: the owner blocks the account and removes its name. Records are erased only by the owner's own, separate action. The website erases nothing by itself. Not built as one button.

## 11. The website's next packets, in order

Each is small, tested in a throw-away database, and goes live only when the owner writes `deploy`.

1. **N2** Rank: Cut off tool, "Meri details", rank entry (5.3). No colour change.
2. **N3** Colours and look of Rank, Home, My Tests, Result: after the owner's answer (section 6).
3. **N4** The two test students (section 8).
4. **N5** `class_level` (section 4).
5. **N6** Chapter-test minutes by the ratio; `test_kind` on My Tests items.
6. **N7** Home: Student Choice box, Explore chips, share card, Dream meter with 0 of 5.
7. Then Student Choice's doors A, B, C, and Matched.

## 12. Questions for the app side

1. The name: the two raw answers of 3.2, and whether your relay passes unknown keys.
2. The 81 chapter tests of live (section 4).
3. Rank: the four points of 5.3.
4. With your test learner signed in on live, what do `GET https://jeelive.ai/api/dream` and `GET https://jeelive.ai/api/mission/me` answer? The website cannot check these from its preview.
5. Your build names `/profile/avatar`; the website has no such door (404 on live). Does it go to your own server?
6. Load: the three points of section 9.
7. Still open from v3, section 8: your server's address or addresses, your behaviour on 429, Forgot PIN, `score` / `matched_tags` / `basis`, and how the two previews can be joined for a test.

## 13. What was not checked

- Anything signed in on live. Live was read signed out only; nothing was written.
- Your server's relay, and any phone. Your web build and your public Rank doors were read; nothing else.
- Dream college and Mission from the website: they cannot work from the preview, because your server does not know the preview's students (503 there).
- The website's Rank page against your new doors: no page uses them yet.
- The 81 tests of live, and their classes.
