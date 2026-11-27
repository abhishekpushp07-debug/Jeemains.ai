# dashboard/: for JLive Command (the CEO dashboard)

This folder is for the separate CEO dashboard project ("JLive Command") and for the jeelive.ai website, so all three
read the same facts.

| File | What it is |
|---|---|
| `APP_ANSWERS_V1.md` | The app's answers to the dashboard's 17 questions (identity, screens, events, build, contacts, CEO API) |
| `../memory/CEO_DASHBOARD.md` | The earlier app handoff: CEO API auth, `/api/ceo/overview`, `/api/ceo/users`, what comes from the website |

Rules for anyone reading this:
- **The join key is `uid`, the website's own user id.**
- The app CEO API is read-only: `Authorization: Bearer <CEO_API_TOKEN>`, server to server only.
- Never put the token or contact numbers in browser code or in this repo.
