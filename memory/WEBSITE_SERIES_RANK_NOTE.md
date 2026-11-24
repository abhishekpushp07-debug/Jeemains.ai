JEELIVE.AI — note for the website project: the whole-series AITS leaderboard
(copy and paste this into the website project's chat)
==========================================================================================

What the app needs
- One new signed-in endpoint. The app already asks it every time the AITS Leaderboard opens; today it answers 404,
  so the app shows only the day-by-day leaderboard. The day it answers in the shape below, a "Poori series" tab,
  its Rank card and its share card appear in the app by themselves. No app update is needed.

      GET /api/series/all-india-jee/leaderboard          (the slug is the series' own slug)
      GET /api/series/all-india-jee/leaderboard?q=<name or Rank>     (search, same as the day leaderboard)

- The app never adds up Scores itself. The Rank must come from the website, so app and website always agree.

The answer (same envelope and same row fields as GET /api/attempts/{id}/leaderboard, plus three new fields)
{
  "state": "ready",            // or "preparing" / "too_few" …: the same words the day leaderboard uses
  "n": 5120,                   // students ranked in the series
  "title": "All India JEE Mains · poori series",
  "days_counted": 12,          // NEW: how many released live days are added up
  "maximum": 3600,             // NEW: the most marks possible over those days (optional)
  "min_finishers": 10,
  "query": "",
  "rows":   [ <row>, … ],      // the top 50
  "around": [ <row>, … ],      // 3 above the student, the student, 3 below
  "found":  [ <row>, … ],      // answers to ?q= (empty without q)
  "you":    <row> or null      // the student's own row; null when the student has no live day yet
}

<row> = {
  "rank": 9, "name": "Arjun Sharma", "named": true, "handle": "<16 hex, same handle as the day leaderboard>",
  "score": 3075,               // the sum of the student's live-day Scores
  "days": 11,                  // NEW: how many of the counted live days this student handed in
  "attempted": 770, "accuracy": 92.3, "time": 104500,   // totals over those days (accuracy in %, time in seconds)
  "is_you": false
}

Rules the app assumes (please say if any is different)
- Only live attempts count (mode "series_live"); a missed day done later as practice is not added.
- Only days whose result is released are added; a sealed day joins the total when its result opens.
- Each student's first attempt of a day counts, as on the day leaderboard.
- Ties: the same tie-break as the day leaderboard.
- Names: the student's display name (PUT /api/profile/display-name) when set, else "Learner XXXXXXXX"; never a phone number.
- Until it is ready, keep answering 404 (or "state" other than "ready" with empty lists). A different shape stays hidden in the app.

How the app checks the shape (so a half-built answer is never shown)
- "state" and "n" present, "days_counted" a number, "rows" and "around" lists, and every row (and "you") has
  number "rank", "score", "days" and text "name", "handle".
