# Audit: JEELIVE proxy latency (authenticated) - 3 runs each, reports median ms
import os, time, uuid, statistics, requests
BASE = open("/app/frontend/.env").read().split("EXPO_PUBLIC_BACKEND_URL=")[1].split()[0].rstrip("/")
sid = "TESTlat" + uuid.uuid4().hex[:16]; H = {"X-JL-SID": sid}
requests.post(BASE + "/api/jl/auth/phone", json={"phone": "9000000001"}, headers=H, timeout=30)
for p in ["auth/session", "series/all-india-jee", "series/all-india-jee/streak", "my/tests?tab=progress&page=1",
          "exam-navigation/jee-main/catalogue?kind=chapters&subject=Physics&q=", "my/sets/9130b8b9-9ec0-567f-8028-20f4e9b92afa",
          "attempts/385dc381-b394-441e-89db-b281f9f081f2/results?score_version=original"]:
    ts, st, sz = [], 0, 0
    for _ in range(3):
        t0 = time.time(); r = requests.get(BASE + "/api/jl/" + p, headers=H, timeout=30); ts.append((time.time() - t0) * 1000); st = r.status_code; sz = len(r.content)
    print(f"{p[:60]:60s} {st} median={statistics.median(ts):.0f}ms max={max(ts):.0f}ms size={sz//1024}KB")
t0 = time.time(); r = requests.post(BASE + "/api/jl/sets/9130b8b9-9ec0-567f-8028-20f4e9b92afa/preflight", json={"preview": False, "test_response": "25"}, headers=H, timeout=30)
print("preflight", r.status_code, round((time.time() - t0) * 1000), "ms")
