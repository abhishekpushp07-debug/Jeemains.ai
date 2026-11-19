"""What a round is played on: up to 5 picks, each a whole subject or one chapter. "PCM Mixed" is the three whole subjects."""
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

ORDER = ("Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning")
SHORT = {"Physics": "Physics", "Chemistry": "Chemistry", "Mathematics": "Maths", "English": "English", "Logical Reasoning": "Reasoning"}
MAX_PICKS = 5
PCM = [{"subject": s, "chapter": None} for s in ORDER[:3]]
Subject = Literal["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning"]
CARD_COUNTS = (30, 50, 100)  # what a student can choose for one round
CARD_SECONDS = 20  # rule R1: 20 seconds per card in every mode


class Pick(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Subject
    chapter: Optional[str] = Field(default=None, max_length=80)


def normalise(picks=None, subject=None, chapter=None) -> list:
    """One tidy list: no repeats, a whole subject swallows its own chapters, always in the same order."""
    get = lambda p, k: p.get(k) if isinstance(p, dict) else getattr(p, k)  # noqa: E731
    rows = [{"subject": get(p, "subject"), "chapter": (get(p, "chapter") or "").strip() or None} for p in picks] if picks else [{"subject": subject or "Physics", "chapter": chapter or None}]
    whole = {r["subject"] for r in rows if not r["chapter"]}
    out = []
    for r in rows:
        if not (r["chapter"] and r["subject"] in whole) and r not in out:
            out.append(r)
    out.sort(key=lambda r: (ORDER.index(r["subject"]) if r["subject"] in ORDER else 9, r["chapter"] or ""))
    if len(out) > MAX_PICKS:
        raise HTTPException(400, f"Pick up to {MAX_PICKS} subjects or chapters.")
    return out


def label_of(picks: list) -> str:
    whole = [SHORT.get(p["subject"], p["subject"]) for p in picks if not p["chapter"]]
    chapters = [p["chapter"] for p in picks if p["chapter"]]
    if not chapters:
        return "PCM Mixed" if whole == ["Physics", "Chemistry", "Maths"] else "Mixed " + " + ".join(whole)
    if not whole:
        return chapters[0] if len(chapters) == 1 else f"{chapters[0]} +{len(chapters) - 1} more"
    return f"Mixed {whole[0]} +{len(picks) - 1} more"


def scope_fields(picks: list) -> dict:
    """The fields every sprint, match, room and cup stores. `subject` and `chapter` stay for older readers."""
    return {"picks": picks, "label": label_of(picks), "subject": picks[0]["subject"], "chapter": picks[0]["chapter"] if len(picks) == 1 else None,
            "scope_key": "|".join(f"{p['subject']}:{p['chapter'] or '*'}" for p in picks)}


def scope_of(doc: dict) -> list:
    return doc.get("picks") or [{"subject": doc["subject"], "chapter": doc.get("chapter")}]


def stored_scope(doc: dict) -> dict:
    """The scope fields of a stored room or match (older ones have only a subject and a chapter)."""
    return scope_fields(scope_of(doc))


def label_for(doc: dict) -> str:
    return doc.get("label") or label_of(scope_of(doc))


def scope_view(doc: dict) -> dict:
    return {"picks": scope_of(doc), "label": label_for(doc)}
