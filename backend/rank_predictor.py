"""JEELIVE.AI Rank: JEE Main 2026 marks / percentile -> rank -> college-branch, from backend/rank_data only.

Everything here is a pure in-memory lookup over the official 2026 data (built by tools/rank_data/build_rank_data.py);
no request ever reaches a government site, so a result comes back in a few milliseconds.
"""
import bisect, gzip, json, math
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import rank_bitsat
import rank_comedk

DIR = Path(__file__).parent / "rank_data"
DATA = json.load(gzip.open(DIR / "jee_main_2026.json.gz", "rt", encoding="utf-8"))
_T25 = json.load(gzip.open(DIR / "jee_main_2025_close.json.gz", "rt", encoding="utf-8"))  # JoSAA 2025 final round
Y25_LABEL = f"2025 R{_T25['round']}"
Y25 = {tuple(r[:5]): r[5] for r in _T25["seats"]}
NTA = DATA["meta"]["nta"]
N = NTA["candidates"]
INST, PROGS = DATA["institutes"], DATA["programs"]

STATES = [
    "Andaman & Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh",
    "Dadra & Nagar Haveli and Daman & Diu", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu & Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
]
GROUPS = ["Computer Science", "AI & Data Science", "Information Technology", "Mathematics & Computing", "Electronics & Communication",
          "Electrical", "Instrumentation", "Mechanical", "Civil", "Chemical", "Metallurgy & Materials", "Production & Industrial",
          "Aerospace", "Biotechnology", "Engineering Physics", "Mining", "Robotics & Mechatronics", "Environmental",
          "Food/Textile/Ceramic", "Science & integrated courses"]
CATEGORIES = ["GEN", "EWS", "OBC-NCL", "SC", "ST"]
JOSAA_ROUNDS = ["R1", "R2", "R3", "R4", "R5", "CSAB 1", "CSAB 2"]
JAC_ROUNDS = ["R1", "R2", "R3", "R4", "Upgrade", "Spot"]
QUOTA_LABEL = {"AI": "All India", "HS": "Home state", "OS": "Other state", "GO": "Goa quota", "JK": "J&K quota",
               "LA": "Ladakh quota", "DL": "Delhi region", "OD": "Outside Delhi"}
OFFICIAL = {"josaa": "https://josaa.admissions.nic.in/Applicant/SeatAllotmentResult/CurrentORCR.aspx",
            "csab": "https://admissions.nic.in/csabspl/Applicant/seatallotmentresult/currentorcr.aspx",
            "jac": "https://jacdelhi.admissions.nic.in/or-cr/"}
NOTE = "2026 ke data par estimate. Asli cutoff har saal badalta hai."
MISSING = ["JAC Delhi ki Upgradation aur Spot round ki closing rank JAC ne publish nahi ki, isliye wo khaane khaali hain.",
           "IIIT-Delhi Round 1 ki PDF ka format alag hai; uski Round 1 rank abhi shaamil nahi."]

# ---------- marks <-> percentile (2026 shift tables grouped into Tough / Normal / Easy papers) ----------
CURVES = {lvl: (c["pct"], c["marks"]) for lvl, c in DATA["marks"].items()}


def _lerp(x, xs, ys):
    i = bisect.bisect_left(xs, x)
    if i <= 0:
        return ys[0]
    if i >= len(xs):
        return ys[-1]
    x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
    return y0 if x1 == x0 else y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def pct_from_marks(marks: float, level: str) -> float:
    pct, mk = CURVES[level]
    return min(100.0, max(0.0, _lerp(marks, mk, pct)))


def marks_at(pct: float, level: str) -> float:
    p, mk = CURVES[level]
    return _lerp(pct, p, mk)


# ---------- percentile <-> CRL, fitted on NTA's own count at the General cut-off ----------
P_UR, R_UR = NTA["advanced_cutoff"][0][2], NTA["advanced_cutoff"][0][3]
K_UR = R_UR / ((100 - P_UR) / 100 * N)  # 0.956: NTA's count sits below the plain formula


def _k(p):
    x = 100 - p
    if x <= 100 - P_UR:
        return 1 - (1 - K_UR) * x / (100 - P_UR)
    return K_UR + (1 - K_UR) * (x - (100 - P_UR)) / P_UR


def rank_from_pct(p: float) -> int:
    p = min(100.0, max(0.0, p))
    return max(1, min(N, round(_k(p) * (100 - p) / 100 * N)))


def pct_from_rank(r: float) -> float:
    lo, hi = 0.0, 100.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if _k(mid) * (100 - mid) / 100 * N > r:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- category rank: share of each category along the CRL, from NTA's category counts ----------
# Above the General cut-off NTA publishes no split, so the top band uses typical shares (estimate).
TOP_SHARE = {"EWS": 0.13, "OBC-NCL": 0.27, "SC": 0.045, "ST": 0.013}
PWD_SHARE = NTA["categories"]["PwD"] / N


def _bands(cat):
    row = next(r for r in NTA["advanced_cutoff"] if r[0] == cat)
    r_cut = rank_from_pct(row[2])
    top = TOP_SHARE[cat] * R_UR
    band = row[3] / (r_cut - R_UR)
    rest = (NTA["categories"][cat] - top - row[3]) / (N - r_cut)
    return [(0, R_UR, TOP_SHARE[cat]), (R_UR, r_cut, band), (r_cut, N, rest)]


BANDS = {c: _bands(c) for c in TOP_SHARE}


def cat_rank(crl: float, cat: str) -> int:
    total = 0.0
    for a, b, share in BANDS[cat]:
        if crl <= a:
            break
        total += (min(crl, b) - a) * share
    return max(1, round(total))


def crl_from_cat(rank: float, cat: str) -> float:
    total = 0.0
    for a, b, share in BANDS[cat]:
        width = (b - a) * share
        if rank <= total + width:
            return a + (rank - total) / share
        total += width
    return N


# ---------- seats ----------
class Seat:
    __slots__ = ("prog", "inst", "kind", "state", "quota", "cat", "pwd", "female", "jac", "opens", "closes", "jclose", "jround", "cclose", "cround", "y25")

    def __init__(self, row):
        self.prog, self.quota, self.cat, self.pwd, self.female, self.opens, self.closes = row
        p = PROGS[self.prog]
        self.inst = p["inst"]
        inst = INST[self.inst]
        self.kind, self.state, self.jac = inst["type"], inst["state"], inst["body"] == "jac"
        main = self.closes[:4] if self.jac else self.closes[:5]
        best = max(((c, i) for i, c in enumerate(main) if c), default=(None, None))
        self.jclose, self.jround = best
        csab = [] if self.jac else [(c, i) for i, c in enumerate(self.closes[5:7], 5) if c]
        self.cclose, self.cround = max(csab) if csab else (None, None)
        self.y25 = Y25.get((self.prog, self.quota, self.cat, self.pwd, self.female))


SEATS = [Seat(r) for r in DATA["seats"]]
BY_INST = {}
for _s in SEATS:
    BY_INST.setdefault(_s.inst, []).append(_s)
INF = float("inf")


def round_label(seat, i):
    return (JAC_ROUNDS if seat.jac else JOSAA_ROUNDS)[i]


def cap(r):
    return 200 if r < 2000 else 500 if r < 10000 else 1000


def fmt(n):
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + parts + [tail])


class Form(BaseModel):
    marks: Optional[int] = Field(default=None, ge=-75, le=300)
    percentile: Optional[float] = Field(default=None, ge=0, le=100)
    level: Literal["tough", "normal", "easy"] = "normal"
    category: Literal["GEN", "EWS", "OBC-NCL", "SC", "ST"] = "GEN"
    female: bool = False
    pwd: bool = False
    state: Optional[str] = None
    branches: List[str] = []

    @field_validator("state")
    @classmethod
    def known_state(cls, v):
        if v and v not in STATES:
            raise ValueError("unknown state")
        return v or None

    @field_validator("branches")
    @classmethod
    def known_groups(cls, v):
        return sorted({g for g in v if g in GROUPS})

    def key(self):
        return tuple(tuple(self.branches) if k == "branches" else getattr(self, k) for k in FORM_FIELDS)


FORM_FIELDS = ("marks", "percentile", "level", "category", "female", "pwd", "state", "branches")


class PredictIn(Form):
    segment: Literal["all", "NIT", "IIIT", "GFTI", "DELHI"] = "all"
    page: int = Field(default=1, ge=1, le=2)
    page_size: Literal[20, 25] = 25


class CollegeIn(Form):
    inst: int = Field(ge=0)
    prog: Optional[int] = None
    quota: Optional[str] = None
    gender: Optional[Literal["N", "F"]] = None
    seat: Optional[Literal["open", "cat"]] = None
    all: bool = False


class Student:
    """Everything the seat check needs, worked out once per form."""

    def __init__(self, f: Form):
        if f.percentile is None and f.marks is None:
            raise HTTPException(422, "Marks ya percentile mein se koi ek daalo.")
        self.f = f
        self.from_marks = f.percentile is None
        p = pct_from_marks(f.marks, f.level) if self.from_marks else f.percentile
        self.pct = p
        r = rank_from_pct(p)
        w = min(cap(r), max(4, round(r * (0.10 if self.from_marks else 0.02))))
        self.hi = min(N, max(1, r - w // 2) + w)
        self.lo = max(1, self.hi - w)
        self.mid = r
        self.cat = None if f.category == "GEN" else f.category

    def crl_range(self):
        return self.lo, self.mid, self.hi

    def ranks_for(self, cat, pwd, crl_only):
        lo, mid, hi = self.crl_range()
        if crl_only:
            return lo, mid, hi, "CRL"
        if cat != "OPEN":
            lo, mid, hi = cat_rank(lo, cat), cat_rank(mid, cat), cat_rank(hi, cat)
        if pwd:
            lo, mid, hi = max(1, round(lo * PWD_SHARE)), max(1, round(mid * PWD_SHARE)), max(1, round(hi * PWD_SHARE))
        label = ("CRL" if cat == "OPEN" else f"{cat} rank") if not pwd else ("PwD rank" if cat == "OPEN" else f"{cat}-PwD rank")
        return lo, mid, hi, label

    def eligible(self, s: Seat):
        f = self.f
        if s.cat != "OPEN" and s.cat != self.cat:
            return False
        if s.pwd and not f.pwd or s.female and not f.female:
            return False
        q = s.quota
        if q in ("DL", "OD"):
            return (q == "DL") == (f.state == "Delhi")
        if q == "AI":
            return True
        if q == "HS":
            return f.state == s.state
        if q == "OS":
            return f.state != s.state
        return f.state == {"GO": "Goa", "JK": "Jammu & Kashmir", "LA": "Ladakh"}[q]


STATUS_ORDER = {"safe": 3, "likely": 2, "borderline": 1}


def judge(close, lo, mid, hi):
    if not close or close < lo:
        return None
    if close >= hi and close >= 1.15 * mid:
        return "safe"
    return "likely" if close >= hi else "borderline"


def path_label(s: Seat):
    seat = s.cat if s.cat != "OPEN" else "Open"
    if s.pwd:
        seat += " (PwD)"
    parts = [QUOTA_LABEL[s.quota], seat]
    if s.female:
        parts.append("Female-only")
    return " · ".join(parts)


def best_paths(st: Student):
    """Per program: the easiest seat this student can get, or the nearest miss."""
    best, near = {}, {}
    groups = set(st.f.branches)
    for s in SEATS:
        if groups and PROGS[s.prog]["group"] not in groups:
            continue
        if not st.eligible(s):
            continue
        options = []
        if s.jclose:
            lo, mid, hi, label = st.ranks_for(s.cat, s.pwd, s.jac)
            options.append((judge(s.jclose, lo, mid, hi), s.jclose, s.jround, lo, mid, label))
        if s.cclose:
            lo, mid, hi, _ = st.ranks_for(s.cat, s.pwd, True)
            st_c = judge(s.cclose, lo, mid, hi)
            options.append(("borderline" if st_c else None, s.cclose, s.cround, lo, mid, "CRL"))
        for status, close, rnd, lo, mid, label in options:
            ease = close / max(mid, 1)
            if status:
                cand = (STATUS_ORDER[status], ease, status, close, rnd, label, s)
                if s.prog not in best or cand[:2] > best[s.prog][:2]:
                    best[s.prog] = cand
            elif close >= lo / 1.10:
                cand = (ease, close, rnd, label, s)
                if s.prog not in near or cand[0] > near[s.prog][0]:
                    near[s.prog] = cand
    return best, near


def demand_key(prog):
    d = PROGS[prog]["demand"]
    return (d is None, d or 0, prog)


def item(prog, close, rnd, label, s, status=None):
    p = PROGS[prog]
    inst = INST[p["inst"]]
    out = {"prog": prog, "inst": p["inst"], "college": inst["short"], "type": inst["type"], "branch": p["name"],
           "degree": p["degree"], "close": close, "round": round_label(s, rnd), "rank_type": label,
           "path": path_label(s), "quota": s.quota, "gender": "F" if s.female else "N", "seat": "open" if s.cat == "OPEN" else "cat",
           "y25": s.y25, "y26": s.jclose}
    if status:
        out["tag"] = status
    return out


def result_block(st: Student):
    f = st.f
    lo, mid, hi = st.crl_range()
    p_hi, p_lo = pct_from_rank(lo), pct_from_rank(hi)
    if p_hi - p_lo > 0.5:
        mid_p = (p_hi + p_lo) / 2
        p_hi, p_lo = mid_p + 0.25, mid_p - 0.25
    res = {"percentile": [round(p_lo, 2), round(min(100, p_hi), 2)], "crl": [lo, hi], "from_marks": st.from_marks,
           "summary": " · ".join(x for x in [f"{f.marks} marks" if st.from_marks else f"{f.percentile:g} percentile",
                                              f.level.capitalize() if st.from_marks else None,
                                              {"GEN": "General"}.get(f.category, f.category),
                                              "Female" if f.female else None, "PwD" if f.pwd else None] if x)}
    if not st.from_marks:
        res["percentile"] = [round(f.percentile, 2), round(f.percentile, 2)]
    if st.cat:
        res["cat_rank"] = {"label": f"{st.cat} rank", "range": [cat_rank(lo, st.cat), cat_rank(hi, st.cat)]}
    if f.pwd:
        base = (cat_rank(lo, st.cat), cat_rank(hi, st.cat)) if st.cat else (lo, hi)
        res["pwd_rank"] = {"label": "PwD rank" if not st.cat else f"{st.cat}-PwD rank",
                           "range": [max(1, round(base[0] * PWD_SHARE)), max(1, round(base[1] * PWD_SHARE))]}
    if st.from_marks:
        tough = rank_from_pct(pct_from_marks(f.marks, "tough"))
        easy = rank_from_pct(pct_from_marks(f.marks, "easy"))
        res["spread"] = f"Tough paper hota to rank lagbhag {fmt(tough)}, Easy paper hota to lagbhag {fmt(easy)}."
    elif f.marks is not None:
        fits = {lvl: abs(marks_at(f.percentile, lvl) - f.marks) for lvl in CURVES}
        paper = min(fits, key=fits.get)
        res["paper"] = f"Aapke marks ke hisaab se paper {paper.capitalize()} jaisa tha."
        if f.marks < marks_at(f.percentile, "tough") - 12 or f.marks > marks_at(f.percentile, "easy") + 12:
            res["check"] = "Marks aur percentile aapas mein mel nahi kha rahe, ek baar check kar lo."
    if f.state == "Delhi":
        res["delhi_note"] = "Delhi region cutoff ke liye 11th-12th Delhi ke school se hona zaroori hai."
    return res


def marks_gap(st: Student, close, label, s):
    """How much more the student needs for this closing rank: marks if they typed marks, else percentile."""
    crl_needed = close
    if label not in ("CRL",):
        base = close / PWD_SHARE if s.pwd else close
        crl_needed = crl_from_cat(base, s.cat) if s.cat != "OPEN" else base
    p_need = pct_from_rank(crl_needed)
    if st.from_marks:
        gap = math.ceil(marks_at(p_need, st.f.level) - st.f.marks)
        return f"lagbhag +{max(1, gap)} marks aur"
    return f"lagbhag +{max(0.01, p_need - st.pct):.2f} percentile aur"


# The 50 shown are the most wanted seats of each chance, so a student always sees dream, fair and safe picks together.
MIX = (("borderline", 20), ("likely", 15), ("safe", 15))


def mixed(ordered, best, size=50):
    chosen = set()
    for tag, n in MIX:
        chosen.update([p for p in ordered if best[p][2] == tag][:n])
    for p in ordered:
        if len(chosen) >= size:
            break
        chosen.add(p)
    return sorted(chosen, key=demand_key)


@lru_cache(maxsize=512)
def _ranked(key):
    f = Form(**{k: (list(v) if k == "branches" else v) for k, v in zip(FORM_FIELDS, key)})
    st = Student(f)
    best, near = best_paths(st)
    ordered = sorted(best, key=demand_key)
    lists = {"all": mixed(ordered, best)}
    for kind in ("NIT", "IIIT", "GFTI", "DELHI"):
        lists[kind] = mixed([p for p in ordered if INST[PROGS[p]["inst"]]["type"] == kind], best)
    near_sorted = sorted(near, key=demand_key)
    return st, best, near, lists, near_sorted


def predict(body: PredictIn):
    st, best, near, lists, near_sorted = _ranked(body.key())
    chosen = lists[body.segment] if body.page_size == 25 else lists[body.segment][:20]
    start = (body.page - 1) * body.page_size
    page = chosen[start:start + body.page_size]
    items = []
    for prog in page:
        _, _, status, close, rnd, label, s = best[prog]
        items.append(item(prog, close, rnd, label, s, status))
    seg = body.segment
    near_items = []
    for prog in near_sorted:
        if seg != "all" and INST[PROGS[prog]["inst"]]["type"] != seg:
            continue
        _, close, rnd, label, s = near[prog]
        it = item(prog, close, rnd, label, s)
        it["gap"] = marks_gap(st, close, label, s)
        near_items.append(it)
        if len(near_items) == 5:
            break
    reach = {"all": len(best), **{k: sum(1 for p in best if INST[PROGS[p]["inst"]]["type"] == k) for k in ("NIT", "IIIT", "GFTI", "DELHI")}}
    return {"result": result_block(st), "counts": {k: len(v) for k, v in lists.items()}, "reach": reach, "segment": seg,
            "page": body.page, "pages": max(1, math.ceil(len(chosen) / body.page_size)), "total": len(chosen),
            "items": items, "near": near_items if body.page_size == 25 else [], "note": NOTE}


SPECIAL_STATE = {"GO": "Goa", "JK": "Jammu & Kashmir", "LA": "Ladakh"}


def blocked(st: Student, inst, quota, gender):
    """Why this quota / gender path is closed to this student, or None if it is open to them."""
    f = st.f
    if gender == "F" and not f.female:
        return "Female-only seat sirf girls ke liye hai"
    if quota == "HS" and f.state != inst["state"]:
        return f"Home state quota sirf {inst['state']} ke students ke liye hai"
    if quota == "OS" and f.state == inst["state"]:
        return f"Aapka home state {inst['state']} hai, isliye Other state seat nahi milegi"
    if quota == "DL" and f.state != "Delhi":
        return "Delhi region seat sirf Delhi se 12th pass students ke liye hai"
    if quota == "OD" and f.state == "Delhi":
        return "Delhi ke students Delhi region seat lete hain, Outside Delhi nahi"
    if quota in SPECIAL_STATE and f.state != SPECIAL_STATE[quota]:
        return f"{QUOTA_LABEL[quota]} sirf {SPECIAL_STATE[quota]} ke students ke liye hai"
    return None


def college(body: CollegeIn):
    if body.inst >= len(INST):
        raise HTTPException(404, "College nahi mila.")
    st = Student(body)
    inst = INST[body.inst]
    seats = BY_INST[body.inst]
    rounds = JAC_ROUNDS if inst["body"] == "jac" else JOSAA_ROUNDS
    quotas = sorted({s.quota for s in seats if s.quota in ("AI", "HS", "OS", "DL", "OD") or st.eligible(s)},
                    key=lambda q: list(QUOTA_LABEL).index(q))
    quota = body.quota if body.quota in quotas else next((q for q in quotas if any(st.eligible(s) for s in seats if s.quota == q)), quotas[0])
    gender = body.gender or ("F" if body.female and inst["type"] == "DELHI" and "Women" in inst["name"] else "N")
    if not any(s.female == (gender == "F") for s in seats if s.quota == quota):
        gender = "F" if gender == "N" else "N"
    seat_kind = body.seat or "open"
    cat = "OPEN" if seat_kind == "open" or not st.cat else st.cat
    pwd = body.pwd and any(s.pwd and s.quota == quota and s.cat == cat for s in seats)
    lo, mid, hi, label = st.ranks_for(cat, pwd, inst["body"] == "jac")
    crl = st.crl_range()
    block = blocked(st, inst, quota, gender)
    rows = {}
    for s in seats:
        if s.quota == quota and s.female == (gender == "F") and s.cat == cat and bool(s.pwd) == pwd:
            rows[s.prog] = s
    progs = sorted(rows, key=demand_key)
    shown = progs if body.all else progs[:10]
    if body.prog in rows and body.prog not in shown:  # the tapped branch is always in the sheet, even outside the top 10
        shown = shown + [body.prog]
    out_rows = []
    for prog in shown:
        s = rows[prog]
        cells = []
        for i in range(len(rounds)):
            close = s.closes[i] if i < len(s.closes) else None
            opening = s.opens[i] if i < len(s.opens) else None
            csab = i >= 5 and not s.jac
            mine, worst = (crl[0], crl[2]) if csab else (lo, hi)
            cells.append({"open": opening, "close": close, "in": bool(not block and close and mine <= close),
                          "mine": None if block else mine, "hi": None if block else worst,
                          "unpublished": bool(s.jac and i >= 4)})
        first = next((rounds[i] for i, c in enumerate(cells) if c["in"]), None)
        out_rows.append({"prog": prog, "branch": PROGS[prog]["name"], "degree": PROGS[prog]["degree"], "cells": cells, "first_in": first, "y25": s.y25})
    target = next((r for r in out_rows if r["prog"] == body.prog), None) or next((r for r in out_rows if r["first_in"]), None)
    line = None
    if block:
        line = f"Ye raasta aapke liye nahi: {block}."
    elif target:
        line = rank_comedk.ladder_line(target["branch"], rounds, target["cells"])
    elif out_rows:
        line = "Is raaste se aapki rank in branches ke kisi round mein andar nahi aayi."
    return {
        "college": {"id": body.inst, "name": inst["name"], "short": inst["short"], "type": inst["type"], "city": inst["city"], "state": inst["state"]},
        "your_rank": {"label": label, "range": [lo, hi]}, "rounds": rounds, "rows": out_rows, "total": len(progs), "line": line,
        "blocked": block, "y25_label": None if inst["body"] == "jac" else Y25_LABEL,
        "path": {"quota": quota, "gender": gender, "seat": "cat" if cat != "OPEN" else "open"},
        "options": {"quota": [{"key": q, "label": QUOTA_LABEL[q]} for q in quotas],
                    "gender": [g for g in ("N", "F") if any(s.female == (g == "F") and s.quota == quota for s in seats)],
                    "seat": ["open"] + (["cat"] if st.cat and any(s.cat == st.cat and s.quota == quota for s in seats) else []),
                    "cat_label": st.cat},
        "official": OFFICIAL["jac"] if inst["body"] == "jac" else OFFICIAL["josaa"],
        "official_csab": None if inst["body"] == "jac" else OFFICIAL["csab"],
    }


CHART = ([round(99.9 - 0.1 * i, 1) for i in range(10)] + [round(98.8 - 0.2 * i, 1) for i in range(20)]
         + [round(94.5 - 0.5 * i, 1) for i in range(10)] + [float(89 - i) for i in range(10)])


def meta():
    return {
        "states": STATES, "branches": GROUPS, "categories": CATEGORIES, "y25_label": Y25_LABEL,
        "chart": [{"pct": p, "rank": rank_from_pct(p), "marks": round(marks_at(p, "normal"))} for p in CHART],
        "note": NOTE, "missing": MISSING, "candidates": N,
        "sources": [{"label": "NTA JEE Main 2026 result (20 Apr 2026)", "url": "https://cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2026/04/20260420809492136.pdf"},
                    {"label": "JoSAA 2026 Round 1-5", "url": OFFICIAL["josaa"]}, {"label": "CSAB Special 2026 Round 1-2", "url": OFFICIAL["csab"]},
                    {"label": "JAC Delhi 2026 Round 1-4", "url": OFFICIAL["jac"]},
                    {"label": "JoSAA 2025 final round (archive)", "url": "https://josaa.admissions.nic.in/applicant/seatmatrix/openingclosingrankarchieve.aspx"},
                    {"label": "BITS admissions: BITSAT cut-offs", "url": rank_bitsat.SOURCE}],
        "comedk": rank_comedk.meta(),
    }


def make_router():
    router = APIRouter(prefix="/rank", tags=["Rank predictor"])
    router.get("/meta")(meta)
    router.post("/predict")(predict)
    router.post("/college")(college)
    router.post("/bitsat")(rank_bitsat.predict)
    router.post("/comedk")(rank_comedk.predict)
    router.post("/comedk/college")(rank_comedk.college)
    return router
