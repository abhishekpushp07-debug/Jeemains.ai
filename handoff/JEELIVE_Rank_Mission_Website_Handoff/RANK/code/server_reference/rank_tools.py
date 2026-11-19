"""JEELIVE.AI Rank tools beside the two predictors: NTA percentile -> rank, target marks for a chosen college, and the
side-by-side compare of saved colleges. Same in-memory data as rank_predictor / rank_comedk / rank_bitsat, plus the
JoSAA 2026 seat matrix (tools/rank_data/build_seat_matrix.py).
"""
import json, math
from typing import List, Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

import rank_bitsat
import rank_comedk as ck
import rank_predictor as rp

_SM = rp.DIR / "jee_main_2026_seat_matrix.json"
JEE_SEATS = {int(k): v for k, v in json.load(open(_SM))["seats"].items()} if _SM.exists() else {}
LEVELS = ("tough", "normal", "easy")
Category = Literal["GEN", "EWS", "OBC-NCL", "SC", "ST"]
JEE_FEE_NOTE = "JoSAA college-wise fee publish nahi karta; JEE colleges ki fee college ki website par dekho."


# ---------- percentile -> rank ----------
class PercentileIn(BaseModel):
    percentile: float = Field(ge=0, le=100)
    category: Category = "GEN"
    pwd: bool = False


def percentile(body: PercentileIn):
    st = rp.Student(rp.Form(percentile=body.percentile, category=body.category, pwd=body.pwd))
    return {"result": rp.result_block(st), "candidates": rp.N,
            "marks": [{"level": lvl, "marks": round(rp.marks_at(body.percentile, lvl))} for lvl in LEVELS],
            "notes": ["Rank NTA JEE Main 2026 ke 15.38 lakh candidates ke percentile data se; same percentile par rank ki chhoti si range banti hai.",
                      "Category aur PwD rank estimate hain; NTA inki table nahi deta.",
                      "Marks = is percentile ke liye us type ki shift mein lagbhag kitne marks lage."]}


# ---------- target marks ----------
def _marks(crl):
    p = rp.pct_from_rank(crl)
    return round(p, 2), {lvl: min(300, max(-75, math.ceil(rp.marks_at(p, lvl)))) for lvl in LEVELS}


def _crl_needed(close, s, i):
    """The CRL a student needs for a closing rank: CSAB and JAC close on CRL, JoSAA category / PwD seats on their own rank."""
    if s.jac or i >= 5:
        return close
    base = close / rp.PWD_SHARE if s.pwd else close
    return rp.crl_from_cat(base, s.cat) if s.cat != "OPEN" else base


def _rank_type(s):
    if s.jac or (s.cat == "OPEN" and not s.pwd):
        return "CRL"
    if s.pwd:
        return "PwD rank" if s.cat == "OPEN" else f"{s.cat}-PwD rank"
    return f"{s.cat} rank"


class Profile(BaseModel):
    """The student's JEE seat profile (from the College predictor form)."""
    category: Category = "GEN"
    female: bool = False
    pwd: bool = False
    state: Optional[str] = None

    @field_validator("state")
    @classmethod
    def known_state(cls, v):
        if v and v not in rp.STATES:
            raise ValueError("unknown state")
        return v or None


class TargetJeeIn(Profile):
    inst: int = Field(ge=0)


def target_jee(body: TargetJeeIn):
    if body.inst >= len(rp.INST):
        raise HTTPException(404, "College nahi mila.")
    inst = rp.INST[body.inst]
    # Only the seat rules are used here; the placeholder percentile never reaches the answer.
    st = rp.Student(rp.Form(percentile=50, category=body.category, female=body.female, pwd=body.pwd, state=body.state))
    best = {}
    for s in rp.BY_INST[body.inst]:
        if not s.jclose or not st.eligible(s):
            continue
        need = _crl_needed(s.jclose, s, s.jround)
        if s.prog not in best or need > best[s.prog][0]:
            best[s.prog] = (need, s)
    rounds = rp.JAC_ROUNDS if inst["body"] == "jac" else rp.JOSAA_ROUNDS
    rows = []
    for prog in sorted(best, key=rp.demand_key):
        need, s = best[prog]
        cells = []
        for i, label in enumerate(rounds):
            close = s.closes[i] if i < len(s.closes) else None
            if close:
                crl = _crl_needed(close, s, i)
                pct, marks = _marks(crl)
                cells.append({"label": label, "close": close, "crl": round(crl), "pct": pct, "marks": marks})
            else:
                cells.append({"label": label, "close": None, "unpublished": bool(s.jac and i >= 4)})
        pct, marks = _marks(need)
        p = rp.PROGS[prog]
        rows.append({"prog": prog, "branch": p["name"], "degree": p["degree"], "group": p["group"], "path": rp.path_label(s),
                     "quota": s.quota, "gender": "F" if s.female else "N",
                     "rank_type": _rank_type(s), "cells": cells, "seats": JEE_SEATS.get(prog), "y25": s.y25,
                     "final": {"label": rounds[s.jround], "close": s.jclose, "crl": round(need), "pct": pct, "marks": marks}})
    return {"exam": "jee", "college": {"id": body.inst, "name": inst["name"], "short": inst["short"], "type": inst["type"],
                                       "city": inst["city"], "state": inst["state"]},
            "rounds": rounds, "rows": rows,
            "official": rp.OFFICIAL["jac"] if inst["body"] == "jac" else rp.OFFICIAL["josaa"],
            "notes": ["Target = 2026 mein us round ki closing rank tak pahunchne ke liye lagbhag kitne marks (paper type ke hisaab se).",
                      "Sabse aasaan seat raasta liya gaya hai jo aapke category, state aur gender par khulta hai.",
                      "Cutoff har saal badalta hai; 10-15 marks extra ka target rakho."]}


class TargetComedkIn(BaseModel):
    code: str


def _comedk_marks(close):
    per = [next((m for m in range(ck.MAX_MARKS + 1) if ck._curve_rank(c["points"], m) <= close), ck.MAX_MARKS) for c in ck.CURVES]
    return [min(per), max(per)], ck.marks_for(close)


def target_comedk(body: TargetComedkIn):
    if body.code not in ck.BY_COLLEGE:
        raise HTTPException(404, "College nahi mila.")
    rows = []
    for s in ck.BY_COLLEGE[body.code]:
        cells = []
        for label, close in zip(ck.ROUNDS, s.rounds):
            if close:
                rng, mid = _comedk_marks(close)
                cells.append({"label": label, "close": close, "marks": rng, "mid": mid})
            else:
                cells.append({"label": label, "close": None})
        rng, mid = _comedk_marks(s.close)
        rows.append({"cc": s.cc, "course": ck._D["courses"].get(s.cc, s.cc), "group": ck.group_of(s.cc), "cells": cells,
                     "final": {"label": ck.ROUNDS[s.rnd], "close": s.close, "marks": rng, "mid": mid},
                     "fee": s.fee, "seats": s.gm, "y25": s.y25})
    return {"exam": "comedk", "college": ck.INFO[body.code], "rounds": ck.ROUNDS, "rows": rows, "official": ck.OFFICIAL,
            "notes": ["Target = 2026 mein us round ki GM closing rank tak pahunchne ke liye lagbhag kitne marks (3 public analyses ki range).",
                      "COMEDK marks-rank table publish nahi karta; 5-10 marks extra ka target rakho."]}


def target_bitsat():
    return {"exam": "bitsat", "years": rank_bitsat.YEARS, "max": rank_bitsat.MAX, "source": rank_bitsat.SOURCE,
            "rows": [{"id": r["id"], "campus": r["campus"], "college": r["college"], "program": r["program"], "degree": r["degree"],
                      "cutoff": r["cutoff"], "history": r["history"], "safe": min(rank_bitsat.MAX, r["cutoff"] + 10)} for r in rank_bitsat.ROWS],
            "notes": ["BITSAT mein cutoff hi target hai: 2026 final cutoff, sab categories ke liye ek.",
                      "Safe = cutoff + 10, kyunki cutoff har saal 10-20 marks upar-neeche hota hai."]}


def colleges():
    jee = [{"inst": i, "short": c["short"], "name": c["name"], "type": c["type"], "state": c["state"], "city": c["city"]}
           for i, c in enumerate(rp.INST) if i in rp.BY_INST]
    comedk = [{"code": code, "short": ck.INFO[code]["short"], "name": ck.INFO[code]["name"], "city": ck.INFO[code]["city"]}
              for code in sorted(ck.BY_COLLEGE, key=lambda c: ck.BY_COLLEGE[c][0].demand)]
    bitsat = [{"campus": campus, "name": f"BITS {campus}", "programs": sum(r["campus"] == campus for r in rank_bitsat.ROWS)}
              for campus in ("Pilani", "Goa", "Hyderabad") if any(r["campus"] == campus for r in rank_bitsat.ROWS)]
    return {"jee": sorted(jee, key=lambda c: (c["type"] != "NIT", c["short"])), "comedk": comedk, "bitsat": bitsat}


# ---------- compare ----------
class CompareItem(BaseModel):
    exam: Literal["jee", "bitsat", "comedk"]
    id: str
    prog: Optional[int] = None
    quota: Optional[str] = None
    gender: Optional[Literal["N", "F"]] = None
    path: Optional[str] = None


class CompareIn(BaseModel):
    items: List[CompareItem] = Field(min_length=1, max_length=3)


def _jee_seat(it: CompareItem):
    """Saved JEE items carry prog, quota, gender and the readable path 'Home state · OBC-NCL (PwD) · Female-only'."""
    if it.prog is None or not it.path or it.prog >= len(rp.PROGS):
        return None
    part = (it.path.split(" · ") + ["", ""])[1]
    cat = "OPEN" if part.startswith("Open") else part.replace("(PwD)", "").strip()
    pwd, female = "(PwD)" in part, it.gender == "F"
    return next((s for s in rp.BY_INST[rp.PROGS[it.prog]["inst"]]
                 if s.prog == it.prog and s.quota == it.quota and s.cat == cat and bool(s.pwd) == pwd and bool(s.female) == female), None)


def _compare_one(it: CompareItem):
    if it.exam == "jee":
        s = _jee_seat(it)
        if not s:
            return {"exam": "jee", "id": it.id, "missing": True}
        p, inst = rp.PROGS[s.prog], rp.INST[s.inst]
        rounds = rp.JAC_ROUNDS if s.jac else rp.JOSAA_ROUNDS
        return {"exam": "jee", "id": it.id, "title": inst["short"], "name": inst["name"], "place": f"{inst['city']}, {inst['state']}",
                "sub": p["name"] + (f" ({p['degree']})" if p["degree"] else ""), "path": rp.path_label(s), "rank_label": _rank_type(s),
                # CSAB closes on CRL even for category / PwD seats, so those cells say so.
                "rounds": [{"label": rd, "close": s.closes[i] if i < len(s.closes) else None, "crl": i >= 5 and not s.jac and _rank_type(s) != "CRL"}
                           for i, rd in enumerate(rounds)],
                "final": {"label": rounds[s.jround], "close": s.jclose} if s.jclose else None,
                "prev": {"label": rp.Y25_LABEL, "close": s.y25} if not s.jac else None,
                "seats": JEE_SEATS.get(s.prog), "seats_label": "JoSAA seats (sab quota)" if not s.jac else None,
                "fee": None, "fee_note": JEE_FEE_NOTE, "higher_is_harder": False}
    if it.exam == "comedk":
        code, _, cc = it.id.partition("|")
        s = next((x for x in ck.BY_COLLEGE.get(code, []) if x.cc == cc), None)
        if not s:
            return {"exam": "comedk", "id": it.id, "missing": True}
        c = ck.INFO[code]
        return {"exam": "comedk", "id": it.id, "title": c["short"], "name": c["name"], "place": c["city"],
                "sub": ck._D["courses"].get(cc, cc), "path": "GM · All India", "rank_label": "COMEDK rank",
                "rounds": [{"label": rd, "close": v} for rd, v in zip(ck.ROUNDS, s.rounds)],
                "final": {"label": ck.ROUNDS[s.rnd], "close": s.close}, "prev": {"label": "2025 final", "close": s.y25},
                "seats": s.gm, "seats_label": "GM seats", "fee": s.fee, "higher_is_harder": False}
    r = next((x for x in rank_bitsat.ROWS if x["id"] == it.id), None)
    if not r:
        return {"exam": "bitsat", "id": it.id, "missing": True}
    years = rank_bitsat.YEARS
    return {"exam": "bitsat", "id": it.id, "title": r["college"], "name": r["college"], "place": r["campus"], "sub": r["program"],
            "path": "Sab categories, ek cutoff", "rank_label": f"score / {rank_bitsat.MAX}",
            "rounds": [{"label": str(y), "close": v} for y, v in zip(years, r["history"])],
            "final": {"label": str(years[-1]), "close": r["cutoff"]}, "prev": {"label": str(years[-2]), "close": r["last"]},
            "seats": None, "fee": None, "fee_note": "BITS program-wise fee aur seats bits-pilani.ac.in par.", "higher_is_harder": True}


def compare(body: CompareIn):
    return {"items": [_compare_one(it) for it in body.items],
            "notes": ["Closing rank: chhota number = mushkil seat. BITSAT mein ulta: zyada cutoff score = mushkil.",
                      "JEE seats = JoSAA 2026 seat matrix (us branch ki saari quota-category seats). COMEDK seats = sirf GM."]}


# ---------- college vs college ----------
class CollegeRef(BaseModel):
    exam: Literal["jee", "bitsat", "comedk"]
    id: str = Field(min_length=1, max_length=40)  # JEE institute number, COMEDK code, BITS campus


class CollegeCompareIn(Profile):
    items: List[CollegeRef] = Field(min_length=1, max_length=3)


CS = "Computer Science"


def _college_one(it: CollegeRef, prof: Profile):
    """One college as a whole: how many branches, the branch needing the fewest / most marks, its Computer Science seat,
    seats and fee. Marks = normal paper, the same numbers as Target marks (JEE: the student's easiest seat path)."""
    gone = {"exam": it.exam, "id": it.id, "missing": True}
    if it.exam == "jee":
        if not it.id.isdigit() or int(it.id) not in rp.BY_INST:
            return gone
        t = target_jee(TargetJeeIn(inst=int(it.id), **prof.model_dump(include={"category", "female", "pwd", "state"})))
        c = t["college"]
        sides = [{"branch": r["branch"] + (f" ({r['degree']})" if r["degree"] else ""), "close": r["final"]["close"], "label": r["final"]["label"],
                  "rank_label": r["rank_type"], "marks": r["final"]["marks"]["normal"], "cs": r["group"] == CS} for r in t["rows"]]
        head = {"title": c["short"], "name": c["name"], "place": f"{c['city']}, {c['state']}", "kind": c["type"]}
        seats, seats_label, fees, fee_note = sum(r["seats"] or 0 for r in t["rows"]), "JoSAA seats (sab quota)", [], JEE_FEE_NOTE
    elif it.exam == "comedk":
        if it.id not in ck.BY_COLLEGE:
            return gone
        t = target_comedk(TargetComedkIn(code=it.id))
        c = t["college"]
        sides = [{"branch": r["course"], "close": r["final"]["close"], "label": r["final"]["label"], "rank_label": "COMEDK rank",
                  "marks": r["final"]["mid"], "cs": r["group"] == CS} for r in t["rows"]]
        head = {"title": c["short"], "name": c["name"], "place": c["city"], "kind": "COMEDK"}
        seats, seats_label, fees, fee_note = sum(r["seats"] or 0 for r in t["rows"]), "GM seats", [r["fee"] for r in t["rows"] if r["fee"]], None
    else:
        rows = [r for r in rank_bitsat.ROWS if r["campus"] == it.id]
        if not rows:
            return gone
        sides = [{"branch": r["program"], "close": r["cutoff"], "label": str(rank_bitsat.YEARS[-1]), "rank_label": f"score / {rank_bitsat.MAX}",
                  "marks": r["cutoff"], "cs": CS in r["program"]} for r in rows]
        head = {"title": rows[0]["college"], "name": rows[0]["college"], "place": it.id, "kind": "BITS"}
        seats, seats_label, fees, fee_note = 0, None, [], "BITS program-wise fee aur seats bits-pilani.ac.in par."
    by_marks = sorted(sides, key=lambda s: s["marks"])
    cs = [s for s in sides if s["cs"]]
    return {"exam": it.exam, "id": it.id, **head, "branches": len(sides), "seats": seats or None, "seats_label": seats_label,
            "fee": [min(fees), max(fees)] if fees else None, "fee_note": fee_note,
            "easiest": by_marks[0] if by_marks else None, "toughest": by_marks[-1] if by_marks else None,
            "cs": max(cs, key=lambda s: s["marks"]) if cs else None, "cs_count": len(cs)}


def compare_colleges(body: CollegeCompareIn):
    return {"items": [_college_one(it, body) for it in body.items],
            "notes": ["Marks = normal paper par 2026 ki final closing tak pahunchne ke liye lagbhag kitne marks. JEE: aapki category, state aur gender ka sabse aasaan seat raasta.",
                      "Sabse aasaan branch = jisme sabse kam marks chahiye; sabse mushkil = sabse zyada.",
                      "Cutoff har saal badalta hai; 10-15 marks extra ka target rakho."]}


def register(router):
    router.post("/percentile")(percentile)
    router.post("/target/jee")(target_jee)
    router.post("/target/comedk")(target_comedk)
    router.get("/target/bitsat")(target_bitsat)
    router.get("/colleges")(colleges)
    router.post("/compare")(compare)
    router.post("/compare/colleges")(compare_colleges)
