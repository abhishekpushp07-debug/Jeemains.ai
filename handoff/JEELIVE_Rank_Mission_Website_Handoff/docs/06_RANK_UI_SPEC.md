# 06 · Rank UI spec

The six Rank tools screen by screen, as the app shows them. Screenshots are in `RANK/screenshots/` (390 × 844 at 2×,
taken fresh from the app for this pack). The React Native files named here are in `RANK/code/app_reference_ui/` and
are the behaviour reference. The website may adapt layout to a wider screen, but keeps the words, the order of
information, the tags and the colours.

## 1. The page

- **Pure black page** (`#000000`), text-only, no photos. Cards carry the colour.
- Header: a small rule title `JEELIVE.AI · Rank`, the serif title **"Rank & college predictor"** and the line
  `JoSAA · CSAB · JAC Delhi · BITSAT · COMEDK, 2026 cutoffs`.
- **Six tool tiles**, three rows of two (`ToolGrid.tsx`), brushed graphite metal, each with its own jewel colour and a
  `NEW` badge where shown:

| Tile | Subtitle | Form colour (`accent.tsx`) |
|---|---|---|
| RANK PREDICTOR | marks se rank | bright yellow `#FFD60A` |
| PERCENTILE SE RANK | NTA percentile | teal `#2DE1C2` |
| TARGET MARKS | college ke liye | lime `#B5F23D` |
| COLLEGE PREDICTOR | colleges + cutoffs | blood red `#D10F2A` (white text) |
| COLLEGE COMPARE | side by side | sky blue `#4CC3FF` |
| DREAM COLLEGE | kitne marks door | violet `#7B2CBF` |

- The chosen tile glows in its colour; the form below wears the same colour (frame, header band, chosen chips, fields,
  main button). Text on yellow/teal/lime/sky is near-black `#0B0B0F`.
- A tool opens below the tiles. A tool keeps its answer when the student switches away and back.
- Every form remembers its last values in the browser (the app uses phone storage), so a returning student sees their score.
- After **Show**, the form collapses into a summary bar with a glowing **Edit** pill and the hint "Doosra number dekhna hai?".
- At the foot: the estimate note, the data line, `meta.missing`, and links to the All India series and results.
- Screenshot: `01_rank_tab_six_tools_and_rank_predictor_form.jpg`.

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

## 4. Percentile se rank (`PercentileRank.tsx`)

Percentile field, category chips, PwD switch → the Rank Card (CRL range, category/PwD rank) and the marks that
percentile took on a tough, normal and easy paper. "Is percentile se colleges dekho" hands over to the College
predictor. Screenshots `05`, `06`.

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
- Form: marks or percentile, paper type, category, female, PwD, home state (searchable picker sheet), branch filter.
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
