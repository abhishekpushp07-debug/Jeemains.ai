# Part 7 — Working together: the website's doors the app uses

## 7.1 Why this part is here

The website can be changed any day. **An app in a student's phone cannot:** it changes only when the student installs a new build, and phones keep an old build for months. So every answer of the website that the app reads is, in effect, a promise. This part lists those answers, so that the website's own work never breaks the app unseen:

- **7.2** every door of the website the app uses today ({{DOOR_COUNT}} of them);
- **7.3** how the app's server reaches the website, and what it does with what comes back;
- **7.4** what may change freely, what may not, and how a change is agreed;
- **7.5** the doors the app already asks for that the website has not built;
- **7.6** what was checked, and what was not.

The list of 7.2 is not written from memory: when this book is built, every door named in the app's own code is looked up in it, and the build stops if one is missing.

## 7.2 Every door of the website the app uses

**How to read the tables.** A door is written without its beginning: `GET /my/tests` is `GET https://jeelive.ai/api/my/tests`. `<id>` stands for an id (of a paper, an attempt, a question, a job, a Misfire item) or, in the exam doors, for the exam's slug (`jee-main`, `bitsat`, `comedk`). The phone never calls the website itself: it calls the app's server (`…/api/jl/<the same path>`), which passes the call on **unchanged**, with the student's own website cookies (Part 7.3). Doors marked **(server)** are called by the app's server on its own.

**The account** (the whole story: Part 6.2)

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `POST /auth/phone/signup` | sign up | `phone`, `pin`, `confirm_pin` | the student with `id`; the session cookies |
| `POST /auth/phone` | sign in | `phone`, `pin` | the same. **A wrong PIN is answered 401 or 403** (the app's server counts them, Part 7.3) |
| `GET /auth/session` | every time the app opens; after a 401 | — | 200 with `user` (an object with a text `id`) or `user: null`. Anything else is read as "could not be checked" and tried again |
| `POST /auth/refresh` | renewing the session | `{}` | 200 with a JSON object and new cookies; **401 with a plain message** when the session is really over |
| `GET /auth/me` | who am I; **(server)** the id Rapid Fire plays under | — | the student with the same `id` |
| `POST /auth/pin` | change the PIN | `phone`, `new_pin`, `confirm_pin` | success; this session stays, the `id` stays |
| `POST /auth/logout` | sign out | `{}` | success |
| `POST /auth/login` | **(server)** the owner's own account, for the two doors below | the owner's email and password | the owner's session |
| `GET /admin/students` | **(server)** Forgot PIN: find the account of a number | `?q=<number>` | `items[]` with `phone` and a whole-number `pin_version` |
| `POST /auth/owner/student-pin-reset` | **(server)** Forgot PIN: set the new PIN | `phone`, `new_pin`, `confirm_pin`, `expected_pin_version` | 200 |

**Exams and the lists of papers**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /catalog/exams` | Home's exams | — | `items[]`: `slug`, `name`, `shown`, `order`, `sections` |
| `GET /catalog/exams/<id>` | an exam's page and its sections | — | `sections[]`: `slug`, `name`, `layout` (`list` or `chapters`), `hidden`, `order`, `live_count`. **404 = the owner has hidden the exam** |
| `GET /exam-navigation/<id>/catalogue` | every list of tests; **(server)** the chapters of Student Choice | `?kind=` (`mocks` or `chapters`) `&section=&subject=&q=&page=` | the fields of Part 1.5; `pages` |
| `GET /exam-navigation/<id>/history` | previous years' papers; Misfire's paper tabs | `?page=` (Misfire also `kind=`) | the list and its paging |
| `GET /pyq/jee-main` | the PYQ page | — | the years, their papers, each paper's own `attempt` |

**A paper, before it starts**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /my/sets/<id>` | the paper's page; the paper's `test_kind` for the Dream College meter | — | `test_kind`, `saved`, the student's own `attempt` |
| `GET /sets/<id>` | the same page for a visitor without a session | — | the paper |
| `POST /sets/<id>/preflight` | the device check before the start | `preview: false`, `test_response: "25"` | 2xx = may start; a refusal's `error.message` is shown |
| `POST /sets/<id>/start` | start | `start_key`, `device_checked: true`, `preview: false`, `get_ready: true` | the attempt's `id` and `status`. A retry sends the same `start_key` |
| `POST /my/tests/saved/<id>` | save a paper for later | `{}` | success |
| `DELETE /my/tests/saved/<id>` | take it off the saved list | — | success |

**The paper being taken**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /attempts/<id>` | the player | — | `set_id`, `questions[]` with `id` and `type` (`integer` for a typed answer), the clock |
| `POST /attempts/<id>/begin` | the get-ready minute is over | `{}` | `server_now`, `ready_until`, `deadline` |
| `PUT /attempts/<id>/answers/<id>` | saving one answer (the second `<id>` is the question's) | the answer; `timeline` when time events ride along | `timeline_cursor` |
| `POST /attempts/<id>/visit` | a question was opened | `question_id` | success |
| `POST /attempts/<id>/timeline` | time events on their own | a batch | `cursor` |
| `POST /attempts/<id>/bonus` | entering the bonus part | `{}` | `bonus_unlocked_at` |
| `POST /attempts/<id>/submit` | hand in | `timeline` when there is one, else `{}` | the receipt |
| `GET /attempts/<id>/assets/links` | the pictures of a paper, in parts | `?kind=solution`, `format=webp`, `look=cut`, `score_version=` (each only when needed) | `limit`, `total`, `parts[]`. **403 or 409 = these pictures are not given in parts**: the app then asks for them one by one |
| `GET /attempts/<id>/questions/<id>/asset/question/<n>` | one picture (also `…/asset/solution/<n>` and `…/asset/piece/<n>`) | `?score_version=`, `format=webp`; `If-None-Match` | the picture; `ETag`; 304 when unchanged; 429 = busy (with `Retry-After`) |

**The result and the analysis**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /attempts/<id>/results` | the result; a paper's Misfire page | `?score_version=` | `set_id`, the questions' ids, `test_kind` |
| `GET /attempts/<id>/analysis` | the analysis | `?mode=` (`personal`, `comparative`) `&compare=&score_version=` | the analysis; `score_version` |
| `GET /attempts/<id>/analysis/report.pdf` | the A4 report | `?score_version=` | a PDF file |
| `GET /attempts/<id>/analysis/share.png` | the scorecard picture | — | a PNG file |
| `GET /attempts/<id>/leaderboard` | a paper's leaderboard; the All India day leaderboard; the Rank journey | `?q=` | `state`, `n`, `rows`, `around`, `found`, `you`; a row: `rank`, `name`, `handle`, `score`, `attempted`, `accuracy`, `time`, `is_you` |
| `GET /attempts/<id>/journey` | the result's Progress tab | — | `state` (`available` or not) |
| `GET /attempts/<id>/historical-rank` | the result's Rank tab | `?score_version=` | `kind` |
| `GET /attempts/<id>/ai-solutions` | the AI's step-by-step solutions | — | the solutions |
| `POST /attempts/<id>/questions/<id>/solution-open` | a solution was opened | `{}` | success |
| `POST /attempts/<id>/questions/<id>/report-wrong` | "this question is wrong" | `category`, `context: "solutions"`, `note` (600 letters at most) | the receipt |
| `PUT /attempts/<id>/reviews/<id>` | the student's review of one question | `request_id`, `revision`, `score_version`, `category`, `note`, and the review's ticks | the saved review |
| `PUT /attempts/<id>/learnings` | "what I learnt" | `items[]` | `items[]` |
| `POST /attempts/<id>/retry` | take the paper again | `start_key`, `score_version` | the new attempt |
| `GET /jobs/<id>` | a result still being made | — | the job's state |
| `POST /jobs/<id>/retry` | make it again | `{}` | success |

**My Tests, Misfire, the All India series**

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /my/tests` | My Tests; the Dream College meter's first read on a new phone | `?tab=&page=&q=&status=&exam=` | `items[]` |
| `POST /my/tests/compare` | compare two papers | `left`, `right` | the comparison |
| `GET /my/misfire/summary` | Misfire's counts | — | Part 4 |
| `GET /my/misfire` | Misfire's list | `?status=&subject=&chapter=&page=` | Part 4; an item's id is `<attempt id>:<question id>` |
| `GET /my/chapters` | Misfire's chapter report | — | Part 4 |
| `POST /my/misfire/<id>/try` | "Check karo" | `value` | `correct`, `item` |
| `POST /my/misfire/<id>/done` | "Samajh gaya" | `{}` | success |
| `POST /my/misfire/<id>/reopen` | "Wapas list mein" | `{}` | success |
| `GET /series/all-india-jee` | the All India series; **(server)** its `last_date`, every 15 minutes, for Home's card | — | `first_date`, `last_date`, `today`, `total`, `slots[]` |
| `GET /series/all-india-jee/history` | the student's days | `?page=` | the days and their attempts |
| `GET /series/all-india-jee/streak` | the streak | — | the streak |
| `PUT /profile/display-name` | the name on leaderboards | `name` | `display_name` |

**Asked today, not built yet on the website** (they answer 404; the app waits: Part 7.5)

| Door | Used for | Sent | The app relies on |
| --- | --- | --- | --- |
| `GET /choice/bank` | **(server)** Student Choice, door A; the Misfire Mock's switch `misfire` | `?exam=jee-main` | Part 1.6; Part 4.8 |
| `GET /choice/chapters/<id>/questions` | **(server)** Student Choice, door B | `?page=` | Part 1.6 |
| `POST /choice/papers` | Student Choice, door C; the Misfire Mock (`mode: "misfire"`) | Part 1.6; Part 4.8 | Part 1.6; Part 4.8 |
| `GET /my/misfire/mocks` | the Misfire Mock's list, asked only while door A says `"misfire": true` | `?page=` | Part 4.8 |
| `GET /matched` | **(server)** Matched: the list, every 2 minutes | — | Part 2.4c |
| `GET /matched/<id>` | **(server)** Matched: one shift | — | Part 2.4c |
| `GET /series/all-india-jee/leaderboard` | the whole-series leaderboard | `?q=` | Part 7.5 |

## 7.3 How the app's server reaches the website

**One address.** Every call above arrives at the website **from the app's server**, never from a student's phone or browser. So the website sees a small number of addresses (the app's servers) for all app students.

- **The student's own address** is sent in `X-Forwarded-For`: exactly one address, checked by the app's server; what a caller wrote into that header himself is never passed on. **A limit the website keeps per address must count this header when the call comes from the app's server**, and must never treat the app's server as one student. (June 2026: the website's limiter stopped sign-ins that came through the app's server, because they all arrived from one address; the header was added then. Whether the website counts it today was not checked by the app side: Part 7.6.)
- **Cookies.** The website's cookies of each device are kept on the app's server, never on the phone. They are sent back as one `Cookie` header. What the app's server understands of a `Set-Cookie`: the name, the value, and **`Max-Age=0` or an empty value = this cookie is gone**. It does not read `Path`, `Domain` or `Expires`. So: **to take a cookie away, send `Max-Age=0` (or an empty value)**; a cookie taken away only by an `Expires` in the past stays in use.
- **The access cookie is named `access_token`.** Student Choice's chapter list is read with that one cookie alone (so that this read can never renew or end the student's session). Under another name the list would stop.
- **Headers passed on to the website:** `Accept`, `Content-Type`, `If-None-Match`, `If-Modified-Since`, `If-Range`, `Range`. **Passed back to the phone:** `Content-Type`, `Retry-After`, `Location`, `Cache-Control`, `ETag`, `Last-Modified`, `Content-Range`, `Accept-Ranges`. No other header of the website reaches the app.
- **Redirects are not followed.** A 301, 302, 307 or 308 on an API door reaches the app as a failure. Answer the door itself, at the address written here, over https.
- **Never two session calls at once.** For one device, `auth/session`, `auth/refresh`, `auth/phone`, `auth/phone/signup`, `auth/pin` and `auth/logout` are sent one after another, never together, also across the app's server processes. A refresh token is therefore never used twice by the app.
- **Nothing private is logged:** not a PIN, not a cookie, not a request's body. A PIN is passed on and never kept. A device's cookies unused for 90 days are removed.

**How long the app waits, and what it tries again**

| What | The rule |
| --- | --- |
| The app's server waits for the website | 28 seconds (a picture: 22); 4 seconds to connect |
| The phone waits for the app's server | 32 seconds (a file: 60; a picture: 25) |
| A read (`GET`) that fails with 408, 500, 502, 503, 504, 520, 522, 524, or does not connect | tried **once** more after a quarter second (or after `Retry-After`, when it is under two seconds). The session doors are not tried again, except `auth/me` |
| A write (`POST`, `PUT`, `DELETE`) | **never sent twice** by the app's server. When the student tries again, a paper's start carries the same `start_key` and a made paper the same `request_key`: the website must answer the same thing for the same key |
| 401 on any door but the session doors | one `auth/refresh`, then the call once more. If the refresh is refused with a plain message, `auth/session` is asked; `user: null` signs the student out. **An empty 401, or one without a plain message, is not taken as "signed out"** |
| Ten wrong PINs for one number in 15 minutes (401 or 403 on `auth/phone`) | the app's server stops sign-in for that number itself (429) until the 15 minutes pass. This is the website's own limit, kept in step so that the website's "tries left" stays true |

**When the website is in trouble**

- **The shield.** When 8 or more calls in 10 seconds fail, and they are at least half of the calls, the app's server stops calling the website for 5 seconds (then 10, 20, 30 at most), and lets one call through to see. "Fail" = no connection, a time-out, an answer slower than 10 seconds, or 502, 503, 504, 520 to 527, 530. Meanwhile the student reads "The website is not answering right now. Your saved work is safe." So **an outage of the website is not made worse by the app**, and Rapid Fire, which runs on the app's server, keeps playing.
- **An HTML page is never shown to a student.** A 5xx whose body is not JSON with a plain `error.message` (a Cloudflare page, a stack trace) is replaced by the sentence above.
- **For planned work, answer 503** with JSON, a plain `error.message` and `Retry-After` in seconds: the student reads the website's own sentence. (While most calls are answered so, the shield is shut and the student reads the app's sentence instead.)

**What an answer looks like to the app**

| What | The rule |
| --- | --- |
| A good answer | plain JSON, or the envelope `{ "data": …, "error": null, "meta": { "api_version": … } }`. The envelope is opened only when `meta.api_version` is there. Its value is not compared: **a new `api_version` alone tells the app nothing** |
| A refusal | `error.message` (or `detail`) in plain words is shown to the student **as it is**; `error.code` is read where Part 1 and Part 2 say so; `Retry-After` in seconds or as a date |
| 204 | accepted as success without a body |
| A good status with a body that is not JSON | "The server response was incomplete": the student is asked to try again |
| Words | `Physics`, `Chemistry`, `Mathematics`; `test_kind` and `kind` exactly as Parts 1, 2 and 4 write them |

**How much the app's server may ask at once** (its settings, **not a measured capacity**): 400 connections to the website for each server process, kept open 45 seconds; when more than 3000 calls of one process are waiting for the website, new ones are answered "busy" at once. The two sides have never been load-tested together (Part 7.6).

## 7.4 Changing a door: what is free, what is not, and how it is agreed

**Free, at any time, without telling anybody**

- A **new field** in an answer. The app reads fields by name and leaves the rest.
- A **new door**.
- Different numbers, words and lists inside the fields that exist (more papers, another exam, a section hidden): that is the website's daily work, and the app follows.
- Making a door faster.

**Not free: tell the app side first** (through the owner, in writing: the door, the answer before and after, the day)

- Renaming, removing or re-typing a field named in this book (a number that becomes text, a list that becomes an object, `null` where an object was).
- A door's address or method; a parameter's name.
- What a status means on a door (above all 401, 403, 404 and 409 where 7.2 gives them a meaning).
- The envelope, the shape of `error`, the cookies' names, the session doors.
- A new limit per address or per account that could meet the app's server (7.3).
- A student's `id`, an attempt's id, a paper's id: they never change (Part 6.3).

**How such a change is made safely**

1. **The new thing comes beside the old:** a new field next to the old field, a new door next to the old door. The old one keeps working.
2. The app side says which app builds read the old one, and builds the new reading. The owner publishes; new builds go to the stores.
3. **The old one is removed only when the owner says so**: phones keep old builds for months, and an old build that meets a missing field shows an error, an empty page, or nothing at all.
4. **First on the test setup** (rule 20 of Part 0.4), then for students.

What the app side promises in return: it asks for nothing that is not in 7.2; when it starts using a new door or a new field, the next version of this book lists it; `/api/arena` and `/api/rf/…` stay the app's own (Part 5).

## 7.5 Doors the app already asks for

The app asks these today and gets 404. **Nothing breaks; a part of the app simply waits.** The day the door answers in the agreed shape, that part appears by itself, without a new app build.

| Door | What appears | The shape |
| --- | --- | --- |
| `GET /api/choice/bank?exam=jee-main`, `GET /api/choice/chapters/<set id>/questions`, `POST /api/choice/papers` | question picking and the random mock | Part 1.6 |
| `GET /api/matched`, `GET /api/matched/<shift id>` | the real shifts of Matched | Part 2.4c |
| `GET /api/series/all-india-jee/leaderboard` (and `?q=<name or Rank>`) | a "Poori series" tab on the AITS Leaderboard, with its Rank card and share card | below |
| `"misfire": true` in `GET /api/choice/bank?exam=jee-main`; then `POST /api/choice/papers` with `mode: "misfire"`, `GET /api/my/misfire/mocks`, and `misfire` in a result | Misfire's "Mock" tab and the Misfire Mock. The last three are asked only once door A says `true`; all agreed with the website on 28 Nov 2026 | Part 4.8 |

**The whole-series leaderboard** (the app side's earlier note, repeated here so that it is in one book). The same envelope and the same row as `GET /api/attempts/<id>/leaderboard`, plus three fields:

```json
{
  "state": "ready",
  "n": 5120,
  "title": "All India JEE Mains · poori series",
  "days_counted": 12,
  "maximum": 3600,
  "min_finishers": 10,
  "query": "",
  "rows": [ { "rank": 9, "name": "Arjun Sharma", "named": true, "handle": "<the same for a student on every day>",
              "score": 3075, "days": 11, "attempted": 770, "accuracy": 92.3, "time": 104500, "is_you": false } ],
  "around": [],
  "found": [],
  "you": null
}
```

- New: `days_counted` (how many released live days are added up), `maximum` (optional), and `days` in a row (how many of them this student handed in).
- Only live attempts of released days count; a student's first attempt of a day; the same tie-break and the same names as on the day leaderboard. The app never adds up Scores itself.
- **The app shows it only when the shape is whole:** `state` and `n` there, `days_counted` a number, `rows` and `around` lists, and every row (and `you`, when not `null`) with number `rank`, `score`, `days` and text `name`, `handle`. **Until it is ready, keep answering 404.** A half-built answer stays hidden.

## 7.6 What was checked, and what was not

**Checked on {{TODAY}}**

- **The list against the code:** every door the app's screens name in their code is in 7.2 (the build of this book stops otherwise). The doors of the app's server were read from its code (`backend/jl_proxy.py`, `choice.py`, `matched.py`, `rf_access.py`, `pin_reset.py`, `account_deletion.py`, `owner_panel.py`).
- **A read-only walk** (`tests/website_doors_walk.py`): 30 screens of the app's preview were opened as the test learner, and every call to the website was written down. Signing in was the one write; nothing was started, answered, saved or submitted. 21 doors were seen: 19 answered 200; `auth/refresh` answered 401 once, before sign-in, as it should; `series/all-india-jee/leaderboard` answered 404 (7.5).
- **The rules of 7.3** were read from the app server's code (`jl_proxy.py`, `jl_transport.py`, `website_shield.py`, `session_coordination.py`, `login_guard.py`) and from the app's (`frontend/src/api/client.ts`).
- **Misfire's two mocks (28 Nov 2026):** Offline Misfire and the Misfire Mock were walked on the preview with the website's answers played by the browser (Parts 4.7 and 4.8). Nothing was written to the website.

**Not checked**

- **The doors that write** (start, begin, answers, visit, bonus, submit, timeline, retry, reviews, learnings, report-wrong, solution-open, save, compare, the name, the PIN, sign-up, Misfire's three buttons) were not called on this walk: the test learner is the owner's own account on the real website. They are in 7.2 from the code.
- **Whether the website counts `X-Forwarded-For`** from the app's server for its own limits today.
- **The two sides under load.** No test has put many students through the app's server and the website together. No number of students at once is claimed for the pair.
- **A change made the way 7.4 says** has not been walked yet: the first one is the test of the method.
