# 01 · Overview

## 1. What is being built

Two parts of the JEELIVE.AI app, brought to the website with the same data, the same answers and the same voice.

**Rank** answers the six questions every JEE Main, BITSAT and COMEDK student asks after a paper or a mock:

| The student asks | The tool | What they get |
|---|---|---|
| "I scored this much. What is my rank?" | Rank predictor | Percentile and rank as a range, for a tough, normal and easy paper |
| "What was the cut-off of this college? Of this branch, everywhere?" | **Cut off** — NEW (`docs/11`) | Every round's 2026 cut-off for one college's branches, or for a branch's 100 most wanted colleges. With the student's own score: only the Safe, Likely and Borderline ones |
| "How many marks do I need for that college?" | Target marks | Marks needed, branch by branch and round by round |
| "Which colleges can I get?" | College predictor | Up to 50 college-branches tagged Safe, Likely or Borderline, each with every counselling round's cut-off |
| "This college or that one?" | College compare | Two or three colleges, or branches, side by side |
| "How far am I from my dream?" | Dream college | Up to five dream seats per exam, measured against the student's mock scores |

Above the six tools sits **Meri details** — NEW (`docs/12`): the student types their marks, percentile, rank and
category once, and every tool starts from those values. Each tool can still be changed on its own.

A student who has only an NTA percentile or a scorecard rank types it straight into the College predictor or Cut off:
every JEE Main form now takes marks, a percentile **or the All India Rank**. The earlier "Percentile se rank" tile is
gone from the app; Cut off stands in its place in the grid (`WHATS_NEW.md`).

**Mission** is the product's promise and its growth loop on one page. A short letter from the maker says the product is
100% free and asks the student to share it. Each student gets a personal link. When a friend opens that link, the
student's page says so: "Aapne 12 logon ki free education mein help ki." After a test, the result opens with one share.

## 2. How the pieces fit

```
                          ┌─────────────────────────────────────────────────────────┐
                          │                JEELIVE.AI app server                    │
                          │           https://jeelive-mobile.emergent.host          │
                          │                                                         │
  Mobile app  ───────────►│  /api/rank/*        public · in-memory · a few ms       │
                          │      rank_predictor.py  rank_comedk.py  rank_bitsat.py  │
                          │      rank_tools.py      rank_cutoff.py  rank_pdf.py     │
  Website backend ───────►│      rank_data/  (5 files, loaded once at start)        │
   (connector file)       │                                                         │
                          │  /api/rf/access     session cookie -> 15-minute pass    │
                          │  /api/rf/mission/me signed-in · MongoDB                 │
  A friend's browser ────►│  /api/j/{code}      public · counts once · redirects    │
                          │  /api/rf/dream*     signed-in · MongoDB                 │
                          └───────────────┬─────────────────────────────────────────┘
                                          │ "who is this student?"  GET /api/auth/me
                                          ▼
                          ┌─────────────────────────────────────────────────────────┐
                          │        JEELIVE.AI website   https://jeelive.ai          │
                          │        the only place that checks phone + PIN           │
                          └─────────────────────────────────────────────────────────┘
```

Three facts explain the whole design:

1. **Rank needs no account and no database.** Every answer is a lookup over five data files held in memory. A request
   never reaches a government site. That is why answers come back in a few milliseconds and why the endpoints are public.
2. **The website owns identity.** The app server stores no phone number, PIN or password. To know who a student is, it
   asks the website's own `GET /api/auth/me` with the student's session, then issues its own short pass.
3. **Mission counts on one server.** Links, visits and counts live in the app server's database, so a student sees the
   same number in the app and on the website.

## 3. Principles behind every answer

These are product decisions, not accidents. The website should keep all of them.

- **Honest ranges.** Marks do not fix a rank; the shift's difficulty and ties move it. The server returns a best and a
  worst estimate and judges every seat against both.
- **Official numbers only, with their source.** Cut-offs are the published 2026 opening and closing ranks. Where an
  official body publishes nothing (COMEDK marks-to-rank, JAC Delhi's last two rounds), the answer says so in plain words.
- **Three plain labels.** Safe, Likely, Borderline. A seat that is out of reach is not listed; the five nearest misses
  are shown separately with what it would take ("lagbhag +5 marks aur").
- **The student's real seat path.** Category, gender, PwD and home state decide which seats a student may take. The
  server applies those rules and names the path it used ("Home state · OBC-NCL").
- **Sentences ship with the data.** Notes, hints and errors come from the server already written, so every client says
  the same thing.
- **Nothing heavy on the client.** No data file is bundled; PDFs are drawn on the server; cards are text, gradients and
  SVG. The website keeps the same discipline.
- **The data lives on the app server only.** The website never writes, imports or stores the college data. Every
  college, branch, cut-off, seat and fee arrives from the app server when a student asks (`docs/05_RANK_DATA.md` §1).

## 4. What to expect

| | |
|---|---|
| Speed | 1–10 ms on the server per Rank call (two heavier ones about 80 ms); 150–600 ms seen from outside including the network (measured 155–560 ms on the live server while this pack was built). PDFs about 50 ms each on the server. |
| Size | `meta` 6 KB; a college list page 10–15 KB; a college sheet 5–20 KB; a PDF 25–70 KB; the Cut off pickers 62 KB (11 KB compressed); a Cut off branch list 64 KB (8 KB compressed). Answers over 1 KB are compressed. |
| Availability | Rank has no outside dependency once the server is up. Mission and Dream college need the database, and sign-in needs the website's `/api/auth/me`. |
| Stability | Field names in this pack are what the released Android app reads. They are changed only by adding. |
| Coverage | JEE Main: 115 institutes (32 NITs, 26 IIITs, 53 GFTIs, 4 JAC Delhi colleges), 750 programs, 10,733 seat rows over 7 rounds. COMEDK: 148 colleges with General Merit allotment, 880 college-courses, 4 rounds. BITSAT: 50 programs on 3 campuses, 5 years. IITs are not covered (they admit through JEE Advanced). |

## 5. The shape of the work for the website

| Layer | Effort | Notes |
|---|---|---|
| Connection | minutes | One backend file, two frontend files, all in `CONNECT/` |
| Rank screens | the main work | Six tools; forms, cards, lists, bottom sheets, tables. `docs/06_RANK_UI_SPEC.md`; Cut off (new) in `docs/11_CUT_OFF_NEW.md` |
| Meri details | small | One bar above the tiles, kept in the browser only; ready logic in `CONNECT/frontend_web/rankProfile.ts`. `docs/12_MERI_DETAILS_NEW.md` |
| Mission page | small | One page, one card, one panel, share buttons. `docs/07_MISSION.md` |
| Sharing | medium | Card picture + caption + the student's link, with graceful fallbacks. `docs/07_MISSION.md` §7 |
| Dream college | medium, optional at first | Needs sign-in and a small local store. `docs/08_DREAM_COLLEGE.md` |

## 6. One source, by design

There is no "copy the data" option. When the app project publishes new cut-offs, the website shows them the same
minute without a release. `RANK/code/server_reference/` holds the server's algorithm code so the team can read how an
answer is made; it is reference only and is not run by the website.
