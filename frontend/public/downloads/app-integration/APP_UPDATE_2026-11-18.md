# JEELIVE app update packet — everything the app must build after the 26 Oct 2026 package

Date: 18 Nov 2026. API: **https://jeelive.ai/api** (one server, one database, one student list for website and app).
Status: everything in this file is **live on jeelive.ai** (checked 18 Nov after the owner's deploy: `GET /api/media/probe.bin` answers 200).
Read this file first, then `APP_INTEGRATION.md` (full contract, sections 1–16) for details that did not change.

Files in this packet:

| File | What it is |
|---|---|
| `APP_UPDATE_2026-11-18.md` | This guide: every change since the 26 Oct package, the exact API, every screen, every message, and the acceptance checks |
| `APP_INTEGRATION.md` | The full website ↔ app contract (login, cookies, start, save, submit, results, catalog, series, pictures) |
| `analysis_rulebook.json` | Analysis rules, tag names and Hinglish labels exactly as the server uses them (`rules_version` 2) |
| `samples/*.json` | Real responses from a test copy of the server (synthetic students, no real data): request, status, headers, body |

Rules that did not change: Rapid Fire stays out; never create a second account; keep server IDs; cookies only (no bearer token); `{data, error, meta}` envelope; honour `Retry-After`; never log PINs, cookies or phone numbers.

---

## 1. What is new or changed: checklist with priority

P0 = the app shows wrong or broken things without it. P1 = a main feature students see on the website. P2 = nice to have.

| # | Priority | Change | Kind | Section |
|---|---|---|---|---|
| 1 | P0 | Picture questions: show only the pictures, never `text` / `accessible_text` / "Original option A" strings | Change existing screen | 2.1 |
| 2 | P0 | Start test: 60 s get-ready screen, `/begin`, whole-paper picture loading (`/assets/links` then `/assets/pack`) | Change existing flow | 2.2 |
| 3 | P0 | Time capture in the test player (`timeline` on answer saves and submit, `POST /timeline`). Without it Time, Attempt Quality and Journey stay locked for app attempts | New | 3 |
| 4 | P0 | Sign-in messages: wrong PIN tries left, 15-minute wait, Forgot PIN, live-paper guard | Change existing screen | 2.3 |
| 5 | P0 | Busy server answers: `503 capacity_busy` and `429` with `Retry-After` | Change network layer | 2.4 |
| 6 | P1 | Analysis 2.0: 8 sections, Personal / Comparative, leaderboard, 3 learnings, PDF report, share scorecard | New | 4–7 |
| 7 | P1 | Solutions screen: one insight line per question (your time, par, class %, most-chosen wrong option, answer changed) | Change existing screen | 7.4 |
| 8 | P1 | Exam structure from the API: exam cards, sections, section lists, series inside its exam (`series_path`) | Change existing screens | 8.1 |
| 9 | P1 | Live exam 15-minute start window and score on submission | Change existing screen | 8.2 |
| 10 | P1 | Test series for every exam (`/series`), All India rank card (`/series-rank`) | New | 8.3 |
| 11 | P1 | Written questions (`render_mode: "written"`) and typed options under picture questions | Change existing screen | 8.4 |
| 12 | P1 | BITSAT bonus section (`POST /attempts/{id}/bonus`) | New if not built | 8.5 |
| 13 | P2 | Display name for leaderboards (`PUT /profile/display-name`) | New | 8.6 |

---

## 2. P0 changes to existing flows

### 2.1 Picture questions: only the picture (fixed on the server 18 Nov)
Applies to every question with `render_mode: "source"` and `asset_count > 0`: BITSAT chapter-wise, BITSAT mocks, JEE Main chapter-wise and JEE Main PYQ papers.
- The server now sends `text: ""` for these questions in the test (`/sets/{id}/start`, `/attempts/{id}`, `/begin`) and in results (`/attempts/{id}/results`). Before, the app showed an English sentence ("Original PDF question and four options…") in the test and machine-read text ("01. For z = x − y…") in results under the picture. Do not show either.
- Show the pictures in index order (`asset_count` pictures from the picture pack, or `/attempts/{id}/questions/{qid}/asset/question/{i}`). White background, no colour filter, pinch-zoom.
- `accessible_text` is only the screen-reader label of the picture (React Native `accessibilityLabel`). Never print it on screen.
- Option buttons for picture MCQs: show the letter only (A, B, C, D) or `source_option_labels[key]` when present. The `options` strings ("Original option A", "Option 1, as printed in the source") are placeholders: never show them as words.
- If `typed_options[key]` exists (the owner typed an option the picture cuts off), show it under the picture as "A. <typed text>" with maths rendering, exactly like the website.
- Results/solutions: the student's answer and the correct answer are shown through `source_option_labels` too (`q.source_option_labels?.[q.response] || q.response || "Unanswered"`).
- Questions with `render_mode: "written"` are different: show `text` (maths between `$`) and option texts, then pictures (section 8.4).

### 2.2 Start test, get-ready and whole-paper pictures
1. `POST /sets/{id}/start` with `{ "start_key": "<new UUID>", "preview": false, "get_ready": true }`. Preflight is no longer needed.
2. The attempt has `ready_until` (start + up to 60 s) and `deadline` (already includes the get-ready time). Show the get-ready screen until `ready_until`: a countdown ring, the rules of the paper and a loading bar for the pictures.
3. Load all question pictures during the countdown:
   - First `GET /attempts/{id}/assets/links` (with cookies). Answer: `{ total, limit: 12, cdn, expires_at, parts: [url] }`.
   - Fetch every `parts[k]` **without cookies** (relative URL → prefix `https://jeelive.ai`). The body is the pack format: 4-byte big-endian header length, JSON header `{ total, items: [{question_id, index, size}] }`, then the PNG bytes in that order.
   - If a part fails twice, use `GET /attempts/{id}/assets/pack?offset=12k&limit=12` (with cookies), then single pictures `/questions/{qid}/asset/question/{i}`. Never give up while the test is open.
   - Keep the pictures in memory for the whole test. Do not cache them on disk after the test.
4. "Begin now" (enable at 100 % loaded): `POST /attempts/{id}/begin` with `{}` → new `deadline = now + full duration`. Otherwise open the paper by itself at `ready_until`.
5. While `ready_until` is in the future the server refuses answers and visits with `409 "Your paper opens in a few seconds."` and `Retry-After: 2`.
6. Bonus pictures are not in the links until the bonus section opens. After `POST /bonus` call `/assets/links` again.
7. Today `cdn` is `false` (links are on jeelive.ai). When the owner connects a CDN the same links point to the CDN host; the app code does not change.

### 2.3 Sign-in, PIN and Forgot PIN messages
- Only wrong PINs count. Each wrong PIN: `401` with the tries left in the message, for example "3 tries left before a 15-minute wait". Show `error.message` as is.
- 10 wrong PINs on one number within 15 minutes → `429` with `Retry-After` (seconds). During the wait even the correct PIN gets 429. Show a countdown from `Retry-After`; do not keep sending.
- One student address: 100 wrong PINs per 15 minutes, then the same wait for that address only.
- A correct PIN clears the number's count.
- Forgot PIN: `POST /auth/pin/reset { phone, new_pin, confirm_pin }`. It signs the student in (same body and cookies as sign-in). `404` "No account with this number" → send the student to signup. 5 resets per number per 15 minutes, then `429`.
- Live paper guard: while that number has a live ranked paper running, Forgot PIN and Change PIN answer `409` "A live ranked paper is running on this number. Forgot PIN works again after that paper ends." (Change PIN: "... PIN change works again after that paper ends."). Show as is.
- PINs are strings of exactly 4 ASCII digits; keep leading zeroes.

### 2.4 Busy and limited answers
- `503` with `error.code: "capacity_busy"` and message "This service is busy. Your saved work is safe; retry shortly." means the server is protecting itself at exam start. Wait `Retry-After` (or 1–3 s with jitter) and retry the same request (same `request_id` for answer saves). Do not show an error screen for one busy answer; show a small "Retrying…" note.
- `429` always comes with `Retry-After`. Wait that long.
- `409 "The time record is busy. Send it again."` (timeline): retry after `Retry-After: 2`.

---

## 3. Time capture in the test player (required for Analysis 2.0)

The website records how long each question was on screen. The server uses it for Time, Attempt Quality, Question Journey, par times, the topper's time and the class averages. **Attempts made in the app without time capture show "Agle mock se shuru hoga" in those three sections, and they are left out of the class time averages.**

### 3.1 What to record
One recorder per attempt and per device install. State: `sid` (random id, 8–40 chars of `A-Z a-z 0-9 _ -`; a UUID works), `n` (next event number, starts at 1), the list of unsent events, and the open stretch.

| Event | JSON | When |
|---|---|---|
| On-screen stretch | `{ "n": 7, "k": "v", "q": "<question uuid>", "a": 1795027000.5, "b": 1795027060.2 }` | A question was on screen from `a` to `b` (server-clock seconds). Close the stretch when the student moves to another question, opens the palette over it, the app goes to background, the screen locks, or the test ends |
| Answer changed | `{ "n": 8, "k": "a", "q": "<uuid>", "a": 1795027061.0, "v": "C" }` | Every answer change; `v` = new value (max 30 chars), `""` when cleared. While typing a numerical answer, update the last unsent `a` event of the same question if it is less than 5 s old instead of adding one per key |
| Mark for review | `{ "n": 9, "k": "m", "q": "<uuid>", "a": 1795027062.0, "v": "1" }` | `"1"` = marked, `"0"` = unmarked |

- Clock: server time, never the phone clock. `server_now` from the last response + monotonic time since then (`server_now + (performance.now() − t0)/1000`). Round to 0.1 s.
- Stretches shorter than 0.5 s are dropped. One stretch counts at most 15 minutes. Stretches must not overlap (the server cuts overlaps).
- Heartbeat: every 5 s store "still on this question at time T" with the open stretch. If the app is killed, on the next start close the open stretch at its last heartbeat (not at the restart time).
- Save the recorder state in app storage after every change, so a crash or restart loses nothing. Key it by user id + attempt id. Delete it after the server has acknowledged everything after submit.
- Do not record during the get-ready countdown (the server cuts anything before `ready_until`).

### 3.2 How to send (no extra requests during the rush)
- Every answer save can carry up to 200 events: `PUT /attempts/{id}/answers/{qid}` body = the normal save body + `"timeline": { "sid": "...", "events": [ ... ] }`. The answer's idempotency (request_id, revision) ignores the `timeline` part, so a retried save with the same events is safe.
- Submit carries the rest: `POST /attempts/{id}/submit` body `{ "timeline": { ... } }` (or `{}`).
- Both answers return `timeline_cursor` = the last event number the server holds for this `sid`. Drop every local event with `n <= timeline_cursor`.
- When 100 or more events are waiting (long time without answering), send them alone: `POST /attempts/{id}/timeline` body `{ "sid": "...", "events": [ ... ] }` → `{ "cursor": 42, "accepted": true }`. Loop until nothing is left or the cursor stops moving.
- Before submit, if more than 200 events wait, flush with `/timeline` first, then submit with the last batch.
- After an auto-submit (time over) or a lost connection, send what is left once with `/timeline`. The server takes it for **10 minutes after `submitted_at`**; later it answers `409 "This attempt ended more than 10 minutes ago. Its time record is final."` → delete the local record.
- Also flush leftovers before opening the analysis of that attempt (the website does this).

### 3.3 Rules the server checks
- Events in one batch must be numbered in order without gaps (`n`, `n+1`, `n+2`…). Otherwise `422 "Number the time events in order, without gaps."`. Batches from one `sid` continue the numbering; resending old numbers is harmless.
- `q` must be a question of this paper (36-char UUID). Unknown ids are dropped.
- `extra` fields are rejected (strict schema). `k` is only `v`, `a` or `m`. `b` only on `v`. Numbers must be JSON numbers.
- At most 2,000 events per attempt and 8 devices (`sid`s) per attempt.
- A second device on the same attempt uses its own `sid`. The server merges them in time order.

---

## 4. Analysis 2.0: API

All analysis calls need the student's cookies. Only the attempt's owner can open them. Other students appear only as a name (or "Learner XXXXXXXX"), a score, totals and times, never as answers.

| Purpose | Method / path | Notes |
|---|---|---|
| Whole analysis (one request) | GET `/attempts/{id}/analysis?mode=personal` | Sample `samples/01_analysis_personal.json` |
| Comparative | GET `/attempts/{id}/analysis?mode=comparative&compare=topper` | `compare` = `topper`, `top10`, `average` or `user:<16-hex handle>` from the leaderboard. Adds the `compare` object. Samples `02_*` |
| Corrected key version | add `&score_version=<name>` | Default `original`. Rank and class only exist on `original` (`class.state: original_only` otherwise) |
| Question list with a filter | GET `/attempts/{id}/analysis/questions?filter=wrong` | `filter` = `all, wrong, skipped, correct, careless, overtime, confused, marked, changed`. Answer `{ filter, total, time_data, items }`, items as `questions[]`. Sample `04_*` |
| Leaderboard | GET `/attempts/{id}/leaderboard` and `?q=<text>` | Sample `03_*`. See 6.2 |
| Save 3 learnings | PUT `/attempts/{id}/learnings` body `{ "items": ["...", "...", "..."] }` | Max 3 items, 140 chars each; empty ones are dropped. Answer `{ items }`. Sample `05_*` |
| PDF report | GET `/attempts/{id}/analysis/report.pdf[?score_version=]` | `application/pdf`, A4, 6–8 pages, file name in `Content-Disposition` (`JEELIVE_<paper>_<date>.pdf`). Save to a file and open with the system viewer / share sheet |
| Share scorecard | GET `/attempts/{id}/analysis/share.png` | `image/png` for WhatsApp share. Never contains the phone number. Share text on the website: "Mera Score {score}/{maximum} · JEELIVE.AI" |
| Live competition: compare with one student | GET `/competitions/{set_id}/compare/{handle}` | Only for live competition papers you submitted. Otherwise 404 "Compare ke liye pehle yeh paper khud submit karna hoga." (sample `09_*`) |

### 4.1 When the analysis opens (errors to show as is)
| Status | Message | App behaviour |
|---|---|---|
| 409 | "Analysis test submit karne ke baad khulta hai." | Attempt still active |
| 409 + `Retry-After: 2` | "Result abhi ban raha hai. Thodi der mein dobara kholo." | Grading still running: retry after 2 s |
| 403 | "Live exam abhi chal raha hai. Analysis sabka time khatam hone par khulega." | Live competition before its end: show the score card only |
| 410 | "Yeh test hata diya gaya hai. Sirf Score bacha hai." | Paper deleted |
| 404 | "Attempt not found." | Not this student's attempt |

### 4.2 `class.state`: what the student is told about the class
| `state` | Meaning | Rank tile text (website) |
|---|---|---|
| `ready` | Class stats exist: `n` students, `ranked: true`, `included`, `computed_at`, `min_finishers` (10), `above` (the student just above: `name`, `score`, `handle`) | Rank `#rank`, "{of} students mein" |
| `preparing` | Stats are being built. **Call the analysis again after 2.5 s, up to 5 more times** (website does this) | "Class ka data ban raha hai…" |
| `sealed` | Live paper before its end; `release_at` | "Rank sabka time khatam hone par aayega" |
| `staff` | Owner or reviewer account | "Staff attempt par Rank nahi banta" |
| `original_only` | A corrected key version is open | "Rank sirf original Score par banta hai" |
| `none` | Paper type without a class (only `practice` and `series_live` attempts have one) | "Is test par Rank nahi banta" |

### 4.3 Offline
The website keeps the last opened analysis (personal, original key) per student. When the request fails without an HTTP status (no internet) it shows that copy with "Internet nahi hai. Yeh pichhli baar khula hua analysis hai." Do the same with app storage keyed by user id. Never show another student's cached analysis after logout.

---

## 5. Analysis 2.0: the response, field by field

Top level: `analysis_version` (2), `rules_version` (2), `attempt_id`, `title`, `exam`, `mode`, `score_version`, `submitted_at`, `student { name }`, `paper`, `time_data`, `copy`, `class`, `overview`, `performance`, `potential`, `quality`, `time`, `difficulty`, `journey`, `habits`, `questions`, `you`, `compare`, `view`, `learnings`, `server_now`.

General rules: numbers are rounded to 0.1 and whole numbers come as integers; `null` means "no data" (show "—"); times are seconds (show as `"{m}m {ss}s"`, e.g. `"1m 05s"`); percentages are 0–100 with one decimal (show `"70.8%"`); question references are question ids (look them up in `questions[]` to show "Q17").

- `paper`: `count` (questions in the analysis), `minutes`, `duration` (s), `block` (s, 900 for papers ≤ 60 min, else 1800), `not_opened_bonus` (bonus questions left out because the bonus was never opened), `marks { correct, wrong }`.
- `time_data`: `true` when this attempt has a time record. `false` → Time, Attempt Quality and Journey show the "Agle mock se shuru hoga" card (sample `08_*`).
- `copy`: labels from the server: `copy.tags[tag] = [name, meaning]`, `copy.levels`, `copy.time_label`, `copy.level_sources`. Use these strings; do not hard-code different ones.

### 5.1 `questions[]` (one row per question; used by every section and by the Solutions screen)
| Field | Meaning |
|---|---|
| `id`, `number`, `subject`, `topic` (chapter or `""`), `type` (`mcq` / `integer`) | Question identity |
| `difficulty` | `easy`, `moderate`, `tough`, `unrated`; `difficulty_source` = `students`, `early`, `paper`, `none` |
| `response` | The student's answer as shown (option letter through `source_option_labels`, or the number), `""` when unanswered |
| `answer` | The correct answer(s) as shown, joined with ", " |
| `outcome` | `correct`, `incorrect`, `skipped`, `dropped`, `bonus` |
| `marks`, `pos`, `neg` | Marks got on this question; marks for right / wrong |
| `time` | Seconds on screen (`null` without time record) |
| `par`, `par_source`, `par_n` | Ideal time in s; from `solvers` (median of `par_n` students who solved it) or `standard` (paper standard) or `none` |
| `tag` | One Attempt Quality tag (5.6) or `null` |
| `marked`, `seen`, `at` (s after start when first answered, `null`), `look` (1 = answered on the first look, 2+ = after coming back) | Behaviour |
| `changed` | `"B→C"` when the first saved answer differs from the final one, else `null` |
| `visits` | How many separate visits (`null` without time record) |
| `class` | `null` until 10 students finished; else `n`, `correct` / `wrong` / `skipped` / `attempted` (% of class), `right_of_attempted` (%), `avg_time` (s), `topper_time` (s or `null` → "—"), `top_wrong { option, percent }` = the wrong option most students chose ("28.6% ne C chuna") or `null` |

### 5.2 `overview`
`score`, `maximum`, `percentage`, `rank`, `of`, `percentile` (only when `class.state` is `ready`), `attempted`, `correct`, `incorrect`, `skipped`, `accuracy`, `time_used` (s in the paper), `time_on_screen` (s on questions or `null`), `subjects[]` (`name, count, maximum, score, correct, incorrect, skipped, attempted, accuracy, time`),
- `ledger`: `earned`, `negative`, `left_wrong` (marks of wrong questions), `left_skipped`, `net`, `maximum`, `no_negative` (score if every wrong answer had been skipped).
- `verdict`: `{ tone: good|warn|bad|mute, section: <section key>, text }`: one Hinglish line; tapping it opens `section`.
- `distribution` (or `null` when fewer than 2 students): `bins[10] { from, to, count, you }`, `n`, `average`, `median`, `top`.
- `next3[]` (0–3 items): `{ key, marks, title, detail, questions[], section }`, already ranked by marks at stake, written by the server in Hinglish. No AI.

### 5.3 `performance`
`subjects[]`: `name, count, correct, incorrect, skipped, score, maximum, negative, attempted, accuracy, attempt_rate, not_seen, time`, `types { mcq|integer: {count, correct, incorrect, skipped, score, maximum, accuracy…} }`, `chapters[] { name, count, correct, incorrect, skipped, accuracy, lost, label }` (`label` = `strong` "Mazboot", `steady` "Theek", `weak` "Kamzor", or `null` under 3 questions).
`weak[]` (top 8): `{ subject, name, wrong, skipped, lost, questions[] }`. `sections` (BITSAT-style papers: `sections[]`, `main`, `bonus` with `entered`) or `null`. `has_chapters`.

### 5.4 `potential`
`available` (false without time record: careless and time steps are then 0), `current`, `steps[]`: `careless { marks, questions }`, `guard { marks, questions }`, `reinvest { marks, minutes, questions }`, `realistic` (= current + careless + guard + half of reinvest), `maximum` (= all three), `paper_maximum`, `at[] { key: current|realistic|maximum, score, rank, of, percentile }` (rank only with a class), `no_negative`, `guess { pos, neg, break_even }` ("Jawab tabhi do jab {break_even}% se zyada yakeen ho").

### 5.5 `time` (only when `available`)
`elapsed`, `on_screen`, `off_screen`, `by_outcome { correct, incorrect, unanswered }` (s), `by_subject[] { name, time, attempted, accuracy, count }`, `share[] { name, time_pct, weight_pct, score, maximum }` (share of time vs share of marks), `blocks[] { from, to, correct, incorrect, answered, time }`, `pace` (21 points: answers done after 0 %, 5 %, … 100 % of the paper time), `pace_split { correct[21], incorrect[21] }`, `first_look { first, return }` each `{ count, correct, accuracy, time, questions }`, `slowest[]` (5 ids). `habits.last` = accuracy in the last 20 % of the time vs before (`{ from, early, late }` or `null` when either side has fewer than 5 answers).

### 5.6 `quality` (Attempt Quality; only when `available`)
Exactly one tag per question (rules in `analysis_rulebook.json`):

| Tag | Name (copy) | Rule | Tone / website icon (lucide) |
|---|---|---|---|
| `perfect` | Perfect | correct within 1.25 × par | good / CheckCircle2 |
| `slow_correct` | Slow-correct | correct, slower than 1.25 × par | warn / Hourglass |
| `wasted` | Careless galti | wrong in less than 0.5 × par | bad / Zap |
| `concept_gap` | Concept gap | wrong between 0.5 × and 1.5 × par | bad / Brain |
| `costly_overtime` | Mehnga overtime | wrong after more than 1.5 × par | bad / Clock3 |
| `confused` | Confused | not answered, more than 0.5 × par spent | warn / HelpCircle |
| `smart_skip` | Smart skip | seen briefly and left | info / SkipForward |
| `not_seen` | Dekha hi nahi | never opened | mute / EyeOff |
| `no_score` | Score se bahar | dropped or bonus for all | mute / Ban |

Fields: `counts {tag: n}`, `headline { perfect, wasted, overtime (= slow_correct + costly_overtime), confused, concept_gap }`, `by_subject[] { name, counts }`, `par_from { solvers, standard }`, `lucky[]` (correct in less than 25 % of par), `painful[]` (wrong and over par).

### 5.7 `difficulty`
`all { easy|moderate|tough|unrated: { count, correct, incorrect, skipped, attempted, accuracy } }`, `by_subject[] { name, levels }`, `leak { wrong[], skipped[], marks }` (Easy marks lost), `sources { students|early|paper|none: n }`, `class_n`, `tough_solved[]`, `unlock { have, need, unrated }` or `null`. Level rule: 50+ students attempted → Easy ≥ 65 % right, Tough < 35 %; else the paper's tag; else early result (10+ students, labelled "shuruaati result se"); else Not rated. Never guessed.

### 5.8 `journey` and `habits`
`journey`: `available`, `visits[] { q, n (question number), a (s after start), d (s), v (which visit: 1, 2, 3…), mark? (true/false), set? ("B", "B→C" or "Clear") }`, `order[]` (subjects in the order first visited), `block` (s), `summary { visited, total, revisits, thrice }`, `first_block { minutes, answered, correct, incorrect }`.
`habits`: `changes { groups { w2r, r2w, w2w, r2s, w2s }, marks, total }` (wrong→right, right→wrong, wrong→wrong, right→cleared, wrong→cleared; `marks` = net effect), `streaks { correct, incorrect }` (longest runs in answer order), `last` (5.5).

### 5.9 `you` and `compare`
`you`: the student's totals in the same shape as other groups: `n, score, maximum, correct, incorrect, skipped, attempted, accuracy, time, on_screen, subjects[], difficulty{}, tags{}, time_by_outcome{}, pace[]`.
`compare` (only with `mode=comparative`):
- Not available: `{ available: false, kind, reason }`. Show `reason` as is. Reasons: "Compare result release hone ke baad khulega.", "Compare ke liye class ka data abhi taiyaar nahi hai. Thodi der mein dobara dekho.", "Abhi sirf aapne yeh paper diya hai. Doosra student aate hi Topper se Compare khul jaayega.", "Class aur Top 10% ka average kam se kam 10 students ke baad dikhta hai. Abhi {n} students ne diya hai.", "Is student ka data abhi jud raha hai. Thodi der mein dobara dekho.", "Yeh student is paper ke leaderboard mein nahi mila.", "Is result ke liye Compare uplabdh nahi hai."
- Available: `kind` (`topper|top10|average|user`), `label` ("Topper", "Top 10% ka average", "Class ka average" or the student's name), `profile` (same shape as `you`), `score`, `gap` (their score − yours), `by_subject[] { name, you, them, gap }` (biggest gap first), `by_difficulty[] { level, you, them }` (accuracy), `split[] { name, volume, quality }` and `split_total` (gap from more attempts vs better marks per attempt), `times { <question id>: seconds }` (their time per question, for the Qs by Qs column) or `null`, `n` (group size), and for `user`: `handle`, `rank`, `of`, `percentile`.

### 5.10 `learnings`
`{ mine: ["..."], previous: { attempt_id, title, items } | null }`: the student's own 3 notes for this attempt and the notes from the mock before it. Private to the student.

---

## 6. Analysis 2.0: screens (same as the website)

### 6.1 Frame and navigation
- Entry: the Results screen has tabs **Analysis**, Progress, Confidence, Real-exam rank (BITSAT: Branch matches) and **Solutions**. Analysis is Analysis 2.0.
- Top: kicker "ANALYSIS · {i} / 8" (+ " · COMPARATIVE"), the section title and its one-line description, then buttons **Report download**, **Share**, **Galat + chhode dobara** (only when there are wrong or skipped questions; this is the existing `/retry`) and **Solutions dekho**.
- Sticky bottom bar: a **Personal / Comparative** switch, then 8 numbered pills. Swipe left/right changes the section (ignore swipes that start on a chart or a horizontally scrolling table). Remember the last section opened per device. At the end of every section: "Pichhla {name}" / "Agla {name}" buttons.

| # | Key | Title | One-line description (show under the title) |
|---|---|---|---|
| 1 | `overview` | Overview | Ek nazar mein poora paper: Score, Rank, marks ka hisaab aur agle mock ke 3 kaam. |
| 2 | `performance` | Performance | Har subject aur chapter mein kitne marks bane aur kahan gaye. |
| 3 | `potential` | Score Potential | Seedha hisaab: kin galtiyon ko theek karke kitne marks aur kaunsi Rank mil sakti thi. |
| 4 | `quality` | Attempt Quality | Har sawaal ko ek tag: sahi time mein sahi, jaldbaazi, overtime ya concept gap. |
| 5 | `time` | Time kahan gaya | Aapka time kis subject, kis sawaal aur paper ke kis hisse mein gaya. |
| 6 | `difficulty` | Difficulty | Easy, Moderate aur Tough sawaalon par aapka haal, aur Easy marks ka leak. |
| 7 | `journey` | Question Journey | Aap paper mein kis raaste chale: kaun sa sawaal kab khola, kab wapas aaye, kab jawab badla. |
| 8 | `qs` | Qs by Qs | Har sawaal ki poori report ek jagah: aapka time, Par time aur class ka haal. |

- Drill-down everywhere: every tile, bar, chip and table row that stands for questions opens a list ("{n} sawaal. Kisi par tap karo, uska solution khulega.": Q number, subject, result, time, tag), and a question opens its solution on the Solutions tab.
- Locked card for sections that need the time record: title "Agle mock se shuru hoga", text "Is attempt mein har sawaal ka time record nahi hua tha. Agla mock doge to yeh hissa apne aap bhar jaayega."
- Labels: result `correct` "Sahi", `incorrect` "Galat", `skipped` "Chhoda", `dropped` "Dropped", `bonus` "Bonus". Tones: good, bad, mute (right/wrong also need an icon, not colour only).
- Colours (dark theme): good `#34D399`, bad `#FB7185`, warn `#FBBF24`, info `#7DB2FF`, mute `#94A5C3`, fill `#E11D48`, gold `#FBBF24`. Light theme: good `#0B8A5F`, bad `#C8213A`, warn `#A2640B`, info `#2459D8`, mute `#6B8192`, fill `#C8102E`, gold `#B7791F`. Fonts and other tokens: `design-tokens.json` of the 26 Oct package.

### 6.2 Section by section

**1. Overview**
- Score block, kicker "{count} SAWAAL · {minutes} MIN · +{correct} / {wrong}": score ring (`score / maximum`, `percentage`), the `verdict` line (tap → its section, link text "{Section} mein poora hisaab"), tiles Rank, Percentile ("Rank ke saath aayega"), Accuracy ("{correct} sahi / {attempted} attempted"), Time ("Sawaalon par {time_on_screen}" or "paper mein laga"), then tappable tiles Attempted, Sahi, Galat, Chhode.
- "MARKS KA HISAAB · Har mark kahan gaya": chips Kamaye +earned, Negative mein kate −negative, Galat jawab mein reh gaye, Chhode mein reh gaye, Net Score; a split bar; footnote "Agar ek bhi galat jawab na hota (sirf chhod dete), to Score {no_negative} hota. Negative ne {negative} marks khaaye."
- "SIRF AAPKE DATA SE · KOI AI NAHI · Agle mock ke liye 3 kaam": `next3` items with "+{marks} marks", "{n} sawaal dekho", "Poora hisaab". Empty: "Is attempt mein koi bada sudhaar ka point nahi mila. Ab naye sawaal try karo."
- Class standing (`distribution`): 10-column histogram, your column highlighted, facts Class average / Median / Top Score / "Aap {score} (average se X upar|neeche)", and `class.above`: "Aapse theek upar: {name} ({score} marks). Sirf {gap} marks aur, aur Rank ek upar." Without distribution: locked card "Class mein aap kahan ho" with the class-state note.
- Question map: one cell per question coloured by outcome, marked-for-review shown, tap → solution.
- Subject cards: score / maximum, meter, "{c} sahi · {w} galat · {s} chhode", "Accuracy x% · Time m s"; tap → wrong + skipped of that subject.
- "SIRF AAPKE LIYE · Is test se meri 3 seekh": 3 inputs (140 chars, hints "Jaise: Easy sawaal pehle round mein hi pakke karunga", "Jaise: 50% se kam yakeen ho to jawab nahi dunga", "Jaise: Ek sawaal par Par time ke 2 guna se zyada nahi"), "Save karo" → PUT learnings, toast "3 seekh save ho gayi. Agle mock ke analysis mein yeh dobara dikhengi.", "Yeh sirf aap dekh sakte ho." If `learnings.previous`: "Pichhle mock ({title}) mein aapne likha tha:" + list + "Kya is baar inpar amal hua? Neeche ke hisaab se khud check karo."

**2. Performance**
- Subject pills "Sab subjects" + each subject.
- All subjects: table Subject, Score, Score % meter, Accuracy, Attempt rate, Negative, Dekha nahi, Time.
- One subject: tiles Score, Accuracy, Attempt rate, Negative marks, Dekha hi nahi; table by type (MCQ / Numerical); chapter table (Chapter, Sawaal, Sahi, Galat, Chhode, Accuracy, Marks gaye, Haal: Mazboot / Theek / Kamzor / —) with "3 se kam sawaal wale chapter par Mazboot / Kamzor nahi likha jaata."
- "SABSE MEHNGE CHAPTERS · Marks kis chapter se gaye" bars from `weak`.
- Sections table for sectioned papers (Main total, Bonus or "Bonus khola hi nahi").
- No chapter tags: "Is paper ke sawaalon par chapter ka tag nahi hai, isliye chapter-wise hisaab nahi bana."

**3. Score Potential**
- "SEEDHA HISAAB · KOI ANDAAZA NAHI · Yahan se marks bach sakte the", note "Realistic target = Careless + Risk poora, aur atke time ka aadha. Maximum = teeno poore."
- Without time record: "Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain. Agle mock se poore dikhenge."
- Tiles Abhi ka Score, Realistic target (+x marks, sirf aadatein badal kar), Maximum potential.
- Waterfall chart: Abhi → Careless → Risk → Time → Max, with a dashed "Target" line at `realistic`.
- Step cards: "Careless galti theek", "Mushkil par risk nahi", "Atka time wapas" (+ "Atka time: {minutes} min."), each with its question chips; empty "Is step mein koi sawaal nahi. Badhiya!"
- "Itne marks par Rank lagbhag": `at[]` tiles with rank, of, percentile (only with a class).
- "NEGATIVE MARKING · Guess ka niyam": "Is paper mein sahi par +{pos} aur galat par {neg}. Jawab tabhi do jab {break_even}% se zyada yakeen ho." + "4 option mein se ek bhi pakka hata sako to guess faydemand hai. Bilkul andhere mein chhodna behtar hai." + "Bina kisi galat jawab ke (sirf chhod kar) aapka Score {no_negative} hota."

**4. Attempt Quality** (locked without time record)
- Headline tiles Perfect, Careless galti, Overtime, Confused, Concept gap (tap → questions) + chips for the other tags with counts; note uses `copy.time_label` and `par_from`.
- Speed-accuracy map: one dot per question with a time and a par; x = time ÷ par (0 to "3x+", dashed line at "Par"), three rows Sahi / Galat / Chhoda; shaded zones "Careless zone" (Galat, under 0.5x), "Mehnga overtime" (Galat, over 1.5x) and "Perfect zone" (Sahi, up to 1.25x); dot colour by outcome; tap → solution.
- "Painful sawaal" (`painful`) and "Kahin tukka to nahi tha?" (`lucky`) chips.
- Subject × tag table + grouped bars.
- Collapsible "Tags ke matlab (rulebook)" with `copy.tags`.

**5. Time kahan gaya** (locked without time record)
- Tiles Paper mein laga, Sawaalon par, Screen se bahar, Sahi par, Galat par; split bar sahi / galat / bina jawab with %; warning when wrong + unanswered time > correct time.
- Subject chart with Time / Questions / Accuracy toggle (y unit "m" or "%") + table with "Time ka hissa vs marks ka hissa".
- Time journey: stacked bars per block ("0–15m"…): Sahi, Galat.
- Pace curve (`pace`, and `pace_split` if you show correct/wrong lines).
- "Pehli nazar vs wapas aakar" tiles, "Aakhri 20% time · Thakaan ka asar" (empty: "Dono hisson mein kam se kam 5 jawab hone par yeh compare banta hai.").
- "Sabse dheeme 5 sawaal" list with time and par.

**6. Difficulty**
- Subject pills; "Leak: Easy sawaal" card ("{w} Easy galat aur {s} Easy chhoote. Yahan se {marks} marks bach sakte the. Easy marks sabse sasta Rank hai." or "Easy sawaalon mein koi leak nahi mila. Shaandaar!").
- Table Level × Sahi / Galat / Chhode as "x / N" (tap → questions) + accuracy meter; grouped bars. Note "Level kahan se aaya: {n} sawaal students ke result se, …".
- `unlock`: "{unrated} sawaal abhi Not rated hain. Jaise-jaise aur students yeh paper denge, unka level students ke result se pakka hota jaayega."
- "AAPKI TAAQAT · Tough sawaal jo aapne nikale" chips.

**7. Question Journey** (locked without time record; answer changes still show)
- Summary line "{total} mein se {visited} sawaal dekhe, {revisits} baar wapas gaye, {thrice} sawaal 3 ya zyada baar dekhe.", tiles Sawaal dekhe, Wapas gaye, Lagaataar sahi, Lagaataar galat, footnote "Subject order: A → B → C. Pehle {minutes} min mein {answered} jawab ({correct} sahi, {incorrect} galat)."
- "JAWAB BADALNA · {total} baar jawab badla": groups Galat se sahi / Sahi se galat / Galat se galat / Jawab hataya with chips; note with net marks.
- Visit chips grouped by block ("0–15 min · {n} visits"): "Q{n}", superscript "2nd/3rd…", duration, flag when marked, "B→C" when changed, tag colour + icon (toggle "Tag chhupao / Tag dikhao"). Tap → solution.

**8. Qs by Qs**
- Subject pills, filter pills with counts (Sab, Galat, Chhode, Careless, Overtime, Confused, Marked, Jawab badla), sort (Sawaal number, Sabse zyada time, Class mein sabse mushkil, Sabse zyada marks gaye).
- Phone: one card per question: "Q{n}", "{subject} · {level}", result + marks, "Aapka **{response}** · Sahi **{answer}** · badla {changed}", "Time {time} · Par {par} · Unka {their time}", "Class: {x}% sahi · avg {avg} · {p}% ne {option} chuna", tag chip. Tap → solution.
- Tablet: table Q, Subject, Chapter, Level, Aapka, Sahi jawab, Result, Marks, Time, Par, {compare label} · time (comparative only), Class avg, Class topper, Class % sahi, Sabse zyada galti, Visits, Tag.
- Empty filter: "Is filter mein koi sawaal nahi."

### 6.3 Comparative mode
- Picker "Kisse compare karna hai?": Topper, Top 10%, Class average, and "Leaderboard se student chuno…" (from leaderboard rows + around, not yourself) → reload the analysis with `compare=...`.
- Not available → card "Compare abhi nahi khula" + `reason`.
- Per section (website): head tiles Aapka Score / {label} / Gap ("marks peeche ho" / "marks aage ho" / "barabar") / Time on Overview, Potential, Journey, Qs; "Gap sabse bada kahan hai" (subject, difficulty, volume vs quality table with "Zyada sawaal attempt karo" / "Accuracy badhao" / "Aap aage ho") on Overview, Potential, Performance; subject chart + table "Aap vs woh" on Overview, Performance; Attempt Quality table on Quality ("Dono taraf time record hone par hi Attempt Quality compare hoti hai."); pace lines on Time (x = % of time); accuracy by difficulty on Difficulty; "{label} · time" column in Qs by Qs.
- Always say "Sirf totals aur averages. Kisi doosre student ke jawab kabhi nahi dikhte."

### 6.4 Leaderboard (Comparative › Overview, when `class.state` is `ready`)
- `GET /attempts/{id}/leaderboard` → `{ state, n, title, rows (top 50), around (5 above, you, 5 below), found, query, you, min_finishers }`. Row: `rank, name, named, handle, score, attempted, accuracy, time, is_you`. Equal scores share a rank.
- Search `?q=` (max 20 chars, wait 350 ms after typing): digits = that rank; 2–16 hex chars (or "learner xxxx") = handle; anything else = display-name prefix. Empty: "Is naam ya Rank ka koi student nahi mila."
- Show the top 10, then "Aapke aas-paas" when you are not in the top 10. Your row says "Aap". Each other row has **Compare** → `compare=user:<handle>`.
- When `state` is not `ready` the answer is `{ state, n: 0, rows: [], around: [], found: [], release_at }`: hide the board.

---

## 7. Report, share and the Solutions screen

### 7.1 PDF report
`GET /attempts/{id}/analysis/report.pdf` (add `?score_version=` for a corrected key). The file is made once and kept; it includes the 3 learnings. Busy button while downloading; error toast "File abhi nahi ban paayi. Thodi der mein dobara try karo."

### 7.2 Share scorecard
`GET /attempts/{id}/analysis/share.png` → system share sheet with text "Mera Score {score}/{maximum} · JEELIVE.AI". If sharing is not possible, save it and say "Scorecard download ho gaya. Ab WhatsApp par bhej sakte ho."

### 7.3 Retry mistakes
"Galat + chhode dobara" is the existing `POST /attempts/{id}/retry` (unchanged).

### 7.4 Solutions screen: one insight line above each solution
From `analysis.questions` (same id): "Q{n} · {subject} · {level} · Aapka time {time} · Par {par} · {x}% ne sahi kiya · Topper {topper_time} · Sabse zyada galti: option {option} ({percent}%) · {visits} baar dekha · Jawab badla {changed} · {tag chip}". Leave out any part that is `null` (topper time 0 or null = leave out). Below it keep the existing answer block: "Your answer" (through `source_option_labels`), the correct answer(s), `typed_options` for picture MCQs, then the original solution pictures (`solution_asset_count`) or "answer key only".

---

## 8. Other changes since 26 Oct (details in APP_INTEGRATION.md)

### 8.1 Exam structure from the API (section 12)
- Home exam cards: `GET /catalog/exams`. Exam page: `GET /catalog/exams/{slug}` → `sections[]` in the owner's order with `live_count`. Section list: `GET /exam-navigation/{slug}/catalogue?section={slug}`. JEE Main PYQ keeps `GET /pyq/jee-main`. Always add a Results entry (`/exam-navigation/{slug}/history`).
- **Correction to older notes:** a test series now appears **inside its exam** as a section with `kind: "aits"`, `live_count: 0` and `series_path` (`/series/all-india-jee` or `/series/{id}`). When `series_path` is set, open the series screen instead of a section list. JEE Main also keeps its Home banner.
- Test names come from `title`; Unlive tests disappear; `catalog_path` on `/my/sets/{id}` and `/sets/{id}` for the back action.

### 8.2 Live exams: 15-minute start window, score on submission (section 13)
`last_start_at` and `can_start` on `/competitions`. After `last_start_at`, start answers 409. Before `end_at`, results come back `embargoed` with `score_released: true` and `summary`; answers, solutions and analysis open at `end_at` (analysis 403 before).

### 8.3 Test series for every exam (section 14)
`GET /series`, `/series/{id}/schedule`, `/series/{id}/history`; All India JEE keeps `/series/all-india-jee`. Series attempts: score and solutions right after submit; the day's rank via `GET /attempts/{id}/series-rank` (`sealed` with `release_at` until the day closes, then `ready` with `rank`, `total`, `top_percent`). JEE All India series: 9 Dec 2026 – 27 Jan 2027 (50 days); dates always from the API.

### 8.4 Written questions and typed options
`render_mode: "written"`: show `text` (maths between `$`), option texts, then `asset_count` pictures; `asset_labels[i]` is `""` for the question figure or "Option A"… for an option figure. Picture questions with `typed_options`: section 2.1.

### 8.5 BITSAT bonus section
Papers with `rules.bonus_rule` have bonus questions (`bonus: true`) hidden until the student enters the bonus. `POST /attempts/{id}/bonus` (empty body) → `{ id, bonus_unlocked_at, server_now }`. It needs every main question answered: otherwise `409 "Answer all {n} main questions first. {m} still unanswered."`. After entering, main answers are locked. Then call `/attempts/{id}` and `/assets/links` again for the bonus questions.

### 8.6 Display name (leaderboards, Compare, own report)
`PUT /profile/display-name { "name": "Arjun" }` → `{ display_name }`; `""` removes it. 2–20 letters, digits and spaces; no phone-number-like digits; abusive or official-looking names refused (422 with a Hinglish message, show as is); 3 changes per day (429 "Naam din mein 3 baar hi badal sakta hai. Kal dobara try karo."); student accounts only. `/auth/me` returns `display_name`. Without a name the student appears as "Learner XXXXXXXX". (The website has no name screen yet; a Profile field "Leaderboard par naam" is enough.)

---

## 9. Acceptance checks for the app

1. Picture paper (BITSAT chapter-wise or JEE Main PYQ): in the test and in results only pictures show; no "Original PDF question…", no "01. For z…", option buttons show letters; typed options appear under the picture where the website shows them.
2. Start a paper: get-ready ring counts down, pictures load through `/assets/links` (no cookies on those requests), "Begin now" works at 100 %, the paper opens by itself at 0. Turn off the internet during loading: it keeps retrying and finishes when back.
3. Time capture: take a 3-question practice paper on the app, move between questions, put the app in background for 20 s, change an answer, mark one, submit. Open the analysis on the **website**: Time, Attempt Quality and Journey are filled; the background time is "Screen se bahar"; the change shows "B→C"; the mark shows a flag.
4. Kill the app in the middle of a question, reopen, continue, submit: no error; the stretch ends at the last heartbeat.
5. Same student, same attempt on website and app: numbers in all 8 sections match exactly (the server computes everything).
6. Old attempt without time record: Overview, Performance, Score Potential (partial note), Difficulty and Qs by Qs work; Time, Attempt Quality and Journey show the locked card.
7. Comparative: Topper / Top 10% / Class average / a leaderboard student; with fewer than 10 students the reason text shows.
8. Leaderboard search by rank and by name; Compare from a row.
9. 3 learnings save, reappear after reopening, and show as "Pichhle mock…" on the next mock.
10. PDF downloads and opens; Share opens the share sheet with the PNG.
11. PIN: 3 wrong PINs show tries left; 10 wrong show the 15-minute wait; Forgot PIN signs in.
12. Busy server (simulate 503 `capacity_busy`): answer saves retry with the same `request_id` and nothing is lost.
13. Exam page shows the series section and opens the series screen through `series_path`.
14. Offline: the last opened analysis shows with the "Internet nahi hai…" note.
