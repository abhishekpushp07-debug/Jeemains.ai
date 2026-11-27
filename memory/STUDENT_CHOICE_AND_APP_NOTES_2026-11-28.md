# Owner's saved notes (2026-11-28): Student Choice Phase 1 handoff + app agent messages

Saved on the owner's request ("sab save rakhna, kaam aaye tab use karna"). NOT started. Do not build anything from here
without the owner's explicit go-ahead. Never deploy unless the owner writes exactly `deploy`.

## 1. Owner's direction (summary)
- Student Choice must be built in sync with the APP: same shape, compatible, one launch, then no app update needed.
- The app already has the screens. "Paper banao" asks the website's doors A/B/C; until they exist the app shows
  "Paper banana abhi jeelive.ai se jud raha hai… aapke chune sawaal yahin rahenge."
- Condition: the doors must match the app's book (Part 7 / feature book v3 Part 1) exactly. A shape change or a new field
  means an app update.
- Before switching Door A on for students, tell the app agent; it will test the full flow with a test student (book rule 20).

## 2. Misfire Mock (owner's decisions, via the app agent)
- Owner's answers: correct answers in the mock auto-mark "Samajh gaya"; if a chapter has fewer Misfire questions than asked,
  give what exists and say so; result shows in BOTH My Tests and Misfire, with the same good test screen.
- Because of the My Tests choice, the app agent recommends building it through the website: a new Door C mode
  `mode: "misfire"` (Misfire's chosen questions), a real website paper (timer, My Tests, Analysis 2.0); on submit the website
  itself marks correct ones "Samajh gaya"; Door A gets a `misfire: true` switch (tab hidden until on, no app update).
- Flow in the app: Misfire → "Mock banao" tab → subjects (P/C/M, one or more) → chapters (multi or "Select all chapters")
  → questions per subject (up to 25) → Start.
- Time per question: Physics 2.4 min, Chemistry 1.6 min, Maths 3.2 min (25 each = 60/40/80 min; 75 = 3 h).
  Example: Physics 10 + Maths 5 = 24 + 16 = 40 min.
- Phone-only version is possible but not recommended (no website result, no rank/Analysis 2.0, not a real My Tests paper).
- The app agent offered to write the `misfire` part as one page in its book so the website builds it with Student Choice.

## 3. AITS analysis note from the app agent (website must keep this shape)
- The app builds no analysis; it shows `GET /attempts/{id}/analysis` (analysis_version 3, rules_version 2) as sent.
- Per question it reads: `subject`, `topic` (= chapter name, same as catalogue), `difficulty` (only
  `easy`/`moderate`/`tough`/`unrated`), `difficulty_source`, `outcome` (`correct`/`incorrect`/`skipped`/`bonus`/`dropped`),
  `marks`, `time`, and the class numbers. Bonus questions are not counted in any column.
- App's own maths only: level accuracy = correct ÷ (correct + wrong); time %.
- Hiding rules: "Previous-year paper" / "Uncategorised" are not chapters; the Easy-leak line only when Easy questions exist;
  "level kahan se aaya" only when `level_sources` has something.
- Website asks: re-build analysis of earlier attempts when tags are added later; `has_chapters: false` when chapters are
  only generic; lists never `null`; level names exactly these 4.
- Match test: open the same AITS attempt on website and app; score, rank, every subject/chapter row and every Difficulty
  cell must be the same. (App side note: `memory/WEBSITE_AITS_ANALYSIS_NOTE.md` in the app project.)

## 4. HANDOFF GUIDE: Student Choice, Phase 1 (as given by the previous agent, verbatim in substance)

### 4.1 Where things stand
- Approved plan: `/app/plan/plan.md` (224 lines) is the source of truth; approval stands, do not ask again.
- Done so far: discovery only. No file created/edited, no DB write, no test, no deploy. All five pockets unimplemented.

### 4.2 Golden rules
1. Never deploy unless the owner writes exactly `deploy`. 2. No drops / hard deletes on any real DB. 3. Do not change
preview data to fake a demo. 4. Do not touch login/PIN/JWT, scoring and rank, chapter tests, PYQ, AITS, `LiveSeries.js`,
Rapid Fire, Mission, Dream, Rank page, PDF/cutter/storage — except the narrow integration points in 4.6. 5. No unrelated
refactors. 6. With both switches Off, website and app behave exactly as today. 7. Small pockets, verify each.
8. MongoDB suites one at a time through `solo.sh`, never overlapping. 9. Auth tests only with `/app/memory/test_credentials.md`.
10. Unique `data-testid` on every interactive/critical element. 11. Hindi/Hinglish with the owner; one final report, stop before deploy.

### 4.3 The three doors (exact contracts)
Full text: `/app/docs/app_book_v3/BOOK.md` lines 219–530 and 656–770. Examples:
`/root/appchoice/handoff/feature_book/examples/choice_door_{A,B,C}.json`. Signed-in student, cookie session; plain JSON or
the `{data, error, meta}` envelope.

**Door A: `GET /api/choice/bank?exam=jee-main`**
```json
{ "pick": true, "random": true, "max_questions": 75, "max_per_subject": null,
  "minutes_per_question": { "Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2 } }
```
- 404 when both modes Off or exam unsupported. Never 5xx (catch everything, answer 404). Never 401/403 for a good session.
  Do not send `subjects`. Nothing personal (shared and cached).

**Door B: `GET /api/choice/chapters/<chapter-test set id>/questions?page=1`**
```json
{ "chapter": { "id": "...", "title": "...", "subject": "Physics" }, "pages": 2,
  "items": [ { "id": "...", "number": 1, "type": "mcq", "text": "...", "stem": [] },
             { "id": "...", "number": 2, "type": "integer", "text": "",
               "stem": [ { "url": "https://...", "w": 506.5, "h": 47 } ] } ] }
```
- 50 items/page; `pages` 1–6. `id` 6–80 chars `[A-Za-z0-9_-]`, stable. `text` ≤ 3000 chars; `stem` ≤ 4 items.
- `url`: absolute https, no spaces, ≤ 900 chars, opens without cookies, valid ≥ 24 h, WebP when possible.
- `w`/`h`: both or neither, print points (file holds 2 px per point). Never options/answer/solution/key.
- Question with neither text nor stem picture is left out. 404 for unknown chapter or nothing to choose; page `pages+1` → 404 or empty.

**Door C: `POST /api/choice/papers`**
```json
{ "exam": "jee-main", "request_key": "<uuid>", "mode": "pick", "question_ids": ["..."] }
{ "exam": "jee-main", "request_key": "<uuid>", "mode": "random", "count": 30 }
```
- 200/201 `{ "set_id": "<id>" }` matching `^[A-Za-z0-9_-]{6,80}$`. Same `request_key` → same `set_id`, never a second paper.
- Failed check → 422 with one plain sentence in `error.message`. App shows 422/409/429 sentences as written; it replaces
  404/405 with its own text, so never use those for a refusal.
- App then calls `GET /api/my/sets/<set_id>` and `POST /api/sets/<set_id>/start`; both work for the owner of the paper and
  "not found" for anyone else. Request arrives with no Origin header.
- Paper: `test_kind: "choice"`, `exam: "JEE Main"`, rules `{correct 4, wrong -1, skipped 0, minutes}`, `maximum = count × 4`.
  `test_kind: "choice"` also on `GET /api/attempts/<id>/results` and every item of `GET /api/my/tests`.

**Paper rules**
- Pick 1–75; Random 3–75. Order P, C, M; inside a subject MCQ first, then numerical.
- Minutes: `ceil(round(Σ count × per-subject minutes, 4))`, no 180 cap. Checks: 3P+2C+2M = 17; 10+10+10 = 72; 25 M = 80; 75 M = 240.
- Random split equal across subjects with live chapters, remainder to Physics then Chemistry (10 = 4+3+3, 11 = 4+4+3, 75 = 25+25+25).
  Inside a subject about 4 MCQ : 1 numerical, mixed across chapters.
- Daily quota 5 papers per student (pick + random), IST day; a retry of the same key does not count.

**Owner's exact sentences** (75 and 5 are the configured values):
- "Ek paper me zyada se zyada 75 sawaal ho sakte hain."
- "Chune hue sawaalon me se kuch ab available nahi hain. Dobara chuno."
- "3 se 75 ke beech ginti likho."
- "Aaj ke 5 paper ban chuke hain. Kal naya paper bana sakte ho."
- "Is paper ke kuch sawaal ab available nahi hain. Naya paper bana lo."
- "Paper banana abhi band hai."
- "Sawaal abhi load nahi ho paaye. Dobara try karo."
- Result screen: "Is test par Rank nahi banta".
(The Door C sample words the 75 limit differently; the owner's wording wins.)

### 4.4 Preview database (read-only checks)
- JEE Main chapter sets: 78 (29 P, 26 M, 23 C), 3,900 questions, distinct 36-char UUIDs. **All 78 `archived: true`** →
  student-live pool on preview is empty; functional tests need an isolated disposable DB with fixtures.
- Every question old look: `render_mode: "source"`, one `q_refs` crop, no `c_refs` (no set in preview has `c_refs`).
- MCQ text like `"Q4.\nSingle correct\n<question>\n(A) …\n(B) …"`; options are placeholders ("See original option A").
  Numerical like `"Q27.\nInteger response\n<question>"`, empty options.
- Every question has `subject`, `section`, `topic`; in samples `section` and `topic` = chapter title. Sources `rights_report: true`, +4/−1.
- Live has a different set (81 tests, 3,750 questions per the plan), probably with cut pieces — unverified.

### 4.5 Code findings
1. Route registry `tejas/route_contracts.py`: every `/api/` route needs a `SPEC` entry `module.function_name` or the server
   will not start; every write route with a body needs `MODELS` (`tejas/request_contracts.py` 315–398). New module → both
   lists in `server.py` (imports 12–74, mounting 264–327).
2. Body checks run first in middleware (`http_limits.py`): schema failure → generic English 422. Door C schema must be loose
   on business limits; handler raises the owner's sentences. Schema strict: no unknown fields, no number coercion.
3. Default body limit 4096 bytes; 75 ids nearly fill it, 76 → 413. Raise Door C limit in `route_contracts.py` 329–347.
4. `HTTPException(status, sentence)` already becomes `{data:null, error:{code:"http_<status>", message}, meta}`.
5. Everything outside `/api/media/` is forced to `Cache-Control: private, no-store`; `/api/media/` may set public caching →
   Door B picture route belongs there.
6. Start flow (`attempts.py` 220–338): checks `status == "published"`, `permitted()`, `hidden_from()`; loads via
   `papers.paper()`; seals pack + profile via `start_data()`; `test_kind = classify_set(s)` never returns `choice`;
   `my_set` 176–183, `preflight` 186–217 (needs `revision`).
7. Private papers in `tejas_sets` would leak into owner screens (`structure.ADMIN_BASE` "unplaced", `content.studio_sets`,
   `manual_solutions.solve_tests`, CEO content counts; `master.py`, `library.py`, `integrity.py`, `duplicates.py` not read).
8. A missing set is tolerated downstream (`misfire.take`, `mock_solutions.for_attempt`, `class_stats.hints_for`,
   `cohorts.read`); answers/timeline/reviews/analysis/reports don't query sets. `jobs.py` grade path not yet checked.
9. Already excluded for non-mocks: personal journey, historical rank, AIR scenario.
10. Need explicit guards: `dreams.is_full()` (would count a 75-q choice paper as a full mock); `class_stats.record()` and
    `analysis_api.class_state()` (class of one); `cohorts.record()` / `cohorts.read()`.
11. Chapter names come free (`q.topic`). `section` is also the chapter title → mixed paper may show one tab per chapter;
    check `Player.js`, if so set `section = subject` on copied questions.
12. Existing picture links don't fit Door B (`media.py` multi-picture `.bin`, relative because `MEDIA_CDN_URL` unset).
    Door B needs a new single-picture signed route with absolute https base. Reuse: HMAC in `media.sign`, expiry
    `(day + 2) × 86400`, `pictures.webp_of()`, `derivatives.render_crop()`.
13. Chapter list: `GET /api/exam-navigation/jee-main/catalogue?kind=chapters&subject=…` (`per_page` ≤ 100) already returns
    counts, types, the student's attempt. No new list endpoint needed.
14. `my_tests.HistoryItem` has no `test_kind`; add it.
15. "Sawaal galat hai": `question_reports.report_wrong` stores the attempt's `set_id`; a choice attempt needs a per-question
    source map so the report lands on the original chapter test (content hash ignores number/section → groups with originals).
16. Build rules with `content.valid_rules()` so `profiles.definition()` accepts them; 240 minutes is within limit.
17. Isolated harnesses swap module-level DB handles to `tejas_isolated_*`; keep new collection handles module-level and caches resettable.

### 4.6 Recommended design (not yet proven)
- Storage: own collection (e.g. `tejas_choice_papers`), not `tejas_sets` (finding 7; finding 8 shows the rest copes).
  Confirm `jobs.py` grade path first; fallback = `tejas_sets` row with `audience: "restricted"` + exclusion in every admin scan.
- New collections: Settings (one doc per exam slug; defaults both Off, max 75, minutes 2.4/1.6/3.2, daily 5, per-subject
  empty; revision check, `updated_by`/`updated_at`, `audit()`); Papers (`_id` from user id + `request_key`; owner, mode,
  ordered question identities, light stubs, rules, title, created IST day, `pack_id` after first start); Day counter (per
  user per IST day, atomic, keyed by `request_key`); Creators (per user, all-time count).
- Door C order: look up by derived id → return if found; validate (mode on, limits, ids live & unique, or draw random);
  reserve quota atomically; insert, on duplicate key return existing.
- Start/freezing: first Start re-checks every source question is live (else owner's sentence), builds, seals pack, saves
  `pack_id`; later Starts reuse the pack.
- Narrow edits: `attempts.py` (`my_set`, `preflight`, `start` fall back to the choice paper for its owner only);
  `dreams.py` (never count `choice`); `class_stats.py`, `cohorts.py`, `analysis_api.py` (no class/rank/leaderboard for
  `choice`); `my_tests.py` (`test_kind`); `question_reports.py` (map to source set); `route_contracts.py`,
  `request_contracts.py`, `server.py` (registration).
- Door B preview rules: cut question → `c_refs` piece part `q` with its `w`/`h`; old-look numerical → whole `q_refs`
  picture, size from crop rectangle; old-look MCQ → text only, strip "Q n." and "Single correct" lines, cut from first `(A)`;
  no option marker → leave out. Picture route resolves the crop on the server from set id, question id, index; never takes
  coordinates from the link; never serves an MCQ's whole crop or a solution.
- Open decisions: 429 for daily limit, 409 for "Paper banana abhi band hai."; new sentence needed for a random mock when a
  subject has too few questions (show the owner); numbering 1..N with original number in the source map (pictures still show
  the printed "Q27."); base URL for picture links without CDN — `FRONTEND_URL` is an inference, verify.

### 4.7 Not yet read
- `jobs.py` grade path (~60–175) and `jobs.status` (329–360); `scoring.py`.
- `safety.py`, `import_guard.py`, `runtime.py` (new POST path not held).
- `master.py`, `library.py`, Super Admin frontend (`components/master`, `components/admin`) for the "Student Choice" tab.
- Frontend: `SetDetail`, `Player` (tabs, long timers), `Results` and `AnalysisWorkspace` (rank, Dream, celebration),
  Profile/My Tests, Home and ExamHub tiles. (Pages are in `frontend/src/features/`.)
- `BOOK.md` 126–218 (screens, search), 1482–1556 (every student sentence), 1574–1595 (screen part names).
- App reference `/root/appchoice/frontend`: `app/choice/*.tsx`, `src/choice/search.ts`, `store.ts`, `parts.tsx`, `looks.tsx`
  (only `api.ts` and `backend/choice.py` were read).
- `tests/chapters_iso182.py`, `chapters_bridge182.py` (best fixture templates).
- Whether memory already records "5 papers a day" and the Phase 2 order (search `/app/memory` first).
- How many of the 3,398 old-look MCQ texts split cleanly at `(A)` (read-only count).

### 4.8 Work pockets
| # | Pocket | Check before moving on |
|---|---|---|
| 0 | Finish 4.7 backend reads; settle storage; record owner decisions in memory | No code yet |
| 1 | New module: settings, owner read/save, registration; both switches Off | Server starts; Door A 404; health + one catalogue call unchanged |
| 2 | Pool, Door A, Door B, signed picture route, caches | Isolated test: exact shapes, no option/answer/solution, links open without cookies |
| 3 | Door C, quota + idempotency, `my_set`/`preflight`/`start`, exclusions, My Tests kind, report mapping | Isolated: double request = one paper + one quota use; other student "not found"; no rank; not counted for Dream |
| 4 | Website pages + Super Admin tab (desktop and 390 px) | One smoke screenshot, then independent frontend run against an isolated bridge |
| 5 | Edge cases, full sequential regression, app compatibility note, PRD update, final report | Compare with baseline; stop |

### 4.9 Testing rules
- `bash /app/backend/tests/runners/solo.sh python -u tests/<file>.py`, one suite at a time; lock `/root/p2/suite.lock`
  (create `/root/p2` if missing). Only disposable `tejas_isolated_*` DBs, storage mocked; drop only those.
- After a timeout wait for child processes to end. Baseline: 54 suites, 1,798 checks, 1,778 passes, 20 inherited failures;
  a new or unexplained failure blocks the report.

### 4.10 Carried-over items (not part of this build)
- PYQ storage 404 → 503 `vault_unavailable` on production: cause unknown.
- N2 Rank page fixes: need an independent retest before any deploy.
- `Player.js` effect-dependency warnings (78/83) and lint config: untouched.
- Unverified: real phone, the app's real server, first paper on live, load capacity.
- Phase 2 and 3 need separate approval (plan lines 188–197).
- Raise with the owner (don't change silently): the website's Dream meter can count a very long chapter test, while the
  owner's rule says chapter tests never count.

### 4.11 Saving credits
- Do not re-read the digested files (`attempts.py`, `content.py`, `db.py`, `server.py`, `route_contracts.py`,
  `request_contracts.py`, `structure.py`, `media.py`, `pictures.py`, `derivatives.py`, `cohorts.py`, `class_stats.py`,
  `analysis_api.py`, `misfire.py`, `my_tests.py`, `dreams.py`, `papers.py`, `packs.py`, `exam_navigation.py`, `catalog.py`,
  `http_limits.py`, `admission.py`); open them only at the line being edited. Start code in pocket 1 once pocket 0 reads are done.
