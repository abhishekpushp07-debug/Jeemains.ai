# JEELIVE.AI · Rank + Mission

### Website hand-off pack

Everything the website needs to offer the app's **Rank** tools and **Mission** page: the documentation, a ready-made
connector to the live app server, the server's algorithm code to read, the app's screen code, real API answers,
sample PDFs and fresh screenshots.

**The data is not in this box, on purpose.** Every college, branch, cut-off, seat and fee lives on the app server and
reaches the website through its API when a student asks. The website never writes the data separately. When new
cut-offs are published, the app server is updated once and the website shows them the same minute.

Rapid Fire is deliberately not part of this pack.

| | |
|---|---|
| Live app server | `https://jeelive-mobile.emergent.host/api` |
| Development server | `https://scale-engine-50k--0gu36hlx.preview.emergentagent.com/api` (may sleep or change; use it only to test unreleased work) |
| Data (served live) | JEE Main 2026 (JoSAA, CSAB, JAC Delhi), COMEDK UGET 2026, BITSAT 2022–2026 |
| Verified | all 21 public checks pass on the live server (`CONNECT/connect_check.py`) on the day of this build |
| Build facts | `MANIFEST.json` (build time, every file with its size and SHA-256) |

---

## The 10-minute start

```bash
# 1. Prove the live server answers you (no account, no key, nothing to install)
python CONNECT/connect_check.py

# 2. Read one real answer
curl -s -X POST https://jeelive-mobile.emergent.host/api/rank/estimate \
  -H 'Content-Type: application/json' \
  -d '{"exam":"jee","marks":180,"level":"normal","category":"GEN","pwd":false}'
```

Then:

3. Copy `CONNECT/backend_fastapi/jeelive_app_connect.py` into the website backend and mount it (3 lines, shown at the top of the file).
4. Copy `CONNECT/frontend_web/jeeliveApp.ts` into the website frontend and call `createJeeliveApp()`.
5. Build the screens from `docs/06_RANK_UI_SPEC.md` and `docs/07_MISSION.md`.

If the website is being built by an AI agent, hand it `START_HERE_FOR_WEBSITE_AGENT.md` first.

---

## What is in the box

| Folder | What it holds | Open it when |
|---|---|---|
| `START_HERE_FOR_WEBSITE_AGENT.md` | A complete brief for the website project: the job, the order of work, the rules, the finish line | you start |
| `docs/` | Ten documents, listed below | you want to understand or decide |
| `CONNECT/` | The system that calls the app server: backend connector, typed browser client, one-command check, curl lines, OpenAPI file | you wire the website |
| `RANK/code/server_reference/` | The app server's Rank and Dream college code (read-only: it runs on the app server, never on the website) | you want to see exactly how an answer is made |
| `RANK/code/app_reference_ui/` | The app's real Rank and Dream college screens (React Native, TypeScript) | you build a screen and want the exact behaviour |
| `RANK/api_examples/` | 22 real request + answer pairs captured from the server (frozen samples, never a data source) | you design a screen or a type |
| `RANK/sample_pdfs/` | The 7 PDFs the server draws, with the request that made each | you add the PDF buttons |
| `RANK/screenshots/` | 25 fresh screens of the app's Rank tab | you design |
| `MISSION/code/` | The Mission server code (read-only) and the app's Mission screens | you build Mission |
| `MISSION/api_examples/` | Mission answers (personal values masked) and the share-link redirect | you design or type |
| `MISSION/screenshots/` | 4 fresh screens: the tab top to bottom, and the share gate | you design |

## The ten documents

| # | Document | Answers |
|---|---|---|
| 01 | `docs/01_OVERVIEW.md` | What are Rank and Mission, how do the pieces fit, what should the website expect? |
| 02 | `docs/02_CONNECT_GUIDE.md` | How does the website call the app server: addresses, the three ways to connect, sign-in, CORS, errors, caching |
| 03 | `docs/03_RANK_API_REFERENCE.md` | Every Rank endpoint: request, answer, field by field |
| 04 | `docs/04_RANK_ALGORITHMS.md` | Every formula and rule, with worked numbers |
| 05 | `docs/05_RANK_DATA.md` | What data the server holds, its official sources, why the website never copies it, how it is renewed each year |
| 06 | `docs/06_RANK_UI_SPEC.md` | The six Rank tools screen by screen: layout, words, states, colours |
| 07 | `docs/07_MISSION.md` | Mission end to end: the idea, the API, the counting rule, the data, the screens, sharing, the share gate |
| 08 | `docs/08_DREAM_COLLEGE.md` | The Dream college tool: API, the multi-device merge rule, the meter |
| 09 | `docs/09_TESTING_AND_ACCEPTANCE.md` | How to prove it works: checks, vectors, the acceptance list |
| 10 | `docs/10_FAQ_GOTCHAS_GLOSSARY.md` | The questions that will come up, the traps, and every term explained |

---

## Six rules that keep the website and the app the same

1. **Data comes from the app server.** Never write, import or store the college data on the website. Call the server
   when a student asks; cache only for minutes.
2. **Numbers come from the app server.** Never recompute a rank, a tag or a target in the browser. One source means the
   app and the website can never disagree.
3. **Show ranges, not single numbers.** A rank from marks is an estimate; the server always returns `[best, worst]`.
4. **Show the server's own sentences.** Notes, hints and error messages arrive ready to display, in the app's Hinglish
   voice. Do not rewrite or translate them.
5. **Keep the three honest labels.** `Safe`, `Likely`, `Borderline`. No other wording, no percentages of "chance".
6. **Never promise.** Every result screen carries the estimate note. 2026 cut-offs describe 2026.

## What is not here

- Rapid Fire (the game, its art, sound, question bank, sockets and shop).
- A copy of the Rank data (it is served live by the app server).
- The test player, results, analysis and the rest of the app.
- Any password, key, token or student record. API samples were captured with a test account and personal values are masked.

One clarification so nothing surprises you: the words "Rapid Fire" still appear in a few harmless places. The Mission
card and caption name it as one of the product's four promises (that is marketing copy, kept word for word); the
app server's signed-in paths live under the historical prefix `/api/rf/` (the connector hides it: the website only sees
`/api/mission/me` and `/api/dream`); and two server error sentences mention it. None of these is Rapid Fire code.
Details in `docs/10_FAQ_GOTCHAS_GLOSSARY.md` and `docs/07_MISSION.md` §10.

## What to send back to the app project

So the two projects stay connected, tell the app project:

1. the website's exact browser origins (production and preview) if you want the browser to call the app server directly;
2. whether the website's session cookie is still called `access_token` and `GET /api/auth/me` still answers with the student's `id`;
3. anything in a server answer that the website needs and does not find.
