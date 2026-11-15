JEELIVE.AI — note for the website project (copy and paste this into the website project's chat)
==========================================================================================

What is new on the app side
- The Android app is called JEELIVE.AI again, with the website's original logo.
- The app now reads the website's exam list and sections (GET /api/catalog/exams and
  GET /api/catalog/exams/{slug}). A new exam or a new section made in the owner panel shows in the app by itself.
  Please keep these two endpoints and their fields (slug, key, name, shown, order, sections[].slug/name/
  description/layout/hidden/order) working as they are today.
- Rapid Fire now also runs in a normal browser (phone, iPhone, laptop) at:
      https://jeelive-mobile.emergent.host/api/arena
  (this is the app's live server; if the app's live address changes, use <new address>/api/arena)
  The link starts working after the app project is published once with this change. Check it opens before adding the button.
  Students sign in there with the same phone number + PIN as on the website. Same ID, same coins and diamonds as the app.

1) Add a "Rapid Fire" button on the website
- Home page: a card or button near the top (next to the All India series / practice area):
      Title: "Rapid Fire"    Line: "15-second formula duels with friends. Same account."
      Button: "Play now" → opens https://jeelive-mobile.emergent.host/api/arena in the same tab.
- Main menu / top navigation: a "Rapid Fire" item with the same link.
- Optional: on the result page, "Revise in Rapid Fire" with the same link.
- Do not put any session, cookie or PIN in this link. It is a plain link.

2) Name and logo — keep both places identical
- Name everywhere: JEELIVE.AI (wordmark "Jeelive.ai", tagline "SCORE 200+ WITH AI").
- Logo: the current original JEELIVE.AI logo (the red emblem + wordmark SVG). Do not redraw or recolour it;
  on light backgrounds the wordmark is near-black (#0F0F12), on dark backgrounds near-white.
- If the logo or name ever changes on the website, tell the app project so it changes there too.
- "Rapid Fire" is always written as two words, both capitalised.

3) Phase 2 (later): open the arena from the website without typing the PIN again
The website stays the only place that checks the phone + PIN. The arena never receives the PIN or the
website's cookies. Proposed hand-off:
- New website endpoint (signed-in student only): POST /api/arena/ticket
  → makes a random one-time ticket (32+ random bytes), stores only its SHA-256 hash with the student id,
    valid for 60 seconds and usable once, then returns
    { "url": "https://<arena address>/api/arena/sso?ticket=<ticket>" }.
  The website's Rapid Fire button calls this and opens the returned url.
- New website endpoint for the app server only (server-to-server, protected by a shared secret header):
  POST /api/internal/arena/ticket/redeem { "ticket": "..." }
  → atomically marks the ticket used (fails if expired, already used or unknown) and returns
    { "user_id": "<same student id>", "name": "...", "pin_version": <n> }.
- The app server then gives the browser its normal Rapid Fire session and removes the ticket from the address bar.
- Rules: ticket never logged, never in analytics, Referrer-Policy: no-referrer on that page, one use only,
  60 seconds max, student id never changes.
- Later still (Phase 3) Rapid Fire can move onto the website's own server and address.
