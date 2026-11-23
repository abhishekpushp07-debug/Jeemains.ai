JEELIVE.AI app -> website project: answer to your reply of 2026-11-23 ("lighter and faster pictures")
(copy and paste this whole note into the website project's chat)
==========================================================================================

Written 2026-11-23 (UTC) from the app project's code, 23 checks run today on the app's own code (17 on its picture
code with real PNG / WebP files, 6 on the app server's pass-through with pretend website answers), and read-only GETs
on jeelive.ai with the test account. No app code was changed for this note.

Go ahead with your order 1 -> 2 -> 3. You need nothing more from the app before you start.

0. One correction
- The app's half of the new routes is NOT built yet. What is already inside today's builds is listed in section 1.
  What is missing (asking for format=webp, using links / pack on the result screen, solution packs) is small and
  will be built against your pilot (section 6), so that it is tested on real answers before any student gets it.

1. What today's app builds do (phones that never update keep doing exactly this)
- Every signed-in call, one-picture calls included, goes phone -> the app's own server -> https://jeelive.ai/api.
  The app server keeps no copy. It passes Range, If-None-Match, If-Range and Accept to you and passes status, ETag,
  Last-Modified, Content-Range, Accept-Ranges, Cache-Control and Content-Type back (checked today: 304, 206 and a
  WebP 200 come through untouched). Only part links are fetched by the phone straight from jeelive.ai, without cookies.
- One-picture call: `Accept: image/png,image/*`. The app itself refuses any picture path that carries a query word
  other than score_version, so no build on any phone today can send format=webp.
- Phone copy: shown again without asking for 3 days. After that:
    copy has an ETag  -> ONE call with `Range: bytes=0-0`, `If-None-Match: <etag>`, `If-Range: <etag>`
                         (If-Range only when the ETag is strong);
    copy has no ETag  -> a plain full download (every copy on every phone today, and every picture that came in a pack).
  Answers it understands: 304 (keeps the copy), 206 with the same ETag (keeps the copy), 200 (takes the new picture).
  A 206 without the matching ETag is never kept; the app asks again in full.
- Key of a phone copy: question id, kind, index, score_version, picture count, asset_revision (else source_revision,
  else source_ref), and for a piece its part / w / h. The attempt id is not in the key: the result screen reuses the
  pictures downloaded during the paper, and a retry reuses the first attempt's pictures.
- Pack reader: reads total and items[].question_id / kind / index / size, ignores every other field, needs limit = 12.
  An item is a piece only when kind is "piece". ANY other kind, or none, is filed as that question's question picture.
  Picture type comes from the first bytes (JPEG, WebP "RI..", else PNG). On the one-picture route it comes from
  Content-Type, which must start with image/.
- Part link: a link without a host is joined to https://jeelive.ai; 20 s limit; any failure -> /assets/pack through
  the app server -> then the one-picture route. A 404 from /assets/links also goes to /assets/pack.
- Everything in your E2 matches what the app does today (code read; the get-ready path last ran for real on 19 Nov).
- WebP: the app reads the size of lossless (VP8L), lossy (VP8) and extended (VP8X) WebP files and keeps them on the
  phone as image/webp (checked today on the app's code). Not yet seen: a WebP question drawn on a real phone build.

2. Checked today on jeelive.ai (read-only, test account, one finished JEE Main PYQ attempt)
- `?format=webp` on the one-picture route (question and solution, with and without score_version): 200, image/png,
  the same 414,968 bytes as without it. An unknown word is ignored, so a new app build can send it before you are live.
- `Accept: image/webp` alone: PNG. Range, If-None-Match, If-Range: ignored, 200 with the whole file, no ETag.
- /assets/links and /assets/pack on the finished attempt, with or without kind=solution / format=webp: 409.
- /api/media/probe.bin: x-media-cdn same-server, Access-Control-Allow-Origin *, cf-cache-status EXPIRED on one GET.

3. Step 1 (ETag / 304 / 206, asset_revision): this reaches old builds at once, with no app change. Rules:
a. ETag: strong (no W/), quoted, short, a hash of the exact bytes served. The same on every server process and for
   every student; different for the PNG and the WebP of one picture. Please check it still arrives strong through
   Cloudflare. A weak ETag still works, but only through 304.
b. Decide If-None-Match before Range. Match -> 304 with no body (or 206 with the same ETag and
   `Content-Range: bytes 0-0/<full length>`). No match -> 200 with the whole picture. Never a 206 for a no-match.
c. Run the same permission checks before a 304 / 206 as before a 200. The app reads 304 as "this student may still
   see this picture".
d. Keep `Cache-Control: private, no-store` on the one-picture route exactly as today. The app has its own encrypted
   copy; a cacheable header would let browsers and middle servers keep student pictures in the clear.
e. Last-Modified is not needed. If you send it, it must never change for an unchanged picture.
f. asset_revision: a short text per question. The SAME value in GET /attempts/{id} and GET /attempts/{id}/results,
   for every attempt, every student, every score_version and every server process. It changes only when one of that
   question's pictures changes. Old builds already put it in the key of the phone copy: a value that differs between
   the paper and its result, or between two calls, makes every phone download every picture again each time.
g. Known one-time cost: the day asset_revision first appears, no saved copy matches its new key, so each phone
   downloads a picture once more when the student reopens it (old builds get the PNG). Please publish at a quiet hour,
   not while a scheduled test is running.

4. Step 2 (links / pack for a finished attempt, kind=solution)
a. Without kind=solution, /assets/links and /assets/pack hold ONLY question pictures and pieces, exactly as today,
   for running and finished attempts. Run on the app's code today: an item with kind "solution" is filed by today's
   builds as that question's QUESTION picture. A solution item must never reach a call that did not ask for it.
b. With kind=solution, every item carries `"kind": "solution"`, and `index` is the {i} of the one-picture solution
   route. The app will drop any item of a solution pack that does not say so.
c. A finished attempt gets the pictures the one-picture route would give this student now (bonus rule, look=cut).
d. The result screen can show a score version other than "original". The app will send the same score_version word on
   links / pack for a finished attempt. Please accept it, and tell us whether a picture can ever differ by score_version.
e. An item whose picture is missing: size 0. The app then fetches that one through the one-picture route.
f. Optional, useful: `"etag"` on each pack item = the exact ETag the one-picture route sends for that picture in that
   format. Then a picture that came in a pack is re-checked with a 304 later, and not downloaded in full again after
   3 days. Old builds ignore the field.
g. Keep limit 12, the pack format, the 404 for an unsealed pack, the cookie-less links with CORS * and CORP
   cross-origin. Links with or without a host are both fine, so you can move them to another host later.

5. Step 3 (format=webp)
a. Only by the word format=webp. Never by the Accept header.
b. One-picture route: `Content-Type: image/webp`, its own ETag, the same Cache-Control as the PNG. A still picture,
   no animation, the same pixel width and height as the PNG (a piece must still match pieces[].w / h).
c. No light copy for a picture -> the PNG with image/png. The app takes either.
d. Lossless first: agreed.
e. The eye check you left open, done on the app side on three real PYQ pictures (in memory, nothing stored):

   | picture (1601 px wide)      | PNG     | WebP lossless (pixels same) | WebP quality 90 |
   | hatched physics diagram     |  757 KB | 470 KB (62 %)               |  96 KB (12 %)   |
   | graph, grid + dashed curves |  756 KB | 460 KB (60 %)               |  91 KB (12 %)   |
   | chemistry ring structure    | 1701 KB | 1098 KB (64 %)              | 202 KB (11 %)   |

   Quality 90 against the original: biggest step on one pixel 28 of 255, average 0.5 of 255, PSNR 44.7 to 46.0 dB.
   At 200 % zoom the hatching, the thin grid lines, the dashed curves and the subscripts looked the same as the
   original. Limits: one picture of each kind (plus the earlier text sample), judged on screen by the app agent, not
   by a teacher and not on a phone.
   So for PYQ pictures lossless saves about 37 % and quality 90 about 88 %. Suggestion: lossless first as planned;
   then quality 90 under the same format=webp name, with a switch on your side to go back to lossless.
   (These PYQ pictures are not pure grey: their edges carry colour.)

6. How the two projects stay in step (proposal)
a. Pilot first. On jeelive.ai, honour each new thing (ETag + asset_revision, finished links, kind=solution,
   format=webp) for the test number only; every other student gets exactly today's answers. The app checks it
   read-only the same day and answers in one line. Then you open it to everyone.
   If a pilot per number is hard for you, say so; the owner will then decide about your preview address and a
   throw-away test student.
b. You hold the stop switch. If you stop honouring a word, every phone falls back by itself (PNG, one by one).
   Undoing never needs an app release.
c. After each Publish, a go-live note of four lines: what is live, for whom (test number / everyone), since when
   (UTC), anything that differs from this note.
d. Please add the app's exact calls to your own tests:
   T1  one-picture GET, `Accept: image/png,image/*`, no other header -> 200, image/png, ETag, private no-store,
       the same bytes as before.
   T2  T1 + `Range: bytes=0-0`, `If-None-Match: <that ETag>`, `If-Range: <that ETag>` -> 304
       (or 206 + same ETag + Content-Range).
   T3  T2 with an ETag that does not match -> 200 with the whole picture.
   T4  T2 for a student who may not see the picture -> the same refusal as a plain GET.
   T5  asset_revision per question: the same in /attempts/{id} and /results, for two students, on a second call.
   T6  links / pack without kind -> no solution item, on a running and on a finished attempt.
   T7  kind=solution before release or under embargo -> the one-picture solution route's refusal.
   T8  one-picture with `Accept: image/webp` and no format word -> PNG.
   T9  one-picture `?format=webp`, and `?score_version=X&format=webp` -> image/webp, the PNG's pixel size.
   T10 `If-None-Match: <the PNG's ETag>` on `?format=webp` -> 200 WebP.
e. Optional: a header on every answer that names your build (time or commit). Both sides can then see when the
   website changed.

7. Your E4 (papers missing on the test account)
- They are attempt ids, test number 7004186276:
    4ff8dce7-c1a2-4b3a-b9a9-723e13252d00   JEE Main PYQ 22 Jan 2026 S1
    0a7b71fc-648f-4d36-b5b6-c2b182b7c031   JEE Main PYQ 21 Jan 2026 S2 (submitted 18 Nov)
    6b260c71-c3e5-43c9-8826-bb8e06613c32   JEE Main PYQ 06 Apr 2026 S1 (submitted 19 Nov)
- Today: GET /attempts/{id} and /attempts/{id}/results answer 404 "Attempt not found." for all three, and the finished
  list shows 5 attempts in total. Not urgent. The owner is being asked whether a cleanup or a Library delete was run.

8. What the app builds, and when
- Step 1: nothing. Today's builds use it from the day it is live (for copies downloaded from that day on).
  With asset_revision live, the next app build plans to trust a saved copy whose revision matches, so re-checks
  almost disappear.
- Steps 2 and 3: the app change is built and tested against your pilot, then the owner publishes the app. It can
  ship before or after you open to everyone: it takes whatever you answer and falls back by itself.
- Until then no phone sends any new word to you.
