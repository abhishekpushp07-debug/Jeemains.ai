# App agent's message, forwarded by the owner on 27 Nov 2026 (~20:42 IST), saved as received (summary kept close to his words)

Owner's ask with it: "dekho isme tumhare kaam ka kya hai ya tum dono me compatibility kya krne se bdhegi, sync me kaise kaam kroge". Also: read targeted, not whole files, and save what is read.

Owner's answers the same turn (ask_human):
- Order: first the small bugs, then the Rank page, then the rest.
- Colours: the website takes the app's look.
- Rank: do as the app ("Percentile se rank" replaced by Cut off).
- Two test students: leave for now.
- class_level: wait for live's 81 tests list; "App ne bna liya dekho mile kahi" (the app has made the list, look for it).

App's offline phase (app preview only, not published):
- Rapid Fire fully offline: all 16,158 JEE cards (Physics, Chemistry, Maths, English, Reasoning) download after sign-in (~1.8 MB), on mobile data too. Offline Solo Sprint: any chapter, 30/50/100 cards, 20 s a card, "Repeat missed". Offline round syncs when the net is back; coins/XP given once.
- Given papers' results: JEE Main first, then BITSAT, then others. Score, every question, own answer, key, solution and pictures kept on the phone paper by paper. Account -> "Bina internet". 512 MB cap, oldest removed first. Sign-out removes private results, Rapid Fire cards stay.
- Their tests: backend 23/23, Rapid Fire offline 33/33, papers 37/37, old features 72/72. Web preview only; nothing written to the owner's QA account.

Not there yet (app side):
- No download while the app is closed.
- Papers NOT attempted (JEE Main chapters, AITS, BITSAT) do not come to the phone: the website gives questions only on Start, and Start begins the timer; the app did not start any paper itself. "Iske liye website se alag feed chahiye" (needs a separate feed from the website).
- 5 JEE Main PYQ results kept WITHOUT pictures: "Website abhi PYQ pictures nahi de rahi (503 error)"; the app shows "0 / N pictures phone par".
- Note for the website agent: /app/memory/WEBSITE_OFFLINE_NOTE.md (in the APP's repo, not in this one).
- Not tested on a real phone; BITSAT result not checked; no load test; Rival, Friends, All India, Cups not offline.


## The app's note for the website (fetched 27 Nov from github.com/abhishekpushp07-debug/Jeemains.ai, branch App, memory/WEBSITE_OFFLINE_NOTE.md)
1. FAULT seen on LIVE 27 Nov ~13:55-14:40 UTC, QA learner, finished PYQ attempt `jee-main-pyq-2026-01-22-s1` (+4 other PYQ attempts), read only:
   - GET /api/attempts/{id}/questions/{qid}/asset/question/0 (plain and format=webp) and /asset/solution/0 -> 503 {"error":{"code":"vault_unavailable",...}}
   - GET /api/attempts/{id}/assets/links (plain, webp, kind=solution, kind=solution&webp) -> 200, total 76/119, 7/10 parts. Every part link 200 after ~10 s, body {"total":76,"items":[]}, cache-control public, max-age=60.
   - GET /api/attempts/{id}/assets/pack?offset=0&limit=12 -> same empty answer after ~10 s, twice 503 after 20 s.
   - Same account's chapter tests (cut pieces, look=cut) fine: 130 parts, ~50 ms each.
   - Their asks: an empty part must not be 200 (503 so a client retries), and never cached at the edge.
2. Ask: unattempted paper on the phone: GET /api/sets/{set_id}/sealed (name free) = the paper's questions + pictures as one encrypted file, edge-cacheable, same for every student; POST .../start also returns the key. Plus a list of what is worth fetching (next AITS day, chapter tests of his subject).
3. Offline start/submit: not asked now.
4. Small: GET /api/my/tests per_page up to 100; a row number that changes when the result changes (app uses `version` today, confirm); confirm part links are the same for every student of a set.
