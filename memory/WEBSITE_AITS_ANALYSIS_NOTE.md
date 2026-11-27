# For the website: AITS analysis — what the app needs before the launch on the 9th

Written by the app side on 28 Nov 2026. The app reads `GET /api/attempts/{id}/analysis` (analysis_version 3,
rules_version 2) and draws every section from it. **No app update can reach students before JEE Main**, so the
AITS analysis must be correct from the website's answer alone.

## What the app already does with your answer (no app change needed)

- **Levels.** It reads `easy`, `moderate`, `tough` and `unrated` from `difficulty.all` and `by_subject`, and the labels
  from `copy.levels` and `copy.level_sources`.
- **Chapters.** It uses `question.topic` and `performance.subjects[].chapters` / `performance.weak`, and a chapter row
  opens the questions whose `topic` equals the chapter name.
- **"Previous-year paper" and "Uncategorised"** are names of a paper, not of a chapter. The app never lists them as
  chapters; it shows "chapter ka tag nahi hai" instead.
- **Partial tags.** Some questions `unrated`, some with an empty `topic`, or a level present in one subject only: all
  are drawn correctly. This was checked with built answers of 75 questions and 9 chapters per subject.
- **A broken field** now shows "Yeh hissa abhi nahi khul paaya" in that one section only, instead of closing the app.
  Please still never send `null` where the contract has a list or an object.

## What the website must do (the app cannot do it)

1. **Send the AITS tags inside the analysis:**
   - `question.topic` = the real chapter name, not "Previous-year paper".
   - `question.difficulty` + `difficulty_source = "paper"` for the paper's own level, until 50 students have tried
     the question.
   - `performance.has_chapters = true` only when real chapter names exist.
   - Fill the chapter lists and `weak` from those names.
2. **Recalculate saved analyses when tags change.** If levels or chapters are added after some students have already
   finished a paper, their saved analysis must be built again. Otherwise they keep seeing "Not rated" and no chapters.
3. **JEE Main PYQ papers today:** every question has `topic = "Previous-year paper"` and `has_chapters = true`.
   Please send real chapter names or `has_chapters = false`. The app already hides that name.
4. **`class.state = "preparing"` after the AITS release:** the app asks again 6 times, 2.5 s apart. After that it shows
   the answer without class numbers, and the student can tap Retry. Please keep the class-stats job well inside that
   window at peak, or keep sending the analysis without class numbers. The app will not poll harder at the peak.
5. **Speed:**
   - Today the analysis answers in 450–950 ms through the app's server (23–46 KB for 75 questions).
   - Please keep it under 1 s at the AITS peak (a saved analysis, not built on every request).
   - Keep the `topic` and `difficulty` strings short.
6. **Tags inside the report PDF / scorecard** come from the same analysis, so items 1 and 2 cover them too.

## Built answers you can test against

- `tests/fixtures/aits_analysis/aits_full.json`
- `tests/fixtures/aits_analysis/aits_partial.json`
- `tests/fixtures/aits_analysis/aits_no_easy.json`
- `tests/fixtures/aits_analysis/real_unrated.json`

They are built by `tests/aits_analysis_fixtures.py` from one real answer.
