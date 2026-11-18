# JEELIVE app update packet (18 Nov 2026)

For the app team. Start with `APP_UPDATE_2026-11-18.md`: the list of everything the app must build or change since the 26 Oct package, with priorities, exact API, every screen and message, and the acceptance checks.

- `APP_UPDATE_2026-11-18.md`: the update guide (read first)
- `APP_INTEGRATION.md`: the full website ↔ app contract (sections 1–16)
- `analysis_rulebook.json`: analysis rules and Hinglish labels as the server uses them
- `samples/`: real responses (request, status, headers, body) from a test copy of the server with synthetic students
- `SHA256SUMS`: checksums of the files

API: https://jeelive.ai/api. Same database, same student IDs, cookies only, Rapid Fire excluded.
No cookies, PINs, phone numbers, answer keys of live papers or real student data are in this packet.
Design tokens, fonts, logo and icons: the 26 Oct package (`/downloads/app-integration/`).
