# 03 · Rank API reference

Every Rank endpoint of the app server, field by field. All paths are relative to the API root
(`https://jeelive-mobile.emergent.host/api`, or the website's own `/api` once the connector is mounted).

- **Public.** No account, no key, no cookie.
- **JSON in, JSON out**, except the seven PDF routes (JSON in, `application/pdf` out).
- **Numbers are server-made.** Show them as they arrive. Never recompute them in the browser (`docs/04` explains them only so you understand them).
- **Sentences are server-made.** Every `note`, `notes`, `summary`, `spread`, `check`, `gap`, `line`, `blocked` and error `detail` is ready to show.
- A real request and answer for every endpoint sits in `RANK/api_examples/` (frozen samples, see the warning in §0).

There are 14 JSON endpoints and 7 PDF endpoints:

| # | Method · path | Tool | Section |
|---|---|---|---|
| 1 | `GET /rank/meta` | every tool (lists, chart, notes, sources) | §1 |
| 2 | `POST /rank/estimate` | Rank predictor | §2 |
| 3 | `POST /rank/percentile` | Percentile se rank | §3 |
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

## 0. Conventions

**The samples are not data.** `RANK/api_examples/*.json` were captured once, when this pack was built. They show the
shape of every answer. Do not load them into the website, do not copy a number from them into a page. The app server's
data is renewed when new cut-offs are published; the website must always show what the server says today.

**Shared form (JEE Main).** `predict`, `college` and `pdf/jee` take the same student form:

| Field | Type | Default | Rule |
|---|---|---|---|
| `marks` | integer | none | −75 … 300. Send `marks` **or** `percentile` |
| `percentile` | number | none | 0 … 100. When both are sent, the percentile is used and `marks` only checks it |
| `level` | `"tough"` · `"normal"` · `"easy"` | `"normal"` | how hard the student's shift was (marks only) |
| `category` | `"GEN"` · `"EWS"` · `"OBC-NCL"` · `"SC"` · `"ST"` | `"GEN"` | |
| `female` | boolean | `false` | opens Female-only seats |
| `pwd` | boolean | `false` | opens PwD seats |
| `state` | string or `null` | `null` | must be one of `meta.states` exactly; decides Home state / Other state / Delhi seats |
| `branches` | string[] | `[]` | names from `meta.branches`; unknown names are dropped silently; `[]` = all branches |

Neither `marks` nor `percentile` → `422 {"detail": "Marks ya percentile mein se koi ek daalo."}`.

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
| `percentile` | always | `[low, high]` (equal when the student typed a percentile) |
| `crl` | always | `[best, worst]` Common Rank List range |
| `from_marks` | always | `true` when worked out from marks |
| `summary` | always | `"180 marks · Normal · General"` — the line under the card title |
| `spread` | from marks | `"Tough paper hota to rank lagbhag 9,702, Easy paper hota to lagbhag 18,779."` |
| `cat_rank` | category ≠ GEN | `{label: "OBC-NCL rank", range}` |
| `pwd_rank` | `pwd: true` | `{label: "PwD rank" or "OBC-NCL-PwD rank", range}` |
| `paper` | percentile **and** marks sent | which paper type the pair fits |
| `check` | percentile and marks disagree | a sentence asking the student to check |
| `delhi_note` | `state: "Delhi"` | Delhi region eligibility sentence |

## 3. `POST /rank/percentile` — Percentile se rank

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
| `gap` | near only: `"lagbhag +5 marks aur"` or `"lagbhag +0.42 percentile aur"` |
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

Samples with their request bodies: `RANK/sample_pdfs/`.
