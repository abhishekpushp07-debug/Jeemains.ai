# Pictures: the website's new way in the app (built and switched on 23 Nov 2026)

What the website offers: `WEBSITE_PICTURES_REPLY_2.md` (its note, update 2). What the app promised: `APP_PICTURES_REPLY.md`.
Live on jeelive.ai for every student since 23 Nov 2026, 10:54 PM IST (owner's message).

## The switch (one number, on our own server)
`backend/app_switches.py` -> `PICTURES_STEP`, served at `GET /api/app/switches` as `{"pictures": n}`. The app asks once when
it starts (`askSwitches` in `src/api/client.ts`). No answer, or a number below 2 = 0 = the old way.
Changing the number + publishing the backend reaches every phone at its next start. No app build needed.

| step | what it adds | where |
|---|---|---|
| 0 | off: pictures load exactly as before | |
| 1 | small re-check (`If-None-Match` + `Range: bytes=0-0` + `If-Range`) of a copy older than 3 days. In every build, no switch | `imageDownload.ts` |
| 2 | a copy kept on the phone under the row's `asset_revision` is shown without asking again, however old | `imageDownload.ts` |
| 3 | a finished paper's question pictures come in parts of 12 (`/assets/links`, `/assets/pack`) | `paperPack.ts` `loadResultPictures` |
| 4 | its solution pictures too (`kind=solution`) | same |
| 5 | every picture is asked for as WebP (`format=webp`): one picture, get-ready parts, result parts | `imageDownload.ts`, `paperPack.ts` |

Each step includes the ones before. Now: **5**. To go back: lower the number, publish.

## The rule that keeps everybody safe
A step is used only for a row that carries the website's `asset_revision` (`assetGrants.ts`: `grant.step` = the switch for such
a row, else 0). A website that gives its old answers sends no `asset_revision`, so the app behaves exactly as before, whatever
the switch says. The app never looks at the phone number or the date.

## Fallbacks (the old routes are never removed)
- links refused 403 / 409 -> that kind (questions or solutions) loads one by one. No second try.
- links 404 -> the same parts through `/assets/pack` on our server.
- a part link fails -> that part through `/assets/pack`; that fails -> the rest of that kind one by one.
- a solution is only ever taken from an item that says `kind: "solution"`. Part names without flag 8, or a first part with no
  such item, stop the solution parts at once (the website's trap 1).
- picture type = the first bytes (PNG / JPEG / WebP); the `Content-Type` header is used only when they say nothing.
- a picture the phone cannot draw (`onError` of the image) -> its next try downloads the plain PNG afresh and replaces the kept
  copy (`drawAsPlain` in `assetGrants.ts`). So a phone that could not draw WebP heals itself, picture by picture.
- a phone that keeps no copies (no storage) -> one by one.
- leaving the result, or signing out, stops the parts.
- part links are never logged.

## How a result loads now (step 5)
1. The picture on screen (and its neighbours) is asked for at once, on its own, as before.
2. Meanwhile `loadResultPictures` checks which pictures the phone already keeps (`savedImages`), and for questions and for
   solutions fetches only the parts in which 4 or more pictures are missing (a short last part: all of them missing).
3. Part pictures are written to the phone's encrypted copy only (no screen picture is made until a screen asks); one a
   screen is already waiting for is shown at once. One part is in memory per worker; 2 workers in all.
4. While the parts run, the queue's own background loading for that result waits (`partLoads` in `paperAssets.ts`); what the
   parts did not bring is handed to it at the end.
The get-ready minute of a paper is unchanged except for the `format=webp` word at step 5 and the kept `etag`.

## Checked
- `node frontend/tests/pictures_new_answers_tests.cjs`: 32 checks against a pretend website that answers as the note says
  (each step alone, every trap of section 5, every fallback above). `pieces_isolated_tests.cjs` 16 still pass.
- `python tests/pictures_live_probe.py` (read-only, test number, one finished attempt): 22 of 22 on jeelive.ai, 23 Nov 17:36 UTC.
  Part links: `public, max-age=86400`; Cloudflare MISS on the first fetch, HIT on the second.
- The app's preview (web) against jeelive.ai, test number, result of JEE Main PYQ 22 Jan 2025 S2 (77 question + 110 solution
  pictures), a browser with nothing kept, one step at a time (`tests/pictures_step_ui.py`):

  | step | requests | KB | all pictures on the phone after |
  |---|---|---|---|
  | 0 (old way) | 187 | 11,172 | 17 to 21 s |
  | 2 | 187 | 11,172 | 17 s (opening again: 0 requests) |
  | 3 | 120 (7 parts) | 11,451 | 14 s |
  | 4 | 26 (16 parts) | 11,667 | 10 s |
  | 5 | 25 (17 parts) | 9,150 | 11.5 s (first WebP making on the website, edge MISS) |

  At every step: first picture drawn in 2 to 3 s as before, question 7 drawn in 0.01 to 0.1 s from the phone copy, opening the
  result again = 0 picture requests, no error box. At step 5 the pictures on screen were `image/webp`.

## NOT checked
- A real phone build. expo-image has a WebP decoder on iOS (SDWebImageWebPCoder) and Android (Glide) and takes data URIs of
  any type, but no WebP question has been seen on a real phone yet. If a phone cannot draw one, it heals itself (above); to
  stop asking for WebP everywhere, set the step to 4.
- The get-ready minute and a running paper against the live website with the new words (needs a real attempt to be started;
  the test number is read-only). Covered by the pretend-website checks only.
- WebP quality 90: not built on the website.
