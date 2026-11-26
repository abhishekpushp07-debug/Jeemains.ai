# Part 5 — Rapid Fire in a browser: the app's, linked from the website

## 5.1 What it is, and who owns it

**Rapid Fire** is the app's game: 20-second formula cards, duels with friends, Gang War, Cup Night and All India Rapid. It is the app's own part. It runs on the app's server and its data (cards, coins, diamonds, friends, ranks) lives there.

**Rapid Fire also runs in a normal browser** (phone, iPhone, laptop) at:

```
https://jeelive-mobile.emergent.host/api/arena
```

This is the app's own live server. If the app's live address ever changes, the arena is `<new address>/api/arena`.

- It was built by **the app side** on 15 Nov 2026, from the owner's plan "students of the website can play Rapid Fire in a browser too". **The website agent did not build it and does not need to.** It is the app's own screens, made for the web, with only Rapid Fire in them.
- A student signs in there with **the same phone number and PIN as on the website** (Part 6). It is the same id, the same coins and diamonds, and the same friends as in the app.
- On a laptop it stays a phone-wide column on the blood-red stage. Home in its bar goes to jeelive.ai. The student's own profile has "Account & sign out".
- It is also what a person without the app gets from a match link ("Play in your browser").

[[shots: r01_arena_laptop | 17. Rapid Fire in a laptop's browser, from the app's server]]

## 5.2 What changed for it (26 and 27 Nov 2026)

The browser copy has to be built again whenever the app's screens change. Building it is one command on the app side, followed by the owner's Publish. It is not a code change.

- **26 Nov 2026:** built again with **All India Rapid's "Misfires" tab** (Part 4.5). This copy is in production since the owner's Publish of that day.
- **Found on 27 Nov 2026: in production its icons are empty boxes.** The copy's icon font sat in a folder that does not travel with a Publish, so production answers 404 for it. On the sign-in screen the phone, the lock and the eye are drawn as empty boxes, and so is every other icon that comes from that font; words, pictures and the game itself are right. The preview read the font from its own disk, so it was not seen there. **Mended on 27 Nov 2026, on the preview:** the font now ships under a name that travels; the build refuses to put a copy in place when one of its files would be left out of a Publish; and a test asks the app's server for every file the copy's pages name (`backend/tests/test_arena_web_complete.py`).
- **27 Nov 2026, the same new copy:** on a slow device the browser Rapid Fire now notices it and rests its decoration and its celebrations, as the app does; scores, coins and the game do not change. The copy talks only to the server it was opened from: no address of a workspace is in it (the build refuses one).
- Students get the new copy **with the owner's next Publish**. The state in production is read when this book is built (Part 3.7).

Nothing in the address, the sign-in or the website's part changes with a rebuild.

## 5.3 What the website does: a link, nothing else

1. Put a **"Rapid Fire"** card or button on the website's Home, near the top (next to the All India series or the practice area):
    - title "Rapid Fire";
    - line "20-second formula duels with friends. Same account." (an earlier note said 15 seconds; every card of Rapid Fire has 20 seconds);
    - button **"Play now"**, which opens `https://jeelive-mobile.emergent.host/api/arena` in the same tab.
2. Put a "Rapid Fire" item with the same link in the main menu. Optionally, add "Revise in Rapid Fire" on the result page.
3. **The link is a plain link:** no session, no cookie and no PIN in it.
4. "Rapid Fire" is always written as two words, both capitalised. The name and logo are JEELIVE.AI's own, the same on both sides.

**The website must not** copy Rapid Fire's code, cards or rules into its own project, keep a second copy of Rapid Fire's data, or change anything under `/api/arena` or `/api/rf/…`. Those are the app's. When the website wants something in Rapid Fire changed, it asks the app side in writing.

## 5.4 Later, not built: open Rapid Fire from the website without typing the PIN again

Today a student who is signed in on the website types the phone and PIN once more in the browser Rapid Fire. The plan to remove that is written down and **not built**. The website stays the only place that checks the phone and PIN, and the arena never sees the PIN or the website's cookies.

- **New website door (signed-in student only):** `POST /api/arena/ticket`. It makes a random one-time ticket (32 or more random bytes), stores only its SHA-256 hash with the student's id, and keeps it valid for 60 seconds and one use. It answers `{ "url": "https://<arena address>/api/arena/sso?ticket=<ticket>" }`. The website's Rapid Fire button would call it and open that url.
- **New website door for the app's server only** (server to server, behind a shared secret header): `POST /api/internal/arena/ticket/redeem { "ticket": "…" }`. It marks the ticket used in one step (failing if it is expired, used or unknown) and answers `{ "user_id": "<the same student id>", "name": "…", "pin_version": <n> }`.
- The app's server then gives the browser its normal Rapid Fire session and removes the ticket from the address bar.
- **Rules:** a ticket is never logged and never sent to analytics; that page sends no referrer; one use; 60 seconds at most; the student id never changes.

**Build this only when the owner asks for it.** The app side builds its half at the same time.

## 5.5 Not checked

- The website's Rapid Fire button: whether it is on jeelive.ai today was not checked by the app side.
- The copy of 27 Nov 2026 in production: it reaches production with the next Publish. On the preview it was walked in a browser at a phone's width, at 320 points and at a laptop's width, at full motion and at rest: it opens, signs in and plays a practice round answered by the browser (picture 17 is the copy of 26 Nov).
- A real slow phone: the rest on a slow device was checked in a browser slowed down on purpose, not on a phone.
