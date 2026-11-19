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

## Gotchas

- `state` must match `meta.states` exactly (`"Jammu & Kashmir"`, `"Dadra & Nagar Haveli and Daman & Diu"`); an unknown
  state is a 422.
- Unknown `branches` names are dropped silently; take them from `meta.branches` / `meta.comedk.groups`.
- `page` is only 1 or 2; `page_size` only 20 or 25.
- Send `marks` **or** `percentile` (COMEDK: `marks` **or** `rank`). With both (JEE), the percentile decides.
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
| Path | the quota + category + gender + PwD combination a seat belongs to |
| Pass | the app server's 15-minute token for signed-in calls |
| Connector | `CONNECT/backend_fastapi/jeelive_app_connect.py`, the website's bridge to the app server |
