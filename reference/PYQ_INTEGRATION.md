# JEE Main PYQ — verified student contract

## Requested flow
Home JEE Main card -> PYQ -> full list immediately. Year/shift filters are optional inline chips, not extra drilldown pages. New paper: Start. Active attempt: Continue (never create a new attempt). Completed: Result + Re-attempt. Earlier results remain unchanged.

## Verified live sources
- Website: `https://jeelive.ai`.
- Website API client in `static/js/main.b56c5966.js`: base `https://jeelive.ai/api`.
- PYQ page in `static/js/723.a1748f42.chunk.js`: `GET /pyq/jee-main`.
- Theme: `static/css/main.cecdf12b.css` final root tokens: surface `#08080A`, cards `#14141C`, primary `#D91222`, text accent `#FF6974`, soft brand `#280D13`, line `#67202C`, foreground `#F8FAFC`, muted `#B0B0BF`, Figtree.

## Catalogue fields
`{items, years, total, server_now, source_note}`. Each item has `id`, `year`, `exam_date` (YYYY-MM-DD), `shift`, `count`, `minutes`, `maximum`, `attempt` (id/status), `latest_result_id`, `attempt_count`. The official web page uses these fields. There is no pagination parameter on that web page; all returned papers are listed and locally filtered.

## Start / resume / result contracts
- `GET /my/sets/{id}` rechecks active attempts before a new start.
- New/reattempt uses existing `POST /sets/{id}/preflight` (`preview:false,test_response:"25"`) followed by `POST /sets/{id}/start` (`start_key,device_checked:true,preview:false`). No intermediate set-detail screen or redundant confirmation click.
- Persist the same start key for uncertain retries; new acknowledged reattempt intent gets a new key. Keep per-user/set single-flight to suppress duplicate starts.
- Continue reads `GET /attempts/{exact_id}` and routes to that same attempt or its sealed result. It never calls `/start`.
- Results use existing `/attempts/{id}/results`, supplied typed text/images and answer-key-only state. Solution assets remain `/attempts/{id}/questions/{question_id}/asset/solution/{index}` and are never fetched before submit. Existing AI solutions are a separate, labelled optional source; no AI regeneration introduced for PYQs.

## Current upstream data blocker
During implementation on2026-10-26, direct authenticated live calls and the preview proxy both returned HTTP200 with `items:[]`, `years:[]`, `total:0`. Authentication and proxy work. Independent troubleshooting confirmed the same empty student catalogue. This does **not** prove the owner's upload failed or that no drafts exist; private studio/database state is not visible here. The website/backend owner needs to verify publication and student visibility of the intended full-length year/date/shift papers.

Do not relabel chapter tests as full-paper PYQs. An undocumented `/sets?kind=pyq` query returning chapter tests does not establish that they are official year/shift PYQs; that filter may be ignored upstream.

No fabricated papers are shipped. Real new PYQ attempt/solution mapping cannot be verified until a published row is available. Test-only network fixtures may verify UI states and request sequencing, but must be reported separately from real backend integration.

## Files
- `frontend/app/pyq.tsx`: direct list, filters, error/empty/loading states, focus refresh.
- `frontend/src/api/pyq.ts`: validated catalogue, state mapping, safe persistent one-tap start/resume.
- `frontend/src/components/PyqPaperCard.tsx`: row actions and status.
- `frontend/src/components/MathText.tsx`: supplied text maths, offline native KaTeX; native preview text fallback on web.
- Backend proxy already forwards this route; no new backend/auth code or env changes were needed.

## Follow-up: real source-contract bug and two verified data sources
- User supplied public source `abhishekpushp07-debug/Jeemains.ai`, inspected at commit `2e0c883da0c5c6ddfe7b008bfbfdeb7f5dbbc442`.
- `backend/resources/jee_pyq.json.gz` contains30 papers/2250 questions, each published/audienceall, and source-backed solution mapping. Manifest SHA256 `7ecfd145c0a8b2d8203c57778e8f8d41198b525174c8c2335a88b035b1803493`.
- **Confirmed frontend bug:** `live_enabled:false` is normal for regular PYQ practice. Upstream `catalog.available()` gates this flag only for import/chapter events, not normal PYQs. Removed both blanket false-flag rejections in local `paperState()` and `begin()`; still rely on authoritative detail/preflight/start authorization. Do NOT reintroduce this frontend restriction.
- Source-project API `https://campus-search-debug.preview.emergentagent.com/api/pyq/jee-main` returns30 genuine papers for the approved pilot. Current `https://jeelive.ai/api/pyq/jee-main` returns0 for its own pilot; two known package IDs also return404 on `/my/sets/{id}`. The phone has different learner UIDs on these sources (see protected test-credentials notes).
- These are different account/data environments. App env remains unchanged, no remote import/reset was invoked, and no source bank was duplicated into app MongoDB. Changing the app base would change which learner histories it displays and requires a conscious owner decision.
- Web browser checks must login AND navigate within one screenshot-tool call; calls use fresh contexts. Website login goes to homepage instead of following the `next` query. Authenticated home uses dynamic controls; inspect actual DOM rather than assuming landing-page anchor selectors.