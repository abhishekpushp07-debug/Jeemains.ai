# JEELIVE app update packet (19 Nov 2026)

For the app team.

1. `APP_UPDATE_2026-11-18.md`: everything the app must build or change since the 26 Oct package, with priorities, exact API, every screen and message, and the acceptance checks. Read first.
2. `APP_UPDATE_2026-11-19.md`: what changed after that guide (three new analysis fields, new blocks in the 8 sections, Solutions cards, leaderboard, (i) texts). **Preview only, not on jeelive.ai until the owner's next deploy.** Section 8 lists the lines of the 18 Nov guide it replaces.

Other files:

- `APP_INTEGRATION.md`: the full website ↔ app contract (sections 1–16)
- `analysis_rulebook.json`: analysis rules and Hinglish labels as the server uses them
- `explain.js`: the website's function for the (i) "yeh kaise bana" texts
- `samples/`: real responses (request, status, headers, body) from a test copy of the updated server with synthetic students; `12_explain_texts.json` is the (i) texts for sample 01
- `SHA256SUMS`: checksums of the files

API: https://jeelive.ai/api. Same database, same student IDs, cookies only, Rapid Fire excluded.
No cookies, PINs, phone numbers, answer keys of live papers or real student data are in this packet.
Design tokens, fonts, logo and icons: the 26 Oct package (`/downloads/app-integration/`).
