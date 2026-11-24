# JEELIVE.AI · CEO dashboard hand-off kit

For the agent building the separate CEO dashboard project. Read in this order:

1. `START_HERE_CEO_DASHBOARD.md` — the two servers, the app's CEO API, what to track and from where, how to build it, privacy.
2. `WHO_BUILDS_WHAT.md` — the ownership table of the three projects (app, website, dashboard) and what the website adds.
3. `examples/` — two real-shaped answers of the app's CEO API (personal values masked).
4. `app_server_reference/ceo_api.py` — the app server's code for those two endpoints (read-only reference; do not copy it into the dashboard).
5. `check_ceo_api.sh` — four curl checks once you have the address and the token.

The dashboard needs two secrets, entered by the owner in the dashboard project (never in code or chat): the app's `CEO_API_TOKEN`, and the website's own owner token. Contacts (phone numbers) come only from the website.
