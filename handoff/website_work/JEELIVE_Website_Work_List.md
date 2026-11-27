# JEELIVE.AI — everything the WEBSITE still has to build, in one place (28 Nov 2026)

(Owner: paste this whole file into the website project's chat, or attach it there.)

## Owner ke liye, chhote mein (Hinglish)

- **Part A** = website ko **app ke liye** kya banana hai: 16 kaam. Inme se zyada tar bante hi app mein **apne aap**
  dikhne lagenge, naye build ke bina.
- **Part B** = website ko **apni website par** test dene wale students ke liye kya banana hai: 6 kaam.
- **Part C** = **aapke faisle**. Jab tak aap nahi batate, website yeh nahi banayegi.
- **Status kaise pata kiya:** 28 Nov 2026 ko app ne **live jeelive.ai** par sirf padh kar (QA learner se, kuch save nahi
  kiya) har cheez dekhi. Website ka packet N1 abhi sirf website ke preview par hai, live par nahi.
- **Student Choice:** app ki taraf se poora bana hua hai (preview mein). "Sawaal khud chuno", "Paper banao" aur
  "Random mock" sirf website ke **3 darwaze (A, B, C)** banne ka intezaar kar rahe hain (Part A, line 1 se 3). Aaj live
  par teeno **404** dete hain, yaani bane hi nahi.

---

## How to read this (for the website agent)

- Written by the app project. The website stays the owner of students, names, questions and papers; the app only asks.
- "Live 28 Nov" = read from the LIVE website (jeelive.ai) on 28 Nov 2026 through the app's server, QA learner, reads
  only (sign-in, then GETs). Nothing was written, no paper was started.
- "N1" = your packet N1 of 28 Nov (preview only, per your own summary).
- Full shapes of every door are in the notes you already have (book version 3, the Student Choice note, the Matched
  note, the note of 27 Nov). The short shape is repeated here so this list can be built from on its own.
- Your 7 questions are answered in the app's `memory/APP_REPLY_V5.md` (branch App, after the owner's "Save to GitHub").

---

## PART A — for the APP (the app already waits for these)

| # | What | Live 28 Nov | When it is live, the app… |
|---|------|-------------|---------------------------|
| 1 | Student Choice **door A** `GET /api/choice/bank?exam=jee-main` | 404 | opens "Sawaal khud chuno" / "Random mock" by itself (~4 min) |
| 2 | Student Choice **door B** `GET /api/choice/chapters/<chapter test id>/questions?page=1` | 404 | lists a chapter's questions without options |
| 3 | Student Choice **door C** `POST /api/choice/papers` | not built | makes the student's paper and opens it |
| 4 | The 81 chapter-wise tests: **time by the ratio, 180 min at most** | every test 60 min | shows the new time by itself |
| 5 | **display_name** in auth answers | key absent: live sends it only for a saved name (N1 = always, preview only) | right name everywhere, by itself |
| 6 | **class_level** on every chapter row, following the APP's list (point A6 below) | absent | small app change to read it |
| 7 | **per_page=100** on the chapter list (and on `/my/tests`) | ignored on the chapter list (N1: preview only) | already sends it; nothing to change |
| 8 | **Matched**: `GET /api/matched`, `GET /api/matched/<shift>`, one paper a shift, super admin page, the matching machine | 404 | Matched fills up by itself |
| 9 | Whole-series **AITS leaderboard** `GET /api/series/all-india-jee/leaderboard[?q=]` | 404 | "Poori series" tab appears by itself |
| 10 | Optional: `GET /api/series/all-india-jee/my-days`, and one handle per student (or `.../compare?with=<handle>`) | 404 | lighter Rank graph; friend compare day by day |
| 11 | **test_kind** on every row of `GET /api/my/tests`, and `"choice"` / `"matched"` on those papers | absent on rows | fewer reads on a new phone; own Misfire tabs later |
| 12 | **Account deletion** call (any shape: the student's own request with the PIN, or a server call) | none | Play Store / App Store need it; the owner deletes by hand today |
| 13 | **PYQ pictures**: `503 vault_unavailable` and empty `200` parts (seen 27 Nov) | fixed on your preview (B1), not live | pictures come back by themselves |
| 14 | **Two test students** (phone + PIN, kept out of leaderboards/exports), given to the owner | not given | the app can finally test writes (names, papers) for real |
| 15 | **Load answers** (rate limit by address? requests a second tested? where/when may a load test run?) | not answered | the app can measure for 1 lakh students at once |
| 16 | **"Meri details" kept with the account**: `GET` / `PUT /api/profile/rank-details` (OWNER 28 Nov: one per account, phone and browser, kept by the website) | not built | the app (built on its preview) syncs by itself, no new build |

### A1–A3. Student Choice doors (short shape)
- **A** `GET /api/choice/bank?exam=jee-main` → `{ "pick": true, "random": true, "max_questions": 75, "max_per_subject": null,
  "minutes_per_question": { "Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2 } }`. 404 = both closed. Do NOT send
  "subjects" (chapters come from your chapter-wise catalogue). Read by the app's server only.
- **B** `GET /api/choice/chapters/<id>/questions?page=1` (id = the chapter-wise test's set id) →
  `{ "chapter": {id, title, subject}, "pages": 2, "items": [ { "id", "number", "type": "mcq"|"integer", "text", "stem": [ {url, w, h} ] } ] }`.
  NEVER options, answer or solution. Picture links: https, open without cookies, valid ≥ 24 h. ~50 a page.
- **C** `POST /api/choice/papers` `{ "exam": "jee-main", "mode": "pick", "question_ids": [...], "request_key": "<uuid>" }`
  or `{ ..., "mode": "random", "count": 30, ... }` → `{ "set_id": "..." }`. Same request_key = same paper. 1 to 75
  questions (never 90). +4 / −1 / 0. Minutes = Maths 3.2 + Physics 2.4 + Chemistry 1.6 a question, sum rounded UP (a made
  paper is NOT cut at 180). Random split equal over the 3 subjects, leftovers to Physics then Chemistry (10 → 4+3+3).
  Order: Physics, Chemistry, Mathematics; single-correct first. `test_kind: "choice"` on the set AND on its result.
  Refusal: 422 with a plain sentence (shown as it is). Owned by the student, listed nowhere else.

### A4. Chapter-test time
`rules.minutes = ceil(count × minutes of its subject)`, **never more than 180**; changes with the count; running
attempts keep their deadline. (7 tests are held at 180; 11 become shorter than 60. Table: Student Choice note part 4.)

### A5. display_name
In `data` of `GET /api/auth/me` (and auth/phone, auth/phone/signup, auth/refresh when they send the user): the name as
kept, or `null`; always present; never the "Learner XXXXXXXX" fallback. Live 28 Nov `auth/me` answer has no such key:
`{"id":"cfcc3ac4-…","name":"Learner","phone":"+91XXXXXX6276","role":"student","exam":"JEE Main","access_type":"unverified_phone","pin_configured":true}`.

### A6. Class 11 / Class 12 — THE OWNER'S DECISION (28 Nov)
The app's division stays exactly as it is ("Itna mehnat se class 11th and 12th wise divide kiye wo rhega"). Put
`"class_level": 11 | 12 | null` on every chapter row **following this list** (not a list of your own):
- Physics 11: 01–15 · Physics 12: 16–30
- Chemistry 11: 01–08, 15, 16, 17 · Chemistry 12: 09–14, 18–23 · Chemistry null: 24 Miscellaneous
- Mathematics 11: 01–17 · Mathematics 12: 18–27

If you think a chapter is in the wrong class, say which: the owner decides and both lists change together. Until
class_level exists: tell the app project BEFORE a chapter-wise test is renamed, added, merged or removed.

### A7. per_page
Keep the default 12 when per_page is not sent, and "pages" right for the size asked. The app now sends per_page=100 for
the Class 11/12 view and for the finished-papers list (`/my/tests?tab=completed`); it still reads every page when you
ignore it.

### A8. Matched (needed before JEE Main's first shift, January 2027)
Super admin page per shift (JEE question + 1–4 of ours with source, tag, answer, solution; "asked"; publish / take back;
Home card auto/on/off) → "Make the paper" (one ordinary paper, +4/−1, minutes by the subject rule, `test_kind:
"matched"`, each of ours carries its `question_id` inside that paper) → two PUBLIC doors read by the app's server:
`GET /api/matched` → `{ "card": "auto", "shifts": [ {id, updated_at} ] }` and `GET /api/matched/<shift>` →
`{ id, asked, updated_at, paper_id, items: [ { n, subject, chapter, jee: <q>, ours: [ <q> + source, tag, question_id ] } ] }`.
Picture links in a shift: public and never expiring. Never delete a published shift (take it back). The machine that
matches a JEE paper with our questions is built nowhere yet.

### A9–A10. Series
Whole-series leaderboard: same envelope and rows as the day leaderboard + `days_counted`, `maximum`, and per row `days`.
Only live attempts of released days, first attempt per day, same tie-break, display name or "Learner XXXXXXXX", never a
phone number. The series runs 9 Dec 2026 to 27 Jan 2027 (live 28 Nov), so this is needed by 9 Dec.

### A16. "Meri details" (shape and rules: the app's reply v5, part 3d)
`GET /api/profile/rank-details` -> `{ "rank_details": <rank.profile.v1 shape> | null, "at": <ms> }`; `PUT` the same
body -> the same answer. null + at = removed. Newer `at` wins; a student's own change always goes up. 404 until built.

### A13. PYQ pictures
An empty part should not be a `200` (a `503` lets a client stop and retry) and should never be cached at the edge.

---

## PART B — on the WEBSITE, for the students who take their tests there

| # | What | Where it stands |
|---|------|-----------------|
| B1 | **Rank page like the app's**: Cut off tool, "Meri details", rank entry | done on your preview (N2), not live |
| B2 | **The differences in the owner's 10 screenshots** (app vs website) | listed in YOUR guide; not known to the app project |
| B3 | **Chapter-wise time by the ratio, 180 at most** (A4): the same sets, so website students get it too | not done (all 60 min) |
| B4 | **PYQ pictures** (A13): the website's own result pages use the same routes | to be checked |
| B5 | **Whole-series AITS leaderboard** (A9) on the website's own series page too, from 9 Dec | not built |
| B6 | **Rapid Fire button** on the website opening the app's Google Play page | N1: done on your preview, not live |

---

## PART C — the owner decides (nothing is built for these until he says)

1. **Colour**: "App wala colour nhi chlega": should the WEBSITE look like the app, or the APP like the website? (You
   asked; nothing changes until he answers.)
2. **Student Choice and Matched on the website itself** (pages for website students): today they are asked only as
   doors for the app. Build website pages too, or app only?
3. **Class 11 / Class 12 tabs on the website's own chapter-wise page** (with class_level, A6)?
4. **A made Student Choice paper above 3 hours** (75 Maths = 240 min): cut at 180 like chapter tests, or keep?
5. **A shortest time for chapter tests** (the ratio gives 4 min for the 2-question Miscellaneous test)?
6. **A Matched paper and the Dream College meter**: count it as a full mock, or never?
7. **Suggestions for made papers** (not rules yet): new questions first in a random mock; a daily limit (e.g. 20);
   removing papers made but never started; no leaderboard.
8. **A Class 11 mock** (door C with `"chapters": [...]`) and one All India mock for everybody: not asked yet.

---

## What to send back to the app project

- Part A: one word a line (done / in work / not started), and for every "done": live or preview, and since when (UTC).
- Your guide's 7 questions, as text.
- Part C: nothing; the owner answers.
