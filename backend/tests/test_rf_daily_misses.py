"""All India Rapid: the result screen's Misfires tab (GET /rf/daily/misses).
A finished run's cards that were not answered right, with the key; nothing before the run is finished, and never a card the
student was not shown (all of India plays the same cards today). TEST-* players only: they never touch the real board."""
import os
import time
import uuid

import requests
from pymongo import MongoClient

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
s = requests.Session()
FIELDS = {"i", "subject", "chapter", "prompt", "options", "outcome", "choice", "answer", "explain", "formula"}


def user():
    return {"X-RF-User": f"TEST-miss-{uuid.uuid4().hex[:10]}"}


def cleanup(*hs):
    for h in hs:
        uid = h["X-RF-User"]
        assert uid.startswith("TEST-miss-")  # only the throw-away players this file made; never a real student's rows
        db.rf_daily_plays.delete_many({"uid": uid})
        db.rf_profiles.delete_many({"uid": uid})
        db.rf_awards.delete_many({"uid": uid})
        db.rf_learning_events.delete_many({"uid": uid})


def key_of(c):
    return db.rf_cards.find_one({"prompt": c["prompt"], "chapter": c["chapter"], "subject": c["subject"], "retired": {"$ne": True}})["answer"]


def post(path, h, **body):
    r = s.post(f"{BASE}/rf/daily/{path}", headers=h, json={"exam": "JEE", **body}, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


def misses(h, day=None):
    return s.get(f"{BASE}/rf/daily/misses?exam=JEE" + (f"&day={day}" if day else ""), headers=h, timeout=30)


def shown(st):
    """Waits until the card is on screen (the server's own pause), a little longer so a skip is timed above zero."""
    time.sleep(st["show_in_ms"] / 1000 + 0.15)
    return st["card"]


def test_misses_only_after_finish_and_only_cards_shown():
    a, b = user(), user()
    try:
        assert misses(a).status_code == 404  # no run at all
        st = post("start", a)
        assert misses(a).status_code == 404  # still playing: no key leaves the server

        c0 = shown(st)
        k0 = key_of(c0)
        st = post("answer", a, i=0, choice=(k0 + 1) % 4)
        assert st["outcome"] == "incorrect"
        c1 = shown(st)
        st = post("answer", a, i=1, choice=key_of(c1))
        assert st["outcome"] == "correct"
        c2 = shown(st)
        st = post("answer", a, i=2, choice=None, skip=True)
        assert st["outcome"] == "skipped"
        assert misses(a).status_code == 404  # three cards in, still playing

        done = post("finish", a)
        assert done["status"] == "done" and done["result"]["correct"] == 1 and done["result"]["total"] == 45

        r = misses(a, done["result"]["day"])
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["day"] == done["result"]["day"] and m["total"] == 45 and m["correct"] == 1
        # 44 not right: the wrong one and the one the student skipped are listed; the 42 never on screen stay sealed.
        assert [x["i"] for x in m["items"]] == [0, 2] and m["sealed"] == 42
        wrong, skipped = m["items"]
        assert set(wrong) == FIELDS and set(skipped) == FIELDS
        assert wrong["prompt"] == c0["prompt"] and wrong["options"] == c0["options"] and wrong["subject"] == c0["subject"]
        assert wrong["outcome"] == "incorrect" and wrong["choice"] == (k0 + 1) % 4 and wrong["answer"] == k0
        assert skipped["prompt"] == c2["prompt"] and skipped["outcome"] == "skipped" and skipped["choice"] is None and skipped["answer"] == key_of(c2)
        assert c1["prompt"] not in [x["prompt"] for x in m["items"]]  # a card answered right is not a misfire

        assert misses(a).json() == m  # no day given = today's run
        assert misses(b, done["result"]["day"]).status_code == 404  # another student's run is never shown
        assert misses(a, "2001-01-01").status_code == 404  # a day this student did not play
        assert s.get(f"{BASE}/rf/daily/misses?exam=JEE&day=today", headers=a, timeout=30).status_code == 422
    finally:
        cleanup(a, b)
