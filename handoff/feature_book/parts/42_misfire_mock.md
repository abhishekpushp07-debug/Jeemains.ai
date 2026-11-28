## 4.8 Misfire Mock made by the website: built in the app, shut until its switch

**Built in the app on 28 Nov 2026, and shut until the website opens it.** The owner decided (28 Nov 2026) that a Misfire mock taken **on the website and in the app alike** must be the website's own paper. So the app asks the website to make it, and from then on it is an ordinary paper on both sides: its page, its timer, autosave, its result, its Analysis, My Tests. **Until door A says `"misfire": true`, no student sees any of it.** The app was checked with the switch off and with it on.

| Decision | Date |
| --- | --- |
| A Misfire mock for both sides is the website's paper, made by door C with `mode: "misfire"` | 28 Nov 2026 (the owner) |
| Its switch is `misfire` in door A, shut unless it is exactly `true` | 28 Nov 2026 |
| Its result says how many of its questions went to "Samajh gaya" | 28 Nov 2026 |
| Offline Misfire (Part 4.7) stays as it is, next to it | 28 Nov 2026 |
| The website and the app agreed every door, answer and sentence below (the website's contract: its `memory/MISFIRE_MOCK_CONTRACT.md`) | 28 Nov 2026 (the website and the app side) |
| A Misfire Mock's result is not counted in Misfire's chapter report; a question already "Samajh gaya" that is wrong in the mock stays "Samajh gaya" | 28 Nov 2026 (the website) |

[[shots: x07_mock_tab | 20. Switch on: Misfire's "Mock" tab ; x08_mock_setup | 21. Its setup asks jeelive.ai for the paper ; x09_mock_paper | 22. The made paper's page ; x10_mock_result | 23. Its result: how many went to "Samajh gaya"]]

The pictures are from the app's preview, with the browser answering in place of the website: the website's doors for the Misfire Mock do not exist yet. The scores in them belong to a paper played as a Misfire Mock.

**What a student sees, once the switch is on**

- Misfire gets a tab **"Mock"**, right after "Sab" (then "Offline Misfire" and the paper-wise tabs). Its dark-red card: "MISFIRE MOCK · Galtiyon se JEE Main mock · Paper jeelive.ai par banega: timer, autosave, result aur Analysis har paper ki tarah. App aur website, dono par chalega. Jo sahi karoge, woh “Samajh gaya” ho jayenge.", the button **"Naya mock banao"**, then every Misfire Mock of the student's, newest first, with its size ("15 sawaal · 32 min"): one not started yet, "SHURU NAHI HUA" ("Shuru karo", its paper's page); one being taken, "CHAL RAHA HAI" ("Resume"); a finished one with its score and its right, wrong and left counts ("Result dekho").
- **"Naya mock banao"** opens the setup of Part 4.7, titled "Misfire Mock banao", with the website's open Misfire list only (never the phone's papers). The time it shows comes from door A's minutes (the owner's ratio).
- **"Mock banao"** asks door C. While it waits: "jeelive.ai aapki galtiyon se paper bana raha hai…". Then the made paper's page opens ("JEE MAIN · MISFIRE MOCK"), and the student starts it like any paper. When fewer questions came than were asked, it says so first: "Aapne 15 sawaal maange the, 12 mile: chune hue chapters mein itne hi khule sawaal the.", with "Paper kholo".
- **The result** of a paper whose `test_kind` is `misfire` has a card on its Analysis tab: "3 / 15 sawaal “Samajh gaya” mein chale gaye" and "Jo sahi kiye, woh Misfire ki list se hat gaye. Baaki galtiyan wahin hain, agle mock ke liye.", with "Misfire kholo". A retry of the wrong questions changes nothing in Misfire, so its result has no card. The top line reads "JEE Main · Misfire Mock".
- **My Tests** shows "JEE Main · Misfire Mock" under the paper's name.
- **The Dream College meter never counts it**, like a chapter test and a Student Choice paper.

### What the website builds

The doors are Student Choice's (Part 1.6); the Misfire Mock only adds to them. The JSON is also in the `examples` folder (`misfire_mock_ask.json`, `misfire_mock_answers.json`).

**1. The switch, in door A** (`GET /api/choice/bank?exam=jee-main`). With only the Misfire Mock open it answers `200 { "pick": false, "random": false, "misfire": true, … }`; Student Choice then stays exactly as today (`pick` and `random` false = shut), and only Misfire's "Mock" tab opens. Anything else (no `misfire`, `false`, `"true"`, `1`, or the 404 of all switches off) keeps the tab shut. Door A answers 401 without a student's cookie. The app's server reads door A every 2 minutes, so the tab appears (or goes) within about 2 minutes, on every phone.

**2. Make the paper: door C** (`POST /api/choice/papers`, sent with the student's own session):

{{file:examples/misfire_mock_ask.json}}

- `counts`: 0 to 25 for each subject, at least 1 in all; a subject left out counts as 0.
- `chapters`: only for a subject where the student ticked some chapters, by their names exactly as `chapters[].name` in `GET /my/misfire?status=open&subject=…`. A subject not named means every chapter; a name not in the student's open list brings no question.
- The questions are the student's own **open** Misfire items (never "Samajh gaya") of Physics, Chemistry and Mathematics, from JEE Main and BITSAT papers alike; the paper's exam is JEE Main. A question listed twice comes once; answered right, both entries go to "Samajh gaya".
- **The same `request_key` gives the same paper.** A retry never makes a second one (rule 6). The app keeps one key while the student stays on the screen with the same counts and chapters, and takes a new one when they change.
- The answer (200 or 201): `{ "set_id", "title", "number", "asked", "given", "minutes" }` (the whole example below). When `given` is less than `asked`, the app says so before the paper opens.
- The trouble answers, each `error.message` shown word for word:

| Status | `error.message` | When |
| --- | --- | --- |
| 422 | "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno." | no open question in the chosen chapters |
| 422 | "Har subject mein 25 tak sawaal chuno, kul kam se kam 1." | counts out of bounds |
| 409 | "Misfire Mock abhi band hai." | the switch is off |
| 409 | "Yeh mock pehle hi ban chuka hai. Misfire ke Mock tab mein dekho." | the same `request_key` with another request |
| 429 | "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao." | 5 a day (apart from Student Choice's 5) |

404 or 405 mean "not built yet" ("Paper banana abhi jeelive.ai se jud raha hai…"); 5xx: "jeelive.ai abhi jawab nahi de raha. Thodi der mein dobara try karo; aapki ginti aur chapters yahin rahenge."

**3. The paper.** A set of the student's own, `test_kind: "misfire"`, exam JEE Main, marked +4 / −1 / 0 and timed by the ratio (rule 5; a made paper is not cut). Every question has its own subject, pieces, key and solution, so that the paper's page, start, player, autosave, deadline, result and Analysis work unchanged, in the app and on the website. `test_kind: "misfire"` also on its rows in `GET /api/my/tests`.

**4. Its list.** `GET /api/my/misfire/mocks?page=`: every Misfire Mock of the student's, **those not started too** (5 can be made a day, so each must be findable), newest first, 20 a page; `attempt` is its newest attempt, or `null`. The app opens one not started at its paper's page, one being taken (`resumable`) in the paper, and any other at its result. (`history?kind=misfire` is not built: the history lists only attempts.)

**5. Its result.** `GET /api/attempts/<id>/results` carries `test_kind: "misfire"` and, once the result is ready (with the score), `"misfire": { "understood": 3, "total": 15 }`: how many of its **questions** (not entries) the website moved to "Samajh gaya" because they were answered right, out of how many. A retry of the wrong questions changes nothing in Misfire, and its result has no `misfire`. A fresh attempt of the same mock moves right answers again.

{{file:examples/misfire_mock_answers.json}}

**6. What the website decided** (28 Nov 2026): a Misfire Mock's result is **not counted** in Misfire's chapter report, so one question is never counted twice; a question already "Samajh gaya" before the mock and wrong in it **stays** "Samajh gaya"; a question wrong or left in the mock does not become a second Misfire item, and stays open under its first id `<attempt id>:<question id>`.

**Until all of this is built, keep `misfire` off.** Then tell the app side, with the switch still off: the first real end-to-end run is on a test account (rule 20), and only then the switch goes on. On the app side, door A's `misfire` reaches production with the owner's next Publish; nothing else waits for the app.

**Checked on 28 Nov 2026** (`tests/misfire_web_check.py`, 37 checks, to the agreed contract; the browser answered in place of the website, and nothing was written). With the switch as the website answers today (not said): no tab, and nothing changed anywhere (Misfire's tabs, a link to `?tab=web`, the setup, Student Choice); door C never asked. With the switch on: the tab right after "Sab"; the list (one not started, newest first, opening its paper's page; one being taken with "Resume"; a finished one with its score and size); the result's count, and no card on a retry's result; the setup asking door C (404, then 503, then a paper) with **one** `request_key` for all three; the five sentences of the table word for word; "maange 5, mile 3" before the paper; the chosen chapters sent by name, under a new key; the made paper's page; My Tests' label; Offline Misfire unchanged. On the app's server, `misfire` is `true` only for an exact `true` (`backend/tests/test_choice.py`).

**Not checked:** anything against a real website door (none exists yet); a Misfire Mock started on the website and finished in the app, or the other way round; a real phone.
