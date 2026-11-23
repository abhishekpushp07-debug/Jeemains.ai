# App project ka note (owner ne 2026-11-23 ko website chat me paste kiya)

Neeche ka text owner ke message se liya gaya hai. Paste me line break mit gaye the; woh website agent ne wapas lagaye hain,
shabd nahi badle. Website ka jawab: /app/memory/WEBSITE_PICTURES_REPLY.md

---

JEELIVE.AI — note for the website project: lighter and faster question / solution pictures
==========================================================================================

Goal: the mobile app should load a whole paper's pictures in seconds on mobile data, without the app ever getting a
storage key. Everything below is ADDITIVE. Old app builds must keep working unchanged.

A) What the app calls today (keep all of this exactly as it is)
- One picture, with the student's session:
    GET /api/attempts/{attempt}/questions/{question}/asset/{question|solution|piece}/{i}[?score_version=...]
  Used for: continuing a paper, any paper opened outside the get-ready minute, and ALL result / solution pictures.
- Get-ready minute of a running paper only:
    GET /api/attempts/{attempt}/assets/links[?look=cut]           -> { total, limit: 12, parts: [url, ...] }
    GET /api/attempts/{attempt}/assets/pack?offset=&limit=12[&look=cut]
        -> 4-byte big-endian header length, JSON { total, items: [{ question_id, kind, index, size }] }, picture bytes in order
  The app fetches each part link WITHOUT cookies. A failed link falls back to /pack; a missing picture falls back to
  the one-picture route.
- The app keeps every picture on the phone (encrypted, per account, 256 MB at most), shows it again without asking
  for 3 days, then re-checks with If-None-Match / "Range: bytes=0-0" + If-Range.
- The app already reads PNG, JPEG, WebP and GIF (it looks at Content-Type and at the file's first bytes).

B) What the app side measured (read-only, test account, one finished JEE Main PYQ paper, 75 questions)
- 80 question pictures + 117 solution pictures = 197 website calls per student for one paper with solutions.
- Every picture is a PNG, 1601 px wide. 36 question pictures sampled: 561 KB on average, so about 46 MB for the
  question pictures of ONE paper. Solution pictures are similar (5 sampled: 44 KB to 709 KB).
- Every picture answer: "Cache-Control: private, no-store", no ETag, no Last-Modified, Range ignored (a re-check gets
  the whole file again, status 200), cf-cache-status DYNAMIC (every picture passes through the website server).
- From a data centre, 6 at a time: about 460 ms per picture (slowest 1.7 s).
- /assets/links and /assets/pack answer 409 "This attempt is no longer active." for a finished attempt.
- Question rows carry no asset_revision / source_revision / source_ref (all null).
- The same 12 real pictures re-encoded in memory (nothing stored): WebP lossless = 63 % of the bytes,
  WebP quality 90 = 12 %, WebP quality 80 = 8 %. At 200 % zoom, quality 90 text looked the same as the original
  (ONE text sample checked by eye; please also check a diagram, a graph and a chemistry structure before choosing).

C) What to add, biggest win first

1. A light copy of every picture (about 8 times fewer bytes)
- At upload (and once for everything already stored) also store a WebP copy: quality 90, same pixel size.
  Keep the original file untouched. Same for cut pieces.
- Serve the light copy only when the call carries format=webp:
    .../asset/{kind}/{i}?format=webp      (together with score_version when present)
    .../assets/links?format=webp          (with look=cut when present)
    .../assets/pack?offset=&limit=12&format=webp
  Without format=webp every route answers exactly as today (old builds, the website's own pages).
  If a light copy is missing, answer with the original (the app accepts either).

2. "Has it changed?" answers, so a saved picture is never downloaded twice
- One-picture route: send a strong ETag (a hash of the bytes served), answer If-None-Match with 304, and answer
  "Range: bytes=0-0" + If-Range with 206 (Content-Range with the full length).
- Add asset_revision to every question row in GET /attempts/{id} and GET /attempts/{id}/results: a short text that
  changes only when one of that question's pictures (question, solution or piece) is replaced, e.g. a hash.
  The app already puts it in its cache key.

3. Links straight from storage, for every screen
- Let /assets/links also answer for a FINISHED attempt (question pictures and pieces).
- Add solutions: /assets/links?kind=solution and /assets/pack?...&kind=solution, only when the one-picture
  solution route would answer 200 for this student (result released, not embargoed); otherwise the same refusal.
- Build each part file once per paper content version and keep it in storage (private bucket); do not build it
  per request. Give it a random, unguessable name that contains the content version; never list the bucket.
  Solution parts are separate files and are signed only after release.
- Each link is a signed storage link. Sign a part once and hand the SAME link to every student of that paper until
  it is close to expiry (for example: valid 2 hours, re-signed every hour). Supabase's CDN keys its cache on the
  whole signed URL, so a new signature per student is a cache miss every time. Sign in batches (createSignedUrls).
  Store the part files with a long cache time (they never change; new content = new file name).
- Links must work without cookies and must allow cross-origin GET (the browser version of the app fetches them).
- Keep limit = 12 and the pack format unchanged (the app checks limit === 12).
- Never write a signed link into logs or analytics.

D) Must not change
Paths, sign-in, attempt ids, score_version behaviour, embargo and locked-bonus rules, the pack format, and every answer
for calls that do not carry the new parameters.

E) Please answer in the app project's chat
- Which of 1, 2, 3 are live, with the exact parameter names if they differ from the above.
- Where the part links of /assets/links point today (website CDN or storage) and how long they live.
- Whether a test copy of the website exists (its /api address + one test student), so the app can run whole papers
  in tests without touching real students.
The app switches each item on only after this answer, with a fallback to today's routes.

---

Owner ki saath wali line: "Website ki taraf ek cheez check kar lo: test account par ab sirf 5 poore papers dikh rahe hain,
aur pehle wale 3 papers ke ID ab website par nahi milte."
