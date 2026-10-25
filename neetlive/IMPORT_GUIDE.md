# Handoff to the NEETLIVE.AI builder

This is a portable **data and integration-reference bundle**, not a new standalone app.

## Content import
1. Verify each SHA-256 checksum in `manifest.json` before importing.
2. Create a NEET-owned database. Load arrays from `content/cards/*.json`, upserting by string `id` with a unique index. Set `retired: false`. Keep `exam: "NEET"`. Do not import `archive/` into the active bank.
3. Load `content/chapters.json` for Physics, Chemistry and Biology. Future subjects belong in this independent catalogue and require explicit validation/rendering support in the new app.
4. Keep answer keys/explanations private; public card lists must exclude `answer` and `explain`. Duels must also hide bank IDs and keys until settlement.
5. Render `diagram` with the included `BiologyDiagram.tsx` reference for native, or equivalent SVG primitives on the website. Shapes use theme token names, viewBox `0 0 320 194`, and labelled pointer coordinates. Highlight only `target`; no part names are embedded in the drawing.
6. Preserve 20-second, no-pen recall rules: at most 90 cards/chapter (120 for inorganic). Diagram cards replace text cards within the cap.

## Current API contract (reference only)
- `GET /api/rf/catalog?exam=NEET`: independent subject totals + `diagram_count`.
- `POST /api/rf/sessions`: `exam: "NEET"`, subject, optional chapter, count <=30, unique request_id. `diagram_only: true` requires Biology; `revision: true` chooses missed cards in that subject/chapter.
- `POST /api/rf/sessions/{id}/complete`: submit card_id/outcome/choice/ms; server determines correctness. Award and learning event are idempotent.
- `GET /api/rf/leaderboard?exam=NEET`: top 20, separate NEET XP and personal rank. Ties use user ID consistently.
- `GET /api/rf/revision?exam=NEET`: chapters ranked by accumulated misses among unresolved active cards; replay <=30. Incorrect/timeouts count, skips do not; a later correct answer clears that card.
- Duel create/join includes exam; random queues are isolated and mismatched invite groups are rejected. Rematches retain the original exam.
- `GET /api/rf/history?exam=NEET` and `GET /api/rf/duels?exam=NEET`: only NEET activity.

## Private progress migration
Run the explicit owner-only export command in README when ready. Do not upload the database dump into public assets. Import only into a protected service with verified identities and user/account mapping. The current `X-RF-User` private-pilot header is **not proof of identity**; implement verified authentication before any public release.

The reference code imports other JEELIVE modules. It is provided to describe the working contracts, not to claim that copying these files alone starts a new backend. The new app must provide its own auth, settings, wallet policy, frontend navigation and subject-expert-reviewed syllabus.

## Content provenance
Physics/Chemistry are independent copies of the current curated shared pool, ready for NEET-specific editing. Biology includes the existing 32 chapters and 18 original schematic questions. Diagrams are original drawings aligned with NCERT concepts, not official NCERT reproductions. An owner/subject-expert pass is still required; no new full-NEET-syllabus certification is claimed.

## Infrastructure note
The existing WebSocket / capped MongoDB `rf_events` transport was preserved. The 500,000-concurrent-user target has **not** been verified by this feature work; a new NEET service still requires capacity testing.