"""JEELIVE.AI Rank: COMEDK UGET 2026 marks or rank -> Karnataka college-course, GM (General Merit, All India) seats only.

Data: rank_data/comedk_2026.json (official COMEDK Round 1-4 cut-off PDFs, 2025 final, 2026 seat & fee matrix),
built by tools/rank_data/build_comedk.py. Pure in-memory lookups, so a result comes back in a few milliseconds.
"""
import bisect, json, math, statistics
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

_D = json.load(open(Path(__file__).parent / "rank_data" / "comedk_2026.json", encoding="utf-8"))
ROUNDS, N, CURVES = _D["rounds"], _D["candidates"], _D["marks_rank"]
MAX_MARKS = 180

GROUPS = {
    "Computer Science": "CS CR CN CE CIT CCC FSD SPE CBD CSD CG CB CM QC",
    "AI & Data Science": "AI AD CA CI CD CP DS AIF",
    "Cyber Security & IoT": "CY CX IC CO CSB",
    "Information Science & IT": "IS IFS IST INT ITE IAR IDA",
    "Electronics & Communication": "EC ED EES ELE ET EI MD VL VLS UE",
    "Electrical": "EE EEC ECE",
    "Mechanical & Robotics": "ME AU AVE MT AR RBE RA RI ROB IM IP MR",
    "Aeronautical & Aerospace": "AE AS",
    "Civil & Planning": "CV BP IMP",
    "Chemical & Biotech": "CH BT BM CC TX AG AL",
    "Design": "BD DC DF DI DL DE",
}
GROUP_OF = {cc: g for g, codes in GROUPS.items() for cc in codes.split()}
GROUP_NAMES = list(GROUPS) + ["Other"]
NOTES = ["Sirf GM (General Merit, All India) seats. KKR (Kalyana Karnataka) quota is list mein nahi.",
         "Closing rank = us round mein GM seat par allot hui aakhri rank. Khaali round = us round mein is seat par allotment nahi hua.",
         "Fee = 2026 ki saalana total fee (tuition + other), COMEDK seat matrix se."]
SOURCES = [{"label": f"COMEDK 2026 Round {i} cut-off", "url": _D["sources"][f"r{i}"]} for i in range(1, 5)] + [
    {"label": "COMEDK 2025 cut-off, all rounds", "url": _D["sources"]["y25"]},
    {"label": "COMEDK 2026 seat matrix & fee", "url": _D["sources"]["fee"]},
] + [{"label": c["label"], "url": c["url"]} for c in CURVES]
OFFICIAL = "https://www.comedk.org/"


# ---------- marks -> rank: three public analyses, interpolated in log(rank) ----------
def _curve_rank(points, marks):
    ms = [p[0] for p in reversed(points)]  # ascending marks
    rs = [math.log(p[1]) for p in reversed(points)]
    i = bisect.bisect_left(ms, marks)
    if i <= 0:
        return round(math.exp(rs[0]))
    if i >= len(ms):
        return 1
    m0, m1, r0, r1 = ms[i - 1], ms[i], rs[i - 1], rs[i]
    return max(1, round(math.exp(r0 + (marks - m0) * (r1 - r0) / (m1 - m0))))


def ranks_at(marks):
    return [_curve_rank(c["points"], marks) for c in CURVES]


def mid_rank(marks):
    return round(statistics.median(ranks_at(marks)))


def marks_for(rank):
    """Fewest marks whose middle estimate reaches this rank."""
    return next((m for m in range(MAX_MARKS + 1) if mid_rank(m) <= rank), MAX_MARKS)


# ---------- seats (GM only) ----------
class Seat:
    __slots__ = ("code", "cc", "rounds", "close", "rnd", "demand", "y25", "total", "gm", "fee")

    def __init__(self, code, cc, rounds, y25):
        self.code, self.cc, self.rounds, self.y25 = code, cc, rounds, y25
        self.close, self.rnd = max((c, i) for i, c in enumerate(rounds) if c)
        self.demand = min(c for c in rounds if c)
        seats = _D["seats"].get(f"{code}|{cc}") or [None, None, None, None]
        self.total, self.gm, self.fee = seats[0], seats[1], seats[3]


SEATS = [Seat(code, cc, rnds, y25) for code, cc, cat, rnds, y25 in _D["rows"] if cat == "GM" and any(rnds)]
SEATS.sort(key=lambda s: (s.demand, s.code, s.cc))
BY_COLLEGE = {}
for _s in SEATS:
    BY_COLLEGE.setdefault(_s.code, []).append(_s)


def college_info(code):
    full, short, city = _D["colleges"][code]
    return {"code": code, "name": full, "short": short, "city": city,
            "blr": "Bengaluru" in full or "Bangalore" in full}


INFO = {code: college_info(code) for code in _D["colleges"]}


def fmt(n):
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail, parts = s[:-3], s[-3:], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + parts + [tail])


class Form(BaseModel):
    marks: Optional[int] = Field(default=None, ge=0, le=MAX_MARKS)
    rank: Optional[int] = Field(default=None, ge=1, le=200000)
    branches: List[str] = []

    @field_validator("branches")
    @classmethod
    def known_groups(cls, v):
        return sorted({g for g in v if g in GROUP_NAMES})


class ComedkIn(Form):
    area: Literal["all", "blr", "other"] = "all"
    page: int = Field(default=1, ge=1, le=2)


class ComedkCollegeIn(Form):
    code: str
    course: Optional[str] = None
    all: bool = False


class Student:
    def __init__(self, f: Form):
        if f.rank is None and f.marks is None:
            raise HTTPException(422, "Marks ya rank mein se koi ek daalo.")
        self.f = f
        self.from_marks = f.rank is None
        if self.from_marks:
            rs = ranks_at(f.marks)
            self.lo, self.hi, self.mid = min(rs), max(rs), round(statistics.median(rs))
            self.shown = [self.lo, self.hi]
        else:
            r = f.rank
            # A rank card rank is exact; the small band only marks seats that close just behind it as Borderline.
            self.lo, self.mid, self.hi = r, r, r + max(50, round(r * 0.05))
            self.shown = [r, r]

    def judge(self, close):
        if close < self.lo:
            return None
        if close >= self.hi and close >= 1.15 * self.mid:
            return "safe"
        return "likely" if close >= self.hi else "borderline"

    def gap(self, close):
        if self.from_marks:
            return f"lagbhag +{max(1, marks_for(close) - self.f.marks)} marks aur"
        return f"rank lagbhag {fmt(self.f.rank - close)} aur upar chahiye"


def group_of(cc):
    return GROUP_OF.get(cc, "Other")


def item(s: Seat, tag=None):
    c = INFO[s.code]
    out = {"id": f"{s.code}|{s.cc}", "code": s.code, "college": c["short"], "city": c["city"], "blr": c["blr"],
           "course": _D["courses"].get(s.cc, s.cc), "cc": s.cc, "group": group_of(s.cc), "close": s.close, "round": ROUNDS[s.rnd],
           "rounds": s.rounds, "y25": s.y25, "seats": s.gm, "fee": s.fee}
    if tag:
        out["tag"] = tag
    return out


MIX = (("borderline", 20), ("likely", 15), ("safe", 15))


def mixed(seats, tags, size=50):
    chosen = set()
    for tag, n in MIX:
        chosen.update([i for i, s in enumerate(seats) if tags[i] == tag][:n])
    for i in range(len(seats)):
        if len(chosen) >= size:
            break
        chosen.add(i)
    return [seats[i] for i in sorted(chosen)]  # seats are already in demand order


def in_area(s, area):
    return area == "all" or INFO[s.code]["blr"] == (area == "blr")


@lru_cache(maxsize=512)
def _ranked(marks, rank, branches):
    st = Student(Form(marks=marks, rank=rank, branches=list(branches)))
    groups = set(branches)
    pool = [s for s in SEATS if not groups or group_of(s.cc) in groups]
    reach, tags, near = [], {}, []
    for s in pool:
        t = st.judge(s.close)
        if t:
            tags[id(s)] = t
            reach.append(s)
        elif s.close >= st.lo / 1.15:
            near.append(s)
    lists, reach_by_area = {}, {}
    for area in ("all", "blr", "other"):
        mine = [s for s in reach if in_area(s, area)]
        lists[area] = mixed(mine, [tags[id(s)] for s in mine])
        reach_by_area[area] = len(mine)
    return st, tags, lists, near, len(reach), len(pool), reach_by_area


def result_block(st: Student, in_reach, total):
    f = st.f
    res = {"rank": st.shown, "mid": st.mid, "from_marks": st.from_marks, "candidates": N, "in_reach": in_reach, "total": total,
           "summary": " · ".join([f"{f.marks} / {MAX_MARKS} marks" if st.from_marks else f"Rank {fmt(f.rank)}", "GM · All India"])}
    if st.from_marks:
        res["spread"] = (f"{f.marks} marks par 3 alag analysis rank {fmt(st.lo)} se {fmt(st.hi)} tak batate hain; "
                         f"beech ka andaaza {fmt(st.mid)}.")
        res["check"] = "COMEDK marks-rank table publish nahi karta, isliye ye andaaza hai. Rank card aa gaya ho to Rank daalo."
    return res


def predict(body: ComedkIn):
    st, tags, lists, near, in_reach, total, reach = _ranked(body.marks, body.rank, tuple(body.branches))
    chosen = lists[body.area]
    page = chosen[(body.page - 1) * 25: body.page * 25]
    near_items = []
    for s in near:
        if in_area(s, body.area):
            it = item(s)
            it["gap"] = st.gap(s.close)
            near_items.append(it)
            if len(near_items) == 5:
                break
    return {"result": result_block(st, in_reach, total), "counts": {k: len(v) for k, v in lists.items()}, "reach": reach, "area": body.area,
            "page": body.page, "pages": max(1, math.ceil(len(chosen) / 25)), "total": len(chosen),
            "items": [item(s, tags[id(s)]) for s in page], "near": near_items, "rounds": ROUNDS, "notes": NOTES}


def ladder_line(name, rounds, cells):
    """Same rule as the app's round ladder: surely in once the worst estimate is inside, borderline if only the best is."""
    sure = next((rounds[i] for i, c in enumerate(cells) if c["close"] and c.get("hi") is not None and c["close"] >= c["hi"]), None)
    maybe = next((rounds[i] for i, c in enumerate(cells) if c["in"]), None)
    if sure:
        return f"{name}: aapki rank {sure} se andar aati hai."
    if maybe:
        return f"{name}: {maybe} se borderline, aapki range ke andar par pakka nahi."
    return f"{name}: aapki rank kisi round ki closing rank tak nahi pahunchi."


def college(body: ComedkCollegeIn):
    if body.code not in BY_COLLEGE:
        raise HTTPException(404, "College nahi mila.")
    st = Student(body)
    seats = BY_COLLEGE[body.code]
    shown = seats if body.all or len(seats) <= 12 else seats[:10]
    if body.course and body.course not in {s.cc for s in shown}:
        shown = shown + [s for s in seats if s.cc == body.course]
    rows = []
    for s in shown:
        cells = [{"close": c, "in": bool(c and st.lo <= c), "mine": st.lo, "hi": st.hi} for c in s.rounds]
        first = next((ROUNDS[i] for i, c in enumerate(cells) if c["in"]), None)
        rows.append({"cc": s.cc, "course": _D["courses"].get(s.cc, s.cc), "group": group_of(s.cc), "cells": cells, "close": s.close,
                     "round": ROUNDS[s.rnd], "first_in": first, "y25": s.y25, "seats": s.gm, "fee": s.fee, "tag": st.judge(s.close)})
    target = next((r for r in rows if r["cc"] == body.course), None) or next((r for r in rows if r["first_in"]), None)
    line = ladder_line(target["course"], ROUNDS, target["cells"]) if target else "Aapki rank is college ke kisi course ke kisi round mein andar nahi aayi."
    return {"college": INFO[body.code], "your_rank": {"label": "COMEDK rank", "range": st.shown}, "rounds": ROUNDS,
            "rows": rows, "total": len(seats), "line": line, "y25_label": "2025 final", "official": OFFICIAL}


def meta():
    return {"groups": GROUP_NAMES, "candidates": N, "max_marks": MAX_MARKS, "rounds": ROUNDS, "notes": NOTES, "sources": SOURCES}
