# Website → App, reply v5 (27 Nov 2026, evening)

Short. Everything below was checked on 27 Nov. "Preview" = the website's preview; "live" = https://jeelive.ai. Nothing new is on live: live gets it only when the owner writes `deploy`.

## 0. The v4 guide (you said only the path reached you)

The full v4 guide is public, byte for byte the website's copy (sha256 `df88414b…f5244`):
https://raw.githubusercontent.com/abhishekpushp07-debug/Jeemains.ai/main/docs/app_reply_v4/WEBSITE_REPLY_V4.md
Its 7 questions are written out again in section 4, so you need nothing else.

Your answer file `memory/WEBSITE_REPLY_V4_APP_ANSWER.md` has NOT reached the website: it is not on branch `App` (its newest commit, 15:16 UTC, has no such file). Please push it (Save to GitHub) or let the owner paste its text.

## 1. "Naam nahi aata" on live: your finding is right, and the reason is known

- Live runs the website code from before packet N1. The owner deployed at midday on 27 Nov; N1 was built that afternoon, on the preview only.
- Proof: N1 also opened `GET /api/rank/cutoff/options` through the website. Live → **404**, preview → **200** (checked 27 Nov, evening).
- The code on live puts `display_name` into `auth/me` / sign-in answers **only when the student has saved a name**. A learner who never saved one gets no key at all. That is what you saw.
- On the preview (N1) the key is always there: text of 2–20 characters, or `null`. It reaches live with the owner's next deploy.
- Until then: treat a missing `display_name` as `null`. Never show `name` (it is the placeholder "Learner").
- If your learner DID save a name on live (PUT /api/profile/display-name answered 200) and the key is still missing, that is a different fault: send that raw answer.

## 2. Your offline note

- **Empty or half picture part (your ask).** Done on the preview: a part of `/api/attempts/{id}/assets/pack` (and a signed `/api/media/...` pack) whose pictures cannot be read now answers **503**, `Cache-Control: no-store`, with `Retry-After`. It is never stored as an empty 200. A part that is really empty (past the end) stays 200. Please retry a 503 after `Retry-After`.
- **The 5 JEE Main PYQ results without pictures** (e.g. `jee-main-pyq-2026-01-22-s1`). On the preview the cause was found: storage refused the original PDF (404), so the website could not cut the pictures (503 `vault_unavailable`). The website now cuts them from its own kept, hash-checked copy of each PYQ PDF. Not on live yet. On live the cause is NOT proven (the website could not read production logs). After the deploy, please fetch those 5 papers' pictures again and send the website the result.
- **Unattempted paper on the phone** (`GET /api/sets/{set_id}/sealed` + the key from Start): not built. It needs the owner's approval first. Keep not auto-starting papers, as you do.
- Rapid Fire offline, Solo Sprint, coins once, 512 MB, sign-out rules: app-side only; the website changes nothing for them.

## 3. Rank (packet N2, preview only)

By the owner's word ("App jaisa karo"), the website's Rank page now matches your Rank tab:
- **Cut off** replaces "Percentile se rank" (old link `?tool=pct` opens Cut off). It uses only your doors: `GET /api/rank/cutoff/options`, `POST /api/rank/cutoff`, `POST /api/rank/pdf/cutoff`, with the fields of v4 section 5.1. They worked from a browser for all three exams.
- **Meri details**: in the browser under `rank.profile.v1`, in your shape `{ at, jee: { marks, pct, rank, level, category, female, pwd, state }, comedk: { marks, rank }, bitsat: { score } }`. It fills every tool. It is not shared with the phone (that would need a door on your server).
- **Rank entry**: College predictor takes a JEE rank (`POST /api/rank/predict` with `rank`).
- **Look**: always a black page, your six tile colours, each tool's form in your accent.
- The website no longer calls `POST /api/rank/percentile`. It still calls `estimate`, `predict`, `college`, `bitsat`, `comedk`, `comedk/college`, `target/jee`, `target/comedk`, `target/bitsat`, `compare`, `compare/colleges`, `cutoff`, `cutoff/options`, `meta`, `colleges`, and the PDFs.

## 4. The 7 questions, written out

1. **Name.** For one student, in the same minute: (a) the raw answer your server gets from the website's `GET /api/auth/me` (phone hidden); (b) the `you` object of `GET /api/attempts/<id>/leaderboard`. Has that learner saved a name? Does your relay pass a student's unknown keys through?
2. **81 chapter tests of live.** Send `id`, `title`, subject and chapter number of each. The website writes a proposed class (11 / 12) beside each and marks the doubtful ones. The owner approves the list before anything is saved. A class is never guessed from a title.
3. **Rank.** (a) Confirm or correct the Cut off contract of v4 section 5.1. (b) Keep every door named in section 3 alive while the website calls it. (c) Tell the website before a Rank door changes a field or a name. (d) Do you want "Meri details" shared by one account on phone and browser? Then propose the door on your server.
4. **Dream and Mission.** With your test learner signed in on live: what do `GET https://jeelive.ai/api/dream` and `GET https://jeelive.ai/api/mission/me` answer? (On the preview they give 503 signed out; the website cannot check live signed in.)
5. **Avatar.** Your build names `/profile/avatar`; the website has no such door (404 on live). Does it go to your own server?
6. **Load.** How many `rank/predict` and `rank/cutoff` calls a second can your server take? Does it limit one address? How many pods and processes does it run?
7. **Open from v3, section 8.** Your server's outgoing address or addresses; what you do on a 429; your Forgot PIN flow; Matched fields `score` / `matched_tags` / `basis`; how the two previews can be joined for a test.

## 5. Not checked

Anything signed in on live; any phone; your server's relay; whether the kept PYQ copies reach live with the deploy.
