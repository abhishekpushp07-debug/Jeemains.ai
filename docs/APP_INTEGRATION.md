# JEELIVE website ↔ native Expo integration

Updated: 2026-11-18 (first written 2026-10-26). Canonical production API: **https://jeelive.ai/api**. This handoff supplements, and supersedes conflicting assumptions in, older Android handoff bundles. **What changed since the 26 Oct package (Analysis 2.0, time capture, picture questions, start flow and more): read `APP_UPDATE_2026-11-18.md` first.**

## 1. Non-negotiable scope

- Website and native app must use this SAME production API and existing database for all academics, profiles, saved work and results. Do not use the website-project preview database as the app's content source.
- Preserve server-issued user IDs, phone profiles, question IDs, paper IDs, attempt IDs, score versions and receipts. No resets, migrations, duplicate student registrations or history deletion.
- **Rapid Fire is explicitly excluded. Leave its separate backend and accounts integration unchanged.** No Rapid Fire migration is part of this work.
- No payments, email verification or OTP integration in this increment.
- Browser and native session cookies may differ. Identity and progress must resolve to the same server-issued `user.id`, not the cookie string, a locally generated ID or a phone-string hash.

## 2. PYQ issue and production repair

The running production database had 222 existing sets but **zero date-wise PYQ sets**. The 30 reviewed papers existed in preview only. It was a missing production import, not an unpublished UI route or a reason to create another database.

The existing owner-authorized, insert-only/resumable importer has now completed against the canonical production service: **30 original PDF hashes verified; 90 records inserted (30 source-file records, 30 version records, 30 paper records); 30 published papers / 2,250 questions**. No student accounts, credentials, attempts or older papers were reset. The source with missing Q48–Q50 (23 January 2025 Shift 1) remains excluded; do not manufacture it.

`evidence/canonical-pyq.json` records the subsequent live catalogue check and every returned paper ID. Its `verification_role` is explicit: this export uses an authorised owner session on the SAME `/pyq/jee-main` endpoint, not an impersonated student. The app agent must re-run that GET with its existing canonical learner session and report the count. Do not mistake a 401 login wall for a zero-paper response.

`evidence/isolated-two-session-proof.json` is a real-backend, real-JWT, original-PDF test using a disposable database. It is explicitly **NOT production/native-device proof**. Two separate sessions for one learner passed preflight → start → save → resume same attempt → second save → submit → identical results → original solution PNG → fresh reattempt with old result retained. No customer test records were created. Native Expo was not available here; its parity must be verified by the app agent.

## 3. PIN cutover LIVE — verified on 2026-10-26

The owner explicitly requested publishing PIN first and receiving this handoff afterward. **The canonical website PIN login UI and live PIN API routes have now been verified.** This post-deployment PIN ZIP supersedes older ZIPs describing a phone-only login or a pending native-readiness hold.

Read `evidence/canonical-api-contract.json` and `evidence/live-pin-verification.json` for dated verification. Both `pin_signup_route_live` and `pin_change_route_live` are `true`; a phone-only login request is rejected with422. Do not silently downgrade to old phone-only login.

### Previous live student login (before this cutover)

The previous deployed app accepted `POST /auth/phone` with `{ "phone": "<student-entered-number>" }`, using the existing phone profile. That legacy flow was unverified phone-only access, not proof of phone ownership. Once the PIN revision is live, a phone-only request is rejected; the frontend must not create a second account when a request fails.

### Current live PIN API

Implement these verified live contracts in the native client:

| Action | Method/path (relative to API base) | Body |
|---|---|---|
| New student signup | POST `/auth/phone/signup` | `phone`, `pin`, `confirm_pin` |
| Existing student sign-in | POST `/auth/phone` | `phone`, `pin` |
| Own signed-in PIN change | POST `/auth/pin` | `phone`, `new_pin`, `confirm_pin` |
| Forgot PIN (not signed in) | POST `/auth/pin/reset` | `phone`, `new_pin`, `confirm_pin` |

Forgot PIN (added 2026-11-15, in preview; live on jeelive.ai only after the owner's next deploy): no OTP, no old PIN, no owner approval. It works for every existing student number, including older profiles that never had a PIN. On success it signs the student in and returns the same body and cookies as sign-in. A number with no account gets 404 "No account with this number": send the student to signup, never create the account here. Limit: 5 resets per number in 15 minutes, then 429 with `Retry-After`. Every other device on that number is signed out; attempts and results stay. Owner/reviewer logins cannot be reset this way. Live paper guard (added 2026-11-17): while that number has a live ranked paper running (All India series day or a live exam), the reset answers 409 "A live ranked paper is running on this number. Forgot PIN works again after that paper ends." Show the message as is. Signed-in Change PIN (POST `/auth/pin`) is blocked the same way with "... PIN change works again after that paper ends."

One account on website and app: use one server (`https://jeelive.ai/api`) and one student list. Keep the cookies the server sends and send them on every call; there is no bearer token. Identify the student by the server's `user.id`, never a local id. Rapid Fire keeps its separate accounts.

Check: sign up on the website, sign in on the app with the same number and PIN, and My Tests must show the same attempts. Then repeat the other way round.

PIN fields are **strings of exactly four ASCII digits**; preserve leading zeroes. Signup never claims an existing profile. Signed-in PIN change requires the current authenticated student and matching normalized phone. Forgot PIN (above) is the public reset chosen by the owner. Other sessions become invalid after any PIN change, but saved work and the account ID remain unchanged. Owner/reviewer password access is separate and never granted from a phone number.

A student who forgot the PIN, or an older profile that never set one, uses Forgot PIN. The login intentionally rejects phone-only requests. Do not add an automatic phone-only fallback after any PIN failure.

PIN rate-limiting (2026-11-18): only WRONG PINs are counted; a correct PIN is never counted and clears that number's count. 10 wrong PINs for one number within 15 minutes of the first one start a 15-minute wait for that number; during the wait every sign-in for it (even the correct PIN) gets 429 with `Retry-After` in seconds, and the PIN is not checked. Each wrong PIN returns 401 with the tries left in the message ("3 tries left before a 15-minute wait"); the 10th returns 429. One student address gets 100 wrong PINs per 15 minutes, then the same 15-minute wait for that address only. The address is the student's real IP: the hop just left of the last Cloudflare address in X-Forwarded-For (anything the client typed further left is ignored). When it cannot be told safely (no Cloudflare hop, private address) only the per-number limit applies, so students behind one proxy are never limited together. Sign-up, Forgot PIN and Change PIN keep their own attempt limits (5 per number, 60 per student address, per 15 minutes). Someone who knows a number can still make that number wait 15 minutes by typing wrong PINs; this is the trade-off of the short-PIN flow.

## 4. Session/cookie transport

- `POST /auth/login` is existing authorised staff email/password access, NOT student signup.
- `GET /auth/session` returns `{ "user": ... }`, or `user:null`. `GET /auth/me` returns the current user or 401.
- Login/signup set `access_token` and `refresh_token` as HttpOnly, Secure cookies. Preserve server cookie attributes and expiry. The JSON body contains a user profile, **not a bearer token**. The backend reads cookies; do not invent `Authorization: Bearer <user.id>`.
- Use one canonical host for login, refresh, JSON and image downloads. The native HTTP layer must retain `Set-Cookie`, persist the cookie jar securely across restarts where supported, and send cookies on subsequent calls. Confirm the Expo build's cookie behavior on-device; browser behavior does not prove native persistence.
- Web uses `credentials: 'include'`. On a protected 401, single-flight `POST /auth/refresh`, then retry once. No parallel refresh storms and no infinite retry. If refresh fails, require login while preserving account-scoped drafts.
- `POST /auth/logout` revokes that session. Discard credentials and prevent another learner from seeing cached results/drafts. Do not clear other devices' sessions except the explicitly documented PIN change.
- Web origins must remain explicitly allowlisted. Native requests may omit Origin; if sent, use the actual allowed canonical origin `https://jeelive.ai`, not an Expo URL invented as a web origin. Never solve a CORS issue with a wildcard or by disabling the unsafe-origin fence.
- Never log/export passwords, PINs, cookies, signing keys, owner email, student phone dumps or production learner/result IDs.

## 5. Response wrapper and errors

JSON routes use `{ "data": ..., "error": null, "meta": { "api_version": "1", "request_id": "..." } }`. Unwrap only when both `data` and `meta.api_version` are present. Errors normally expose `error.message`; some errors use `detail`. PNG endpoints return binary, not JSON.

```js
const API_BASE = 'https://jeelive.ai/api';
async function readJson(path, options = {}) {
  // Native implementation supplies its SAME secure cookie jar here.
  const response = await fetch(API_BASE + path, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message || body.detail || `HTTP ${response.status}`);
  return body?.meta?.api_version && Object.hasOwn(body, 'data') ? body.data : body;
}
const session = await readJson('/auth/session');
const catalogue = await readJson('/pyq/jee-main');
// Do not print session.user, cookies, personal results or answers in shared logs.
```

This abbreviated sample omits the single-flight refresh layer; use the complete behavior described above. Honour `Retry-After` on 429/503, back off with jitter, and treat empty success separately from failure. A GET response is not a new account.

## 6. Existing academic endpoints

Paths below are relative to `https://jeelive.ai/api`; do not append `/api` twice.

| Purpose | Method/path | Notes |
|---|---|---|
| Date-wise JEE PYQ | GET `/pyq/jee-main` | Auth required; `items`, `years`, `total`, per-user `attempt`, `attempt_count`, `latest_result_id` |
| Public published catalogue | GET `/sets?exam=JEE%20Main&page=1` | Public summaries, no answer keys |
| Public paper summary | GET `/sets/{set_id}` | Published/available only |
| My available papers | GET `/my/sets?exam=JEE%20Main&page=1` | Authenticated availability |
| My paper summary | GET `/my/sets/{set_id}` | Use before start, retains server rules |
| Exam list (new) | GET `/catalog/exams` | Auth required. Exams in Home order, built-in first; owner-created exams appear only after the owner chooses Show on Home |
| Exam sections (new) | GET `/catalog/exams/{slug}` | Sections in the owner's order; only sections with at least one live test for this learner are returned, with `live_count` |
| Exam section tests | GET `/exam-navigation/{slug}/catalogue?section={section_slug}` | Use the section `slug` from `/catalog/exams/{slug}`. Legacy `kind=mocks|chapters` still works. Response `section.layout` is `list` or `chapters` (subject › chapter) |
| Exam result history | GET `/exam-navigation/{slug}/history` | Current learner only |
| All India schedule | GET `/series/all-india-jee` | Never substitute locally invented dates/counts |
| All India own history | GET `/series/all-india-jee/history` | Auth required |
| My Tests library | GET `/my/tests` | Read current response filters/counts; do not create a second local history store |
| Saved-paper state | GET/POST/DELETE `/my/tests/saved/{set_id}` | Same canonical learner |
| Attempt history | GET `/attempts?page=1` | Current learner; 20 per page |
| Connection check (optional) | POST `/sets/{set_id}/preflight` | Body `{ "test_response": "A" }`; no timer starts; no longer required before start |
| Start/full reattempt | POST `/sets/{set_id}/start` | See next section |
| Begin now | POST `/attempts/{attempt_id}/begin` | Empty JSON body; ends the 60 s get-ready early; returns `ready_until`, `deadline`, `server_now` |
| Whole-paper pictures | GET `/attempts/{attempt_id}/assets/pack?offset=0&limit=12` | Active attempt only. Binary: 4-byte big-endian header length, JSON header `{total, items:[{question_id,index,size}]}`, then PNG bytes in order. Loop `offset` by `limit` until `total` |
| Whole-paper pictures through the CDN (preferred, added 2026-11-18) | GET `/attempts/{attempt_id}/assets/links` | Active attempt only. `{total, limit: 12, cdn, expires_at, parts:[url]}`. Fetch each `parts[k]` **without cookies** (it may be on another host); the body is exactly the `/assets/pack?offset=12k&limit=12` format. If a link fails twice, use `/assets/pack` for that part. See section 15 |
| All India rank | GET `/attempts/{attempt_id}/series-rank` | `state: sealed` (with `release_at`) until the day closes, then `ready` with `rank`, `total`, `top_percent` |
| Resume state | GET `/attempts/{attempt_id}` | Same attempt, not another start |
| Lightweight state | GET `/attempts/{attempt_id}/status` | Server time/deadline/status/grading |
| Save answer | PUT `/attempts/{attempt_id}/answers/{question_id}` | Receipt + revision protocol below |
| Mark visited | POST `/attempts/{attempt_id}/visit` | `{ "question_id": "<actual question UUID>" }` |
| Submit | POST `/attempts/{attempt_id}/submit` | Empty JSON body; 200 or 202 |
| Results | GET `/attempts/{attempt_id}/results` | May return 202 grading or embargo state |
| Original crop | GET `/attempts/{attempt_id}/questions/{question_id}/asset/{kind}/{index}` | `kind=question|solution`, zero-based index, authenticated PNG |
| Solution viewed | POST `/attempts/{attempt_id}/questions/{question_id}/solution-open` | After solution release only |
| Mistake-only retry | POST `/attempts/{attempt_id}/retry` | NOT the same as repeating the full PYQ paper |

The website's route `/exams/jee-main/pyq` corresponds to the dedicated catalogue. An app route can be named differently; paper, learner and attempt identities must not differ.

Latest PYQ UI revision (2026-10-26): only a year selector; render EVERY paper of that year in one vertical list (current reviewed metadata:2026 has19,2025 has11). No date filter, pagination or load-more. Dates/shifts remain on each card. Ignore/remove legacy `date` query parameters while retaining `year`. Cards alternate ruby/navy/plum/forest dark surfaces and keep Start/Resume/View Result/Attempt Again actions. This UI revision is newer than the previously delivered PIN LIVE ZIP's design snapshot; use the updated source `pyq.css`/`PyqCatalogue.js` or request a refreshed visual handoff before asserting native pixel parity.

## 7. Start, autosave and two-device consistency

1. Fetch the summary and server rules; preserve official question/order/options/marking.
2. POST start with `{ "start_key": "<fresh UUID for this intentional start>", "preview": false, "get_ready": true }`. Preflight is no longer needed. With `get_ready: true` the attempt has `ready_until` (start + up to 60 s): show the rules and load the whole paper with `/assets/pack`; the `deadline` already adds this time. Open the paper at `ready_until`, or call `/begin` when the student taps Begin now (the deadline then becomes now + full duration). Without `get_ready` the clock starts at once, as before.
3. Persist that start key until its response is known; retries reuse it. An already active same-paper attempt is returned, including the same ID/deadline. Use its server state, not a freshly reset timer. Full intentional reattempt after completion uses a NEW start key and retains old results.
4. Render the returned `questions` using their server UUIDs, `type`, `options`, text/HTML/math and `asset_count`. Scanned question and solution images must come from the protected crop endpoint; do not OCR/retype them or guess options.
   - **Picture questions (`render_mode: "source"`, `asset_count > 0`) — fixed 2026-11-18:** show only the pictures, exactly like the website. Do not show `text`, `accessible_text` or the `options` strings ("Original option A" / "Option 1, as printed in the source") as question words. The server now sends `text: ""` for these in the test and in results. `accessible_text` is only the screen-reader label of the picture. Option buttons show just the letter (or `source_option_labels`) and any `typed_options[key]`.
5. Queue edits per learner → attempt → question. Save body:

```json
{
  "value": "A",
  "marked": false,
  "confidence": 0.8,
  "revision": 1,
  "request_id": "<new UUID for this answer edit>"
}
```

`value` is a string (including numerical responses), maximum 30 characters at the handler; use an actually returned option label for MCQ. `confidence` can be omitted/null. First revision is 1; next is exactly the **currently acknowledged question revision + 1**, not a device-local total. Receipt includes `accepted`, `current_revision`, `duplicate`, `server_now`; `accepted.server_seq` orders accepted saves. Only acknowledge UI as saved after this receipt.

6. A network retry must resend the identical body/request_id. Reusing a request ID for different content is 409. A stale revision from another device is 409: fetch canonical attempt state and reconcile visibly, never silently overwrite or endlessly increase revisions.
7. On resume/reconnect/app foreground fetch canonical state and deadline. Local-only unsent drafts cannot magically appear on the other device. Label them pending, replay safely before deadline, and never represent them as server-saved.
8. Honour `server_now` and `deadline`. Backgrounding or switching devices never pauses/resets the exam clock. After deadline, the server rejects late drafts and seals accepted answers.
9. Flush acknowledged edits before submit. 202 means sealed and grading, not failed; preserve `receipt`, `sealed_seq`, `submitted_at`, follow `Location`/`Retry-After` and fetch results. Do not create another attempt because grading is pending.
10. Results may be `embargoed` until `release_at`; do not expose keys/solutions early. Preserve `score_version=original` unless the learner intentionally chooses an available corrected version.
11. Continue uses the existing active attempt ID. Full **Attempt Again** uses start on the same set with a new key. `/retry` creates an incorrect/skipped-question revision set and is a different feature.

## 8. Original solutions and image delivery

On released results, use `asset_count` and `solution_asset_count` for each question. Fetch every original solution crop in ascending index; some span multiple regions/pages. Keep white source backgrounds, natural aspect ratio, zoom/pan and mathematical fidelity. No CSS invert/filter/blend, no cropping away diagrams, no AI substitute for the supplied original solution.

Question images require ownership of the attempt; solution images additionally require completed/released state. Preserve `Cache-Control: private, no-store`; do not upload crops into a public app CDN or share cached assets between learner IDs. A native Image component may need explicit cookie handling or an authenticated fetch-to-private-cache adapter; a public URL alone is not sufficient. Binary 401 follows the same one-refresh policy. Existing reviewed AI explanation endpoints are optional enhancements, not replacements for original supplied solutions; no new paid AI calls are needed for parity.

## 9. Exact visual handoff

- `design-tokens.json`: live-browser computed root tokens, exact card gradients/shadows/type/spacing, CSS custom properties, normal/hover/focus/disabled/selected states and explicit page scopes. Values are measured, not guessed.
- `assets/brand`: active original vector logo + favicon. No pasted reference-image crop.
- `assets/fonts`: installed website Fontsource originals and TTF conversions for Expo, with upstream OFL licences. Figtree 400/500/600/700/800; Roboto Mono 400/500/600/700. Do not follow stale, unused Tailwind font-name defaults instead of the actual loaded families.
- `assets/icons`: original Lucide SVG paths generated from the installed library, with licence; use `lucide-react-native` equivalents or these SVGs, not emoji approximations.
- `reference-css`: exact current CSS source for every screen, plus load-order metadata. Later `vibrant-ui.css` rules override old colours in earlier sheets. Do not copy the old blue values near its top and miss the active black/crimson block further down.
- `references`: actual live public website at **390×844** and **1920×800**, no student data. State-reference measurements are separate from content fixtures.

Home palette mapping (applies BOTH guest landing `/` and signed-in `/home` through `.polished-home`):

| Card | Current identity |
|---|---|
| JEE Main | Royal blue/platinum; pale platinum CTA |
| All India series home banner | Ruby/polished onyx; ruby CTA |
| BITSAT | Bright amber/orange; dark espresso text and CTA |
| COMEDK | Teal/onyx; pale mint CTA |

Other pages intentionally keep the global black/blood-red system; do NOT paint every JEE card blue or every series card ruby. Use the per-selector mapping in the token file. Generic cards: dark `#14141C`; page `#08080A`; brand `#D91222`; body `#F8FAFC`. Source-paper pixels stay white/unfiltered. Selected navigation is red/white; disabled controls retain their actual reduced-opacity state.

Native rendering must reproduce **layered** gradients, thin inner highlights, borders, radii and shadows rather than flattening each card into a solid colour. CSS gradient angles require aspect-ratio-aware conversion to native/SVG coordinates; do not assume a 145deg CSS gradient is always start=(0,0),end=(1,1). Fonts and platform rasterisation can still differ; compare against the supplied mobile references before claiming 100% pixel parity. Honour reduced motion and card-shine pause; shadows must not obscure text or source images.

## 10. Ordered acceptance checks for the app agent

1. Keep API base canonical; log ONLY base URL + HTTP status/count, never identity credentials.
2. With the existing native learner session GET PYQ: expect 30 paper IDs matching `canonical-pyq.json`. Confirm 401/403/errors are not converted to empty lists.
3. In a controlled, explicitly authorised learner session, compare `/auth/me` on website and native. Compare user.id privately, not in chat/GitHub. No duplicate registration when an account exists.
4. Compare an existing saved result ID/score privately on both. Do not manipulate anyone else's attempts.
5. Use a disposable isolated environment for new tests, or obtain explicit approval for a dedicated production test learner before creating attempts. Run one supplied full paper start/save/resume/submit/solution scenario. Verify same attempt ID across devices, old result retained on reattempt, asset ordering and no active-attempt solution leakage.
6. Compare all card styles at 390px with supplied references, including selected/disabled and reduced-motion states. Keep Rapid Fire untouched.
7. Update native PIN signup/login/change now that the owner has requested the backend cutover first. Preserve valid sessions for first-PIN enrollment. Re-run the existing same-ID/history checks after installing the app update; reject old phone-only sign-in instead of falling back.

## 11. Evidence boundaries and current status

- Production source-backed import: completed, not just a GitHub/source-code change.
- Live catalogue metadata and API schema: captured in the evidence files, with auth role/time explicitly recorded.
- Shared backend two-session full-paper flow and PIN/admin regression: test155 passed in isolation (12 new + 27 regression tests). Not a native-device test or production-load proof.
- Native existing-history/ID checks described by the app agent were reported by that agent, not independently reproduced here.
- Full native visual parity and actual native cookie persistence: app-agent/device verification pending.
- PIN + simple owner student directory: deployed; live route/schema/validation and public login/signup forms verified without creating production students or attempts. Full real-auth signup/change/permissions tests were run in isolated databases. No payment/OTP service enabled.
- No passwords, cookies, signing keys, private source PDFs, answer-key dumps or private student exports are included in this package.

## 12. Exam structure: exams, sections, order and visibility (added 2026-11-14)

The owner now manages the student-facing structure from Super Admin › Exams & Content. The app must render the same places as the website, in the same order, from the API. Do not hard-code which sections an exam has.

1. Home exam cards: `GET /catalog/exams` → `items[]` with `slug`, `name`, `short`, `subjects`, `color`, `builtin`, `shown`, `order`. Built-in exams (`jee-main`, `bitsat`, `comedk`) keep their existing card designs. Owner-created exams (`builtin:false`) follow in `order`; `color` is one of `teal|amber|violet|rose|lime|sky`. A learner never receives an exam the owner has not shown on Home.
2. Exam page: `GET /catalog/exams/{slug}` → the exam plus `sections[]` in owner order: `id`, `slug`, `name`, `description`, `layout` (`list` or `chapters`), `kind` (`pyq`, `mocks`, `chapters` or `custom`), `live_count`. Only sections with at least one live test for this learner are returned. Always add a Results entry at the end (`GET /exam-navigation/{slug}/history`). A hidden or unknown exam returns 404.
3. Section list: `GET /exam-navigation/{slug}/catalogue?section={section_slug}&page=1` (plus optional `subject`, `q`). Items are already in the owner's order. For `layout=chapters`, first show `subject_counts`, then call again with `subject`. JEE Main `pyq` keeps its dedicated `GET /pyq/jee-main` screen.
4. Test names: use `title` from the API; the owner can rename tests and the API returns the new name. Mocks from a combined book use their printed names (for example "Mock Test 07"); the book title is not student-facing.
5. Availability: the owner can switch any test Unlive. Unlive tests disappear from every list and cannot be started; existing attempts, scores and results stay readable. Tests in a hidden exam are unavailable even by direct link (404 on summary/start).
6. `GET /my/sets/{set_id}` and `GET /sets/{set_id}` now include `catalog_path` (for example `/exams/bitsat/mocks`) so a back action can return to the right section.
7. Old `/book-series` routes are retired on the website; book mocks now appear inside their exam section. `GET /book-series/{id}` still answers and includes `path`.

Acceptance: compare the app's Home, exam page and one section list with the website for the same learner; names, order and counts must match.



## 13. Live exam start window and instant score (added 2026-11-14)

Applies to regular live exams (`competition:true`), not the All India series.

1. `GET /competitions` and `GET /competitions/{id}` items now include `last_start_at` (epoch seconds, may be null on older exams) and `can_start` (bool). `status` is unchanged (`scheduled|live|unlive|ended`). Show "Start by <last_start_at>" and hide the start button when `can_start` is false.
2. New starts are accepted from `start_at` until `last_start_at` (15 minutes). Each student's `deadline` is their own start + full duration. `end_at` = `last_start_at` + duration (the last possible finish). After `last_start_at`, `POST /sets/{id}/preflight` and `POST /sets/{id}/start` return 409 with a readable message; resuming an attempt already started still works.
3. Score on submission: `GET /attempts/{id}/results` before `end_at` still returns `status:"embargoed"` with `release_at`, plus `score_released:true` and `summary` (score, maximum, correct, incorrect, skipped, accuracy, subjects…). While scoring is running `summary` is null; poll again after `retry_after_ms`. `GET /attempts`, `GET /attempts/{id}` and My Tests show the summary as soon as it is graded.
4. Answers, solutions, worked solutions, question reports, revision attempts and the leaderboard stay locked until `end_at`, so students who started later in the window cannot receive answers early.
5. All India series attempts (changed 2026-11-17): score, answers and solutions open right after submission. Only the day's All India rank waits until the series day closes (`GET /attempts/{id}/series-rank`).

## 14. Test series for every exam and written questions (added 2026-11-15, preview only until deployed)
- `GET /api/series` (no login needed) lists every test series that is switched on: `id`, `title`, `exam {slug,name,color}`, `first_date`, `last_date`, `total`, `open_time`, `last_start`, `today`, `today_slot`, `builtin`. The JEE Main series is the item with `builtin: true`; its existing endpoints under `/api/series/all-india-jee` are unchanged.
- `GET /api/series/{id}/schedule` gives the day list in the same slot shape as the JEE series (`day`, `date`, `opens_at`, `last_start_at`, `closes_at`, `archive_at`, `state`, `ready`, `set_id`, `title`, `can_start`). `GET /api/series/{id}/history` (login) lists the student's own attempts.
- Starting, autosave, submit and results use the existing set and attempt endpoints. A live series attempt carries `series_id`, `series_date`, `mode: series_live`; its score and solutions open on submission and its rank at that day's `closes_at`.
- Changed 2026-11-16: `GET /api/catalog/exams/{slug}` lists an open test series inside its own exam as a section with `kind: "aits"`, `live_count: 0` and `series_path` (`/series/all-india-jee` or `/series/{id}`). Open the series screen when `series_path` is set. `GET /api/series` still lists every open series.
- Questions written in Super Admin have `render_mode: "written"`: show `text` (maths between `$` signs) and option texts, then `asset_count` images from the existing `/asset/question/{i}` endpoint. `asset_labels[i]` is empty for the question figure or `Option A`…`Option D` for an option figure. Solutions work the same way with `solution_asset_count`.
- PYQ papers made in Super Admin may have an empty `exam_date` and `shift: 0`; use `year` and `title` for those.

## 15. Question pictures through a CDN (added 2026-11-18, preview only until deployed)
- Why: at exam start the whole class downloads the same paper pictures (~7.4 MB per JEE paper). Through `/assets/pack` every student pulls them from the API server. Through `/assets/links` every student of one paper on one day gets the **same** public links, so a CDN downloads each part from the server once and serves everyone else itself.
- Flow: start (or resume) the attempt → `GET /attempts/{id}/assets/links` with the session → fetch every `parts[k]` with no cookies and no extra headers (simple GET) → read it with the same parser as `/assets/pack`. Keep the pictures in memory for the test.
- Links are handed out only for an active attempt, carry only question pictures (never answers or solutions), are signed and stop working after `expires_at` (1–2 days). Bonus pictures are left out until the bonus section opens; call `/assets/links` again after `/bonus`.
- Responses: `200 application/octet-stream`, `Cache-Control: public, max-age≤86400, s-maxage, immutable`, `Access-Control-Allow-Origin: *`. A tampered or expired link answers `404` with `no-store`. If one picture of a part could not be prepared, that part comes back with `no-store` and without that picture; load the missing one from `/questions/{qid}/asset/question/{i}`.
- `cdn: true` means the links point at the CDN host set in `MEDIA_CDN_URL`; `cdn: false` means they are on this server (`/api/media/pack/...`, relative: prefix the API host). `/assets/pack` stays as the fallback and is unchanged.

## 16. Analysis 2.0, time capture and display name (added 2026-11-18, live)
- After 18 Nov: `APP_UPDATE_2026-11-19.md` lists what changed next (analysis version 3: `rules`, `overview.class_subjects`, `journey` in `you` / `compare.profile`; Solutions cards; leaderboard on Overview; (i) texts). Preview only until the next deploy.
- Time capture in the player (`timeline` on answer saves and submit, `POST /attempts/{id}/timeline`), the 8-section analysis (`GET /attempts/{id}/analysis`, `/analysis/questions`, `/leaderboard`, `PUT /learnings`, `/analysis/report.pdf`, `/analysis/share.png`, `GET /competitions/{id}/compare/{handle}`) and `PUT /profile/display-name` are specified field by field in `APP_UPDATE_2026-11-18.md`, with real sample responses in `samples/` and the rules in `analysis_rulebook.json`.
