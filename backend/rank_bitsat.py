"""JEELIVE.AI Rank: BITSAT score -> BITS Pilani / Goa / Hyderabad programs, from the official 2022-2026 final cut-offs.

BITSAT has no category quota, so one cut-off per program decides everything. Data: rank_data/bitsat_cutoffs.json.
"""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

_B = json.load(open(Path(__file__).parent / "rank_data" / "bitsat_cutoffs.json"))
SOURCE, MAX, YEARS, NAMES = _B["source"], _B["max"], _B["years"], _B["programs"]
COLLEGE = {"Pilani": "BITS Pilani", "Goa": "BITS Goa", "Hyderabad": "BITS Hyderabad"}


def _degree(name):
    return "BE" if name.startswith("B.E.") else "MSc" if name.startswith("M.Sc.") else "BPharm"


ROWS = sorted(({"id": f"{c}-{k}", "campus": c, "college": COLLEGE[c], "program": NAMES[k], "degree": _degree(NAMES[k]),
                "history": h, "cutoff": h[-1], "last": h[-2]}
               for c, progs in _B["campus"].items() for k, h in progs.items()), key=lambda r: (-r["cutoff"], r["id"]))
NOTES = ["BITSAT mein category reservation nahi hai, sabke liye ek hi cutoff.",
         "Cutoff har saal 10-20 marks upar-neeche hota hai (2024 se 2025 mein lagbhag 20 gira, 2026 mein phir chadha).",
         "Same score par seats kam padein to PCM marks se tie todi jaati hai."]


class BitsatIn(BaseModel):
    score: int = Field(ge=-130, le=MAX)
    campus: Literal["all", "Pilani", "Goa", "Hyderabad"] = "all"
    degree: Literal["all", "BE", "MSc", "BPharm"] = "all"


def chance(score, cutoff):
    d = score - cutoff
    return "safe" if d >= 10 else "likely" if d >= 0 else "borderline" if d >= -5 else None


def predict(body: BitsatIn):
    s = body.score
    rows = [r for r in ROWS if body.campus in ("all", r["campus"]) and body.degree in ("all", r["degree"])]
    items = [{**r, "tag": chance(s, r["cutoff"]), "gap": max(0, r["cutoff"] - s)} for r in rows]
    # The card is about the student, so it always looks at every campus and degree; the filters only shape the list.
    every = [r for r in ROWS if s >= r["cutoff"]]
    best = every[0] if every else None
    target = min((r for r in ROWS if r["cutoff"] > s), key=lambda r: (r["cutoff"] - s, -r["cutoff"]), default=None)
    return {
        "result": {
            "score": s, "max": MAX, "cleared": sum(1 for i in items if i["gap"] == 0), "total": len(items),
            "cleared_all": len(every), "total_all": len(ROWS),
            "best": {k: best[k] for k in ("college", "program", "cutoff")} if best else None,
            "target": {**{k: target[k] for k in ("college", "program", "cutoff")}, "gap": target["cutoff"] - s} if target else None,
        },
        "items": [i for i in items if i["tag"]],
        "near": [i for i in items if not i["tag"] and i["gap"] <= 20],
        "rest": [i for i in items if not i["tag"] and i["gap"] > 20],
        "years": YEARS, "notes": NOTES, "source": SOURCE,
    }
