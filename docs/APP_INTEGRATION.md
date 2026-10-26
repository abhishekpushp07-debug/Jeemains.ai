# JEELIVE website ↔ native Expo integration

Updated: 2026-10-26. Canonical production API: **https://jeelive.ai/api**. This handoff supplements, and supersedes conflicting assumptions in, older Android handoff bundles.

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

## 3. Deployment boundary: LIVE auth vs prepared PIN auth

Read `evidence/canonical-api-contract.json` for the live route/schema snapshot. **Do not assume the current repository auth changes are deployed.**

### Current live student login

The deployed app currently accepts `POST /auth/phone` with `{ "phone": "<student-entered-number>" }`, using the existing phone profile. This legacy flow is unverified phone-only access, not proof of phone ownership. The frontend must not silently create a second account when a request fails.

### Prepared, tested, NOT yet published PIN update

The website preview implements the following, but the live cutover is held until the native client is ready:

| Action | Method/path (relative to API base) | Body |
|---|---|---|
| New student signup | POST `/auth/phone/signup` | `phone`, `pin`, `confirm_pin` |
| Existing student sign-in | POST `/auth/phone` | `phone`, `pin` |
| Own signed-in PIN change | POST `/auth/pin` | `phone`, `new_pin`, `confirm_pin` |

PIN fields are **strings of exactly four ASCII digits**; preserve leading zeroes. Signup never claims an existing phone-only profile. PIN change requires the current authenticated student and matching normalized phone; no OTP, old PIN or public reset is used. Other sessions become invalid after changing the PIN, but saved work and the account ID remain unchanged. Owner/reviewer password access is separate and never granted from a phone number.

Existing legacy students can set their first PIN from an existing signed-in session. A legacy user without an active session must not be given an insecure public claim/reset flow. Coordinate that recovery policy with the owner before rollout; do not reset or duplicate the account. The new login intentionally rejects phone-only requests after cutover. **Update native signup/login/PIN UI before publishing this backend revision.** Do not add an automatic phone-only fallback after any PIN failure.

PIN rate-limiting limitation: short-window per-number limits are enforced; successful sign-in resets that short window. A trusted/public ASGI peer also has an IP limit. The shared private ingress does NOT provide a trusted client IP yet; per-number protection plus existing auth concurrency applies there. Raw forwarded headers are not trusted. A longer-window failure budget and operator-managed trusted proxy configuration remain optional hardening, not claimed as completed protection or 500,000-user capacity.

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
| Exam chapters/mocks | GET `/exam-navigation/{slug}/catalogue?kind=chapters` | Slugs `jee-main`, `bitsat`, `comedk`; JEE date-wise PYQ uses its dedicated endpoint |
| Exam result history | GET `/exam-navigation/{slug}/history` | Current learner only |
| All India schedule | GET `/series/all-india-jee` | Never substitute locally invented dates/counts |
| All India own history | GET `/series/all-india-jee/history` | Auth required |
| My Tests library | GET `/my/tests` | Read current response filters/counts; do not create a second local history store |
| Saved-paper state | GET/POST/DELETE `/my/tests/saved/{set_id}` | Same canonical learner |
| Attempt history | GET `/attempts?page=1` | Current learner; 20 per page |
| Connection/content check | POST `/sets/{set_id}/preflight` | Body `{ "test_response": "A" }`; no timer starts |
| Start/full reattempt | POST `/sets/{set_id}/start` | See next section |
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

## 7. Start, autosave and two-device consistency

1. Fetch the summary and server rules; preserve official question/order/options/marking.
2. Run preflight successfully. Within its validity window, POST start with `{ "start_key": "<fresh UUID for this intentional start>", "device_checked": true, "preview": false }`.
3. Persist that start key until its response is known; retries reuse it. An already active same-paper attempt is returned, including the same ID/deadline. Use its server state, not a freshly reset timer. Full intentional reattempt after completion uses a NEW start key and retains old results.
4. Render the returned `questions` using their server UUIDs, `type`, `options`, text/HTML/math and `asset_count`. Scanned question and solution images must come from the protected crop endpoint; do not OCR/retype them or guess options.
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
7. Coordinate PIN client rollout, legacy-profile enrollment and website/backend release together. Re-run the existing same-ID/history checks after cutover. Until then, leave live auth unchanged.

## 11. Evidence boundaries and current status

- Production source-backed import: completed, not just a GitHub/source-code change.
- Live catalogue metadata and API schema: captured in the evidence files, with auth role/time explicitly recorded.
- Shared backend two-session full-paper flow and PIN/admin regression: test155 passed in isolation (12 new + 27 regression tests). Not a native-device test or production-load proof.
- Native existing-history/ID checks described by the app agent were reported by that agent, not independently reproduced here.
- Full native visual parity and actual native cookie persistence: app-agent/device verification pending.
- PIN + simple owner student directory: built/tested in preview; publication held for coordinated native compatibility. No payment/OTP service enabled.
- No passwords, cookies, signing keys, private source PDFs, answer-key dumps or private student exports are included in this package.
