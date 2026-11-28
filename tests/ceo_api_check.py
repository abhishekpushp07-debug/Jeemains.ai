"""Read-only checks of the CEO API additions (shapes, auth, no-store, ordering). Never writes anything."""
import os
import re
import sys

import httpx
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
BASE = "http://localhost:8001/api/ceo"
TOKEN = os.environ.get("CEO_API_TOKEN", "").strip()
H = {"Authorization": f"Bearer {TOKEN}"}
ok = fails = 0


def check(name, cond, detail=""):
    global ok, fails
    ok, fails = (ok + 1, fails) if cond else (ok, fails + 1)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f" :: {detail}"))


def get(path, **params):
    return httpx.get(BASE + path, params=params, headers=H, timeout=30)


DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
if not TOKEN:
    print("CEO_API_TOKEN missing in this environment")
    sys.exit(1)

check("no token -> 401", httpx.get(BASE + "/rapid/daily", timeout=10).status_code == 401)

r = get("/users", limit=500)
check("users 200 + no-store", r.status_code == 200 and r.headers.get("cache-control") == "no-store", r.status_code)
items = r.json()["items"]
check("users carry is_test", all("is_test" in i for i in items) and not any(i["is_test"] for i in items), items[:2])
keys = [(-int((i["last_active"] or "0000-00-00").replace("-", "")), i["uid"]) for i in items]
check("users sorted last_day desc, uid asc", keys == sorted(keys))
r2 = get("/users", limit=500, include_test=1)
check("users include_test=1 shows test profiles", r2.status_code == 200 and r2.json()["total"] >= r.json()["total"]
      and any(i["is_test"] for i in r2.json()["items"]), r2.json()["total"])
check("users ordering stable across calls", [i["uid"] for i in get("/users", limit=500).json()["items"]] == [i["uid"] for i in items])

r = get("/rapid/daily", **{"from": "2026-11-01", "to": "2026-11-28"})
j = r.json()
check("rapid/daily 200 + no-store", r.status_code == 200 and r.headers.get("cache-control") == "no-store", r.status_code)
check("rapid/daily one row per day", len(j["rows"]) == 28 and j["rows"][0]["date"] == "2026-11-01", len(j["rows"]))
row = j["rows"][-1]
check("rapid/daily row shape", set(row) >= {"date", "players", "solo_completed", "duels_finished", "daily_plays", "by_mode"}
      and set(row["by_mode"]) >= {"solo", "duel"}, row)
check("rapid/daily by_mode adds up", all(sum(x["by_mode"].values()) == x["solo_completed"] + x["duels_finished"] + x["daily_plays"] for x in j["rows"]))
t = get("/rapid/daily", **{"from": "2026-11-01", "to": "2026-11-28", "include_test": 1}).json()
check("rapid/daily include_test counts more", sum(x["players"] for x in t["rows"]) >= sum(x["players"] for x in j["rows"]),
      (sum(x["players"] for x in t["rows"]), sum(x["players"] for x in j["rows"])))
print("   rapid (test included) busiest:", max(t["rows"], key=lambda x: x["players"]))
check("rapid/daily bad range -> 400", get("/rapid/daily", **{"from": "2026-11-28", "to": "2026-11-01"}).status_code == 400)
check("rapid/daily bad date -> 400", get("/rapid/daily", **{"from": "28-11-2026"}).status_code == 400)
check("rapid/daily default = last 30 days", len(get("/rapid/daily").json()["rows"]) == 30)

r = get("/economy/daily", include_test=1)
j = r.json()
check("economy/daily 200 + shape", r.status_code == 200 and r.headers.get("cache-control") == "no-store" and len(j["rows"]) == 30
      and set(j["rows"][0]) == {"date", "coins_awarded", "diamonds_awarded", "xp_awarded"}
      and set(j["totals"]) == {"coins_balance", "diamonds_balance"}, j.get("totals"))
print("   economy (test included) totals:", j["totals"], "busiest:", max(j["rows"], key=lambda x: x["xp_awarded"]))

r = get("/mission")
j = r.json()
check("mission 200 + shape", r.status_code == 200 and r.headers.get("cache-control") == "no-store"
      and {"links_total", "helped_total", "visits_daily"} <= set(j) and all(DATE.match(v["date"]) and "visits" in v for v in j["visits_daily"]), j)
r = get("/mission/links", page=1, limit=500, include_test=1)
j = r.json()
check("mission/links 200 + shape", r.status_code == 200 and j["page"] == 1
      and all(set(i) == {"uid", "code", "helped", "created_at"} for i in j["items"]), j)
check("mission/links limit capped at 500", get("/mission/links", limit=9999).json()["limit"] == 500)

r = get("/dream", include_test=1)
j = r.json()
check("dream 200 + shape", r.status_code == 200 and r.headers.get("cache-control") == "no-store"
      and isinstance(j["students_with_dream"], int) and all(set(c) == {"college", "count"} for c in j["top_colleges"]), j)
check("dream real-only <= with tests", get("/dream").json()["students_with_dream"] <= j["students_with_dream"])

check("overview still 200", get("/overview").status_code == 200)
print(f"\n{ok}/{ok + fails} passed")
