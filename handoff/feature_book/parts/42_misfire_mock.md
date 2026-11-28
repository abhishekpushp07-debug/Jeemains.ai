## 4.8 Misfire Mock made by the website: built in the app, shut until its switch

**Built in the app on 28 Nov 2026, and shut until the website opens it.** The owner decided (28 Nov 2026) that a Misfire mock taken **on the website and in the app alike** must be the website's own paper. So the app asks the website to make it, and from then on it is an ordinary paper on both sides: its page, its timer, autosave, its result, its Analysis, My Tests. **Until door A says `"misfire": true`, no student sees any of it.** The app was checked with the switch off and with it on.

| Decision | Date |
| --- | --- |
| A Misfire mock for both sides is the website's paper, made by door C with `mode: "misfire"` | 28 Nov 2026 (the owner) |
| Its switch is `misfire` in door A, shut unless it is exactly `true` | 28 Nov 2026 |
| Its result says how many of its questions went to "Samajh gaya" | 28 Nov 2026 |
| Offline Misfire (Part 4.7) stays as it is, next to it | 28 Nov 2026 |

[[shots: x07_mock_tab | 20. Switch on: Misfire's "Mock" tab ; x08_mock_setup | 21. Its setup asks jeelive.ai for the paper ; x09_mock_paper | 22. The made paper's page ; x10_mock_result | 23. Its result: how many went to "Samajh gaya"]]

The pictures are from the app's preview, with the browser answering in place of the website: the website's doors for the Misfire Mock do not exist yet. The scores in them belong to a paper played as a Misfire Mock.

**What a student sees, once the switch is on**

- Misfire gets a tab **"Mock"**, right after "Sab" (then "Offline Misfire" and the paper-wise tabs). Its dark-red card: "MISFIRE MOCK · Galtiyon se JEE Main mock · Paper jeelive.ai par banega: timer, autosave, result aur Analysis har paper ki tarah. App aur website, dono par chalega. Jo sahi karoge, woh “Samajh gaya” ho jayenge.", the button **"Naya mock banao"**, then the student's Misfire Mocks, newest first: a finished one with its score and its right, wrong and left counts ("Result dekho"), one being taken marked "CHAL RAHA HAI" ("Resume").
- **"Naya mock banao"** opens the setup of Part 4.7, titled "Misfire Mock banao", with the website's open Misfire list only (never the phone's papers). The time it shows comes from door A's minutes (the owner's ratio).
- **"Mock banao"** asks door C. While it waits: "jeelive.ai aapki galtiyon se paper bana raha hai…". Then the made paper's page opens ("JEE MAIN · MISFIRE MOCK"), and the student starts it like any paper.
- **The result** of a paper whose `test_kind` is `misfire` has a card on its Analysis tab: "3 / 15 sawaal “Samajh gaya” mein chale gaye" and "Jo sahi kiye, woh Misfire ki list se hat gaye. Baaki galtiyan wahin hain, agle mock ke liye.", with "Misfire kholo". Its top line reads "JEE Main · Misfire Mock".
- **My Tests** shows "JEE Main · Misfire Mock" under the paper's name.
- **The Dream College meter never counts it**, like a chapter test and a Student Choice paper.

### What the website builds

The doors are Student Choice's (Part 1.6); the Misfire Mock only adds to them. The JSON is also in the `examples` folder (`misfire_mock_ask.json`, `misfire_mock_answers.json`).

**1. The switch, in door A** (`GET /api/choice/bank?exam=jee-main`). Add `"misfire": true`. Anything else (no `misfire`, `false`, `"true"`, `1`, or a 404) keeps the tab shut. It changes nothing about `pick` and `random`. The app's server reads door A every 2 minutes, so the tab appears (or goes) within about 2 minutes, on every phone.

**2. Make the paper: door C** (`POST /api/choice/papers`, sent with the student's own session):

{{file:examples/misfire_mock_ask.json}}

- `counts`: 0 to 25 for each subject, at least 1 in all.
- `chapters`: only for a subject where the student ticked some chapters, by their names exactly as `chapters[].name` in `GET /my/misfire?status=open&subject=…`. A subject not named means every chapter.
- The questions are the student's own **open** Misfire items (never "Samajh gaya"), from those chapters. Fewer than asked: as many as there are. None at all: 422 with a plain `error.message`.
- **The same `request_key` gives the same paper.** A retry never makes a second one (rule 6). The app keeps one key while the student stays on the screen with the same counts and chapters.
- The answers are door C's (Part 1.6): `{ "set_id": "…" }` with 200 or 201. 404 or 405: "not built yet" ("Paper banana abhi jeelive.ai se jud raha hai…"). 409, 422 or 429 with `error.message`: that sentence is shown. 5xx: "jeelive.ai abhi jawab nahi de raha. Thodi der mein dobara try karo; aapki ginti aur chapters yahin rahenge."

**3. The paper.** A set of the student's own, `test_kind: "misfire"`, exam JEE Main, marked +4 / −1 / 0 and timed by the ratio (rule 5; a made paper is not cut). Every question has its own subject, pieces, key and solution, so that the paper's page, start, player, autosave, deadline, result and Analysis work unchanged, in the app and on the website.

**4. Its list.** `GET /api/exam-navigation/jee-main/history?kind=misfire&page=`: the student's Misfire Mocks, newest first, with the rows of the other history lists (`id` of the attempt, `title`, `started_at`, `submitted_at`, `summary {score, maximum, correct, incorrect, skipped}`), plus `status` and `resumable` on one still being taken. And `test_kind: "misfire"` on its rows in `GET /api/my/tests`.

**5. Its result.** `GET /api/attempts/<id>/results` carries `test_kind: "misfire"` and `"misfire": { "understood": 3, "total": 15 }`: how many of its questions **the website moved to "Samajh gaya"** because they were answered right, out of how many. The website moves them; the app only shows the number. Without `misfire`, the card says a general sentence instead.

{{file:examples/misfire_mock_answers.json}}

**6. A question for the website.** A wrong or left question of a Misfire Mock is already an open Misfire item, under the id of the paper it first came from (`<attempt id>:<question id>`). The app expects it **not** to become a second item under the Misfire Mock's own attempt. Please tell the app side what the website does.

**Until all of this is ready, keep `misfire` off.** Then tell the app side: the first real end-to-end run is on a test setup, before students see it (rule 20). On the app side, door A's `misfire` reaches production with the owner's next Publish; nothing else waits for the app.

**Checked on 28 Nov 2026** (`tests/misfire_web_check.py`, 30 checks; the browser answered in place of the website, and nothing was written). With the switch as the website answers today (not said): no tab, and nothing changed anywhere (Misfire's tabs, a link to `?tab=web`, the setup, Student Choice); door C never asked. With the switch on: the tab right after "Sab"; the list (a finished mock with its score, one being taken with "Resume"); the result's count; the setup asking door C (404, then 503, then a paper) with **one** `request_key` for all three; the chosen chapters sent by name, under a new key; the made paper's page; My Tests' label; Offline Misfire unchanged. On the app's server, `misfire` is `true` only for an exact `true` (`backend/tests/test_choice.py`). The app side's independent review found no fault in the app.

**Not checked:** anything against a real website door (none exists yet); a Misfire Mock started on the website and finished in the app, or the other way round; a real phone.
