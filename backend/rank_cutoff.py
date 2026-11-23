"""JEELIVE.AI Rank: Cut off. The student picks ONE thing, a college or a branch, and sees every round's 2026 cut-off:

    by = "college"  ->  every branch of that college
    by = "branch"   ->  the 100 most wanted college-branches of that branch

A score (marks, percentile or rank) is optional. With it only the rows the student can reach stay: Safe, Likely and
Borderline, by the College predictor's own rule (rank_predictor.judge / rank_comedk.Student.judge / rank_bitsat.chance).
JEE Main, COMEDK and BITSAT; the same in-memory data as every other Rank tool, so an answer takes a few milliseconds.
"""
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import Field

import rank_bitsat as rb
import rank_comedk as ck
import rank_predictor as rp
import rank_tools as rt

LIMIT = 100  # rows of a branch list
NEAR = 3     # nearest misses shown under a filtered list
KIND = {"NIT": "NIT", "IIIT": "IIIT", "GFTI": "GFTI", "DELHI": "JAC Delhi"}
JEE_COLUMNS, JAC_COLUMNS = rp.JOSAA_ROUNDS, rp.JAC_ROUNDS[:4]  # JAC never published its Upgrade / Spot ranks
COMEDK_MID = [ck.mid_rank(m) for m in range(ck.MAX_MARKS + 1)]  # marks -> middle rank estimate, worked out once
ELIGIBLE = "Eligible = Safe + Likely + Borderline, College predictor wala hi rule. Borderline kinare par hai, pakka nahi."


class CutoffIn(rt.Profile):
    """category, female, pwd and state (rank_tools.Profile) are used by JEE Main only."""
    exam: Literal["jee", "comedk", "bitsat"]
    by: Literal["college", "branch"]
    key: str = Field(min_length=1, max_length=60)  # exactly as GET /rank/cutoff/options gave it
    marks: Optional[int] = Field(default=None, ge=-130, le=390)
    percentile: Optional[float] = Field(default=None, ge=0, le=100)
    rank: Optional[int] = Field(default=None, ge=1, le=2_000_000)
    level: Literal["tough", "normal", "easy"] = "normal"  # JEE Main marks only: how hard the student's shift was


def _cell(label, close, state=None, **more):
    """One round of one row. state: "in" = the whole rank range is inside, "edge" = only part of it, "out"."""
    out = {"label": label, "close": close, **more}
    if state and close:
        out["state"] = state
    return out


def _state(close, lo, hi):
    return None if not close else "in" if close >= hi else "edge" if close >= lo else "out"


def _counts(rows):
    return {tag: sum(1 for r in rows if r["tag"] == tag) for tag in ("safe", "likely", "borderline")}


def _answer(body, head, columns, rows, total, you, near, notes, **more):
    """rows = every row that passed, most wanted first; a branch list keeps the first LIMIT of them."""
    shown = rows[:LIMIT] if body.by == "branch" else rows
    if you:
        you["counts"] = _counts(rows)
    return {"exam": body.exam, "by": body.by, "key": body.key, **head, "columns": columns, "rows": shown, "total": total,
            "eligible": len(rows) if you else None, "limit": LIMIT if body.by == "branch" else None,
            "you": you, "near": near if you else [], "notes": notes, **more}


# ---------- JEE Main ----------
def _jee_row(s, close, rnd, st, level, columns, tag=None):
    p, inst = rp.PROGS[s.prog], rp.INST[s.inst]
    own = rp.JAC_ROUNDS if s.jac else rp.JOSAA_ROUNDS
    cells = []
    for label in columns:
        i = own.index(label) if label in own else None
        if i is None or (s.jac and i >= 4):
            cells.append(_cell(label, None, na=True))  # this college has no such round (JAC Delhi: R1 to R4 only)
            continue
        value = s.closes[i] if i < len(s.closes) else None
        crl = i >= 5  # CSAB closes on CRL, even on a category or PwD seat
        state = None
        if st:
            lo, _, hi, _ = st.ranks_for(s.cat, s.pwd, s.jac or crl)
            state = _state(value, lo, hi)
            if crl and state == "in":
                state = "edge"  # CSAB only fills left-over seats: a seat from it is Borderline at best (best_paths)
        cells.append(_cell(label, value, state, **({"crl": True} if crl and rt._rank_type(s) != "CRL" else {})))
    pct, marks = rt._marks(rt._crl_needed(close, s, rnd))
    return {"id": f"jee-{s.prog}", "college": inst["short"], "place": f"{inst['city']}, {inst['state']}", "kind": inst["type"],
            "branch": p["name"] + (f" ({p['degree']})" if p["degree"] else ""), "path": rp.path_label(s),
            "rank_type": "CRL" if rnd >= 5 else rt._rank_type(s), "cells": cells, "final": {"label": own[rnd], "close": close},
            "prev": None if s.jac else {"label": rp.Y25_LABEL, "close": s.y25}, "seats": rt.JEE_SEATS.get(s.prog), "fee": None,
            "need": {"marks": marks[level], "pct": pct, "level": level}, "tag": tag}


def _jee(body: CutoffIn):
    if body.marks is not None and not -75 <= body.marks <= 300:
        raise HTTPException(422, "JEE Main marks −75 se 300 ke beech daalo.")
    if body.by == "college":
        if not body.key.isdigit() or int(body.key) not in rp.BY_INST:
            raise HTTPException(404, "College nahi mila.")
        inst = rp.INST[int(body.key)]
        seats, groups = rp.BY_INST[int(body.key)], []
        columns = JAC_COLUMNS if inst["body"] == "jac" else JEE_COLUMNS
        head = {"title": inst["short"], "name": inst["name"], "sub": f"{KIND[inst['type']]} · {inst['city']}, {inst['state']}", "kind": inst["type"]}
    else:
        if body.key not in rp.GROUPS:
            raise HTTPException(404, "Branch nahi mili.")
        seats, groups, columns = None, [body.key], JEE_COLUMNS
        head = {"title": body.key, "name": body.key, "sub": "JEE Main 2026 · NIT, IIIT, GFTI aur Delhi (JAC)", "kind": None}
    scored = body.rank is not None or body.percentile is not None or body.marks is not None
    profile = body.model_dump(include={"category", "female", "pwd", "state"})
    # Without a score only the seat rules are used; the placeholder percentile never reaches the answer.
    form = rp.Form(marks=body.marks, percentile=body.percentile if scored else 50, rank=body.rank, level=body.level, branches=groups, **profile)
    st = rp.Student(form)
    pool = rp.SEATS if seats is None else seats

    # Every program's easiest seat path open to this profile (the same pick as Target marks): the list without a score.
    easiest = {}
    for s in pool:
        if not s.jclose or (groups and rp.PROGS[s.prog]["group"] not in groups) or not st.eligible(s):
            continue
        need = rt._crl_needed(s.jclose, s, s.jround)
        if s.prog not in easiest or need > easiest[s.prog][0]:
            easiest[s.prog] = (need, s)
    order = sorted(easiest, key=rp.demand_key)
    notes = ["Closing rank = us round mein us seat par allot hui aakhri rank. Chhota number = mushkil seat.",
             "Har row ka seat raasta likha hai: aapki category, gender, PwD aur home state par khulne wala sabse aasaan raasta.",
             "JoSAA rounds (R1–R5) seat ke apne rank type par band hote hain; CSAB 1 aur CSAB 2 hamesha CRL par.",
             "≈ Marks = final closing tak pahunchne ke liye lagbhag kitne marks (aapka chuna hua paper type).", rp.NOTE]
    if columns is JAC_COLUMNS or any(rp.INST[rp.PROGS[p]["inst"]]["body"] == "jac" for p in order[:LIMIT]):
        notes.insert(3, "JAC Delhi (DTU, NSUT, IIIT-Delhi, IGDTUW): sirf R1–R4. Upgrade aur Spot round ki rank JAC ne publish nahi ki.")
    official = rp.OFFICIAL["jac"] if columns is JAC_COLUMNS else rp.OFFICIAL["josaa"]
    if not scored:
        rows = [_jee_row(easiest[p][1], easiest[p][1].jclose, easiest[p][1].jround, None, body.level, columns) for p in order]
        return _answer(body, head, columns, rows, len(order), None, [], notes, metric="rank", prev_label=None if columns is JAC_COLUMNS else rp.Y25_LABEL, official=official)

    best, miss = rp.best_paths(st, seats, every_miss=True)
    rows = []
    for p in sorted(best, key=rp.demand_key):
        _, _, tag, close, rnd, _, s = best[p]
        rows.append(_jee_row(s, close, rnd, st, body.level, columns, tag))
    near = []
    for p in sorted((p for p in miss if p not in best), key=lambda p: -miss[p][0])[:NEAR]:
        _, close, rnd, label, s = miss[p]
        near.append({**_jee_row(s, close, rnd, st, body.level, columns), "gap": rp.marks_gap(st, close, label, s)})
    res = rp.result_block(st)
    line = [res["summary"].split(" · ")[0] + (f" ({body.level.capitalize()} paper)" if st.from_marks else "")]
    if st.source != "percentile":
        line.append(f"{_pct(res['percentile'])} percentile")
    if st.source != "rank":
        line.append(f"rank {_rng(res['crl'])} (CRL)")
    you = {"source": st.source, "summary": res["summary"], "percentile": res["percentile"], "rank": {"label": "CRL", "range": res["crl"]},
           "cat_rank": res.get("cat_rank"), "pwd_rank": res.get("pwd_rank"), "check": res.get("check"), "line": " ≈ ".join(line)}
    if columns is JEE_COLUMNS:
        notes.append("CSAB 1 / CSAB 2 sirf bachi hui seats ke round hain: jo seat sirf wahan se milti hai wo hamesha Borderline hai, isliye uska box peela.")
    return _answer(body, head, columns, rows, len(order), you, near, notes + [ELIGIBLE], metric="rank",
                   prev_label=None if columns is JAC_COLUMNS else rp.Y25_LABEL, official=official)


def _rng(r):
    return rp.fmt(r[0]) if r[0] == r[1] else f"{rp.fmt(r[0])} – {rp.fmt(r[1])}"


def _pct(r):
    return f"{r[0]:.2f}" if r[0] == r[1] else f"{r[0]:.2f} – {r[1]:.2f}"


# ---------- COMEDK (GM seats) ----------
def _comedk_row(s, st=None):
    c = ck.INFO[s.code]
    cells = [_cell(label, close, _state(close, st.lo, st.hi) if st else None) for label, close in zip(ck.ROUNDS, s.rounds)]
    return {"id": f"{s.code}|{s.cc}", "college": c["short"], "place": c["city"], "kind": "COMEDK", "branch": ck._D["courses"].get(s.cc, s.cc),
            "path": "GM · All India", "rank_type": "COMEDK rank", "cells": cells, "final": {"label": ck.ROUNDS[s.rnd], "close": s.close},
            "prev": {"label": "2025 final", "close": s.y25}, "seats": s.gm, "fee": s.fee,
            "need": {"marks": next((m for m, r in enumerate(COMEDK_MID) if r <= s.close), ck.MAX_MARKS)}, "tag": st.judge(s.close) if st else None}


def _comedk(body: CutoffIn):
    if body.percentile is not None:
        raise HTTPException(422, "COMEDK mein percentile nahi chalta. Marks ya rank daalo.")
    if body.marks is not None and not 0 <= body.marks <= ck.MAX_MARKS:
        raise HTTPException(422, "COMEDK marks 0 se 180 ke beech daalo.")
    if body.rank is not None and body.rank > 200000:
        raise HTTPException(422, "COMEDK rank 1 se 2,00,000 ke beech daalo.")
    if body.by == "college":
        if body.key not in ck.BY_COLLEGE:
            raise HTTPException(404, "College nahi mila.")
        c = ck.INFO[body.key]
        seats, head = ck.BY_COLLEGE[body.key], {"title": c["short"], "name": c["name"], "sub": f"COMEDK · GM · {c['city'] or 'Karnataka'}", "kind": "COMEDK"}
    else:
        if body.key not in ck.GROUPS:
            raise HTTPException(404, "Branch nahi mili.")
        seats = [s for s in ck.SEATS if ck.group_of(s.cc) == body.key]
        head = {"title": body.key, "name": body.key, "sub": "COMEDK 2026 · GM (All India) seats", "kind": None}
    notes = ["Closing rank = us round mein GM seat par allot hui aakhri rank. Chhota number = mushkil seat.",
             "— = us round mein is seat par allotment nahi hua.", "≈ Marks = final closing tak pahunchne ke liye lagbhag kitne marks (180 mein se).", *ck.NOTES[:1]]
    more = {"metric": "rank", "prev_label": "2025 final", "official": ck.OFFICIAL}
    if body.rank is None and body.marks is None:
        return _answer(body, head, ck.ROUNDS, [_comedk_row(s) for s in seats], len(seats), None, [], notes, **more)
    st = ck.Student(ck.Form(marks=body.marks, rank=body.rank))
    rows = [_comedk_row(s, st) for s in seats if st.judge(s.close)]
    missed = sorted((s for s in seats if not st.judge(s.close)), key=lambda s: -s.close)[:NEAR]
    est = ck.estimate(body.marks) if st.from_marks else None
    you = {"source": "marks" if st.from_marks else "rank", "summary": ck.result_block(st, 0, 0)["summary"],
           "percentile": est["percentile"] if est else None, "rank": {"label": "COMEDK rank", "range": st.shown}, "cat_rank": None, "pwd_rank": None,
           "check": "COMEDK marks-rank table publish nahi karta, isliye marks se rank ek andaaza hai." if st.from_marks else None,
           "line": (f"{body.marks} / {ck.MAX_MARKS} marks ≈ rank {_rng(st.shown)} (beech ka andaaza {rp.fmt(st.mid)}) ≈ {_pct(est['percentile'])} percentile"
                    if est else f"Rank {rp.fmt(body.rank)} · GM (All India)")}
    near = [{**_comedk_row(s, st), "gap": st.gap(s.close)} for s in missed]
    return _answer(body, head, ck.ROUNDS, rows, len(seats), you, near, notes + [ELIGIBLE], **more)


# ---------- BITSAT (no rounds are published: five years of final cut-off scores) ----------
def _bitsat_row(r, score=None):
    tag = rb.chance(score, r["cutoff"]) if score is not None else None
    last = len(rb.YEARS) - 1
    state = None if score is None else "in" if tag in ("safe", "likely") else "edge" if tag else "out"
    cells = [_cell(str(y), h, state if i == last else None) for i, (y, h) in enumerate(zip(rb.YEARS, r["history"]))]
    return {"id": r["id"], "college": r["college"], "place": r["campus"], "kind": "BITS", "branch": r["program"], "path": "Sab categories, ek cutoff",
            "rank_type": f"score / {rb.MAX}", "cells": cells, "final": {"label": str(rb.YEARS[-1]), "close": r["cutoff"]},
            "prev": None, "seats": None, "fee": None, "need": {"marks": r["cutoff"]}, "tag": tag}


def _bitsat(body: CutoffIn):
    if body.percentile is not None or body.rank is not None:
        raise HTTPException(422, "BITSAT mein sirf score chalta hai (390 mein se).")
    if body.by == "college":
        rows_in = [r for r in rb.ROWS if r["campus"] == body.key]
        if not rows_in:
            raise HTTPException(404, "Campus nahi mila.")
        head = {"title": rows_in[0]["college"], "name": rows_in[0]["college"], "sub": f"BITSAT · {body.key} campus", "kind": "BITS"}
    else:
        rows_in = [r for r in rb.ROWS if r["id"].split("-", 1)[1] == body.key]
        if not rows_in:
            raise HTTPException(404, "Program nahi mila.")
        head = {"title": rb.NAMES[body.key], "name": rb.NAMES[body.key], "sub": "BITSAT · Pilani, Goa aur Hyderabad", "kind": None}
    columns = [str(y) for y in rb.YEARS]
    notes = ["BITS round-wise cutoff publish nahi karta. Yahan 5 saal ke final cutoff score hain; sabse naya saal hi aaj ka cutoff hai.",
             "Cutoff score: bada number = mushkil. Aapka score cutoff ke barabar ya zyada ho to seat milti hai.", *rb.NOTES[:2]]
    more = {"metric": "score", "prev_label": None, "official": rb.SOURCE}
    if body.marks is None:
        return _answer(body, head, columns, [_bitsat_row(r) for r in rows_in], len(rows_in), None, [], notes, **more)
    rows = [_bitsat_row(r, body.marks) for r in rows_in if rb.chance(body.marks, r["cutoff"])]
    missed = sorted((r for r in rows_in if not rb.chance(body.marks, r["cutoff"])), key=lambda r: r["cutoff"])[:NEAR]
    you = {"source": "marks", "summary": f"{body.marks} / {rb.MAX}", "percentile": None, "rank": None, "cat_rank": None, "pwd_rank": None, "check": None,
           "line": f"Score {body.marks} / {rb.MAX} · BITSAT mein percentile aur rank publish nahi hote, seedha cutoff score se milaya"}
    near = [{**_bitsat_row(r, body.marks), "gap": f"+{r['cutoff'] - body.marks} marks aur"} for r in missed]
    return _answer(body, head, columns, rows, len(rows_in), you, near,
                   notes + ["Eligible = Safe (cutoff se 10+ upar), Likely (cutoff ya upar) aur Borderline (cutoff se 5 tak neeche, pakka nahi)."], **more)


def cutoff(body: CutoffIn):
    return {"jee": _jee, "comedk": _comedk, "bitsat": _bitsat}[body.exam](body)


# What students type for a branch; the picker also searches every course name inside the group.
SHORT = {"Computer Science": "CSE CS", "AI & Data Science": "AI ML DS AIML AIDS", "Information Technology": "IT", "Mathematics & Computing": "MnC MNC",
         "Electronics & Communication": "ECE EC ENTC VLSI", "Electrical": "EE EEE", "Instrumentation": "EIE ICE", "Mechanical": "ME Mech", "Civil": "CE",
         "Chemical": "CH ChE", "Metallurgy & Materials": "MME Meta", "Production & Industrial": "PIE", "Aerospace": "AE Aero", "Biotechnology": "BT Biotech",
         "Cyber Security & IoT": "Cyber IoT", "Information Science & IT": "ISE IT"}


def _find(group, names):
    return " ".join([SHORT.get(group, ""), *dict.fromkeys(names)]).strip()


def _options():
    """Everything the two pickers need, per exam. `key` goes back to POST /rank/cutoff exactly as it is."""
    jee_progs = {}
    for s in rp.SEATS:
        if s.jclose:
            jee_progs.setdefault(rp.PROGS[s.prog]["group"], set()).add(s.prog)
    jee_colleges = sorted((i for i in rp.BY_INST), key=lambda i: (rp.INST[i]["type"] != "NIT", rp.INST[i]["short"]))
    comedk_groups = {g: [s for s in ck.SEATS if ck.group_of(s.cc) == g] for g in ck.GROUPS}
    programs = {}
    for r in rb.ROWS:  # already highest cut-off first
        programs.setdefault(r["id"].split("-", 1)[1], []).append(r["campus"])
    return {
        "limit": LIMIT,
        "jee": {"name": "JEE Main", "score": ["marks", "percentile", "rank"], "marks": [-75, 300], "levels": True, "profile": True,
                "colleges": [{"key": str(i), "title": rp.INST[i]["short"], "sub": f"{KIND[rp.INST[i]['type']]} · {rp.INST[i]['city']}, {rp.INST[i]['state']}",
                              "find": rp.INST[i]["name"], "kind": rp.INST[i]["type"]} for i in jee_colleges],
                "branches": [{"key": g, "title": g, "sub": f"{len(jee_progs[g])} college-branch · {len({rp.PROGS[p]['inst'] for p in jee_progs[g]})} colleges",
                              "find": _find(g, (rp.PROGS[p]["name"] for p in sorted(jee_progs[g])))} for g in rp.GROUPS if g in jee_progs]},
        "comedk": {"name": "COMEDK", "score": ["marks", "rank"], "marks": [0, ck.MAX_MARKS], "levels": False, "profile": False,
                   "colleges": [{"key": code, "title": ck.INFO[code]["short"], "sub": ck.INFO[code]["city"] or "Karnataka", "find": ck.INFO[code]["name"], "kind": "COMEDK"}
                                for code in sorted(ck.BY_COLLEGE, key=lambda c: ck.BY_COLLEGE[c][0].demand)],
                   "branches": [{"key": g, "title": g, "sub": f"{len(v)} college-course · {len({s.code for s in v})} colleges",
                                 "find": _find(g, (ck._D["courses"].get(s.cc, s.cc) for s in v))} for g, v in comedk_groups.items() if v]},
        "bitsat": {"name": "BITSAT", "score": ["marks"], "marks": [-130, rb.MAX], "levels": False, "profile": False,
                   "colleges": [{"key": c, "title": rb.COLLEGE[c], "sub": f"{sum(r['campus'] == c for r in rb.ROWS)} programs", "kind": "BITS"}
                                for c in ("Pilani", "Goa", "Hyderabad")],
                   "branches": [{"key": k, "title": rb.NAMES[k], "sub": " · ".join(c for c in ("Pilani", "Goa", "Hyderabad") if c in campuses)}
                                for k, campuses in programs.items()]},
    }


OPTIONS = _options()  # the data never changes while the server runs


def options():
    return OPTIONS


def register(router):
    router.get("/cutoff/options")(options)
    router.post("/cutoff")(cutoff)
