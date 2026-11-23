JEELIVE.AI app -> website project: what the app needs now for "lighter and faster pictures"
(owner: paste this whole note into the website project's chat)
==========================================================================================

The owner says your half is built but not live on jeelive.ai. The app's half is not built yet. It will be built and
tested on your real answers before any student gets it. For that the app needs four things.

1. What is built, in a few lines
- Which of these are built: (a) ETag / 304 / 206 on the one-picture route + asset_revision on question rows,
  (b) /assets/links and /assets/pack for a finished attempt, and kind=solution, (c) format=webp (lossless or quality 90).
- Anything that differs from the app's reply of 2026-11-23: other parameter names, other field names, a rule you
  could not keep.
- Three answers still open from that reply: is score_version accepted on links / pack for a finished attempt (4d);
  can a picture ever differ by score_version (4d); do pack items carry "etag" (4f).

2. One place where the app can see the real answers (the owner chooses one)
- A. Pilot on jeelive.ai: the new answers only for test number 7004186276, every other student exactly as today.
  The app then checks read-only, the same day.
- B. Your preview: its /api address + one throw-away test student (number and PIN, sent through the owner) that has
  one finished paper with released solutions and one paper it can start. Say how long that address stays valid.
- The app needs no storage key and none of your code.

3. Before you publish for everyone
- The day and hour (UTC). The day asset_revision first appears, every phone downloads each picture once more,
  so a quiet hour, not during a scheduled test.

4. After each Publish, the four-line go-live note
- What is live, for whom (test number / everyone), since when (UTC), anything that differs from the notes.

What happens next on the app side
- (a) needs no app change: today's builds use it from the day it is live.
- (b) and (c): built and tested on 2A or 2B, then the owner publishes the app once. The app falls back to today's
  routes by itself when a new answer is missing, so your stop switch never needs an app release.
