# Audit script: Rapid Fire card bank quality + API latency + profile/history math (run: python audit_rf_data.py)
import os, time, uuid, json, re, collections, concurrent.futures as cf
import requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or open("/app/frontend/.env").read().split("EXPO_PUBLIC_BACKEND_URL=")[1].split()[0]
BASE = BASE.rstrip("/")
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
H = {"X-RF-User": UID}
S = requests.Session()


def t(method, path, **kw):
    t0 = time.time()
    r = S.request(method, BASE + path, timeout=60, **kw)
    return r, round((time.time() - t0) * 1000)


out = {}
# 1. full bank
r, ms = t("GET", "/api/rf/cards?page=1&limit=200")
pages = r.json()["pages"]
out["cards_total"] = r.json()["total"]
out["cards_page_ms"] = ms
cards = r.json()["items"]
with cf.ThreadPoolExecutor(8) as ex:
    for res in ex.map(lambda p: S.get(f"{BASE}/api/rf/cards?page={p}&limit=200", timeout=60).json()["items"], range(2, pages + 1)):
        cards += res
print("fetched", len(cards))

issues = collections.defaultdict(list)
prompts = collections.defaultdict(list)
for c in cards:
    o = c.get("options", [])
    if len(o) != 4:
        issues["options_not_4"].append(c["id"])
    if not isinstance(c.get("answer"), int) or not (0 <= c["answer"] < len(o)):
        issues["answer_out_of_range"].append(c["id"])
    norm = [re.sub(r"\s+", "", str(x)).lower() for x in o]
    if len(set(norm)) != len(norm):
        issues["duplicate_options"].append((c["id"], o))
    if any(not str(x).strip() for x in o):
        issues["empty_option"].append(c["id"])
    if not c.get("explain"):
        issues["no_explain"].append(c["id"])
    for fld in ("prompt", "formula", "explain", *[f"opt{i}" for i in range(len(o))]):
        s = c.get(fld, "") if not fld.startswith("opt") else str(o[int(fld[3:])])
        if s.count("$") % 2 or s.count("{") != s.count("}") or "\\\\(" in s or re.search(r"\\(frac|sqrt|times|alpha|theta)", s):
            issues["latex_suspect"].append((c["id"], fld, s[:90]))
            break
    prompts[(c["subject"], re.sub(r"\s+", " ", c["prompt"].strip().lower()))].append(c["id"])
    # answer-position bias
    issues["_answer_pos"].append(c.get("answer"))
    if len(c["prompt"]) > 220:
        issues["prompt_long_gt220"].append(c["id"])
    if any(len(str(x)) > 60 for x in o):
        issues["option_long_gt60"].append(c["id"])
dups = {k: v for k, v in prompts.items() if len(v) > 1}
out["duplicate_prompt_groups"] = len(dups)
out["duplicate_prompt_cards"] = sum(len(v) for v in dups.values())
out["dup_examples"] = [(k[1][:80], v[:3]) for k, v in list(dups.items())[:6]]
out["answer_position_dist"] = dict(collections.Counter(issues.pop("_answer_pos")))
for k, v in issues.items():
    out[k] = {"count": len(v), "examples": v[:5]}
out["by_subject"] = dict(collections.Counter(c["subject"] for c in cards))
out["review_status"] = dict(collections.Counter(c.get("review_status") for c in cards))

# 2. catalog vs bank
r, ms = t("GET", "/api/rf/catalog")
out["catalog_ms"] = ms
cat = r.json()
out["catalog_totals"] = {s["name"]: s["total"] for s in cat["subjects"]}
out["empty_chapters"] = [(s["name"], c["name"]) for s in cat["subjects"] for c in s["chapters"] if c["count"] == 0]
known = {(s["name"], c["name"]) for s in cat["subjects"] for c in s["chapters"]}
out["cards_with_unlisted_chapter"] = len([c for c in cards if (c["subject"], c["chapter"]) not in known])

# 3. sessions per subject: dupes within session, latency
for subj in ("Physics", "Chemistry", "Mathematics"):
    r, ms = t("POST", "/api/rf/sessions", headers=H, json={"subject": subj, "count": 30, "request_id": "TEST_" + uuid.uuid4().hex[:12]})
    j = r.json()
    ids = [c["id"] for c in j["cards"]]
    ps = [c["prompt"] for c in j["cards"]]
    out[f"session_{subj}"] = {"ms": ms, "n": len(ids), "dup_ids": len(ids) - len(set(ids)), "dup_prompts": len(ps) - len(set(ps)),
                              "answer_exposed": "answer" in j["cards"][0], "chapters": len({c['chapter'] for c in j['cards']})}

# 4. profile/history consistency + latency
r1, ms1 = t("GET", "/api/rf/profile", headers=H)
r2, ms2 = t("GET", "/api/rf/history", headers=H)
r3, ms3 = t("GET", "/api/rf/leaderboard", headers=H)
r4, ms4 = t("GET", "/api/rf/shop", headers=H)
r5, ms5 = t("GET", "/api/rf/duels", headers=H)
p, h, lb = r1.json(), r2.json(), r3.json()
out["lat_ms"] = {"profile": ms1, "history": ms2, "leaderboard": ms3, "shop": ms4, "duels_mine": ms5}
out["profile"] = {k: p[k] for k in ("xp", "level", "coins", "streak", "sessions", "duels", "wins", "cards_correct")}
out["history_totals"] = h["totals"]
out["history_items_returned"] = len(h["items"])
xs = [i["xp"] for i in lb["items"]]
out["leaderboard_sorted"] = xs == sorted(xs, reverse=True)
out["leaderboard_names"] = collections.Counter(i["name"] for i in lb["items"]).most_common(3)
out["leaderboard_len"] = len(xs)

# 5. JEELIVE proxy latency
sid = "TESTaudit" + uuid.uuid4().hex[:16]
for path in ("health", "exams", "catalogue", "me"):
    r, ms = t("GET", "/api/jl/" + path, headers={"X-JL-SID": sid})
    out[f"jl_{path}"] = {"status": r.status_code, "ms": ms}
r, ms = t("POST", "/api/jl/auth/phone", headers={"X-JL-SID": sid}, json={"phone": "9000000001"})
out["jl_auth_phone"] = {"status": r.status_code, "ms": ms, "body": r.text[:160]}
print(json.dumps(out, indent=1, default=str))
