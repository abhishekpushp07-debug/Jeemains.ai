# 03 · Rank API reference

Every Rank endpoint of the app server, field by field. All paths are relative to the API root
(`https://jeelive-mobile.emergent.host/api`, or the website's own `/api` once the connector is mounted).

- **Public.** No account, no key, no cookie.
- **JSON in, JSON out**, except the seven PDF routes (JSON in, `application/pdf` out).
- **Numbers are server-made.** Show them as they arrive. Never recompute them in the browser (`docs/04` explains them only so you understand them).
- **Sentences are server-made.** Every `note`, `notes`, `summary`, `spread`, `check`, `gap`, `line`, `blocked` and error `detail` is ready to show.
- A real request and answer for every endpoint sits in `RANK/api_examples/` (frozen samples, see the warning in §0).

There are 16 JSON endpoints and 7 PDF endpoints. Two are **new in this pack** (Cut off, §13), and the JEE Main form
gained one optional field, the scorecard `rank` (§0):

| # | Method · path | Tool | Section |
|---|---|---|---|
| 1 | `GET /rank/meta` | every tool (lists, chart, notes, sources) | §1 |
| 2 | `POST /rank/estimate` | Rank predictor | §2 |
| 3 | `POST /rank/percentile` | no screen any more (was "Percentile se rank"); still served | §3 |
| 4 | `POST /rank/predict` | College predictor · JEE Main list | §4 |
| 5 | `POST /rank/college` | College predictor · JEE college sheet | §5 |
| 6 | `POST /rank/bitsat` | College predictor · BITSAT | §6 |
| 7 | `POST /rank/comedk` | College predictor · COMEDK list | §7 |
| 8 | `POST /rank/comedk/college` | College predictor · COMEDK college sheet | §8 |
| 9 | `GET /rank/colleges` | Target marks + College compare search lists | §9 |
| 10 | `POST /rank/target/jee` | Target marks · JEE | §10 |
| 11 | `POST /rank/target/comedk` | Target marks · COMEDK | §10 |
| 12 | `GET /rank/target/bitsat` | Target marks · BITSAT | §10 |
| 13 | `POST /rank/compare` | College compare · branch vs branch | §11 |
| 14 | `POST /rank/compare/colleges` | College compare · college vs college | §11 |
| 15–21 | `POST /rank/pdf/…` | PDF buttons | §12 |
| **22** | **`GET /rank/cutoff/options`** | **Cut off · the college and branch pickers — NEW** | §13.1 |
| **23** | **`POST /rank/cutoff`** | **Cut off · the cut-off table, with or without a score — NEW** | §13.2 |

## 0. Conventions

**The samples are not data.** `RANK/api_examples/*.json` were captured once, when this pack was built. They show the
shape of every answer. Do not load them into the website, do not copy a number from them into a page. The app server's
data is renewed when new cut-offs are published; the website must always show what the server says today.

**Shared form (JEE Main).** `predict`, `college` and `pdf/jee` take the same student form:

| Field | Type | Default | Rule |
|---|---|---|---|
| `marks` | integer | none | −75 … 300 |
| `percentile` | number | none | 0 … 100 (the NTA percentile) |
| `rank` | integer | none | **new** · 1 … 20,00,000: the All India Rank (CRL) printed on the scorecard |
| `level` | `"tough"` · `"normal"` · `"easy"` | `"normal"` | how hard the student's shift was (used with marks only) |
| `category` | `"GEN"` · `"EWS"` · `"OBC-NCL"` · `"SC"` · `"ST"` | `"GEN"` | |
| `female` | boolean | `false` | opens Female-only seats |
| `pwd` | boolean | `false` | opens PwD seats |
| `state` | string or `null` | `null` | must be one of `meta.states` exactly; decides Home state / Other state / Delhi seats |
| `branches` | string[] | `[]` | names from `meta.branches`; unknown names are dropped silently; `[]` = all branches |

**Which score is used.** Send at least one of `marks`, `percentile`, `rank`. With more than one, the most exact wins:
**rank, then percentile, then marks**. The result block's `source` says which one was used. The others are only used
to check it: when they disagree the answer carries a `check` sentence. Forms written for the earlier pack (marks or
percentile only) work unchanged.

None of the three → `422 {"detail": "Marks, percentile ya rank mein se koi ek daalo."}`
(a server without this pack's work still says "Marks ya percentile mein se koi ek daalo.").

**Ranges.** A pair `[a, b]` is always `[better, worse]` for ranks (smaller number first) and `[lower, higher]` for
percentiles. When both ends are equal, show one number.

**Tags.** `"safe"` · `"likely"` · `"borderline"`. Display them as **Safe**, **Likely**, **Borderline**. A seat out of
reach has no tag and is never in `items`; the nearest ones are in `near` with a `gap` sentence.

**Errors.** `{"detail": "<sentence>"}` for rule errors (422, 404); `{"detail": [ {loc, msg, …} ]}` for a wrong field
type or range (422; validate in the form so the student never sees this). See `docs/02_CONNECT_GUIDE.md` §6.

**Indian number format.** The server sends plain integers; the app shows them as `1,07,693`. `fmt()` in
`CONNECT/frontend_web/jeeliveApp.ts` does exactly that.

---

## 1. `GET /rank/meta`

The lists and words every Rank screen needs. About 6 KB. Fetch once per visit.

| Field | Meaning |
|---|---|
| `states` | 36 states and union territories, in the exact spelling the server accepts |
| `branches` | 20 JEE branch groups (`"Computer Science"`, `"AI & Data Science"`, …) for the branch filter |
| `categories` | `["GEN","EWS","OBC-NCL","SC","ST"]` |
| `chart` | 50 lines `{pct, rank, marks}`: percentile 99.9 → 80, the CRL at it and the marks on a normal paper (Percentile chart) |
| `note` | the estimate sentence under every JEE result |
| `missing` | sentences naming data the official bodies did not publish (show under the JEE list) |
| `candidates` | JEE Main 2026 candidates (`1538468`) |
| `y25_label` | label of the trend column (`"2025 R6"`) |
| `sources` | `[{label, url}]` official sources, for the "Data" line |
| `comedk` | `{groups, candidates, max_marks, rounds, notes, sources}`: the same for COMEDK (`groups` = 12 course groups, `max_marks` 180, `rounds` `["R1","R2","R3","R4"]`) |

## 2. `POST /rank/estimate` — Rank predictor

Marks → percentile and rank only (no colleges).

Request:

| Field | Type | Rule |
|---|---|---|
| `exam` | `"jee"` · `"comedk"` | default `"jee"` |
| `marks` | integer | JEE −75 … 300; COMEDK 0 … 180 (else 422 `"COMEDK marks 0 se 180 ke beech daalo."`) |
| `level`, `category`, `pwd` | as the shared form | ignored for COMEDK |

Answer, JEE (`exam: "jee"`):

| Field | Meaning |
|---|---|
| `result` | the block for the chosen `level` (see "result block" below) |
| `levels` | 3 rows, `tough`, `normal`, `easy`: `{level, percentile, crl, cat_rank, pwd_rank}` — the same marks on all three paper types |
| `candidates` | 1538468 |
| `notes` | 3 sentences to show under the card |

Answer, COMEDK (`exam: "comedk"`):

| Field | Meaning |
|---|---|
| `rank` | `[best, worst]` across three public analyses |
| `mid` | the middle estimate (median of the three) |
| `percentile` | `[low, high]`, share of candidates behind the student |
| `candidates` | 129000 |
| `summary` | `"110 / 180 marks · COMEDK 2026"` |
| `sources` | the three analyses `{label, url, rank}`, each with its own rank for these marks |
| `notes` | 3 sentences |

**The result block** (used by `estimate`, `percentile`, `predict`):

| Field | Present | Meaning |
|---|---|---|
| `percentile` | always | `[low, high]` (equal when the student typed a percentile or a rank) |
| `crl` | always | `[best, worst]` Common Rank List range; both ends equal for a scorecard rank (`[7500, 7500]`): show one number |
| `from_marks` | always | `true` when worked out from marks |
| `source` | always (new) | `"marks"` · `"percentile"` · `"rank"`: the score that was used |
| `summary` | always | `"180 marks · Normal · General"`, `"97.4 percentile · General"` or `"Rank 7,500 · General"` — the line under the card title |
| `spread` | from marks | `"Tough paper hota to rank lagbhag 9,702, Easy paper hota to lagbhag 18,779."` |
| `cat_rank` | category ≠ GEN | `{label: "OBC-NCL rank", range}` |
| `pwd_rank` | `pwd: true` | `{label: "PwD rank" or "OBC-NCL-PwD rank", range}` |
| `paper` | marks sent together with a percentile or a rank | which paper type the pair fits |
| `check` | the numbers sent disagree | `"Marks aur percentile aapas mein mel nahi kha rahe, ek baar check kar lo."`, `"Marks aur rank …"` or `"Rank aur percentile aapas mein mel nahi kha rahe, ek baar check kar lo."` |
| `delhi_note` | `state: "Delhi"` | Delhi region eligibility sentence |

## 3. `POST /rank/percentile` — no screen any more

> The app's "Percentile se rank" tile was replaced by **Cut off** (§13). This endpoint still answers, because older
> app versions call it, but no current screen uses it: **do not build a page for it**. A student with a percentile types
> it into the College predictor (§4) or Cut off's score box; both show the rank it stands for.

Request `{percentile: 0…100, category, pwd}`.

Answer: `result` (the block above, `percentile` equal to the input), `candidates`, `marks` (3 rows
`{level, marks}`: what that percentile took on each paper type), `notes` (3 sentences).

## 4. `POST /rank/predict` — College predictor, JEE Main

Request: the shared form plus

| Field | Type | Default | Meaning |
|---|---|---|---|
| `segment` | `"all"` · `"NIT"` · `"IIIT"` · `"GFTI"` · `"DELHI"` | `"all"` | the filter chips above the list |
| `page` | 1 or 2 | 1 | the list has at most 50 items, 25 a page |
| `page_size` | 20 or 25 | 25 | 20 = the short list used by the Percentile chart rows (no `near`) |

Answer:

| Field | Meaning |
|---|---|
| `result` | the result block (Rank Card) |
| `counts` | items on each chip's list (each at most 50): `{all, NIT, IIIT, GFTI, DELHI}` |
| `reach` | **every** college-branch in reach for each chip (e.g. `all: 655`): the "655 college-branches in reach" line |
| `segment`, `page`, `pages`, `total` | paging of the chosen list |
| `items` | up to 25 seats (below) |
| `near` | up to 5 near misses with `gap` (page size 25 only) |
| `note` | the estimate sentence |

A seat (`items[]`, `near[]`):

| Field | Meaning |
|---|---|
| `prog`, `inst` | program and institute numbers: send them back to `/rank/college`, `/rank/target/jee`, compare |
| `college` | short name (`"NIT Rourkela"`) |
| `type` | `"NIT"` · `"IIIT"` · `"GFTI"` · `"DELHI"` |
| `branch`, `degree` | full branch name; degree note (`""`, `"5-yr dual"`, …) |
| `close`, `round` | the closing rank that decided the tag and its round (`"R5"`, `"CSAB 2"`, …) |
| `rank_type` | which rank `close` is on: `"CRL"`, `"OBC-NCL rank"`, `"PwD rank"`, … |
| `path` | the seat path used: `"Home state · OBC-NCL · Female-only"` |
| `quota`, `gender`, `seat` | the same path as codes (`"HS"`, `"F"`, `"cat"`): send them back to `/rank/college` |
| `tag` | items only: `safe` · `likely` · `borderline` |
| `gap` | near only, in the kind of score the student gave: `"lagbhag +5 marks aur"`, `"lagbhag +0.42 percentile aur"` or (new) `"rank lagbhag 626 aur upar chahiye"` |
| `y26` | the 2026 JoSAA final closing on this path (trend arrow, against `y25`) |
| `y25` | the 2025 final closing on this path, or `null` |

Order: by demand (most wanted first). The 50 mix up to 20 Borderline, 15 Likely and 15 Safe (`docs/04` §6).

## 5. `POST /rank/college` — JEE college sheet

Opened when the student taps a card. Request: the shared form plus

| Field | Meaning |
|---|---|
| `inst` | institute number (from the card) — unknown → `404 "College nahi mila."` |
| `prog` | the tapped branch; it is always in the sheet even outside the top 10 |
| `quota`, `gender`, `seat` | the path to show (from the card). Omitted → the server picks the student's own path |
| `all` | `true` = every branch of the college (default: the 10 most wanted + the tapped one) |

Answer:

| Field | Meaning |
|---|---|
| `college` | `{id, name, short, type, city, state}` |
| `your_rank` | `{label, range}` — the student's rank on this path's rank type |
| `rounds` | JoSAA `["R1","R2","R3","R4","R5","CSAB 1","CSAB 2"]` or JAC `["R1","R2","R3","R4","Upgrade","Spot"]` |
| `rows` | `{prog, branch, degree, cells[], first_in, y25}` one per branch |
| `cells[]` | per round `{open, close, in, mine, hi, unpublished}`: `in` = the best estimate is inside; `mine`/`hi` = the student's best/worst rank on that round's rank type; `unpublished` = JAC never published this round |
| `first_in` | the first round the student gets in, or `null` |
| `line` | the sentence over the ladder: `"Electrical Engineering: aapki rank R3 se andar aati hai."` |
| `blocked` | not `null` when this path is closed to the student: `"Home state quota sirf Odisha ke students ke liye hai"` (no cell is green then) |
| `total` | branches on this path |
| `path` | `{quota, gender, seat}` actually shown |
| `options` | the switches: `quota[]` `{key,label}`, `gender[]`, `seat[]`, `cat_label` |
| `official`, `official_csab` | official result pages for the "Official" link |
| `y25_label` | `"2025 R6"` (JoSAA) or `null` (JAC) |

## 6. `POST /rank/bitsat` — BITSAT

Request `{score: −130…390, campus: "all"|"Pilani"|"Goa"|"Hyderabad", degree: "all"|"BE"|"MSc"|"BPharm"}`.

Answer:

| Field | Meaning |
|---|---|
| `result` | `{score, max: 390, cleared, total, cleared_all, total_all, best, target}`: `cleared`/`total` follow the filters, `*_all` look at all 50 programs; `best` = hardest program cleared; `target` = the next program above with its `gap` |
| `items` | programs with a tag (Safe / Likely / Borderline) |
| `near` | no tag, at most 20 marks short |
| `rest` | further away |
| each program | `{id, campus, college, program, degree, history[5], cutoff, last, tag, gap}`; `history` = 2022…2026 finals, `cutoff` = 2026, `last` = 2025 |
| `years` | `[2022, 2023, 2024, 2025, 2026]` |
| `notes`, `source` | 3 sentences; the official BITS page |

## 7. `POST /rank/comedk` — COMEDK list

Request:

| Field | Type | Rule |
|---|---|---|
| `marks` | integer 0…180 | send `marks` **or** `rank` |
| `rank` | integer 1…200000 | from the COMEDK rank card |
| `branches` | string[] | course groups from `meta.comedk.groups` |
| `area` | `"all"` · `"blr"` · `"other"` | Bengaluru / outside Bengaluru |
| `page` | 1 or 2 | |

Neither → `422 "Marks ya rank mein se koi ek daalo."`

Answer: `result` `{rank, mid, from_marks, candidates, in_reach, total, summary, spread?, check?}`, `counts`, `reach`,
`area`, `page`, `pages`, `total`, `items` (tagged), `near` (with `gap`), `rounds`, `notes`.

An item: `{id: "E095|CY", code, college, city, blr, course, cc, group, close, round, rounds[4], y25, seats, fee, tag?, gap?}`.
`seats` = GM seats, `fee` = 2026 yearly total in rupees, `rounds` = closing rank per round (`null` = no allotment).

## 8. `POST /rank/comedk/college` — COMEDK college sheet

Request `{marks | rank, branches, code, course?, all?}`. Unknown `code` → 404.

Answer: `college` `{code, name, short, city, blr}`, `your_rank` `{label: "COMEDK rank", range}`, `rounds`, `rows`
(`{cc, course, group, cells[], close, round, first_in, y25, seats, fee, tag}`), `total`, `line`, `y25_label`, `official`.

## 9. `GET /rank/colleges`

Search lists: `jee` `[{inst, short, name, type, state, city}]` (115), `comedk` `[{code, short, name, city}]` (148),
`bitsat` `[{campus, name, programs}]` (3). Fetch once per visit.

## 10. Target marks

**`POST /rank/target/jee`** `{inst, category, female, pwd, state}` → `{exam, college, rounds, rows, official, notes}`.
A row is one branch on the student's easiest open path:
`{prog, branch, degree, group, path, quota, gender, rank_type, seats, y25, cells[], final}`;
a cell `{label, close, crl, pct, marks: {tough, normal, easy}}` or `{label, close: null, unpublished}`;
`final` = the last round that had a closing `{label, close, crl, pct, marks}`. Marks are the marks needed on each paper
type (the app shows Normal big, Tough/Easy small).

**`POST /rank/target/comedk`** `{code}` → rows `{cc, course, group, fee, seats, y25, cells[], final}` with
`marks: [low, high]` and `mid` per cell.

**`GET /rank/target/bitsat`** → `{years, max, source, notes, rows}`; a row `{id, campus, college, program, degree, cutoff, history, safe}` (`safe` = cutoff + 10).

## 11. College compare

**`POST /rank/compare`** — branch vs branch, 1–3 saved college-branches:

```json
{"items": [
  {"exam": "jee", "id": "jee-230", "prog": 230, "quota": "OS", "gender": "N", "path": "Other state · Open"},
  {"exam": "comedk", "id": "E095|CY"},
  {"exam": "bitsat", "id": "Pilani-cs"}
]}
```

A JEE item carries `prog`, `quota`, `gender` and the card's `path` sentence (that is how the server finds the exact seat).
Answer `{items, notes}`; an item `{exam, id, title, name, place, sub, path, rank_label, rounds[{label, close, crl?}],
final, prev, seats, seats_label, fee, fee_note, higher_is_harder}` or `{exam, id, missing: true}` when the seat no longer exists.

**`POST /rank/compare/colleges`** — whole colleges, 1–3: `{items: [{exam, id}], category, female, pwd, state}` where `id`
is the JEE institute number as a string, the COMEDK code or the BITS campus. Answer items:
`{exam, id, title, name, place, kind, branches, seats, seats_label, fee: [min,max]|null, fee_note, easiest, toughest, cs, cs_count}`;
`easiest`/`toughest`/`cs` = `{branch, close, label, rank_label, marks, cs}`.

## 12. PDFs

White A4 PDFs drawn by the server (25–70 KB, about 50 ms each). The answer has
`Content-Disposition: attachment; filename="JEELIVE-…pdf"`: use that name.

| Path | Body |
|---|---|
| `/rank/pdf/jee` | the shared form + `segment` |
| `/rank/pdf/comedk` | `{marks|rank, branches, area}` |
| `/rank/pdf/bitsat` | `{score, campus, degree}` |
| `/rank/pdf/target/jee` | `{inst, category, female, pwd, state}` |
| `/rank/pdf/target/comedk` | `{code}` |
| `/rank/pdf/target/bitsat` | `{campus}` |
| `/rank/pdf/saved` | `{items: CompareItem[1..50], tags: (tag or null)[], pick: [up to 3 indexes]}` |
| `/rank/pdf/cutoff` — NEW | **exactly the body of `POST /rank/cutoff`** that drew the list on screen (§13.2), score included |

Samples with their request bodies: `RANK/sample_pdfs/`. The JEE list PDF is named after the score that was used:
`JEELIVE-JEE-colleges-180-marks.pdf`, `…-97.4-percentile.pdf` or (new) `…-rank-7500.pdf`.

The Cut off PDF is named `JEELIVE-cutoff-{exam}-{by}-{score}.pdf`, where `{score}` is `rank-7500`, `pct-99.2`,
`200-marks`, or `all` when no score was sent (`JEELIVE-cutoff-jee-college-200-marks.pdf`). It carries the heading, the
student's line and the three counts (with a score), every row with every round, the last-year arrow, the near misses
and the notes. A request the list would refuse is refused the same way (the same 404 / 422 sentence, as JSON).

---

## 13. Cut off — NEW

Two endpoints, both public. What the tool is, its rules per exam, the screen word by word and its acceptance list are
in `docs/11_CUT_OFF_NEW.md`; this section is the field reference. Real answers: `RANK/api_examples/23_…` to `34_…`.

### 13.1 `GET /rank/cutoff/options`

The pickers of the three exams in one answer. About 62 KB (11 KB compressed). Fetch once per visit; it changes only
when the app server is redeployed (the connector keeps it 10 minutes).

```json
{ "limit": 100,
  "jee":    { "name": "JEE Main", "score": ["marks", "percentile", "rank"], "marks": [-75, 300],  "levels": true,  "profile": true,
              "colleges": [ …115 ], "branches": [ …20 ] },
  "comedk": { "name": "COMEDK",   "score": ["marks", "rank"],               "marks": [0, 180],    "levels": false, "profile": false,
              "colleges": [ …148 ], "branches": [ …11 ] },
  "bitsat": { "name": "BITSAT",   "score": ["marks"],                       "marks": [-130, 390], "levels": false, "profile": false,
              "colleges": [ …3 ],   "branches": [ …19 ] } }
```

| Field | Meaning |
|---|---|
| `limit` | the most rows a branch list returns (100) |
| `score` | the kinds of score this exam accepts, in the order of the chips |
| `marks` | `[lowest, highest]` marks of the exam |
| `levels` | `true` = the Tough / Normal / Easy question applies (JEE Main marks) |
| `profile` | `true` = category, Female, PwD and home state apply (JEE Main only) |
| `colleges[]`, `branches[]` | the two pickers; one option = `{key, title, sub, find?, kind?}` |

One option:

| Field | Meaning |
|---|---|
| `key` | send it back to `POST /rank/cutoff` **exactly as received** |
| `title` | the bold line (`"NIT Trichy"`, `"Computer Science"`, `"BITS Pilani"`, `"B.E. Computer Science"`) |
| `sub` | the small line (`"NIT · Tiruchirappalli, Tamil Nadu"`, `"125 college-branch · 93 colleges"`, `"18 programs"`, `"Pilani · Goa · Hyderabad"`) |
| `find` | extra words for the search only, never shown (a college's full name; a branch's short forms and course names: `"CSE CS …"`) |
| `kind` | colleges only: `"NIT"` · `"IIIT"` · `"GFTI"` · `"DELHI"` · `"COMEDK"` · `"BITS"` (the type chip) |

What a `key` is:

| Exam | College | Branch |
|---|---|---|
| JEE Main | the institute number as text (`"25"` = NIT Trichy; the same number as `inst` elsewhere) | the branch group name (`"Computer Science"`; the same 20 names as `meta.branches`) |
| COMEDK | the college code (`"E095"`) | the course group name (`"Computer Science"`; 11 groups that have GM seats) |
| BITSAT | the campus (`"Pilani"`, `"Goa"`, `"Hyderabad"`) | the program key (`"cs"`, `"mnc"`, …) |

Order as served: JEE colleges NITs first, then by short name; COMEDK colleges most wanted first; BITSAT programs
highest cut-off first. Keep the order.

### 13.2 `POST /rank/cutoff` — request

| Field | Type | Default | Rule |
|---|---|---|---|
| `exam` | `"jee"` · `"comedk"` · `"bitsat"` | required | |
| `by` | `"college"` · `"branch"` | required | BITSAT: college = campus, branch = program |
| `key` | string, 1–60 characters | required | from §13.1, exact. Unknown → a 404 sentence (§13.4) |
| `marks` | integer | none | optional. JEE −75 … 300 · COMEDK 0 … 180 · BITSAT −130 … 390 (the score out of 390) |
| `percentile` | number 0 … 100 | none | optional. JEE Main only |
| `rank` | integer | none | optional. JEE 1 … 20,00,000 (scorecard CRL) · COMEDK 1 … 2,00,000 (rank card) |
| `level` | `"tough"` · `"normal"` · `"easy"` | `"normal"` | JEE Main only: the paper type for a marks score, and for the "≈ marks" on every row |
| `category`, `female`, `pwd`, `state` | as the shared form (§0) | `"GEN"`, `false`, `false`, `null` | JEE Main only; leave them out for COMEDK and BITSAT |

- **No score** → the full table: every row open to the student.
- **A score** → only the rows the student can reach, each with a tag, plus up to 3 nearest misses.
- JEE Main with several scores: rank, then percentile, then marks (§0). COMEDK with both: the rank.

### 13.3 `POST /rank/cutoff` — answer

| Field | Meaning |
|---|---|
| `exam`, `by`, `key` | the request, echoed. Show an answer only while these equal the student's current choice |
| `title`, `name`, `sub` | the heading: short name, full name, and the line under it |
| `kind` | the type chip of a college (`"NIT"`, `"IIIT"`, `"GFTI"`, `"DELHI"`, `"COMEDK"`, `"BITS"`); `null` for a branch list |
| `metric` | `"rank"`: a smaller number is harder · `"score"` (BITSAT): a bigger number is harder |
| `columns` | the labels of the round boxes: JoSAA `["R1","R2","R3","R4","R5","CSAB 1","CSAB 2"]` · JAC Delhi `["R1","R2","R3","R4"]` · COMEDK `["R1","R2","R3","R4"]` · BITSAT `["2022","2023","2024","2025","2026"]` (years, not rounds) |
| `prev_label` | label of the last-year box (`"2025 R6"`, `"2025 final"`) or `null` |
| `rows` | the cards, most wanted first. A college: all of them. A branch: the first `limit` |
| `total` | rows open to this student before the score filter |
| `eligible` | rows that passed the score filter, counted over the whole list (can be more than `rows.length` on a branch); `null` without a score |
| `limit` | `100` for a branch list, `null` for a college |
| `you` | `null` without a score; else the student's own line (below) |
| `near` | up to 3 nearest misses, nearest first, each a row with `gap` and no tag; `[]` without a score |
| `notes` | sentences to show under the list, in order |
| `official` | the official results page for the "Official" link |

A row (`rows[]`, `near[]`):

| Field | Meaning |
|---|---|
| `id` | stable key of the row (`"jee-230"`, `"E095|CY"`, `"Pilani-cs"`) |
| `college`, `place` | short college name; city and state (BITSAT: the campus) |
| `kind` | the college's type chip |
| `branch` | full branch / course / program name |
| `path` | the seat path used: `"Other state · Open"`, `"Home state · OBC-NCL"`, `"GM · All India"`, `"Sab categories, ek cutoff"` |
| `rank_type` | what the closing numbers are: `"CRL"`, `"OBC-NCL rank"`, `"COMEDK rank"`, `"score / 390"` |
| `cells[]` | one per column, in the order of `columns` (below) |
| `final` | `{label, close}`: without a score the last JoSAA / JAC round's closing (COMEDK: the largest over R1–R4; BITSAT: 2026); with a score the closing that decided the tag (it can be a CSAB round; `rank_type` is then `"CRL"`) |
| `prev` | `{label, close}` last year's final closing on the same path (`close` can be `null`), or `null` (JAC Delhi, BITSAT) |
| `seats` | JEE: JoSAA seat matrix for the program (`null` for JAC) · COMEDK: GM seats · BITSAT `null` |
| `fee` | COMEDK: 2026 yearly total in rupees; else `null` |
| `need` | `{marks, pct?, level?}`: marks needed to reach `final` (JEE: on the paper type `level`, with the percentile `pct`; COMEDK: out of 180; BITSAT: the cut-off itself) |
| `tag` | `"safe"` · `"likely"` · `"borderline"` with a score, else `null` |
| `gap` | near misses only: `"lagbhag +3 marks aur"`, `"lagbhag +0.42 percentile aur"`, `"rank lagbhag 323 aur upar chahiye"`; COMEDK and BITSAT have their own (`"+28 marks aur"`) |
| `trend` — NEW | `{dir, prev, label}` or `null`: this year against last year (below) |
| `save` — NEW | the row as one saved item for the shortlist / College compare (below). Always present |

`trend` (the small arrow on a card; `docs/11` §13.1):

| Field | Meaning |
|---|---|
| `dir` | `"tough"` = harder than last year (up arrow, red) · `"easy"` = easier (down arrow, green) · `"same"` = within 3 % (no arrow, soft text) |
| `prev` | last year's number that was compared |
| `label` | the sentence to print: `"is saal aur mushkil"` · `"is saal thoda aasaan"` · `"≈ pichhle saal jaisa"` |

What is compared, always like for like: JEE Main = the **last JoSAA round of 2026 against 2025's final round on the
same seat path** (never a CSAB closing, even when a CSAB round decided the tag) · COMEDK = 2026 final against 2025
final · BITSAT = the 2026 cut-off score against 2025's (a bigger score is tougher). `null` when either number is
missing, and for every JAC Delhi row (no last-year data). Never compute it in the browser.

`save` (hand it to the shortlist unchanged; `docs/11` §13.2):

| Field | Meaning |
|---|---|
| `id` | the shortlist key: `"jee-262"` · `"comedk-E015|CS"` · `"bitsat-Pilani-cs"` (the same keys the College predictor saves under, so a row saved in either place is one item) |
| `exam` | `"jee"` · `"comedk"` · `"bitsat"` |
| `title`, `sub`, `line` | what the saved card prints: college, branch, and one ready line (`"Closing 8,754 CRL · R5 · Other state · Open"`) |
| `tag` | the row's tag at the moment it was saved, or `null` |
| `jee` | JEE Main only: `{prog, quota, gender, path}`, the seat path to compare on |

To compare a saved item send `{exam, id, ...jee}` for JEE Main, and `{exam, id without its "comedk-" / "bitsat-" prefix}`
for the other two, to `POST /rank/compare` (§11). The app's `toCompareItem` in `shortlist.ts` does exactly this.

A cell (`cells[]`):

| Field | Meaning |
|---|---|
| `label` | the column's label |
| `close` | the closing rank (BITSAT: the cut-off score) of that round / year; `null` = no allotment, or not published |
| `state` | only with a score: `"in"` = the student's whole range is inside (green) · `"edge"` = only part of it, **or any reachable CSAB round** (amber) · `"out"`. BITSAT: only the 2026 cell has it |
| `na` | `true` = this college has no such round (a JAC Delhi row inside a JoSAA-column branch list). Leave the box out |
| `crl` | `true` = this CSAB closing is on CRL although the row's `rank_type` is a category or PwD rank. Print "CSAB 1 · CRL" |

`you` (with a score):

| Field | Meaning |
|---|---|
| `source` | `"marks"` · `"percentile"` · `"rank"`: the score that was used |
| `summary` | the short form (`"200 marks · Normal · General"`, `"280 / 390"`) |
| `line` | the sentence to show in bold: `"200 marks (Normal paper) ≈ 99.48 – 99.52 percentile ≈ rank 7,417 – 7,917 (CRL)"` |
| `percentile` | `[low, high]` or `null` (BITSAT; COMEDK from a rank) |
| `rank` | `{label, range}` (`"CRL"`, `"COMEDK rank"`) or `null` (BITSAT) |
| `cat_rank`, `pwd_rank` | `{label, range}` or `null` (JEE Main only) |
| `check` | a sentence to show in the warning colour, or `null` |
| `counts` | `{safe, likely, borderline}` over the whole list; they add up to `eligible` |

### 13.4 What the server refuses

| Request | Answer |
|---|---|
| unknown college `key` (JEE Main, COMEDK) | `404 "College nahi mila."` |
| unknown branch `key` (JEE Main, COMEDK) | `404 "Branch nahi mili."` |
| unknown BITSAT campus | `404 "Campus nahi mila."` |
| unknown BITSAT program | `404 "Program nahi mila."` |
| JEE Main `marks` outside −75 … 300 | `422 "JEE Main marks −75 se 300 ke beech daalo."` |
| COMEDK with a `percentile` | `422 "COMEDK mein percentile nahi chalta. Marks ya rank daalo."` |
| COMEDK `marks` outside 0 … 180 | `422 "COMEDK marks 0 se 180 ke beech daalo."` |
| COMEDK `rank` above 2,00,000 | `422 "COMEDK rank 1 se 2,00,000 ke beech daalo."` |
| BITSAT with a `percentile` or a `rank` | `422 "BITSAT mein sirf score chalta hai (390 mein se)."` |
| another `exam` or `by`, an empty `key`, an unknown `state`, a number outside the field's own limit | `422` with a **list** (validate in the form so the student never sees it) |

All of them, as answered by the server: `RANK/api_examples/34_cutoff_what_the_server_refuses.json`.
