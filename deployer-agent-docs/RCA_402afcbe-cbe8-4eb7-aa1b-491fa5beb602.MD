# RCA — Intermittent 30s→Cloudflare 520 on live app (campus-search-debug / jeelive.ai)

**Run:** 402afcbe-cbe8-4eb7-aa1b-491fa5beb602 (active, success) · tier_2 (Grow), 2 replicas · frontend_type=cloudflare · cluster deployment-cluster-05 · ns customers-app
**Follow-up to:** perfRCA402afcbe / testagent163

## Problem statement
~20% of low-rate public GETs (9/46 in testagent163), including `/api/health` (ServerTiming 0.5ms, no DB, admission bypass) and `/api/ready`, hang 30.1–30.6s then return **Cloudflare 520**. Preview 0/15 on the same probe. Cold Playwright networkidle also 30s timeout. Symptom is invisible in backend logs ("zero 5xx").

## What I verified (evidence)

1. **Reproduced live.** An 8-request burst to the edge: **3 timed out** — `net/http: request canceled (Client.Timeout exceeded while awaiting headers)`, elapsed 15000ms (my client cap is 15s; testagent measured the full ~30s → CF 520). The other 5 answered in 99–442ms. Rate ≈ 3/8, consistent with the reported ~20% (9/46). The hang is **"awaiting headers" = zero response bytes** — not a slow body, the origin produced nothing.

2. **Hung requests never reach the app.** The timed-out requests do NOT appear in either pod's uvicorn access log. Every request that DOES reach a pod returns 200 fast. So the stall is not uvicorn processing — the request is black-holed before delivery to a working backend. This is exactly why your earlier RCA saw "zero 5xx": the failures occur outside the backend.

3. **Both replicas are healthy AND both serve real traffic.** `get_pod_events`: pods `-4gxlv` and `-w42jm` both Running, ready=true, restart_count=0, no kills/OOM/evictions. `fetch_app_logs per_pod`: BOTH pods serve real `/api/*` (auth/session, series, catalogue, sets, health, ready) with 200s via CF edge IPs (104.22.x / 172.x). Neither replica is a zombie at the application layer.

4. **Fixed ~30s timeout = edge proxy, not app.** The tight 30.1–30.6s band is a fixed upstream/read timeout at the Cloudflare layer (CF 520 = origin returned empty/unexpected response), not variable app latency.

5. **No manifest overrides exist** (stock platform template). The in-pod readiness/liveness probe hammers `GET /health` → **404** (HTTP/1.0 from 127.0.0.1), while the app's real endpoint is `/api/health` → 200. Pods are nonetheless Ready (probe accepts the 404 as "server responded"), so this probe mismatch is NOT flapping endpoints and is NOT the cause of the 520s — it is a latent cosmetic/hardening issue only.

6. **Onset context:** 4 redeploys in ~4h (18:18, 19:54, 20:53, 22:14, 22:34→22:40), each minting a new pod IP set. The black-hole fraction is consistent with **stale/half-open upstream connections or stale Service endpoints** left in the Cloudflare-worker→k8s path after the rapid rollout burst.

## Root cause (proven location, platform layer)
A fraction of requests on the **Cloudflare edge/worker → k8s** connection path are routed onto a dead/half-open upstream (stale keepalive connection or stale Service endpoint from the recent rollout burst). Cloudflare opens/reuses the connection, the origin never responds, CF times out at ~30s and emits 520. The app (both pods), its code, DB, secrets, and tier are all healthy and under-loaded — ruling those out.

Not the cause, ruled out by evidence: backend 5xx/crash (no errors, pods never restarted), OOM/CPU/tier (no kills; app unloaded; `get_tier` cpu/mem well within limits), DB (health path has no DB and still hangs), secrets, DNS/SSL on the apex (jeelive.ai SSL active). The `/health` 404 probe is a separate latent item, not the 520 driver.

## Operator next steps (CF-ray correlated) — requires platform/infra access I do not have
- Pull the CF-ray IDs captured in `iteration_163.json` / `iter163_live_frontend_baseline.json` and correlate them against **CF Worker → origin fetch logs** and the **Cloudflare Tunnel / load-balancer origin pool** for this deployment.
- Inspect the **k8s Service endpoints** for workload `r-402afcbe-...` (ns customers-app, cluster deployment-cluster-05): confirm only the 2 current pod IPs are present and no stale/draining endpoint lingers; check kube-proxy/iptables/conntrack for half-open entries to prior-rollout IPs.
- **Flush/recycle the edge→origin connection pool** (worker keepalive / tunnel) so stale upstreams are dropped; verify connection draining fires correctly on redeploy.
- Confirm the CF origin read/connect timeout vs. uvicorn `--timeout-keep-alive` (default ~5s) — a keepalive-window mismatch is a plausible contributor to half-open reuse.

## Operator limits of this agent
My tooling sees pod state, app logs, DNS/SSL, DB, secrets, tier. I have **no visibility into, and no control over, the CF Worker logs, the Cloudflare Tunnel/LB origin pool, or Service-endpoint/conntrack health** — which is precisely the layer where the black-hole lives. Hence platform escalation. No tool lets me flush that pool.

## Secondary hardening (NOT the 520 cause; needs a future redeploy — deferred per "no new deploy yet")
- Add a plain `GET /health` → 200 route in the backend so the readiness/liveness probe gets a real 200 instead of a 404 (currently passes only because the probe tolerates non-5xx). Removes a latent failure mode where a stricter probe would drop a live pool.
- Consider raising uvicorn `--timeout-keep-alive` above the edge idle window to reduce half-open reuse.

## Known-problem status
OPEN platform-side incident: intermittent CF 520 (~30s) on a fraction of requests in the edge→k8s path following rapid consecutive redeploys. App end-to-end is NOT clean until this is resolved — do not mark healthy. Minor unrelated note: `www.jeelive.ai` SSL still `initializing` (apex `jeelive.ai` active); not related to the 520s.
