# Start here: brief for the website project

Paste this file into the website project's chat, or read it first if you are the developer.
It is written so that a person or an AI agent can do the whole job from this pack alone.

---

## The job in one paragraph

The JEELIVE.AI mobile app has two features the website must now offer: **Rank** (six tools that turn a student's marks
into a rank, a college list, target marks and comparisons) and **Mission** (a page that asks students to share the
product, gives each of them a personal link, and thanks them with a live count of the friends that link brought in).
The app's server already holds all the data and does all the thinking. The website builds the screens and connects to
that server through one small backend file. You do not rebuild any algorithm.

```
 Student's browser ──►  Website frontend  ──►  Website backend  ──►  JEELIVE.AI app server
                        (your screens)         (one connector file)   (data + algorithms, already live)
```

## The order of work

> **This pack has new parts.** **Cut off** is a NEW Rank tool (it took the place of the "Percentile se rank" tile),
> **Meri details** is a NEW bar above the tiles, and every JEE Main form now also takes the scorecard **rank**.
> If the website was already built from the earlier pack, read `WHATS_NEW.md` first: it lists exactly what to change.

**Step 1 · Prove the connection (2 minutes).**
Run `python CONNECT/connect_check.py`. Expect `ALL 29 CHECKS PASSED`, or `21 CHECKS PASSED, 8 WAIT` while the live server
does not have Cut off yet (it arrives with the app project's next publish; until then build Cut off against the
development server named in `README.md`). A `FAIL` line: stop and read `docs/02_CONNECT_GUIDE.md` §9.

**Step 2 · Mount the connector (10 minutes).**
Copy `CONNECT/backend_fastapi/jeelive_app_connect.py` into the website backend. Mount it under the existing `/api` router:

```python
from jeelive_app_connect import router as jeelive_app_router, close as close_jeelive_app

api_router.include_router(jeelive_app_router)
app.add_event_handler("shutdown", close_jeelive_app)
```

Add `httpx` to `requirements.txt` if it is not there. Optional settings are in `CONNECT/.env.example`; the defaults
already point at the live app server.
Check: `python CONNECT/connect_check.py https://<your-website>/api --website` passes.

**Step 3 · Add the browser client (5 minutes).**
Copy `CONNECT/frontend_web/jeeliveApp.ts` and `rankProfile.ts` into the frontend. Everything is typed:

```ts
import { createJeeliveApp } from "./jeeliveApp";
const app = createJeeliveApp();          // calls the website's own /api
const meta = await app.rank.meta();
```

**Step 4 · Build Rank.** Follow `docs/06_RANK_UI_SPEC.md` tool by tool, in this order (each one is useful alone):

1. Rank predictor (`rank.estimate`)
2. **Cut off — NEW** (`rank.cutoffOptions`, `rank.cutoff`): its own document, `docs/11_CUT_OFF_NEW.md`
3. College predictor: JEE Main (`rank.predict`, `rank.college`; the form takes marks, percentile **or rank**), then BITSAT (`rank.bitsat`), then COMEDK (`rank.comedk`, `rank.comedkCollege`)
4. Target marks (`rank.colleges`, `rank.targetJee`, `rank.targetComedk`, `rank.targetBitsat`)
5. College compare (`rank.compare`, `rank.compareColleges`)
6. PDF buttons (`rank.pdf`)
7. **Meri details — NEW** (the bar above the tiles; `rankProfile.ts`, no server call): `docs/12_MERI_DETAILS_NEW.md`
8. Dream college (`dream.*`, signed-in; `docs/08_DREAM_COLLEGE.md`)

There is no "Percentile se rank" page any more. `rank.percentile` still answers for older app versions; do not build a
screen for it.

**Step 5 · Build Mission.** Follow `docs/07_MISSION.md`: the page, the share card, the Impact panel (`mission.me`), the
share buttons with the student's own link, and, if the website shows test results, the "Share to view results" gate.

**Step 6 · Prove it.** Work through the acceptance list in `docs/09_TESTING_AND_ACCEPTANCE.md`.

## Rules

Do:

- Call the app server only from the website backend (the connector). It works from every environment and needs no CORS.
- Display the server's numbers, ranges, tags, notes and error sentences exactly as they arrive.
- Use the screenshots in `RANK/screenshots/` and `MISSION/screenshots/` as the visual reference, and the React Native
  files in `*/code/app_reference_ui/` as the behaviour reference.
- Cache `rank.meta()`, `rank.colleges()` and `rank.cutoffOptions()` for the visit; they change only when the app server is redeployed.
- Keep every form's last values in the browser's storage, as the app does, so a returning student sees their own score.
  Use the keys and shapes of `rankProfile.ts`, so "Meri details" can fill every tool.

Do not:

- Do not copy, import, scrape or store the college data (colleges, branches, cut-offs, seats, fees) on the website.
  It lives on the app server only; call it when a student asks (`docs/05_RANK_DATA.md` §1).
- Do not use the numbers in `RANK/api_examples/` on a page. They are frozen samples.
- Do not recompute ranks, tags, gaps or target marks in the browser.
- Do not fetch `…/api/j/{code}` from a server. That link must be opened by the friend's own browser, or nobody is counted.
- Do not log, store or send to analytics the student's session cookie or the 15-minute pass. The connector keeps the pass in memory only.
- Do not change the three tags (`Safe`, `Likely`, `Borderline`), the estimate notes or the Mission disclaimer.
- Do not add Rapid Fire. It is outside this hand-off.

## The finish line

- `connect_check.py --website --pdf` passes against the website's own `/api`, including the signed-in checks.
- For the same inputs, the website shows exactly what the live app server answers (`docs/09_TESTING_AND_ACCEPTANCE.md` §2).
- A signed-in student sees their Impact panel; a friend opening the student's link in a fresh browser raises the count
  by exactly one, and opening it again does not.
- Every screen works at 320 px width, with the keyboard only, and with motion reduced.

## Where to look when something is unclear

| Question | Read |
|---|---|
| What does this field mean? | `docs/03_RANK_API_REFERENCE.md`, then the matching file in `RANK/api_examples/` |
| Why is this seat "Borderline"? | `docs/04_RANK_ALGORITHMS.md` §6 |
| How does Cut off work, exam by exam? | `docs/11_CUT_OFF_NEW.md` §4; fields in `docs/03` §13 |
| What does "Meri details" write into each tool? | `docs/12_MERI_DETAILS_NEW.md` §3 |
| Where does this number come from? | `docs/05_RANK_DATA.md`, then the live answer from the app server |
| How exactly does the app behave here? | the component named in `docs/06_RANK_UI_SPEC.md`, in `RANK/code/app_reference_ui/` |
| How is a friend counted? | `docs/07_MISSION.md` §4 |
| The server said 401 / 422 / 503 | `docs/02_CONNECT_GUIDE.md` §6 |

## Report back to the app project

When the website is connected, send the app project these three lines so both sides stay in step:

```
Website origins (production, preview): ...
Session cookie name and /api/auth/me still unchanged: yes / no (what changed)
Anything missing from an API answer: ...
```
