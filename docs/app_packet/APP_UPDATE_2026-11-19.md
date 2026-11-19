# JEELIVE app update — 19 Nov 2026 addendum (Analysis 2.0, after the 18 Nov packet)

Date: 19 Nov 2026. Read `APP_UPDATE_2026-11-18.md` first. This file lists only what changed after it.

**Status: preview only. Not on jeelive.ai yet.** It goes live with the owner's next deploy.
The server in this packet answers `analysis_version` 3. A server that has not been updated answers 2 and has none of the new fields, so treat every new field below as optional.

What did not change: no endpoint added, removed or renamed; no request changed; time capture (18 Nov guide, section 3) is the same; `rules_version` is still 2 (no rule number changed).

Files added or refreshed in this packet:

| File | What it is |
|---|---|
| `APP_UPDATE_2026-11-19.md` | This addendum |
| `samples/*.json` | Taken again from the updated server (version 3, synthetic students) |
| `samples/12_explain_texts.json` | The (i) texts of the website for sample 01 (not an API response) |
| `explain.js` | The website's 50-line function that builds every (i) text from `analysis.rules` |
| `analysis_rulebook.json` | Same rules, `analysis_version` now 3 |

---

## 1. Checklist

| # | Priority | Change | Section |
|---|---|---|---|
| 1 | P1 | Three new fields in the analysis response: `rules`, `overview.class_subjects`, `journey` inside `you` and `compare.profile` | 2 |
| 2 | P1 | Solutions screen: four cards and the question's own journey replace the long insight line | 4 |
| 3 | P1 | Leaderboard on Overview in both modes, top 50, "Aapse ek Rank upar", name box | 5 |
| 4 | P1 | New blocks inside the 8 sections (list in section 3) | 3 |
| 5 | P2 | (i) "yeh kaise bana" on every number | 6 |
| 6 | P2 | Display-name dialog copy is now Hinglish | 5.3 |
| 7 | P2 | Button names: "Analysis report", "Scorecard share", "Solutions PDF" | 7 |

---

## 2. API: new fields in `GET /attempts/{id}/analysis`

### 2.1 `rules` (top level)
`{ par, quality, difficulty, extra, potential, compare }`: the rulebook numbers this analysis was made with (same numbers as `analysis_rulebook.json`). Use them in the (i) texts so the words can never differ from the maths. Example in `samples/01_analysis_personal.json`.

### 2.2 `overview.class_subjects`
Subject scores of the class next to the student's own.

- Missing when the class is not ranked yet. `null` when fewer than 2 students.
- Else `[{ name, topper, average, top10, average_accuracy }]`. `topper` shows from 2 students. `average`, `top10` and `average_accuracy` are `null` until `class.min_finishers` (10) students.
- The student's own score for the same subject is `overview.subjects[].score` (match by `name`).

### 2.3 `you.journey` and `compare.profile.journey`
`{ visited, revisits }` or `null`.

- In `you`: questions the student opened, and how many times the student came back to a question already opened.
- In `compare.profile` (Topper, Top 10%, Class average, a student): the same two numbers, averaged over the students of that group who have a time record.
- `null` when there is no time record on that side.

### 2.4 Unchanged but newly used
- `class.above { handle, score, name }`: used for the "Aapse ek Rank upar" compare button (5.2).
- `compare.split[] { name, volume, quality }` and `compare.split_total`: shown as a table (3.9).
- `questions[].seen`: used for two new Qs by Qs filters (3.8).
- `/analysis/questions?filter=` has the same 8 filters as before. The two new filters are worked out on the device.

---

## 3. Screens: what is new inside each section

Copy is exact. `{…}` are values.

### 3.1 Frame
- Buttons under the section title, in this order: **Analysis report**, **Scorecard share**, **Solutions PDF** (the old solutions report; only when the result has `report_allowed`; reads "Answer keys PDF" when every question is answer-key only), **Galat + chhode dobara**, **Solutions dekho**.
- Every block has an (i) button at its top right. Tiles that are numbers have one too (section 6).

### 3.2 Overview
- Rank tile: tap scrolls to the leaderboard. Tap label "Leaderboard dekho →".
- When the student is rank 1: "Aap is paper ke **topper** ho: {of} students mein sabse upar. Ab apna hi Score todna hai."
- New block, kicker "{n} STUDENTS MEIN", title "Har subject mein aap vs class" (from `class_subjects`): grouped bars Aap / Class average / Top 10% / Topper, then a table Subject, Aap, Class average, Top 10%, Topper, Average se (signed, green when ≥ 0, red when below).
  - Note with all four: "Aapka Score, class ka average, Top 10% ka average aur Topper ka Score."
  - Note when only Topper is there: "Abhi sirf Topper dikh raha hai. Class average aur Top 10% kam se kam {min_finishers} students par khulte hain." Then show only Aap and Topper.
  - Hide the block when `class_subjects` is missing, `null` or empty.
- The leaderboard block sits on Overview in Personal and in Comparative (section 5).

### 3.3 Performance
- All-subjects table columns: Subject, Score, Score %, Sahi, Galat, Chhode, Dekha hi nahi, Accuracy, Attempt rate, Negative, Time. Last row "Kul" with the sums (only with 2 or more subjects).
- Chapter table: tapping a row opens that chapter's questions.

### 3.4 Score Potential
- Chart bars, left to right: Abhi, Careless, Risk, Time (each step bar floats from the running total, label "+{marks}"), Target (`realistic`), Max (`maximum`). Target is now a bar, not a dashed line.
- Without time record: "Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain. Mushkil par risk wala step class ke data se banta hai, woh dikhega. Agle mock se teeno poore dikhenge."
- New block, kicker "GALAT JAWAB, CHAPTER KE HISAAB SE", title "Marks kis chapter se gaye", note "Sirf galat jawab: jo marks nahi mile aur jo negative mein kate, dono milaakar. Bar par tap karo, sawaal khulenge." Made on the device from `questions[]`: for each question with `outcome` `incorrect` and a `topic`, add `pos − neg` to its chapter. Show the top 8, biggest first, as "{chapter}" / "{subject} · {n} galat" / "−{lost}". Tap opens those questions. Hide when empty.
- Guess block, last line: "Bina kisi galat jawab ke (har galat ko chhod dete) aapka Score **{no_negative}** hota, abhi se **{no_negative − current}** zyada."

### 3.5 Attempt Quality
- Above the Speed-Accuracy map: one chip per tag that has dots, "{tag name} ({count})" with the tag icon. Tap hides or shows that tag's dots. A hidden chip is struck through.
- Painful block: kicker "DOHRA NUKSAAN", title "{n} Painful sawaal", note "Galat bhi hue aur Par time se zyada bhi khaaya. Chapter ke hisaab se: inka concept sabse pehle dekho." Group the chips by `topic` (by `subject` when the topic is empty). With only one group, show the chips without a group name.
- Lucky block: kicker "JALDI-SAHI", title "Kahin tukka to nahi tha?", note "Par ke 25% se bhi kam time mein sahi. Tukka tha to concept ek baar dekh lo."

### 3.6 Time kahan gaya
- New line above the subject chart when one subject's `time_pct − weight_pct` is 8 or more (take the biggest): "{name} par {time_pct}% time gaya, jabki paper mein uske marks {weight_pct}% hain. Wahan se {score} / {maximum} marks bane."
- Pace chart: chips Sab jawab / Sahi / Galat turn each line on or off. At least one line always stays on.
- "Pehli nazar vs wapas aakar": tiles "Pehli nazar mein" and "Wapas aakar" = accuracy, sub "{correct} / {count} sahi · {time}", tap opens the questions.
- "AAKHRI 20% TIME · Thakaan ka asar": tiles "Usse pehle" and "Aakhri 20% mein" = accuracy, sub "{count} jawab". With d = early accuracy − late accuracy: d > 10 → "Aakhir mein Accuracy {d}% giri. Aakhri hisse mein naye mushkil sawaal mat kholo, pakke wale dobara check karo."; d < −10 → "Aakhir mein Accuracy {−d}% badhi. Aapka stamina achha hai."; else "Aakhir tak Accuracy lagbhag barabar rahi."

### 3.7 Difficulty
- New table column "Level kahan se aaya": per level, the count by `difficulty_source` of its questions, e.g. "12 shuruaati result se, 3 paper ke tag se" (words from `copy.level_sources`; for Not rated just "abhi Not rated").
- Under the table when `difficulty.unlock` is set: "**{unrated}** sawaal abhi Not rated hain: paper mein unka tag nahi hai aur abhi {have} students ne yeh paper diya hai." Then, when `have` < `rules.difficulty.early_attempted`: " Kisi sawaal ko kam se kam {early_attempted} students attempt karein to shuruaati level khulta hai ({early_attempted − have} aur chahiye), aur {min_attempted} par pakka level." Otherwise: " Kisi sawaal ko {min_attempted} students attempt karein to uska level pakka hota hai." Always end with " Tab tak andaaza nahi lagaya." With `have` 0 say "abhi kisi aur student ne yeh paper nahi diya".
- Tough block note: "Tough = class mein 35% se kam students se bana, ya paper mein Hard likha tha. Inka tareeka yaad rakho."

### 3.8 Question Journey and Qs by Qs
Journey:
- Every visit chip starts with a round mark for that question's result: ✓ Sahi (green), ✕ Galat (red), – Jawab nahi (grey). Legend above the chips: "✓ Sahi", "✕ Galat", "– Jawab nahi", and with tag colours on the chip also shows the tag's small icon after the time, and the legend adds: "Kinara aur chhota icon = tag. Perfect" / "Careless / Concept gap / Mehnga overtime" / "Slow-correct / Confused" / "Smart skip".
- Toggle text: "Tag ka rang chhupao" / "Tag ka rang dikhao".
- Each time block is a fold. Header "{from}–{to} min" + "{n} visits · {k} baar jawab diya ya badla" (k = visits with `set` other than "Clear"). Up to 6 blocks: all open. More: first 3 open.
- Block note: "Ek chip = ek baar sawaal khola. Gol nishaan = us sawaal ka result. Chhota number = kaun si baar. B→C = jawab badla. Time block par tap karke band ya khol sakte ho."

Qs by Qs:
- New block on top, kicker "POORA PAPER EK NAZAR MEIN", title "Sawaalon ka grid". Group by subject, and by "{subject} · MCQ" / "{subject} · Numerical" when a subject has both types. Group header shows "{right}/{count} sahi". Each cell: number, colour by result, a dot in the tag's tone at a corner, the review flag, and a thin blue strip whose width follows `class.correct` (only with class data). Tap opens the solution. Note: "Rang = aapka result. Kone ka dot = tag ka rang. Neeche ki neeli patti = class mein kitne % ne sahi kiya. Number par tap karo, solution khulega." (leave out the third sentence without class data).
- Filters, in order: Sab, Galat, Chhode, **Dekha hi nahi** (`outcome` skipped and `seen` false), **Dekha, jawab nahi** (`outcome` skipped and `seen` not false), Careless, Overtime, Confused, Marked, Jawab badla.
- New "Level" picker ("Sab level" + the levels this paper has) next to Sort.
- Result label is "Dekha nahi" for a skipped question that was never opened.
- Phone card, class line: "Class: {correct}% sahi · avg {avg_time} · topper {topper_time} · {percent}% ne {option} chuna".

### 3.9 Comparative mode
- Picker has a fifth choice "Aapse ek Rank upar" when `class.above.handle` is there → `compare=user:{handle}`.
- Comparing with the Topper while the student is rank 1 with gap 0: "Aap khud is paper ke topper ho, isliye yeh compare aapka apne hi saath hai. Upar se Top 10% ya Class average chuno."
- Gap block (Overview, Performance, Score Potential): kicker "GAP KA HISAAB", title "Gap sabse bada kahan hai", note "Volume = unhone zyada sawaal attempt kiye. Quality = har attempt par unke marks zyada bane (kam galat jawab)."
  - gap > 0: "Kul gap {gap} marks: **{split_total.volume}** kam attempt se, **{split_total.quality}** galat jawab (kam Accuracy) se."
  - gap ≤ 0: "Is compare mein aap {−gap} marks aage ho." or "Is compare mein aap barabar ho."
  - Table from `split`: Subject, Kam attempt se (`volume`), Galat jawab se (`quality`), Kya karein = "Aap aage ho" when both ≤ 0, "Zyada sawaal attempt karo" when volume > quality, else "Accuracy badhao".
- Time section, new block: kicker "TIME", title "Har subject par laga time: aap vs woh", note "Sawaalon par screen time, minute mein." Grouped bars Aap / {label} from `you.subjects[].time` and `compare.profile.subjects[].time`. When either side has no times: "Dono taraf time record hone par hi subject ka time compare hota hai."
- Journey section, new block: kicker "QUESTION JOURNEY", title "Raasta: aap vs woh", note "Kitne sawaal khole aur kitni baar kisi sawaal par wapas aaye." Table rows Sawaal dekhe (`journey.visited`), Wapas gaye (`journey.revisits`), Attempt kiye (`attempted`), columns Aap / {label}. When either `journey` is `null`: "Dono taraf time record hone par hi raasta compare hota hai."
- Head note says "{n} students ka hisaab." only when the group has more than 1 student.

---

## 4. Solutions screen

Replaces 18 Nov guide section 7.4. All data comes from the analysis already loaded (`questions[]` by id, `journey.visits`).

- One short line: "Q{number} · {subject} · {topic} · {level} · {visits} baar dekha · Jawab badla {changed}" + the tag chip. Leave out empty parts; "baar dekha" only when `visits` > 1.
- Four cards (2 × 2 on a phone):

| Card title | Content |
|---|---|
| Aapka time vs Par (with (i) `par`) | `time` large, "Par {par}", a meter filled to min(time ÷ par, 2) ÷ 2: green up to 1.25, amber up to 1.5, red above. Then "Par se {diff} kam" or "Par se {diff} zyada" + " · Par {par_n} students ke median se" (`par_source` solvers) or " · Par paper standard se". No time record: "Is attempt mein har sawaal ka time record nahi hua tha." |
| Class ka time | `class.avg_time` + "average", then "Topper ka time: {class.topper_time}" ("—" when 0 or `null`) |
| Attempt karne walon mein | "{right_of_attempted}% sahi" (green), "{100 − right_of_attempted}% galat" (red), a two-colour bar, then "Sabse zyada chuna galat option: {option} ({percent}% students)" when `top_wrong` is there. When `right_of_attempted` is `null`: "Class mein kisi ne yeh sawaal attempt nahi kiya." |
| Kitno ne attempt kiya | "{attempted}% attempt", "{skipped}% chhoda", a bar, "{n} students mein" |

- Cards 2 to 4 without `class`: "Class ka data kam se kam {min_finishers} students ke baad dikhta hai. Abhi {class.n} students ne diya hai." (stop after the first sentence when `class.n` is 0).
- Below the cards, when the attempt has visits for this question: title "Is sawaal ki journey", small "time = paper shuru hone ke kitni der baad". One row per visit of this question (`journey.visits` where `q` is this id), in order: `a` as "{m}m {ss}s", then "{Pehli|Doosri|Teesri|{v}vi} baar khola · {d} ruke · " + one of "jawab nahi diya, aage badhe" (no `set`), "jawab diya {set}", "jawab badla {set}" (`set` has "→"), "jawab hata diya" (`set` is "Clear"), then " · review ke liye mark kiya" (`mark` true) or " · mark hataya" (`mark` false).
- Number strip: each number also carries the tag-tone dot. Key under it: "Kone ka dot = tag. Perfect", "Careless / Concept gap / Mehnga overtime", "Slow-correct / Confused", "Smart skip".

---

## 5. Leaderboard and display name

### 5.1 Leaderboard block
Replaces 18 Nov guide section 6.4 where they differ. The API is the same.

- Shown on Overview in Personal and Comparative when `class.state` is `ready`.
- Kicker "{n} STUDENTS · HAR STUDENT KA PEHLA ATTEMPT", title "Is paper ka leaderboard", note "Kisi bhi student par Compare dabao: aap vs woh khul jaayega. Sirf naam, Score aur totals dikhte hain; kisi ke jawab ya phone number kabhi nahi."
- Top 10 first. With more than 10 rows a button "Top {rows} dikhao" opens all rows (up to 50); it then reads "Sirf top 10 dikhao".
- Your row: "Aap · {name}" when you have a name, else "Aap".
- "Aapke aas-paas" (5 above, you, 5 below) shows when your row is not in the list on screen.
- Compare on a row switches to Comparative with `compare=user:{handle}` and scrolls to the top.

### 5.2 Name box on the leaderboard
When `you.named` is false, above the table: "Leaderboard par aap abhi **{you.name}** dikh rahe ho. Apna naam likh do, sab aapko pehchaan lenge." with the display-name control next to it. After a save, load the leaderboard again.

### 5.3 Display-name control (copy changed to Hinglish)
Replaces the labels in 18 Nov guide section 8.6. The API and its messages are the same.

- Row: "Leaderboard naam: **{name}**" or "**Abhi nahi likha**", link "Naam likho" (no name) or "Naam badlo".
- Dialog title "Leaderboard par aapka naam". Text: "Leaderboard, Compare aur aapki report par "Learner" aur code ki jagah yeh naam dikhega. Aapka phone number kabhi nahi dikhta. Naam din mein 3 baar badal sakte ho."
- Field "Aapka naam", placeholder "Jaise: Arjun Sharma", hint "2 se 20 akshar, ank ya space · {typed}/20".
- Buttons "Rehne do", "Naam hatao" (only when a name is set), "Naam save karo" (busy: "Save ho raha hai…"). Empty field on save: "Naam likho, ya "Naam hatao" dabao."
- Toasts: "Naam save ho gaya. Leaderboard par ab "{name}" dikhega." / "Naam hat gaya. Leaderboard par aap phir se Learner dikhoge."
- Server refusals (422, 429) are shown as they come.

---

## 6. (i) "yeh kaise bana"

Tap (i) → a small card: the number's name as title, then one or two plain lines saying what it means and how it was counted.

- Every text is built from `analysis.rules`, `analysis.paper.marks` and `analysis.class.n`. Copy `explain.js` (50 lines, no dependencies) or port it one to one. Do not type the numbers by hand.
- `samples/12_explain_texts.json` has all the texts for sample 01, to compare with.
- Without `rules` (older server) show no (i).
- Where each text is used on the website: block headers use the key named after the block (`score`, `ledger`, `next3`, `standing`, `vs_class`, `attempt_rate` on the Performance table, `chapters`, `guess`, `par` on the Attempt Quality head, `speed_map`, `painful`, `lucky`, `time_share`, `pace`, `first_look`, `last`, `difficulty`, `journey`, `changes`, `gap`); tiles use `rank`, `percentile`, `accuracy`, `time`, `attempted`, `realistic`, `maximum`, `perfect`, `wasted`, `overtime`, `confused`, `concept_gap`, `elapsed`, `on_screen`, `off_screen`, `streak`, `negative`, `not_seen`; the three Score Potential step cards use `careless`, `guard`, `reinvest`.

---

## 7. PDF report and share

The two endpoints are the same. The PDF content changed (the server makes it; the app only downloads and opens it):

- Page 1 is a cover: paper, exam, date, the display name when set, Score ring, Rank, Percentile, Accuracy, Time, the verdict line, the marks bar and "Is report mein" (contents).
- Then the 8 sections with their charts (class Score chart, Speed-Accuracy map, time blocks, pace lines), "Is test se meri 3 seekh", "Tags ke matlab", and the Question Journey as visit boxes per time block.
- A4, PDF 1.7, not encrypted. Roman text uses standard Helvetica. A display name, note or paper title in Hindi or another script is printed in that script with an embedded font (the scorecard PNG too). For the 30-question sample: 8 pages, about 220 KB (6 pages without a time record).
- File name is unchanged: `JEELIVE_<paper>_<date>.pdf`.

---

## 8. Lines of the 18 Nov guide that this file replaces

| 18 Nov guide | Now |
|---|---|
| 5, top level: `analysis_version` (2) | 3, plus `rules` (2.1) |
| 5.2 `overview` | + `class_subjects` (2.2) |
| 5.9 `you` and `compare.profile` | + `journey` (2.3) |
| 6.1 buttons "Report download", "Share" | 3.1 |
| 6.2 Score Potential: dashed "Target" line | Target is a bar (3.4) |
| 6.2 Qs by Qs filters | 10 filters and a Level picker (3.8) |
| 6.3 Gap table wording | 3.9 |
| 6.4 Leaderboard on Comparative › Overview only | Overview in both modes (5.1) |
| 7.4 one insight line | Four cards and the journey (4) |
| 8.6 display-name labels in English | 5.3 |

---

## 9. Acceptance checks added

1. Same attempt on website and app: "Har subject mein aap vs class" shows the same four numbers per subject. With 2 to 9 students only Aap and Topper show, with the note.
2. Comparative › Question Journey shows "Raasta: aap vs woh"; with an attempt that has no time record it shows the one-line reason instead.
3. Solutions: a question opened twice with a changed answer shows two journey rows, the second with "jawab badla A→B".
4. Solutions on a paper with fewer than 10 students: cards 2 to 4 show the "kam se kam 10 students" line, card 1 still shows the student's own time.
5. Leaderboard: a student without a name sees the name box; after saving a name the box goes and the row shows the name.
6. Qs by Qs: "Dekha hi nahi" + "Dekha, jawab nahi" counts add up to the "Chhode" count.
7. Every (i) text matches `samples/12_explain_texts.json` when the app is fed sample 01.
8. Against a server that still answers `analysis_version` 2: no crash, the new blocks and (i) buttons are simply absent.
