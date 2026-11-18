"""College vs college compare (/api/rank/compare/colleges), BITS campuses in /colleges, quota+gender on JEE target rows."""
import requests

B = "http://localhost:8001/api/rank"


def test_three_exams_side_by_side():
    r = requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "jee", "id": "0"}, {"exam": "comedk", "id": "E095"}, {"exam": "bitsat", "id": "Pilani"}],
                                                      "category": "GEN", "state": "Bihar"}, timeout=20)
    assert r.status_code == 200
    jee, ck, bits = r.json()["items"]
    assert jee["title"] == "NIT Jalandhar" and jee["branches"] > 5 and jee["seats"] > 0 and jee["fee"] is None
    assert jee["easiest"]["marks"] <= jee["cs"]["marks"] <= jee["toughest"]["marks"]
    assert ck["kind"] == "COMEDK" and ck["fee"][0] > 0 and ck["seats_label"] == "GM seats"
    assert bits["title"] == "BITS Pilani" and bits["cs"]["branch"].startswith("B.E. Computer") and bits["seats"] is None


def test_profile_changes_jee_marks():
    body = {"items": [{"exam": "jee", "id": "0"}]}
    gen = requests.post(f"{B}/compare/colleges", json={**body, "category": "GEN"}, timeout=20).json()["items"][0]
    sc = requests.post(f"{B}/compare/colleges", json={**body, "category": "SC"}, timeout=20).json()["items"][0]
    assert sc["easiest"]["marks"] < gen["easiest"]["marks"]


def test_missing_and_invalid():
    got = requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "jee", "id": "99999"}, {"exam": "comedk", "id": "NOPE"}, {"exam": "bitsat", "id": "Mars"}]}, timeout=20)
    assert got.status_code == 200 and all(i["missing"] for i in got.json()["items"])
    assert requests.post(f"{B}/compare/colleges", json={"items": []}, timeout=20).status_code == 422
    assert requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "jee", "id": "0"}] * 4}, timeout=20).status_code == 422
    assert requests.post(f"{B}/compare/colleges", json={"items": [{"exam": "jee", "id": "0"}], "state": "Atlantis"}, timeout=20).status_code == 422


def test_colleges_list_has_bits_and_target_rows_have_quota():
    c = requests.get(f"{B}/colleges", timeout=20).json()
    assert [b["campus"] for b in c["bitsat"]] == ["Pilani", "Goa", "Hyderabad"] and all(b["programs"] > 0 for b in c["bitsat"])
    rows = requests.post(f"{B}/target/jee", json={"inst": 0, "state": "Punjab"}, timeout=20).json()["rows"]
    assert all(r["quota"] and r["gender"] in ("N", "F") for r in rows)
    # a branch added from the college list is found again by the branch compare
    r = rows[0]
    got = requests.post(f"{B}/compare", json={"items": [{"exam": "jee", "id": f"jee-{r['prog']}", "prog": r["prog"], "quota": r["quota"], "gender": r["gender"], "path": r["path"]}]}, timeout=20).json()
    assert not got["items"][0].get("missing") and got["items"][0]["final"]["close"] == r["final"]["close"]
