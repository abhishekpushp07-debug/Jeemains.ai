"""Student Choice: GET /api/choice/bank (the chapters = the website's JEE Main chapter-wise tests), GET
/api/choice/chapters/<id>, and Matched's real paper (paper_id, qid, the website copy). The shaping is checked on plain
dicts; the routes are only read. Nothing is written to any collection
(the signed-in check uses conftest.py's throw-away grant, removed when the run ends)."""
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import choice  # noqa: E402
import matched  # noqa: E402

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
CID, QID = "4b4ff9a5-85ba-5325-83cd-60f2994acc57", "9d8575c5-61fc-57a8-8457-cdddc8b28ebf"


def chapter(cid=CID, **change):
    return {"id": cid, "number": 1, "title": "Units, Dimensions and Errors", "count": 68, "mcq": 64, "integer": 4, **change}


def test_the_bank_keeps_three_subjects_in_order_and_the_owners_rules():
    bank = choice.shape_bank({"exam": "JEE Main", "secret": 1, "subjects": [
        {"name": "Mathematics", "chapters": [chapter("m-000001", title="Sets and Relations", count=38, mcq=31, integer=7)]},
        {"name": "Biology", "chapters": [chapter("b-000001")]},
        {"name": "Physics", "chapters": [chapter(), chapter(), chapter("p-000002", title="", count=5), chapter("p-000003", count=0), {"id": "x"}, "junk",
                                         chapter("p-000004", number="2", mcq=999)]}]})
    assert set(bank) == {"ready", "sample", "exam", "pick", "random", "max_questions", "max_per_subject", "minutes", "marks", "subjects"}
    assert bank["ready"] is True and bank["sample"] is False and bank["exam"] == "JEE Main"
    assert [s["name"] for s in bank["subjects"]] == ["Physics", "Mathematics"]  # no Chemistry chapter: not shown; Biology never
    physics = bank["subjects"][0]["chapters"]
    # A chapter twice, one without a name, one without questions and junk are left out.
    assert [c["id"] for c in physics] == [CID, "p-000004"] and set(physics[0]) == {"id", "n", "title", "count", "mcq", "integer", "test"}
    assert physics[0] == {"id": CID, "n": 1, "title": "Units, Dimensions and Errors", "count": 68, "mcq": 64, "integer": 4, "test": None}
    assert physics[1]["n"] is None and physics[1]["mcq"] == 0
    # The owner's rules when the website says nothing: 75 questions, +4 / -1, 60 + 40 + 80 minutes for 25 + 25 + 25.
    assert bank["max_questions"] == 75 and bank["max_per_subject"] is None and bank["marks"] == {"correct": 4, "wrong": -1}
    assert bank["minutes"] == {"Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2}
    for bad in (None, [], {}, {"subjects": []}, {"subjects": [{"name": "Physics", "chapters": []}]}):
        assert choice.shape_bank(bad) is None


def test_the_website_may_lower_the_top_but_never_raise_it():
    one = {"subjects": [{"name": "Physics", "chapters": [chapter()]}]}
    assert choice.shape_bank({**one, "max_questions": 30, "max_per_subject": 25})["max_questions"] == 30
    assert choice.shape_bank({**one, "max_questions": 30, "max_per_subject": 25})["max_per_subject"] == 25
    for wrong in (90, 0, -5, "75", True, None, 75.0):
        assert choice.shape_bank({**one, "max_questions": wrong})["max_questions"] == 75
    per = choice.shape_bank({**one, "minutes_per_question": {"Physics": 2, "Chemistry": "1.6", "Mathematics": 99}})["minutes"]
    assert per == {"Physics": 2.0, "Chemistry": 1.6, "Mathematics": 3.2}


def row(n=1, **change):
    """A chapter test as the website's chapter-wise list gives it (copied from the live list, 26 Nov 2026)."""
    return {"id": CID, "exam": "JEE Main", "status": "published", "test_kind": "chapter", "live_enabled": True, "chapter_number": n, "chapter_subject": "Physics",
            "title": f"{n:02d} Units, Dimensions and Errors", "count": 68, "approved_count": 68, "types": {"mcq": 64, "integer": 4}, "maximum": 272.0,
            "rules": {"minutes": 60.0, "correct": 4.0, "wrong": -1.0, "skipped": 0}, "attempt": {"id": "someone's own attempt", "status": "completed"}, "saved": True, **change}


def test_the_chapters_are_the_websites_chapter_wise_tests():
    pages = [{"pages": 2, "items": [row(), row(2, id="p-000002", title="02 Kinematics", count=50, maximum=200.0, types={"mcq": 50}),
                                    row(3, id="p-hidden1", status="draft"), row(4, id="p-hidden2", live_enabled=False), row(5, id="m-000001", chapter_subject="Mathematics"),
                                    row(6, id="p-mock01", test_kind="mock"), "junk", None]},
             {"pages": 2, "items": [row(13, id="p-000013", title="13 13 Reasons", rules={"correct": 4, "wrong": -1}), row(14, id="p-000014", title="Oscillations", maximum=None)]},
             "junk"]
    bank = choice.shape_bank({"subjects": [{"name": "Physics", "chapters": choice.chapter_tests("Physics", pages)}]}, own=False)
    chapters = bank["subjects"][0]["chapters"]
    # Hidden ones, another subject's, another kind of paper and junk are left out; the order is the website's.
    assert [c["id"] for c in chapters] == [CID, "p-000002", "p-000013", "p-000014"]
    # The chapter's id is the test's id; its title loses the number it starts with; nothing of any student comes along.
    assert chapters[0] == {"id": CID, "n": 1, "title": "Units, Dimensions and Errors", "count": 68, "mcq": 64, "integer": 4,
                           "test": {"page": 1, "minutes": 60, "correct": 4, "wrong": -1, "marks": 272}}
    assert chapters[1]["title"] == "Kinematics" and chapters[1]["integer"] == 0 and chapters[1]["test"]["marks"] == 200
    # The page the test is listed on is kept (the app reads the student's own attempt from it); no time = untimed.
    assert chapters[2]["title"] == "13 Reasons" and chapters[2]["test"] == {"page": 2, "minutes": None, "correct": 4, "wrong": -1, "marks": 272}
    assert chapters[3]["title"] == "Oscillations" and chapters[3]["test"] is None  # its marks are not known: listed, not offered as a test
    # The website cannot make a paper yet: neither way is open, and the owner's rules stand.
    assert bank["pick"] is False and bank["random"] is False and bank["sample"] is False and bank["max_questions"] == 75
    assert choice.chapter_tests("Physics", []) == [] and choice.chapter_tests("Physics", [{"items": None}, {}]) == []
    assert choice.shape_bank({"subjects": [{"name": "Physics", "chapters": []}]}, own=False) is None


def test_making_a_paper_opens_only_when_the_website_says_so():
    tests = {"subjects": [{"name": "Physics", "chapters": choice.chapter_tests("Physics", [{"items": [row()]}])}]}
    # The chapter-wise tests as the chapters: a way opens when the website's Student Choice door says yes, each on its own.
    for said, pick, random in (({}, False, False), ({"pick": True}, True, False), ({"random": True}, False, True), ({"pick": True, "random": True}, True, True),
                               ({"pick": "yes", "random": 1}, False, False)):
        bank = choice.shape_bank({**said, **tests}, own=False)
        assert (bank["pick"], bank["random"]) == (pick, random)
    # The website listing the chapters itself (the first note's door): both are open unless it says no.
    own = {"subjects": [{"name": "Physics", "chapters": [chapter()]}]}
    assert (choice.shape_bank(own)["pick"], choice.shape_bank(own)["random"]) == (True, True)
    assert (choice.shape_bank({**own, "pick": False})["pick"], choice.shape_bank({**own, "random": False})["random"]) == (False, False)
    # A test's time follows the website whatever it sets (the owner's ratio gives 164 minutes for 68 Physics questions):
    # whole minutes, never more than the website gives; no time or a senseless one = no time limit.
    timed = lambda m: choice.shape_test({"page": 1, "maximum": 272, "correct": 4, "wrong": -1, "minutes": m})["minutes"]
    assert [timed(m) for m in (60, 60.0, 164, 163.2, 276, 4, 0.5, 0, None, "60", True, 1001)] == [60, 60, 164, 163, 276, 4, None, None, None, None, None, None]
    assert choice.shape_test(None) is None and choice.shape_test({"page": 0, "maximum": 272, "correct": 4, "wrong": -1}) is None
    assert choice.shape_test({"page": 1, "maximum": 272, "correct": 4, "wrong": 1}) is None and choice.shape_test({"page": 1, "maximum": 272.5, "correct": 4, "wrong": -1}) is None


def test_time_is_given_by_subject_and_rounded_up():
    assert choice.minutes_for({"Physics": 25, "Chemistry": 25, "Mathematics": 25}) == 180
    assert choice.minutes_for({"Mathematics": 25}) == 80 and choice.minutes_for({"Physics": 25}) == 60 and choice.minutes_for({"Chemistry": 25}) == 40
    assert choice.minutes_for({"Physics": 10, "Chemistry": 10, "Mathematics": 10}) == 72
    assert choice.minutes_for({"Mathematics": 1}) == 4 and choice.minutes_for({"Chemistry": 1}) == 2 and choice.minutes_for({"Physics": 5}) == 12
    assert choice.minutes_for({}) == 0
    # A whole chapter test: the same ratio, three hours at most (86 Maths questions would bring 276 minutes).
    assert choice.chapter_test_minutes("Mathematics", 86) == 180 and choice.chapter_test_minutes("Physics", 76) == 180
    assert choice.chapter_test_minutes("Physics", 75) == 180 and choice.chapter_test_minutes("Physics", 74) == 178
    assert choice.chapter_test_minutes("Chemistry", 103) == 165 and choice.chapter_test_minutes("Chemistry", 2) == 4
    # A made paper is not cut: 75 Maths questions bring their 240 minutes.
    assert choice.minutes_for({"Mathematics": 75}) == 240


def test_a_question_goes_out_without_options_answer_or_solution():
    q = choice.shape_question({"id": QID, "number": 1, "type": "mcq", "text": "", "answer": "C", "options": {"A": "x"}, "solution": "s", "c_refs": [1],
                               "stem": [{"url": "https://cdn.example/q.webp", "w": 506.5, "h": 47}, "https://cdn.example/b.webp", {"url": "http://cdn.example/no.png"},
                                        {"url": "https://cdn.example/half.webp", "w": 10}, {"url": "javascript:alert(1)"}]})
    assert set(q) == {"id", "n", "type", "text", "stem"} and q["id"] == QID and q["n"] == 1 and q["type"] == "mcq"
    assert q["stem"] == [{"url": "https://cdn.example/q.webp", "w": 506.5, "h": 47.0}, {"url": "https://cdn.example/b.webp", "w": None, "h": None},
                         {"url": "https://cdn.example/half.webp", "w": None, "h": None}]
    assert choice.shape_question({"id": QID, "type": "numeric", "text": "A typed question $x^2$"})["type"] == "mcq"
    assert choice.shape_question({"id": QID, "type": "integer", "text": "t"})["type"] == "integer"
    for bad in (None, "x", {}, {"id": QID}, {"id": "no", "text": "t"}, {"id": QID, "text": "  ", "stem": []}):
        assert choice.shape_question(bad) is None


def test_a_chapter_joins_its_pages_and_drops_repeats():
    rows = [{"id": f"q-{i:05d}", "number": i, "text": f"Question {i}"} for i in range(1, 6)]
    pages = [{"chapter": {"id": CID, "title": "Kinematics", "subject": "Physics"}, "pages": 2, "items": rows[:3]}, {"items": rows[2:] + [{"id": "bad"}]}]
    c = choice.shape_chapter(CID, pages)
    assert (c["id"], c["title"], c["subject"], c["total"]) == (CID, "Kinematics", "Physics", 5) and [q["n"] for q in c["items"]] == [1, 2, 3, 4, 5]
    assert choice.shape_chapter(CID, [{"chapter": {"subject": "Biology"}, "items": rows[:1]}])["subject"] == ""
    assert choice.shape_chapter(CID, []) is None and choice.shape_chapter(CID, [{"items": []}]) is None


def test_matched_names_the_real_paper_only_when_ours_are_in_it():
    def item(qid=None):
        ours = {"text": "Ours", "options": ["a", "b"], "correct": 1, "source": "AITS Day 12 · Q 7"}
        return {"n": 1, "subject": "Physics", "jee": {"text": "JEE"}, "ours": [{**ours, **({"question_id": qid} if qid else {})}]}
    s = matched.shape_shift({"_id": "2027-01-25-s1", "paper_id": "paper-0001", "items": [item("q-000001"), item("q-000002"), item("q-000001"), item()]})
    assert s["paper_id"] == "paper-0001" and s["paper_questions"] == 2 and [i["ours"][0]["qid"] for i in s["items"]] == ["q-000001", "q-000002", "q-000001", ""]
    # A paper without any of ours named in it, or a bad id, is not offered.
    for doc in ({"paper_id": "paper-0001", "items": [item()]}, {"paper_id": "no", "items": [item("q-000001")]}, {"paper_id": 5, "items": [item("q-000001")]},
                {"items": [item("q-000001")]}):
        s = matched.shape_shift({"_id": "2027-01-25-s1", **doc})
        assert s["paper_id"] == "" and s["paper_questions"] == 0


def test_the_website_copy_reads_only_what_changed():
    rows = matched.site_rows({"shifts": [{"id": "2027-01-25-s1", "updated_at": 5}, "2027-01-25-s2", {"id": "nope"}, {"id": "2027-01-26-s1", "updated_at": "x"}, 7]})
    assert rows == {"2027-01-25-s1": 5, "2027-01-25-s2": None, "2027-01-26-s1": None}
    assert matched.site_rows(None) == {} and matched.site_rows({"shifts": "x"}) == {}
    have = {"published": True, "updated_at": 5, "synced_at": 1000}
    assert not matched.stale(have, 5, 1100) and matched.stale(have, 6, 1100)  # the website changed it
    assert matched.stale(None, 5, 1100) and matched.stale({**have, "published": False}, 5, 1100)  # new here, or hidden here
    assert not matched.stale(have, None, 1500) and matched.stale(have, None, 1601)  # no stamp: read again after ten minutes
    assert matched.site_data({"data": {"a": 1}, "error": None, "meta": {}}) == {"a": 1} and matched.site_data({"a": 1}) == {"a": 1}


def test_the_bank_is_for_signed_in_students_only():
    for path in ("/choice/bank", f"/choice/chapters/{CID}"):
        assert requests.get(f"{BASE}{path}", timeout=40).status_code == 401
        assert requests.get(f"{BASE}{path}", headers={"Authorization": "Bearer nobody"}, timeout=40).status_code == 401


def test_routes_answer_a_signed_in_student():
    # conftest.py swaps this header for a real short-lived grant of a throw-away player (no website session behind it).
    me = {"X-RF-User": "TEST-choice"}
    r = requests.get(f"{BASE}/choice/bank", headers=me, timeout=60)
    # 401 + "website_session" = the website wants a real session (the app then renews it and asks again). 200 = a real
    # student's read is being kept (the bank is the same for everyone), or the website's lists are open.
    assert r.status_code in (200, 401) and "public" not in r.headers.get("cache-control", "")
    if r.status_code == 401:
        assert r.json()["code"] == "website_session"
        return
    bank = r.json()
    assert isinstance(bank["ready"], bool)
    print("choice bank on this server: ready =", bank["ready"], "| sample =", bank.get("sample"), "| pick =", bank.get("pick"), "| random =", bank.get("random"))  # `pytest -s`
    if not bank["ready"]:
        assert bank == {"ready": False}  # no chapter to choose from: nothing else is sent
    if bank["ready"]:
        assert bank["max_questions"] <= 75 and bank["marks"] == {"correct": 4, "wrong": -1} and bank["subjects"]
        assert isinstance(bank["pick"], bool) and isinstance(bank["random"], bool)
        assert bank["minutes"] == {"Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2} or bank["sample"] is False  # the owner's 60 / 40 / 80 for 25 each
        first = bank["subjects"][0]["chapters"][0]
        assert set(first) == {"id", "n", "title", "count", "mcq", "integer", "test"}
        if not bank["sample"] and not bank["pick"]:  # the chapters are the chapter-wise tests: each can be taken as it is
            assert all(c["test"] and c["test"]["page"] >= 1 and c["test"]["marks"] == c["count"] * c["test"]["correct"] for s in bank["subjects"] for c in s["chapters"])
        c = requests.get(f"{BASE}/choice/chapters/{first['id']}", headers=me, timeout=40)
        # The questions of a chapter need the website's door: 404 until it has one (or 401 for this player without a session).
        assert c.status_code in (200, 404, 401)
        if c.status_code == 200:
            assert c.json()["total"] == len(c.json()["items"]) > 0 and all(set(q) == {"id", "n", "type", "text", "stem"} for q in c.json()["items"])
        assert requests.get(f"{BASE}/choice/chapters/no-such-chapter-000", headers=me, timeout=40).status_code in (404, 401)
    assert requests.get(f"{BASE}/choice/chapters/x", headers=me, timeout=40).status_code == 422


def test_matched_paper_route_is_public_and_read_only():
    assert requests.get(f"{BASE}/matched/paper/no-such-paper-000", timeout=40).status_code == 404
    assert requests.get(f"{BASE}/matched/paper/x", timeout=40).status_code == 422
