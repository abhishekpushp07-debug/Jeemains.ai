# Rank tools (iteration 86): /api/rank/percentile, /target/jee, /target/comedk, /target/bitsat, /colleges, /compare
# Read-only, no auth, no DB writes.
import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
BASE_URL = BASE_URL.rstrip("/")
R = f"{BASE_URL}/api/rank"
CATS = ["GEN", "EWS", "OBC-NCL", "SC", "ST"]


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


@pytest.fixture(scope="module")
def cols(s):
    r = s.get(f"{R}/colleges", timeout=30)
    assert r.status_code == 200
    return r.json()


# --- percentile -> rank ---
@pytest.mark.parametrize("cat", CATS)
def test_percentile_shape(s, cat):
    for pwd in (False, True):
        r = s.post(f"{R}/percentile", json={"percentile": 97.3, "category": cat, "pwd": pwd}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        res = d["result"]
        lo, hi = res["crl"]
        assert 0 < lo <= hi
        assert [m["level"] for m in d["marks"]] == ["tough", "normal", "easy"]
        mk = [m["marks"] for m in d["marks"]]
        assert mk[0] <= mk[1] <= mk[2], mk
        if cat != "GEN":
            assert "cat_rank" in res, res.keys()
        if pwd:
            assert "pwd_rank" in res, res.keys()


def test_percentile_monotonic(s):
    prev = None
    for p in (80, 90, 95, 98, 99, 99.5, 99.9, 100):
        d = s.post(f"{R}/percentile", json={"percentile": p}, timeout=30).json()
        lo = d["result"]["crl"][0]
        if prev is not None:
            assert lo <= prev, (p, lo, prev)
        prev = lo
    assert prev >= 1


@pytest.mark.parametrize("bad", [101, -1, "abc", None])
def test_percentile_invalid(s, bad):
    r = s.post(f"{R}/percentile", json={"percentile": bad}, timeout=30)
    assert r.status_code == 422


def test_percentile_bad_category(s):
    assert s.post(f"{R}/percentile", json={"percentile": 90, "category": "XYZ"}, timeout=30).status_code == 422


# --- colleges list ---
def test_colleges_counts(cols):
    assert len(cols["jee"]) == 115
    assert len(cols["comedk"]) == 148
    assert any("Bhopal" in (c["name"] + c["city"]) for c in cols["jee"])
    assert any(c["code"] == "E095" for c in cols["comedk"])


# --- target JEE ---
def _check_jee(d):
    assert d["exam"] == "jee" and d["rows"]
    n = len(d["rounds"])
    for row in d["rows"]:
        assert len(row["cells"]) == n
        f = row["final"]
        m = f["marks"]
        assert m["tough"] <= m["normal"] <= m["easy"], (row["branch"], m)
        assert 0 <= f["pct"] <= 100
        assert row["rank_type"]
        assert row["path"]
        for c in row["cells"]:
            if c.get("close"):
                assert c["marks"]["tough"] <= c["marks"]["normal"] <= c["marks"]["easy"]


def test_target_jee_manit(s, cols):
    inst = next(c["inst"] for c in cols["jee"] if "Bhopal" in c["name"] and c["type"] == "NIT")
    r = s.post(f"{R}/target/jee", json={"inst": inst, "category": "GEN"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "Bhopal" in d["college"]["name"] or d["college"]["city"] == "Bhopal"
    _check_jee(d)
    # better (smaller) closing CRL => higher (or equal) marks
    rows = sorted(d["rows"], key=lambda x: x["final"]["crl"])
    for a, b in zip(rows, rows[1:]):
        assert a["final"]["marks"]["normal"] >= b["final"]["marks"]["normal"], (a["branch"], b["branch"])


@pytest.mark.parametrize("cat,female,pwd", [("OBC-NCL", True, False), ("SC", False, True), ("EWS", True, True), ("ST", False, False)])
def test_target_jee_variants(s, cols, cat, female, pwd):
    inst = cols["jee"][0]["inst"]
    r = s.post(f"{R}/target/jee", json={"inst": inst, "category": cat, "female": female, "pwd": pwd, "state": "Madhya Pradesh"}, timeout=30)
    assert r.status_code == 200, r.text
    _check_jee(r.json())


def test_target_jee_404(s):
    r = s.post(f"{R}/target/jee", json={"inst": 9999}, timeout=30)
    assert r.status_code == 404


def test_target_jee_bad_state(s):
    assert s.post(f"{R}/target/jee", json={"inst": 0, "state": "Atlantis"}, timeout=30).status_code == 422


def test_target_jee_negative(s):
    assert s.post(f"{R}/target/jee", json={"inst": -1}, timeout=30).status_code == 422


# --- target COMEDK ---
def test_target_comedk(s):
    r = s.post(f"{R}/target/comedk", json={"code": "E095"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["exam"] == "comedk" and d["rows"]
    for row in d["rows"]:
        lo, hi = row["final"]["marks"]
        assert lo <= row["final"]["mid"] <= hi, row
        assert 0 <= lo <= hi <= 180
        assert row["fee"] is None or row["fee"] > 0
        assert "seats" in row
        assert len(row["cells"]) == len(d["rounds"])


def test_target_comedk_404(s):
    assert s.post(f"{R}/target/comedk", json={"code": "ZZZZ"}, timeout=30).status_code == 404


# --- target BITSAT ---
def test_target_bitsat(s):
    r = s.get(f"{R}/target/bitsat", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert len(d["rows"]) == 50
    for row in d["rows"]:
        assert row["safe"] == min(d["max"], row["cutoff"] + 10)
        assert row["safe"] <= 390


# --- compare ---
def test_compare_mixed(s):
    p = s.post(f"{R}/predict", json={"percentile": 98, "category": "OBC-NCL", "female": True}, timeout=30).json()
    it = p["items"][0]
    jee = {"exam": "jee", "id": f"{it['inst']}-{it['prog']}", "prog": it["prog"], "quota": it["quota"], "gender": it["gender"], "path": it["path"]}
    bits = s.get(f"{R}/target/bitsat", timeout=30).json()["rows"][0]["id"]
    r = s.post(f"{R}/compare", json={"items": [jee, {"exam": "comedk", "id": "E095|CS"}, {"exam": "bitsat", "id": bits}]}, timeout=30)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 3
    assert all(not x.get("missing") for x in items), items
    # compare "final" = JoSAA final (y26); the predictor's best close (may be a CSAB round) must appear in rounds
    assert items[0]["final"]["close"] == it["y26"], (items[0]["final"], it)
    assert it["close"] in [r["close"] for r in items[0]["rounds"]]
    assert items[1]["fee"] and items[1]["seats"]
    assert items[2]["higher_is_harder"] is True


def test_compare_all_predict_items_resolve(s):
    for body in ({"percentile": 95}, {"percentile": 99, "category": "SC", "pwd": True}, {"percentile": 90, "female": True, "state": "Bihar"}):
        p = s.post(f"{R}/predict", json=body, timeout=30).json()
        for i in range(0, len(p["items"]), 3):
            chunk = p["items"][i:i + 3]
            q = [{"exam": "jee", "id": str(x["prog"]), "prog": x["prog"], "quota": x["quota"], "gender": x["gender"], "path": x["path"]} for x in chunk]
            d = s.post(f"{R}/compare", json={"items": q}, timeout=30).json()
            for x, y in zip(chunk, d["items"]):
                assert not y.get("missing"), (body, x)
                assert y["final"]["close"] == x["y26"], (body, x, y["final"])
                assert x["close"] in [r["close"] for r in y["rounds"]], (body, x, y["rounds"])


def test_compare_missing_and_limits(s):
    d = s.post(f"{R}/compare", json={"items": [{"exam": "comedk", "id": "E095|ZZ"}, {"exam": "bitsat", "id": "nope"}, {"exam": "jee", "id": "x"}]}, timeout=30).json()
    assert all(x["missing"] for x in d["items"])
    four = [{"exam": "comedk", "id": "E095|CS"}] * 4
    assert s.post(f"{R}/compare", json={"items": four}, timeout=30).status_code == 422
    assert s.post(f"{R}/compare", json={"items": []}, timeout=30).status_code == 422
    assert s.post(f"{R}/compare", json={"items": [{"exam": "neet", "id": "a"}]}, timeout=30).status_code == 422


def test_compare_jee_bad_prog(s):
    r = s.post(f"{R}/compare", json={"items": [{"exam": "jee", "id": "x", "prog": 999999, "path": "Other state · Open"}]}, timeout=30)
    assert r.status_code == 200 and r.json()["items"][0]["missing"]
    r = s.post(f"{R}/compare", json={"items": [{"exam": "jee", "id": "x", "prog": -1, "path": "Other state · Open"}]}, timeout=30)
    assert r.status_code in (200, 422), r.status_code
