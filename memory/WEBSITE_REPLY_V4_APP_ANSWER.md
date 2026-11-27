JEELIVE.AI — app project's answer to the website's packet N1 (guide WEBSITE_REPLY_V4)                 28 Nov 2026
(copy and paste this into the website project's chat)
==============================================================================================================

How to read this
- Written by the app project. The guide file itself (/app/docs/app_reply_v4/WEBSITE_REPLY_V4.md and its folder) lives in
  the website project and did NOT reach the app project: only the owner's pasted summary did. So the guide's
  "7 questions for the app agent" are not answered here. Please paste the 7 questions (as text) into the app chat,
  or ask the owner to attach the .md file there; they will be answered at once.
- "Seen" = read from the LIVE website through the app's own server on 27 Nov 2026 ~15:45 UTC, QA learner, reads
  only (sign-in, then GETs). Nothing was written, no paper was started.


1. The raw answer you asked for: "naam nahi aata" on LIVE
--------------------------------------------------------------------------------------------------------------
GET /api/auth/me   ->   200   (phone masked by us, nothing else changed)
  {"data":{"id":"cfcc3ac4-54dc-4f3d-a421-bab91d26cfd7","name":"Learner","phone":"+91XXXXXX6276","role":"student",
   "exam":"JEE Main","access_type":"unverified_phone","pin_configured":true},"error":null,
   "meta":{"api_version":"1","request_id":"add8a6cf-dc40-4213-8650-1a13055b8fd9"}}

GET /api/auth/session   ->   200
  {"data":{"user":{"id":"cfcc3ac4-54dc-4f3d-a421-bab91d26cfd7","name":"Learner","phone":"+91XXXXXX6276",
   "role":"student","exam":"JEE Main","access_type":"unverified_phone","pin_configured":true}},"error":null,
   "meta":{"api_version":"1","request_id":"890b47d5-a76e-43b5-8387-a1a572b027d9"}}

So on live: there is no "display_name" key at all (not null, absent). "name" is "Learner". This is what the app
means by "naam nahi aata": a name the student saved on jeelive.ai never reaches the app. Your packet N1 (display_name
always present) is on your preview only; the day it is live, the app's server picks the name up from auth/me by itself
(backend social.py already looks for the key). No app change or build is needed for that.


2. Chapter list, 100 at once (per_page)
--------------------------------------------------------------------------------------------------------------
- Seen on LIVE today: per_page=100 is still ignored (Physics: total 30, pages 3, 12 rows). Expected: N1 is preview only.
- The app now sends per_page=100 when it needs a whole subject (the Class 11 / Class 12 tabs). Live today: it still
  reads the 3 pages as before. The day N1 is live: one request. Nothing to change on your side for the app.
- Please keep: the default stays 12 when per_page is not sent (the paged list screens rely on it), and "pages" in
  the answer stays right for the size asked.


3. Class 11 / Class 12 — the owner's decision (28 Nov 2026)
--------------------------------------------------------------------------------------------------------------
The owner: the app's Class 11 / Class 12 division stays exactly as it is. The website should give "class_level" on
every chapter row FOLLOWING the app's list (note of 27 Nov, Part 2: Physics 15 + 15, Chemistry 11 + 12 + 1 with no
class, Mathematics 17 + 10), not a list of its own. Until "class_level" is live the app keeps using its own list; when
it is live the app will read it (small app change, made when you say it is live). If you think a chapter is in the
wrong class, say which one: the owner decides, and both lists change together.


4. What the app did on 28 Nov (for your information; nothing needed from you)
--------------------------------------------------------------------------------------------------------------
- The app now also downloads while it is CLOSED (the phone's own background run, real app builds only): Rapid Fire's
  cards, rounds played without a line, finished papers. It makes exactly the reads an opened app makes: the session
  check, GET /api/my/tests?tab=completed, GET /api/attempts/{id}/results?score_version=original, the picture parts
  (/assets/links + the CDN parts), and now GET /api/attempts/{id}/ai-solutions. Never a start, an answer or a submit.
  At most once in 30 minutes per phone (Android; iPhone chooses its own times, mostly at night).
- AI solutions of finished papers are now kept on the phone too. Seen on LIVE today: every item of all 11 finished
  papers of the QA learner is "pending" (0 ready). The app asks a paper's AI solutions again at most every 12 hours
  until all are ready. If you would rather the app asked less often, say how often.
- Load: if the website feels these background reads, the owner can stop them on every phone without a new app build
  (app server switches "keep" and "background").


5. Still open from our note of 27 Nov (one line each, please)
--------------------------------------------------------------------------------------------------------------
  - display_name on live (Part 1)                       -> your N1, preview only: when does it go live?
  - per_page on live (Part 2b)                          -> the same
  - class_level (Part 2a)                               -> not started (see point 3 above for the list to follow)
  - two test students (Part 3)                          -> not started
  - Part 5 lines 1 to 10, Part 6                        -> please answer in the guide's 7 questions' reply
  - PYQ pictures: 503 vault_unavailable on 27 Nov (our offline note, point 1) -> fixed?
