# Rank tools retest (iteration 87): compare rounds[].crl flag, DTU (JAC) target rounds, colleges full-name, BITSAT history nulls.
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


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def _jee_items(s, body):
    p = s.post(f"{R}/predict", json=body, timeout=30).json()
    return [{"exam": "jee", "id": f"{x['inst']}-{x['prog']}", "prog": x["prog"], "quota": x["quota"], "gender": x["gender"], "path": x["path"]}
            for x in p["items"]]


# Compare: crl true only on CSAB rounds of non-CRL JoSAA seats
@pytest.mark.parametrize("body", [{"percentile": 97, "category": "OBC-NCL"}, {"percentile": 99, "category": "SC", "pwd": True},
                                  {"percentile": 96}, {"percentile": 95, "pwd": True}])
def test_compare_crl_flag(s, body):
    items = _jee_items(s, body)
    assert items
    seen_csab_flag = False
    for i in range(0, min(len(items), 30), 3):
        d = s.post(f"{R}/compare", json={"items": items[i:i + 3]}, timeout=30)
        assert d.status_code == 200, d.text
        for col in d.json()["items"]:
            assert not col.get("missing"), col
            jac = col["rounds"][0]["label"] == "R1" and any(r["label"] == "Spot" for r in col["rounds"])
            for r in col["rounds"]:
                want = r["label"].startswith("CSAB") and col["rank_label"] != "CRL" and not jac
                assert r["crl"] == want, (col["title"], col["rank_label"], r)
                seen_csab_flag |= r["crl"]
    if body.get("category") or body.get("pwd"):
        assert seen_csab_flag, "expected at least one CSAB CRL flag for category/PwD seats"


def test_compare_comedk_bitsat_no_crl_true(s):
    bits = s.get(f"{R}/target/bitsat", timeout=30).json()["rows"][0]["id"]
    d = s.post(f"{R}/compare", json={"items": [{"exam": "comedk", "id": "E095|CS"}, {"exam": "bitsat", "id": bits}]}, timeout=30).json()
    for col in d["items"]:
        assert not any(r.get("crl") for r in col["rounds"])


# DTU (JAC) target: Upgrade/Spot rounds present, no CSAB rounds; MANIT has CSAB rounds
def test_target_dtu_rounds(s):
    d = s.post(f"{R}/target/jee", json={"inst": 111, "category": "GEN", "female": False, "pwd": False, "state": None}, timeout=30).json()
    assert d["college"]["name"] == "Delhi Technological University"
    assert d["rounds"] == ["R1", "R2", "R3", "R4", "Upgrade", "Spot"]
    assert d["rows"]
    # JAC never published Upgrade / Spot closing ranks
    for row in d["rows"]:
        assert all(c["close"] is None for c in row["cells"] if c["label"] in ("Upgrade", "Spot")), row["cells"]


def test_target_manit_has_csab(s):
    d = s.post(f"{R}/target/jee", json={"inst": 2, "category": "GEN", "female": False, "pwd": False, "state": None}, timeout=30).json()
    assert any(r.startswith("CSAB") for r in d["rounds"])
    assert "Bhopal" in d["college"]["name"] or "Bhopal" in d["college"]["city"]


# College list carries the full name, so "delhi technological" can match DTU on the client
def test_colleges_full_name(s):
    j = s.get(f"{R}/colleges", timeout=30).json()["jee"]
    dtu = next(c for c in j if c["inst"] == 111)
    assert "delhi technological" in dtu["name"].lower()
    manit = next(c for c in j if c["inst"] == 2)
    assert "bhopal" in f"{manit['name']} {manit['city']}".lower()


# BITSAT history may contain null (rendered as '—' in UI)
def test_bitsat_history_shape(s):
    d = s.get(f"{R}/target/bitsat", timeout=30).json()
    assert len(d["rows"]) == 50
    assert all(v is None or isinstance(v, int) for row in d["rows"] for v in row["history"])


# Percentile: typed value accepted with 4 decimals
def test_percentile_4dp(s):
    r = s.post(f"{R}/percentile", json={"percentile": 97.4567, "category": "GEN", "pwd": False}, timeout=30)
    assert r.status_code == 200
    lo, hi = r.json()["result"]["crl"]
    assert 0 < lo <= hi
