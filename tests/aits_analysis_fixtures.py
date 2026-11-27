# Builds AITS-like analysis answers for the browser tests, from ONE real answer of the QA learner (read only: sign in +
# GETs). The real JEE Main PYQ analysis (75 questions, a chapter on every question, every level "unrated") is the base;
# the levels the website will send for AITS are written in, and the difficulty totals are worked out the way the
# website's rulebook does (count / correct / incorrect / skipped per level, Easy leak, sources, tough solved).
# Out: /app/tests/fixtures/aits_analysis/{real_unrated,aits_full,aits_partial,aits_no_easy}.json + meta.json
# The `student` block is removed. Nothing is written to the website.
import json, os, sys, uuid, urllib.request

BACKEND = os.environ.get("BACKEND", "http://localhost:8001")
OUT = "/app/tests/fixtures/aits_analysis"
sys.path.insert(0, "/app/tests")
from shine_helpers import PHONE, PIN  # noqa: E402

SID = str(uuid.uuid4())


def call(path, body=None):
    req = urllib.request.Request(BACKEND + "/api/jl" + path, data=None if body is None else json.dumps(body).encode(),
                                 method="GET" if body is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json", "X-JL-Sid": SID})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


call("/auth/phone", {"phone": PHONE, "pin": PIN})
items = call("/my/tests?tab=completed&page=1&q=&status=all&exam=")["data"]["items"]
paper = next(t for t in items if "PYQ" in str(t.get("title")) and "22 Jan 2026" in str(t.get("title")))
body = call(f"/attempts/{paper['id']}/analysis?mode=personal&compare=topper&score_version=original")
base = body["data"]
base.pop("student", None)
LEVELS = ["easy", "moderate", "tough", "unrated"]


def bucket(q):
    # The website counts only "correct" as Sahi and only "skipped" as Chhode; a bonus or dropped question is in no column
    # (the real answer: Not rated 75 = 0 / 2 / 72 and one bonus).
    o = q.get("outcome")
    return o if o in ("correct", "incorrect", "skipped") else None


CH = json.load(open("/app/backend/class_levels.json"))["exams"]["jee-main"]
NAMES = {s: [n.title() for n in list(v)[::2]] for s, v in CH.items()}  # every other name (the list carries aliases)
NAMES["Physics"][1] = "Electromagnetic Induction and Alternating Currents with LC Oscillations"  # a very long chapter name


def with_chapters(an, untagged=lambda i, q: False):
    """Real chapter names on the questions (3 in a row share one), and the chapter totals the website builds from them."""
    qs = an["questions"]
    seen = {}
    for i, q in enumerate(qs):
        k = seen[q["subject"]] = seen.get(q["subject"], -1) + 1
        names = NAMES.get(q["subject"]) or ["Chapter"]
        q["topic"] = "" if untagged(i, q) else names[(k // 3) % len(names)]
    weak = []
    for s in an["performance"]["subjects"]:
        rows = {}
        for q in qs:
            if q["subject"] != s["name"] or not q["topic"]:
                continue
            r = rows.setdefault(q["topic"], {"name": q["topic"], "count": 0, "correct": 0, "incorrect": 0, "skipped": 0, "score": 0, "maximum": 0, "negative": 0, "ids": []})
            b = bucket(q)
            r["count"] += 1
            if b:
                r[b] += 1
            r["score"] += q.get("marks") or 0
            r["maximum"] += abs(q.get("pos") or 4)
            r["negative"] += -(q.get("marks") or 0) if (q.get("marks") or 0) < 0 else 0
            if b != "correct" and b:
                r["ids"].append(q["id"])
        chapters = []
        for r in rows.values():
            att = r["correct"] + r["incorrect"]
            acc = round(100 * r["correct"] / att, 1) if att else None
            label = None if r["count"] < 3 else "strong" if (acc or 0) >= 70 else "steady" if (acc or 0) >= 40 else "weak"
            ids = r.pop("ids")
            chapters.append({**r, "attempted": att, "accuracy": acc, "attempt_rate": round(100 * att / r["count"], 1), "label": label, "lost": r["maximum"] - r["score"]})
            if r["maximum"] - r["score"] > 0:
                weak.append({"subject": s["name"], "name": r["name"], "wrong": r["incorrect"], "skipped": r["skipped"], "lost": r["maximum"] - r["score"], "questions": ids})
        s["chapters"] = chapters
    an["performance"]["weak"] = sorted(weak, key=lambda w: -w["lost"])[:7]
    an["performance"]["has_chapters"] = any(q["topic"] for q in qs)
    return an


def with_levels(an, level_of):
    an = json.loads(json.dumps(an))
    qs = an["questions"]
    for i, q in enumerate(qs):
        lv = level_of(i, q)
        q["difficulty"], q["difficulty_source"] = lv, ("paper" if lv != "unrated" else "none")
    empty = lambda: {k: 0 for k in ("count", "correct", "incorrect", "skipped")}
    allv = {l: empty() for l in LEVELS}
    subj = {}
    for q in qs:
        b = bucket(q)
        for box in (allv, subj.setdefault(q["subject"], {l: empty() for l in LEVELS})):
            box[q["difficulty"]]["count"] += 1
            if b:
                box[q["difficulty"]][b] += 1
    for x in allv.values():
        x["attempted"] = x["correct"] + x["incorrect"]
        x["accuracy"] = round(100 * x["correct"] / x["attempted"], 1) if x["attempted"] else None
    easy_wrong = [q["id"] for q in qs if q["difficulty"] == "easy" and bucket(q) == "incorrect"]
    easy_skip = [q["id"] for q in qs if q["difficulty"] == "easy" and bucket(q) == "skipped"]
    by = {q["id"]: q for q in qs}
    marks = sum(abs(by[i].get("pos") or 4) + abs(by[i].get("neg") or 1) for i in easy_wrong) + sum(abs(by[i].get("pos") or 4) for i in easy_skip)
    sources = {}
    for q in qs:
        sources[q["difficulty_source"]] = sources.get(q["difficulty_source"], 0) + 1
    unrated = allv["unrated"]["count"]
    an["difficulty"] = {
        "all": allv, "by_subject": [{"name": s, "levels": v} for s, v in subj.items()],
        "leak": {"wrong": easy_wrong, "skipped": easy_skip, "marks": marks}, "sources": sources,
        "class_n": (an.get("difficulty") or {}).get("class_n"),
        "tough_solved": [q["id"] for q in qs if q["difficulty"] == "tough" and bucket(q) == "correct"],
        "unlock": {"have": 1, "need": 50, "unrated": unrated} if unrated else None,
    }
    return an


os.makedirs(OUT, exist_ok=True)
cases = {
    # Today's real answer: every level "unrated", every chapter the paper's own name ("Previous-year paper").
    "real_unrated": base,
    # Every question rated from the paper's own tag (Easy / Moderate / Tough in turn), real chapter names.
    "aits_full": with_chapters(with_levels(base, lambda i, q: ["easy", "moderate", "tough"][i % 3])),
    # Half rated, half not yet; Chemistry has no Easy at all; every 5th question has no chapter yet.
    "aits_partial": with_chapters(with_levels(base, lambda i, q: "unrated" if i % 2 else ("moderate" if q["subject"] == "Chemistry" else ["easy", "tough"][i % 4 // 2])),
                                  untagged=lambda i, q: i % 5 == 0),
    # No Easy question anywhere: the Easy-leak line must not show.
    "aits_no_easy": with_chapters(with_levels(base, lambda i, q: ["moderate", "tough"][i % 2])),
}
for name, an in cases.items():
    json.dump({"data": an, "error": None, "meta": body.get("meta", {"api_version": "1"})}, open(f"{OUT}/{name}.json", "w"))
json.dump({"attempt_id": paper["id"], "title": paper["title"], "questions": len(base["questions"]),
           "levels": {n: c["difficulty"]["all"] if n != "real_unrated" else "all unrated" for n, c in cases.items()}},
          open(f"{OUT}/meta.json", "w"), indent=1)
print("attempt", paper["id"], "->", sorted(os.listdir(OUT)))
for n, c in cases.items():
    d = c["difficulty"]
    print(n, {l: d["all"][l]["count"] for l in LEVELS if d["all"].get(l)}, "leak", len(d["leak"]["wrong"]) + len(d["leak"]["skipped"]), "tough_solved", len(d["tough_solved"]))
