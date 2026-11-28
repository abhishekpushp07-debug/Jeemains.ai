# Misfire Mock on jeelive.ai — what the app sends and reads (Pocket 2, 28 Nov 2026)

Proposed shape, built in the app behind the switch and tested only with the browser playing the website.
Pocket 3 adjusts the app to the website's exact reply. While the switch is not `true`, students see nothing new.

## 1. The switch — door A (`GET /api/choice/bank?exam=jee-main`, read by the app's server every 2 minutes)
- Add `"misfire": true` to open Misfire's **Mock** tab. Anything else (missing, `false`, `"true"`, `1`, 404) = shut.
- Student Choice's `pick` / `random` are unchanged by it.

## 2. Make the paper — door C (`POST /api/choice/papers`, the student's own request, like `pick` / `random`)
```json
{ "exam": "jee-main", "request_key": "<uuid>", "mode": "misfire",
  "counts": { "Physics": 5, "Chemistry": 10, "Mathematics": 0 },
  "chapters": { "Physics": ["01 Units and Measurement"] } }
```
- `counts`: 0 to 25 per subject, at least 1 in all. `chapters` only for a subject where the student ticked some
  chapters (names exactly as `chapters[].name` in `GET /my/misfire?status=open&subject=…`); missing = every chapter.
- Questions: the student's own **open** Misfire items (never "Samajh gaya"); fewer available = as many as there are.
- `request_key`: the same key for every retry of the same ask → the same `set_id`, never a second paper.
- Answer `{ "set_id": "<6-80 letters, digits, - or _>" }` (200/201). 404/405 = "not built yet"; 422/409/429 with
  `error.message` = that sentence is shown; 5xx = "try again". Same table as Student Choice door C.

## 3. The paper
- An ordinary set owned by the student, `test_kind: "misfire"`, exam "JEE Main", `rules` +4 / −1 / 0,
  minutes by the owner's rule (Physics 2.4, Chemistry 1.6, Maths 3.2 a question: 25+25+25 = 180), each question with
  its own subject, pieces, key and solution. Then a normal paper: `/my/sets/<id>`, `/sets/<id>/start`, attempt,
  autosave, deadline, result, Analysis, My Tests, on the app and the website alike.
- The Dream College meter never counts it (like `choice`).

## 4. Lists and results the app reads
- `GET /exam-navigation/jee-main/history?kind=misfire&page=` → `items[]` {id (attempt), title, started_at,
  submitted_at, summary {score, maximum, correct, incorrect, skipped} | null, status, resumable}, `pages`.
- `GET /my/tests` rows: `test_kind: "misfire"` (shown as "JEE Main · Misfire Mock").
- `GET /attempts/<id>/results`: `test_kind: "misfire"` and
  `"misfire": { "understood": 3, "total": 15 }` = how many of its questions went to "Samajh gaya" (the website moves
  every right one). Without `misfire` the result says the general sentence instead.

## 5. The website's two decisions (28 Nov) — both fine for the app, no app change needed
- A Misfire Mock's result is **not counted** in Misfire's chapter report (one question is never counted twice).
- A question already "Samajh gaya" before the mock and wrong in the mock **stays "Samajh gaya"**.
- Please also keep: a question wrong or left in the mock does **not** become a second Misfire item; it stays open
  under its first id `<attempt id>:<question id>`. `misfire.understood` counts only the questions this mock moved.

## App files
`src/misfire/web.ts`, `src/misfire/web/WebMocksTab.tsx`, `src/misfire/web/Understood.tsx`, `app/misfire/index.tsx`
(tab), `app/misfire/mock/new.tsx` (`?web=1`), `backend/choice.py` (`misfire_on`). Check: `tests/misfire_web_check.py`.
