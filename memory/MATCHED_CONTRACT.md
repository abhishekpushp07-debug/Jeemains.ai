# Matched: what the app shows, and what the future machine / super admin must write

Written 25 Nov 2026, when the app side was built ahead of time. **Read this before building the matching machine or the
super-admin page.** The app in students' hands already knows how to show Matched; nothing below needs a new app build.

## What a student sees

- **Home**: from the day after the All India series ends, the All India series card gives its place to the **Matched**
  card ("JEE Mains questions matched with ours": glossy red and yellow, fireworks, running edge). The series and its
  practice archive stay on Home's ALL INDIA tile.
- **Sign-in screen**: from the same day, a small Matched bar. People without an account can open Matched too.
- **Matched page** (`/matched`): month pills (Jan 2027, Apr 2027) → days → shifts ("Shift 1 · 18 of 75 matched").
- **Shift page** (`/matched/<shift id>`): a red card with the golden cup and fireworks: the count ("6 of 75 questions
  matched with ours"), the paper's facts (questions, marks, +4 / −1) and the button **"Attempt all matched"**; subject
  pills; then one card per matched question: the JEE Main question (soft red) and our question(s) it matched (soft gold,
  where ours was asked, how close the match is), **without options**, with tabs "Question | Solution" (the Solution tab
  opens the right answer and the worked solution of both).
- **Matched paper** (`/matched/paper/<shift id>`, the "Attempt all matched" button): OUR matched questions of that shift,
  one at a time, with OUR options to tap (or a number to type), and under each the JEE Main question it matched (without
  options). Submit → result: marks (+4 right, −1 wrong, 0 left), right / wrong / left, time, and every question again with
  the right option green, a wrong choice red, and our solution. Everything is marked ON THE PHONE from the shift's own
  answer (`correct` / `answer`); nothing is sent to any server and no sign-in is needed. The last result of a shift is
  remembered on that phone only ("Attempt again · Pichhli baar: 14 of 28").
  **A question of ours is in the paper only when it can be marked:** it has options AND `correct`, or it has no options
  and its `answer` is a number. A shift where none of ours can be marked has no paper (the card says it opens when the
  answers arrive).
- Before the first shift is written, the card and the page say that matches will appear after every shift.

## The one thing to write: a document per shift in the `matched_shifts` collection

```
{
  "_id": "2027-01-25-s1",        // the exam day in India + "-s" + the shift number (1 to 9). Day and shift are read from here.
  "published": true,              // students see the shift only while this is true. false = prepared, or taken back.
  "asked": 75,                    // how many questions the shift's paper had. Optional: without it "18 matched" is shown.
  "updated_at": 1800000000,       // unix seconds of the last change. Optional.
  "items": [                      // ONLY the questions that matched. The app counts them ("18 of 75").
    {
      "n": 12,                    // the question's number in the JEE paper. Optional (then it goes after the numbered ones).
      "subject": "Physics",       // exactly Physics, Chemistry or Mathematics. Anything else: shown without a subject.
      "chapter": "Kinematics",    // optional
      "jee":  { ...question },    // the JEE Main question
      "ours": [ { ...question, "source": "AITS Day 12 · Q 7", "tag": "Same concept" } ]   // 1 to 4 of ours
    }
  ]
}
```

A `question` (the JEE one and each of ours has the same shape):

| field | what | limit |
| --- | --- | --- |
| `text` | the question's words; maths in `$…$` (TeX), exactly like the website's typed questions | 6000 characters |
| `options` | list of option texts, in order; shown as (A), (B), … | 6 options, 1500 characters each |
| `images` | list of `{ "url": "https://…", "w": 800, "h": 300 }` (or just the URL). **https and readable without sign-in** (the page is public). `w` and `h` (pixels) are optional but stop the page jumping while a picture loads | 6 pictures |
| `correct` | which option is right: its place from 1 (`2`) or its letter (`"B"`). The app turns that option green when the student opens the solution | one option |
| `answer` | the right answer in words, for a question without options (a number answer: `"8"`) | 300 characters |
| `solution` | the worked solution; maths in `$…$` | 6000 characters |
| `solution_images` | pictures of the solution, same shape and rules as `images` | 6 pictures |
| `source` (ours only) | where our question was asked: "AITS Day 12 · Q 7" | 80 characters |
| `tag` (ours only) | how close the match is, shown as a yellow seal: "Same question", "Same concept" | 40 characters |

A question needs `text` or at least one picture. An item needs the JEE question and at least one of ours. Anything that
does not fit is left out by the server and not counted, so it cannot break the app; nothing else in the document is
sent to phones.

**Both the JEE question and ours should come with their solution** (`correct` or `answer`, and `solution` and/or
`solution_images`): every question has a Solution tab on the app, and ours needs `correct` (or a number `answer`) to be
in the Matched paper. A question without any of them says "Is question ka solution abhi nahi aaya"; one with only the
right answer says the written solution is not there yet.

Every option must have words: if one is empty, none of the options is shown (a missing one would move the letters), so
put the right answer in `answer` for such a question.

Up to 150 items per shift and 200 shifts are read.

## Rules to keep

- **Never delete a shift.** To take one back, set `published` to false. To correct one, write the document again.
- A change reaches students within about two minutes (the server keeps each answer for 60 seconds).
- The matching machine and the super-admin page are **server-side work only**: they write the document above. If their
  own data looks different, change it into this shape before writing (or add the change to `shape_shift` in
  `backend/matched.py`). The app must keep getting the answers below.

## What the app asks the server (all public, read-only)

- `GET /api/matched` → `{ total, updated_at, shifts: [{ id, day, shift, asked, matched, subjects: [{ name, n }], updated_at }] }`, newest first.
- `GET /api/matched/<shift id>` → the same shift row plus `items`. 404 when it is not published.
- `GET /api/app/switches` → now also `matched: true | false`: whether Home shows the Matched card.

## When the card is on

`backend/app_switches.py` → `MATCHED_CARD`:
- `"auto"` (now): from the day after the series' last day. The server reads that day from the website's public schedule
  every 15 minutes (`backend/matched.py`, kept in `rf_meta` under `matched:aits_last_day`). Today the website says the
  series runs 9 Dec 2026 to 27 Jan 2027, so the card appears on **28 Jan 2027**.
- `"on"`: now, whatever the dates are. Needed if a new series starts later and Matched must stay on Home.
- `"off"`: never.

**The same three words in Mongo win over the code**: `rf_meta` `{ "_id": "matched:card", "value": "on" | "off" | "auto" }`
(read at most once a minute). The super-admin page can write this row to switch the card with no publish at all; with no
row, or any other value, the code's word is used.

Changing the code's word needs a server publish only. A phone learns the answer when the app is opened, and again when it is brought
back after half an hour; it remembers the last answer.

## What the app cannot show without a new build

Video solutions; a picture that needs sign-in; more than 4 of ours per question; subjects other than Physics, Chemistry,
Mathematics (they show, but without a subject name or filter); a Matched paper that is saved on the server (rank,
history across phones); one paper across several shifts; a time limit for the paper; marking other than +4 / −1.

## Files

- Server: `backend/matched.py`, `backend/app_switches.py`, `backend/tests/test_matched.py`
- Sample shifts for the owner's eyes on the preview only: `python3 backend/tests/matched_sample.py show | hide`
- App: `frontend/src/matched/*` (a question's card in the list: `Pair.tsx`; the paper: `paper.ts`, `PaperQuestion.tsx`; shared: `QuestionBlock.tsx`, `html.ts`, `parts.tsx`; the red cards, cup and fireworks: `MatchedCard.tsx`, `looks.tsx`), `frontend/app/matched/index.tsx`, `frontend/app/matched/[id].tsx`, `frontend/app/matched/paper/[id].tsx`,
  `frontend/src/components/GlossWord.tsx`; Home `app/(tabs)/index.tsx`; sign-in `app/entry.tsx`; public route in `app/_layout.tsx`
- UI test stand-in: `tests/matched_fixture.py`
