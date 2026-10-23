# Rapid Fire iteration 7: 3D avatar shop (16 avatars, 4 free), 10 entry effects, legacy avatar mapping, duel start_at = now+4s
import os
import uuid
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
FREE = {"av_topper", "av_scholar", "av_robo", "av_panda"}
ENTRIES = {"entry_rocket", "entry_lightning", "entry_supercar", "entry_crown", "entry_tornado", "entry_meteor", "entry_dragon", "entry_phoenix", "entry_galaxy", "entry_blackhole"}


def H(u):
    return {"X-RF-User": u}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    yield u
    DB.rf_profiles.delete_many({"uid": u})
    DB.rf_duels.delete_many({"players.uid": u})


def set_coins(u, c, **extra):
    DB.rf_profiles.update_one({"uid": u}, {"$set": {"coins": c, **extra}}, upsert=True)


# ---------- Avatars ----------
class TestAvatarShop:
    def test_shop_avatars_shape(self, s, uid):
        r = s.get(f"{API}/shop", headers=H(uid))
        assert r.status_code == 200, r.text
        av = r.json()["avatars"]
        assert len(av) == 16
        for a in av:
            assert set(a.keys()) == {"id", "title", "rarity", "price"}
            assert a["rarity"] in ("common", "rare", "epic", "legendary")
        free = {a["id"] for a in av if a["price"] == 0}
        assert free == FREE
        paid = [a for a in av if a["price"]]
        assert len(paid) == 12 and all(300 <= a["price"] <= 2000 for a in paid)
        assert r.json()["avatar"] == "av_robo"

    def test_buy_avatar_insufficient_409(self, s, uid):
        set_coins(uid, 100)
        r = s.post(f"{API}/shop/buy", json={"item_id": "av_photon"}, headers=H(uid))
        assert r.status_code == 409 and "coins" in r.json()["detail"]

    def test_set_paid_not_owned_403(self, s, uid):
        r = s.post(f"{API}/profile/avatar", json={"avatar": "av_photon"}, headers=H(uid))
        assert r.status_code == 403

    def test_set_free_ok(self, s, uid):
        r = s.post(f"{API}/profile/avatar", json={"avatar": "av_panda"}, headers=H(uid))
        assert r.status_code == 200
        assert s.get(f"{API}/profile", headers=H(uid)).json()["avatar"] == "av_panda"

    def test_unknown_avatar_400(self, s, uid):
        for bad in ("nope", "ninja", None):
            r = s.post(f"{API}/profile/avatar", json={"avatar": bad}, headers=H(uid))
            assert r.status_code == 400, (bad, r.status_code)

    def test_buy_avatar_then_use(self, s, uid):
        set_coins(uid, 500)
        r = s.post(f"{API}/shop/buy", json={"item_id": "av_photon"}, headers=H(uid))
        assert r.status_code == 200, r.text
        assert r.json()["coins"] == 200 and "av_photon" in r.json()["owned"]
        r = s.post(f"{API}/shop/buy", json={"item_id": "av_photon"}, headers=H(uid))
        assert r.status_code == 409 and "own" in r.json()["detail"]
        assert s.get(f"{API}/shop", headers=H(uid)).json()["coins"] == 200
        r = s.post(f"{API}/profile/avatar", json={"avatar": "av_photon"}, headers=H(uid))
        assert r.status_code == 200
        assert s.get(f"{API}/profile", headers=H(uid)).json()["avatar"] == "av_photon"

    def test_free_avatar_not_buyable(self, s, uid):
        r = s.post(f"{API}/shop/buy", json={"item_id": "av_robo"}, headers=H(uid))
        assert r.status_code == 404

    def test_legacy_avatar_mapped(self, s, uid):
        for legacy in ("ninja", "robot-happy"):
            DB.rf_profiles.update_one({"uid": uid}, {"$set": {"avatar": legacy}})
            assert s.get(f"{API}/profile", headers=H(uid)).json()["avatar"] == "av_robo"
            assert s.get(f"{API}/shop", headers=H(uid)).json()["avatar"] == "av_robo"


# ---------- Entry effects ----------
class TestEntryEffects:
    def test_ten_entries_in_shop(self, s, uid):
        items = s.get(f"{API}/shop", headers=H(uid)).json()["items"]
        ent = {i["id"] for i in items if i["slot"] == "entry"}
        assert ent == ENTRIES

    def test_buy_equip_entry(self, s, uid):
        set_coins(uid, 3000)
        assert s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "entry_blackhole"}, headers=H(uid)).status_code == 403
        r = s.post(f"{API}/shop/buy", json={"item_id": "entry_blackhole"}, headers=H(uid))
        assert r.status_code == 200 and r.json()["coins"] == 0
        r = s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "entry_blackhole"}, headers=H(uid))
        assert r.status_code == 200
        assert s.get(f"{API}/shop", headers=H(uid)).json()["equipped"]["entry"] == "entry_blackhole"
        # wrong slot
        assert s.post(f"{API}/shop/equip", json={"slot": "frame", "item_id": "entry_blackhole"}, headers=H(uid)).status_code == 403
        # avatar ids not equippable via slot
        assert s.post(f"{API}/shop/equip", json={"slot": "avatar", "item_id": "av_photon"}, headers=H(uid)).status_code == 400


# ---------- Duel timing + AI rival entry ----------
class TestDuelStart:
    def test_bot_duel_start_at_4s_and_entry(self, s, uid):
        r = s.post(f"{API}/duels", json={"subject": "Physics", "mode": "invite", "name": "TEST_Av", "request_id": uuid.uuid4().hex}, headers=H(uid))
        assert r.status_code == 200, r.text
        did = r.json()["id"]
        r = s.post(f"{API}/duels/{did}/bot", headers=H(uid))
        assert r.status_code == 200, r.text
        d = r.json()
        gap = d["start_at"] - d["server_now"]
        assert 3.0 <= gap <= 4.05, gap
        me = [p for p in d["players"] if p["you"]][0]
        bot = [p for p in d["players"] if p["bot"]][0]
        assert me["avatar"] in ("av_photon", "av_robo") and me["entry"] == "entry_blackhole"
        assert bot["entry"] in ENTRIES
        assert bot["avatar"].startswith("av_")
        s.post(f"{API}/duels/{did}/forfeit", headers=H(uid))

    def test_rival_entry_random(self, s, uid):
        import sys
        sys.path.insert(0, "/app/backend")
        from shop import rival_profile
        seen = {rival_profile()["entry"] for _ in range(300)}
        assert seen <= ENTRIES and len(seen) >= 8
