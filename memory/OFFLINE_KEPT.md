# What the phone keeps for itself — Rapid Fire's cards and finished papers (27 Nov 2026)

Owner (27 Nov): "jo app download kare background me, sara paper download hota rahe. Sabse pehle rapid fire and jee mains ke
sare chapters and aits. Fir bitsat ke. Uske sare result bhi … offline and low internet par bhi … lightning fast."
His answers to the questions: "Jo app akela kar sakta hai, abhi" · "Mobile data par bhi sab" · "512 MB" ·
"Fark nahi padta jo chalak wo jeeta. Ye game nahi revision hai … rapid fire pura offline khela ja sakta, without any animations".

This replaces two points of the parked plan `OFFLINE_SOLUTIONS_PLAN.md` by the owner's later words: papers are kept
**by themselves** (no "Offline save" button), and the room is **512 MB with the oldest-used copy giving way** (no pinning).
Everything else of that plan stands: 7 days after the last confirmed session, sign-out removes private things, the
signed-in app is never drawn from a cached profile, never the one-picture route for a background download.

## 1. What is built

| What | On the phone | Without a line |
|---|---|---|
| Rapid Fire, all 16,158 JEE cards (Physics, Chemistry, Maths, English, Reasoning) | yes, by itself (1.8 MB download, about 7.5 MB kept) | Solo Sprint, any chapters, 30 / 50 / 100 cards, 20 s a card, Repeat missed. Plain screens, nothing moves. |
| A round played without a line | kept under the account (up to 200 rounds) | goes up by itself when the line is back; the server marks it with its own key and pays it once |
| Results of FINISHED papers (JEE Main first, then BITSAT, then the rest; newest first) | yes, by themselves: score, every question, your answer, the key, the supplied solution, all pictures | list "Mere results" and a reader |
| A result the student opens on screen | kept at once, no extra call | the same |

Not built, because the app cannot do it alone (section 6): the QUESTIONS of a paper that was not attempted yet.

## 2. Rapid Fire

- Server: `backend/rf_bank.py` — `GET /api/rf/bank?exam=JEE` (one part per subject + the hash of its bytes),
  `GET /api/rf/bank/part?exam&subject&h` (gzip; 409 when the hash is old; 401 without a pass). Built once per server
  copy, kept in memory; looked at again at most once a minute from the card files' hashes AND the ids a sprint deals
  from (so a retired card leaves the phones too). Shed first when the server is packed (`load_guard.BACKGROUND`).
  `backend/sprints.py` — `POST /api/rf/sessions/offline` {request_id, card_ids ≤ 100, results, picks?, played_at?, repeat?}:
  written and closed in one go through the same `finish()` as an online sprint; the same `request_id` is the same sprint
  and the same reward; unknown / retired cards are left out; unknown fields are refused (422).
- App: `src/offline/bank.ts` (fetch only the parts whose hash changed; list asked at most every 6 h; `dealRound` deals
  like `backend/rapid_deck.py choose`), `rounds.ts` (kept rounds, `sendRounds`, `summarise` = the server's marking for
  the result screen), `shelf.ts` / `shelf.web.ts` (plain files in the app's documents / IndexedDB `jeelive-kept-v1`: the
  cards are nobody's secret, they stay after sign-out), `PlainRound.tsx`, `Shell.tsx`, `app/offline/index.tsx`, `rapid.tsx`.
- Where it shows: a fresh Solo Sprint that the server has not dealt in 4 s (slow line) or cannot be asked for (no line)
  starts from the phone (`app/rapid/session.tsx`); a sprint whose line dropped at the end keeps its answers and shows the
  result without an invented reward; the lobby's chapter list comes from the phone when the server's cannot be read.
- Rival, Friends, All India, Cups, Gang wars need the line: another student is on the other side. Not offline, by design.
- Known and accepted by the owner: the answers are on the phone, and the phone chooses the cards of an offline round.

## 3. Finished papers

- Switch: `backend/app_switches.py` `KEEP_RESULTS = 10` → `keep` in `GET /api/app/switches`. The number = papers a phone
  may fetch in one run. `0` = no phone fetches anything (what is kept stays readable). No app build needed to change it.
- `src/offline/papers.ts`
  - `keepResults(uid)`: a run starts 4 s after a confirmed session (after the rounds went up and the cards were
    checked), and again when the switches are read again; at most once in 15 minutes. One paper at a time, 4 s between
    papers. Waits while a paper is being attempted (`/attempt/…`) or a Rapid Fire round is on (`/rapid/…`): checked
    before every paper and before every part of 12 pictures.
  - Per paper: `GET /attempts/{id}/results?score_version=original` (the call the result screen makes), then the pictures
    **only in the website's parts of 12** (`src/assets/paperPack.ts keepResultPictures`: `/assets/links`, CDN parts,
    `/assets/pack` as fallback; WebP at step 5). Needs `PICTURES_STEP ≥ 4` and rows with `asset_revision`. Never the
    one-picture route. Only parts with a missing picture are fetched; a part that brings nothing ends that paper's
    pictures for this run (and its solutions are not asked for).
  - A paper already whole is never fetched again. Some pictures came and it stopped → the next run goes on. Nothing
    came → tried again after 6 hours. A result's `version` in the list changed → fetched again.
  - Room: papers are kept only while their sizes add up to 80 % of 512 MB; beyond that the lower ones in the order are
    simply not kept (nothing is thrown out for them).
  - Each run also looks, without asking the server, whether every kept result's document and a few of its pictures are
    still on the phone; what gave way is counted again, and the list says the truth.
  - `keepOpened(id, data)` (called from `src/api/paperOpening.ts warmResult`): a result opened on screen is kept at once.
- Store: the account's encrypted picture store (`src/assets/deviceCache`), now **512 MB** (`DISK_BUDGET`), the
  oldest-used copy gives way first. Result documents sit beside the pictures (`saveKeptText` / `readKeptText`), same
  key, same account. Native: the list of copies is written 1.5 s after a run of pictures (not once per picture) and at
  once after a document.
- Who may read without a line (`src/offline/door.tsx`): the account whose session the server last confirmed on this
  phone, for 7 days. Sign-out removes every kept result and picture; a session the server ended closes the door
  (the files stay for the same account's next sign-in; another account's sign-in wipes them).
- Screens: `app/offline/results.tsx` ("Mere results"), `app/offline/result.tsx` (reader: score, counts, subject tabs,
  question rail, question, your answer / key, supplied solution; no analysis, rank, AI, report, notes). A result still
  behind its share card ("Share to view results") stays shut here too.
- On the normal result screen: `src/offline/KeptOffer.tsx` — when the result has not answered in 2.5 s, or failed, and
  the phone keeps it: "Phone par rakha result kholo".
- Account → "Bina internet": two rows (cards, results). Sign-in screen and the session-check screen: the door.

## 4. Measured (web preview against jeelive.ai, QA learner, read only, 27 Nov 2026 ~14:00 UTC)

- 11 finished papers: 6 chapter tests (cut look) + 5 JEE Main PYQ papers.
- The 6 chapter tests: 1,652 pictures, 25 MB kept (about 4 MB a paper), about 5 s a paper + the 4 s pause, 130 parts,
  all from the CDN, 0 one-picture calls. First run 10 papers, the 11th at the next opening, nothing fetched at the third.
- **The 5 PYQ papers got no picture: the website's picture store was not answering for PYQ scans** (one-picture route:
  `503 vault_unavailable "Private content is temporarily unavailable"`; parts: `200` after ~10 s with an empty list,
  `max-age=60`). Outside the app. Their results (score, answers, key, text) are kept; the list says "0 / 195 pictures";
  each cost one part, not seventeen; they are tried again after 6 hours, or filled when the student opens them online.
  **A PYQ paper has therefore NOT been seen whole on the phone yet.**
- 512 MB: with the store made to look 40 MB too full, the next write pushed out the oldest stand-in copy only.

## 5. Checks (all read-only for the QA learner; nothing started, nothing submitted)

- `python3 /app/tests/offline_rapid_check.py [arena] [small]` — 33 checks.
- `python3 /app/tests/offline_papers_check.py [small]` — 37 checks (about 6 minutes; it really downloads the papers).
- `backend/tests/test_rf_bank.py` (4), `test_phase2_speed.py` (route count 166), `node frontend/tests/pictures_new_answers_tests.cjs` (32).

## 6. NOT built / NOT checked — say so to the owner

- **Papers not attempted yet** (chapter tests, AITS days, BITSAT mocks before Start): the website gives a paper's
  questions only after Start, and Start starts the clock. The app never starts a paper by itself. To keep such a
  paper on the phone the website must offer a sealed copy that opens at Start (asked in `WEBSITE_OFFLINE_NOTE.md`).
- **Starting or submitting a paper without a line**: the website owns the clock and the submission.
- **Analysis, rank, AI solutions, reports, notes** of a result without a line.
- **Downloading while the app is closed**: BUILT on 28 Nov 2026 (section 7), but it can only be seen in a real app build:
  never run here (web preview and Expo Go cannot run it).
- **A real phone.** Only the web preview was run. On a phone the store is `store.ts` (files in the app's cache folder,
  AES key in SecureStore) and `shelf.ts` (documents folder): the same logic, never run by this check. The cache folder
  may be emptied by the phone itself when it is short of space; the papers then come again.
- **BITSAT results**: the QA learner has none; the order is checked by rule, not by a BITSAT paper.
- **Load**: one new phone asks for up to 10 results and about 20 to 30 CDN parts each in its first two minutes. No
  number of phones was measured. If the website or our server feels it: lower `KEEP_RESULTS`, publish.

## 7. While the app is closed + AI solutions (28 Nov 2026) — preview only, NOT published

Owner (28 Nov): picked "App band hone par bhi download" and "Offline solutions"; "iPhone lock ho tab bhi download chale?"
→ "Haan, lock par bhi". He refused a storage meter ("Banana hi nahi hai").

- **Background run** `src/offline/background.ts` (native; `background.web.ts` does nothing): `expo-background-task` +
  `expo-task-manager` (app.json plugin `expo-background-task`: iOS `UIBackgroundModes: processing` + the permitted
  identifier). Registered after every confirmed session (`door.tsx` → `scheduleKeeping(true)`), every 30 minutes at the
  soonest (Android WorkManager, network required, Wi-Fi or mobile data); iPhone runs it when iOS chooses (mostly at
  night). Unregistered after signing out and after a session the server ended.
  One run: nothing if the app is on screen → `offlineIdentity()` (7-day stamp, not signed out) → `GET /auth/session` must
  give the same uid (else nothing) → stamp renewed → switches → rounds go up → cards → finished papers (`keepResults`,
  skipped while a paper or round was open) → the picture list is written (`flushImageDisk`). Stops after 8 minutes or
  at iOS expiry (`stopKeeping`): what came is kept. Owner's switch `background` (backend/app_switches.py
  `KEEP_BACKGROUND = 1`): 0 stops it on every phone at its next run.
- **Known limit (Android)**: the task is defined when the root layout loads. iPhone wakes the whole app, so it is always
  defined there. Android runs it while the app's process is still alive; when Android has ended the process (often at
  night) the run is skipped. Making it run then needs a custom entry file (package.json "main"), a protected file:
  NOT done; asked of the owner.
- **Locked iPhone**: the session handle `jl_sid` is now written with `keychainAccessible: AFTER_FIRST_UNLOCK`
  (`src/utils/storage/index.ts secureSet`); a handle written by an older build is written once more when the app is on
  screen (`client.ts keepHandleReadableLocked`, flag `jl_sid_after_unlock`). A new handle is never made while the app is
  not on screen (it would sign the phone out when the Keychain refuses a read). The picture store's key was already
  AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY.
- **AI solutions** (`papers.ts`): with each kept paper `GET /attempts/{id}/ai-solutions` (the result screen's call); a
  copy `ai.<id>` beside the result, in the same encrypted store, only when at least one is ready. `row.ai = {ready, total,
  at, bytes}`; a paper with some not ready is asked again after 12 hours (a light answer, ~10 KB; up to `keep` papers a
  run). The result screen's own answer is kept too (`keepAiCopy`, no extra call). Reader: `kept-ai-<number>`; list:
  `kept-row-ai-<attempt>`. **Live on 27 Nov: all items of all 11 QA papers "pending"**: nothing to show yet.
- **Chapter list**: `catalogueAll` sends `per_page=100` (website packet N1, preview only on the website); live still gives
  12 a page and the app reads all pages as before. Class 11 / Class 12 unchanged (owner: "wo rhega").
- Checked: tsc 0, eslint clean, Android bundle builds; testing agent iteration_153 (web preview): AI kept and read
  without a line (mocked ready item in the test browser only), per_page on all 8 requests with identical class counts,
  switches, offline Rapid Fire 33/33. Two small findings fixed after it (AI total from `data.total`; "1 sawaal ka").
- NOT checked: the background run on a real phone (needs a new Android + iOS build after Publish).
