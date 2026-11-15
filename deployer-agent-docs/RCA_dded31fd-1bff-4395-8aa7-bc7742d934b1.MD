# jeelive.ai — READ-ONLY Health Report

Deployment: campus-search-debug (jeelive.ai)
Active run: dded31fd-1bff-4895... (dded31fd-1bff-4895-8aa7? see below)
Active run id: dded31fd-1bff-4895 — canonical: dded31fd-1bff-4895-8aa7-bc7742d934b1
Report time anchor: ~2026-11-15T21:34Z
Mode: strictly read-only. No deploy/restart/secret/DB-write/session performed.

Key tooling limits that shape several answers (stated up front):
- Backend access logs (uvicorn) retain ~24h max and the log line format carries **no User-Agent and no response-time field**. So: 7-day log counts fall back to 24h; User-Agent split is not derivable from logs; ">10s" and "30s hang" latency cannot be measured from access logs.
- The read-only DB tool exposes find/count/distinct/list_* only — **no dbStats/collStats (byte sizes), no profiler/slow-query log, no backup/snapshot metadata**.
- No live-metrics tool, so **live CPU/memory utilization** is not readable (only the tier's configured requests/limits).
- Frontend is served by Cloudflare/R2; I can read the repo source but not the live Cloudflare response headers. /api reachability was confirmed independently (health 200).

---

## 1. Deploy history (last 5 runs)
All 5 most recent runs are type=redeploy, status=success:
1. dded31fd-1bff-4895-8aa7-bc7742d934b1 — created 2026-11-15T12:22:58Z, completed 12:29:07Z — **ACTIVE / serving now** — image customers-app-5@sha256:8f159f50...d5cdf
2. a10e616c-9936-4c1f-b07f-0abdfaf7772e — 2026-11-15T11:14:46Z → 11:20:34Z — success
3. 625bb77c-8ee4-460c-bb11-36be29eace7f — 2026-11-14T22:10:25Z → 22:16:44Z — success
4. c7c23017-0e07-40f3-ad68-968b0e383e2c — 2026-11-14T21:27:24Z → 21:33:40Z — success
5. 5bd79e09-006f-4c44-be14-1e4b8895ef46 — 2026-11-14T18:35:23Z → 18:41:46Z — success

The most recent run (dded31fd) completed successfully, and the deployment's active_run_id = dded31fd with run_image = customers-app-5@sha256:8f159f50... — i.e. **that build is what is serving now.** Live /api/health returned 200 on all 12 external probes.

## 2. Scheduled maintenance / nightly repair
- **WEBHOOK_CRON_SECRET is set** on the active run (present, not empty). Value not read.
- POST /api/cron/maintenance in the last 24h (log retention cap): all hits returned **200 OK** (35 log lines, zero non-200). No failures.
- tejas_cron_receipts: **189 receipts written in the last 7 days** — cron maintenance is running and recording itself.
- tejas_migrations: **1 record, state "done"** (`library-2026-11-bitsat-and-jee-main-chapters`, finished).
- tejas_integrity_archive: **20 records** present (nightly integrity repair has run and archived orphaned cohort entries, reason "attempt no longer exists").
- Conclusion: the first nightly repair / integrity run has completed and is recurring.

## 3. Errors & slowness (24h window — see log-retention limit)
- 5xx by path: exactly **one 503** — `GET /api/studio/sets/.../questions/.../asset/question/0` → 503 Service Unavailable. No 500 / 502 / 504 observed.
- 503 "capacity_busy": the `capacity_busy` body label does not appear in access logs; the one 503 above is the only 503 in-window and is an asset fetch, not confirmed as capacity_busy.
- Requests slower than 10s / 30s hangs / Cloudflare 520: **not measurable** — access logs carry no latency field, and Cloudflare 520s are edge events that do not reach the backend log. No backend evidence of hangs in-window. (Re: earlier RCA 402afcbe — no recurrence visible in backend logs, but this window is only 24h.)
- Pod restarts / OOM: **0 restarts on both pods, no OOMKilled, no kill findings.**

## 4. Production topology
Tier_4 "Elite": **2 replicas** (max 2, HPA disabled, VPA enabled).
Per pod — CPU request 2 / **limit 4 cores**; memory request 8Gi / **limit 16Gi**; ephemeral-storage 10Gi.
Both pods Running, Ready, restart_count 0.
**Live CPU/memory utilization: not available** (no metrics tool) — only the configured requests/limits above.

## 5. In-browser PDF reader (pdf.js / CSP)
- **No pdf.js worker is shipped by this build.** No `pdfjs-dist`/`react-pdf`/`pdf-worker` dependency in frontend/package.json, and no `pdf.worker.*` file anywhere in source. Only a static document file exists (frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf).
- **No Content-Security-Policy is defined anywhere** in the repo — not in nginx.conf (it only sets Content-Type text/plain on two locations), not in the frontend, and there is no `_headers` / `wrangler` / Cloudflare worker file. So nothing in the deployment sets worker-src/script-src or blocks `blob:`.
- Net: the deployment does **not** block worker-src/blob:, but it also does **not currently ship a pdf.js in-browser reader**. (Caveat: live Cloudflare response headers not directly readable here; conclusion is from source + confirmed /api health.)

## 6. Database
DB: campus-search-debug-test_database.
- **Total DB size: not available** (tool has no dbStats/collStats). Byte sizes per collection also unavailable.
- Largest collections by **document count** (sizes not exposable):
  1. tejas_book_pages — 8,962
  2. tejas_question_solutions — 7,100
  3. tejas_files — 5,564
  4. tejas_audits — 976
  5. tejas_sets — 288
  6. tejas_cron_receipts — 189 (last 7d)
  7. tejas_attempts — 49
  8. tejas_cohort_entries — 45
  9. tejas_packs — 34
  10. tejas_integrity_archive — 20
  (also: phone_profiles 14, books 2, book_page_history 2, users 1; smart_questions / ai_solutions / book_parts / smart_papers / question_reports = 0)
- Slow queries >1s: **not available** — no profiler/slow-query log access via the read-only tool.
- Backup/snapshot visibility & last snapshot time: **not available** — no tool to read Atlas backup metadata. (Confirm in the MongoDB Atlas console.)

## 7. Do mobile-app sign-ups reach this server?
- POST /api/auth/phone in the last 24h: 11 requests — 10×200, 1×401. No POST /api/auth/phone/signup lines appeared in the 24h window.
- All of these arrived via Cloudflare edge IPs (104.x / 172.x). **User-Agent split (okhttp / Dart / CFNetwork / Expo / ReactNative vs browser) is NOT derivable** — the uvicorn access-log line format contains no User-Agent. So I cannot prove device origin from logs.
- tejas_phone_profiles: **1 created in the last 7 days** (14 total). (count only — no phone numbers/ids read.)
- So phone-auth endpoints are live and returning 200s, and phone profiles are being created, but whether a given request originated from the mobile app vs a browser cannot be confirmed from the available logs.

## Overall
App is healthy: most-recent build is live, /api/health 200, 2/2 pods Ready with 0 restarts/0 OOM, cron maintenance + nightly integrity repair running and recorded, only a single 503 (one asset fetch) in the last 24h. No deployment-side CSP blocks the PDF reader (though no pdf.js worker is bundled yet). Several requested metrics (byte-level DB size, Atlas backups, live CPU/mem, per-request latency, User-Agent split) are outside this agent's read tooling and must be checked in Atlas / Cloudflare / an APM.
