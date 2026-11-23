# JEELIVE.AI website -> app project: picture answers, update 2 (replaces the "nothing built" parts of WEBSITE_PICTURES_REPLY.md)

Written 2026-11-23 from the website project's code and its isolated tests. Paste this whole note into the app project's chat.

## 0. Status in one look

- Built and tested in the website's preview. It reaches jeelive.ai with the NEXT deploy; the owner will tell you the day it is live.
- After that deploy it is ON FOR EVERY STUDENT (server setting `PICTURE_PILOT_PHONES`, default `*` = everyone).
  The owner can narrow it to some numbers for a while (comma list); students outside such a list then get today's answers, byte for byte.
- Until the owner says it is live, jeelive.ai answers as today. Keep every new switch off until then, and keep today's fallbacks forever.
- Website test: `tests/pictures_iso220.py` 66/66 (isolated throw-away database, 2026-11-23): old answers byte for byte when narrowed,
  new answers, and "no setting = every student". `tests/media_four_qa216.py` 33/33 with every student on.

## 1. What is built (your items 1, 2, 3)

| Your item | Built? | Notes |
| --- | --- | --- |
| 2. ETag / 304 / 206 on the one-picture route | Yes | Strong ETag; If-None-Match 304; single Range 206; If-Range; 416 |
| 2. `asset_revision` on question rows | Yes | `GET /attempts/{id}` and `GET /attempts/{id}/results` |
| 3. `/assets/links` and `/assets/pack` for a FINISHED attempt | Yes | Same part format, items now carry `etag` |
| 3. `kind=solution` on links and pack | Yes | Same rule as the one-picture solution route |
| 1. `format=webp` | Yes, LOSSLESS only | Same pixels. Quality 90 is NOT built (eye check on a diagram, graph and chemistry structure still open) |
| 3. Part files kept in storage + storage-signed links | No | Links still point to the website server, signed by the website (as in reply 1) |

Parameter names are exactly yours: `format=webp`, `kind=solution`, `asset_revision`. `limit` stays 12. The pack format is unchanged; only extra item fields were added (below).

## 2. One-picture route (every student after the next deploy)

`GET /api/attempts/{attempt}/questions/{question}/asset/{question|solution|piece}/{i}[?score_version=...][&format=webp]`

Headers on every 200 / 206 / 304:
- `ETag: "<32 hex>"` = first 32 hex of SHA-256 of exactly the bytes served. PNG and WebP of the same picture have DIFFERENT ETags.
- `Accept-Ranges: bytes`
- `Cache-Control: private, no-store` (unchanged on purpose: these are private pictures; the phone keeps its own copy as today).

Re-check rules:
- `If-None-Match: <etag>` -> `304`, empty body, same ETag. A list (`"a", "b"`), a weak form (`W/"..."`) and `*` are accepted.
- `Range: bytes=0-0` + `If-Range: <etag>` -> `206`, 1 byte, `Content-Range: bytes 0-0/<full length>`.
- `If-Range` with an old ETag -> `200` with the whole new picture.
- `Range: bytes=-10` -> last 10 bytes, `206`.
- A range outside the picture -> `416` with `Content-Range: bytes */<length>`.
- Several ranges (`bytes=0-1,4-5`) -> `200`, whole picture.
- A 304 for a picture that was saved at publish is answered without reading storage. A picture drawn from the PDF on each request is drawn first, then compared, so the 304 saves bytes but not server time.

`format=webp`:
- Answers `Content-Type: image/webp`, lossless (VP8L), same pixel size, every pixel compared with the PNG before it is sent.
- If the WebP would not be smaller, or anything goes wrong, the PNG is sent (`Content-Type: image/png`). Always read the type from Content-Type and the first bytes.
- Any other value (`format=jpeg`) -> PNG as before.
- The WebP is made on the first request and kept in the server's memory (48 MB). It is not stored as a file. After a server restart the first request makes it again.

## 3. `asset_revision` (every student after the next deploy)

- On every question row of `GET /api/attempts/{id}` and `GET /api/attempts/{id}/results`: a 16-character hex text.
- Different per question; the same on every read; the same in both answers.
- It changes when any of that question's pictures (question, pieces, solution) is replaced, and when the website changes how pictures are drawn.
- Before the deploy (or for a number outside a narrowed list) the field is absent (not null). Treat "absent" as "use your old cache key".

## 4. `/assets/links` and `/assets/pack` (every student after the next deploy)

Calls:
- `GET /api/attempts/{id}/assets/links[?look=cut][&kind=solution][&format=webp][&score_version=...]`
- `GET /api/attempts/{id}/assets/pack?offset=&limit=12[&look=cut][&kind=solution][&format=webp][&score_version=...]`

What changed:
- A FINISHED attempt now answers `200` (was `409 "This attempt is no longer active."`). It lists every question, bonus questions included.
- `kind=solution`:
  - running paper -> `403 "Solution assets remain private until submission."`
  - finished but sealed (live exam before release) -> the same `403`; question links still `200`.
  - finished and released -> `200` with the solution pictures (the same bytes as the one-picture solution route).
- Deleted test -> `404 "This test is no longer available."`. Unknown `score_version` -> `404`. Another student's attempt -> `404`. No sign-in -> `401`.
- A paper without a sealed pack -> `/assets/links` answers `404 "This paper loads its pictures through /assets/pack."` (as before).
- `/assets/pack` answers `Cache-Control: private, no-store` (as before).

Links answer (shape unchanged): `{ total, limit: 12, cdn: false, expires_at, parts: [path, ...] }`
- Each part is a path on the website server (no host; join it to the API host): `/api/media/pack/{pack_id}/{offset}-12-{flags}-{exp}-{sig}.bin`.
- Signed by the website (HMAC). No cookies needed. `Access-Control-Allow-Origin: *`, `Cross-Origin-Resource-Policy: cross-origin`.
- Lifetime as before: `exp` = end of the next UTC day (24 to 48 hours). Same links for every student of a paper on one UTC day.
- Part answer: `Cache-Control: public, max-age=N, s-maxage=N, immutable` (N = seconds left, at most 86400) and `ETag: "<sig>"`.
  A part in which one picture could not be drawn answers `no-store`; the missing picture is simply left out of the part. Load it on its own.
- `flags` (third number) is a sum: 1 = bonus questions / finished, 2 = cut look, 4 = new item fields, 8 = solutions, 16 = WebP.
  Old answers always have flags 0 to 3. Examples: running paper 4, finished 5, released solutions 13, released solutions in WebP 29.

Pack / part bytes (format unchanged): 4-byte big-endian header length, JSON header `{ total, items: [...] }`, then the picture bytes in item order.
- New items: `{ question_id, index, size, etag }` plus `kind` when it is not a question picture (`"piece"` or `"solution"`).
- `etag` = the ETag of that picture's bytes, equal to the one-picture route's ETag for the same picture and the same format.
  So you can store it and later re-check through the one-picture route with `If-None-Match` and get a `304`.
- Old answers keep `{ question_id, index, size }` (+ `kind: "piece"` for cut pieces). No `etag`.

## 5. Traps to guard against in the app

These matter only against a server that still gives the old answers (jeelive.ai before the deploy, or a number outside a narrowed list):
1. The old answers IGNORE `kind=solution` and `format=webp`. On a RUNNING attempt `/assets/links?kind=solution` then returns the QUESTION links.
   Only use a picture as a solution when its pack item says `kind: "solution"`. An item without `kind` is a question picture.
2. Detect the new answers from the response, never from the phone number or the date: an `ETag` header on the one-picture route,
   an `etag` on pack items, flags of 4 or more in a part name, `asset_revision` present on rows.
3. With the old answers a finished attempt still gets `409` on links and pack. Keep today's fallback to the one-picture route.
4. Always read the picture type from Content-Type and the first bytes. A `format=webp` call can answer PNG.
5. Never put a part link into logs or analytics.

## 6. Suggested order to switch on in the app (each with today's route as fallback)

1. Re-check with If-None-Match / `Range: bytes=0-0` + If-Range. Safe even against the old answers: they just send the whole picture (200), as today.
2. `asset_revision` in your cache key when present.
3. Links and pack for finished attempts (fallback on 409).
4. `kind=solution` (fallback on 403 / 409; check item `kind`).
5. `format=webp` last.

## 7. Not built, not checked

- WebP quality 90 (about 8 times fewer bytes in your test). Needs the eye check first; then it would be built behind the same switch.
- WebP copy stored as a file at upload; part files in storage with storage-signed links; a separate CDN (`MEDIA_CDN_URL` is empty).
- Whether jeelive.ai's edge (Cloudflare) caches real part links. Only `probe.bin` was seen as a HIT.
- Pictures are still drawn at 2x of the PDF page (1601 px wide in your sample), as today.
- Your E4 question (only 5 whole papers on the test account, 3 older paper IDs not found): still not checked. Send the 3 IDs through the owner.

## 8. Test copy (your E3)

- There is no agreed test copy with a test student. The website tests run on throw-away databases inside its own workspace.
- After the deploy, use the owner's test number `7004186276` on jeelive.ai read-only, as before; do not create test students on jeelive.ai.
