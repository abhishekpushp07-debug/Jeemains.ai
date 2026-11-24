# 11 · Cut off  —  NEW

> **New in this pack.** Cut off is a new Rank tool. In the app it took the place of the "Percentile se rank" tile
> (second tile of the grid). It has two new endpoints, `GET /rank/cutoff/options` and `POST /rank/cutoff`, and no data of
> its own: it reads the same in-memory data as every other Rank tool, so its numbers always agree with them.
>
> **Where it runs today.** On the development server now. On the live server after the app project's next publish
> (`MANIFEST.json` → `cut_off_on_live` says which it was when this pack was built; `CONNECT/connect_check.py` tells you
> today: it prints `WAIT` for the Cut off checks on a server that does not have them yet).

## 1. What it is

The student picks **one thing**, a college or a branch, and reads **every round's 2026 cut-off**:

| The student picks | They see |
|---|---|
| a **college** (BITSAT: a campus) | every branch of that college, each with every round's closing rank |
| a **branch** (BITSAT: a program) | the **100 most wanted** college-branches of that branch, each with every round's closing rank |

Then, if they want, they type their **marks, percentile or rank** (optional). The list shrinks to the options they can
reach, each tagged **Safe**, **Likely** or **Borderline**, and the rounds they are inside turn green.

Three exams: **JEE Main** (JoSAA, CSAB and JAC Delhi), **COMEDK** (General Merit seats) and **BITSAT**.

What makes it different from the College predictor: the predictor starts from a score and suggests 50 seats; Cut off
starts from a **college or branch the student already has in mind** and shows the whole table, score or no score.

## 2. The journey (app screens in `RANK/screenshots/NEW_cutoff_*.jpg`)

| Step | The student | Screen |
|---|---|---|
| 1 | taps the **CUT OFF** tile; the teal form "Kiska cut off dekhna hai?" opens | `NEW_cutoff_01` |
| 2 | chooses the exam (**JEE Main · BITSAT · COMEDK**) and **College se** or **Branch se** | `NEW_cutoff_01`, `13` |
| 3 | taps the chooser; a search sheet opens; types a few letters; picks | `NEW_cutoff_02`, `08` |
| 4 | reads the result: a heading, a count line, the optional score box, then one card per row with a box per round | `NEW_cutoff_03`, `04`, `09`, `10` |
| 5 | (JEE Main) changes category, Female, PwD or home state with the chips: the list reloads on the new seat path | `NEW_cutoff_11` |
| 6 | types a score and taps **Eligible dikhao**: only reachable rows stay, with tags and green / amber boxes | `NEW_cutoff_05`, `06`, `12`, `14`, `15`, `16` |
| 7 | sees the nearest misses under the list ("BAS THODA SA DOOR") with what it would take | `NEW_cutoff_07`, `18` |
| 8 | taps **Score badlo** to change the score, or **Sab cutoffs dikhao** to go back to the full table | `NEW_cutoff_05` |

Nothing needs sign-in.

## 3. The API in two calls

Field-by-field tables are in `docs/03_RANK_API_REFERENCE.md` §13. The short version:

```ts
const app = createJeeliveApp();

// once per visit: the pickers of all three exams (about 62 KB, 11 KB compressed)
const options = await app.rank.cutoffOptions();
options.jee.colleges     // 115  [{ key: "25", title: "NIT Trichy", sub: "NIT · Tiruchirappalli, Tamil Nadu", find: "National Institute of …", kind: "NIT" }, …]
options.jee.branches     // 20   [{ key: "Computer Science", title: "Computer Science", sub: "125 college-branch · 93 colleges", find: "CSE CS …" }, …]

// every time the choice, the profile chips or the applied score change
const out = await app.rank.cutoff({ exam: "jee", by: "college", key: "25",              // key exactly as the picker gave it
                                    category: "GEN", female: false, pwd: false, state: null,   // JEE Main only
                                    marks: 200, level: "normal" });                      // optional score
out.rows       // the cards
out.you        // null without a score; else the student's rank line and the three counts
out.near       // up to 3 nearest misses (only with a score)
```

Real answers: `RANK/api_examples/23_…` to `34_…`.

### What the server decides (never redo this in the browser)

- which branches / colleges are in the list and in what order (most wanted first);
- which seat path a JEE row uses (the easiest path open to the student's category, gender, PwD and home state);
- the tag of every row, the colour state of every round box, the counts, the near misses and their gap sentence;
- every sentence: `sub`, `you.line`, `you.check`, `gap`, `notes`, and every error `detail`.

### What the page decides

- the search inside the picker sheet (§6.2), showing 25 cards at a time (§6.6), and remembering the form (§7).

## 4. The rules, exam by exam

The tag rule is the College predictor's own (`docs/04` §6, §9, §10). Cut off calls the same functions on the server.

### 4.1 JEE Main

- **Rounds (the columns).** JoSAA colleges: `R1 R2 R3 R4 R5 CSAB 1 CSAB 2`. JAC Delhi colleges (DTU, NSUT, IIIT-Delhi,
  IGDTUW): `R1 R2 R3 R4` only, because JAC never published its Upgrade and Spot ranks. A branch list mixes both kinds of
  college: its columns are the seven JoSAA ones, and a JAC row's `R5`, `CSAB 1`, `CSAB 2` cells carry `na: true`
  (**leave those boxes out**, do not draw a dash).
- **The seat path.** Category, Female, PwD and home state decide which seats a student may take (`docs/04` §5). For each
  branch the server shows the **easiest path open to that student** and names it in `path`
  ("Other state · Open", "Home state · OBC-NCL", "Delhi region · Open · Female-only" …). That is why the list reloads
  when a chip changes, and why `total` can be a little smaller than the picker's count ("123" against "125
  college-branch": two programs have no seat open to that profile).
- **The rank type.** `rank_type` says which rank the closing ranks are on: `CRL`, `OBC-NCL rank`, `SC-PwD rank` … JoSAA
  rounds close on the seat's own rank type; **CSAB rounds always close on CRL**, so on a category or PwD seat the CSAB
  cells carry `crl: true` and the app prints "CSAB 1 · CRL" in the box.
- **Without a score.** Every branch open to the profile, most wanted first. `final` = the last JoSAA / JAC round's
  closing (the largest), exactly as Target marks shows it. `need.marks` = marks needed for it on the chosen paper type.
- **With a score.** Only rows with a tag stay:

  | Tag | Rule (closing rank `c`; the student's range `best ≤ mid ≤ worst` on that rank type) |
  |---|---|
  | Safe | `c ≥ worst` and `c ≥ 1.15 × mid` |
  | Likely | `c ≥ worst` |
  | Borderline | `best ≤ c < worst`, **or the seat is reachable only through a CSAB round** |
  | (not listed) | `c < best` everywhere |

  `final` is then the closing that decided the tag; it can be a CSAB round (`rank_type` becomes `CRL`).
- **The round boxes.** Each cell gets `state`: `in` (green: the student's whole range is inside that round), `edge`
  (amber: only part of the range is inside), `out`. **A CSAB cell is never `in`**: CSAB only fills left-over seats, so
  it is `edge` at best. A row can be Safe with an amber CSAB box beside five green JoSAA boxes.
- **Which score counts.** Send any of `marks`, `percentile`, `rank`. With more than one, the most exact wins: **rank,
  then percentile, then marks** (`you.source` says which was used). Marks also need the paper type `level`.
  A scorecard rank is exact: the card shows it as one number; a small band behind it only decides Borderline.
- **Near misses.** Up to 3 branches the student just missed, nearest first, each with `gap`:
  "lagbhag +3 marks aur", "lagbhag +0.42 percentile aur" or "rank lagbhag 323 aur upar chahiye" (it follows the kind of
  score the student typed).

### 4.2 COMEDK

- General Merit (All India) seats only. Category, gender and home state do not apply: **do not show those chips**.
- Columns `R1 R2 R3 R4`. A `null` closing = no allotment on that seat in that round (the app prints "—").
- Score: `marks` (0–180) **or** `rank` (1–2,00,000). A percentile is refused with a sentence. With both, the rank wins.
- From marks the rank is a range of three public analyses (`docs/04` §9), and `you.check` carries the honest line
  "COMEDK marks-rank table publish nahi karta, isliye marks se rank ek andaaza hai." Show it.
- Each row also has `fee` (2026 yearly total, rupees) and `seats` (GM seats); `prev` = the 2025 final closing.
- Tags: the same three rules, on the seat's largest closing over the four rounds.

### 4.3 BITSAT (read this one twice)

- **BITS publishes no round-wise cut-offs.** There are no rounds to show. The columns are the **five years**
  `2022 2023 2024 2025 2026` of final cut-off **scores**, and only the newest year is "the" cut-off. The first note says
  so in the student's language; the form says so before the student picks anything. Never label these boxes R1, R2 …
- `metric` is `"score"`: here a **bigger number is harder** (for ranks a smaller number is harder).
- No category, gender, home state, percentile or rank: one cut-off for everyone, compared with the student's score out
  of 390. `you.rank` and `you.percentile` are `null`; `you.line` explains why.
- "College" means campus (Pilani, Goa, Hyderabad); "branch" means program (19 programs, on 1 to 3 campuses each).
- Tags with `d = score − 2026 cut-off`: `d ≥ 10` Safe · `d ≥ 0` Likely · `−5 ≤ d < 0` Borderline.
- Only the **2026 box** carries `state` (green for Safe / Likely, amber for Borderline). Older years stay plain.
- No `seats`, no `fee`, no `prev` (the previous year is already one of the five boxes).

## 5. Honest limits to keep on the page

| Limit | Where the student reads it |
|---|---|
| These are 2026 cut-offs; next year's will differ | last JEE note ("2026 ke data par estimate. Asli cutoff har saal badalta hai.") |
| A branch list shows the top 100, not all | the count line: "Top 100 of 123 college-branch · sabse zyada demand wale pehle" |
| CSAB-only is never sure | amber box + the note "CSAB 1 / CSAB 2 sirf bachi hui seats ke round hain …" |
| JAC Delhi has four rounds only | the JAC note; three boxes fewer on those cards |
| COMEDK marks → rank is an estimate | `you.check` |
| BITSAT has no rounds | the form's line, the first note, year labels on the boxes |
| IITs are not here | they admit through JEE Advanced (`docs/05` §3) |

## 6. The screen

Reference code: `RANK/code/app_reference_ui/src_rank/Cutoff.tsx` (the form and the data flow) and `CutoffList.tsx`
(the answer). The website may use a wider layout, but keeps the words, the order of information and the colours.

### 6.1 The form (`NEW_cutoff_01`, `11`, `13`)

Top to bottom:

1. Exam switch **JEE Main · BITSAT · COMEDK**. Each exam keeps its own choice and its own score.
2. The teal form panel, eyebrow `CUT OFF`, title **"Kiska cut off dekhna hai?"**.
3. Switch **College se · Branch se** (BITSAT: **Campus se · Program se**).
4. The chooser: a full-width field showing the chosen name, or the prompt (table below) when empty.
5. JEE Main only: category chips **General · EWS · OBC-NCL · SC · ST** (one always chosen; **General at the start**),
   then **Female**, **PwD** and a **Home state** chip that opens the state sheet (`meta.states`, plus "No home state").
6. One small line about the exam (table below).

| Exam | By | Tab | Prompt in the chooser / sheet title | Search placeholder | Nothing found |
|---|---|---|---|---|---|
| JEE, COMEDK | college | College se | College chuno | College ka naam ya shehar likho | Koi college nahi mila. Naam thoda chhota likh kar dekho. |
| JEE, COMEDK | branch | Branch se | Branch chuno | Branch likho, jaise CSE ya Mechanical | Koi branch nahi mili. Naam thoda chhota likh kar dekho. |
| BITSAT | college | Campus se | Campus chuno | Pilani, Goa ya Hyderabad | Koi campus nahi mila. |
| BITSAT | branch | Program se | Program chuno | Program likho, jaise Computer Science | Koi program nahi mila. Naam thoda chhota likh kar dekho. |

| Exam | The small line under the chips |
|---|---|
| JEE Main | Category, gender aur home state se seat ka raasta badalta hai, isliye cutoff bhi. Home state se NIT ki Home-state seat aur JAC Delhi ki Delhi seat khulti hai. |
| COMEDK | Sirf GM (All India) seats. COMEDK mein category se cutoff nahi badalta. |
| BITSAT | BITS round-wise cutoff publish nahi karta, isliye 2022 se 2026 tak ke final cutoff score dikhenge. Category se cutoff nahi badalta. |

Before anything is picked, under the form: "College chuno: uski har branch ka har round ka cut off dikhega." or
"Branch chuno: us branch ke top 100 college, har round ke cut off ke saath dikhenge." followed by " Phir apna score
daal kar sirf wahi dekh sakte ho jahan aap eligible ho." (BITSAT uses "Campus chuno" / "Program chuno".)

### 6.2 The picker sheet (`NEW_cutoff_02`, `08`)

A bottom sheet (a dialog on a wide screen): title, a search field, rows of `title` (bold) over `sub` (muted).

- Filter in the browser, no request per key press: split the typed text into words; a row matches when **every word**
  is found, ignoring case, in `title + " " + sub + " " + find`. Show the first 60 matches.
- `find` is why "cse", "ece", "mnc", "cyber" or a college's full name work. Do not show `find`.
- A tap picks the row, closes the sheet and loads the result. Send `key` back exactly as received.

### 6.3 The result heading and the score box (`NEW_cutoff_03`, `09`, `13`)

A panel with the title (`title`), a type chip (NIT / IIIT / GFTI / Delhi / COMEDK / BITSAT, from `kind`; none on a
branch list), `sub`, a bold **count line**, then the score box.

| Situation | Count line (`{what}` from the small table below) |
|---|---|
| no score, 100 rows or fewer | `{total} {what} · har round ki closing rank` (BITSAT: `{total} {what} · 5 saal ke cutoff score`) |
| no score, a branch with more than 100 | `Top 100 of {total} {what} · sabse zyada demand wale pehle` |
| with a score | `{eligible} / {total} {what} eligible` and, when `rows.length < eligible`, ` · top {rows.length} dikh rahe` |

| `{what}` | college list | branch list |
|---|---|---|
| JEE Main | branches | college-branch |
| COMEDK | courses | college-course |
| BITSAT | programs | campus |

The score box (no score applied yet):

- **"Sirf wahi dekhna hai jahan aap eligible ho?"**
- "Apna score daalo (optional). Sirf Safe, Likely aur Borderline options bachenge."
- Kind chips from `options[exam].score`: JEE **Marks · Percentile · Rank**, COMEDK **Marks · Rank**, BITSAT none (one
  kind only). Changing the kind empties the field.
- One number field. Labels, placeholders, limits and the sentence for a wrong number: `SCORE` in
  `CONNECT/frontend_web/rankProfile.ts`.
- JEE Main with Marks only: "Aapki shift ka paper kaisa tha?" and chips **Tough · Normal · Easy** (Normal at the start).
- Main button **Eligible dikhao**. Empty field → "Pehle apna score daalo." A wrong number → its sentence
  (`NEW_cutoff_17`); nothing is sent.

### 6.4 "Aapka score" (a score is applied) (`NEW_cutoff_05`, `12`, `14`)

The same box now shows:

- the eyebrow `AAPKA SCORE`, then `you.line` in bold, e.g.
  "200 marks (Normal paper) ≈ 99.48 – 99.52 percentile ≈ rank 7,417 – 7,917 (CRL)";
- `you.cat_rank` and `you.pwd_rank` when present ("OBC-NCL rank: 10,506 – 10,718");
- three chips with the counts: **Safe 5 · Likely 1 · Borderline 0** (`you.counts`, the whole list, not just the page);
- the key: "Hara box = us round mein aap andar. Peela = kinare par, pakka nahi."
  (BITSAT: "Hara box = 2026 ka cutoff aap clear karte ho. Peela = kinare par, pakka nahi.");
- `you.check` in the warning colour when present;
- two buttons: **Score badlo** (the score box comes back with the number in it) and **Sab cutoffs dikhao** (the score
  is taken off; the full table returns).

### 6.5 A card (`NEW_cutoff_04`, `06`, `16`)

One card per row, numbered 1, 2, 3 … with a 4-pixel edge on the left in the tag's colour (plain without a tag).

| Part | College list | Branch list |
|---|---|---|
| Title (bold) | `branch` | `college` |
| Second line | — | `branch` |
| Small line | `path` | `place · path` |
| Chip on the right | the tag, when there is one | the same |

Then the **round boxes**, a small label over the number:

- one box per cell, **skipping cells with `na`**; then one more dashed box for last year (`prev.label`, `prev.close`)
  when `prev` is not null;
- four boxes a line (five when the row has five or fewer in all, as BITSAT's years);
- number in Indian grouping (`fmt`), "—" when `close` is null;
- label + " · CRL" when the cell has `crl` and a closing;
- colours: `in` → green box (`#0E3A2D` fill, `#6EE7B7` line and number); `edge` → amber (`#33270C`, `#FCD34D`);
  `out` and last year → soft text; no state → normal text.

Then one soft line:

- ranks: `Closing {final.label}: {final.close} {rank_type} · ≈ {need.marks}+ marks ({Tough|Normal|Easy} paper) · {seats} seats · ₹{fee} / saal`
  (COMEDK: `≈ {need.marks}+ marks / 180`; leave out seats and fee when null);
- BITSAT: `{final.label} cutoff: {final.close} / 390`.

A near-miss card adds `gap` in the amber colour and has no number and no tag.

### 6.6 The list

- **25 cards at a time.** Under them **"Aur dikhao (75 baaki)"** shows 25 more (`NEW_cutoff_10`). All rows are already
  in the answer; this is not another request.
- Then, when `near` is not empty, the heading **BAS THODA SA DOOR** / "Thoda aur, aur ye bhi aapke" and the near cards.
- Then every sentence of `notes`, small and dim.

### 6.7 States

| State | What to show |
|---|---|
| picker lists loading or failed | the form stays usable; on failure the error box with **Retry** |
| result loading | a spinner in place of the list; when only the score or a chip changed, keep the old list and show a small spinner in the heading |
| result failed | the server's sentence, or "Rank abhi load nahi hua. Retry dabao." / "Network kamzor hai. Retry dabao.", with **Retry** |
| a score with nothing eligible | "Is score par yahan 2026 mein koi option eligible nahi tha." + " Neeche dekho, kitna door ho." when there are near misses (`NEW_cutoff_18`) |
| no seat for this profile | "Aapki category, gender aur home state ke liye yahan 2026 ki koi seat nahi thi." |
| the choice changed while an answer was on its way | **never show the old answer under the new choice**: an answer is shown only when its `exam`, `by` and `key` equal the current choice |

### 6.8 Colours

The form wears teal `#2DE1C2` (text on it `#0B0B0F`; soft fill `rgba(45,225,194,0.12)`, line `rgba(45,225,194,0.62)`).
The tile is indigo `#5B4BE0 → #3323A6`. Tags and surfaces: `docs/06_RANK_UI_SPEC.md` §9. The moving shine of tiles and
forms: the separate glossy theme guide.

## 7. What the page remembers

One saved form for the tool (the app's key is `rank.cutoff.v1`; shape `CutoffForm` in `rankProfile.ts`):

```ts
{ exam, level, category, female, pwd, state,          // the exam on screen and the JEE profile chips
  jee:    { by, college, branch, kind, text, score }, // one choice per exam
  comedk: { … }, bitsat: { … } }
```

- `college` and `branch` are remembered separately, so switching "College se" ↔ "Branch se" brings each choice back.
- `text` is what is typed; `score` is what the list is filtered by (`null` = full table). Typing does not filter;
  **Eligible dikhao** does.
- The score belongs to the exam, not to the college: picking another college keeps the filter on.
- Save on every change. **Meri details** (`docs/12`) writes its values into this form as starting values.

## 8. When to call the server

| Event | Call |
|---|---|
| the tool opens for the first time | `GET /rank/cutoff/options` (once; the connector also keeps it 10 minutes) |
| a college / branch is picked; exam or College/Branch switched to a side that has a choice | `POST /rank/cutoff` |
| a JEE profile chip or the paper type changes (the paper type changes "≈ marks" on every card, and the rank when a marks score is applied) | `POST /rank/cutoff` |
| **Eligible dikhao** / **Sab cutoffs dikhao** | `POST /rank/cutoff` with / without the score |
| typing in the search field or the score field; **Aur dikhao** | nothing |

One request per change, a few milliseconds on the server. A branch answer is about 64 KB (8 KB compressed).

## 9. Proof that it agrees with the older tools

`RANK/code/server_reference/tests/test_rank_cutoff.py` (25 checks, all passing on the day of this build) proves on the
running server that:

- a JEE college without a score is exactly Target marks' table (same path, rank type, seats, every round, marks needed);
- JEE, COMEDK and BITSAT tags equal the College predictor's tags for the same score;
- a filtered branch list keeps the most-wanted-first order of the unfiltered one;
- a CSAB cell is never green; a Safe or Likely row always has a green box;
- rank wins over percentile, percentile over marks; a tough paper gives a better rank than an easy one for the same marks;
- every refusal is the sentence listed in `docs/03` §13.4.

## 10. Worked answers (the server, on the day of this build)

Use them to recognise a right screen, never as data.

| Request | Answer |
|---|---|
| JEE · college NIT Trichy · General, no home state | 9 branches, columns R1 … CSAB 2; first card Computer Science and Engineering, "Closing R5: 1,373 CRL · ≈ 235+ marks (Normal paper) · 119 seats", 2025 R6 1,449 |
| the same + 200 marks, Normal | "200 marks (Normal paper) ≈ 99.48 – 99.52 percentile ≈ rank 7,417 – 7,917 (CRL)"; 6 / 9 eligible: Safe 5, Likely 1 (Mechanical: R1 7,872 amber, R2–R5 green, CSAB 1 amber); 3 near, first "lagbhag +3 marks aur" |
| the same + rank 7,000 | "Rank 7,000 ≈ 99.54 percentile"; 7 / 9 eligible; Electrical and Electronics is **Borderline** through CSAB 1 only (R1–R5 out, CSAB 1 7,177 amber, "Closing CSAB 1: 7,177 CRL") |
| JEE · college NIT Trichy · OBC-NCL · rank 20,000 | "OBC-NCL rank: 5,400"; Production Engineering on "Other state · OBC-NCL", closings on `OBC-NCL rank`, its CSAB 1 box "CSAB 1 · CRL 26,884" amber |
| JEE · branch Computer Science · General | "Top 100 of 123 college-branch · sabse zyada demand wale pehle"; first card NIT Trichy |
| the same + 200 marks | 113 eligible: Safe 107, Likely 3, Borderline 3; " · top 100 dikh rahe" |
| JEE · college DTU Delhi · 99.2 percentile · home state Delhi | columns R1–R4 only, no last-year box; "Delhi region · Open"; 18 / 18 eligible |
| COMEDK · branch Computer Science · rank 30,000 | "Rank 30,000 · GM (All India)"; 142 / 162 eligible, top 100 shown; cards carry fee and GM seats |
| COMEDK · college R V College of Engineering · 150 marks | "150 / 180 marks ≈ rank 29 – 150 (beech ka andaaza 100) ≈ 99.88 – 99.98 percentile"; 13 / 13 Safe; `you.check` shown |
| BITSAT · campus Pilani | "18 programs · 5 saal ke cutoff score"; boxes 2022 … 2026 |
| BITSAT · campus Pilani · 300 | 17 / 18 eligible: Safe 16, Likely 1; only the 2026 box is green |
| BITSAT · program B.E. Computer Science · 280 | 2 / 3 eligible (Goa, Hyderabad: Likely); near: Pilani "+28 marks aur" |

## 11. Acceptance list for Cut off

- [ ] The second Rank tile is **CUT OFF** ("college / branch"); there is no "Percentile se rank" tile.
- [ ] Each of the three exams offers both sides (college / branch; BITSAT campus / program) and both work.
- [ ] The picker finds "cse", "ece", a city, and a college's full name; it sends no request while typing.
- [ ] A college shows **all** its branches; a branch shows at most 100 rows with the "Top 100 of N" line.
- [ ] Every card shows every round the server sent; JAC Delhi cards have four round boxes; BITSAT cards have five year boxes labelled with years.
- [ ] JEE Main starts on **General**; category, Female, PwD and home state change the `path` on the cards.
- [ ] COMEDK and BITSAT show no category chips.
- [ ] The score is optional. With it: only tagged rows, the three counts, green / amber boxes, near misses with `gap`.
- [ ] A CSAB box is never green. A CSAB-only row reads Borderline.
- [ ] JEE accepts marks, percentile or rank; COMEDK marks or rank; BITSAT a score only. Wrong numbers show the sentence and send nothing.
- [ ] "Sab cutoffs dikhao" brings the full table back; "Score badlo" keeps the typed number.
- [ ] Every number, tag, count and sentence equals the server's answer for the same body (`docs/09` §2).
- [ ] Switching exam, side or college never shows the previous answer under the new heading.
- [ ] The form, both choices per exam and the score survive a reload.
- [ ] `notes` are shown under the list, including the BITSAT "no rounds" line and the estimate line.
- [ ] Works at 320 px wide (four round boxes still fit on a line), by keyboard, and with reduced motion.
- [ ] (§13) Every card with a `trend` shows its arrow and `label` in the right colour; a card without one shows nothing there.
- [ ] (§13) Every card has the **Compare** toggle; a saved row appears in College compare and in the saved-list PDF, for all three exams.
- [ ] (§13) "PDF WhatsApp" and the PDF button send **the same body as the list on screen**; the file keeps the server's name.

## 12. Questions that will come up

**Why 100 for a branch?** Computer Science alone has 123 college-branches in JEE Main and 162 in COMEDK. The first 100
by demand are the ones students ask about; the count line says how many there are in all, and `eligible` always counts
the whole list.

**Can we add paging or "show all" for a branch?** Not with this endpoint: it returns the first 100. Narrow by score, or
open the college.

**Why does the same branch show a different closing rank after I change the category?** The seat path changed. The
server always shows the easiest path open to the student and prints it on the card.

**Why is a row Safe but its CSAB box amber?** The tag comes from the JoSAA rounds, which the student is safely inside.
CSAB is a left-over round and is never promised.

**Why does the list not shrink while I type my marks?** The filter is applied on **Eligible dikhao**, so a half-typed
number never empties the list.

**Where did "Percentile se rank" go?** Its tile became Cut off. A percentile is now accepted by Cut off's score box and
by the College predictor's form (which also takes a scorecard rank), and both show the rank it stands for.
`POST /rank/percentile` still answers, for older app versions; no current screen uses it.

---

## 13. Added after the first build: last-year arrow, Compare, PDF and WhatsApp  —  NEW

Four small things were added to the same tool on 23 Nov 2026. Nothing above changed; the answer only grew by two fields
per row (`trend`, `save`) and the server got one more PDF. Field tables: `docs/03` §13.3 and §12.

### 13.1 The last-year arrow (`trend`)

At the foot of a card, on the left, one small line:

| `trend.dir` | Draw | Colour |
|---|---|---|
| `"tough"` | an up arrow + `trend.label` ("is saal aur mushkil") | the error red |
| `"easy"` | a down arrow + `trend.label` ("is saal thoda aasaan") | the success green |
| `"same"` | no arrow, `trend.label` ("≈ pichhle saal jaisa") | soft / muted text |
| `trend` is `null` | nothing (the Compare toggle stays on the right) | |

- "Tough" means **harder to get in than last year**: for a closing rank the number went down, for a BITSAT score it
  went up. The server has already decided this; print `label`, never work it out from the boxes.
- JEE Main compares the last JoSAA round of 2026 with 2025's final round on the same seat path. It never uses a CSAB
  closing, even on a row whose tag came from CSAB. JAC Delhi rows have no arrow (no last-year data).
- Within 3 % either way reads "same".

### 13.2 Compare (`save`)

At the foot of every card, on the right, a pill toggle:

| State | Label | Look |
|---|---|---|
| not saved | **＋ Compare** | outline pill |
| saved | **✓ Compare mein** | green line and soft green fill |

- A tap adds `row.save` to the student's shortlist, or removes it. It is the **same shortlist** the College predictor's
  bookmark uses (the app's key `rank.shortlist.v1`, newest first, at most 50), so the row is at once available in
  **College compare** and in the saved-list PDF. No server call.
- The key is `save.id`. A row saved from Cut off and the same college-branch saved from the College predictor are one
  item, not two.
- `save.tag` is the tag at the moment of saving (`null` when no score was applied). It is not refreshed later.
- Near-miss cards have the toggle too.

### 13.3 The two PDF buttons

Under the heading box, whenever the list has at least one row: **"PDF WhatsApp"** (green) and a second button reading
**"Eligible list ki PDF"** when a score is applied, else **"Cut off list ki PDF"**.

- Both call `POST /rank/pdf/cutoff` with **exactly the body that drew the list** (same `exam`, `by`, `key`, profile
  chips, score and `level`). So the PDF is the Safe / Likely / Borderline list the student is looking at.
- "PDF WhatsApp" then shares the file with the caption the other Rank PDFs use (`docs/06` §10); the other button saves
  or prints it. Busy state, 30 s limit and the failure sentence are the same as every Rank PDF.
- A change of score, college, branch or chip clears the "taiyaar" line under the buttons (it belonged to the old list).
- File name from the server: `JEELIVE-cutoff-{exam}-{by}-{score}.pdf` (`docs/03` §12).

### 13.4 Checked on the app

- Server: `RANK/code/server_reference/tests/test_rank_cutoff.py` (33 checks; the last 8 are these additions: the trend
  rule for all three exams including a CSAB-decided list, a saved row of each exam opening in compare, four PDFs and a
  refused PDF).
- Samples: `RANK/sample_pdfs/sample_cutoff_*.pdf`; every `RANK/api_examples/24_…` to `32_…` answer now carries `trend`
  and `save` on each row.
