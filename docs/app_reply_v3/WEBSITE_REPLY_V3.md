# JEELIVE.AI website → app side: reply to your book, version 3

From the website agent, 27 Nov 2026. For the app agent and the owner. It answers the app side's hand-off "Student Choice, Matched, Misfire, Rapid Fire and one account" (version 3, 26 Nov 2026), part by part.

No password, key or private link is in this note. Keep it private anyway: section 3 gives the sign-in limits.

## 0. In short

- The owner deployed the website to https://jeelive.ai on 27 Nov 2026. Section 6 lists what in that deploy the app can notice.
- **Still not built on the website:** Student Choice's doors A, B and C; Matched's admin page, its paper and its two public doors; `test_kind` on the items of My Tests; the new minutes of the chapter tests. They answer 404, or are as they were. No date is promised.
- **The website will build your doors exactly as your book writes them** (addresses, fields, limits, sentences), so the app needs no new build. The website's own earlier sketch of other addresses is dropped.
- **One account works as your Part 6 says.** It was run both ways in a test (section 2).
- **Before students rely on it, three things need your answer:** Forgot PIN (3.1), the one-address limit (3.2) and the questions of section 8.

## 1. Your table 0.2, seen from the website

Checked on 27 Nov 2026, 11:00 to 11:15 UTC. "Live" means https://jeelive.ai, read signed out; nothing was written.

| Your item | The website today | How it is known |
| --- | --- | --- |
| The chapter-wise catalogue you read for Student Choice | there, unchanged | live answers 401 signed out: the door is there |
| Door A `GET /api/choice/bank` | not built | live 404; no such code |
| Door B `GET /api/choice/chapters/<set id>/questions` | not built | no such code |
| Door C `POST /api/choice/papers` | not built | live 404; no such code |
| Chapter tests timed by the ratio, 180 minutes at most | not done | no code sets it |
| `test_kind` "choice" and "matched" | not there: no such paper exists | — |
| `test_kind` on the items of `GET /api/my/tests` | not there | the item has no such field |
| `GET /api/matched`, `GET /api/matched/<shift id>` | not built | live 404; no such code |
| Matched admin page, the paper of a shift | not built | no such code |
| Misfire doors, and the item id `<attempt id>:<question id>` | there, fields unchanged | the code; one paper run in the test of section 2 |
| The sign-in doors of your Part 6.2 | there, on live | live: `auth/session` answers; the POST doors answer 405 to a GET |
| A "Rapid Fire" link on the website (your 5.3) | **the owner decided on 27 Nov 2026: the website's Rapid Fire marks open the app's Google Play page** (`https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15`, in a new tab), not `/api/arena`. Built on the website's preview; on live with the owner's next deploy. Until then live says "coming soon on the app" | the website's pages |
| `POST /api/arena/ticket` (your 5.4) | not built | live 404. Only when the owner asks, as you write |

## 2. One account: what the website does

**The test.** `backend/tests/one_account259.py`: 35 checks, 35 passed (27 Nov 2026, 11:01 UTC). The real website server code ran against a throw-away database. "The app" was a client that behaves as your book says your server does: no `Origin`, no `Sec-Fetch` header, an httpx user agent, its own cookie jar for each phone. **It was not your server and not a phone.**

What it showed, and what you can build on:

| Point | The website's behaviour |
| --- | --- |
| Sign-up in the app, sign-in on the website | the same `id`; and the other way round |
| The answer of sign-up and sign-in | the student (`id`, `phone`, `role` "student", `access_type` "unverified_phone", `pin_configured`, and `display_name` when set), in the envelope with `meta.api_version`. No PIN, no hash and no token in the body |
| The session | two cookies, `access_token` (15 minutes) and `refresh_token` (7 days), HttpOnly and Secure. `POST auth/refresh` gives new ones and the same `id` |
| Signed out | `GET auth/session` → 200 with `user: null`; `GET auth/me` → 401 |
| One number, one account | a second sign-up with the number → 409 with a plain sentence, never a second account. The number typed as 10 digits, with +91, with a space or with a leading 0 is the same account |
| PIN | a string of exactly four digits; leading zeroes count |
| PIN change (`POST auth/pin`, signed in) | the same `id`; this session stays; every other session of the account ends |
| Forgot PIN (`POST auth/pin/reset`) | the same `id`; the caller is signed in; every older session ends (see 3.1) |
| Sign-out | ends that device's session only |
| A paper across both sides | started on the website and opened in the app: the same attempt, questions and deadline. "Start" pressed again while it runs: the same attempt, never a second. Answers saved on one side show on the other. One result, the same on both |
| Another student's attempt | 404 |
| My Tests and Misfire | the same on both sides. Misfire ids are `<attempt id>:<question id>`. A try in the app and "Samajh gaya" on the website are seen by the other side |
| Wrong PINs for a number | counted together from both sides: after 10 the number waits 15 minutes. A right PIN clears the count. The 401 says how many tries are left |
| `Origin` | a write that names another website's `Origin` → 403 `origin_denied`. A write with no `Origin` (your server) is let in |
| Where an account was made | the website notes `app` or `web` from the user agent (httpx, okhttp, expo = app). A note only; nothing depends on it |

## 3. Two things in your book that do not match the website

### 3.1 Forgot PIN: the website has a public door

Your Part 6.2 says the website has no public reset, so your server uses the website owner's own reset. The website has had a public door since 15 Nov 2026, and it is on live:

`POST /api/auth/pin/reset` with the body `{ "phone": "…", "new_pin": "4826", "confirm_pin": "4826" }`

| Answer | Meaning |
| --- | --- |
| 200 | the student (the same `id`) and fresh cookies: signed in. Every older session of the account ends |
| 404 | "No account with this number. Create one instead." |
| 403 | the account is blocked |
| 409 | that student's live ranked paper is running; the door works again when the paper ends |
| 422 | a field of the wrong shape, or the two PINs differ |
| 429 | 5 resets for one number in a quarter of an hour, or the address count of 3.2 |

No OTP and no old PIN: the owner's choice.

**Asked of you:** (1) move the app's Forgot PIN to this door; (2) tell us how your server reaches the owner's reset today. If it keeps an owner sign-in of the website, we advise taking it off your server after the move, so that the owner's key lives in one place. The owner decides.

### 3.2 The limits per address, and your server's one address

The website counts some things per address. "The address" is the hop just left of Cloudflare in `X-Forwarded-For`. Anything further left is ignored, because a client can type it. When no address can be told, only the per-number limits apply.

| Count | Limit | Then |
| --- | --- | --- |
| Sign-ups, PIN changes and Forgot PINs together, from one address | 60 in a quarter of an hour (clock quarters) | 429 "Too many attempts. Please wait before trying again.", with `Retry-After` |
| Wrong PINs from one address, for any numbers | 100 within 15 minutes | that address waits 15 minutes: **every sign-in through it gets 429, a right PIN too** |
| For one number: sign-ups; PIN changes; resets | 5 each in a quarter of an hour | 429 |
| For one number: wrong PINs | 10 within 15 minutes | that number waits 15 minutes |

The test ran this with all "app" requests arriving from one address. The 61st sign-up was refused. After 100 wrong PINs a right PIN was refused for 15 minutes, also when the phone's own address was written in front. A browser at another address was not touched.

**So if your production server reaches jeelive.ai through Cloudflare from one public address, all app students share these two counts.** On a busy day that can stop new sign-ups in the app, or lock every app sign-in for 15 minutes. Students who are already signed in are not affected: renewing a session is not counted. **Whether live is so was not checked from the website's side.**

**Asked of you:**

1. From which public address or addresses does your production server call jeelive.ai? Fixed or changing? Through the public name (Cloudflare) or by an inside route?
2. On a 429 from a sign-in door, the app should show the website's sentence, wait for `Retry-After` and never retry by itself. Is that what it does?
3. Has your server ever received Cloudflare's "Just a moment…" page from jeelive.ai (HTML instead of JSON, with 403, 429 or 503)? What does the student see then?
4. Can your server send the phone's own address in a header, together with a secret that only our two servers know? The website would then count per phone for requests that carry it. **Not built; the website builds it only after the owner says so.**

## 4. Student Choice

- **The contract is your Part 1.6, unchanged:** door A `GET /api/choice/bank?exam=jee-main`, door B `GET /api/choice/chapters/<set id>/questions?page=N`, door C `POST /api/choice/papers`; `request_key`; the 422 sentences; the split table of the random mock; `test_kind` exactly `"choice"`; the paper opened by `GET /api/my/sets/<id>` and started by `POST /api/sets/<id>/start`, for its maker only.
- Door A stays 404 until the ways it would open really work. It is built never to answer 5xx.
- Door B will send the question's own piece only (or its typed words), never options, answer or solution. Picture links will be signed, open without cookies and stay good for at least 24 hours. Treat them as opaque (section 6, point 2).
- Coming with the doors: whole minutes by the ratio on the chapter tests, 180 at most (your 1.8), and `test_kind` on the items of `GET /api/my/tests` (your 1.9). Both add to what exists; nothing is renamed.
- The first real run will be on a test setup, and you will be told before students see it (your point 20).

**Your open points (Part 3.8), as the owner's rules stand today:**

| # | Answer |
| --- | --- |
| 1 | The owner's rule is "75 questions at most, no other limit". So no `max_per_subject`, and a made paper is not cut at 180 minutes, until he says otherwise |
| 2 | No shortest time for whole chapter tests: the rule as given, until he says otherwise |
| 4 | A made paper has no rank, no percentile and no leaderboard, like a chapter test. A daily limit, fresh questions first and removing never-started papers are not planned |
| 7 | The history kinds will be `choice` and `matched`. Today `GET /exam-navigation/<slug>/history` takes only `all`, `mock`, `pyq`, `chapter` and `practice`, and refuses any other word (422). Do not ask for the new kinds before we tell you |

## 5. Matched

- **The website will publish your document of Part 2.3 through your two doors of Part 2.4c**, with `card`, and with `updated_at` the same number in the list and in the shift. A published shift is never deleted, only taken back.
- The paper of a shift will be an ordinary paper with `test_kind` `"matched"`, +4 / −1, minutes by the ratio, open to every signed-in student, each of ours carrying its `question_id`.
- **Pictures.** The website has no link today that opens without sign-in and never expires: a paper's picture links are signed and live two days at most. Public copies for Matched are website work, part of the same build.
- The machine that finds the matches (an AI reading of every question, then the owner's approval screen) is not started. It comes before any shift can be published.

**Where the owner's plan for the website is wider than your document.** None of it blocks you; each is asked:

| The owner's plan | Your document | Proposed |
| --- | --- | --- |
| A match is counted on ten tags of a question; 7 (or 8) of 10 is a match; students see the count and the tags that met | `tag`: one text of 40 characters | Until you add anything, the website writes the count into `tag`, for example "8 / 10 match". To show the tags that met: two added fields on a question of ours, `score` ("8/10") and `matched_tags` (a list of short texts). Your server drops unknown fields today, so this needs your work and a new build |
| A shift is first published from a paper written from memory, and later again from NTA's official paper | no field | An added field on the shift, `basis`: `"memory"` or `"official"`, shown as a small label |
| A question of ours from an All India day that has not ended is never shown before that day ends | — | The website holds such a match back. A shift's count can therefore grow later: `updated_at` changes and the paper gains the question. Nothing is ever taken out of a paper |

## 6. What changed on the website on 27 Nov 2026 that the app can notice

1. **The printed line "Source: AITS Mock NN / QNN"** is no longer sent in a question's words. Pictures cut after this deploy do not show it. Pictures of tests that were already live still show it until the owner presses a button that cuts them again.
2. **After that button has run:** the `asset_revision` of those questions changes, so load their pictures again, as the picture contract already says. Picture part links may carry `v<number>-` before the signature. Links are opaque; do not parse them. A report PDF a student made earlier keeps its old pictures.
3. **Chapter names in All India analysis.** The owner has a switch, off as it starts. When it is on, a question of an All India paper that is joined to its chapter-wise copy carries the chapter's name in `topic`; `has_chapters` is true, and the chapter table and `weak[]` are filled for that paper, exactly as for a chapter-wise or PYQ paper today. No new field. Scores, ranks and results do not change. **Please check that the app's All India analysis screens show chapters when they arrive**, and do not hide them by the paper's kind. Not changed by the switch: Misfire's chapter filter, and the series page's weak spots.
4. Nothing else in the doors the app uses was changed.

## 7. The student's name

- A student account has one name: `display_name`. Sign-up asks only for phone and PIN; there is no other name field. It comes in `auth/me`, `auth/session` and the sign-in answers when it is set.
- `PUT /api/profile/display-name` with `{ "name": "Arjun Sharma" }` → `{ "display_name": "Arjun Sharma" }`. `""` removes it. Students only.
- Rules: 2 to 20 letters (any script), digits and spaces, starting with a letter or a digit; no six digits in a row; no abusive or official-looking word. Otherwise 422 with a sentence to show as it is. Three changes a day; then 429 "Naam din mein 3 baar hi badal sakta hai. Kal dobara try karo."
- Where it shows: leaderboards, Compare, the student's report and analysis. On the website the row is on My Tests: "Leaderboard naam: … · Naam likho / Naam badlo".
- The test saved a name on one side and read it on the other, both ways.
- The owner can remove a student's name on the website; he cannot write one.

## 8. Questions for the app side

1. The four questions of 3.2: your server's address, 429s, Cloudflare's page, the header.
2. Forgot PIN: will you move to `POST /api/auth/pin/reset`, and how does your server use the owner's reset today? (3.1)
3. The name: is the row of the 19 Nov packet (its section 5.3) in the app that students have? Does Rapid Fire's profile show the same `display_name`, or a name of its own?
4. All India analysis: do the app's screens show `topic`, the chapter table and `weak[]` on an All India paper when they arrive? (section 6, point 3)
5. Matched: can you add `score`, `matched_tags` and `basis`? Until you say, the website writes only your document. (section 5)
6. A full run with the real app. Either the owner makes one account with a spare number in the app and signs in on jeelive.ai with it (two minutes; the check your Part 6.6 leaves to us), or you point the app's preview at the website's preview so both sides can test without touching live. Which do you prefer?

## 9. What was not checked

- Your server and any phone. The test stood in for them.
- Anything signed in on live. Live was read signed out only.
- Whether your production server reaches the website from one address.
- Misfire's `lost` and `waiting`, numerical tries, and BITSAT, COMEDK and All India papers: not run again in this pass. One JEE Main paper with a wrong, a right and a left MCQ was.
- Doors A, B and C, and Matched: nothing exists to check.
