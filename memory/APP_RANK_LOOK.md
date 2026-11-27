# The app's Rank tab, read 27 Nov 2026 from github.com/abhishekpushp07-debug/Jeemains.ai (branch App). Copies: docs/app_side_2026-11-27/rank/
Owner's decisions (27 Nov): the website takes the app's look; "Percentile se rank" goes, Cut off comes (as the app).

- Page: pure black (#000). Cards #121218, raised #1A1A23, lines #23232E / #30303E, text #E6E8EE, muted #8F92A3, dim #868A9C, eyebrow #9095AB, soft text #C3C6D0.
- Tiles (two a row), tool -> colour from -> to, chip, line: rank maroon #BC1F55 -> #7C1038 (#93143F, #FF9DBA); cutoff indigo #5B4BE0 -> #3323A6 (#4132BC, #B9B0FF);
  target teal #0A7B70 -> #06574F (#07665D, #6FE9D7); college blood #D10F2A -> #B00C22 (#A80B21, #FF6B78); compare gold #F2C14E -> #C98C16 (ink #1C1300, chip #FFE08A);
  dream violet #8E3BD9 -> #58169A (#6C22B5, #D2A8FF). White ink; gloss rgba(255,255,255,.22), glint .5 (gold .5 / .9). Running edges: toolEdges in theme.ts.
- Form accents: rank #B01C4F (text #FF8FB1, white on it); cutoff #2DE1C2; target #B5F23D; college #D10F2A (text #FF4D5E); compare #4CC3FF; dream #7B2CBF (text #B983FF). Dark words #0B0B0F on light accents.
- "Meri details" bar: baby pink #FFDCE8 -> #FFB5CE, words #0F0F12 / #5B3A46, a dotted rim with lights #FF2D7A, #FFD60A, #FFFFFF, #B45CFF; "Click" / "Edit" pill black.
- Meri details store `rank.profile.v1` = { at, jee: { marks, pct, rank, level, category, female, pwd, state }, comedk: { marks, rank }, bitsat: { score } }; saving fills every tool's saved form (most exact JEE score first: rank, percentile, marks).
- Cut off: POST /api/rank/cutoff {exam, by college|branch, key, optional marks|percentile|rank, JEE also level, category, female, pwd, state}; options GET /api/rank/cutoff/options; PDF POST /api/rank/pdf/cutoff. Saved under `rank.cutoff.v1`.
