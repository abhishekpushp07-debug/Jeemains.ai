# Iteration 29: Rapid Fire pool audit caps (90 / inorganic 120), NEET exam map + Biology subject, retired cards never served, Biology duels.
import os, uuid, json, pathlib, requests, pytest
from pymongo import MongoClient

API = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"
INORGANIC = {"Periodic Properties", "p-Block", "d & f Block", "Coordination Compounds"}
CARDS_DIR = pathlib.Path(__file__).resolve().parents[1] / "rapidfire" / "cards"


def H(u=UID):
    return {"X-RF-User": u, "Content-Type": "application/json"}


def rid():
    return "TEST_" + uuid.uuid4().hex[:12]


@pytest.fixture(scope="module")
def cat():
    r = requests.get(f"{API}/catalog", timeout=30)
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="module")
def retired_ids():
    return {d["id"] for d in DB.rf_cards.find({"retired": True}, {"id": 1})}


# Catalog: subjects, exam map, Biology 32 chapters
class TestCatalog:
    def test_subjects_and_exams(self, cat):
        assert [s["name"] for s in cat["subjects"]] == ["Physics", "Chemistry", "Mathematics", "Biology"]
        assert cat["exams"] == {"JEE": ["Physics", "Chemistry", "Mathematics"], "NEET": ["Physics", "Chemistry", "Biology"]}

    def test_biology_32_chapters_with_cards(self, cat):
        bio = next(s for s in cat["subjects"] if s["name"] == "Biology")
        assert len(bio["chapters"]) == 32
        assert all(c["count"] > 0 for c in bio["chapters"]), [c for c in bio["chapters"] if not c["count"]]
        assert bio["total"] == sum(c["count"] for c in bio["chapters"])

    def test_chapter_caps(self, cat):
        over = [(s["name"], c["name"], c["count"]) for s in cat["subjects"] for c in s["chapters"]
                if c["count"] > (120 if c["name"] in INORGANIC else 90)]
        assert not over, over

    def test_totals_match_db(self, cat):
        for s in cat["subjects"]:
            n = DB.rf_cards.count_documents({"subject": s["name"], "retired": {"$ne": True}})
            assert s["total"] == n, (s["name"], s["total"], n)

    # card JSON files on disk agree with the active pool (sync)
    def test_files_match_active_pool(self, cat):
        counts = {(c["subject"], c["chapter"]) for f in CARDS_DIR.glob("*.json") for c in json.loads(f.read_text())}
        file_n = sum(len(json.loads(f.read_text())) for f in CARDS_DIR.glob("*.json"))
        assert file_n == sum(s["total"] for s in cat["subjects"]), (file_n,)
        assert counts


# Sessions: Biology 30 cards, never retired
class TestSessions:
    def test_biology_mixed_session(self, retired_ids):
        r = requests.post(f"{API}/sessions", headers=H(), json={"subject": "Biology", "request_id": rid()}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d["cards"]) == 30 and d["seconds_per_card"] == 20
        assert all(c["subject"] == "Biology" for c in d["cards"])
        assert not {c["id"] for c in d["cards"]} & retired_ids
        assert all(len(c["options"]) == 4 and 0 <= c["answer"] <= 3 for c in d["cards"])

    def test_biology_chapter_session(self, cat):
        ch = next(s for s in cat["subjects"] if s["name"] == "Biology")["chapters"][0]["name"]
        r = requests.post(f"{API}/sessions", headers=H(), json={"subject": "Biology", "chapter": ch, "request_id": rid()}, timeout=30)
        assert r.status_code == 200
        assert {c["chapter"] for c in r.json()["cards"]} == {ch}

    def test_many_sessions_never_retired(self, retired_ids):
        for sub in ["Physics", "Chemistry", "Mathematics", "Biology"] * 3:
            r = requests.post(f"{API}/sessions", headers=H(), json={"subject": sub, "request_id": rid()}, timeout=30)
            assert r.status_code == 200
            ids = {c["id"] for c in r.json()["cards"]}
            assert not ids & retired_ids, sub

    def test_repeat_missed_with_retired_ids(self, retired_ids):
        doc = DB.rf_cards.find_one({"retired": True, "subject": "Physics"})
        if not doc:
            pytest.skip("no retired physics card")
        r = requests.post(f"{API}/sessions", headers=H(), json={"subject": "Physics", "card_ids": [doc["id"]], "request_id": rid()}, timeout=30)
        assert r.status_code == 404

    def test_complete_biology_session(self):
        d = requests.post(f"{API}/sessions", headers=H(), json={"subject": "Biology", "count": 5, "request_id": rid()}, timeout=30).json()
        res = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 3000} for c in d["cards"]]
        r = requests.post(f"{API}/sessions/{d['id']}/complete", headers=H(), json={"results": res}, timeout=30)
        assert r.status_code == 200, r.text
        g = requests.get(f"{API}/sessions/{d['id']}", headers=H(), timeout=30).json()
        assert g["status"] == "completed" and g["subject"] == "Biology"

    def test_invalid_subject_422(self):
        r = requests.post(f"{API}/sessions", headers=H(), json={"subject": "Zoology", "request_id": rid()}, timeout=30)
        assert r.status_code == 422


# Duels with Biology: random -> AI fallback, invite
class TestBiologyDuel:
    def test_random_then_bot(self, retired_ids):
        u = "TEST-" + uuid.uuid4().hex[:16]
        r = requests.post(f"{API}/duels", headers=H(u), json={"subject": "Biology", "mode": "random", "name": "TEST", "request_id": rid()}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["subject"] == "Biology"
        b = requests.post(f"{API}/duels/{d['id']}/bot", headers=H(u), timeout=30)
        assert b.status_code == 200, b.text
        g = requests.get(f"{API}/duels/{d['id']}", headers=H(u), timeout=30).json()
        assert g["status"] in ("ready", "live", "countdown") or g.get("vs_bot"), g["status"]
        raw = DB.rf_duels.find_one({"id": d["id"]})
        assert len(raw["card_ids"]) == 30 and not set(raw["card_ids"]) & retired_ids
        subs = {c["subject"] for c in DB.rf_cards.find({"id": {"$in": raw["card_ids"]}}, {"subject": 1})}
        assert subs == {"Biology"}

    def test_invite_and_cancel(self):
        u = "TEST-" + uuid.uuid4().hex[:16]
        d = requests.post(f"{API}/duels", headers=H(u), json={"subject": "Biology", "mode": "invite", "name": "TEST", "request_id": rid()}, timeout=30).json()
        assert d["code"] and d["subject"] == "Biology"
        assert requests.post(f"{API}/duels/{d['id']}/cancel", headers=H(u), timeout=30).json()["ok"]
        assert DB.rf_duels.find_one({"id": d["id"]})["status"] == "cancelled"
