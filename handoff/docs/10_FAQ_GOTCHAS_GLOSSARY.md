# 10 · FAQ, gotchas and glossary

## FAQ

**Can we copy the college data into our database? It would be faster.**
No. The data lives on the app server only (`docs/05` §1). A Rank answer takes a few milliseconds on the server and
150–600 ms from outside; that is fast enough, and the connector caches the lists. One copy means one truth and one
yearly renewal.

**Can we show the numbers from `RANK/api_examples/`?**
No. They are frozen samples for design and typing.

**Can the browser call the app server directly?**
For Rank only, and only from `https://jeelive.ai` (the one origin the live server allows today). Mission and Dream
college need the connector because the session cookie is HttpOnly. The connector is the recommended path everywhere.

**Why does marks → rank give a range?**
Ties and the paper's difficulty move a rank. The server returns `[best, worst]` and judges every seat against both
(`docs/04` §3, §6).

**Why no shift picker?**
Next year's shifts will not match 2026 dates. The student picks Tough / Normal / Easy instead.

**Why is a CSAB-only seat never Safe?**
CSAB Special rounds fill leftover seats; reaching one is never certain.

**A student says their category rank is wrong.**
NTA publishes no category rank table; category and PwD ranks are labelled estimates (`docs/04` §4). Show the note.

**Why did the count not go up when I opened my own link?**
It counts each browser once, and never scripts or link previews. Test with a fresh browser profile on a real browser.

**Where is the fee for NITs?**
JoSAA publishes no college fee; the compare screen says where to look.

**Will field names change?**
Only by adding fields. The released Android app reads the same names.

**Where did "Percentile se rank" go?**
Its tile became **Cut off** (new, `docs/11`). A percentile is now typed into Cut off's score box or the College
predictor's form, and both show the rank it stands for. `POST /rank/percentile` still answers for older app versions;
do not build a page for it.

**Is Cut off on the live server?**
It reaches the live server with the app project's next publish. Until then it answers on the development server
(`README.md`). `python CONNECT/connect_check.py` tells you today: `WAIT` = not yet, `PASS` = yes.

**BITSAT has no round-wise cut-offs in Cut off. Is something missing?**
No. BITS publishes only one final cut-off score per program per year. The boxes are the five years 2022 … 2026; never
label them R1, R2 … (`docs/11` §4.3).

**A student typed marks, a percentile and a rank. Which one counts?**
The most exact: rank, then percentile, then marks. The result's `source` says which. The form says so as soon as two
boxes are filled.

**If the student changes their category inside one tool, does "Meri details" change?**
No. Meri details gives starting values; each tool is then edited on its own (`docs/12` §1).

## Gotchas

- `state` must match `meta.states` exactly (`"Jammu & Kashmir"`, `"Dadra & Nagar Haveli and Daman & Diu"`); an unknown
  state is a 422.
- Unknown `branches` names are dropped silently; take them from `meta.branches` / `meta.comedk.groups`.
- `page` is only 1 or 2; `page_size` only 20 or 25.
- JEE Main: send at least one of `marks`, `percentile`, `rank`. With several, the rank decides, then the percentile,
  then the marks. COMEDK: `marks` **or** `rank` (the rank decides); never a percentile. BITSAT: the score only.
- Cut off: send `key` back exactly as `GET /rank/cutoff/options` gave it (a JEE college key is a number **as text**).
- Cut off: skip a cell with `na: true` (JAC Delhi has four rounds); a `null` closing is a dash, not a zero.
- Cut off: a CSAB box is never green, and a branch list is at most 100 rows while `eligible` counts the whole list.
- Cut off: show an answer only while its `exam`, `by` and `key` equal the student's current choice.
- Meri details and every tool's saved form live in the browser only; never send them to a server or to analytics.
- `inst` and `prog` are numbers; in `compare/colleges` the JEE `id` is the institute number **as a string**.
- A JEE compare item needs the card's `path` sentence exactly as received.
- Ranges are `[better, worse]`: the smaller rank first.
- Never fetch `/api/j/{code}` from a server; always let the friend's browser open it.
- Keep the share link base the same once students have shared links.
- Show the server's sentences as they are (Hinglish, the app's voice). Do not translate.
- PDF requests can take up to 30 s on a slow network; show a busy state.
- The app server's own signed-in errors (401 when the pass is missing or expired, a rare 503 during a short server
  maintenance) are worded for the app. The connector replaces them with "Please sign in again." and
  "Abhi load nahi hua. Thodi der mein dobara try karo.", so the website never shows them.

## Glossary

| Term | Meaning |
|---|---|
| CRL | Common Rank List: the All India rank across all categories |
| Category rank | rank among the student's own category (EWS, OBC-NCL, SC, ST) |
| PwD | Persons with Disabilities seats and rank |
| JoSAA | Joint Seat Allocation Authority: counselling for NITs, IIITs, GFTIs (Rounds 1–5 in 2026) |
| CSAB | Central Seat Allocation Board: Special rounds after JoSAA for leftover seats (CSAB 1, CSAB 2) |
| JAC Delhi | Joint Admission Counselling for DTU, NSUT, IIIT-Delhi, IGDTUW (Rounds 1–4, Upgrade, Spot) |
| GFTI | Government Funded Technical Institutes |
| HS / OS / AI | Home state / Other state / All India quota |
| DL / OD | Delhi region / Outside Delhi (JAC Delhi) |
| GO / JK / LA | Goa / Jammu & Kashmir / Ladakh quotas |
| Opening / closing rank | best / worst rank admitted to a seat in a round |
| Demand | how early a seat fills; the list is ordered by it |
| GM | General Merit: COMEDK's All India seats (the only ones covered) |
| KKR | Kalyana Karnataka quota (not covered) |
| Paper type | Tough / Normal / Easy: how hard the student's shift was |
| Safe / Likely / Borderline | the three chance tags (`docs/04` §6) |
| Near miss | a seat just out of reach, with what it would take |
| Cut off | (new) the tool that shows every round's cut-off of one college or one branch; also the closing rank or score itself |
| Eligible | (Cut off) a row with a tag for the student's score: Safe + Likely + Borderline |
| Meri details | (new) the student's score and category typed once above the tiles; starting values for all six tools |
| Scorecard rank | the All India Rank (CRL) printed on the NTA scorecard; the `rank` field of the JEE Main form |
| Path | the quota + category + gender + PwD combination a seat belongs to |
| Pass | the app server's 15-minute token for signed-in calls |
| Connector | `CONNECT/backend_fastapi/jeelive_app_connect.py`, the website's bridge to the app server |
