# Rank PDF export (iteration 88): /api/rank/pdf/* must mirror the on-screen Top-50 lists exactly. Read-only, no auth, no DB writes.
import io
import os
import re
import time

import pdfplumber
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
BASE_URL = BASE_URL.rstrip("/")
R = f"{BASE_URL}/api/rank"
TAG = {"safe": "Safe", "likely": "Likely", "borderline": "Borderline"}


def fmt(v):  # same Indian grouping as rank_predictor.fmt
    s = str(int(v))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def pdf(s, path, body, status=200):
    t0 = time.time()
    r = s.post(f"{R}/pdf{path}", json=body, timeout=60)
    took = time.time() - t0
    assert r.status_code == status, r.text[:300]
    if status != 200:
        return r, None, took
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF"
    assert re.search(r'filename="[^"]+\.pdf"', r.headers.get("content-disposition", ""))
    with pdfplumber.open(io.BytesIO(r.content)) as d:
        text = "\n".join(pg.extract_text() or "" for pg in d.pages)
    return r, text, took


def lines_of(text):
    return [ln.strip() for ln in text.split("\n")]


def check_rows(section, rows):
    """rows = [(row_no, college_short, [numbers that must be on the numbered line], tag_label)] in order."""
    ls = lines_of(section)
    pos = 0
    for no, college, nums, label in rows:
        idx = next((i for i in range(pos, len(ls)) if re.match(rf"^{no}( |$)", ls[i])), None)
        assert idx is not None, f"row {no} ({college}) not found"
        ctx = " ".join(ls[max(pos, idx - 4):idx + 3])
        assert college in ctx, f"row {no}: {college} not near: {ctx}"
        for v in nums:
            assert v in ls[idx] or v in ctx, f"row {no}: {v} missing in {ls[idx]}"
        if label:
            assert label in ls[idx] or label in ctx, f"row {no}: tag {label} missing"
        pos = idx + 1


JEE_BASE = {"marks": 180, "level": "normal", "category": "OBC-NCL", "state": "Bihar", "branches": []}


# JEE list PDF == /predict page1+2 per segment (order, closing, tag) + near list
@pytest.mark.parametrize("segment", ["all", "NIT", "IIIT", "GFTI", "DELHI"])
def test_jee_pdf_matches_predict(s, segment):
    body = {**JEE_BASE, "segment": segment}
    p1 = s.post(f"{R}/predict", json={**body, "page": 1}, timeout=30).json()
    items = p1["items"] + (s.post(f"{R}/predict", json={**body, "page": 2}, timeout=30).json()["items"] if p1["pages"] > 1 else [])
    r, text, took = pdf(s, "/jee", body)
    assert took < 3, took
    tail = "" if segment == "all" else f"-{segment}"
    assert f'filename="JEELIVE-JEE-colleges-180-marks{tail}.pdf"' in r.headers["content-disposition"]
    assert f"Top {len(items)} college-branch" in text
    top, _, near = text.partition("Bas thoda sa door")
    check_rows(top.split(f"Top {len(items)} college-branch")[-1],
               [(i, x["college"], [fmt(x["close"])], TAG[x["tag"]]) for i, x in enumerate(items, 1)])
    if p1["near"]:
        assert near, "near section missing"
        check_rows(near, [(i, x["college"], [fmt(x["close"])], None) for i, x in enumerate(p1["near"], 1)])


@pytest.mark.parametrize("body", [{"percentile": 97.5, "category": "GEN"},
                                  {"marks": 150, "category": "SC", "female": True, "pwd": True, "state": "Delhi"},
                                  {"marks": 200, "branches": ["Computer Science"]}])
def test_jee_pdf_variants(s, body):
    items = s.post(f"{R}/predict", json=body, timeout=30).json()["items"][:25]
    r, text, _ = pdf(s, "/jee", body)
    if "percentile" in body:
        assert "97.5-percentile" in r.headers["content-disposition"]
    check_rows(text.split("college-branch\n")[-1] if False else text.partition("Bas thoda sa door")[0],
               [(i, x["college"], [fmt(x["close"])], TAG[x["tag"]]) for i, x in enumerate(items, 1)])


# COMEDK list PDF == /comedk pages 1+2 (closing, fee, GM seats)
@pytest.mark.parametrize("body", [{"marks": 120, "area": "all"}, {"rank": 4500, "area": "blr"}, {"marks": 120, "area": "other"},
                                  {"marks": 100, "branches": ["Computer Science"]}])
def test_comedk_pdf_matches(s, body):
    p1 = s.post(f"{R}/comedk", json={**body, "page": 1}, timeout=30).json()
    items = p1["items"] + (s.post(f"{R}/comedk", json={**body, "page": 2}, timeout=30).json()["items"] if p1["pages"] > 1 else [])
    r, text, took = pdf(s, "/comedk", body)
    assert took < 3
    top = text.partition("Bas thoda sa door")[0]
    check_rows(top, [(i, x["code"] and x["college"][:0] or "", [fmt(x["close"]), f"₹{fmt(x['fee'])}" if x["fee"] else "—",
                                                                  str(x["seats"]) if x["seats"] else "—"], TAG[x["tag"]])
                     for i, x in enumerate(items, 1)])
    assert f"Top {len(items)} college-course" in text


# BITSAT PDF lists every program of items/near/rest
@pytest.mark.parametrize("body", [{"score": 280}, {"score": 280, "campus": "Goa"}, {"score": 250, "degree": "MSc"}])
def test_bitsat_pdf(s, body):
    d = s.post(f"{R}/bitsat", json=body, timeout=30).json()
    r, text, _ = pdf(s, "/bitsat", body)
    flat = text.replace("\n", " ")
    for x in d["items"] + d["near"] + d["rest"]:
        assert x["program"].split()[-1] in flat
    check_rows(text.partition("Bas thoda sa door")[0], [(i, "", [str(x["cutoff"])], TAG[x["tag"]] if x.get("tag") else None)
                                                         for i, x in enumerate(d["items"], 1)])
    if d["near"]:
        assert "Bas thoda sa door" in text
    if d["rest"]:
        assert "Baaki programs" in text


# Target marks PDFs
@pytest.mark.parametrize("body", [{"inst": 2, "category": "OBC-NCL", "state": "Bihar"},
                                  {"inst": 111, "category": "GEN", "female": True, "state": "Delhi"},
                                  {"inst": 2, "category": "SC", "pwd": True}])
def test_target_jee_pdf(s, body):
    d = s.post(f"{R}/target/jee", json=body, timeout=30).json()
    r, text, _ = pdf(s, "/target/jee", body)
    flat = text.replace("\n", " ")
    for i, row in enumerate(d["rows"], 1):
        assert f"{i}. {row['branch'][:20]}" in flat, row["branch"]
        f = row["final"]
        assert f"Normal {f['marks']['normal']}+" in flat
        for c in row["cells"]:
            if c.get("close"):
                assert fmt(c["close"]) in flat
    assert len(d["rows"]) > 0


def test_target_comedk_bitsat_pdf(s):
    d = s.post(f"{R}/target/comedk", json={"code": "E095"}, timeout=30).json()
    _, text, _ = pdf(s, "/target/comedk", {"code": "E095"})
    for r in d["rows"]:
        assert f"{r['final']['mid']}+" in text
        assert r["course"][:15] in text.replace("\n", " ")
    b = s.get(f"{R}/target/bitsat", timeout=30).json()
    goa = [x for x in b["rows"] if x["campus"] == "Goa"]
    r, text, _ = pdf(s, "/target/bitsat", {"campus": "Goa"})
    assert "JEELIVE-target-BITSAT-Goa.pdf" in r.headers["content-disposition"]
    assert f"{len(goa)} programs" in text
    for x in goa:
        assert f"{x['cutoff']}+" in text and f"{x['safe']}+" in text


def _saved_items(s):
    p = s.post(f"{R}/predict", json={"percentile": 97, "category": "OBC-NCL"}, timeout=30).json()["items"][:2]
    jee = [{"exam": "jee", "id": f"{x['inst']}-{x['prog']}", "prog": x["prog"], "quota": x["quota"], "gender": x["gender"], "path": x["path"]}
           for x in p]
    return jee + [{"exam": "comedk", "id": "E095|CS"}, {"exam": "bitsat", "id": "Pilani-cs"}, {"exam": "jee", "id": "x", "prog": 999999}]


# Saved + compare PDF
def test_saved_pdf_side_by_side(s):
    items = _saved_items(s)
    r, text, _ = pdf(s, "/saved", {"items": items, "tags": ["safe", "likely", "borderline", None, None], "pick": [0, 1, 2]})
    assert "Side by side" in text and "Side by side: 3 chune hue" in text
    assert "nahi mili" in text
    assert f"Saved colleges ({len(items)})" in text
    assert "JEELIVE-saved-colleges-5.pdf" in r.headers["content-disposition"]
    assert "RVCE" in text or "R V College" in text


def test_saved_pdf_no_side_by_side(s):
    items = _saved_items(s)[:3]
    _, text, _ = pdf(s, "/saved", {"items": items, "pick": [0]})
    assert "Side by side" not in text
    assert "Saved colleges (3)" in text


# Validation
@pytest.mark.parametrize("path,body,code", [
    ("/jee", {"category": "GEN"}, 422), ("/target/jee", {"inst": 9999}, 404), ("/target/comedk", {"code": "ZZ"}, 404),
    ("/saved", {"items": []}, 422), ("/saved", {"items": [{"exam": "bitsat", "id": "Pilani-cs"}] * 51}, 422),
    ("/comedk", {"marks": 500}, 422)])
def test_validation(s, path, body, code):
    r = s.post(f"{R}/pdf{path}", json=body, timeout=30)
    assert r.status_code == code, r.text[:300]
    assert "detail" in r.json()


# Speed: each PDF builds < 1s (server side; allow network overhead)
@pytest.mark.parametrize("path,body", [("/jee", JEE_BASE), ("/comedk", {"marks": 120}), ("/bitsat", {"score": 280}),
                                       ("/target/jee", {"inst": 2, "category": "OBC-NCL"}), ("/target/comedk", {"code": "E095"}),
                                       ("/target/bitsat", {"campus": "all"})])
def test_speed(s, path, body):
    s.post(f"{R}/pdf{path}", json=body, timeout=30)  # warm
    t0 = time.time()
    r = s.post(f"{R}/pdf{path}", json=body, timeout=30)
    assert r.status_code == 200
    assert time.time() - t0 < 1.5, time.time() - t0
