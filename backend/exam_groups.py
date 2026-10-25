"""Exam boundaries shared by the arena, content sync and portable NEET bank."""
from pathlib import Path
from typing import Literal

from fastapi import HTTPException

Exam = Literal["JEE", "NEET"]
SUBJECTS = {"JEE": ["Physics", "Chemistry", "Mathematics"], "NEET": ["Physics", "Chemistry", "Biology"]}
NEET_ROOT = Path(__file__).resolve().parents[1] / "neetlive"


def resolve_exam(exam, subject):
    # Backward-compatible old clients: Biology was always NEET; other legacy play was JEE.
    exam = exam or ("NEET" if subject == "Biology" else "JEE")
    if subject not in SUBJECTS[exam]:
        raise HTTPException(422, f"{subject} is not available in {exam}.")
    return exam


def exam_filter(exam):
    return {"exam": exam} if exam else {}