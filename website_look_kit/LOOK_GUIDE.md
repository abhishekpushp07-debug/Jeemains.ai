# JEELIVE.AI app look — guide for the website

Goal: a student who uses both the app and the website should feel it is one product. The website copies the app's
**look**. Nothing about data changes.

## 0. Rules (read first)

1. Look only. Keep every website route, field, response shape, timer and paper rule exactly as it is. The app reads
   them; changing them breaks the app.
2. Name: show `display_name`. If it is missing, null or empty, show **Learner**. Never fall back to `name`.
3. Rapid Fire is an app-only game. On the website every Rapid Fire button is a download button:
   Android phone → `https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15`,
   iPhone → the App Store page once the owner gives it (until then say "iPhone app is coming soon"),
   computer → the Google Play button. Do not build a Rapid Fire game on the website.
4. Do not start a paper to read its questions. Starting begins the student's timer.
5. Every colour below is in `reference_code/theme.ts`. If a value here and that file ever differ, the file wins.

## 1. Base

| Token | Value | Used for |
|---|---|---|
| Page | `#FFFFFF` | every academic page (light only) |
| Ink | `#0F0F12` | titles, body, black buttons |
| Muted ink | `#6B6B75` | second lines |
| Eyebrow | `#74747E`, 12–13 px, 700, letter spacing ~3 px, CAPS | "ALL INDIA SERIES", "PRACTICE" |
| Card | `#FFFFFF`, 1 px `#ECECF0` (strong `#DEDEE4`), radius 22–24 px | lists, tiles |
| Raised | `#F6F6F8` | icon circles, search pills |
| Brand red | `#D91222` (text `#C1121F`) | main red buttons, small accents only |
| Primary action | black pill `#0F0F12`, white words | "Start", "Open result" |
| Success / warning / error | `#15803D` / `#B45309` / `#DC2626` | |
| Spacing | 4 · 8 · 12 · 16 · 24 · 32 · 48 px | |
| Radius | 6 · 12 · 20 · pill 999 | |

Fonts: Figtree (regular 400, medium 500, semibold 600, bold 700, heavy 800). Numbers in analysis (scores, ranks,
times) use Roboto Mono 700. Page titles are Figtree 800, about 34 px; card titles Figtree 800, 20–24 px.

The dock at the bottom (app only) is ink black `#0B0B0D`. The website keeps its own header but uses the same colours.

## 2. Glossy tabs (My Tests, Chapter-wise, Student Choice)

Picture: `screens/02_my_tests_completed.png`, `screens/04_chapter_wise_class_11.png`. Code: `reference_code/GlossTabs.tsx`.

- Three equal pill tabs, height ~46 px, label 13 px (open tab heavy 800, others semibold 600) with the count under it
  in a small white bubble on the open tab.
- Each tab is a top-to-bottom gradient with a white gloss on the upper half and a thin glass glint; a 2 px border of
  three running colours.
- Colours (`theme.ts` → `custom_tab*` and `tabEdges`):
  - **Completed / All** = baby pink: face `#FFAFC9` → `#FF82AB`; resting wash `#FFD3E1` → `#FFBDD2`; edge
    `#FF2D7A`, `#B45CFF`, `#FF8A6B`.
  - **In progress / Class 11** = yellow: face `#FFEE5C` → `#FFD60A`; resting `#FFF29A` → `#FFE455`; edge `#FF7A00`,
    `#FF4F3A`, `#FFB300`.
  - **Saved / Class 12** = sky blue: face `#9BDCFF` → `#52BDFF`; resting `#C4E8FF` → `#96D5FF`; edge `#0A84FF`,
    `#4F46E5`, `#8E7BFF`.
  - Words on every tab `#0F0F12` (open) / `#3D3D47` (resting).
- My Tests: under the tabs a grey search pill, then black/white outcome chips ("All outcomes", "Scored",
  "Time expired", "Preparing"), then the cards.

## 3. Chapter-wise tests — subject first, then class

Pictures: `screens/04_chapter_wise_all_1.png`, `04_chapter_wise_all_2.png`, `04_chapter_wise_class_11.png`,
`04_chapter_wise_class_12.png`.

- Row 1: the three glossy tabs **All (pink) · Class 11 (yellow) · Class 12 (sky blue)**, each with its count.
- Row 2: subject chips **Physics · Chemistry · Mathematics**, each with its count; the chosen one is brand red with
  white words.
- The list shows **one subject at a time**. Counts on the class tabs are for the chosen subject (live today: Physics
  All 30 = Class 11 15 + Class 12 15). Never merge the three subjects into one Class 11 list.
- "All" lists Class 11 first, then Class 12, in chapter order.
- Row: number circle (`#F6F6F8`, 1 px line), title "09 Fluids" 20 px 800, second line
  "31 Q · 60 min · +4/-1 · 124 marks" muted, black "Start" pill on the right.
- Loading: ask for up to **100 chapters per request** (`per_page=100`) so a subject fills in one go; keep paging if
  `total` is larger. The class of a chapter must come from the website's own data (see the website work list), not
  from guessing the title.

## 4. Home

Pictures: `screens/01_home_1.png` … `01_home_5.png`.

1. **Greeting**: "good evening, learner." (lower case, Figtree 800 ~34 px) + "one focused step today." muted.
   The name is `display_name` → Learner.
2. **All India Series card** (`01_home_1`): onyx → deep ruby gradient `#0B0B0D` → `#17090D` → `#3A0912`, red glow
   `#E11D2E`, running edge `#FF2D4A`, `#FFC857`, `#FF7A93`, radius ~28 px. Inside: "ALL INDIA SERIES" pill with red dot,
   "DAY 10 / 62", status caps, big white title, ring with "7 of 62", a glass row (75 questions · 180 minutes · +4 / -1
   marking), streak line, and a full-width red button "View result" / "Start".
3. **Practice tiles** (`01_home_1`, `01_home_2`): two-column white tiles, height 168 px, radius 24, 1 px `#DEDEE4`,
   white → `#F3F3F6` gradient, round icon (50 px) top left, small green "PYQ" badge top right. Code:
   `reference_code/HomeParts.tsx`.
4. **Misfire card** (`01_home_2`): blood red `#C1121F` with white words, deeper rim `#5C060D` carrying a row of
   running dots (`#FFD60A`, `#FFFFFF`, `#2DE1C2`), title in glossy yellow `#FFC61A` (upper half `#FFF3A6`).
   Code: `reference_code/HomeMisfire.tsx`.
5. **Dream College Meter** (`01_home_3`): shining purple only outside — header band `#B43CFF` → `#6A16E8`, glow
   `#A855F7` — inside pure black `#000000` with `rgba(255,255,255,0.12)` card lines; up arrow numbers in lime
   `#B5F23D`; full-width red button "Dream college chuno". Code: `reference_code/HomeDream.tsx`.
6. **Explore JEELIVE chips** (`01_home_4`, `01_home_5`): two-column pills, height 52, white → `#F3F3F6`, 1 px
   `#DEDEE4`, coloured icon + lower-case label ("comedk mocks", "results & history", "share with friends",
   "our mission").
7. **Share card** (`01_home_5`): royal blue `#3561F0` → `#2344CC` → `#142B8C`, glow `#9DB6FF`, white glass tiles
   `rgba(255,255,255,0.12)` with `rgba(255,255,255,0.24)` lines, "100% FREE · FOREVER" pill, big white title
   "Share it with your friends.", four feature tiles, the "200+" panel, white "Share on WhatsApp" button.
   Code: `reference_code/ShareCard.tsx`. On the website the Rapid Fire tile is a download link (rule 3).

## 5. My Tests

Pictures: `screens/02_my_tests_completed.png`, `02_my_tests_progress.png`, `02_my_tests_saved.png`.

- Title "My Tests" 34 px 800; the glossy tabs of section 2; search pill; outcome chips.
- Card: white → very light grey, radius 24, status in caps with a coloured dot ("SCORED" blue dot), exam name on the
  right, title 22 px 800, "Started 27 Nov, 12:15 pm · 0/68 saved", bold marks line, two white pill buttons
  "Compare" (with a round tick) and "Open result →".
- Status line colours (`websiteDesign.ts`): completed `rgb(86, 217, 154)`, saved `rgb(255, 105, 116)`,
  in progress `rgb(217, 119, 6)`.

## 6. Result analysis

Pictures: `screens/03_result_analysis_1.png`, `_2.png`, `_3.png`. Code: `reference_code/ReportCard.tsx`.

- Header: eyebrow "JEE MAIN · RESULT", paper title 26 px 800, a row of tab pills (Analysis black, Progress,
  Confidence…).
- Score hero: deep ruby card with the Attempted / Sahi / Galat / Chhode glass row.
- Insight strip: cream `#FFF7E6`, 4 px amber left bar, bold sentence, amber "Time mein poora hisaab →" link.
- Four stat tiles (RANK, PERCENTILE, ACCURACY, TIME): white, 4 px coloured left bar, big Roboto Mono numbers.
- Report download card: sky → aqua glossy card `#86CFFB` → `#66E0CC`, halo `#38BDF8`, ink `#0F0F12`, with the
  "ORIGINAL" mark.
- Bottom: "Personal · Comparative" switch and numbered section chips (1 Overview red, 2 Performance, 3 Score Potential…
  with the shine edge `#FF3D9A`, `#FFB020`, `#10C7A8`, `#3B82F6`, `#9B5CFF`).

## 7. Rank (black world)

Pictures: `screens/05_rank_1.png`, `05_rank_2.png`. Page is pure black `#000000`; cards are brushed graphite
(`#1C1D22` → `#0E0F12` → `#150A0E`) with silver words `#EEF2F7`. Tool tiles each wear their own colour:
maroon `#BC1F55`, indigo `#5B4BE0`, teal `#0A7B70`, blood `#D10F2A`, gold `#F2C14E` (near-black words), violet
`#8E3BD9`. The "Meri details" bar has a dotted running rim (`#FF2D7A`, `#FFD60A`, `#FFFFFF`, `#B45CFF`). The saved
details belong to the website (shared with the app); the rank numbers stay as the app computes them.

## 8. Student Choice

Pictures: `screens/06_student_choice_1.png`, `_2.png`. Subject tabs are glossy like section 2: Physics red
(`#FF9AA2` → `#FF6B76`), Chemistry amber (`#FFD27A` → `#FFB52E`), Maths teal (`#7EEBDC` → `#2FD4BE`); a chosen chapter
wears the soft wash of its subject (`#FFF1F2`, `#FFF7E6`, `#E9FBF8`). The paper itself is still made only by the
website (doors A, B, C in the website work list).

## 9. Misfire and All India Series pages

Pictures: `screens/07_misfire.png`, `screens/08_all_india_series.png`. Series day cards use the status pastels in
`theme.ts` → `pastel` (today coral/pink, done royal blue `#2F56E0` with white words, upcoming teal/sky, missed sand);
day chips are blood red `#C1121F` (still to come) or parrot green `#96EA3A` (over).

## 10. Rapid Fire download card (what the friend sees at the end of a match)

Code: `reference_code/GetTheApp.tsx`. A friend who opened a match link without the app plays in the browser; at the
end of the result a big gold-framed card says "PLAY IN THE APP" with three reasons and one store button for their
phone ("GOOGLE PLAY" / "APP STORE", small line "Get the app · …").
The website's own Rapid Fire buttons can use the same words and the same store links (rule 3).
