# Student Choice — website side, for the app team (2026-11-27)

The website now answers the three doors exactly as the app book (Part 1.6) asks. Both switches are **Off** in preview and
production until the owner turns them on in Super Admin › Student Choice; Off = door A answers 404, so the app stays as today.

## Doors (signed-in cookie session; normal `{data,error,meta}` envelope)
- **A** `GET /api/choice/bank?exam=jee-main` → `{pick, random, max_questions, max_per_subject, minutes_per_question:{Physics,Chemistry,Mathematics}}`.
  404 when both Off or any other exam; never 5xx (any trouble reads as 404); no personal data; no `subjects` field.
- **B** `GET /api/choice/chapters/{chapter-test set id}/questions?page=N` → `{chapter:{id,title,subject}, pages, items:[{id,number,type,text,stem:[{url,w,h}]}]}`.
  50 a page, at most 6 pages. Only live JEE Main chapter-wise tests (the catalogue's own query for every student). Dropped and bonus
  questions are left out. Never options, answer or solution. Ids are stable UUIDs (same id in every paper made from that question).
  Picture rules: a cut question = its question piece(s) only; an old-look numerical = its whole crop; an old-look MCQ = its words up to
  "(A)" (no picture), left out when there is no "(A)". Links: absolute https, ~150 chars, cookie-free, signed, valid 24–48 h,
  `Cache-Control: public`, WebP when the server can make it (PNG otherwise). `w`/`h` in print points (the file has 2 px a point).
  404: pick Off, unknown / not-live chapter, page past the end. 503 only if the database itself fails.
- **C** `POST /api/choice/papers` `{exam, request_key, mode:"pick", question_ids}` or `{..., mode:"random", count}` → `{set_id}` (200).
  Same request_key (same student) = the same paper, never a second slot of the day. Sentences (shown verbatim by the app):
  - 422 `Ek paper me zyada se zyada 75 sawaal ho sakte hain.` (more than max_questions ids)
  - 422 `Chune hue sawaalon me se kuch ab available nahi hain. Dobara chuno.` (unknown, gone or repeated id)
  - 422 `Kam se kam ek sawaal chuno.` (empty pick list) — new sentence, not in the book
  - 422 `<Subject> ke zyada se zyada N sawaal ho sakte hain. Koi hatao, tab naya chuno.` (only when the owner sets a per-subject top)
  - 422 `3 se 75 ke beech ginti likho.` (random count outside 3..max)
  - 422 `Abhi <Subject> ke sirf N sawaal hain. Kam ginti likho.` (random: a subject has fewer questions than its share) — new sentence
  - 429 `Aaj ke 5 paper ban chuke hain. Kal naya paper bana sakte ho.` (5 a student a IST day, pick + random together)
  - 409 `Paper banana abhi band hai.` (that way is Off)
  - 409 on Start `Is paper ke kuch sawaal ab available nahi hain. Naya paper bana lo.` (a source chapter went off before the first Start)
  No Origin header needed (same as start). Body up to 48 KB, so 76 ids reach the 422, not a 413.

## The made paper
- Lives in its own collection (never in the catalogue, Master, Library or any owner count). Only its maker can open it:
  `GET /api/my/sets/{id}`, `POST /api/sets/{id}/preflight`, `POST /api/sets/{id}/start`; anyone else gets the usual 404.
- `test_kind: "choice"` on the paper, the attempt, results and every `GET /api/my/tests` item (that list now carries `test_kind` for all papers).
- Exam `JEE Main`, +4 / −1 / 0, maximum `count*4`, order Physics → Chemistry → Mathematics, MCQ before numerical, then chapter order and
  the question's number. Questions are numbered 1..N in the paper; `section` = subject (the player groups by subject).
- Minutes = ceil(round(Σ count×minutes, 4)), no 180 cap: 3P+2C+2M = 17, 10+10+10 = 72, 25 Maths = 80, 75 Maths = 240, 25+25+25 = 180.
- Random: equal over subjects, remainder Physics then Chemistry (10 = 4+3+3, 11 = 4+4+3, 75 = 25+25+25); ~4 MCQ : 1 numerical a subject; drawn across all chapters.
- Frozen on the first Start (a later chapter edit never changes it; a second Start reuses the same copy). Each question keeps its
  answer key, solution, topic (chapter name), difficulty and pictures, plus `source_set_id`/`source_question_id` (internal).
- Never ranked: no class, no cohort rank (cohort answers `state:"unavailable"`, reason `Is test par Rank nahi banta.`), not comparable,
  never a Dream-meter full mock (website_mocks leaves it out; owner's rule also applied to long chapter tests).
- Misfire takes its wrong/skipped questions like any paper (chapter = the question's chapter). A wrong-question report lands on the
  original chapter test's question. AI solutions shown come from the original chapter test.

## Not done on the website side (needs the app team / owner)
- Misfire Mock (`mode:"misfire"`, door A `misfire:true`) is not in the book yet; nothing was built for it.
- Real phone check: please run the app's own Student Choice flow with a test student once the owner turns a switch on.
