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
  "rank": 9, "name": "Arjun Sharma", "named": true, "handle": "<16 hex; see part 3: please keep ONE handle per student for the whole series>",
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


==========================================================================================
PART 2 (added 24 Nov 2026) — the student's own Rank of every day, in one answer ("Rank journey")
==========================================================================================
What the app does today
- The series page has a small graph of the student's All India Rank day by day. The app has no single place to ask for
  it, so it asks GET /api/attempts/{id}/leaderboard once for every released live day (two at a time) and keeps only the
  "you" row's rank and n. It keeps each day's Rank on the phone for a week (the two newest days: 10 minutes).
  On day 40 a student who opens the graph for the first time costs the website 40 leaderboard answers.

What would make it light (optional, the graph works without it)
      GET /api/series/all-india-jee/my-days
      -> { "days": [ { "day": 1, "attempt_id": "<id>", "rank": 412, "n": 5120, "score": 187, "maximum": 300 }, ... ] }
- Only released live days. A day whose leaderboard is not ready is left out.
- One answer instead of one per day. Tell the app project when it exists; the app then asks this first.

==========================================================================================
PART 3 (added 24 Nov 2026) — one student followed across days ("Friend compare, day by day")
==========================================================================================
What was seen for real (QA learner, read only, 24 Nov 2026)
- The same student has a DIFFERENT "handle" on every paper's leaderboard (four papers, four handles).
- A student without a display name is shown as "Learner XXXXXXXX", and XXXXXXXX is the first 8 letters of THAT paper's
  handle, so the same student is "Learner B3417CFC" on one paper and "Learner B974D4F1" on the next. Such a student
  cannot be followed from day to day at all, not even by name.
- ?q= is not case-sensitive and finds a student by the name (whole or its beginning), by the handle's first letters
  and by Rank. The single word "Learner" finds nobody.
- So the app cannot tell that "Arjun Sharma" on Day 3 and "Arjun Sharma" on Day 7 are the same student: names are not
  unique and can be changed. The app therefore compares two students on ONE day only, from the two rows it already has.
  It does not match students by name across days (that could show another student's Scores as the friend's).

What the owner asked for
- Pick a friend on the leaderboard and see both students' Scores side by side for EVERY day of the series.

What the website would need to send (either one is enough)
  (a) a handle that stays the same for a student on every All India day and on the whole-series leaderboard
      (still not the user id, still no phone number), or
  (b)   GET /api/series/all-india-jee/compare?with=<handle from any series leaderboard row>
        -> { "them": { "name": "...", "named": true },
             "days": [ { "day": 1, "you": { "score": 187, "rank": 412 } or null, "them": { "score": 201, "rank": 288 } or null }, ... ] }
        null = that student did not hand in that live day. Totals only, never answers, the same privacy as the leaderboard.
- Until then the app shows "Aap vs <student>" for the open day (and for the whole series once PART 1 exists).
