# Repro (iteration 21): random duel vs seated arena opponent - does a "win" pay the PvP win coins/wins counter?
import os, time, uuid, requests
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv("/app/frontend/.env"); load_dotenv("/app/backend/.env")
API = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
u = "TEST-" + uuid.uuid4().hex[:16]; H = {"X-RF-User": u}
try:
    d = requests.post(f"{API}/duels", headers=H, json={"subject": "Physics", "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
    if d["status"] == "waiting":
        d = requests.post(f"{API}/duels/{d['id']}/bot", headers=H, json={}).json()
    time.sleep(max(0, d["start_at"] - d["server_now"]) + 0.3)
    raw = DB.rf_duels.find_one({"id": d["id"]})
    cards = {c["id"]: c for c in DB.rf_cards.find({"id": {"$in": raw["card_ids"]}})} if "rf_cards" in DB.list_collection_names() else {}
    prof0 = requests.get(f"{API}/profile", headers=H).json()
    for i in range(30):
        ans = cards.get(raw["card_ids"][i], {}).get("answer", 0)
        r = requests.post(f"{API}/duels/{d['id']}/answer", headers=H, json={"index": i, "choice": ans, "outcome": "answer"})
        if r.status_code != 200:
            print("answer", i, r.status_code, r.text[:120]); break
    time.sleep(1)
    g = requests.get(f"{API}/duels/{d['id']}", headers=H).json()
    me = [p for p in g["players"] if p["you"]][0]; opp = [p for p in g["players"] if not p["you"]][0]
    print("status", g["status"], "me", me["score"], "opp", opp["score"], opp["answered"], "winner==me", g["winner"] == g.get("you"), "tie_break", g.get("tie_break"))
    print("reward", {k: g["reward"].get(k) for k in ("xp", "coins")} if g.get("reward") else None)
    prof1 = requests.get(f"{API}/profile", headers=H).json()
    print("wins before/after", prof0.get("wins"), prof1.get("wins"), "duels", prof0.get("duels"), prof1.get("duels"))
    lst = requests.get(f"{API}/duels", headers=H).json()["items"]
    print("history won flag", lst[0].get("won"))
finally:
    DB.rf_duels.delete_many({"players.uid": u})
    for c in ("rf_profiles", "rf_sessions", "rf_rewards", "rf_game"):
        DB[c].delete_many({"$or": [{"uid": u}, {"user_id": u}]})
