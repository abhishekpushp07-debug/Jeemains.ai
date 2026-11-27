"""Which class a chapter belongs to: Class 11 or Class 12 (GET /api/app/classes).

The list is class_levels.json beside this file: exam -> subject -> chapter name -> 11 or 12. A chapter is looked up by
its name written plainly (`key`): small letters, no number in front, "&" as "and", no punctuation. Both spellings are in
the list: the website's chapter-wise tests ("01 Units, Dimensions and Errors") and Rapid Fire's chapters
("Units & Measurements"). A chapter that is not in the list has no class: the app shows it after the others and never
hides it.

The app carries the same list (frontend/src/classLevels.json; backend/tests/test_class_levels.py keeps the two
identical), so its screens are drawn without waiting for this server. To move a chapter to the other class, or to add an
exam, without a new app build: change class_levels.json here, raise its "version" by one and publish. GET
/api/app/switches then says the new number, and every app asks for this list once and uses it from then on."""
import json
import os
import re

from fastapi import APIRouter
from starlette.responses import JSONResponse

with open(os.path.join(os.path.dirname(__file__), "class_levels.json"), encoding="utf-8") as _file:
    BOOK = json.load(_file)
VERSION = BOOK["version"]
# The address carries the version (?v=3), so a copy kept on the way is never an older list.
CACHE = {"Cache-Control": "public, max-age=86400"}

router = APIRouter()


def key(title) -> str:
    """A chapter's name as the list knows it. The app's `classKey` (frontend/src/classLevel.ts) does the same."""
    plain = re.sub(r"^\s*\d+[.)]?\s+", "", str(title).lower()).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def level_of(exam: str, subject: str, title) -> int | None:
    """11, 12, or None for a chapter the list does not know."""
    return BOOK["exams"].get(exam, {}).get(subject, {}).get(key(title))


@router.get("/app/classes")
async def classes():
    return JSONResponse(BOOK, headers=CACHE)
