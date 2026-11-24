# 06 · Rank UI spec

The six Rank tools screen by screen, as the app shows them. Screenshots are in `RANK/screenshots/` (390 × 844, taken
from the app). The React Native files named here are in `RANK/code/app_reference_ui/` and
are the behaviour reference. The website may adapt layout to a wider screen, but keeps the words, the order of
information, the tags and the colours.

> **New in this pack:** the **Meri details** bar above the tiles (§1, `docs/12`), the **Cut off** tool in the second
> tile (§4, `docs/11`), and a third score box, **Rank (CRL)**, in the College predictor's JEE form (§6).
> The "Percentile se rank" tool is gone.

## 1. The page

- **Pure black page** (`#000000`), text-only, no photos. Cards carry the colour.
- Header: a small rule title `JEELIVE.AI · Rank`, the serif title **"Rank & college predictor"** and the line
  `JoSAA · CSAB · JAC Delhi · BITSAT · COMEDK, 2026 cutoffs`.
- **Meri details** (new, `ProfileBar.tsx`): one card between the header and the tiles. Never saved: "Apni details ek
  baar daalo" with a **+ Bharo** pill. Saved: "Meri details", the profile in one line and an **Edit** pill. It opens
  into a small form; Save fills every tool's form. Everything about it: `docs/12_MERI_DETAILS_NEW.md`.
- **Six tool tiles**, three rows of two (`ToolGrid.tsx`, `JewelFace.tsx`). Each tile is its tool's own colour from
  corner to corner, with a faceted diamond in its corner, a soft gloss, a glint that crosses it and three matching
  colours running round its edge; a white `NEW` badge where shown:

| Tile | Subtitle | Tile colour | Form colour (`accent.tsx`) |
|---|---|---|---|
| RANK PREDICTOR | marks se rank | maroon | bright yellow `#FFD60A` |
| **CUT OFF** — new | college / branch | indigo | teal `#2DE1C2` |
| TARGET MARKS | college ke liye | teal | lime `#B5F23D` |
| COLLEGE PREDICTOR | colleges + cutoffs | blood red | blood red `#D10F2A` (white text) |
| COLLEGE COMPARE | side by side | gold (near-black words) | sky blue `#4CC3FF` |
| DREAM COLLEGE | kitne marks door | violet | violet `#7B2CBF` |

- The chosen tile glows in its form's colour; the form below wears the same colour (frame, header band, chosen chips, fields,
  main button). Text on yellow/teal/lime/sky is near-black `#0B0B0F`. Exact tile colours and the moving shine: `theme.ts`
  (`custom_tile…`, `toolEdges`, `formEdges`) in `RANK/code/app_reference_ui/shared/`.
- A tool opens below the tiles. A tool keeps its answer when the student switches away and back.
- Every form remembers its last values in the browser (the app uses phone storage), so a returning student sees their score.
  Keys and shapes: `docs/12` §4.
- After **Show**, the form collapses into a summary bar with a glowing **Edit** pill and the hint "Doosra number dekhna hai?".
- At the foot: the estimate note, the data line, `meta.missing`, and links to the All India series and results.
- Screenshot: `01_rank_tab_meri_details_bar_and_six_tools.jpg`.

## 2. The Rank Card (shared look)

`MetalCard.tsx`, `ResultCard.tsx`. A quiet black metal card: soft graphite corner fading to black, a soft blood-red
glow, a shimmering top edge, sparkle-silver serif numbers, blood-red hairlines and tracked caps, a `№` serial, a faint
diamond watermark. Gradients and SVG only, no image files. The big line is the rank range; under it the percentile
range, the summary line, category/PwD rank, and the `spread` sentence.

Colours: card `#1C1D22 → #0E0F12 → #150A0E`, glow `rgba(153,27,27,0.30)`, silver `#EEF2F7`, muted silver `#94A3B8`,
blood red `#B3172F`, blood ink `#F4A3AE`.

## 3. Rank predictor (`RankPredictor.tsx`)

- Exam switch: **JEE Main · COMEDK**. Fields: marks; paper type chips **Tough · Normal · Easy** (JEE); category chips;
  PwD switch. Main button **Show**.
- JEE answer: the Rank Card for the chosen paper type, then **all three paper types side by side** (percentile, CRL,
  category/PwD rank per row), the notes, a share button, and **"Is score se colleges dekho"** which opens the College
  predictor with the same score already shown.
- COMEDK answer: rank range, middle estimate, percentile, the three analyses with their own rank and link.
- Screenshots `02`, `03`, `04`.

## 4. Cut off (`Cutoff.tsx`, `CutoffList.tsx`) — NEW

The second tile. It took the place of "Percentile se rank" (that tool and its screen no longer exist; screenshots
`05` and `06` of the earlier pack were removed with it).

- Exam switch **JEE Main · BITSAT · COMEDK**; then **College se · Branch se** (BITSAT: **Campus se · Program se**); a
  chooser that opens a search sheet over `GET /rank/cutoff/options`; for JEE Main the category chips (General at the
  start), Female, PwD and Home state.
- Answer (`POST /rank/cutoff`): a heading with a count line, an **optional score box** ("Sirf wahi dekhna hai jahan aap
  eligible ho?"), then one card per branch (or per college) with **a small box for every round's cut-off**, 25 cards at
  a time. A college shows all its branches; a branch shows its top 100 colleges.
- With a score (marks, percentile or rank): only Safe / Likely / Borderline rows stay, the boxes turn green (inside)
  or amber (on the edge), and the nearest misses follow under "BAS THODA SA DOOR".
- BITSAT has no rounds: its boxes are the five years 2022 … 2026.
- Added after the first build (`docs/11` §13): at the foot of every card a **last-year arrow** on the left ("is saal aur
  mushkil" in red with an up arrow, "is saal thoda aasaan" in green with a down arrow, "≈ pichhle saal jaisa") and a
  **＋ Compare / ✓ Compare mein** toggle on the right (the same shortlist as the College predictor's bookmark); under
  the heading box the buttons **"PDF WhatsApp"** and **"Eligible list ki PDF" / "Cut off list ki PDF"**.

This tool has its own document with every word, state, rule and its acceptance list: **`docs/11_CUT_OFF_NEW.md`**.
Screenshots `NEW_cutoff_01` to `NEW_cutoff_20`.

## 5. Target marks (`TargetMarks.tsx`)

- Exam switch JEE / BITSAT / COMEDK. JEE needs the seat profile (category, female, PwD, home state).
- **College search sheet** (`CollegeSearch.tsx`): a bottom sheet with a search field over `GET /rank/colleges`.
- Answer: one card per branch, the big serif "235+" = marks on a normal paper, "Tough paper 226+ · Easy paper 247+ ·
  99.91 percentile", the path and seats; tap a branch for the round table (Round · Closing · Tough · Normal · Easy).
- PDF buttons: "PDF WhatsApp" (green) and "Is college ki PDF".
- Screenshots `07`, `08`, `09`.

## 6. College predictor

Exam switch **JEE Main · BITSAT · COMEDK**; each keeps its own score and list.

**JEE Main** (`InputCard.tsx`, `ResultCard.tsx`, `SeatList.tsx`, `CollegeCard.tsx`, `CollegeSheet.tsx`):

- Mode switch **My marks · Percentile chart**.
- Form: three score boxes, **Marks (out of 300)**, **Percentile** and (new) **Rank (CRL), scorecard se** (whole number,
  1 … 20,00,000, placeholder "e.g. 12000"). Under them one small line: "Koi ek kaafi hai: marks, percentile ya rank." and,
  as soon as two boxes are filled, "Ek se zyada bhare hain: sabse pakka number chalega. Pehle Rank, phir Percentile,
  phir Marks." Nothing filled → "Marks, percentile ya rank mein se koi ek daalo." Then paper type, category, female,
  PwD, home state (searchable picker sheet), branch filter.
- With a rank the Rank Card shows that rank as **one number** (not a range), the percentile it stands for, and the
  summary "Rank 7,500 · General"; the collapsed summary bar reads the same.
- Answer: the Rank Card with a shining purple score bar (`#B43CFF → #6A16E8`), "655 college-branches in reach", filter
  chips **All · NIT · IIIT · GFTI · Delhi** with counts, a branch filter, "Top 50 ki PDF".
- **College cards**: a coloured chance edge, a medal, tags (type, chance), the branch, three stat boxes (closing rank +
  round, 2026 vs 2025 trend arrow ▲ tough hua / ▼ aasaan hua, path), and a **"Cutoff dekho ›"** call to action. A tap
  hint above the first card; the first card's CTA breathes until the student opens one; opened cards get a "Dekha" tag.
  Save (shortlist), compare and 🎯 Dream college buttons on each card.
- **Near misses**: cards with an amber edge and the server's `gap` sentence, after the list.
- **College sheet** (bottom sheet): college name and place, path switches (quota, gender, seat), the student's rank,
  the round ladder sentence (`line`), a ladder of rounds, the branches × rounds grid (green = inside), official links,
  2025 R6 column.
- **Percentile chart**: 50 rows of percentile · ~rank · ~marks with category chips; a row opens its 20 colleges.
- Screenshots `10` to `18`.

**BITSAT** (`Bitsat.tsx`): score field (out of 390), campus and degree filters → a card ("clears 47 of 50 programs",
best program, next target) and program cards with the 5-year history. Screenshots `19`, `20`.

**COMEDK** (`Comedk.tsx`, `ComedkSheet.tsx`): marks **or** rank, course groups, Bengaluru / outside → card with the
range and three analyses, college-course cards with fee and GM seats, a sheet with round-wise closing. Screenshots `21`, `22`.

## 7. College compare (`Compare.tsx`, `CompareColleges.tsx`)

Two modes: **saved branches** (from the shortlist, 2–3 side by side, round by round) and **college vs college**
(pick 2–3 colleges from the search sheet; branches, easiest/toughest branch with marks, Computer Science, seats, fee).
Screenshots `23`, `24`.

## 8. Dream college

See `docs/08_DREAM_COLLEGE.md`. Screenshot `25`.

## 9. Tags and labels (`tones.ts`)

| Tag | Ink | Soft fill |
|---|---|---|
| Safe | `#6EE7B7` | `#0E3A2D` |
| Likely | `#93C5FD` | `#14213F` |
| Borderline | `#FCD34D` | `#33270C` |

College type chips: NIT `#F9A8C0`, IIIT `#5EEAD4`, GFTI `#E9C46A`, Delhi `#C4B5FD`. Paper type: Tough `#FCA5A5`,
Normal `#E6E8EE`, Easy `#6EE7B7`. Page surfaces: cards `#121218`, raised `#1A1A23`, lines `#23232E`, body text
`#E6E8EE`, muted `#8F92A3`.

## 10. Sharing and PDFs

- Share = the Rank Card as a picture plus a short text with the student's personal Mission link (`docs/07` §7), so every
  Rank share also counts for Mission.
- PDFs come from the server (`docs/03` §12). Show a busy state; allow 30 s; on failure show
  "PDF nahi bani. Network check karke dobara try karo."

## 11. States every screen has

| State | What to show |
|---|---|
| loading | skeleton or a busy main button; never fake numbers |
| error | the server's sentence + **Retry** |
| empty list | the server always returns near misses or a sentence; show them |
| offline | "Network kamzor hai. Retry dabao." |

## 12. Accessibility and small screens

- Works at 320 px wide: card numbers size from the width; stat boxes stack under 360 px; chips wrap.
- Touch targets at least 44 px. Every control reachable by keyboard; visible focus.
- Animations (shimmer, breathing CTA, count-up) are off when the student asks for reduced motion.
