> **OUT OF DATE since 14 Nov 2026.** Redis was removed from the backend in commit `923c12c` (deploy health check):
> `redis_runtime.py`, `redis_runtime.json`, the supervisor template, the `redis` / `hiredis` packages and their tests are
> gone, and there is no `jeelive-redis` service. `backend/metadata_cache.py` now keeps the same public Rapid Fire lists in
> the server's own memory. Everything below describes what was there between 27 Oct and 14 Nov; do not tell the owner
> that Redis is in use.

# API speed + private Redis — 27 October 2026

## User intent / scope
API fetching and Redis were explicitly prioritized before Android APK sizing.
The user selected app-private Redis and asked us to choose the implementation.
No new user account/key was required. Redis is SERVER-side; no native/frontend
dependency was added. "World fastest/lightest" is a goal, not a verified claim.

## Measured before / after
Same read-only runner, payloads, target URLs and sample counts were retained:
`backend/tests/perf_api_benchmark.py`, reports `test_reports/api_speed_before.json`
and `api_speed_after.json`. No benchmark result was fabricated from a fake loader.

| Measurement | Before p50 | After p50 | Scope |
| --- | ---: | ---: | --- |
| Select 30 unique Physics cards | 17.586 ms | **1.718 ms** | Warm backend selection, 15 samples; ~10.2x faster |
| RF catalogue over external preview | 82.562 ms | **68.878 ms** | 8 requests; ~16.6% lower median |
| RF card page over external preview | 73.652 ms | **62.174 ms** | 8 requests; ~15.6% lower median |
| RF catalogue, local HTTPX | 42.024 ms | 41.974 ms | 10 requests; essentially unchanged client-side measurement |
| RF card page, local HTTPX | 47.989 ms | 41.995 ms | 10 requests |

- Warm selection p95: 17.915 → 2.070 ms.
- External catalogue p95: **280.234 → 324.782 ms (worse)**; card-page p95:
  250.321 → 82.097 ms. These small samples include cold/network variance; no
  universal tail-latency claim is justified.
- Actual response payload hashes matched before/after. All protected data hashes matched.
- Server-Timing on warm metadata responses was approximately 0.7–1.2 ms. Local
  curl separately showed ~1.4–1.9 ms while HTTPX retained a ~42ms read delay;
  that client/transport discrepancy was not removed from the benchmark to inflate gains.
- These are preview/server observations, NOT physical Android measurements or
  a guarantee about the separate canonical website's first fetch.

## Implementation
### Private Redis and backend
- Supervised service `jeelive-redis`, private UNIX socket configured by
  `backend/redis_runtime.json`. Socket+directory mode0700, **no TCP listener**,
  maxmemory32MB/allkeys-LRU, no snapshots/AOF. Disposable, never a database of record.
- Namespace `jeelive:public-metadata:v1`: ONLY RF catalogue, public card pages
  with answer/explain/formula removed, and selection metadata `{id,chapter,fingerprint}`.
- **No auth, cookies, PINs, users, balances, live results/attempts or canonical
  academic responses are stored in Redis.** Mongo/canonical remain authoritative.
- Bounded L1, TTL60s for catalogues/pages and120s for selection metadata, same-key
  single-flight, short distributed contention lock, prefix-scoped invalidation on
  bank sync. Errors are not cached. Redis deadlines/circuit breaker fail open.
- Fresh decks fetch ONLY30 authoritative full documents instead of all2383 Physics
  documents every time. Final checks reject retired/missing/duplicate/bad-diagram
  cards even when selection metadata is stale; retry refreshes metadata once.
- Pure ASGI RF authorization guard preserves owner checks, token expiry and
  private no-store headers, without BaseHTTPMiddleware wrapping every response.
- HTTPX canonical pool enables HTTP/2 and45s keepalive, retaining explicit per-SID
  cookies and RejectAllCookies jar policy. No credential/write POST auto-retries.
- Web canonical JSON fetches explicitly use no-store; proxy responses vary by
  X-JL-Sid and auth responses are no-store, preventing an implicit browser cache
  from defeating account-scoped freshness. Explicit encrypted image caching stays.
- Original PNG/JPEG/WebP assets avoid wasted gzip recompression; JSON gzip level4.
  Server-Timing and public X-Cache headers aid measurement.
- Indexes added for ordered card pages and participant history; wallet/results
  are queried fresh, not replaced by a stale cache.
- Credentialed CORS now uses configured app/site origins, never `*`. Trusted
  preview preflight200 with exact ACAO, foreign-origin preflight400/no ACAO verified.

### App request coordination
- `frontend/src/resourceCache.ts` / `useCached.ts`: same-key concurrent reads
  share one request; account reset/invalidation aborts obsolete work and prevents
  stale data from repopulating another account's cache.
- RAM JSON cache capped at64 entries/2MiB encoded accounting and384KiB per item.
  Public RF catalogue can use a short freshness window; personal/wallet reads
  still revalidate. Optional storage failures cannot break successful fetches.
- One background prefetch lane, maximum6 queued tasks, foreground demand promotes
  its key; route blur removes queued speculative work. Home's speculative work
  reduced from5 requests to2, with the correct shared RF catalogue key.
- Focus revalidation respects public freshness; explicit pull-to-refresh forces
  a fresh read. Native academic API transport and encrypted question-image cache
  remain unchanged. Unsignalled GETs have a bounded32s deadline, not endless spinners.

## Verification
- Agent iteration46: cache/runtime/privacy/gameplay suites passed; service-stop
  fail-open, private socket/config, namespace privacy and original artwork bytes verified.
- Final rerun without repeated live PIN login: **25 passed,1 data-dependent sparse
  chapter skipped,1 canonical login deselected**. All frontend ResourceCache unit
  checks and full TypeScript check passed. Modified-source lint passed.
- Main 390px browser: first RF mount made exactly **one catalogue GET and one
  profile GET** despite mount+focus. Through shop/history navigation the catalogue
  stayed at one fetch, while the live profile was re-fetched (2 observed GETs).
- Actual isolated game completion credited2 Coins (250→252); result and shop/live
  profile showed252. All gameplay/wallet/history requests used real backend APIs.
- Browser-only fixture auth was intercepted explicitly; unrelated academic
  prefetch was isolated. This is test harness code, not production fake login.
  The agent's initial fake-PIN attempt without a harness correctly received401.
- All exact QA profiles/grants/matches/awards were cleaned. Protected baseline:
  344 profiles,10257 total Coins,399 award records; ownership and NEET fingerprints
  unchanged. All records belonging to the explicitly created QA identities were
  removed. Final inspection found two other JEE duel records (cancelled/ready)
  without those QA identities; they were deliberately retained, not reset.

## Runtime recovery
Repo files: `backend/redis_runtime.py`, `redis_runtime.json`,
`redis.supervisor.conf` (service template). Current service configuration is also
installed under `/etc/supervisor/conf.d/jeelive-redis.conf`.
Redis server binary and Python redis/hiredis/http2 dependencies are server-only.
If this runtime is recreated, ensure the Redis binary/service are provisioned
using this configuration. The API remains functional with a cache miss if Redis
is unavailable; speed then falls back to Mongo rather than breaking login/gameplay.
No public cache administration/debug endpoint was added. Do not use FLUSHALL.

## Remaining
- Physical Android cold/warm navigation, image decode/scroll/memory and actual
  APK/AAB size still need measurement. No under20MB guarantee is made.
- Canonical jeelive.ai502/503/read-timeout availability is NOT solved by local
  Redis. Private data is not served stale to hide an upstream outage. Diagnosing
  slow first fetches further needs canonical-side timing/logs as well as device traces.
- Public metadata freshness can lag briefly by the documented TTL/invalidation
  window; actual deck eligibility, auth, coins and results always use source checks.