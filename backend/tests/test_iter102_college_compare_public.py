"""Iter102 public-URL regression: college vs college compare, /colleges bitsat list, JEE target quota+gender rows."""
import os
import requests

BASE = os.environ.get("EXPO_BACKEND_URL", os.environ.get("EXPO_PUBLIC_BACKEND_URL")).rstrip("/")
B = f"{BASE}/api/rank"


# Colleges list for the search sheet (JEE / COMEDK / BITSAT)
def test_colleges_list_has_three_exams():
    d = requests.get(f"{B}/colleges", timeout=20).json()
    assert len(d["jee"]) > 50 and len(d["comedk"]) > 20
    names = [c["campus"] for c in d["bitsat"]]
    assert "Pilani" in names and all(c["programs"] > 0 for c in d["bitsat"])
    assert any("jalandhar" in (c["name"] + c["short"]).lower() for c in d["jee"])


# College compare: 3 exams side by side via public ingress
def test_compare_colleges_public():
    r = requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "jee", "id": "0"}, {"exam": "comedk", "id": "E095"}, {"exam": "bitsat", "id": "Pilani"}],
                                                      "category": "GEN", "state": "Bihar"}, timeout=20)
    assert r.status_code == 200
    items = r.json()["items"]
    assert [i["exam"] for i in items] == ["jee", "comedk", "bitsat"]
    assert all(not i.get("missing") and i["easiest"]["marks"] > 0 for i in items)
    assert "_id" not in r.text


# Profile category changes JEE marks
def test_category_changes_marks_public():
    body = {"items": [{"exam": "jee", "id": "0"}, {"exam": "jee", "id": "1"}]}
    gen = requests.post(f"{B}/compare/colleges", json={**body, "category": "GEN"}, timeout=20).json()["items"]
    obc = requests.post(f"{B}/compare/colleges", json={**body, "category": "OBC-NCL"}, timeout=20).json()["items"]
    assert any(o["easiest"]["marks"] != g["easiest"]["marks"] for o, g in zip(obc, gen))


# Validation errors
def test_compare_validation_public():
    assert requests.post(f"{B}/compare/colleges", json={"items": []}, timeout=20).status_code == 422
    assert requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "neet", "id": "0"}]}, timeout=20).status_code == 422


# JEE target rows carry quota + gender
def test_target_jee_quota_gender():
    r = requests.post(f"{B}/target/jee", json={"inst": 0, "category": "GEN", "state": "Bihar"}, timeout=20)
    if r.status_code == 405:
        r = requests.get(f"{B}/target/jee", params={"inst": 0, "category": "GEN", "state": "Bihar"}, timeout=20)
    assert r.status_code == 200, r.text[:200]
    rows = r.json()["rows"]
    assert rows and all("quota" in x and "gender" in x for x in rows)
    assert all(x["final"]["marks"]["normal"] >= 0 for x in rows)
