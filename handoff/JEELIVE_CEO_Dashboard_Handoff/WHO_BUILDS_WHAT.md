# 13 · App update for the website agent: All India series on the app, and who builds what

> Written by the app-side agent on 23 Nov 2026, after the Cut off pack. Read this before starting new work, so that
> three builders (app, website, CEO dashboard) never build the same thing twice or change each other's part.
> Travels in the website pack as `docs/13_…`; the source is `/app/memory/WEBSITE_AGENT_BRIEF.md` in the app project.

## 1. Who builds what (the one table to keep)

| Part | Owner | Where it lives | Others may |
|---|---|---|---|
| Accounts: signup, phone number, PIN, session, which exam | **website** | jeelive.ai backend | read through the website's own API only |
| Papers, attempts, grading, results, solutions, pictures | **website** | jeelive.ai backend | the app shows them; it never grades or stores them |
| All India series: schedule, each day's paper, live window, result time, streak, history | **website** | jeelive.ai backend (`/series/all-india-jee…`) | the app shows them exactly as served |
| Rank: every college, cut-off, rule, tag, sentence, PDF | **app** | app server `/api/rank/*` | the website shows them through the connector; never copies data, never recomputes |
| Mission links and counts, Dream college | **app** | app server | the website shows them through the connector |
| App engagement (active, streak, coins, Rapid Fire) | **app** | app server | the CEO dashboard reads `/api/ceo/*` |
| App screens (Expo) | **app** | app project | — |
| Website pages | **website** | website project | — |
| CEO dashboard (pages, its own login, its own copy of numbers) | **CEO dashboard project (new)** | its own project | reads the two servers; **writes to neither** |

Four rules:

1. **One owner per fact.** A phone number is the website's. A closing rank is the app server's. Nobody keeps a second copy to edit.
2. **Change only your own project.** If you need something from another part, ask for it in a document like this one; do not reach in.
3. **A contract changes in writing first.** Field names in an answer only grow; a field is never renamed or removed without the reader's owner agreeing.
4. **The dashboard is read-only.** It never writes to the website or the app server, and never holds a PIN.

## 2. What the website agent has to do now

| # | Task | Size | Read |
|---|---|---|---|
| 1 | **CEO signups export** on the website backend: `GET /api/ceo/signups` and `GET /api/ceo/signups/daily`, bearer-protected, read-only, with the canonical `uid` in every row | small | `docs/14_CEO_DASHBOARD.md` §4 and §6 |
| 2 | **Cut off additions**, only if the website's Cut off page exists or is being built: replace the connector file and the browser client, then add the last-year arrow, the Compare toggle and the two PDF buttons | small | `docs/11_CUT_OFF_NEW.md` §13, `WHATS_NEW.md` §6 |
| 3 | **Confirm three facts** about the series API (below, §3.6). No code, one reply | tiny | §3.6 |
| 4 | Optional, owner's call: give the website's own series page the same behaviour as the app (§3) | medium | §3 |

**No website API change is needed for the app's series work.** The app only reads what the website already serves.

## 3. All India series on the app: what changed (23 Nov 2026)

The series page of the app (`/live`) and one new screen. Everything is drawn from the website's three answers
(`GET /series/all-india-jee`, `…/streak`, `…/history?page=N`); the app adds no rule of its own about time, marks or
eligibility.

### 3.1 Words

- **The day's attempt** = the day's live attempt (`mode: "series_live"`); for a day that was missed, the newest archive
  practice of that day's paper (`mode: "series_practice"`). Live always wins when both exist.
- **Scored** = that attempt has `summary: {score, maximum}`. **Sealed** = submitted, `status: "embargoed"`, no summary yet.
- **Result time** = the day's `closes_at` shown in India time (11:59 PM today, from the website's schedule; never typed into the app).

### 3.2 Marks on the day button

Every day button in the "All days" strip shows `score/maximum` (for example `210/300`) under the day number once the
day's attempt is scored. A sealed, running or missed day shows only its number. A practised missed day shows its
practice marks.

### 3.3 What a tap on a day does (strip button and 50-day map cell alike)

| The day | Tap |
|---|---|
| has a scored or sealed attempt | opens that attempt's analysis (the result screen) |
| has a running attempt | resumes it |
| is over, was missed, and its slot says `can_start` with a `set_id` | a small sheet **"Is din ka test shuru karein?"** → **Haan, shuru karo** starts it at once; **Abhi nahi** closes the sheet |
| is today and not attempted | only selects the day; today's live paper starts from its card and its full rules page, as before |
| is still to come | only selects the day (its card shows when it opens) |

The start after "Haan" is the same checked start as everywhere: device check (`POST /sets/{id}/preflight`), then
`POST /sets/{id}/start` with `{start_key, device_checked: true, preview: false, get_ready: true}`, then the 60-second
get-ready and the timer. There is no second Start button to press. If the start is refused, the paper's own page stays
open with the server's sentence and its usual Start button. For a slot in `state: "archive"` the sheet also says that
this is a practice attempt and does not count in the live streak or the live result.

### 3.4 The blood-red button on the cards

A glossy blood-red button with a glass glint crossing corner to corner and five colours running round its edge.

| Where | State | Button says |
|---|---|---|
| Today's card | today's paper submitted, sealed | **Aaj ka result {result time}** / second line: **Pichhla attempt · Day N: 244/300** (the newest scored day before today); with no earlier scored day: "Result {result time} par khulega" |
| Today's card | today's result released | **Aaj ke marks 232/300** / second line "Analysis dekho" |
| The selected day's card | scored | **Analysis dekho**, with the marks beside it ("MARKS", or "PRACTICE MARKS" for a practised missed day) |
| The selected day's card | sealed | **Result {result time}** |

A tap opens that attempt's analysis. A practised missed day keeps its "Practise this paper" button under the red one.

### 3.5 The AITS Analysis list (new screen, `/series-analysis`)

- Reached from "AITS Analysis" beside "My results" on the series page.
- One card per day that has an attempt, **newest day first**. Each card: `DAY 5 · 1 DEC · LIVE` (or `PRACTICE`), the
  paper's title, **four facts** (Day · Date · Score · Status; a sealed day shows "—" for the score and the result time
  under "Result at"), and **one** blood-red button: "Analysis dekho", "Result {result time}" for a sealed day, or
  "Attempt resume karo" for a running one.
- **Back path:** an analysis opened from a day (button, card or map) goes back to this list, and this list goes back
  to the series page. An analysis opened from the list goes back to the list. Android's own back button follows the
  same path.

### 3.6 What the app relies on (please confirm, website agent)

These are read from the field names and from the app's existing behaviour. The live series starts on 9 Dec 2026, so
none of this could be seen with real series data yet; it was checked in a test browser with made-up series answers
(nothing sent to the website).

1. A past day that can still be taken arrives as a slot with `state: "archive"`, `can_start: true` and its `set_id`,
   and starting it makes an attempt with `mode: "series_practice"` and the same `series_date`. **Is that right?**
2. A history item has `mode`, `series_date`, `status`, `resumable`, and `summary: {score, maximum}` only once the
   result is released; a submitted live attempt reads `status: "embargoed"` until the day's `closes_at`. **Is that right?**
3. `POST /sets/{id}/start` accepts `get_ready: true` for an archive practice exactly as for a live paper. **Is that right?**

If any of these is different, say so and the app will follow the website; do not change the website to fit the app.

Fields the app reads, so please do not rename them:
`Series {first_date, last_date, total, today, server_now, slots[]}` · `Slot {day, date, state, ready, set_id, title,
can_start, opens_at, last_start_at, closes_at}` · `Streak {stage, completed_count, current_streak, best_streak,
total_days, today_state, days[{day, date, state, attempt_id}], milestones[]}` · history item `{id, title, mode,
series_date, status, resumable, remaining_seconds, summary{score, maximum}}`.

### 3.7 If the website's series page gets the same behaviour

Same rules as §3.2 to §3.5, same words. Decide everything from the same three answers; add no clock or marks rule in
the browser. The colours of the red button are in the app's `theme.ts` (`custom_chipBlood` `#C1121F` →
`custom_chipBloodDeep` `#8A0B15`, white words; edge colours `bloodEdge`).

## 4. Cut off: what grew (detail in `docs/11` §13)

- Each row of `POST /rank/cutoff` now also carries `trend` (last-year arrow) and `save` (the row as a shortlist item).
- New `POST /rank/pdf/cutoff`: the body is the same as the list's; the PDF is the list on screen.
- On the app: arrow and **＋ Compare** toggle at the foot of every card; **PDF WhatsApp** and a PDF button under the heading.
- All of it reaches the live app server with the app project's next publish (the same publish that brings Cut off itself).

## 5. CEO dashboard (detail in `docs/14_CEO_DASHBOARD.md`)

- The app server now has `GET /api/ceo/overview` and `GET /api/ceo/users` (bearer token, read-only): engagement only.
- **The app holds no phone numbers.** The contact list for marketing can only come from the website: task 1 in §2.
- The dashboard joins the two on the canonical `uid`. That one field must be the same id on both sides.
