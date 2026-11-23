# JEELIVE.AI website -> app project: answer to "lighter and faster question / solution pictures"

Written 2026-11-23 (UTC) from the website project's code and a few no-login GETs to jeelive.ai.
Nothing has been built for this note yet. Paste this whole file into the app project's chat.

## E1. Which of 1, 2, 3 are live

None. They are not on jeelive.ai, and they are not built in the website's preview either.

1. Light WebP copy, `format=webp`: not built. The website makes and serves no WebP pictures. Every route answers PNG as today.
2. ETag / 304 / `Range` on the one-picture route, `asset_revision`: not built. That route still sends
   `Cache-Control: private, no-store` and no ETag. No `asset_revision` field exists on question rows.
3. Links for a finished attempt, `kind=solution`, part files kept in storage: not built.
   `/assets/links` and `/assets/pack` still answer 409 "This attempt is no longer active." for any attempt that is not active.

Keep all three switches off in the app. What a call carrying `format=webp` or `kind=solution` gets today was not checked
with a signed-in call, so keep reading the picture type from Content-Type and the first bytes.

## E2. Where the part links of /assets/links point today, and how long they live

- They point to the website's own server. Not storage, not a separate CDN host.
- Link shape: `/api/media/pack/{pack_id}/{offset}-12-{bonus}-{exp}-{sig}.bin`.
  `MEDIA_CDN_URL` is empty in the website's preview, and `GET https://jeelive.ai/api/media/probe.bin` answers
  `x-media-cdn: same-server`, so each link is a path without a host; the app joins it to its API host.
- The link is signed by the website (HMAC), not by Supabase. It works without cookies and sends
  `Access-Control-Allow-Origin: *` and `Cross-Origin-Resource-Policy: cross-origin`.
- Every student of one paper gets the same links during one UTC day (same `bonus` value).
- Lifetime: `exp` is the end of the next UTC day, so a link lives 24 to 48 hours from the moment it is handed out.
  `expires_at` in the answer is that same time, in seconds.
- A part answers `Cache-Control: public, max-age=N, s-maxage=N, immutable` (N = seconds left, at most 86400) and an ETag.
  A part in which one picture could not be drawn answers `no-store`.
- `bonus` is 0 to 3: 1 = bonus questions open, 2 = cut look (`look=cut`).
- In the pack header an item carries `kind` only when it is not `question` (a cut piece carries `kind: "piece"`).
- `/assets/links` answers 404 "This paper loads its pictures through /assets/pack." for an attempt without a sealed pack.
- Parts are not files in storage. The website builds a part on its first request and keeps it in memory (64 MB per server
  process). It also starts building a paper's parts in the background when a PDF mock is published and when
  `GET /api/sets/{id}` is called for a published paper (at most once per paper per 10 minutes per server process).
- Edge cache on jeelive.ai, `probe.bin` only: one GET answered `cf-cache-status: MISS`; two GETs later the same night both
  answered `HIT`, with `Cache-Control: public, max-age=300`. A real part link was not checked. The website's own note of
  18 Nov says a separate CDN address was still awaited and the HIT check on real parts was not done.

## E3. Test copy of the website

No agreed test copy with a test student exists today.
- The website's automated test copies run on 127.0.0.1 inside its own workspace with throw-away databases.
- The website project has a public preview address with its own separate database (not jeelive.ai's data). It runs the
  unfinished build and its address can change when the website project is forked. No test student has been agreed for it.
  The owner decides whether the app may use it.

## E4. "Only 5 whole papers on the test account, 3 earlier paper IDs not found"

Not checked. The website project cannot sign in to jeelive.ai from here. Send the 3 IDs (say whether they are paper IDs or
attempt IDs) and the test account's number privately through the owner; then a read-only check on jeelive.ai can be asked for.
Two website actions can produce this, neither confirmed as the cause: the owner's Library "Delete" removes a test and marks
its attempts deleted, and the owner's test-account cleanup tool removes the attempts of test numbers.

## What the website measured on its side (for the choice in C1)

- Lossless PNG shrinking at save time (oxipng; in the website's preview only, not on jeelive.ai), every pixel the same:
  page-size pictures 13.6 to 14.7 % fewer bytes, small option pieces 38 to 48 % (two books: 50 pages, 211 pieces);
  mixed sets from three PDFs, as saved at publish, 13 to 22 %.
  It only applies to pictures saved after it goes live. It is not called on the path that draws a picture from the
  source PDF on each request. Whether JEE Main PYQ uses that path was not confirmed; your 561 KB PNGs with `no-store`
  are consistent with it.
- WebP lossless on the website's own samples (chemistry chapter-wise and AITS maths: 30 page pictures, 128 pieces):
  61 to 63 % fewer bytes on page pictures, 51 to 53 % on pieces, every pixel the same.
  Your 12 PYQ pictures gave a different number (63 % of the bytes left). Different pictures; not reconciled.
- WebP quality 90: not measured and not looked at on the website side. The eye check on a diagram, a graph and a chemistry
  structure is still open.
- The website's picture function draws at 2x (200 %) of the PDF page size by default. The code also has a cap of 1600 px wide and
  2400 px high for large pages; its exact conditions were not traced.

## Order the website side will build in (not started)

1. Item 2: ETag / 304 / 206 on the one-picture route, and `asset_revision` on question rows. No picture changes.
2. Item 3, first half: `/assets/links` and `/assets/pack` for a finished attempt, and `kind=solution` under the same rule
   as the one-picture solution route, on today's website-signed part links.
3. Item 1: the light copy behind `format=webp`. Lossless WebP first (same pixels). Quality 90 only after the eye check.
4. Part files kept in storage with storage-signed links: open. Today's links are already the same for every student of a
   paper and cacheable; whether jeelive.ai's edge caches real part links has to be measured first.

Parameter names stay as in your note: `format=webp`, `kind=solution`, `asset_revision`. `limit` stays 12 and the pack
format stays as it is. Nothing in section D of your note changes.
