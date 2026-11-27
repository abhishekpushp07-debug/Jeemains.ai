"""Class 11 / Class 12 (27 Nov 2026): the list that says which class a chapter belongs to.

What must hold:
  * the app's copy and the server's copy of the list are the same file, byte for byte;
  * every Physics, Chemistry and Maths chapter of Rapid Fire has a class, and so has every JEE Main chapter-wise test the
    website had on 27 Nov 2026 except the one that belongs to no class ("Miscellaneous (beyond the current syllabus)");
  * a chapter is found by its name however it is numbered or punctuated;
  * GET /api/app/classes gives the list, and GET /api/app/switches says its number.

Nothing is written anywhere: the catalog and the two doors are read, the rest is the files."""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import class_levels

BASE = "http://localhost:8001/api"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SERVER_COPY = os.path.join(ROOT, "backend", "class_levels.json")
APP_COPY = os.path.join(ROOT, "frontend", "src", "classLevels.json")
WEBSITE = os.path.join(ROOT, "tests", "data", "website_chapters_27nov2026.json")  # the chapter-wise lists as the website gave them
PCM = ("Physics", "Chemistry", "Mathematics")
JEE = "jee-main"


def test_the_apps_copy_is_the_servers_copy():
    with open(SERVER_COPY, "rb") as a, open(APP_COPY, "rb") as b:
        assert a.read() == b.read()


def test_the_list_holds_only_classes_and_plain_names():
    book = class_levels.BOOK
    assert isinstance(book["version"], int) and book["version"] >= 1 and class_levels.VERSION == book["version"]
    assert set(book["exams"][JEE]) == set(PCM)
    for subjects in book["exams"].values():
        for names in subjects.values():
            assert names and all(level in (11, 12) for level in names.values())
            assert all(name == class_levels.key(name) for name in names), "a name in the list must be written the way key() writes it"


def test_a_chapter_is_found_however_it_is_written():
    key, level = class_levels.key, class_levels.level_of
    assert key("01 Units, Dimensions and Errors") == key("1. units dimensions and errors") == key("  Units, Dimensions   and Errors ") == "units dimensions and errors"
    assert key("Centre of Mass & Collisions") == "centre of mass and collisions" and key("d- and f-Block Elements") == "d and f block elements"
    assert key("3D Geometry") == "3d geometry", "a name that begins with a digit keeps it; only a number standing alone in front goes"
    assert level(JEE, "Physics", "16 Electrostatics") == 12 and level(JEE, "Physics", "Kinematics") == 11
    assert level(JEE, "Chemistry", "Thermodynamics") is None, "a Physics chapter's name is not looked for in Chemistry"
    assert level(JEE, "Physics", "A chapter nobody has heard of") is None and level("bitsat", "Physics", "Kinematics") is None
    assert level(JEE, "Logical Reasoning", "Syllogisms") is None


def test_every_rapid_fire_chapter_of_physics_chemistry_and_maths_has_a_class():
    subjects = {s["name"]: s["chapters"] for s in requests.get(f"{BASE}/rf/catalog?exam=JEE", timeout=30).json()["subjects"]}
    seen = {}
    for name in PCM:
        levels = [class_levels.level_of(JEE, name, c["name"]) for c in subjects[name]]
        assert None not in levels, [c["name"] for c, level in zip(subjects[name], levels) if level is None]
        seen[name] = (levels.count(11), levels.count(12))
    assert all(a and b for a, b in seen.values()), seen
    for name in ("English", "Logical Reasoning"):  # BITSAT's own subjects are not split into classes
        assert all(class_levels.level_of(JEE, name, c["name"]) is None for c in subjects.get(name, []))


def test_every_chapter_wise_test_of_the_website_has_a_class():
    with open(WEBSITE, encoding="utf-8") as f:
        lists = json.load(f)[JEE]
    counts, without = {}, []
    for name in PCM:
        levels = [class_levels.level_of(JEE, name, row["title"]) for row in lists[name]]
        counts[name] = (levels.count(11), levels.count(12))
        without += [row["title"] for row, level in zip(lists[name], levels) if level is None]
    assert counts == {"Physics": (15, 15), "Chemistry": (11, 12), "Mathematics": (17, 10)}, counts
    assert without == ["24 Miscellaneous (beyond the current syllabus)"], without


def test_the_two_doors():
    answer = requests.get(f"{BASE}/app/classes", timeout=30)
    assert answer.status_code == 200 and answer.json() == class_levels.BOOK
    assert "max-age" in answer.headers.get("cache-control", "")
    switches = requests.get(f"{BASE}/app/switches", timeout=30).json()
    assert switches["classes"] == class_levels.VERSION
    assert {"pictures", "matched"} <= set(switches), "the switches that were there are still there"
